# 多租户数据库隔离方案 / Multi-Tenant Database Isolation

_Last updated: **2026-05-20**_

## 背景

PSD 架构目标是 **每个 Agency 拥有独立数据库实例**（per-Agency Neon project）。
但全量迁移需要多周工作（DSN 路由、连接池、跨集群迁移、DR 等）。本 PR 落地的是
MVP 折中方案：**Schema-per-Agency**，物理隔离行级数据，并保留向 Phase 2
（per-Agency Neon project）平滑演进的接口。

## 当前状态（Phase 1 / MVP）

共享一个 Postgres 集群（本地 `:5432`，生产 Neon）：

| 层级           | Schema 位置     | 表                                                                                                                                                                                                                                                                                                                                                                                                    |
| -------------- | --------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Platform-owned | `public`        | `agencies`, `users`, `user_invitations`, `audit_logs`, `tenants`, `alembic_version`                                                                                                                                                                                                                                                                                                                   |
| Agency-owned   | `tenant_<slug>` | `personas`, `generations`, `generation_results`, `campaigns`, `campaign_budget_configs`, `attribution_reports`, `audience_exports`, `report_history`, `report_schedules`, `notifications`, `field_mappings`, `field_mapping_versions`, `integrations`, `credentials`, `sync_logs`, `marketing_data_points`, `token_usage`, `consent_records`, `dsar_requests`, `brands`, `clients`, `client_accounts` |

> 注：当前代码库未发现 `creatives` 与 `reports` 主表（创意产物落在 `generations` /
> `generation_results`，报告主表通过 `report_history` + `report_schedules`
> 体现），故 `agency_schema.sql` 未包含同名表。

### 数据模型字段

`agencies` 表新增两个字段（migration `021_agency_isolation.sql`）：

| 字段        | 类型            | 含义                                                                                         |
| ----------- | --------------- | -------------------------------------------------------------------------------------------- |
| `db_schema` | `TEXT NOT NULL` | 当前 Agency 在共享 Postgres 中使用的 schema，例如 `tenant_acme`                              |
| `db_dsn`    | `TEXT NULL`     | 预留字段。Phase 2 中，若设置则 `TenantSessionRouter` 会改为路由到该 DSN（独立 Neon project） |

### 关键代码

- `infra/migrations/021_agency_isolation.sql` —— 字段迁移 + 现有 Agency 回填
- `infra/migrations/agency_schema.sql` —— 租户 schema 模板，含 `__TENANT_SCHEMA__` 占位符
- `backend/app/core/tenant_db.py` —— 提供：
  - `derive_schema_name(slug)`：从 slug 推导安全的 schema 名
  - `provision_agency_schema(session, schema)`：`CREATE SCHEMA` + 回放模板
  - `set_search_path(session, schema)`：`SET LOCAL search_path TO <schema>, public`
  - `get_tenant_db(...)`：FastAPI 依赖，按当前用户的 Agency 自动设置 search_path
- `backend/app/api/v1/personas.py` —— POC：已切换到 `get_tenant_db`
- `backend/app/api/v1/platform.py` / `auth.py` —— 创建 Agency 时同步 provision

### 为什么不全量迁移所有路由？

- 现有 20+ 个 router 全部带 `agency_id` 过滤，**行级隔离已经存在**；schema 切换主要
  是物理隔离 + 为 Phase 2 铺路。
- 一次性切换风险大（事务 / 测试 fixtures / dbt staging 都要同步更新），分批进行
  更安全。`personas` 作为 POC 验证 pattern。
- 现存 `public.<agency-owned-table>` 仍然保留，作为兼容层；新写入由 `get_tenant_db`
  路由到 `tenant_<slug>.<table>`。

### 数据回填策略

本 PR 的存量数据（截至 2026-05-20，仅 1 个 Agency `Fy` / `tenant_fy`）：

- 现有 `public.personas` 行数为 0，**无需迁移**。
- `tenant_fy` schema 已通过 `sed` 替换占位符后回放 `agency_schema.sql` 创建。

后续若 `public` 中已有数据需要批迁移到 tenant schema，应编写一次性脚本：

```sql
INSERT INTO tenant_<slug>.<table>
SELECT * FROM public.<table>
WHERE agency_id = '<agency-uuid>';
```

并在迁移完成后 `TRUNCATE` `public.<table>` 中已经迁出的数据（或保留旁路只读副本，
直到 Phase 2 完成）。

## Phase 2：Per-Agency Neon Project

目标：每个 Agency 对应一个独立 Neon 项目（独立 control plane + 独立计算 + 独立
存储 + 独立 PITR）。

### 演进步骤

1. **新建 Agency**：在 Neon API 创建 project，得到 `db_dsn`，写入 `agencies.db_dsn`
2. **TenantSessionRouter**：替换 `get_tenant_db` 实现：

   ```python
   class TenantSessionRouter:
       _engines: dict[str, AsyncEngine] = {}

       def get_engine_for_agency(self, agency: Agency) -> AsyncEngine:
           if agency.db_dsn:
               eng = self._engines.get(agency.db_dsn)
               if eng is None:
                   eng = create_async_engine(agency.db_dsn, ...)
                   self._engines[agency.db_dsn] = eng
               return eng
           # Fallback：共享集群 + schema 隔离
           return shared_engine
   ```

3. **存量迁移**：`pg_dump` 共享集群中 `tenant_<slug>` 的数据 → restore 到新 Neon
   project 的 `public` schema；将 `db_dsn` 设值；删除共享集群的 `tenant_<slug>`
   schema。
4. **审计/支付/平台报表**：仍指向 Platform 集群的 `public.audit_logs`。跨集群
   报表通过定时 ETL 汇总到 Platform 数据仓库。

### 为什么 public vs tenant 拆分？

| 表归属                                                         | 原因                                                        |
| -------------------------------------------------------------- | ----------------------------------------------------------- |
| `public.agencies` / `public.users` / `public.user_invitations` | 平台运营操作的全局表，跨租户访问                            |
| `public.audit_logs`                                            | HIPAA 要求 INSERT-only、6 年保留，集中存储便于合规检索      |
| `tenant_*.personas` 等                                         | 属于 Agency 的业务资产；行级 + 物理隔离；Phase 2 可独立搬迁 |

### 已知限制 / TODO

- `get_tenant_db` 当前仅在 `personas` router 使用；其余 router 仍读写 `public`，
  需要按业务节奏分批迁移
- `tests/conftest.py` 的 `_TRUNCATE_TABLES` 列表仍指向 `public.*`，新增 tenant
  schema 测试需要扩展 fixture
- dbt staging（`dbt/models/staging/`）的 source 定义仍引用 `public.*`
- `db_dsn` 字段已就位但 `TenantSessionRouter` 未实现（Phase 2）

## 验证命令

```bash
# 查看 Agency 与其 schema 映射
PGPASSWORD=receptiviq psql -h localhost -U receptiviq -d receptiviq \
  -c "SELECT name, slug, db_schema, db_dsn FROM agencies;"

# 查看某 Agency schema 下的表
PGPASSWORD=receptiviq psql -h localhost -U receptiviq -d receptiviq \
  -c "\dt tenant_fy.*"

# 触发新 Agency 创建（验证自动 provision）
curl -X POST http://127.0.0.1:8000/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"new@example.com","password":"Test1234!","full_name":"X","agency_name":"NewCo"}'
```
