# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Language

**Code (mandatory)**: All source-code comments, docstrings, log messages, exception messages, identifier names, commit messages and CLI output **MUST be in English** — no Chinese characters in any `.py / .ts / .tsx / .js / .jsx / .sql / .yml / .yaml / .toml / .json` file (test fixture data with intentional i18n content is the only exception, and must be flagged).

**Documentation (`.md` files)**: Bilingual — Chinese-leading prose with English technical terms inlined is the default; pure-English variants (`*-en.md`) may exist for international stakeholders.

**Conversation / summaries**: Respond in Chinese (中文) for documentation and summaries unless otherwise specified.

## Documentation Maintenance

**Last-updated date stamps (mandatory)**: Whenever a documentation file (`*.md`) is modified, update its visible "Last updated" / "最后更新" / "_Last updated:_" / "更新日期" header to **today's date** (UTC, `YYYY-MM-DD`) in the same edit. This applies to:

- `README.md` / `README.zh-CN.md`
- `docs/**/*.md` whenever they carry a top-of-file date stamp
- Any `*-en.md` bilingual sibling — keep the two dates in sync

If a doc has no date stamp yet but is being meaningfully revised, add one immediately under the H1 title in the same `_Last updated: **YYYY-MM-DD**_` format (or `_最后更新:**YYYY-MM-DD**_` for Chinese docs).

## Project Context

This is a TypeScript monorepo (likely with biz-api backend and frontend). Always check Vite proxy config when adding new API routes. When implementing file downloads (PDF, etc.), use fetch with auth headers instead of window.open.

## Bug Prevention

After implementing any new API endpoint, verify:

1. The Vite proxy config includes the new route
2. Any modal/form that references related entities (e.g., tenants, clients) includes all required selectors
3. Dependencies are installed in the correct workspace package

## Commands

### Backend

```bash
# Run all tests (from backend/)
cd backend && python3 -m pytest -v

# Run single test file
python3 -m pytest tests/test_campaigns.py -v

# Run single test
python3 -m pytest tests/test_campaigns.py::test_budget_config_crud -v

# Start dev server
uvicorn app.main:app --reload --port 8000

# Run Celery worker
celery -A app.worker:celery_app worker --loglevel=info
```

### Docker Compose (full stack)

```bash
docker compose up -d              # Start all 9 services
docker compose exec backend alembic upgrade head  # Run migrations
```

### Frontend

```bash
cd frontend && npm install && npm run dev
```

## Architecture

**Backend**: Python 3.9 / FastAPI (async) / SQLAlchemy 2.0 / Pydantic v2

### Request Flow

```
Client → FastAPI Middleware (CORS → Security Headers → HIPAA Session Guard → Request Logging)
       → Router (/api/v1/*) → Dependency Injection (get_current_user + get_db)
       → Handler → Service Layer → PostgreSQL / DuckDB-Snowflake / Redis
```

### Entity Pattern (Model → Schema → API)

Every entity follows this pattern — copy from `personas` when adding new ones:

- **Model** (`models/*.py`): SQLAlchemy ORM, UUID PK, `agency_id` FK (NOT NULL, indexed), soft-delete via `is_active`
- **Schema** (`schemas/*.py`): Pydantic v2 with `ConfigDict(from_attributes=True)`, split into Create/Update/Response
- **API** (`api/v1/*.py`): FastAPI router, all endpoints require `get_current_user`, all queries filter by `user.agency_id`

Register new routers in `api/v1/router.py`.

### ETL Adapter Pattern

All adapters inherit `BaseAdapter` (in `services/etl/base.py`):

- `platform: str` — platform identifier
- `fetch(start_date, end_date, cursor)` → `(records, next_cursor)` — extract from API
- `get_raw_table()` → table name like `"raw_meta_ads"`
- `transform(record)` → transformed dict or `None` to skip
- `credentials.get("mock")` → return synthetic data for dev

`ETLRunner` handles the full pipeline: fetch → PHI scan → anonymize → transform → warehouse write → sync state update.

When adding a new adapter:

1. Create `services/etl/adapters/<platform>.py`
2. Add raw table to `warehouse_client.py` `_ALLOWED_TABLES` + `_init_duckdb_schema()`
3. Add dbt staging model `dbt/models/staging/stg_<platform>.sql`
4. Add source definition to `dbt/models/staging/sources.yml`

### Warehouse Client (Dual Backend)

`core/warehouse_client.py` abstracts DuckDB (dev) and Snowflake (prod), selected via `WAREHOUSE_BACKEND` env var. SQL injection protection via:

- `_ALLOWED_SQL_PREFIXES`: only SELECT/INSERT/UPDATE/CREATE TABLE IF NOT EXISTS
- `_ALLOWED_TABLES`: whitelist of valid table names for `insert_many()`
- `_COL_PATTERN`: regex `^[a-z_][a-z0-9_]*$` for column names

When adding new warehouse tables: add to both `_ALLOWED_TABLES` set and `_init_duckdb_schema()` method.

### AI Agent Pattern

Three agents (Persona, Creative, Attribution) in `services/ai/agents/`. All route through `services/ai/brain.py` which handles:

- Model selection per agent (env vars `PERSONA_MODEL`, `CREATIVE_MODEL`, etc.)
- Token usage tracking to `token_usage` table
- Budget enforcement (`monthly_token_budget` on Agency model, 429 when exhausted)
- Mock mode when `OPENROUTER_API_KEY` is empty

## Compliance Rules (MANDATORY — 所有开发决策的前置约束)

> 权威来源：`features/PROJECT-PLAN.md` 合规顶层策略 + `features/compliance/architecture.md`
> 原则：**Privacy by Design** — 合规嵌入架构，而非事后补丁。合规不是附加功能。

本项目必须**同时满足 GDPR + CCPA + HIPAA 三大法规**。以下规则适用于所有新增代码，违反任何一条视为阻塞性问题。

### 数据分级（Data Classification）

所有数据字段必须归属以下级别之一，决定加密、访问控制和保留策略：

| 级别               | 说明           | 示例                                | 策略                              |
| ------------------ | -------------- | ----------------------------------- | --------------------------------- |
| Level 0 — Public   | 公开数据       | 平台名称、活动名称、汇总指标        | 无特殊限制                        |
| Level 1 — Internal | 内部数据       | 租户配置、系统日志                  | 内部访问控制                      |
| Level 2 — PII      | 个人可识别信息 | 邮箱、姓名、IP、Cookie ID、设备指纹 | 加密+哈希+审计+保留策略           |
| Level 3 — PHI      | 受保护健康信息 | 健康状况、医疗记录                  | AES-256加密+BAA+15min超时+6年保留 |

### 数据仓库入仓规则（ETL 管道）

1. **PII/PHI 永远不以明文存入仓库** — 所有用户标识符进仓库前必须经 `hash_identifier(value, agency_salt)` 单向哈希（SHA-256 + 租户盐值）
2. **ETL Runner 无条件匿名化** — `anonymize_record_for_warehouse()` 对每条记录执行，不仅限于 PHI 检测命中的记录
3. **禁止 `raw_json` 字段** — 原始 API 响应可能包含绕过检测的 PII，新 adapter 不得存储原始响应
4. **IP 地址截断** — IPv4 截断为 /24（192.168.1.0），IPv6 截断为 /48
5. **数据最小化** — 只保留业务分析所需的最小字段集，移除冗余个人信息
6. **PHI 检测拦截** — `phi_detector.scan_record()` 扫描 HIPAA Safe Harbor 18 类标识符，发现 PHI 时记录警告日志

### 数据库存储规则（PostgreSQL）

7. **用户 PII 加密存储** — email/full_name 使用 Fernet 加密，email_hash (SHA-256) 用于 WHERE 查找
8. **每个 Agency 独立加密密钥** — 密钥与数据物理分离，密钥存储在独立服务
9. **凭证加密** — Credential 表的 encrypted_data 字段使用 Fernet 加密存储 OAuth token / API key

### 访问控制与审计

10. **租户隔离强制执行** — 每条查询 MUST 通过 `agency_id` 过滤（来自已认证用户），无例外
11. **审计日志全覆盖** — 所有 API 端点必须调用 `audit_simple()`，特别是仓库读写操作。审计日志为 INSERT-only
12. **HIPAA 会话超时** — 15 分钟不活动超时（Redis-backed + 内存 LRU fallback），HIPAA 客户强制启用
13. **登录限流** — IP 级别 5 次失败 / 5 分钟 → 15 分钟锁定

### 数据保留策略（取三法规最严值）

| 数据类型      | 保留期限       | 来源          |
| ------------- | -------------- | ------------- |
| 审计日志      | **6 年**       | HIPAA（最长） |
| PHI 数据      | 6 年           | HIPAA         |
| 财务/计费     | 7 年           | GDPR          |
| 营销活动数据  | 3 年           | GDPR/CCPA     |
| 会话/行为日志 | 90 天          | GDPR/CCPA     |
| PII 数据      | 合同期 + 30 天 | GDPR          |

### DSAR（数据主体权利）

14. **DSAR SLA** — GDPR 30天 / CCPA 45天 / HIPAA 30天内响应
15. **支持操作** — access（导出）、delete（删除/匿名化）、export（可携格式）、rectify（更正）、restrict（限制处理）
16. **删除不销毁审计** — 执行 DSAR 删除时保留审计痕迹本身（GDPR 要求）

### 违规通知

17. **通知时限** — GDPR 72小时通知监管机构 / HIPAA 60天通知 HHS / CCPA 通知受影响消费者
18. **BAA 追踪** — HIPAA 客户必须有签署的 Business Associate Agreement，系统追踪 BAA 状态和到期日

### 开发检查清单

每次提交前确认：

- [ ] 新增字段是否标注了数据分级（Level 0-3）？
- [ ] 新增 ETL adapter 是否移除了 raw_json？是否有 PII 字段需要 `transform()` 哈希处理？
- [ ] 新增 API 端点是否有 `get_current_user` + `agency_id` 过滤 + `audit_simple()`？
- [ ] 新增数据库列如包含 PII，是否使用了 Fernet 加密或 SHA-256 哈希？
- [ ] 新增仓库表是否加入 `_ALLOWED_TABLES` 白名单？

## Testing

Tests use `pytest-asyncio` with a real PostgreSQL database. Key fixtures from `conftest.py`:

- `client` — AsyncClient for API testing
- `test_agency` → `test_user` → `admin_token` → `auth_headers` — seed data chain
- `clean_tables` (autouse) — TRUNCATE all tables between tests

For warehouse/ETL tests, use an in-memory DuckDB:

```python
@pytest.fixture
def warehouse():
    from app.core.warehouse_client import WarehouseClient
    wh = WarehouseClient(backend="duckdb")
    wh._db_path = ":memory:"
    wh.connect()
    yield wh
    wh.close()
```

**Python 3.9 compatibility**: Do not use `X | Y` union syntax in type hints for ORM models — use `Optional[X]` from typing instead.

## Database Migrations

SQL migration files live in `infra/migrations/` (numbered `001_` through `016_`). Apply via:

```bash
# In Docker
docker compose exec backend alembic upgrade head

# Or run SQL directly via asyncpg (see migration scripts)
```

When adding new tables: create a new migration file (`017_<name>.sql`) and add the table to `conftest.py`'s `_TRUNCATE_TABLES` list if it needs test cleanup.
