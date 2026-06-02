# f20-etl-adapters 设计文档 — Quorum / LeadRX / LiveRamp / DV360 / StackAdapt

> 版本：v1.0 | 日期：2026-04-02

## 架构概览

```
Platform APIs
  ├── Quorum API     ──→ QuorumAdapter     ──→ raw_quorum
  ├── LeadRX API     ──→ LeadRXAdapter     ──→ raw_leadrx
  ├── LiveRamp API   ──→ LiveRampAdapter   ──→ raw_liveramp
  ├── DV360 API      ──→ DV360Adapter      ──→ raw_dv360
  └── StackAdapt API ──→ StackAdaptAdapter ──→ raw_stackadapt
                            ↓
                    ETLRunner (existing)
                    ├── PHI scan + anonymize
                    ├── transform
                    └── insert_many → warehouse
                            ↓
                    dbt staging → canonical → marts
```

**核心原则**：所有 adapter 继承 `BaseAdapter`，遵循相同的 fetch→transform→load 模式。

## 目录结构

### 新建文件

| 文件 | 说明 |
|------|------|
| `backend/app/services/etl/adapters/quorum.py` | Quorum adapter |
| `backend/app/services/etl/adapters/leadrx.py` | LeadRX adapter |
| `backend/app/services/etl/adapters/liveramp.py` | LiveRamp adapter |
| `backend/app/services/etl/adapters/dv360.py` | DV360 adapter |
| `backend/app/services/etl/adapters/stackadapt.py` | StackAdapt adapter |
| `dbt/models/staging/stg_quorum.sql` | Quorum staging |
| `dbt/models/staging/stg_leadrx.sql` | LeadRX staging |
| `dbt/models/staging/stg_liveramp.sql` | LiveRamp staging |
| `dbt/models/staging/stg_dv360.sql` | DV360 staging |
| `dbt/models/staging/stg_stackadapt.sql` | StackAdapt staging |

### 修改文件

| 文件 | 变更 |
|------|------|
| `backend/app/core/warehouse_client.py` | 添加 5 张 raw 表到白名单 + DuckDB schema |
| `backend/app/tasks/etl_tasks.py` | 注册新 adapter 的定时任务 |
| `backend/dags/etl_sync_dag.py` | Airflow DAG 添加新平台 |
| `dbt/models/staging/sources.yml` | 添加新 source 定义 |

## 数据模型 — DuckDB/Snowflake raw 表

### raw_quorum

| 字段 | 类型 | 说明 |
|------|------|------|
| agency_id | VARCHAR | 租户 |
| client_id | VARCHAR | nullable |
| date | DATE | |
| audience_id | VARCHAR | 受众 segment ID |
| audience_name | VARCHAR | |
| category | VARCHAR | 行为类别 |
| reach | INTEGER | |
| engagement_score | FLOAT | |
| raw_json | JSON | 原始响应 |
| ingested_at | TIMESTAMP | |

### raw_leadrx

| 字段 | 类型 | 说明 |
|------|------|------|
| agency_id | VARCHAR | |
| client_id | VARCHAR | nullable |
| date | DATE | |
| conversion_id | VARCHAR | |
| touchpoint_channel | VARCHAR | 触点渠道 |
| touchpoint_source | VARCHAR | 触点来源 |
| attribution_model | VARCHAR | 归因模型 |
| attribution_weight | FLOAT | 归因权重 |
| conversion_value | FLOAT | |
| raw_json | JSON | |
| ingested_at | TIMESTAMP | |

### raw_liveramp

| 字段 | 类型 | 说明 |
|------|------|------|
| agency_id | VARCHAR | |
| client_id | VARCHAR | nullable |
| date | DATE | |
| segment_id | VARCHAR | |
| segment_name | VARCHAR | |
| match_type | VARCHAR | cookie/device/email |
| matched_count | INTEGER | |
| total_count | INTEGER | |
| match_rate | FLOAT | |
| raw_json | JSON | |
| ingested_at | TIMESTAMP | |

### raw_dv360

| 字段 | 类型 | 说明 |
|------|------|------|
| agency_id | VARCHAR | |
| client_id | VARCHAR | nullable |
| date | DATE | |
| advertiser_id | VARCHAR | |
| campaign_id | VARCHAR | |
| campaign_name | VARCHAR | |
| line_item_id | VARCHAR | |
| impressions | INTEGER | |
| clicks | INTEGER | |
| spend | FLOAT | |
| conversions | INTEGER | |
| conversion_value | FLOAT | |
| raw_json | JSON | |
| ingested_at | TIMESTAMP | |

### raw_stackadapt

| 字段 | 类型 | 说明 |
|------|------|------|
| agency_id | VARCHAR | |
| client_id | VARCHAR | nullable |
| date | DATE | |
| campaign_id | VARCHAR | |
| campaign_name | VARCHAR | |
| creative_id | VARCHAR | |
| impressions | INTEGER | |
| clicks | INTEGER | |
| spend | FLOAT | |
| conversions | INTEGER | |
| conversion_value | FLOAT | |
| raw_json | JSON | |
| ingested_at | TIMESTAMP | |

## Adapter 实现模式

每个 adapter 遵循统一模式（以 DV360 为例）：

```python
class DV360Adapter(BaseAdapter):
    platform = "dv360"
    BASE_URL = "https://displayvideo.googleapis.com/v3"

    def get_raw_table(self) -> str:
        return "raw_dv360"

    def fetch(self, start_date, end_date, cursor=None):
        if self.credentials.get("mock"):
            return self._mock_data(start_date, end_date), None
        # 真实 API 调用 + 分页
        ...

    def _mock_data(self, start_date, end_date):
        return [{ ... }]  # 开发用 mock 数据
```

**关键约定**：
- `credentials.get("mock")` 为 True 时返回 mock 数据
- `fetch()` 返回 `(records, next_cursor)`
- `get_raw_table()` 返回 `raw_<platform>`
- 无需覆写 `transform()`，默认透传

## dbt staging 模式

```sql
-- stg_dv360.sql
SELECT
    agency_id,
    client_id,
    date,
    campaign_id,
    campaign_name,
    SUM(impressions) AS impressions,
    SUM(clicks) AS clicks,
    SUM(spend) AS spend,
    SUM(conversions) AS conversions,
    SUM(conversion_value) AS conversion_value
FROM {{ source('receptiviq', 'raw_dv360') }}
GROUP BY 1,2,3,4,5
```

## 安全考量

- API credentials 从 Credential Vault 解密获取，不硬编码
- PII/PHI 数据经 `scan_record` + `anonymize_record_for_warehouse` 处理
- LiveRamp 的 identity 数据需特别注意跨设备标识符的哈希处理：
  - `email` 字段：使用 `anonymizer.hash_identifier(email, agency_salt)` 单向哈希后存储
  - `device_id` 字段：同样哈希处理，不存明文
  - `segment_name` 保留明文（非 PII）
- LeadRX adapter 的 `fetch()` 必须实现分页（API 返回 next_cursor），单次请求上限 1000 条

## 错误处理

| 场景 | 处理 |
|------|------|
| API 认证失败 (401/403) | 标记 integration 状态为 EXPIRED，通知用户重新授权 |
| API 限流 (429) | 指数退避重试，最多 3 次 |
| 数据格式异常 | 记录到 ETLResult.errors，跳过该记录，继续处理 |
| 网络超时 | 记录错误，不更新 sync_state，下次自动从上次位置继续 |
