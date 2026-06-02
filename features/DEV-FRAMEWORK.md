# ReceptivIQ Platform — 开发框架文档

> 版本：v1.1 | 日期：2026-04-02
> 本文档是新项目的权威开发参考，标注每个框架组件的完成状态和优先级。

---

## 状态图例

| 图标 | 含义                                         |
| ---- | -------------------------------------------- |
| ✅   | **已完成** — 代码已写入，可直接使用          |
| 🔧   | **骨架已有** — 设计/结构存在，核心逻辑待实现 |
| 📋   | **未开始** — 需全新开发                      |

优先级：**P0** = 所有 Pillar 的前置依赖（必须第一批完成）| **P1** = 核心产品功能 | **P2** = 增强/体验

---

## 框架总览

| 编号 | 模块                             | 优先级 | 状态                                                      | 阶段    |
| ---- | -------------------------------- | ------ | --------------------------------------------------------- | ------- |
| F-00 | 合规基础层（GDPR/CCPA/HIPAA）    | **P0** | ✅ **已完成** — 2026-03-31，27/27 测试通过                | Phase 0 |
| F-01 | 多租户基础设施                   | **P0** | ✅ **已完成** — 2026-03-31，27/27 测试通过                | Phase 0 |
| F-02 | 认证与授权（Auth + RBAC）        | **P0** | ✅ **已完成** — 2026-03-31，27/27 测试通过                | Phase 0 |
| F-03 | 凭证保险库（Credential Vault）   | **P0** | ✅ **已完成** — 2026-03-31，Fernet 加密，API Key 存储     | Phase 0 |
| F-04 | 审计日志（Audit Logging）        | **P0** | ✅ **已完成** — 2026-03-31，INSERT-only，extra_data 字段  | Phase 0 |
| F-05 | 平台集成管理                     | **P0** | ✅ **已完成** — 2026-03-31，12 平台注册，connect/sync     | Phase 0 |
| F-06 | ETL 数据管道                     | **P0** | ✅ **已完成** — 2026-03-31，GA4/Meta/HubSpot，PHI 合规层  | Phase 1 |
| F-07 | Canonical Schema + dbt 转换层    | **P0** | ✅ **已完成** — 2026-03-31，staging+canonical+mart 全层   | Phase 1 |
| F-08 | Snowflake 数据仓库集成           | **P0** | ✅ **已完成** — 2026-03-31，DuckDB 降级+Snowflake 接口    | Phase 1 |
| F-09 | Core AI Brain（LLM 路由器）      | **P1** | ✅ **已完成** — 2026-03-31，TokenUsage+预算控制+API       | Phase 1 |
| F-10 | Persona Agent（Pillar 1）        | **P1** | ✅ **已完成** — 2026-03-31，9/9 测试通过，CRUD+AI 生成    | Phase 2 |
| F-11 | Creative Agent（Pillar 2）       | **P1** | ✅ **已完成** — 2026-03-31，8/8 测试通过，四平台创意生成  | Phase 2 |
| F-12 | Attribution Agent（Pillar 3）    | **P1** | ✅ **已完成** — 2026-03-31，9/9 测试通过，多触点归因分析  | Phase 3 |
| F-13 | 品牌入驻系统（Brand Onboarding） | **P1** | ✅ **已完成** — 2026-03-31，7/7 测试通过，PATCH 语义更新  | Phase 1 |
| F-14 | 历史数据手动导入                 | **P1** | ✅ **已完成** — 2026-03-31，9/9 测试通过，三平台+自动检测 | Phase 1 |
| F-15 | 字段映射系统（Field Mapping）    | **P1** | ✅ **已完成** — 2026-03-31，14/14 测试通过，版本管理+回滚 | Phase 1 |
| F-16 | 客户门户（Client Portal）        | **P2** | ✅ **已完成** — 2026-03-31，8/8 测试通过，5 端点白标门户  | Phase 3 |
| F-17 | 实时通知（WebSocket）            | **P2** | ✅ **已完成** — 2026-03-31，9/9 测试通过，WS+通知系统     | Phase 3 |
| F-18 | 监控与可观测性                   | **P2** | ✅ **已完成** — 2026-03-31，Sentry+Langfuse+健康检查      | Phase 0 |
| F-19 | 统一 Campaign 视图 + Budget Alerts | **P1** | ✅ **已完成** — 2026-04-02，12/12 测试通过，仓库聚合+预算告警 | Phase 1 |
| F-20 | ETL Adapters 扩展（5 平台）      | **P0** | ✅ **已完成** — 2026-04-02，18/18 测试通过，Quorum/LeadRX/LiveRamp/DV360/StackAdapt | Phase 1 |
| F-21 | Persona-to-Audience Export       | **P1** | ✅ **已完成** — 2026-04-02，13/13 测试通过，Meta/DV360 受众导出+PII过滤 | Phase 2 |
| F-22 | PDF 报告引擎 + 自动发送          | **P0** | ✅ **已完成** — 2026-04-02，11/11 测试通过，模板渲染+调度+邮件+加密recipients | Phase 1 |

---

## F-00 合规基础层（GDPR · CCPA · HIPAA）

**优先级：P0 — 所有数据处理的前置约束**
**阶段：Phase 0**
**状态：✅ 已完成 — 2026-03-31**

> 合规不是附加功能，是所有开发决策的前置约束。每条数据流都必须经过合规层。

### 已完成 ✅

| 文件                                           | 内容                                                                                                           |
| ---------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `features/compliance/architecture.md`          | 10 节完整合规设计文档，覆盖三大法规                                                                            |
| `infra/migrations/011_compliance.sql`          | 7 张合规表：consent_records, dsar_requests, retention_policies, breach_incidents, BAA, DPA, data_flow_mappings |
| `backend/app/core/compliance/anonymizer.py`    | hash_identifier / truncate_ip / mask_email / anonymize_record_for_warehouse / scrub_pii_from_logs              |
| `backend/app/core/compliance/phi_detector.py`  | HIPAA Safe Harbor 18 类 PHI 检测 + deidentify_safe_harbor                                                      |
| `backend/app/core/compliance/session_guard.py` | HIPAA 15 分钟会话超时中间件（M-05：Redis + 内存 LRU 双层 fallback）                                            |
| `backend/app/core/pii_crypto.py`               | M-02/M-03：用户 PII Fernet 加密/解密 + email SHA-256 哈希                                                      |
| `backend/app/api/v1/compliance.py`             | DSAR API + 同意管理 API（M-06：agency_id 强制隔离，M-04：IP 截断，H-08：审计日志）                             |
| `backend/app/models/consent.py`                | ConsentRecord ORM（C-03：subject_hash 匿名化，无明文 email 列）                                                |
| `backend/app/models/dsar.py`                   | DSARRequest ORM（C-03：subject_email_hash 哈希存储，数据最小化）                                               |
| `backend/app/main.py`                          | C-05 启动校验 + M-01 CORS + M-11 安全头 + HIPAASessionGuard                                                    |
| `backend/app/core/security.py`                 | C-04：JWT jti + Redis 黑名单撤销（内存 fallback）                                                              |
| `backend/app/api/v1/auth.py`                   | M-10：IP 级登录限流（5次/5分钟→锁定15分钟），M-02：email_hash 查找                                             |
| `backend/app/api/v1/oauth_callback.py`         | C-01：HMAC 签名 state 参数 + 10 分钟过期（CSRF + 跨租户防护）                                                  |
| `backend/app/core/warehouse_client.py`         | H-02/H-03：SQL 语句前缀白名单 + 表名列名正则校验                                                               |
| `backend/app/core/audit.py`                    | L-03：extra_data 字段名修复，审计元数据正确持久化                                                              |
| `backend/app/models/persona.py`                | L-01：agency_id NOT NULL 强制租户隔离                                                                          |
| `backend/app/schemas/field_mapping.py`         | L-02：transform config 4KB 大小限制 + 200 条/次映射条目限制                                                    |
| `backend/app/core/config.py`                   | H-06：Airflow 凭证无默认值，强制环境变量配置                                                                   |
| `backend/app/tasks/etl_tasks.py`               | H-10：dbt 子进程错误信息脱敏，不泄露内部细节                                                                   |
| `backend/app/services/etl/adapters/hubspot.py` | M-08：API 错误日志只记录异常类名，不暴露响应体/token                                                           |

### 合规审计历史（4 轮，共 56 项发现，全部已处理）

| 轮次    | 日期       | 修复项 | 重点                                           |
| ------- | ---------- | ------ | ---------------------------------------------- |
| 第 1 轮 | 2026-03-31 | 12 项  | 核心表结构 + API 端点基础合规                  |
| 第 2 轮 | 2026-03-31 | 24 项  | PII 加密（M-02/M-03）+ 审计日志 + OAuth CSRF   |
| 第 3 轮 | 2026-04-01 | 4 项   | 深层架构级问题梳理                             |
| 第 4 轮 | 2026-04-01 | 8 项   | 限流 + 内存 fallback + SQL 注入防护 + 输入校验 |

### 后续待实现 📋

| 任务             | 说明                                                      |
| ---------------- | --------------------------------------------------------- |
| 数据保留定时任务 | Celery Beat 任务，按 retention_policies 表定期清理/匿名化 |
| BAA 管理 UI      | 内部工具，追踪第三方 BAA 状态                             |
| 违规事件告警     | 检测到违规时自动触发通知（72h GDPR / 60d HIPAA）          |

---

## F-01 多租户基础设施（Multi-Tenant Foundation）

**优先级：P0**
**阶段：Phase 0**
**状态：✅ 已完成 — 2026-03-31**

### 已完成 ✅

| 文件                                    | 内容                                                          |
| --------------------------------------- | ------------------------------------------------------------- |
| `infra/migrations/001_multi_tenant.sql` | agencies + clients 表，pgvector 扩展，set_updated_at() 触发器 |
| `backend/app/models/agency.py`          | Agency ORM 模型，AgencyStatus / AgencyPlan 枚举               |
| `backend/app/models/client.py`          | Client ORM 模型，含 verticals ARRAY 字段                      |
| `backend/app/schemas/tenant.py`         | AgencyCreate / AgencyResponse / ClientCreate / ClientResponse |
| `backend/app/api/v1/tenants.py`         | Agency/Client CRUD API，slug 去重，agency_id 隔离校验         |

### 后续待实现 📋

| 任务                | 文件                                     |
| ------------------- | ---------------------------------------- |
| PostgreSQL RLS 策略 | `infra/migrations/001b_rls_policies.sql` |

---

## F-02 认证与授权（Auth + RBAC）

**优先级：P0**
**阶段：Phase 0**
**状态：✅ 已完成 — 2026-04-01（含 4 轮合规修复）**

### 已完成 ✅

| 文件                                        | 内容                                                              |
| ------------------------------------------- | ----------------------------------------------------------------- |
| `infra/migrations/002_auth.sql`             | users 表，user_role 枚举（agency_admin/agency_ops/client_viewer） |
| `infra/migrations/015_encrypt_user_pii.sql` | M-02/M-03：添加 email_hash 列，UNIQUE 索引                        |
| `backend/app/core/security.py`              | JWT 生成/验证/撤销（C-04：jti + Redis 黑名单），bcrypt 密码哈希   |
| `backend/app/core/pii_crypto.py`            | M-02/M-03：用户 PII Fernet 加密/解密 + email SHA-256 哈希         |
| `backend/app/models/user.py`                | User ORM（email/full_name 加密存储，email_hash 确定性查找）       |
| `backend/app/schemas/auth.py`               | LoginRequest / TokenResponse / UserResponse.from_user() 解密 PII  |
| `backend/app/api/v1/auth.py`                | M-10：IP 限流（5次/5分钟→锁15分钟）+ M-02：email_hash 查找        |
| `backend/app/core/deps.py`                  | get_current_user / get_current_agency_admin / get_agency_id       |

### 后续待实现 📋

| 任务                  | 说明                                       |
| --------------------- | ------------------------------------------ |
| Token 黑名单（Redis） | logout 时将 jti 写入 Redis blacklist       |
| Google 登录自动注册   | 首次 Google 登录时自动创建 agency_ops 用户 |

---

## F-03 凭证保险库（Credential Vault）

**优先级：P0**
**阶段：Phase 0**
**状态：✅ 已完成 — 2026-03-31**

### 已完成 ✅

| 文件                                          | 内容                                                   |
| --------------------------------------------- | ------------------------------------------------------ |
| `backend/app/core/encryption.py`              | Fernet 对称加密，encrypt_credentials / decrypt / mask  |
| `infra/migrations/003_credential_vault.sql`   | credentials 表，credential_type/status 枚举            |
| `backend/app/models/credential.py`            | Credential ORM 模型，scopes ARRAY，expires_at 字段     |
| `backend/app/schemas/credential.py`           | CredentialCreate / CredentialResponse（脱敏输出）      |
| `backend/app/api/v1/credentials.py`           | POST/GET/DELETE，加密存储，脱敏返回，agency_admin 权限 |
| `backend/app/services/oauth/token_refresh.py` | GA4/Meta/HubSpot/TikTok OAuth token 自动刷新           |

### 后续待实现 📋

| 任务         | 说明                               |
| ------------ | ---------------------------------- |
| 凭证健康巡检 | 定时任务，提前刷新临近过期的 token |

---

## F-04 审计日志（Audit Logging）

**优先级：P0 — GDPR 法律要求**
**阶段：Phase 0**
**状态：✅ 已完成 — 2026-03-31**

### 已完成 ✅

| 文件                                 | 内容                                                           |
| ------------------------------------ | -------------------------------------------------------------- |
| `infra/migrations/004_audit_log.sql` | audit_logs 表，BigSerial PK，prevent_audit_modification 触发器 |
| `backend/app/models/audit_log.py`    | AuditLog ORM 模型，contains_phi 标记，extra_data JSONB 字段    |
| `backend/app/core/audit.py`          | record_audit_event() 异步函数，从 request.state 提取上下文     |

### 后续待实现 📋

| 任务           | 说明                            |
| -------------- | ------------------------------- |
| 中间件自动记录 | 为所有 API 调用自动写入审计日志 |

---

## F-05 平台集成管理（Platform Integration Management）

**优先级：P0**
**阶段：Phase 0**
**状态：✅ 已完成 — 2026-03-31**

### 已完成 ✅

| 文件                                        | 内容                                                   |
| ------------------------------------------- | ------------------------------------------------------ |
| `infra/migrations/006_integrations.sql`     | integrations + sync_logs 表，integration_platform 枚举 |
| `backend/app/models/integration.py`         | Integration ORM 模型，credential_id 外键               |
| `backend/app/models/sync_log.py`            | SyncLog ORM 模型，BigSerial PK，extra_data 字段        |
| `backend/app/schemas/integration.py`        | ConnectRequest / IntegrationResponse / SyncLogResponse |
| `backend/app/services/platform_registry.py` | 12 平台静态注册表（auth_type, scopes 等）              |
| `backend/app/api/v1/integrations.py`        | 平台列表、连接/断开、同步触发、同步日志查询            |

**已注册平台（12个）：** GA4 · Meta Ads · HubSpot · TikTok · DV360 · StackAdapt · LeadRX · LiveRamp · Quorum · Canva · Adobe Firefly · Icon.app

### 后续待实现 📋

| 任务            | 说明                                 |
| --------------- | ------------------------------------ |
| OAuth 完整流程  | GA4/Meta/HubSpot 的 OAuth 授权回调   |
| Celery 同步任务 | trigger_sync 后真正执行 ETL 数据拉取 |

---

## F-06 ETL 数据管道（ETL Pipeline）

**优先级：P0**
**阶段：Phase 1**
**状态：✅ 已完成 — 2026-03-31**

### 已完成 ✅

| 文件                                            | 内容                                                             |
| ----------------------------------------------- | ---------------------------------------------------------------- |
| `backend/app/services/etl/base.py`              | BaseAdapter ABC + ETLResult dataclass，标准 fetch/transform 接口 |
| `backend/app/services/etl/runner.py`            | ETLRunner：fetch→PHI 检测→transform→WarehouseClient 写入         |
| `backend/app/services/etl/adapters/ga4.py`      | GA4Adapter：Google Analytics Data API v1，mock 模式支持          |
| `backend/app/services/etl/adapters/meta_ads.py` | MetaAdsAdapter：Meta Graph API v19，cursor 分页，mock 模式       |
| `backend/app/services/etl/adapters/hubspot.py`  | HubSpotAdapter：HubSpot CRM v3 Contacts，mock 模式               |
| `backend/app/core/compliance/phi_detector.py`   | scan_record() PHI 检测，集成到 ETL Runner                        |
| `backend/app/core/compliance/anonymizer.py`     | anonymize_record_for_warehouse() 匿名化，集成到 ETL Runner       |
| `backend/tests/test_etl.py`                     | 11 个测试用例，含三适配器端到端+PHI 合规，11/11 通过             |

### 待实现 📋（P2 适配器）

| 适配器     | 优先级 | 文件                                              |
| ---------- | ------ | ------------------------------------------------- |
| LeadRX     | P1     | `backend/app/services/etl/adapters/leadrx.py`     |
| TikTok Ads | P2     | `backend/app/services/etl/adapters/tiktok.py`     |
| DV360      | P2     | `backend/app/services/etl/adapters/dv360.py`      |
| StackAdapt | P2     | `backend/app/services/etl/adapters/stackadapt.py` |

---

## F-07 Canonical Event Schema + dbt 转换层

**优先级：P0 — 所有 AI Pillar 的数据基础**
**阶段：Phase 1**
**状态：✅ 已完成 — 2026-03-31**

### 已完成 ✅

| 文件                                             | 内容                                                                         |
| ------------------------------------------------ | ---------------------------------------------------------------------------- |
| `dbt/dbt_project.yml`                            | dbt 项目配置，三层物化策略（staging=view/canonical=incremental/marts=table） |
| `dbt/profiles.yml.example`                       | dev（DuckDB）/prod（Snowflake）双目标配置                                    |
| `dbt/models/staging/sources.yml`                 | 三个 raw 表 source 声明                                                      |
| `dbt/models/staging/stg_ga4.sql`                 | GA4 staging 层，标准化字段/bounce_rate 百分比                                |
| `dbt/models/staging/stg_meta_ads.sql`            | Meta Ads staging 层，派生 CTR/CPC/CPM/ROAS                                   |
| `dbt/models/staging/stg_hubspot.sql`             | HubSpot staging 层，联系人数据标准化                                         |
| `dbt/models/canonical/canonical_events.sql`      | Canonical Events 核心模型，UNION 三平台，增量模型                            |
| `dbt/models/marts/mart_campaign_performance.sql` | 活动绩效 mart，按 campaign+月份聚合                                          |
| `dbt/models/marts/mart_persona_signals.sql`      | Persona 信号 mart，按平台+周聚合供 AI 查询                                   |
| `dbt/macros/set_updated_at.sql`                  | set_updated_at() 宏                                                          |

### 待实现 📋

| 任务             | 文件                                        |
| ---------------- | ------------------------------------------- |
| Attribution Mart | `dbt/models/marts/mart_attribution.sql`     |
| 数据质量测试     | `dbt/models/canonical/canonical_events.yml` |

---

## F-08 Snowflake 数据仓库集成

**优先级：P0**
**阶段：Phase 1**
**状态：✅ 已完成 — 2026-03-31**

### 已完成 ✅

| 文件                                   | 内容                                                                 |
| -------------------------------------- | -------------------------------------------------------------------- |
| `backend/app/core/warehouse_client.py` | WarehouseClient 统一接口，`WAREHOUSE_BACKEND=duckdb\|snowflake` 切换 |
| `infra/migrations/005_token_usage.sql` | token_usage 表 + 月度聚合视图（BIGSERIAL PK，与 ORM 对齐）           |
| `backend/tests/test_warehouse.py`      | 7 个测试用例，DuckDB schema/insert/query/sync_state，7/7 通过        |

**三层 Schema（DuckDB 开发/Snowflake 生产兼容）：**

- `raw_ga4_events` / `raw_meta_ads` / `raw_hubspot_contacts` — ETL 原始写入区
- `etl_sync_state` — 增量同步游标状态
- staging/canonical/mart — 由 dbt 模型生成

**切换方式：**

```bash
WAREHOUSE_BACKEND=duckdb   # 本地开发（默认）
WAREHOUSE_BACKEND=snowflake  # 生产，需配置 SNOWFLAKE_* 环境变量
```

### 待实现 📋

| 任务                     | 文件                                       |
| ------------------------ | ------------------------------------------ |
| Snowflake Raw Schema DDL | `infra/snowflake/raw_tables.sql`           |
| 数据加载服务（ETL集成）  | `backend/app/services/warehouse/loader.py` |

---

## F-09 Core AI Brain（LLM 路由器）

**优先级：P1**
**阶段：Phase 1**
**状态：✅ 已完成 — 2026-03-31**

### 已完成 ✅

| 文件                                     | 内容                                                                       |
| ---------------------------------------- | -------------------------------------------------------------------------- |
| `infra/migrations/005_token_usage.sql`   | token_usage 表（BIGSERIAL PK，nullable 字段）+ 月度视图                    |
| `backend/app/models/token_usage.py`      | TokenUsage ORM 模型，BigInteger PK，agency/client/user FK                  |
| `backend/app/services/ai/context.py`     | build_shared_context()：读 Agency 配置 + 当月 token 用量 → SharedContext   |
| `backend/app/services/ai/brain.py`       | LLM 路由器，agent 分发，token 追踪，审计日志，结构化输出                   |
| `backend/app/services/ai/agents/base.py` | BaseAgent ABC + AgentResponse dataclass                                    |
| `backend/app/schemas/ai.py`              | AIRequest / AIResponse / MonthlyUsageSummary Pydantic 模型                 |
| `backend/app/api/v1/ai.py`               | POST /ai/chat（预算检查→OpenRouter→写 token_usage）+ GET /ai/usage/monthly |
| `backend/app/api/v1/router.py`           | ai_router 已注册                                                           |
| `backend/tests/test_ai.py`               | 7 个测试用例：认证/成功/预算超限 429/月度聚合，7/7 通过                    |

### 待实现 📋

| 任务              | 文件                          |
| ----------------- | ----------------------------- |
| Redis Prompt 缓存 | 集成到 brain.py 或 context.py |

---

## F-10 Persona Agent（Pillar 1 — 市场研究智能）

**优先级：P1**
**阶段：Phase 2**
**状态：✅ 已完成 — 2026-03-31**

### 已完成 ✅

| 文件                                        | 内容                                                                       |
| ------------------------------------------- | -------------------------------------------------------------------------- |
| `infra/migrations/009_persona_agent.sql`    | 添加 agency_id/source/model_used/is_active 到 personas 表                  |
| `backend/app/models/persona.py`             | Persona ORM（agency-scoped），支持 psychographics/channel_preferences JSON |
| `backend/app/services/ai/agents/persona.py` | Persona Agent（Claude Opus），结构化 persona 生成 + mock fallback          |
| `backend/app/schemas/persona.py`            | Create/Update/Response/GenerateRequest                                     |
| `backend/app/api/v1/personas.py`            | 6 端点：list/create/generate/get/update/delete                             |
| `backend/tests/test_personas.py`            | 9 个测试用例，9/9 通过                                                     |

### 待实现 📋（P2 增强）

| 任务               | 说明                                     |
| ------------------ | ---------------------------------------- |
| Warehouse 查询工具 | 从 DuckDB/Snowflake 提取分析数据辅助生成 |
| 受众导出           | Meta Ads / DV360 受众同步                |
| Persona UI         | React 前端组件                           |

---

## F-11 Creative Agent（Pillar 2 — 创意内容引擎）

**优先级：P1**
**阶段：Phase 2**
**状态：✅ 已完成 — 2026-03-31**

### 已完成 ✅

| 文件                                         | 内容                                                            |
| -------------------------------------------- | --------------------------------------------------------------- |
| `infra/migrations/010_creative_agent.sql`    | 添加 agency_id/agent_type/metadata 到 generations 表            |
| `backend/app/models/creative.py`             | Generation + GenerationResult ORM，复用已有 DB enum             |
| `backend/app/services/ai/agents/creative.py` | Creative Agent（Claude Sonnet），四平台文案生成 + mock fallback |
| `backend/app/schemas/creative.py`            | GenerationCreate/GenerationResponse/GenerationResultResponse    |
| `backend/app/api/v1/creatives.py`            | 3 端点：generate/list/get                                       |
| `backend/tests/test_creatives.py`            | 8 个测试用例，8/8 通过                                          |

### 待实现 📋（P2 增强）

| 任务           | 说明                           |
| -------------- | ------------------------------ |
| 图片生成       | Adobe Firefly / Canva API 集成 |
| 品牌合规过滤器 | 检查文案是否符合品牌指南       |
| 异步生成       | Celery 任务 + SSE 进度推送     |
| Creative UI    | React 前端组件                 |

---

## F-12 Attribution Agent（Pillar 3 — 归因测量）

**优先级：P1**
**阶段：Phase 3**
**状态：✅ 已完成 — 2026-03-31**

### 已完成 ✅

| 文件                                            | 内容                                                           |
| ----------------------------------------------- | -------------------------------------------------------------- |
| `infra/migrations/012_attribution_agent.sql`    | 创建 attribution_reports 表 + 索引                             |
| `backend/app/models/attribution.py`             | AttributionReport ORM（agency-scoped）                         |
| `backend/app/services/ai/agents/attribution.py` | Attribution Agent（Claude Sonnet），DuckDB 数据查询 + 归因分析 |
| `backend/app/schemas/attribution.py`            | AttributionReportCreate/AttributionReportResponse              |
| `backend/app/api/v1/attribution.py`             | 3 端点：report/reports/reports/{id}                            |
| `backend/tests/test_attribution.py`             | 9 个测试用例，9/9 通过                                         |

### 待实现 📋（P2 增强）

| 任务                 | 说明                 |
| -------------------- | -------------------- |
| LeadRX 适配器        | 第三方归因数据源 ETL |
| LiveRamp 适配器      | 跨设备归因           |
| PDF 报告生成         | 导出归因报告 PDF     |
| dbt Attribution Mart | mart_attribution.sql |
| Attribution UI       | React 前端组件       |

---

## F-13 品牌入驻系统（Brand Onboarding）

**优先级：P1**
**阶段：Phase 1**
**状态：✅ 已完成 — 2026-03-31**

### 已完成 ✅

| 文件                           | 内容                                                                    |
| ------------------------------ | ----------------------------------------------------------------------- |
| `backend/app/schemas/brand.py` | BrandConfigUpdate / BrandConfigResponse，PATCH 语义，9 个可选字段       |
| `backend/app/api/v1/brands.py` | GET / PUT / DELETE `/brands/config`，存储于 agencies.brand_config JSONB |
| `backend/tests/test_brands.py` | 7 个测试用例，7/7 通过                                                  |

### 待实现 📋（P2 增强）

| 任务         | 说明                     |
| ------------ | ------------------------ |
| Logo 上传    | 文件上传替代 URL 存储    |
| 变更审计日志 | 品牌配置修改记录到审计表 |
| 品牌入驻 UI  | React 前端组件           |

---

## F-14 历史数据手动导入（Historical Import）

**优先级：P1**
**阶段：Phase 1**
**状态：✅ 已完成 — 2026-03-31**

### 已完成 ✅

| 文件                                              | 内容                                                             |
| ------------------------------------------------- | ---------------------------------------------------------------- |
| `backend/app/services/etl/historical_importer.py` | CSV 解析、平台自动检测（detect_format）、字段规范化、DuckDB 写入 |
| `backend/app/schemas/import_schema.py`            | ImportResponse：platform/rows_imported/rows_skipped/message      |
| `backend/app/api/v1/imports.py`                   | POST `/import/upload`，multipart，最大 50MB，支持三平台          |
| `backend/tests/test_imports.py`                   | 9 个测试用例，9/9 通过                                           |

**支持格式：** meta_ads · ga4 · hubspot（自动检测或手动指定）

### 待实现 📋（P2 增强）

| 任务         | 说明                           |
| ------------ | ------------------------------ |
| 更多平台     | tiktok_ads / dv360 / shopify   |
| 异步进度     | 大文件 Celery 任务 + WebSocket |
| 重复数据检测 | date + campaign_id 去重        |

---

## F-15 字段映射系统（Field Mapping）

**优先级：P1**
**阶段：Phase 1**
**状态：✅ 已完成 — 2026-03-31**

### 已完成 ✅

| 文件                                                     | 内容                                                                         |
| -------------------------------------------------------- | ---------------------------------------------------------------------------- |
| `backend/app/models/field_mapping.py`                    | FieldMapping + FieldMappingVersion ORM，agency 多租户                        |
| `backend/app/services/field_mapping/canonical_schema.py` | 24 个标准字段，6 类别（time/identity/performance/engagement/revenue/custom） |
| `backend/app/services/field_mapping/transform.py`        | TransformEngine：direct/value_mapping/unit_conversion/formula                |
| `backend/app/services/field_mapping/template_loader.py`  | 模板加载，list_supported_platforms()                                         |
| `backend/app/services/field_mapping/templates/`          | ga4/meta_ads/hubspot/tiktok_ads/dv360/stackadapt 六个 JSON 模板              |
| `backend/app/schemas/field_mapping.py`                   | 9 个 Pydantic 模型                                                           |
| `backend/app/api/v1/field_mappings.py`                   | 10 个端点：CRUD + /versions + /rollback + /preview + canonical-schema        |
| `infra/migrations/008_field_mapping_agency.sql`          | 添加 agency_id FK + platform 列，保留 tenant_id 兼容                         |
| `backend/tests/test_field_mappings.py`                   | 14 个测试用例，14/14 通过                                                    |

### 待实现 📋（P2 增强）

| 任务             | 说明                              |
| ---------------- | --------------------------------- |
| ETL 深度集成     | ETL runner 自动应用字段映射       |
| 公共模板库       | 跨 Agency 共享标准模板            |
| formula 沙箱强化 | 替换 AST 白名单为更严格的沙箱执行 |

---

## F-16 客户门户（Client Portal）

**优先级：P2**
**阶段：Phase 3**
**状态：✅ 已完成 — 2026-03-31**

### 已完成 ✅

| 文件                           | 内容                                                      |
| ------------------------------ | --------------------------------------------------------- |
| `backend/app/api/v1/portal.py` | 5 个只读端点：dashboard/brand/personas/creatives/reports  |
| `backend/app/core/deps.py`     | get_current_client_viewer() + get_portal_user() RBAC 依赖 |
| `backend/tests/test_portal.py` | 8 个测试用例，8/8 通过                                    |

### 待实现 📋（前端）

| 任务         | 说明                            |
| ------------ | ------------------------------- |
| PortalLayout | React 门户布局组件              |
| 白标主题     | brand_config → CSS 变量动态注入 |
| 客户仪表板   | ClientDashboard.tsx 前端        |

---

## F-17 实时通知（WebSocket）

**优先级：P2**
**阶段：Phase 3**
**状态：✅ 已完成 — 2026-03-31**

### 已完成 ✅

| 文件                                               | 内容                                              |
| -------------------------------------------------- | ------------------------------------------------- |
| `infra/migrations/013_notifications.sql`           | notifications 表 + 索引                           |
| `backend/app/models/notification.py`               | Notification ORM                                  |
| `backend/app/services/notifications/manager.py`    | WebSocket ConnectionManager（内存级全局单例）     |
| `backend/app/services/notifications/dispatcher.py` | create_notification()（写 DB + WS 推送）          |
| `backend/app/schemas/notification.py`              | NotificationResponse / NotificationMarkRead       |
| `backend/app/api/v1/notifications.py`              | 4 端点：list/unread-count/mark-read/mark-all-read |
| `backend/app/api/v1/ws.py`                         | WebSocket /ws?token=JWT（认证 + 心跳）            |
| `backend/tests/test_notifications.py`              | 9 个测试用例，9/9 通过                            |

### 待实现 📋（增强）

| 任务          | 说明                  |
| ------------- | --------------------- |
| Redis Pub/Sub | 多实例 WebSocket 广播 |
| 前端 Hook     | useWebSocket.ts       |
| Email 渠道    | 通知 Email 发送       |

---

## F-18 监控与可观测性（Observability）

**优先级：P2**
**阶段：Phase 0 补完**
**状态：✅ 已完成 — 2026-03-31**

### 已完成 ✅

| 文件                                  | 内容                                                                             |
| ------------------------------------- | -------------------------------------------------------------------------------- |
| `backend/app/core/monitoring.py`      | `init_sentry()`、`get_langfuse()` 单例、`RequestLoggingMiddleware` 请求 ID 注入  |
| `backend/app/core/health.py`          | `ComponentHealth` dataclass、DB/Redis/Warehouse 检查、`full_health_check()` 聚合 |
| `backend/app/api/v1/health.py`        | `GET /health` 深度检查端点（无需认证，down=503/degraded=200）                    |
| `backend/app/api/v1/ai.py`            | Langfuse trace 注入（无 key 时静默跳过）                                         |
| `backend/app/main.py`                 | Sentry 迁移至 monitoring.py，注册 RequestLoggingMiddleware，health router        |
| `backend/tests/test_observability.py` | 10 个测试用例，覆盖健康检查/X-Request-Id/Langfuse 降级/Sentry 无崩溃，10/10 通过 |

### 合规说明

- Sentry 设置 `send_default_pii=False`（不上报请求体，防止 PHI 泄露）
- Langfuse 仅追踪 LLM 调用元数据（model/tokens），不传输用户 prompt 内容到外部

### 待实现 📋

| 任务                                        | 优先级 |
| ------------------------------------------- | ------ |
| Prometheus 指标暴露 `/metrics`              | P2     |
| 告警规则（DB 连接池耗尽、token 预算超 80%） | P2     |

---

## 开发执行路径

### Phase 0 — 基础设施层（约 2 周）

> **目标：** 搭建可运行的全栈开发环境，所有 P0 基础模块就绪。

```
优先顺序：
1. Docker Compose 环境验证（已有 docker-compose.yml）
2. F-01 数据库迁移 001-004（已有 001，需补 002-004）
3. F-02 认证系统（JWT + Google OAuth 从 IQ 迁移）
4. F-03 凭证保险库（encryption.py 已有，迁移其余部分）
5. F-04 审计日志中间件
6. F-05 平台集成管理（从 IQ 迁移）
7. F-00 合规中间件注册 + DSAR API
8. F-18 Sentry 初始化（顺手做）
```

### Phase 1 — 数据层 + AI 基础（约 4 周）

> **目标：** 数据能流入 Snowflake，AI Brain 可查询数据。

```
优先顺序：
1. F-08 Snowflake 连接 + Raw Schema
2. F-07 dbt staging 模型（GA4/Meta）
3. F-06 GA4 适配器升级（写 Snowflake 替代 PostgreSQL）
4. F-06 Meta Ads 适配器（新建）
5. F-07 canonical_events 模型测试验证
6. F-09 AI Brain 完善（Context 组装器、缓存）
7. F-13 品牌入驻系统
8. F-15 字段映射（从 IQ 迁移）
9. F-14 历史数据导入
```

### Phase 2 — Pillar 1 & 2（约 4 周）

> **目标：** Persona + Creative 两个核心 Pillar MVP 可演示。

```
优先顺序：
1. F-10 Persona Agent（依赖 mart_persona_signals dbt 模型）
2. F-11 Creative Agent（依赖 Persona 输出）
3. Canva / Adobe Firefly 集成
4. Persona UI + Creative UI
```

### Phase 3 — Pillar 3 + 客户门户（约 4 周）

> **目标：** 归因闭环，客户可自助查看报告。

```
优先顺序：
1. F-12 LeadRX + LiveRamp 适配器
2. F-12 Attribution Agent + 报告 PDF
3. F-16 客户门户（白标主题）
4. F-17 WebSocket 实时推送
5. 合规审查：DSAR 端对端测试、数据保留任务验证
```

---

## 基础设施文件完成状态

| 文件                                           | 状态                                                                          |
| ---------------------------------------------- | ----------------------------------------------------------------------------- |
| `docker-compose.yml`                           | ✅ 已有（9 服务：backend, celery, frontend, redis, minio, langfuse, airflow） |
| `.env.example`                                 | ✅ 已有（所有变量已定义）                                                     |
| `infra/migrations/001_multi_tenant.sql`        | ✅ 已有                                                                       |
| `infra/migrations/002_auth.sql`                | ✅ 已有（users 表，user_role 枚举）                                           |
| `infra/migrations/003_credential_vault.sql`    | ✅ 已有（credentials 表，Fernet 加密）                                        |
| `infra/migrations/004_audit_log.sql`           | ✅ 已有（audit_logs 表，INSERT-only 触发器）                                  |
| `infra/migrations/005_token_usage.sql`         | ✅ 已有                                                                       |
| `infra/migrations/006_integrations.sql`        | ✅ 已有（integrations + sync_logs 表）                                        |
| `infra/migrations/007_brand_config.sql`        | 📋 待建                                                                       |
| `infra/migrations/008_personas.sql`            | 📋 待建                                                                       |
| `infra/migrations/009_creatives.sql`           | 📋 待建                                                                       |
| `infra/migrations/010_attribution.sql`         | 📋 待建                                                                       |
| `infra/migrations/011_compliance.sql`          | ✅ 已有                                                                       |
| `dbt/models/canonical/canonical_events.sql`    | ✅ 已有                                                                       |
| `dbt/models/staging/stg_ga4.sql`               | 📋 待建                                                                       |
| `dbt/models/staging/stg_meta_ads.sql`          | 📋 待建                                                                       |
| `dbt/models/staging/stg_hubspot.sql`           | 📋 待建                                                                       |
| `backend/app/services/ai/brain.py`             | ✅ 已有                                                                       |
| `backend/app/core/compliance/anonymizer.py`    | ✅ 已有                                                                       |
| `backend/app/core/compliance/phi_detector.py`  | ✅ 已有                                                                       |
| `backend/app/core/compliance/session_guard.py` | ✅ 已有                                                                       |
| `features/compliance/architecture.md`          | ✅ 已有                                                                       |

---

## 关键依赖关系

```
F-01（多租户）
    ↓
F-02（认证）  F-03（凭证）  F-04（审计）  F-00（合规）
    ↓               ↓
F-05（平台集成）  F-08（Snowflake）
    ↓               ↓
F-06（ETL 管道）→ F-07（dbt Canonical Schema）
                    ↓
              F-09（AI Brain）
              ↙      ↓       ↘
         F-10      F-11      F-12
       （Persona） （Creative） （Attribution）
                                ↓
                           F-16（客户门户）
```

所有 P0 模块必须在 P1 模块开始前完成。F-07 Canonical Schema 是 AI 三个 Pillar 共同的数据基础。

---

_最后更新：2026-03-31 | P0 全部完成（27/27 测试通过）_
