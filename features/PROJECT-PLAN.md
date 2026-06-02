# ReceptivIQ Platform — 底层框架开发计划

> 版本：v1.0 | 日期：2026-03-31
> 基于 IQ（Python/FastAPI）+ ReceptivIQ（Node.js Agent 架构）两个原型，合并为统一技术栈。

---

## 项目概述

AI-native Agency OS，自动化 `研究 → 创意 → 媒介投放 → 归因` 完整营销链路。
核心价值：消除代理商跨 50+ 工具的手动协调成本，建立统一的数据仓库，让 AI 推理整个数据集而非单个 API。

---

## 合规顶层策略

> **强制要求：GDPR · CCPA · HIPAA — 三者同时满足**
> 合规不是附加功能，是所有开发决策的前置约束。

| 法规      | 适用场景                         | 关键要求                                                      |
| --------- | -------------------------------- | ------------------------------------------------------------- |
| **GDPR**  | 任何处理欧盟居民数据的客户       | 同意管理、被遗忘权（DSAR）、数据可携、跨境传输合规（SCC/DPF） |
| **CCPA**  | 加州消费者数据                   | Do Not Sell、数据访问/删除权、隐私通知                        |
| **HIPAA** | 医疗行业营销客户（PHI 相关活动） | PHI 加密（AES-256）、审计日志、BAA、15分钟会话超时、去标识化  |

**架构级合规原则（Privacy by Design）：**

- PII/PHI **永远不以明文**存入数据仓库（Snowflake）
- 所有用户标识符进仓库前**单向哈希**（SHA-256 + 租户盐值）
- IP 地址**截断**后存储（192.168.1.x → 192.168.1.0）
- 数据保留策略取三法规最严值（审计日志 6 年）
- 每个 Agency 独立加密密钥（密钥与数据物理分离）
- HIPAA 客户：15 分钟会话超时 + PHI 检测拦截 + BAA 追踪
- 违规通知自动化：GDPR 72h / HIPAA 60天 / CCPA 通知受害者
- 详细设计见：[features/compliance/architecture.md](compliance/architecture.md)

---

## 技术栈决策

| 层级        | 技术选型                                      | 来源                   |
| ----------- | --------------------------------------------- | ---------------------- |
| Backend API | **Python / FastAPI** (async)                  | IQ 项目，AI 生态更完整 |
| 任务队列    | **Celery** + Redis                            | IQ 项目                |
| ETL 编排    | **Apache Airflow**                            | 两者共用               |
| 数据转换    | **dbt** + Snowflake                           | ReceptivIQ 项目        |
| 数据仓库    | **Snowflake**（开发：DuckDB）                 | 技术提案要求           |
| 业务数据库  | **PostgreSQL** + pgvector                     | 两者共用               |
| 对象存储    | **MinIO**（生产：S3）                         | IQ 项目                |
| AI 路由     | **OpenRouter** + LangGraph                    | 两者共用               |
| Frontend    | **React 19** + TypeScript + Vite + Ant Design | IQ 项目                |
| 监控        | **Sentry** + Langfuse                         | 已有 Langfuse          |
| 部署        | **Docker Compose**（本地）→ Render（生产）    | 两者共用               |

---

## 架构分层总览

```
┌─────────────────────────────────────────────────┐
│  Frontend (React)                               │
│  ┌───────────────┐  ┌─────────────────────────┐ │
│  │  Ops View     │  │  Client Portal           │ │
│  │  (Staff 内部) │  │  (白标客户门户)          │ │
│  └───────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────┘
          ↕ REST / WebSocket
┌─────────────────────────────────────────────────┐
│  FastAPI — API Layer (/api/v1)                  │
│  Auth · Tenants · Integrations · AI             │
│  Personas · Creatives · Attribution · Reports   │
└─────────────────────────────────────────────────┘
          ↕
┌─────────────────────────────────────────────────┐
│  Service Layer                                  │
│  ┌──────────────┐ ┌─────────┐ ┌──────────────┐ │
│  │  Core AI     │ │   ETL   │ │    Brand     │ │
│  │  Brain       │ │ Pipeline│ │  Onboarding  │ │
│  │  ├ Persona   │ │ Airflow │ │  Parser      │ │
│  │  ├ Creative  │ │ +dbt    │ │              │ │
│  │  └ Attribution│ └────────┘ └──────────────┘ │
│  └──────────────┘                               │
└─────────────────────────────────────────────────┘
          ↕
┌─────────────────────────────────────────────────┐
│  Data Layer                                     │
│  ┌────────────┐ ┌────────────┐ ┌─────────────┐ │
│  │ PostgreSQL │ │ Snowflake  │ │   MinIO     │ │
│  │ (业务数据) │ │ (数据仓库) │ │ (文件存储)  │ │
│  └────────────┘ └────────────┘ └─────────────┘ │
└─────────────────────────────────────────────────┘
```

---

## 底层框架功能清单

### F-01 多租户基础设施（Multi-Tenant Foundation）

> 来源：ReceptivIQ 迁移文件，Priority: P0

**功能：**

- Agency（顶层机构）→ Client（下级客户）双层租户体系
- 所有表均有 `agency_id` + `client_id` 字段，数据库级 Row-Level Security（RLS）
- Tenant provisioning API：创建机构、添加客户、分配权限
- 每租户独立的品牌配置（颜色、字体、Logo）
- 白标子路径路由（`/agency-slug/client-slug`）

**文件：**

```
infra/migrations/001_multi_tenant.sql    ← agencies + clients 表 + RLS 策略
infra/migrations/002_auth.sql           ← users + roles + sessions
backend/app/models/agency.py
backend/app/models/client.py
backend/app/api/v1/tenants.py
```

---

### F-02 认证与授权（Auth & RBAC）

> 来源：IQ auth，Priority: P0

**功能：**

- JWT Bearer Token（access + refresh），jti 唯一标识支持撤销
- Google OAuth2（主要登录方式）
- 角色：`agency_admin` / `agency_ops` / `client_viewer`
- SSO/SAML 接口预留（企业版 Phase 3）
- 会话管理，Token 黑名单（Redis 优先 + 内存 fallback）
- M-02/M-03：用户 email/full_name Fernet 加密存储，email_hash SHA-256 确定性查找
- M-10：IP 级登录限流（5 次/5 分钟失败 → 锁定 15 分钟），暴力破解防护
- C-04：JWT jti + Redis 黑名单（TTL 自动清理）
- C-01：OAuth state HMAC 签名（CSRF + 跨租户防护）
- C-05：生产启动时 SECRET_KEY 强度校验

**文件：**

```
infra/migrations/002_auth.sql
infra/migrations/015_encrypt_user_pii.sql     ← M-02/M-03: email_hash 列
backend/app/core/security.py                  ← C-04: jti 黑名单
backend/app/core/pii_crypto.py                ← M-02/M-03: PII 加密
backend/app/api/v1/auth.py                    ← M-10: 登录限流
backend/app/api/v1/oauth_callback.py          ← C-01: HMAC state
```

---

### F-03 凭证保险库（Credential Vault）

> 来源：ReceptivIQ credential_vault，Priority: P0

**功能：**

- 加密存储第三方平台 OAuth Token、API Key
- Fernet 字段级加密（`cryptography` 库）
- Token 自动刷新（OAuth 2.0 refresh_token 流程）
- 凭证健康状态检测（expired / valid / error）
- 按租户隔离，不同机构无法访问彼此凭证

**文件：**

```
infra/migrations/003_credential_vault.sql
backend/app/core/encryption.py
backend/app/models/credential.py
backend/app/services/oauth/token_refresh.py   ← NEW
backend/app/api/v1/integrations.py
```

---

### F-04 审计日志（Audit Logging）

> 来源：ReceptivIQ audit_logs，Priority: P0，GDPR 要求

**功能：**

- 记录所有数据访问、AI 查询、仓库读取操作
- 字段：`agency_id`, `user_id`, `action`, `resource_type`, `ip_address`, `timestamp`
- 不可篡改（只追加，不更新删除）
- GDPR/CCPA 数据删除请求支持（right-to-erasure 流程）

**文件：**

```
infra/migrations/004_audit_log.sql
backend/app/core/audit.py
backend/app/models/audit_log.py
```

---

### F-05 集成平台管理（Platform Integration Management）

> 来源：IQ platform-management，Priority: P0

**功能：**

- 平台注册表：GA4、Meta Ads、HubSpot、TikTok、LeadRX、LiveRamp、DV360、StackAdapt、Quorum
- OAuth 2.0 授权流程（GA4、Meta、HubSpot、TikTok）
- API Key 连接方式（StackAdapt、DV360、LeadRX）
- 连接状态管理（CONNECTED / EXPIRED / FAILED / DISCONNECTED）
- 手动触发同步 + 定时同步调度

**文件：**

```
infra/migrations/006_integrations.sql
backend/app/models/integration.py
backend/app/services/platform_registry.py
backend/app/api/v1/integrations.py
```

---

### F-06 ETL 数据管道（ETL Pipeline）

> 来源：IQ ETL + ReceptivIQ Airflow DAGs，Priority: P0

**功能：**

- Airflow 编排，Celery 作为 fallback
- 平台适配器（Adapters）：

  | 适配器         | 优先级 | 状态                                   |
  | -------------- | ------ | -------------------------------------- |
  | GA4            | P0     | ✅ IQ 已实现                           |
  | Meta Ads API   | P0     | 🔧 ReceptivIQ DAG 存在，Adapter 待实现 |
  | HubSpot        | P1     | 📋 待实现                              |
  | LeadRX         | P1     | 📋 待实现                              |
  | LiveRamp       | P1     | 📋 待实现（确认合同）                  |
  | Quorum         | P1     | 📋 待实现                              |
  | TikTok Ads     | P2     | 📋 待实现                              |
  | DV360          | P2     | 📋 待实现                              |
  | StackAdapt     | P2     | 📋 待实现                              |
  | Icon.app/Adspy | P2     | 📋 待实现                              |
  | Canva API      | P2     | 📋 待实现                              |
  | Adobe Firefly  | P2     | 📋 待实现                              |

- 数据写入 Snowflake Raw 区（替代当前写 PostgreSQL）
- 同步日志、错误重试、数据健康状态

**文件：**

```
backend/dags/ga4_etl.py             ← IQ 已有
backend/dags/meta_ads_etl.py        ← 需移植
backend/dags/hubspot_etl.py         ← 新建
backend/dags/manual_sync.py         ← IQ 已有
backend/dags/scheduled_sync.py      ← IQ 已有
backend/app/services/etl/runner.py  ← IQ 已有
backend/app/services/etl/adapters/  ← 按需扩展
```

---

### F-07 Canonical Event Schema & dbt 转换层

> 来源：ReceptivIQ dbt，Priority: P0，架构核心

**功能：**

- 所有平台数据规范化到统一事件 Schema（Canonical Event）
- 解决跨平台"conversion"定义冲突（Meta vs GA4 vs HubSpot）
- dbt 模型分层：
  - `staging/`：原始数据清洗（每个平台一个模型）
  - `canonical/`：统一事件模型（所有 Pillar 查询的来源）
  - `marts/`：按业务需求聚合（campaign_performance、persona_signals、attribution）
- 数据质量测试（uniqueness、not null、referential integrity）
- 增量模型（Incremental Models）降低仓库查询成本

**Canonical Event 核心字段：**

```sql
event_id, event_timestamp, agency_id, client_id,
platform, event_type, user_id_hashed,
campaign_id, campaign_name, ad_set_id, ad_id,
impressions, clicks, conversions, spend_usd,
channel, device_type, geography,
raw_payload JSONB
```

**文件：**

```
dbt/models/staging/stg_ga4.sql          ← ReceptivIQ 已有
dbt/models/staging/stg_meta_ads.sql     ← ReceptivIQ 已有
dbt/models/staging/stg_hubspot.sql      ← 新建
dbt/models/canonical/canonical_events.sql ← NEW，核心
dbt/models/marts/mart_campaign_performance.sql ← ReceptivIQ 已有
dbt/models/marts/mart_persona_signals.sql     ← 新建
dbt/models/marts/mart_attribution.sql         ← 新建
```

---

### F-08 Snowflake 数据仓库集成

> 来源：ReceptivIQ snowflake.ts（移植到 Python），Priority: P0

**功能：**

- Snowflake Python Connector（`snowflake-connector-python`）
- 三层 Schema：`raw_`（ETL 原始）→ `staging_`（dbt 清洗）→ `mart_`（业务聚合）
- Snowflake Warehouse 按用途分离：ETL Warehouse / Analytics Warehouse / AI Warehouse
- 成本管理：auto-suspend（5分钟）、结果缓存、Resource Monitor 告警
- 开发环境降级：DuckDB（本地模拟 Snowflake，零费用）
- H-02/H-03：SQL 语句前缀白名单防注入 + insert_many 表名/列名正则校验

**文件：**

```
backend/app/core/warehouse_client.py    ← 统一仓库客户端（DuckDB/Snowflake 双后端）
infra/snowflake/schemas.sql             ← Snowflake schema/仓库/角色初始化
infra/snowflake/raw_tables.sql          ← Snowflake RAW 层表定义
```

> **实现说明**：原计划的 `snowflake_client.py` 和 `warehouse/loader.py` 已合并为统一的 `warehouse_client.py`（DuckDB 开发 / Snowflake 生产双后端），简化架构。

---

### F-09 Core AI Brain（LLM 路由器）

> 来源：ReceptivIQ brain/router.ts（移植到 Python），Priority: P1

**功能：**

- 中心 LLM 路由器：接收请求 → 分发给对应 Agent
- 支持的 Agent：`persona` / `creative` / `attribution_reporting`
- Shared Context 组装：品牌配置 + 历史活动 + Persona 对象 + 集成元数据
- Token 用量按租户记录（`token_usage` 表）
- Per-tenant Token 预算限制和告警
- Prompt 缓存（Redis）：相同请求避免重复 LLM 调用
- 轻量模型用于分类/路由，重量模型用于生成任务
- 审计日志（每次 AI 调用）

**文件：**

```
infra/migrations/005_token_usage.sql
backend/app/services/ai/brain.py        ← NEW（移植自 ReceptivIQ）
backend/app/services/ai/context.py      ← NEW
backend/app/models/token_usage.py       ← NEW
backend/app/api/v1/ai.py               ← NEW
```

---

### F-10 Persona Agent（Pillar 1 — 市场研究智能）

> 来源：ReceptivIQ personaAgent.ts，Priority: P1

**功能：**

- 基于 GA4 + Quorum + HubSpot 数据生成结构化 Persona 对象
- 每客户生成 3-7 个命名 Persona，包含：
  - 人口属性（年龄、地理、设备）
  - 心理属性（兴趣、价值观、购买动机）
  - 渠道偏好（最佳触达渠道 + 最佳时段）
  - 消息接受度线索（推荐语气、CTA 类型）
- 输出：Audience Blueprint 对象（结构化，供 Pillar 2/3/4 引用）
- Persona → 受众导出：一键推送到 Meta Ads / DV360 受众配置
- 竞品广告分析：Icon.app/Adspy 集成（竞品创意模式摘要）
- 置信度评分（冷启动阶段透明展示数据充分性）

**文件：**

```
infra/migrations/009_persona_agent.sql
backend/app/services/ai/agents/persona.py  ← NEW
backend/app/core/warehouse_client.py       ← 仓库查询（已集成在统一客户端中）
backend/app/models/persona.py
backend/app/api/v1/personas.py             ← NEW
frontend/src/apps/ops/Persona.tsx
```

---

### F-11 Creative Agent（Pillar 2 — 创意内容引擎）

> 来源：ReceptivIQ creativeAgent.ts + IQ CreativeHub，Priority: P1

**功能：**

- 输入：Persona 对象 + 品牌配置 + 竞品参考广告
- 生成多个创意变体（文案 + 图片）
- 图片生成：Adobe Firefly API（已订阅）
- 模板格式化：Canva API（Teams 版）
- 跨渠道格式适配：Meta / DV360 / TikTok / Display 规格自动调整
- 品牌合规过滤器：检测违规颜色、字体、禁用词（MVP：规则型；Phase 2：AI 评分）
- 创意资产管理：版本、标签、审批工作流
- 竞品参考工作流：Pin ad → 作为 Creative Agent 输入上下文

**文件：**

```
infra/migrations/010_creative_agent.sql
backend/app/services/ai/agents/creative.py
backend/app/models/creative.py
backend/app/api/v1/creatives.py
frontend/src/apps/ops/Creative.tsx          ← 待实现（前端 Phase 2）
```

> **待实现**：`canva.py` 和 `firefly.py` 工具集成推迟至 Phase 3，当前创意生成通过 OpenRouter LLM 文案 + 提示词图片描述实现。

---

### F-12 Attribution Agent（Pillar 3 — 归因测量）

> 来源：ReceptivIQ attributionAgent.ts，Priority: P1

**功能：**

- 多触点归因管道：LeadRX（主）+ GA4（基线）+ LiveRamp（跨设备身份匹配）
- Pixel & Tag 管理：GTM 集成，系统感知已部署的追踪代码
- 归因仪表板：渠道贡献可视化，客户客会汇报级别报告
- AI 生成报告摘要（Attribution Reporting Agent）
- PDF 报告导出（模板化）
- 数据新鲜度指示器（"数据截止至 X 时间"）

**文件：**

```
backend/app/services/ai/agents/attribution.py
backend/app/services/etl/adapters/leadrx.py  ← NEW
backend/app/services/etl/adapters/liveramp.py ← NEW
backend/app/api/v1/attribution.py
backend/app/api/v1/reports.py
frontend/src/apps/ops/Attribution.tsx
frontend/src/apps/portal/ClientDashboard.tsx
```

---

### F-13 品牌入驻系统（Brand Onboarding）

> 新功能，Priority: P1

**功能：**

- 上传品牌指南（PDF / 图片 / JSON）
- 解析提取：主色/辅色调色板、字体系列、语调描述词、视觉资产、法规禁用词
- 存入规范化 `brand_config` 对象（每客户版本化存储）
- 分发给 Creative Agent、Attribution Agent、客户门户主题层
- 品牌配置版本管理（历史活动关联到执行时的品牌状态）
- MVP：内部工具；Phase 2：客户自助入驻流程

**文件：**

```
infra/migrations/007_brand_config.sql
backend/app/services/brand/parser.py        ← NEW（PyMuPDF + PIL）
backend/app/services/brand/onboarding.py    ← NEW
backend/app/models/brand_config.py
backend/app/api/v1/brands.py
frontend/src/apps/ops/BrandOnboarding.tsx   ← NEW
```

---

### F-14 历史数据手动导入（Historical Import）

> 来源：ReceptivIQ historical_import.py DAG，Priority: P1

**功能：**

- 接受 CSV/JSON 历史数据导出（Meta Ads Manager、GA4、HubSpot、Shopify）
- 规范化到与实时集成相同的 Canonical Event Schema
- 支持至少 12 个月历史数据
- 内部工具，不对客户门户暴露（MVP）
- 数据量依赖评估（影响 ETL 工时估算）

**文件：**

```
backend/dags/historical_import.py
backend/app/services/etl/historical_importer.py ← NEW
backend/app/api/v1/import.py
frontend/src/apps/ops/Import.tsx
```

---

### F-15 字段映射系统（Field Mapping）

> 来源：IQ field-mapping，Priority: P1

**功能：**

- 平台原始字段 → Canonical Event Schema 字段的映射配置
- 内置模板（GA4、Meta Ads 标准映射）
- 用户可自定义映射规则
- 映射应用于 ETL transform 层

**文件：**

```
backend/app/services/field_mapping/
backend/app/api/v1/field_mappings.py
frontend/src/apps/ops/FieldMapping.tsx
```

---

### F-16 客户门户（Client Portal）

> 来源：ReceptivIQ portal/ views，Priority: P2

**功能：**

- 独立于 Ops 内部视图的简化客户界面
- 白标主题（颜色、Logo 按租户动态注入）
- 内容：归因仪表板、创意报告、活动摘要
- 访问控制：`client_viewer` 角色，只能查看自己客户的数据
- 移动端响应式布局

**文件：**

```
frontend/src/apps/portal/PortalLayout.tsx
frontend/src/apps/portal/ClientDashboard.tsx
frontend/src/apps/portal/Reports.tsx
```

---

### F-17 实时通知（WebSocket）

> 新功能，Priority: P2

**功能：**

- WebSocket 服务器（FastAPI WebSocket 或 Socket.io）
- 推送：AI Agent 任务状态、ETL 同步完成、报告生成完成
- 替代当前 SSE 轮询方式

**文件：**

```
backend/app/api/v1/ws.py
frontend/src/hooks/useWebSocket.ts
```

---

### F-18 监控与可观测性（Observability）

> 部分来源：IQ Langfuse，Priority: P2

**功能：**

- **Sentry**：错误追踪 + 性能监控（已有 `@sentry/node` 依赖）
- **Langfuse**：LLM 调用追踪、Token 成本可视化（IQ 已配置）
- **Prometheus + Grafana**（可选）：基础设施指标

**文件：**

```
backend/app/core/monitoring.py
docker-compose.yml（Sentry DSN 配置）
```

---

## 功能模块状态总览

| 模块                        | 状态                            | 来源                                                | 优先级 |
| --------------------------- | ------------------------------- | --------------------------------------------------- | ------ |
| F-01 多租户基础             | ✅ 已完成（2026-03-31）         | agencies/clients 二级隔离                           | P0     |
| F-02 认证与授权             | ✅ 已完成（2026-03-31）         | JWT+OAuth+RBAC 三角色                               | P0     |
| F-03 凭证保险库             | ✅ 已完成（2026-03-31）         | Fernet 加密存储                                     | P0     |
| F-04 审计日志               | ✅ 已完成（2026-03-31）         | INSERT-only 审计表                                  | P0     |
| F-05 平台集成管理           | ✅ 已完成（2026-03-31）         | 12 平台注册，connect/sync                           | P0     |
| F-06 ETL 数据管道           | ✅ 已完成（2026-03-31）         | GA4/Meta/HubSpot+PHI 合规                           | P0     |
| F-07 Canonical Schema + dbt | ✅ 已完成（2026-03-31）         | staging+canonical+mart 全层                         | P0     |
| F-08 Snowflake 集成         | ✅ 已完成（2026-03-31）         | DuckDB 降级+Snowflake 接口                          | P0     |
| F-09 Core AI Brain          | ✅ 已完成（2026-03-31）         | TokenUsage+预算控制+API                             | P1     |
| F-10 Persona Agent          | ✅ 已完成（2026-03-31）         | personas.py，CRUD+AI 生成                           | P1     |
| F-11 Creative Agent         | ✅ 已完成（2026-03-31）         | creatives.py，四平台文案                            | P1     |
| F-12 Attribution Agent      | ✅ 已完成（2026-03-31）         | attribution.py，多触点归因                          | P1     |
| F-13 品牌入驻               | ✅ 已完成（2026-03-31）         | brands.py，PATCH 语义                               | P1     |
| F-14 历史数据导入           | ✅ 已完成（2026-03-31）         | historical_importer.py，三平台                      | P1     |
| F-15 字段映射               | ✅ 已完成（2026-03-31）         | field_mappings.py，版本管理                         | P1     |
| F-16 客户门户               | ✅ 已完成（2026-03-31）         | portal.py，5 端点白标门户                           | P2     |
| F-17 WebSocket 实时通知     | ✅ 已完成（2026-03-31）         | WS+通知系统，4 REST+1 WS                            | P2     |
| F-18 监控可观测性           | ✅ 已完成（2026-03-31）         | Sentry+Langfuse+健康检查                            | P2     |
| F-19 统一 Campaign 视图     | ✅ 已完成（2026-04-02）         | 仓库聚合+Budget Alerts，12/12 测试                  | P1     |
| F-20 ETL Adapters 扩展      | ✅ 已完成（2026-04-02）         | Quorum/LeadRX/LiveRamp/DV360/StackAdapt，18/18 测试 | P0     |
| F-21 Persona-to-Audience    | ✅ 已完成（2026-04-02）         | Meta/DV360 受众导出+PII过滤，13/13 测试             | P1     |
| F-22 PDF 报告引擎           | ✅ 已完成（2026-04-02）         | 模板+调度+邮件+加密recipients，11/11 测试           | P0     |
| F-23 The Trade Desk Adapter | 📋 待开发（Discovery 文档新增） | DSP/程序化广告：CTV/Display/Audio 数据              | P1     |
| F-24 Google Ads Adapter     | 📋 待开发（Discovery 文档新增） | 搜索广告活动数据（与 GA4 独立）                     | P1     |
| F-25 Salesforce CRM Adapter | 📋 待开发（Discovery 文档新增） | CRM：accounts/contacts/opportunities/activities     | P1     |
| F-26 NetSuite Adapter       | 📋 待开发（Discovery 文档新增） | Oracle ERP/CRM：客户+收入数据                       | P2     |
| F-27 PlacerIQ Adapter       | 📋 待开发（Discovery 文档新增） | 位置情报 + 客流量分析                               | P1     |
| F-28 Experian Adapter       | 📋 待开发（Discovery 文档新增） | Syndicated Audiences：人口统计/心理图谱             | P1     |
| F-29 Adobe Firefly 集成     | 📋 待开发（Discovery 文档新增） | Creative Agent 图像生成下游工具                     | P2     |
| F-30 Canva Connect 集成     | 📋 待开发（Discovery 文档新增） | Creative Agent 设计模板下游工具                     | P2     |

状态图例：✅ 已实现可直接复用 | 🔧 需移植/重构 | 📋 全新开发

### Discovery 文档来源备注

F-23 ~ F-30 来自 `ReceptivIQ_Discovery_Interview_Guide` (Stage-6 Step-1 Post-Sale Discovery) 中客户提及的三方平台,平台元数据已注册到 `backend/app/services/platform_registry.py`（带 `"status": "planned"` 标记）。Adapter 实现工作量预估见对应 `features/<module>/design/` 子目录（待后续生成）。

**客户反馈警示(逐字引用)**:Canva & Adobe 客户当前体验差(`"AI output is unusable, and UI is too cluttered"`)— 实施 F-29/F-30 前需先做 PoC 验证我方生成质量明显超过客户现状,否则集成无价值。

---

## 开发分阶段计划

### Phase 0 — 基础设施层（2 周）

**目标：** 所有开发的前置依赖，必须在任何 Pillar 工作开始前完成。

| 任务                            | 来源                   | 工时估算 |
| ------------------------------- | ---------------------- | -------- |
| Docker Compose 全栈环境搭建     | 两者融合               | 1d       |
| PostgreSQL 迁移脚本（001-005）  | 移植自 ReceptivIQ      | 2d       |
| 多租户 RLS 策略                 | 移植自 ReceptivIQ      | 1d       |
| 认证系统（JWT + Google OAuth）  | 移植自 IQ              | 1d       |
| 凭证保险库 + 加密               | 移植自 ReceptivIQ + IQ | 2d       |
| Snowflake 连接 + Raw Schema     | 新建                   | 2d       |
| dbt 环境配置 + Canonical Schema | 移植自 ReceptivIQ      | 2d       |
| 审计日志中间件                  | 移植自 ReceptivIQ      | 1d       |

### Phase 1 — ETL + AI 基础层（4 周）

**目标：** 数据流通，AI 可访问数据。

| 任务                                 | 来源              | 工时估算 |
| ------------------------------------ | ----------------- | -------- |
| ETL Runner + Airflow DAG 框架        | 移植自 IQ         | 2d       |
| GA4 适配器 → 写入 Snowflake          | 移植+升级 IQ      | 3d       |
| Meta Ads 适配器                      | 新建              | 3d       |
| HubSpot 适配器                       | 新建              | 3d       |
| dbt staging 模型（GA4/Meta/HubSpot） | 移植+新建         | 3d       |
| dbt canonical_events 核心模型        | 新建              | 2d       |
| Core AI Brain（Python 实现）         | 移植自 ReceptivIQ | 3d       |
| Token 用量追踪                       | 移植自 ReceptivIQ | 1d       |
| 品牌入驻系统（PDF 解析）             | 新建              | 3d       |

### Phase 2 — Pillar 1 & 2（4 周）

**目标：** 研究 + 创意两个核心 Pillar MVP 可用。

| 任务                          | 来源      | 工时估算 |
| ----------------------------- | --------- | -------- |
| Persona Agent（数据驱动）     | 移植+重构 | 4d       |
| Audience Blueprint 数据模型   | 新建      | 2d       |
| Persona → Meta/DV360 受众导出 | 新建      | 3d       |
| Creative Agent（品牌合规）    | 重构自 IQ | 4d       |
| Canva API 集成                | 新建      | 2d       |
| Adobe Firefly 集成            | 新建      | 2d       |
| 创意资产管理 UI               | 重构自 IQ | 3d       |

### Phase 3 — Pillar 3 + 客户门户（4 周）

**目标：** 归因 + 客户可见报告。

| 任务                 | 来源              | 工时估算 |
| -------------------- | ----------------- | -------- |
| LeadRX 适配器        | 新建              | 3d       |
| LiveRamp 适配器      | 新建              | 3d       |
| dbt attribution mart | 新建              | 3d       |
| Attribution Agent    | 新建              | 4d       |
| PDF 报告生成         | 新建              | 3d       |
| 客户门户（白标主题） | 移植自 ReceptivIQ | 4d       |
| WebSocket 实时推送   | 新建              | 2d       |

### Phase 4 — SaaS 化 & 合规（持续）

- GDPR/CCPA/HIPAA 合规审查
- SSO/SAML 企业认证
- Render 生产部署配置
- Sentry 监控接入
- SOC 2 准备

---

## 目录结构

```
ReceptivIQ-Platform/
├── docker-compose.yml          # 全栈开发环境
├── .env.example                # 环境变量模板
├── features/
│   └── PROJECT-PLAN.md         # 本文件
│
├── backend/                    # Python / FastAPI
│   ├── requirements.txt
│   ├── alembic/                # DB 迁移（Alembic）
│   ├── dags/                   # Airflow DAGs
│   │   ├── ga4_etl.py
│   │   ├── meta_ads_etl.py
│   │   ├── hubspot_etl.py
│   │   ├── manual_sync.py
│   │   ├── scheduled_sync.py
│   │   └── historical_import.py
│   └── app/
│       ├── main.py
│       ├── worker.py           # Celery worker
│       ├── api/v1/             # FastAPI routes
│       │   ├── auth.py
│       │   ├── tenants.py
│       │   ├── integrations.py
│       │   ├── ai.py
│       │   ├── personas.py
│       │   ├── creatives.py
│       │   ├── attribution.py
│       │   ├── reports.py
│       │   ├── brands.py
│       │   ├── import.py
│       │   └── field_mappings.py
│       ├── core/
│       │   ├── config.py
│       │   ├── database.py     # Async PostgreSQL
│       │   ├── sync_database.py # Celery sync session
│       │   ├── security.py     # JWT
│       │   ├── encryption.py   # Fernet
│       │   ├── airflow_client.py
│       │   ├── snowflake_client.py  ← NEW
│       │   ├── storage.py      # MinIO
│       │   └── audit.py        ← NEW
│       ├── models/             # SQLAlchemy ORM
│       │   ├── agency.py
│       │   ├── client.py
│       │   ├── user.py
│       │   ├── credential.py
│       │   ├── integration.py
│       │   ├── brand_config.py
│       │   ├── persona.py
│       │   ├── creative.py
│       │   ├── token_usage.py  ← NEW
│       │   ├── audit_log.py    ← NEW
│       │   └── sync_log.py
│       ├── schemas/            # Pydantic
│       └── services/
│           ├── ai/
│           │   ├── brain.py        ← Core AI Brain
│           │   ├── context.py      ← Shared Context
│           │   ├── agents/
│           │   │   ├── persona.py
│           │   │   ├── creative.py
│           │   │   └── attribution.py
│           │   └── tools/
│           │       ├── warehouse.py
│           │       ├── meta_ads.py
│           │       └── canva.py
│           ├── etl/
│           │   ├── runner.py
│           │   ├── transform.py
│           │   └── adapters/
│           │       ├── ga4.py      ✅
│           │       ├── meta_ads.py
│           │       ├── hubspot.py
│           │       ├── tiktok.py
│           │       ├── leadrx.py
│           │       └── liveramp.py
│           ├── brand/
│           │   ├── parser.py
│           │   └── onboarding.py
│           ├── warehouse/
│           │   ├── loader.py
│           │   └── canonical.py
│           └── field_mapping/
│
├── dbt/                        # Data Transformation
│   ├── dbt_project.yml
│   ├── profiles.yml.example
│   └── models/
│       ├── staging/
│       │   ├── sources.yml
│       │   ├── stg_ga4.sql
│       │   ├── stg_meta_ads.sql
│       │   └── stg_hubspot.sql
│       ├── canonical/
│       │   └── canonical_events.sql    ← 核心
│       └── marts/
│           ├── mart_campaign_performance.sql
│           ├── mart_persona_signals.sql
│           └── mart_attribution.sql
│
├── frontend/                   # React / TypeScript
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
│       ├── apps/
│       │   ├── ops/            # Staff 内部视图
│       │   │   ├── Dashboard.tsx
│       │   │   ├── Integrations.tsx
│       │   │   ├── Persona.tsx
│       │   │   ├── Creative.tsx
│       │   │   ├── Attribution.tsx
│       │   │   ├── Import.tsx
│       │   │   └── Settings.tsx
│       │   └── portal/         # 客户白标门户
│       │       ├── ClientDashboard.tsx
│       │       └── Reports.tsx
│       ├── api/
│       ├── components/
│       ├── hooks/
│       └── store/
│
└── infra/
    ├── migrations/             # PostgreSQL（顺序执行）
    │   ├── 001_multi_tenant.sql
    │   ├── 002_auth.sql
    │   ├── 003_credential_vault.sql
    │   ├── 004_audit_log.sql
    │   ├── 005_token_usage.sql
    │   ├── 006_integrations.sql
    │   ├── 007_brand_config.sql
    │   ├── 008_personas.sql
    │   ├── 009_creatives.sql
    │   └── 010_data_sync.sql
    └── snowflake/
        ├── schemas.sql
        └── raw_tables.sql
```

---

## 关键架构决策记录（ADR）

| 日期       | 决策                                                   | 原因                                                                              |
| ---------- | ------------------------------------------------------ | --------------------------------------------------------------------------------- |
| 2026-03-31 | 统一使用 Python/FastAPI（放弃 Node.js BizAPI）         | Python AI 生态（LangChain、LangGraph、dbt）更完整；两个项目最终合并为一套技术栈   |
| 2026-03-31 | 数据仓库选 Snowflake，开发降级 DuckDB                  | 生产需要 Snowflake 能力（Time Travel、Zero-Copy Clone）；本地开发用 DuckDB 零成本 |
| 2026-03-31 | Agent 架构继承 ReceptivIQ 设计（3 Agent + Core Brain） | ReceptivIQ 的 brain/router.ts 设计与技术提案完全一致，Python 移植成本低           |
| 2026-03-31 | ETL 目标从 PostgreSQL 改为 Snowflake                   | 文档明确要求"所有集成数据入仓"，PostgreSQL 不适合做分析型数据仓库                 |
| 2026-03-31 | Canonical Event Schema 是架构核心                      | 所有平台 ETL → 同一 Schema；AI 只查 canonical，不查原始表；确保跨平台归因一致性   |
| 2026-03-25 | Airflow + Celery 共存                                  | Airflow 负责 DAG 编排，Celery 作 fallback（IQ 已验证）                            |
| 2026-03-26 | JSONB 查询用 `.astext` 而非 `cast().as_string()`       | 后者返回带 JSON 引号的字符串（IQ 调试教训）                                       |
