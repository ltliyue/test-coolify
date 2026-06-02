# f19-campaigns 设计文档 — 统一 Campaign 视图 & Budget Alerts

> 版本：v1.0 | 日期：2026-04-02

## 架构概览

```
Meta Ads / DV360 / StackAdapt
       ↓ ETL Adapters (existing + f20)
  DuckDB/Snowflake (raw_meta_ads, raw_dv360, raw_stackadapt)
       ↓ dbt
  mart_campaign_unified (聚合视图)
       ↓
  CampaignQueryService → /api/v1/campaigns (只读)
       ↓
  BudgetPacingService (Celery beat) → Notifications
       ↓
  campaign_budget_configs (PG, 配置存储)
```

**核心原则**：仓库是 campaign 数据的 Single Source of Truth，PG 仅存预算配置和告警规则。

## 目录结构

### 新建文件

| 文件 | 说明 |
|------|------|
| `backend/app/models/campaign.py` | CampaignBudgetConfig ORM 模型 |
| `backend/app/schemas/campaign.py` | Pydantic schemas |
| `backend/app/api/v1/campaigns.py` | API 路由 |
| `backend/app/services/campaign_query.py` | 仓库查询服务 |
| `backend/app/services/budget_pacing.py` | 预算节奏检查服务 |
| `backend/app/tasks/budget_tasks.py` | Celery 定时任务 |
| `infra/migrations/016_campaign_budget_configs.sql` | PG 迁移 |
| `dbt/models/marts/mart_campaign_unified.sql` | dbt 跨平台聚合模型 |
| `dbt/models/staging/stg_dv360.sql` | DV360 staging（配合 f20） |
| `dbt/models/staging/stg_stackadapt.sql` | StackAdapt staging（配合 f20） |

### 修改文件

| 文件 | 变更 |
|------|------|
| `backend/app/api/v1/router.py` | 注册 campaigns_router |
| `backend/app/core/warehouse_client.py` | 添加 raw_dv360/raw_stackadapt 到白名单 + DuckDB schema |
| `backend/app/tasks/__init__.py` | 注册 budget 定时任务 |

## 数据模型

### PG: campaign_budget_configs

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PK | |
| agency_id | UUID FK → agencies | 租户隔离 |
| client_id | UUID FK → clients | nullable |
| platform | Enum(meta_ads/dv360/stackadapt) | 广告平台 |
| external_campaign_id | String(255) | 外部平台 campaign ID |
| campaign_name | String(500) | 冗余存储用于快速展示 |
| daily_budget | Numeric(12,2) | 日预算，nullable |
| total_budget | Numeric(12,2) | 总预算，nullable |
| pacing_alert_threshold | Float | 默认 0.15（15% 偏差触发） |
| alert_enabled | Boolean | 默认 true |
| created_at | DateTime(tz) | |
| updated_at | DateTime(tz) | |

**约束**：`UNIQUE(agency_id, platform, external_campaign_id)` — 防止重复配置

### DuckDB/Snowflake: mart_campaign_unified

```sql
SELECT
    agency_id, client_id, date, 'meta_ads' AS platform,
    campaign_id, campaign_name,
    SUM(impressions) AS impressions,
    SUM(clicks) AS clicks,
    SUM(spend) AS spend,
    SUM(reach) AS reach,
    SUM(conversions) AS conversions,
    SUM(conversion_value) AS conversion_value
FROM raw_meta_ads
GROUP BY 1,2,3,4,5,6
UNION ALL
-- ... raw_dv360, raw_stackadapt 同理
```

## API 设计

### 只读 Campaign 数据（从仓库查）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/campaigns` | 跨平台 campaign 列表，支持 ?platform=&date_from=&date_to=&client_id=&limit=50&offset=0 |
| GET | `/campaigns/summary` | 聚合摘要：总花费/总转化/平台分布。?view=staff(默认)\|client（client 视图简化字段名） |
| GET | `/campaigns/{platform}/{external_id}/metrics` | 单 campaign 时序数据，支持 ?limit=&offset= |

### Budget 配置 & 告警（PG CRUD）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/campaigns/budget-configs` | 列出当前 agency 的预算配置 |
| POST | `/campaigns/budget-configs` | 创建预算配置 |
| PUT | `/campaigns/budget-configs/{id}` | 更新预算配置 |
| DELETE | `/campaigns/budget-configs/{id}` | 删除预算配置 |
| GET | `/campaigns/budget-alerts` | 获取最近告警（复用 notifications 表） |

### Response Schema 示例

```python
class CampaignMetric(BaseModel):
    date: str
    platform: str
    campaign_id: str
    campaign_name: str
    impressions: int
    clicks: int
    spend: float
    reach: int
    conversions: int
    conversion_value: float

class CampaignSummary(BaseModel):
    total_spend: float
    total_conversions: int
    platform_breakdown: dict[str, float]  # platform → spend
    date_range: dict  # {from, to}
```

## 关键逻辑

### CampaignQueryService

```python
class CampaignQueryService:
    def __init__(self, warehouse: WarehouseClient):
        self.wh = warehouse

    def list_campaigns(self, agency_id, platform=None, date_from=None, date_to=None):
        sql = "SELECT * FROM mart_campaign_unified WHERE agency_id=?"
        params = [agency_id]
        if platform:
            sql += " AND platform=?"
            params.append(platform)
        # ... date filters
        return self.wh.query(sql, params)
```

### BudgetPacingService（Celery task）

```python
@celery_app.task
def check_budget_pacing():
    # 1. 查 PG 所有 alert_enabled 的 budget configs
    # 2. 对每个 config，查仓库该 campaign 当日实际 spend
    # 3. 计算 pacing = actual_spend / expected_spend_at_this_hour
    # 4. 如果偏差 > threshold → 创建 notification
    # 5. 调度频率：每 30 分钟一次
```

## 安全考量

- 所有 API 端点通过 `get_current_user` 依赖验证，`agency_id` 过滤
- 仓库 SQL 查询参数化，复用 warehouse_client 白名单机制
- Budget configs 的 CRUD 增加 `audit_simple` 审计日志

## 错误处理

| 场景 | 处理 |
|------|------|
| 仓库连接失败 | 返回 503，前端展示 "数据暂时不可用" |
| 无数据（新 agency） | 返回空列表，不报错 |
| Budget config 引用不存在的 campaign | 允许创建（campaign 数据可能尚未 ETL） |
| Celery task 异常 | 记录 error log，不影响下次调度 |
