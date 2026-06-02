[English](README.md) | **中文**

# ReceptivIQ Platform

> AI-native Agency OS — GDPR · CCPA · HIPAA 合规的营销代理智能运营平台

_最后更新:**2026-05-21**_

---

## 架构速览

### 技术架构 — 开发环境分层栈

![开发环境分层架构](docs/diagrams/dev-stack-layered.png)

> 本地开发栈分层视图:Docker Compose 容器编排 · 热重载工具链 · 外部依赖 Mock · 开发面板可观测性。逐层术语解释见 [`docs/diagrams/env-stack-glossary.md`](docs/diagrams/env-stack-glossary.md)。
> 源码:[`docs/diagrams/dev-stack-layered.py`](docs/diagrams/dev-stack-layered.py)。

### 技术架构 — 生产环境分层栈

![生产环境分层架构](docs/diagrams/prod-stack-layered.png)

> 生产栈分层视图:托管 Postgres / Snowflake / S3 · Render 托管服务 · 异步 Celery Worker · 真实第三方凭据接入的 ETL adapter · 完整可观测性(Langfuse + Sentry + 审计管线)。
> 源码:[`docs/diagrams/prod-stack-layered.py`](docs/diagrams/prod-stack-layered.py)。

### 客户向架构图(销售 / 高管演示)

![平台架构图](docs/psd/architecture-schema.png)

> PSD 级架构图,面向客户与审计师 — 呈现 3-Lake Medallion(Landing / Raw PII / Processed)、PII 边界、共享参考湖、dbt 5 层转换、AI Agent 平面,以及合规覆盖层(审计/DSAR/留存)。
> 源码:[`docs/psd/architecture-schema.svg`](docs/psd/architecture-schema.svg) · 说明:[`docs/psd/architecture-schema-explained.md`](docs/psd/architecture-schema-explained.md)。

### 数据流水线(ELT)端到端

![数据流水线架构](docs/diagrams/data-pipeline.svg)

> **9 个三方平台 → Airflow + Python adapters → 合规闸口 → Snowflake(Load)→ dbt 仓内 Transform → FastAPI → PostgreSQL → React 客户端。** 包含 DevOps(GitHub → Render / Docker)与可观测(Langfuse / Sentry / SMTP / S3)全套集成。

### 系统上下文

![系统上下文图](docs/diagrams/system-context.svg)

> 3 类用户角色 · 1 个多租户 SaaS 核心 · 9 个外部数据源 · 2 条 LLM 通道(OpenRouter + 计划中的 AWS Bedrock HIPAA 旁路) · 3 个运维集成。
> 实现细节见 [docs/ARCHITECTURE-DEEP-DIVE.md](docs/ARCHITECTURE-DEEP-DIVE.md);8 视角完整图集见 [docs/ARCHITECTURE-DIAGRAM.md](docs/ARCHITECTURE-DIAGRAM.md)。

---

## 项目概述

ReceptivIQ 是一个面向营销代理公司的全栈 SaaS 平台，集成了 AI 驱动的受众洞察、创意生成和归因分析三大核心能力（三支柱架构）。平台以合规为设计基石，从数据采集到 AI 推理的每一层都内置了 GDPR/CCPA/HIPAA 合规控制。

**技术栈**：FastAPI · SQLAlchemy 2.0 · Neon Postgres · DuckDB/Snowflake · Redis · Celery · Airflow · dbt · OpenRouter (LLM) · MinIO · React · Vite · Render (部署)

---

## 目录结构

```
ReceptivIQ-Platform/
├── backend/                    # Python 后端（FastAPI）
│   ├── app/
│   │   ├── api/v1/            # REST API 路由层
│   │   ├── core/              # 基础设施（配置、数据库、安全、合规）
│   │   ├── models/            # SQLAlchemy ORM 模型
│   │   ├── schemas/           # Pydantic 请求/响应模型
│   │   ├── services/          # 业务逻辑层
│   │   └── tasks/             # Celery 异步任务
│   ├── worker.py              # Celery App 入口
│   ├── tests/                 # 测试套件（189 个用例）
│   ├── dags/                  # Airflow DAG 定义（etl_sync_dag.py）
│   ├── Dockerfile             # 后端容器镜像（Python 3.9-slim）
│   ├── requirements.txt       # Python 依赖
│   └── pytest.ini             # 测试配置
├── frontend/                   # React 前端（Vite + TypeScript）
│   └── src/
│       ├── api/               # Axios HTTP 客户端
│       ├── apps/              # 页面级应用（ops 运营端 / portal 客户端）
│       ├── components/        # 可复用 UI 组件
│       └── hooks/             # 自定义 React Hooks
├── dbt/                        # 数据转换层（dbt）
│   ├── models/
│   │   ├── staging/           # 平台原始数据标准化
│   │   ├── canonical/         # 跨平台统一事件 Schema
│   │   └── marts/             # 业务聚合层（Campaign/Persona）
│   └── macros/                # dbt 宏
├── infra/                      # 基础设施
│   ├── migrations/            # PostgreSQL 迁移脚本（16 个，含合规迁移 + Campaign 配置）
│   └── snowflake/             # Snowflake 初始化脚本
├── features/                   # 功能模块文档
│   ├── PROJECT-PLAN.md        # 项目总规划
│   ├── DEV-FRAMEWORK.md       # 开发框架文档（21 模块状态）
│   └── f10-f18, p0, p1/      # 各模块完成报告 + 测试报告
├── docker-compose.yml          # Docker 服务编排
└── .env.example                # 环境变量模板
```

---

## 后端详细结构

### `backend/app/core/` — 基础设施层

| 文件                          | 说明                                                                                                |
| ----------------------------- | --------------------------------------------------------------------------------------------------- |
| `config.py`                   | Pydantic Settings 配置加载（数据库、Redis、AI 模型、Snowflake 等）；H-06 修复：Airflow 凭证无默认值 |
| `database.py`                 | SQLAlchemy 异步引擎 + 会话工厂（asyncpg）                                                           |
| `sync_database.py`            | 同步引擎（供 Celery Worker 使用）                                                                   |
| `security.py`                 | JWT 创建/解码/撤销 + 密码哈希（bcrypt）+ jti 黑名单（Redis 优先 + 内存 fallback）                   |
| `encryption.py`               | Fernet 对称加密（凭证保险库用）                                                                     |
| `pii_crypto.py`               | M-02/M-03：用户 PII 加密/解密（Fernet）+ email SHA-256 哈希（确定性查找）                           |
| `deps.py`                     | FastAPI 依赖注入（get_current_user / get_current_agency_admin / get_portal_user）                   |
| `audit.py`                    | 审计日志记录（record_audit_event + audit_simple）；L-03 修复：extra_data 字段名                     |
| `health.py`                   | 深度健康检查（DB/Redis/Warehouse 三组件状态聚合）                                                   |
| `monitoring.py`               | Sentry 初始化 + Langfuse 懒加载单例 + RequestLoggingMiddleware                                      |
| `warehouse_client.py`         | DuckDB/Snowflake 双后端仓库客户端；H-02/H-03：SQL 语句前缀白名单防注入                              |
| `storage.py`                  | MinIO 对象存储客户端（懒加载单例，upload/presigned_url/delete）                                     |
| `compliance/anonymizer.py`    | PII 匿名化（hash_identifier / mask_email / truncate_ip / scrub_pii_from_logs）                      |
| `compliance/phi_detector.py`  | PHI 检测器（HIPAA Safe Harbor 18 类标识符扫描）                                                     |
| `compliance/session_guard.py` | HIPAA 会话超时中间件（15 分钟）；M-05：Redis 不可用时自动降级内存 LRU 缓存                          |

### `backend/app/models/` — 数据模型（17 个 ORM 模型）

| 文件               | 模型                               | 说明                                                                         |
| ------------------ | ---------------------------------- | ---------------------------------------------------------------------------- |
| `agency.py`        | Agency                             | 代理公司（顶层租户，含 brand_config JSONB、monthly_token_budget）            |
| `client.py`        | Client                             | 客户品牌（属于 Agency，含独立 brand_config 用于白标）                        |
| `user.py`          | User                               | 用户（三角色 RBAC）；M-02/M-03：email/full_name Fernet 加密，email_hash 查找 |
| `credential.py`    | Credential                         | 加密凭证存储（Fernet 加密 OAuth token / API key）                            |
| `integration.py`   | Integration                        | 平台集成记录（GA4/Meta/HubSpot 等 12 个平台）                                |
| `sync_log.py`      | SyncLog                            | ETL 同步日志（状态追踪 + 错误记录）                                          |
| `consent.py`       | ConsentRecord                      | GDPR/CCPA 同意记录（subject_hash 哈希存储，IP 截断 /24）                     |
| `dsar.py`          | DSARRequest                        | 数据主体访问请求（subject_email_hash 哈希存储，数据最小化）                  |
| `audit_log.py`     | AuditLog                           | 审计日志（INSERT-only，含 IP/UA/contains_phi/extra_data）                    |
| `token_usage.py`   | TokenUsage                         | LLM Token 用量追踪（按 agency/model/agent 维度）                             |
| `field_mapping.py` | FieldMapping + FieldMappingVersion | 字段映射（版本管理 + 回滚支持）                                              |
| `persona.py`       | Persona                            | 市场画像；L-01 修复：agency_id NOT NULL 强制租户隔离                         |
| `creative.py`      | Generation + GenerationResult      | 创意内容（Generation 1:N GenerationResult 多平台）                           |
| `attribution.py`   | AttributionReport                  | 归因报告（channels/results JSONB，多触点归因）                               |
| `notification.py`  | Notification                       | 通知消息（分类/严重度/已读状态）                                             |
| `campaign.py`      | CampaignBudgetConfig               | 预算配置与告警规则（唯一约束 agency+platform+campaign）                      |
| `enums.py`         | —                                  | 共享枚举（IntegrationPlatform/AuthType/SyncStatus 等）                       |

### `backend/app/schemas/` — Pydantic Schema（15 个模块）

| 文件               | 说明                                                                                              |
| ------------------ | ------------------------------------------------------------------------------------------------- |
| `auth.py`          | LoginRequest / TokenResponse / UserResponse（from_user 自动解密 PII）                             |
| `tenant.py`        | AgencyCreate / ClientCreate / AgencyResponse                                                      |
| `compliance.py`    | ConsentCreate / DSARCreate / ConsentResponse / DSARResponse                                       |
| `credential.py`    | CredentialCreate / CredentialResponse                                                             |
| `integration.py`   | IntegrationConnect / IntegrationResponse                                                          |
| `ai.py`            | AIRequest / AIResponse / MonthlyUsageSummary                                                      |
| `brand.py`         | BrandConfigUpdate / BrandConfigResponse                                                           |
| `persona.py`       | PersonaCreate / PersonaUpdate / PersonaResponse / PersonaGenerateRequest                          |
| `creative.py`      | GenerationCreate / GenerationResponse / GenerationResultResponse                                  |
| `attribution.py`   | AttributionReportCreate / AttributionReportResponse                                               |
| `field_mapping.py` | MappingEntry / FieldMappingCreate / FieldMappingUpdate；L-02：config 大小限制 + 条目数限制        |
| `import_schema.py` | ImportResponse                                                                                    |
| `notification.py`  | NotificationResponse / NotificationMarkRead                                                       |
| `campaign.py`      | CampaignMetric / CampaignSummary / BudgetConfigCreate / BudgetConfigUpdate / BudgetConfigResponse |

### `backend/app/api/v1/` — API 路由（18 个路由模块）

| 文件                | 前缀                  | 端点数 | 说明                                                           |
| ------------------- | --------------------- | ------ | -------------------------------------------------------------- |
| `auth.py`           | `/auth`               | 5      | 登录/OAuth/刷新/登出/me；M-10：IP 限流 + M-02：email_hash 查找 |
| `tenants.py`        | `/agencies`           | 5      | Agency + Client CRUD                                           |
| `credentials.py`    | `/credentials`        | 3      | 凭证加密存储 CRUD                                              |
| `integrations.py`   | `/integrations`       | 4      | 平台连接/断开/同步触发（Celery 分发）                          |
| `oauth_callback.py` | `/integrations/oauth` | 2      | 平台 OAuth 授权 URL + callback（HMAC CSRF 防护）               |
| `compliance.py`     | `/compliance`         | 5      | Consent 管理 + DSAR 工作流（agency_id 强制隔离）               |
| `ai.py`             | `/ai`                 | 2      | AI Chat（OpenRouter）+ 月度用量摘要                            |
| `brands.py`         | `/brands`             | 3      | 品牌配置 GET/PUT/DELETE（PATCH 语义）                          |
| `imports.py`        | `/import`             | 1      | CSV 历史数据上传（自动格式检测）                               |
| `field_mappings.py` | `/field-mappings`     | 10     | CRUD + 版本管理 + 回滚 + 预览 + 模板                           |
| `personas.py`       | `/personas`           | 6      | 手动/AI 创建 + CRUD + 软删除                                   |
| `creatives.py`      | `/creatives`          | 3      | AI 生成多平台创意 + 列表 + 详情                                |
| `attribution.py`    | `/attribution`        | 3      | AI 归因报告生成 + 列表 + 详情                                  |
| `portal.py`         | `/portal`             | 5      | 客户门户只读视图（精简字段，白标支持）                         |
| `notifications.py`  | `/notifications`      | 4      | 通知列表/未读计数/标记已读/全部已读                            |
| `campaigns.py`      | `/campaigns`          | 9      | 跨平台 Campaign 聚合视图 + Budget Config CRUD + 告警           |
| `reports.py`        | `/reports`            | 7      | PDF 报告调度 CRUD + 手动生成 + 历史 + 下载                     |
| `health.py`         | `/health`             | 1      | 深度健康检查（无需认证）                                       |
| `ws.py`             | `/ws`                 | 1      | WebSocket 实时连接（JWT 认证 + 心跳）                          |

### `backend/app/services/` — 业务逻辑层

#### AI 服务 (`services/ai/`)

| 文件                    | 说明                                                                                  |
| ----------------------- | ------------------------------------------------------------------------------------- |
| `brain.py`              | 中心 LLM 路由器（AgentRequest → 分发 persona/creative/attribution → 记录用量 + 审计） |
| `context.py`            | SharedContext 组装器（品牌配置 + Token 预算 + 历史摘要）                              |
| `agents/base.py`        | BaseAgent 抽象基类                                                                    |
| `agents/persona.py`     | Persona Agent — Claude Opus 生成结构化画像（含 mock fallback）                        |
| `agents/creative.py`    | Creative Agent — Claude Sonnet 四平台文案生成（含 Persona 上下文注入）                |
| `agents/attribution.py` | Attribution Agent — Claude Sonnet 多触点归因分析（DuckDB 数据查询）                   |

#### AI / LLM 架构（OpenRouter）

平台通过 [OpenRouter](https://openrouter.ai) 统一接入大模型，实现模型路由、Token 计费和预算控制。

```
用户请求 → /api/v1/ai/chat 或 /personas/generate 等
              │
              ▼
        ┌─────────────┐     ┌──────────────────┐
        │  AI Brain    │────▶│  OpenRouter API   │──▶ Claude Opus / Sonnet
        │  (brain.py)  │     │  (统一入口)       │     GPT-4 / Gemini 等
        └──────┬───────┘     └──────────────────┘
               │
        ┌──────▼───────┐
        │ TokenUsage    │  每次调用记录：
        │ (token_usage) │  agency_id / model / prompt_tokens / completion_tokens / cost
        └──────────────┘
```

**关键设计**：

| 特性                | 说明                                                                                  |
| ------------------- | ------------------------------------------------------------------------------------- |
| **统一模型路由**    | 所有 LLM 调用走 OpenRouter API，支持一个 API Key 调用多个模型供应商                   |
| **按 Agent 选模型** | Persona Agent → Claude Opus（深度推理），Creative/Attribution → Claude Sonnet（高效） |
| **Token 预算控制**  | 每个 Agency 有 `monthly_token_budget`，耗尽时返回 429                                 |
| **用量追踪**        | 每次调用记录到 `token_usage` 表，支持按模型/Agent/月份聚合查询                        |
| **成本估算**        | 基于 OpenRouter 定价自动估算 `estimated_cost_usd`                                     |
| **Mock 模式**       | `OPENROUTER_API_KEY` 为空时，所有 Agent 返回 mock 数据（本地开发零成本）              |
| **Langfuse 追踪**   | 可选集成 Langfuse，追踪每次 LLM 调用的 prompt/completion/延迟                         |

**模型配置**（在 `.env` 或 Render 环境变量中设置）：

```bash
OPENROUTER_API_KEY=sk-or-v1-...              # OpenRouter API 密钥
PERSONA_MODEL=anthropic/claude-opus-4-6       # Persona Agent 使用的模型
CREATIVE_MODEL=anthropic/claude-sonnet-4-6    # Creative Agent 使用的模型
ATTRIBUTION_MODEL=anthropic/claude-sonnet-4-6 # Attribution Agent 使用的模型
OPENROUTER_TEXT_MODEL=anthropic/claude-sonnet-4-6  # AI Chat 通用模型
```

> 可在 [OpenRouter Models](https://openrouter.ai/models) 查看所有可用模型和定价。切换模型只需改环境变量，无需修改代码。

**Token 用量 API**：

```
GET /api/v1/ai/usage/monthly
→ { total_tokens, total_cost_usd, budget, budget_remaining, by_model, by_agent }
```

#### ETL 服务 (`services/etl/`) + Airflow 调度

ETL 管道由 [Apache Airflow](https://airflow.apache.org) 调度执行，数据流经合规层后写入数据仓库：

```
Airflow Scheduler
    │
    ▼
┌─────────────────────────────────────────────────────┐
│  ETL DAG（每日/手动触发）                            │
│                                                      │
│  1. Adapter.fetch()     从平台 API 拉取原始数据      │
│     ├── GA4 Adapter     (Google Analytics Data API)  │
│     ├── Meta Ads Adapter (Graph API v19)             │
│     └── HubSpot Adapter  (CRM v3 Contacts)          │
│                                                      │
│  2. PHI 检测            scan_record() HIPAA 扫描     │
│  3. 匿名化              anonymize_for_warehouse()   │
│  4. 字段映射            TransformEngine 规范化       │
│  5. 仓库写入            DuckDB / Snowflake          │
│                                                      │
│  6. dbt 转换            staging → canonical → marts  │
└─────────────────────────────────────────────────────┘
```

**Airflow 配置**（`docker-compose.yml` 中包含 webserver + scheduler + init）：

| 组件                | 说明                                                       |
| ------------------- | ---------------------------------------------------------- |
| `airflow-init`      | 初始化 DB + 创建 admin 用户 + 安装 Python 依赖             |
| `airflow-webserver` | Web UI（`http://localhost:8080`），管理 DAG 和查看任务日志 |
| `airflow-scheduler` | 定时调度器，触发 DAG 执行                                  |
| `backend/dags/`     | DAG 定义目录（通过 volume 挂载到 Airflow）                 |

**ETL 服务文件**：

| 文件                     | 说明                                                                    |
| ------------------------ | ----------------------------------------------------------------------- |
| `base.py`                | BaseAdapter ABC + ETLResult dataclass                                   |
| `runner.py`              | ETLRunner：fetch → PHI 检测 → transform → 匿名化 → 仓库写入             |
| `historical_importer.py` | CSV 导入：parse → PHI 匿名化 → DuckDB 写入（三平台自动检测）            |
| `adapters/ga4.py`        | GA4 适配器（Google Analytics Data API v1，mock 模式）                   |
| `adapters/meta_ads.py`   | Meta Ads 适配器（Graph API v19，cursor 分页，mock 模式）                |
| `adapters/hubspot.py`    | HubSpot 适配器（CRM v3 Contacts，mock 模式）；M-08：日志不暴露 API 响应 |
| `adapters/quorum.py`     | Quorum 适配器（行为/受众数据，Daily 频率，mock 模式）                   |
| `adapters/leadrx.py`     | LeadRX 适配器（归因数据，1h 频率，conversion_id 哈希，分页支持）        |
| `adapters/liveramp.py`   | LiveRamp 适配器（身份解析，Daily 频率，segment_id 哈希处理）            |
| `adapters/dv360.py`      | DV360 适配器（programmatic campaign 数据，advertiser_id 验证）          |
| `adapters/stackadapt.py` | StackAdapt 适配器（native/programmatic ad 数据，分页支持）              |

#### 字段映射服务 (`services/field_mapping/`)

| 文件                  | 说明                                                                             |
| --------------------- | -------------------------------------------------------------------------------- |
| `canonical_schema.py` | 24 个标准字段定义（6 类别：time/identity/performance/engagement/revenue/custom） |
| `transform.py`        | TransformEngine（4 种变换：direct/value_mapping/unit_conversion/formula）        |
| `template_loader.py`  | JSON 模板加载器 + list_supported_platforms()                                     |
| `templates/*.json`    | 6 个平台默认模板（ga4/meta_ads/hubspot/tiktok_ads/dv360/stackadapt）             |

#### 通知服务 (`services/notifications/`)

| 文件            | 说明                                                           |
| --------------- | -------------------------------------------------------------- |
| `manager.py`    | WebSocket ConnectionManager（内存级全局单例，按 user_id 分组） |
| `dispatcher.py` | create_notification()（写 DB + 自动 WebSocket 推送）           |

#### 其他服务

| 文件                     | 说明                                                                                                  |
| ------------------------ | ----------------------------------------------------------------------------------------------------- |
| `campaign_query.py`      | CampaignQueryService（从仓库 mart_campaign_unified 查询跨平台 campaign 数据）                         |
| `budget_pacing.py`       | BudgetPacingService（检查预算节奏偏差 → 触发通知告警）                                                |
| `platform_registry.py`   | 12 个平台注册表（GA4/Meta/HubSpot/TikTok/DV360/StackAdapt/LeadRX/LiveRamp/Quorum/Canva/Firefly/ICON） |
| `oauth/token_refresh.py` | OAuth Token 自动刷新                                                                                  |

### `backend/tests/` — 测试套件（18 个文件，165 个用例）

| 文件                       | 用例数 | 覆盖模块                                                       |
| -------------------------- | ------ | -------------------------------------------------------------- |
| `conftest.py`              | —      | 测试 fixtures（DB 引擎、test_agency、test_user、auth_headers） |
| `test_auth.py`             | 6      | JWT 登录/登出/me/无效 token                                    |
| `test_tenants.py`          | 5      | Agency/Client CRUD + 认证                                      |
| `test_compliance.py`       | 10     | Consent/DSAR/PHI 检测/匿名化                                   |
| `test_integrations.py`     | 6      | 平台连接/断开/列表                                             |
| `test_etl.py`              | 11     | 三适配器 + ETL Runner + PHI 合规                               |
| `test_warehouse.py`        | 7      | DuckDB schema/insert/query/sync_state                          |
| `test_ai.py`               | 7      | AI Chat/预算控制/月度用量                                      |
| `test_observability.py`    | 10     | Health/Sentry/Langfuse/RequestId                               |
| `test_brands.py`           | 7      | 品牌配置 CRUD + PATCH 语义                                     |
| `test_imports.py`          | 9      | CSV 导入三平台 + 自动检测 + 边界                               |
| `test_field_mappings.py`   | 14     | CRUD + 版本 + 回滚 + 预览 + 模板                               |
| `test_personas.py`         | 9      | 手动/AI 创建 + CRUD + 过滤                                     |
| `test_creatives.py`        | 8      | 生成 + 平台过滤 + 列表                                         |
| `test_attribution.py`      | 9      | 报告生成 + 日期范围 + insights                                 |
| `test_portal.py`           | 8      | 仪表板 + 白标 + 精简视图                                       |
| `test_notifications.py`    | 9      | 通知 CRUD + 未读计数 + 标记已读                                |
| `test_etl_new_adapters.py` | 18     | 5 个新 adapter mock + ETL Runner 集成 + 白名单验证             |
| `test_campaigns.py`        | 12     | Campaign 查询 + 聚合摘要 + Budget Config CRUD + 租户隔离       |

---

## 数据库迁移 (`infra/migrations/`)

| 文件                              | 说明                                                                                     |
| --------------------------------- | ---------------------------------------------------------------------------------------- |
| `001_multi_tenant.sql`            | agencies + clients 表（二级多租户），set_updated_at 触发器                               |
| `002_auth.sql`                    | users 表（三角色 RBAC），user_role enum                                                  |
| `003_credential_vault.sql`        | credentials 表（Fernet 加密存储）                                                        |
| `004_audit_log.sql`               | audit_logs 表（INSERT-only，含 contains_phi 标记）                                       |
| `005_token_usage.sql`             | token_usage 表（BIGSERIAL PK，月度聚合索引）                                             |
| `006_integrations.sql`            | integrations + sync_logs 表（12 平台注册）                                               |
| `007_brand_config.sql`            | agencies/clients 添加 brand_config JSONB 列                                              |
| `008_field_mapping_agency.sql`    | field_mappings 添加 agency_id + platform 列                                              |
| `009_persona_agent.sql`           | personas 添加 agency_id/source/model_used/is_active                                      |
| `010_creative_agent.sql`          | generations 添加 agency_id/agent_type/metadata                                           |
| `011_compliance.sql`              | consent_records + dsar_requests + 5 张合规表                                             |
| `012_attribution_agent.sql`       | attribution_reports 表                                                                   |
| `013_notifications.sql`           | notifications 表 + 索引                                                                  |
| `014_remove_pii_columns.sql`      | C-03：DROP consent_records.subject_email，RENAME dsar subject_email → subject_email_hash |
| `015_encrypt_user_pii.sql`        | M-02/M-03：ADD email_hash 列 + UNIQUE 索引，支持 PII 加密迁移                            |
| `016_campaign_budget_configs.sql` | F-19：campaign_budget_configs 表（预算配置 + 告警规则，含唯一约束）                      |

---

## dbt 数据转换层 (`dbt/`)

```
dbt/
├── dbt_project.yml                        # 项目配置
├── profiles.yml.example                   # Snowflake 连接模板
├── macros/set_updated_at.sql             # 通用时间戳宏
├── models/
│   ├── staging/
│   │   ├── sources.yml                   # 数据源定义（8 个 raw 表）
│   │   ├── stg_ga4.sql                   # GA4 原始数据标准化
│   │   ├── stg_meta_ads.sql              # Meta Ads 原始数据标准化
│   │   ├── stg_hubspot.sql               # HubSpot 原始数据标准化
│   │   ├── stg_quorum.sql                # Quorum 受众行为数据
│   │   ├── stg_leadrx.sql                # LeadRX 归因数据
│   │   ├── stg_liveramp.sql              # LiveRamp 身份解析
│   │   ├── stg_dv360.sql                 # DV360 programmatic 数据
│   │   └── stg_stackadapt.sql            # StackAdapt native ad 数据
│   ├── canonical/
│   │   └── canonical_events.sql          # 跨平台统一事件 Schema
│   └── marts/
│       ├── mart_campaign_performance.sql # 营销活动绩效聚合
│       ├── mart_campaign_unified.sql    # 跨平台统一 Campaign 视图（Meta/DV360/StackAdapt）
│       ├── mart_persona_signals.sql      # 受众信号聚合
│       └── mart_attribution.sql          # 多触点归因分析（渠道贡献度）
└── tests/                                 # dbt 数据质量测试
```

---

## 功能模块文档 (`features/`)

| 目录                           | 模块                          | 状态      | 测试  |
| ------------------------------ | ----------------------------- | --------- | ----- |
| `p0-core/`                     | F-00~F-05 核心基础层          | ✅ 已完成 | 27/27 |
| `p1-etl-warehouse-ai/`         | F-06~F-09 ETL/仓库/AI         | ✅ 已完成 | 36/36 |
| `f10-persona-agent/`           | Persona Agent（Pillar 1）     | ✅ 已完成 | 9/9   |
| `f11-creative-agent/`          | Creative Agent（Pillar 2）    | ✅ 已完成 | 8/8   |
| `f12-attribution-agent/`       | Attribution Agent（Pillar 3） | ✅ 已完成 | 9/9   |
| `f13-brand-onboarding/`        | 品牌入驻系统                  | ✅ 已完成 | 7/7   |
| `f14-historical-import/`       | 历史数据 CSV 导入             | ✅ 已完成 | 9/9   |
| `f15-field-mapping/`           | 字段映射系统                  | ✅ 已完成 | 14/14 |
| `f16-client-portal/`           | 客户门户                      | ✅ 已完成 | 8/8   |
| `f17-realtime-notifications/`  | 实时通知（WebSocket）         | ✅ 已完成 | 9/9   |
| `f18-observability/`           | 监控与可观测性                | ✅ 已完成 | 10/10 |
| `f19-campaigns/`               | 统一 Campaign 视图 + Budget   | ✅ 已完成 | 12/12 |
| `f20-etl-adapters/`            | ETL 扩展（5 平台）            | ✅ 已完成 | 18/18 |
| `f21-persona-audience-export/` | Persona 受众导出              | ✅ 已完成 | 13/13 |
| `f22-pdf-reports/`             | PDF 报告引擎 + 自动发送       | ✅ 已完成 | 11/11 |
| `compliance/`                  | 合规架构设计文档              | ✅ 已完成 | —     |

每个模块目录包含：

- `COMPLETION.md` — 完成报告（功能摘要 + 文件清单 + 已知限制）
- `test/test-execution-report.md` — 测试执行报告（逐条用例结果）

---

## 多租户隔离

ReceptivIQ 实现了**物理 per-Agency 数据库隔离** + **Postgres 行级安全(RLS)by `client_id`** + **可配置 RBAC**(权限码可配 · 审计闭环 · Shadow→Enforce)三层防御。即使 SQL 漏写 `WHERE agency_id = ?` 也无法跨租户泄露;即使漏写 `WHERE client_id = ?` 也无法跨客户泄露。

### 角色分层

| 层级         | 角色                                      | `agency_id` | `client_id` | 可见范围                                         |
| ------------ | ----------------------------------------- | ----------- | ----------- | ------------------------------------------------ |
| **Platform** | `platform_super_admin` · `platform_admin` | `NULL`      | `NULL`      | 跨租户运维:暂停 / 邀请 / 审计所有 Agency         |
| **Agency**   | `agency_admin` · `agency_ops`             | 必填        | `NULL`      | 单一 Agency,可访问该 Agency 独立物理库的全部数据 |
| **Client**   | `client_viewer`                           | 必填        | 必填        | 单一 Client 门户(Agency 之下),只读               |

三层在前端渲染**完全不同的页面**(`<PermissionSwitch>` 拦截 `/` + 按权限过滤的 Sidebar 分组),参见 [`frontend/src/components/PermissionSwitch.tsx`](frontend/src/components/PermissionSwitch.tsx) 与 [`frontend/src/components/layout/Sidebar.tsx`](frontend/src/components/layout/Sidebar.tsx)。

### Layer 1 · 物理 Agency 隔离(per-Agency Postgres 数据库)

每个 Agency 拥有独立 Postgres 实例。平台层数据库只保留平台级元数据(`agencies / users / user_invitations / audit_logs` + RBAC 三表);租户库内 21 张 Agency 私有表全部落在自己的 `public` 命名空间。

```
平台库 (receptiviq)
  └─ public.{agencies, users, user_invitations, audit_logs,
             permissions, role_permissions, agency_role_permissions}

租户库(每 Agency 一个,例如 tenant_acme)
  └─ public.{personas, creatives, campaigns, attribution_reports,
             reports, integrations, credentials, …}   ← 21 表 + RLS
```

- **Provisioning**(`POST /auth/register` 或 `POST /platform/agencies`)原子且审计(`tenant.db.provisioned`):
  1. `INSERT INTO public.agencies (db_dsn = ENCRYPTED(...))`
  2. 本地走 `CREATE DATABASE tenant_<slug>`;生产走 Neon Management API `create_project`
  3. 在新库内回放 [`infra/migrations/agency_schema.sql`](infra/migrations/agency_schema.sql)(21 张表 + 18 个枚举类型 + RLS)
  4. Fernet 加密连接串后写回 `agencies.db_dsn`
- **每请求路由**:[`backend/app/core/tenant_router.py`](backend/app/core/tenant_router.py) 的 `TenantSessionRouter` 单例为每个 Agency 缓存一个 `AsyncEngine`(`pool_size=5, max_overflow=5`,LRU 64,空闲 30 分钟驱逐);[`backend/app/core/tenant_db.py`](backend/app/core/tenant_db.py) 解析调用者所在 Agency,返回绑定到该物理库的 session,并按 1% 采样写 `auth.session.guc_set` 审计。
- **DSN 保护**:`agencies.db_dsn` 经 Fernet `TypeDecorator`([`backend/app/core/encrypted_types.py`](backend/app/core/encrypted_types.py))加密落盘;日志 / Sentry / 审计均只出现 12 字节 SHA-256 指纹(`backend/app/core/dsn_fingerprint.py`),明文 DSN 不离开内存。
- **迁移工具**:[`backend/scripts/split_agency_to_neon.py`](backend/scripts/split_agency_to_neon.py) 执行 `pg_dump → provision → restore → 行数对账 → 原子翻转 db_dsn + 保留 db_dsn_previous` 流程;批量包装 [`backend/scripts/migrate_all_existing_agencies.py`](backend/scripts/migrate_all_existing_agencies.py) 已用于把旧 schema-per-Agency 的 3 个租户切到各自的独立物理库。

### Layer 2 · 客户级 Row-Level Security(租户库内)

在 Agency 独立库内,Postgres RLS 在 9 张含 `client_id` 列的表上强制隔离(`attribution_reports / campaign_budget_configs / consent_records / credentials / integrations / report_schedules / report_history / audit_logs / token_usage`):

```sql
ALTER TABLE attribution_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE attribution_reports FORCE ROW LEVEL SECURITY;
CREATE POLICY client_isolation ON attribution_reports
  USING (
    client_id IS NULL
    OR current_setting('app.client_id', true) = ''
    OR client_id::text = current_setting('app.client_id', true)
  );
```

每请求 yield session 前,`set_tenant_gucs()` 调用 `set_config('app.role', …)` / `set_config('app.client_id', …)` / `set_config('app.agency_id', …)`。`agency_admin` 的 `app.client_id = ''` → 看到全部行;`client_viewer` 仅看自己 `client_id` 的行 — 即使应用代码漏写 `WHERE` 条件。

### Layer 3 · 可配置 · 审计闭环的 RBAC

权限是码(`personas.read` / `team.invite` / `platform.permissions.manage` …),不是角色。每个角色有系统级默认;每个 Agency 可按角色覆盖;Platform 与 Agency 管理员**均可创建自定义角色**。

| 表名                      | 用途                                                                           |
| ------------------------- | ------------------------------------------------------------------------------ |
| `permissions`             | 46 个权限码(14 分类,含 `audit.read`)字典                                       |
| `roles`                   | 角色注册:code、label、tier(platform/agency/client)、rank、agency_id、is_system |
| `role_permissions`        | 系统级默认 — 每行一条 (role, code, granted)                                    |
| `agency_role_permissions` | Agency 级覆盖 — 存在即压过默认                                                 |

- **自定义角色** — Platform Super Admin 创建系统级角色(`agency_id = NULL`);Agency Admin 创建本租户角色(`agency_id = <自己>`,tier ∈ {agency, client})。内置角色 `is_system = true`,不可改名 / 不可删除。详见 [`backend/app/api/v1/roles_admin.py`](backend/app/api/v1/roles_admin.py)。
- **等级守卫** — 每个角色有整数 `rank`。用户只能编辑 `rank` **严格小于自己**的角色;违例返回 HTTP 403 并写审计 `rbac.permission.denied_self_edit`。内置默认 rank:`platform_super_admin=100 / platform_admin=90 / agency_admin=50 / agency_ops=40 / client_viewer=10`。这从源头堵死越权:Agency 管理员不能给自己加权限。
- 后端 enforce:[`backend/app/core/permissions.py`](backend/app/core/permissions.py) 暴露 `require_permission(code)` FastAPI 依赖工厂;`PermissionResolver` 缓存 `effective_permissions(agency_id, role)` 5 分钟,PUT 写入侧主动清缓存。
- 模式开关 `RBAC_ENFORCEMENT_MODE`:
  - **`shadow`**(默认,首次上线):不命中权限不抛 403,只写 `rbac.permission.denied_shadow` 到审计;跑 1 周后审计为 0 再翻 enforce。
  - **`enforce`**:不命中直接 403 + 写 `rbac.permission.denied_enforce`。
- 前端:[`useHasPermission(code)`](frontend/src/hooks/usePermission.ts) 驱动 [`<PermissionGate>`](frontend/src/components/PermissionGate.tsx) 与 [`<PermissionSwitch>`](frontend/src/components/PermissionSwitch.tsx);Sidebar 走**两段式过滤** — 先按 tier(平台用户即使继承了所有 46 个权限码也不会看到 Agency 工具),再按权限码。详见 [`groupsForUser(perms, tier)`](frontend/src/components/layout/Sidebar.tsx)。
- 配置 UI:
  - **Platform** → `/platform/roles`(角色 CRUD)· `/platform/permissions`(默认矩阵,46 码 × 全部系统角色)
  - **Agency** → `/settings/roles`(本租户角色 CRUD)· `/settings/permissions`(三态覆盖矩阵;rank ≥ 自己的角色列禁用)
  - `/auth/me` 返回 `role_label`、`role_rank`、用户的生效 `permissions[]`,前端无需额外请求即可决定 UI 显示。

### Layer 4 · 不可篡改的审计日志 + 租户级查看器

所有状态变更(每次端点 mutation、每次权限授予/撤销、每次租户 provision、每次角色创建/编辑/删除、每次 shadow/enforce 拒绝)都经 [`audit_event(...)`](backend/app/core/audit.py) 写入 `public.audit_logs`。该表 INSERT-only,触发器拒绝 UPDATE/DELETE(`audit_logs is INSERT-only`)。审计行是 SOC 2 CC7 与 GDPR Art. 30 的唯一可信记录。

平台内置审计查看器:

- **`GET /api/v1/audit-logs`** 支持 keyset 分页 + `agency_id`/`client_id`/`user_id`/`event`(LIKE on action)/`since`/`until`/`success` 过滤。每条返回已经在服务端 JOIN 解析的 `member_name` / `member_email` / `client_name` / `agency_name`(PII 服务端 Fernet 解密),UI 直接显示可读名,不再是 UUID。
- **`GET /api/v1/audit-logs/{members,clients}`** 为筛选器下拉提供数据,两个端点自动作用域:Agency 管理员只看本租户,平台管理员看全部租户。
- 前端:`/settings/audit`(Agency 视角,权限码 `audit.read`)和 `/platform/audit`(跨租户视角,权限码 `platform.audit.read`)复用同一 `<AuditLog />` 组件,仅传 `scopeAgencyId` 不同。筛选器含 Member · Client · Event · Date range · Status pills;行可展开,显示 `request_path` / `request_method` / `status_code` / 原始 `extra_data` JSON。

### 详细文档

完整设计与迁移路线见 [`docs/MULTI-TENANT-DB.md`](docs/MULTI-TENANT-DB.md);分阶段实施计划见 `/Users/ligc/.claude/plans/swirling-growing-wirth.md`(本地开发机)。

---

## 合规架构

> 详细设计见 [`features/compliance/architecture.md`](features/compliance/architecture.md)，以下为实现摘要。

### 数据加密与隐私（Privacy by Design）

| 控制项           | 实现                                                     | 合规标记  |
| ---------------- | -------------------------------------------------------- | --------- |
| 用户 PII 加密    | email/full_name Fernet 加密存储，email_hash SHA-256 查找 | M-02/M-03 |
| 凭证加密         | Credential.encrypted_data Fernet 加密                    | F-03      |
| IP 截断          | consent_records.ip_address 截断为 /24 网段               | M-04      |
| DSAR 数据最小化  | subject_email_hash 哈希存储，不保存明文姓名              | C-03      |
| ETL 匿名化       | 进仓库前 hash_identifier + truncate_ip                   | 架构 §5   |
| 日志 PII 清洗    | scrub_pii_from_logs() 正则过滤 email/SSN/phone           | 架构 §10  |
| HubSpot 日志脱敏 | API 错误只记录异常类名，不暴露响应体                     | M-08      |

### 认证与访问控制

| 控制项          | 实现                                                    | 合规标记 |
| --------------- | ------------------------------------------------------- | -------- |
| JWT 撤销        | jti + Redis 黑名单（TTL 自动清理），内存 fallback       | C-04     |
| 登录限流        | 5 次/5 分钟失败 → 锁定 15 分钟（IP 级暴力破解防护）     | M-10     |
| OAuth CSRF      | HMAC 签名 state 参数 + 10 分钟过期                      | C-01     |
| SECRET_KEY 校验 | 生产启动时检查弱/默认密钥，不通过则拒绝启动             | C-05     |
| CORS 限制       | 环境变量 CORS_ORIGINS，限定方法/头部白名单              | M-01     |
| 安全头          | HSTS / X-Frame-Options:DENY / nosniff / Referrer-Policy | M-11     |
| API 文档保护    | 生产环境自动禁用 /docs 和 /redoc                        | M-04     |

### GDPR 合规

- **Consent 管理**：subject_hash 哈希存储，支持授予/撤回/按目的过滤；agency_id 强制隔离
- **DSAR 工作流**：30 天 SLA，subject_email_hash 哈希存储（数据最小化）
- **数据匿名化**：hash_identifier / mask_email / truncate_ip / anonymize_record_for_warehouse
- **审计日志**：INSERT-only 不可变审计表，extra_data JSONB 扩展字段

### CCPA 合规

- **Do Not Sell**：consent_records.do_not_sell 标记
- **DSAR**：45 天 SLA（加州居民）
- **数据删除**：soft-delete 架构

### HIPAA 合规

- **PHI 检测**：Safe Harbor 18 类标识符扫描（ETL 管道 + CSV 导入）
- **会话超时**：15 分钟不活动过期（M-05：Redis + 内存 LRU 双层 fallback）
- **Sentry**：send_default_pii=False
- **加密存储**：凭证 Fernet 加密 + 用户 PII Fernet 加密
- **最小权限**：RBAC 三级角色（admin/ops/client_viewer）

### 数据安全防护

| 控制项       | 实现                                                          | 合规标记  |
| ------------ | ------------------------------------------------------------- | --------- |
| SQL 注入防护 | warehouse_client SQL 前缀白名单 + insert_many 表名/列名正则   | H-02/H-03 |
| 租户隔离     | 全端点强制 current_user.agency_id，Persona.agency_id NOT NULL | L-01/M-06 |
| 输入限制     | 字段映射 transform config 4KB 限制 + 200 条/次条目限制        | L-02      |
| 错误信息安全 | dbt 子进程/Google OAuth/HubSpot API 只返回通用错误            | H-10/H-01 |
| 弱凭证防护   | Airflow 配置无默认用户名密码，强制环境变量                    | H-06      |

### 合规审计轮次

| 轮次    | 日期       | 发现  | 修复  | 重点领域                                   |
| ------- | ---------- | ----- | ----- | ------------------------------------------ |
| 第 1 轮 | 2026-03-31 | 12 项 | 12 项 | 核心表结构 + API 端点                      |
| 第 2 轮 | 2026-03-31 | 24 项 | 24 项 | PII 加密 + 审计日志 + OAuth CSRF           |
| 第 3 轮 | 2026-04-01 | 12 项 | 4 项  | 深层架构级问题梳理                         |
| 第 4 轮 | 2026-04-01 | 8 项  | 8 项  | 限流 + 内存 fallback + SQL 注入 + 输入校验 |

---

## 外部服务集成状态

| 服务                      | 状态      | 说明                                                                   |
| ------------------------- | --------- | ---------------------------------------------------------------------- |
| **OpenRouter LLM**        | ✅ 已接入 | 3 个 Agent 实际调用 OpenRouter API，mock fallback                      |
| **Airflow ETL 调度**      | ✅ 已接入 | `dags/etl_sync_dag.py`：GA4/Meta/HubSpot 并行 → dbt 转换               |
| **Celery Worker**         | ✅ 已接入 | `worker.py` + `@celery_app.task` 装饰器，`integrations/sync` 自动分发  |
| **Neon Postgres**         | ✅ 已接入 | asyncpg + psycopg2 双连接，`?sslmode=require`                          |
| **DuckDB（开发仓库）**    | ✅ 已接入 | 零配置内存模式，`WAREHOUSE_BACKEND=duckdb`                             |
| **Snowflake（生产仓库）** | ✅ 已接入 | `snowflake.connector` 真实连接代码，`WAREHOUSE_BACKEND=snowflake` 切换 |
| **dbt 转换**              | ✅ 已接入 | 9 个 SQL 模型（staging/canonical/marts），Celery task + Airflow 触发   |
| **Langfuse LLM 追踪**     | ✅ 已接入 | AI endpoint Trace/Generation span，无 key 时静默跳过                   |
| **Sentry 错误监控**       | ✅ 已接入 | `send_default_pii=False`，启动时初始化                                 |
| **Google OAuth**          | ✅ 已接入 | `/login/google` token 验证 + 自动注册                                  |
| **平台 OAuth 回调**       | ✅ 已接入 | `/integrations/oauth/authorize/{platform}` + `/callback/{platform}`    |
| **MinIO 对象存储**        | ✅ 已接入 | `storage.py` 懒加载单例，upload/presigned_url/delete                   |
| **Redis**                 | ✅ 已接入 | Celery Broker + HIPAA 会话超时（`redis.asyncio`，不可用时降级）        |
| **WebSocket**             | ✅ 已接入 | `/ws?token=JWT` 认证连接 + ping/pong 心跳                              |
| **Token 预算控制**        | ✅ 已接入 | 所有 AI 端点预算检查，429 超限拒绝                                     |
| **审计日志**              | ✅ 已接入 | brands/personas/creatives/attribution/compliance/oauth 端点均记录审计  |

---

## 快速启动

### 环境要求

- Python 3.9+
- PostgreSQL 14+
- Redis（可选，降级为内存模式）
- Node.js 18+（前端）

### 后端启动

```bash
cd backend
pip install -r requirements.txt

# 配置环境变量
cp ../.env.example .env
# 编辑 .env 填入数据库连接、API Key 等

# 执行迁移
for f in ../infra/migrations/*.sql; do
  PGPASSWORD=receptiviq psql -U receptiviq -d receptiviq -f "$f"
done

# 启动开发服务器
uvicorn app.main:app --reload --port 8000
```

### 运行测试

```bash
cd backend
PYTHONPATH=. DATABASE_URL=postgresql+asyncpg://receptiviq:receptiviq@localhost:5432/receptiviq \
  python3 -m pytest tests/ -v
# 期望结果：135 passed
```

### Docker Compose（本地全栈）

```bash
docker-compose up --build
# 后端: http://localhost:8000
# 前端: http://localhost:5173
# API 文档: http://localhost:8000/docs（仅开发环境）
# Langfuse: http://localhost:3100
# MinIO Console: http://localhost:9001
# Airflow: http://localhost:8080
```

---

## 数据库架构

| 环境                 | 数据库                                        | 说明                                    |
| -------------------- | --------------------------------------------- | --------------------------------------- |
| **本地开发**         | PostgreSQL（本机安装）                        | `localhost:5432`，用户 `receptiviq`     |
| **线上生产**         | [Neon](https://neon.tech) Serverless Postgres | 自动伸缩，连接池，分支功能              |
| **数据仓库（开发）** | DuckDB 内存模式                               | 零配置，测试时自动降级                  |
| **数据仓库（生产）** | Snowflake                                     | 通过 `WAREHOUSE_BACKEND=snowflake` 切换 |

### Neon 连接配置

Neon 提供两种连接字符串格式，在 Render 环境变量中分别配置：

```bash
# 异步连接（FastAPI 主应用使用）
DATABASE_URL=postgresql+asyncpg://<user>:<password>@<host>.neon.tech/<dbname>?sslmode=require

# 同步连接（Celery Worker / Airflow 使用）
SYNC_DATABASE_URL=postgresql+psycopg2://<user>:<password>@<host>.neon.tech/<dbname>?sslmode=require
```

> **注意**：Neon 连接必须带 `?sslmode=require`，否则连接会被拒绝。

### 迁移执行

```bash
# 本地 PostgreSQL
for f in infra/migrations/*.sql; do
  PGPASSWORD=receptiviq psql -U receptiviq -d receptiviq -f "$f"
done

# Neon（线上）— 使用 Neon 提供的连接字符串
for f in infra/migrations/*.sql; do
  psql "<neon-connection-string>" -f "$f"
done
```

---

## 部署（Render）

平台使用 [Render](https://render.com) 进行生产部署，配置文件为 `render.yaml`（Blueprint 规范）。

### 架构

```
┌─────────────┐    ┌──────────────────┐    ┌─────────────┐
│  Render Web │───▶│  Neon Postgres   │    │  Snowflake  │
│  (FastAPI)  │    │  (Serverless)    │    │  (数据仓库)  │
└──────┬──────┘    └──────────────────┘    └──────▲──────┘
       │                                          │
       ├──▶ Render Redis（Celery Broker + 缓存 + HIPAA 会话）
       │                                          │
       ├──▶ Render Worker（Celery — AI 生成任务） │
       │                                          │
       ├──▶ Airflow（ETL 调度）───────────────────┘
       │      ├── GA4 / Meta Ads / HubSpot Adapter
       │      ├── PHI 检测 + 匿名化（合规层）
       │      └── dbt 转换（staging → canonical → marts）
       │
       ├──▶ OpenRouter API（LLM 统一入口 + Token 计费）
       │      ├── Claude Opus    → Persona Agent（深度推理）
       │      ├── Claude Sonnet  → Creative / Attribution Agent
       │      └── Token 用量 → token_usage 表（Agency 级预算控制）
       │
       ├──▶ Langfuse Cloud（LLM 调用追踪 · 可选）
       └──▶ Sentry（错误监控 · 可选）

┌─────────────┐
│ Render      │
│ Static Site │───▶ React SPA（Vite 构建）
└─────────────┘
```

### 部署步骤

1. **创建 Neon 项目**
   - 在 [Neon Console](https://console.neon.tech) 创建项目
   - 获取连接字符串（asyncpg 和 psycopg2 两种格式）
   - 执行数据库迁移（`infra/migrations/*.sql`）

2. **连接 Render**
   - 在 [Render Dashboard](https://dashboard.render.com) 选择 "Blueprint" → 连接 GitHub 仓库
   - Render 自动解析 `render.yaml`，创建以下服务：
     - `receptiviq-api`（Web Service — Docker）
     - `receptiviq-web`（Static Site — React）
     - `receptiviq-worker`（Background Worker — Celery）
     - `receptiviq-redis`（Redis 实例）

3. **配置环境变量**（在 Render Dashboard 中手动设置）

   | 变量                  | 值来源                                                                                       | 说明                                        |
   | --------------------- | -------------------------------------------------------------------------------------------- | ------------------------------------------- |
   | `DATABASE_URL`        | Neon Console                                                                                 | `postgresql+asyncpg://...?sslmode=require`  |
   | `SYNC_DATABASE_URL`   | Neon Console                                                                                 | `postgresql+psycopg2://...?sslmode=require` |
   | `SECRET_KEY`          | 随机生成 32+ 字符                                                                            | JWT 签名密钥（C-05：弱密钥阻止启动）        |
   | `ENCRYPTION_KEY`      | `python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` | Fernet 密钥（PII + 凭证加密）               |
   | `OPENROUTER_API_KEY`  | OpenRouter Dashboard                                                                         | LLM API 密钥                                |
   | `GOOGLE_CLIENT_ID`    | Google Cloud Console                                                                         | OAuth 客户端 ID                             |
   | `AIRFLOW_USERNAME`    | 自定义强密码                                                                                 | H-06：无默认值，必须手动配置                |
   | `AIRFLOW_PASSWORD`    | 自定义强密码                                                                                 | H-06：无默认值，必须手动配置                |
   | `CORS_ORIGINS`        | 逗号分隔域名列表                                                                             | M-01：限制跨域来源                          |
   | `SENTRY_DSN`          | Sentry 项目设置                                                                              | 错误追踪                                    |
   | `LANGFUSE_PUBLIC_KEY` | Langfuse Cloud                                                                               | LLM 追踪                                    |

4. **部署**
   - Render 自动构建和部署
   - 健康检查端点：`/health`
   - API 文档：生产环境自动禁用 `/docs`（安全设计）

### render.yaml 服务清单

| 服务名              | 类型        | 运行时  | 说明                                      |
| ------------------- | ----------- | ------- | ----------------------------------------- |
| `receptiviq-api`    | Web Service | Docker  | FastAPI 后端，端口由 `$PORT` 环境变量决定 |
| `receptiviq-web`    | Static Site | Node.js | React 前端，Vite 构建后静态托管           |
| `receptiviq-worker` | Worker      | Docker  | Celery 异步任务（ETL 同步、AI 生成等）    |
| `receptiviq-redis`  | Redis       | —       | Celery Broker + 会话缓存 + HIPAA 超时     |

---

## 环境变量

### 核心配置

| 变量                | 说明                | 本地默认值                                                              | 线上                  |
| ------------------- | ------------------- | ----------------------------------------------------------------------- | --------------------- |
| `DATABASE_URL`      | PostgreSQL 异步连接 | `postgresql+asyncpg://receptiviq:receptiviq@localhost:5432/receptiviq`  | Neon 连接字符串       |
| `SYNC_DATABASE_URL` | PostgreSQL 同步连接 | `postgresql+psycopg2://receptiviq:receptiviq@localhost:5432/receptiviq` | Neon psycopg2 格式    |
| `SECRET_KEY`        | JWT 签名密钥        | `change-me-in-production`                                               | Render 自动生成       |
| `ENCRYPTION_KEY`    | Fernet 加密密钥     | —                                                                       | 手动生成              |
| `REDIS_URL`         | Redis 连接          | `redis://localhost:6379/0`                                              | Render Redis 自动注入 |

### AI 配置

| 变量                 | 说明                   | 默认值                        |
| -------------------- | ---------------------- | ----------------------------- |
| `OPENROUTER_API_KEY` | OpenRouter LLM API Key | —（空则 mock 模式）           |
| `PERSONA_MODEL`      | Persona Agent 模型     | `anthropic/claude-opus-4-6`   |
| `CREATIVE_MODEL`     | Creative Agent 模型    | `anthropic/claude-sonnet-4-6` |
| `ATTRIBUTION_MODEL`  | Attribution Agent 模型 | `anthropic/claude-sonnet-4-6` |

### 数据仓库

| 变量                 | 说明                                | 默认值   |
| -------------------- | ----------------------------------- | -------- |
| `WAREHOUSE_BACKEND`  | 仓库后端（`duckdb` 或 `snowflake`） | `duckdb` |
| `SNOWFLAKE_ACCOUNT`  | Snowflake 账号                      | —        |
| `SNOWFLAKE_USER`     | Snowflake 用户名                    | —        |
| `SNOWFLAKE_PASSWORD` | Snowflake 密码                      | —        |

### 可观测性

| 变量                  | 说明              | 默认值                       |
| --------------------- | ----------------- | ---------------------------- |
| `SENTRY_DSN`          | Sentry 错误追踪   | —（空则跳过）                |
| `LANGFUSE_PUBLIC_KEY` | Langfuse LLM 追踪 | —（空则跳过）                |
| `LANGFUSE_SECRET_KEY` | Langfuse 密钥     | —                            |
| `LANGFUSE_HOST`       | Langfuse 地址     | `https://cloud.langfuse.com` |

完整变量列表见 `.env.example`。

---

## 已知限制与后续规划

### 🔴 前端（CRITICAL — 待实现）

当前 `frontend/` 目录仅有空目录结构，无实际 React 代码。后端 API（61 个端点）已全部就绪，前端需独立实现：

| 前端模块            | 说明               | 对应后端 API                                                      |
| ------------------- | ------------------ | ----------------------------------------------------------------- |
| Ops Dashboard       | 运营团队内部视图   | /tenants, /integrations, /ai, /personas, /creatives, /attribution |
| Client Portal       | 白标客户门户       | /portal (5 端点)                                                  |
| Auth Pages          | 登录/OAuth/注册    | /auth (5 端点)                                                    |
| Compliance UI       | 同意管理/DSAR 查看 | /compliance (5 端点)                                              |
| Notification Center | 实时通知面板       | /notifications + WebSocket                                        |

### 🟡 后续开发规划

| 优先级      | 任务                       | 说明                                                  |
| ----------- | -------------------------- | ----------------------------------------------------- |
| **Phase 2** | 前端 React 实现            | React 19 + TypeScript + Vite + Ant Design             |
| **Phase 2** | PostgreSQL RLS 策略        | 数据库级别行级安全策略                                |
| **Phase 2** | dbt 数据质量测试           | Snowflake 数据校验（uniqueness/not_null/referential） |
| **Phase 3** | Canva / Adobe Firefly 集成 | Creative Agent 图片生成工具                           |
| **Phase 3** | DSAR 自动化执行            | access/delete/export 自动化处理                       |
| **Phase 3** | 数据保留定时任务           | Celery Beat 按 retention_policies 自动清理            |
| **Phase 3** | 违规事件告警               | GDPR 72h / HIPAA 60 天自动通知                        |
| **Phase 3** | 跨境传输控制               | EU 数据路由到对应 Snowflake 区域                      |
| **Phase 3** | 每 Agency 独立加密密钥     | 密钥与数据物理分离 + 90 天自动轮换                    |
