# DB Schema Snapshot

_Last updated: **2026-05-26**_

> 当前生产/本地 PostgreSQL 数据库结构快照,使用 `pg_dump --schema-only` 导出。
> 用于:架构评审 · 客户技术对接 · 合规审计 · 新成员上手参考。

## 文件清单

| 文件                                 | 说明                                                                   | 表数 |
| ------------------------------------ | ---------------------------------------------------------------------- | ---- |
| `platform_receptiviq.sql`            | **平台元数据库**(`receptiviq`)— 跨租户 + 平台管理 + RBAC + 审计 + DSAR | 32   |
| `tenant_fy.sql`                      | Agency "Fy" 的独立租户库                                               | 21   |
| `tenant_demo_brand_agency.sql`       | Agency "demo-brand-agency" 的独立租户库                                | 21   |
| `tenant_receptiviq_platform_ops.sql` | Agency "receptiviq-platform-ops" 的独立租户库                          | 21   |

## 架构说明 · 双层数据库模型

```
┌──────────────────────────────────────────────────────────────┐
│  Platform DB (receptiviq)                                      │
│  ─────────────────────────────────                             │
│  • agencies / users / tenants(全局元数据)                    │
│  • roles / permissions / role_permissions(RBAC)              │
│  • agency_role_permissions(Agency 级权限覆盖)                │
│  • audit_logs(不可篡改 · 6 年保留)                          │
│  • dsar_requests / consent_records(GDPR/CCPA/HIPAA 合规)     │
│  • user_invitations / token_usage / v_token_usage_monthly     │
└──────────────────────────────────────────────────────────────┘
                          │
            ┌─────────────┼─────────────┐
            ▼             ▼             ▼
   ┌────────────┐  ┌────────────┐  ┌────────────┐
   │ tenant_fy  │  │ tenant_demo│  │ tenant_ops │
   │  ────────  │  │  ────────  │  │  ────────  │
   │ 21 表 ·    │  │ 21 表 ·    │  │ 21 表 ·    │
   │ 业务数据   │  │ 业务数据   │  │ 业务数据   │
   │ RLS by     │  │ RLS by     │  │ RLS by     │
   │ client_id  │  │ client_id  │  │ client_id  │
   └────────────┘  └────────────┘  └────────────┘
```

### 隔离机制(双重)

1. **Agency 间:物理隔离** — 每个 Agency 独立 Postgres 数据库,DSN Fernet 加密存于 `agencies.db_dsn`
2. **Agency 内 Client 间:行级隔离** — 所有含 `client_id` 的表启用 RLS,`set_config('app.client_id')` GUC 控制

## 平台库 32 表分类

| 分类               | 表                                                                        |
| ------------------ | ------------------------------------------------------------------------- |
| **租户身份**       | `agencies` · `users` · `tenants` · `user_invitations` · `client_accounts` |
| **RBAC**           | `roles` · `permissions` · `role_permissions` · `agency_role_permissions`  |
| **审计 + 合规**    | `audit_logs` · `dsar_requests` · `consent_records`                        |
| **平台业务(冗余)** | 与租户库同名的 21 张表(`personas` / `campaigns` 等)— 平台超管视图用       |
| **观测**           | `token_usage` · `v_token_usage_monthly`(view)                             |
| **迁移**           | `alembic_version`                                                         |

## 租户库 21 表(每个 Agency 一份独立)

| 业务域            | 表                                                                        |
| ----------------- | ------------------------------------------------------------------------- |
| **客户/品牌**     | `clients` · `brands` · `client_accounts`                                  |
| **集成**          | `credentials` · `integrations` · `sync_logs`                              |
| **AI Agent 产物** | `personas` · `generations` · `generation_results` · `attribution_reports` |
| **活动管理**      | `campaign_budget_configs`                                                 |
| **数据资产**      | `marketing_data_points` · `field_mappings` · `field_mapping_versions`     |
| **激活**          | `audience_exports`                                                        |
| **报表**          | `report_schedules` · `report_history`                                     |
| **观测**          | `token_usage` · `notifications`                                           |
| **合规**          | `consent_records` · `dsar_requests`                                       |

## 重新生成命令

```bash
cd docs/schema-snapshot

PGPASSWORD=receptiviq pg_dump -h localhost -U receptiviq -d receptiviq \
  --schema-only --no-owner --no-privileges > platform_receptiviq.sql

for db in tenant_fy tenant_demo_brand_agency tenant_receptiviq_platform_ops; do
  PGPASSWORD=receptiviq pg_dump -h localhost -U receptiviq -d "$db" \
    --schema-only --no-owner --no-privileges > "${db}.sql"
done
```

## 相关文档

- 业务流: [`docs/END-TO-END-DATA-FLOW.md`](../END-TO-END-DATA-FLOW.md)
- 多租户架构: [`docs/MULTI-TENANT-DB.md`](../MULTI-TENANT-DB.md)
- 合规策略: [`features/compliance/architecture.md`](../../features/compliance/architecture.md)
- Alembic 迁移源: [`infra/migrations/`](../../infra/migrations/)
