# f21-persona-audience-export 设计文档

> 版本：v1.0 | 日期：2026-04-02

## 架构概览

```
Persona (PG)
    ↓ API: POST /personas/{id}/export-audience
AudienceExportService
    ├── PersonaToTargetingTranslator（转换 persona → targeting spec）
    ├── MetaAudienceClient（Meta Marketing API 调用）
    ├── DV360AudienceClient（DV360 API 调用）
    └── AudienceExport (PG)（记录导出状态）
        ↓ Celery task（异步执行）
    Platform API（Meta / DV360）
```

## 目录结构

### 新建文件

| 文件 | 说明 |
|------|------|
| `backend/app/models/audience_export.py` | AudienceExport ORM 模型 |
| `backend/app/schemas/audience_export.py` | Pydantic schemas |
| `backend/app/services/audience_export/translator.py` | Persona → targeting spec 转换 |
| `backend/app/services/audience_export/meta_client.py` | Meta Marketing API 客户端 |
| `backend/app/services/audience_export/dv360_client.py` | DV360 API 客户端 |
| `backend/app/services/audience_export/service.py` | AudienceExportService 主逻辑 |
| `backend/app/tasks/audience_tasks.py` | Celery 异步导出任务 |
| `infra/migrations/017_audience_exports.sql` | PG 迁移 |
| `backend/tests/test_audience_export.py` | 测试 |

### 修改文件

| 文件 | 变更 |
|------|------|
| `backend/app/api/v1/personas.py` | 新增 export-audience 端点 |
| `backend/app/models/__init__.py` | 注册 AudienceExport |

## 数据模型

### PG: audience_exports

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PK | |
| agency_id | UUID FK → agencies | 租户隔离（Level 1） |
| persona_id | UUID FK → personas | 来源 persona |
| platform | String(50) | meta_ads / dv360 |
| external_audience_id | String(255) | 平台返回的受众 ID（Level 0） |
| targeting_spec | JSON | 发送给平台的 targeting 配置（Level 0，不含 PII） |
| status | Enum | pending / processing / success / failed |
| error_message | Text | 失败原因（nullable） |
| retry_count | Integer | 重试次数，默认 0 |
| created_at | DateTime(tz) | |
| completed_at | DateTime(tz) | nullable |

**数据分级**：targeting_spec 仅含 Level 0 数据（兴趣/年龄段/地域等聚合属性），不含 email/phone 等 PII。

## API 设计

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/personas/{persona_id}/export-audience` | 发起导出（返回 export record，Celery 异步执行） |
| GET | `/personas/{persona_id}/export-audience` | 查看该 persona 的导出历史 |
| GET | `/personas/{persona_id}/export-audience/preview` | 预览 targeting spec（不实际调用平台 API） |
| GET | `/personas/audience-exports` | 列出当前 agency 所有导出记录 |

### Request/Response

```python
class AudienceExportRequest(BaseModel):
    platform: str  # "meta_ads" | "dv360"
    audience_name: Optional[str] = None  # 自定义受众名称，默认用 persona.name

class AudienceExportPreview(BaseModel):
    platform: str
    persona_name: str
    targeting_spec: dict  # 转换后的平台 targeting 配置
    warnings: list[str]  # 可能的问题提示

class AudienceExportResponse(BaseModel):
    id: uuid.UUID
    persona_id: uuid.UUID
    platform: str
    status: str
    external_audience_id: Optional[str]
    targeting_spec: dict
    error_message: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
```

## 关键逻辑

### PersonaToTargetingTranslator

```python
class PersonaToTargetingTranslator:
    def translate(self, persona: Persona, platform: str) -> dict:
        """将 persona 的结构化属性转为平台 targeting spec。"""
        # 1. 提取 psychographics（兴趣、行为标签）
        # 2. 提取 channel_preferences（渠道偏好 → 投放版位）
        # 3. 提取人口统计（年龄段、性别、地域 — 仅聚合级别，无个人 PII）
        # 4. PII 过滤：移除任何 email/phone/name 字段（合规要求）
        # 5. 按平台格式化输出

    def _to_meta_spec(self, attrs: dict) -> dict:
        """Meta Ads targeting_spec 格式"""
        return {
            "geo_locations": {"countries": attrs.get("countries", [])},
            "age_min": attrs.get("age_min", 18),
            "age_max": attrs.get("age_max", 65),
            "interests": [{"id": i, "name": n} for i, n in attrs.get("interests", [])],
            "behaviors": [{"id": b, "name": n} for b, n in attrs.get("behaviors", [])],
        }

    def _to_dv360_spec(self, attrs: dict) -> dict:
        """DV360 audience segment 格式"""
        return {
            "displayName": attrs.get("audience_name", ""),
            "membershipDurationDays": 30,
            "audienceType": "FIRST_PARTY",
            "description": attrs.get("description", ""),
        }
```

### MetaAudienceClient

```python
class MetaAudienceClient:
    BASE_URL = "https://graph.facebook.com/v19.0"

    async def create_custom_audience(self, access_token, account_id, name, targeting_spec):
        """调用 Meta Marketing API 创建 Custom Audience。"""
        # POST /act_{account_id}/customaudiences
        # 返回 external_audience_id

    async def mock_create(self, name, targeting_spec):
        """Mock 模式：返回模拟的 audience ID。"""
        return {"id": f"mock_meta_{uuid.uuid4().hex[:8]}"}
```

### Celery Task

```python
@celery_app.task(bind=True, max_retries=1)
def execute_audience_export(self, export_id: str):
    """异步执行受众导出。"""
    # 1. 查 AudienceExport 记录
    # 2. 查关联 Persona
    # 3. 从 Credential Vault 获取平台凭证
    # 4. 调用平台 API 创建受众
    # 5. 更新 export 状态为 success + external_audience_id
    # 6. 失败时 retry 一次
```

## 安全 & 合规考量

- **PII 过滤**（合规规则 1）：translator 转换时显式移除 email/phone/name 等 Level 2+ 字段，仅保留聚合属性
- **审计日志**（合规规则 11）：export-audience 端点调用 `audit_simple()`，记录 persona_id、platform、结果
- **租户隔离**（合规规则 10）：所有查询 + 导出均通过 `agency_id` 过滤
- **凭证安全**（合规规则 9）：平台 API token 从 Credential Vault 解密获取，不日志记录
- **数据最小化**（合规规则 5）：targeting_spec 只含投放所需的最小属性集

## 错误处理

| 场景 | 处理 |
|------|------|
| Persona 不存在/已删除 | 404 |
| 平台凭证未配置 | 400, "Platform credentials not configured" |
| 平台 API 调用失败 | Celery 重试 1 次，最终失败记录 error_message |
| Persona 无 psychographics 数据 | 返回 preview 的 warnings 提示 |
| 并发重复导出同一 persona | 允许（创建新 export 记录） |
