# 环境架构图释义（Environment Stack Glossary）

> 配套图：
>
> - **生产环境**：[prod-stack-layered.svg](./prod-stack-layered.svg) · [prod-stack-layered-en.svg](./prod-stack-layered-en.svg)
> - **开发环境**：[dev-stack-layered.svg](./dev-stack-layered.svg) · [dev-stack-layered-en.svg](./dev-stack-layered-en.svg)
> - 关联 PSD：[Technical Solution](../psd/technical-solution.md)
>   视角：把图上每一个名字、每一个 tag、每一条边界都讲清楚——方便客户 / 投资人 / 新工程师独立读懂

---

## 0. 整体结构与差异

两张图都是 **7 层自上而下** 架构：

```
LAYER 1 · 呈现层 / Presentation
LAYER 2 · 接入层 / API Gateway
LAYER 3 · 应用服务层 / Application
LAYER 4 · ELT 管道 / Extract-Load-Transform
LAYER 5 · 数据层 / Data Storage （3-Lake Medallion）
LAYER 6 · 外部服务层 / External Services
LAYER 7 · 部署层 / Infrastructure
```

**生产 vs 开发关键差异**：

| 维度        | 🟢 生产（PROD）                                          | 🟧 开发（DEV）                                  |
| ----------- | -------------------------------------------------------- | ----------------------------------------------- |
| L5 仓库     | **Neon Postgres**（每 Agency 独立 project · serverless） | **PostgreSQL**（本地容器 · schema 模拟 3-Lake） |
| L5 缓存     | **Redis Cloud**（managed）                               | **Redis**（docker container）                   |
| L5 对象存储 | **AWS S3**（cloud）                                      | **MinIO**（self-hosted S3 兼容）                |
| L7 部署平台 | **Render PaaS**（托管 · 自动扩缩容）                     | **Coolify**（self-host 图形化 PaaS）            |
| 网络        | mTLS + private VPC subnet                                | docker network                                  |
| 密钥        | per-Agency KMS                                           | Fernet 模拟加密                                 |
| 凭证        | AWS Secrets Manager                                      | `.env` 文件                                     |

---

## 1. LAYER 1 · 呈现层（Presentation）

**面向用户的 Web 应用**——Agency / Client 用户在此登录、查看仪表盘、操作业务模块。

| 元素                   | 含义                                                                      |
| ---------------------- | ------------------------------------------------------------------------- |
| **React**              | 前端 UI 框架；构建 SPA（Single Page Application），含 TypeScript 类型系统 |
| **Google OAuth**       | Google 提供的 OAuth 2.0 第三方身份认证，登录入口                          |
| **Authentication 2.0** | OAuth 2.0 授权框架（行业标准）                                            |
| **TypeScript**         | JavaScript 的静态类型扩展，编译时类型检查                                 |
| **SPA**（隐含）        | Single Page Application，单页应用，前后端分离架构                         |

> Post-MVP 计划新增 **Office 365 / Microsoft Entra ID** SSO（生产图标注）。

---

## 2. LAYER 2 · 接入层（API Gateway）

**HTTP / WebSocket 请求的统一入口 + 中间件链**——所有客户端请求必经此层做认证、鉴权、合规、限流。

| 元素                   | 含义                                                                                     |
| ---------------------- | ---------------------------------------------------------------------------------------- |
| **FastAPI**            | Python 的现代 async web 框架，承载所有 REST + WebSocket 端点                             |
| **async REST + WS**    | 异步 REST API + WebSocket 实时通道（单进程高并发）                                       |
| **async**              | 异步 I/O 模式（非阻塞），单进程高并发                                                    |
| **WebSocket**          | 全双工实时通信协议；用于 `/ws` 推送 Agent 完成、审批就绪等事件                           |
| **Real-time /ws**      | WebSocket 端点（实时通道）                                                               |
| **MIDDLEWARE CHAIN**   | 中间件链：每个请求依序经过：CORS → SecurityHeaders → HIPAA SessionGuard → RequestLogging |
| **CORS**               | Cross-Origin Resource Sharing（跨域资源共享）—— 控制哪些前端域名可访问 API               |
| **SecurityHeaders**    | 强制 HTTPS、CSP（内容安全策略）、X-Frame-Options 等安全响应头                            |
| **HIPAA SessionGuard** | HIPAA 合规会话守卫：15 分钟无活动自动登出，记录所有 PII 访问                             |
| **RequestLogging**     | 所有请求写 audit log（INSERT-only），含 actor / endpoint / status / latency              |

---

## 3. LAYER 3 · 应用服务层（Application）

**AI Brain + 业务服务的并行执行层**——AI 调用与业务逻辑解耦。

### 3.1 AI Brain 区

| 元素           | 含义                                                                                                                                      |
| -------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| **AI Brain**   | Core AI Brain 服务；6 个内部组件（Context Builder / LLM Router / Agent Orchestrator / Tool Executor / Memory & Retrieval / Audit & Cost） |
| **LLM router** | 模型路由器；按 agent / 成本 / 延迟 / 合规选模型                                                                                           |
| **budget**     | Token 预算控制（每 Agency 月度 token 上限）                                                                                               |

### 3.2 AI AGENTS 区（4 个 Pillar Agent）

| Agent                 | 默认模型      | 职责                                 |
| --------------------- | ------------- | ------------------------------------ |
| **Persona Agent**     | Claude Opus   | 受众画像构建（深度推理）             |
| **Creative Agent**    | Claude Sonnet | 创意生成 + A/B                       |
| **Attribution Agent** | Claude Sonnet | 跨渠道归因 / ROI                     |
| **Media Agent**       | Claude Sonnet | 媒介采买优化（写回需 human approve） |

### 3.3 BUSINESS SERVICES 区

| 元素               | 含义                                                                                                                                    |
| ------------------ | --------------------------------------------------------------------------------------------------------------------------------------- |
| **Reports**        | 报表服务——聚合 marts 层数据，渲染 dashboard / PDF / API 输出                                                                            |
| **AudienceExport** | 受众导出——把 canonical.audience_segment 通过 PII Access Service 转为各平台特定 hash 上传（Meta CA / DV360 / TikTok / TTD / StackAdapt） |
| **Campaign**       | 活动管理——跨广告平台的 Campaign / Ad Group / Creative 元数据 CRUD                                                                       |
| **BudgetPacing**   | 预算监控——按计划检测 Campaign 投放消耗 vs 预算曲线；超额触发 Notifs                                                                     |
| **Notifs**         | 通知服务——WebSocket + Email + Slack 多通道；Agent 完成、审批就绪、预算告警等事件出口                                                    |
| **Brand**          | 品牌管理——Agency 白标配置（logo / 主题色 / 域名）+ 品牌资料库                                                                           |
| **FieldMapping**   | 字段映射——CRM/CSV 上传时把源字段映射到 canonical schema（如 HubSpot `lifecycle` → canonical `funnel_stage`）                            |
| **OAuth**          | 第三方平台 OAuth 流程管理——为每个数据源（Meta / DV360 / GA4 等）维护 token 刷新与过期处理                                               |
| **PlatformReg**    | 平台注册——把 Agency 的 Meta ad account / GA4 property 等账户接入平台的注册与凭证存储入口（凭证经 Credential Vault 加密存储）            |

### 3.4 Langfuse SDK

| 元素             | 含义                                                                       |
| ---------------- | -------------------------------------------------------------------------- |
| **Langfuse SDK** | LLM 应用全链路追踪 SDK；每次 LLM 调用自动记录 prompt / token / 成本 / 延迟 |
| **LLM tracing**  | LLM 调用追踪与可观测性                                                     |

---

## 4. LAYER 4 · ELT 管道（Extract-Load-Transform · 先保存后转换）

**"先把原始数据完整保存，再在仓库内转换" 的现代数据架构**——区别于传统 ETL（先转换再保存）。

### 4.1 ORCHESTRATION 区（编排引擎二选一）

| 元素        | 含义                                                                                    |
| ----------- | --------------------------------------------------------------------------------------- |
| **Airflow** | Apache Airflow，业内最普及的 DAG 编排器；1000+ Provider 生态；标 `current` 表示当前可用 |
| **Dagster** | Asset-centric 现代编排器；原生数据血缘 + dagster-dbt 一等集成；标 `target` 表示推荐目标 |
| **Celery**  | Python 异步任务队列；用于 PDF 生成、受众导出、预算告警等长任务                          |
| **DAG**     | Directed Acyclic Graph（有向无环图）—— Airflow 的工作流模型                             |
| **Asset**   | Dagster 的核心抽象——每个数据产物（表/文件/模型）= 一个 asset                            |

> 详见 [ELT-ORCHESTRATION-PRIORITY](../ELT-ORCHESTRATION-PRIORITY.md)。

### 4.2 EXTRACT ADAPTERS 区（数据源连接器）

每个 chip 代表一个 **BaseAdapter 子类**，负责从一个外部平台拉取数据：

| Adapter        | 数据源                     | 类型                               |
| -------------- | -------------------------- | ---------------------------------- |
| **Meta**       | Facebook / Instagram Ads   | 广告平台（A 类 tenant-private）    |
| **DV360**      | Google Display & Video 360 | 广告平台                           |
| **TikTok**     | TikTok Ads                 | 广告平台                           |
| **Trade Desk** | The Trade Desk DSP         | 广告平台                           |
| **StackAdapt** | StackAdapt DSP             | 广告平台                           |
| **GA4**        | Google Analytics 4         | 网站分析（A 类）                   |
| **HubSpot**    | HubSpot CRM                | CRM（A 类）                        |
| **Experian**   | Experian 人群画像          | 共享参考数据（B 类）               |
| **TransUnion** | TransUnion 信用 + 画像     | 共享参考数据                       |
| **Nielsen**    | Nielsen Panel              | 共享参考数据                       |
| **Placer IQ**  | Placer IQ POI / 人流量     | 共享参考数据                       |
| **LiveRamp**   | LiveRamp 身份解析          | C 类（基于 Agency 名单的查询服务） |
| **Quorum**     | Quorum 立法监控            | 共享参考数据                       |
| **Tresorit**   | Tresorit 加密传输          | HIPAA 合规文件通道（A 类）         |

> 数据分类说明详见 [Technical Solution §3.5](../psd/technical-solution.md#35-数据分类与共享参考数据策略tenant-scoping--shared-reference)。

### 4.3 dbt Core 行

| 元素                    | 含义                                                                           |
| ----------------------- | ------------------------------------------------------------------------------ |
| **dbt Core**            | Data Build Tool（开源版）—— SQL-based 数据转换框架                             |
| **清洗·合并·映射·聚合** | dbt 在仓库内执行的 4 类操作：清洗噪声 / 合并跨源 / 映射 canonical / 聚合 marts |

### 4.4 ELT 八步映射

| STEP | 阶段                                                | 由谁完成                             |
| ---- | --------------------------------------------------- | ------------------------------------ |
| 1    | Extract                                             | Adapter 拉取                         |
| 2    | Classify                                            | Classification Gate（PII/PHI 分级）  |
| 3    | Load                                                | 写 Landing Lake                      |
| 4-8  | Normalize / Deduplicate / Validate / Enrich / Index | dbt 4 层模型在 Processed Lake 内执行 |

---

## 5. LAYER 5 · 数据层（Data Storage · 3-Lake Medallion）

**核心**：图中 L5 横向布局 6 元素 + 1 边界 + 1 TENANT ISOLATION 徽章。

### 5.1 三 Lake Medallion 架构

| 元素                         | 生产实现                                       | 开发实现                                 | 含义                                                                                                                 |
| ---------------------------- | ---------------------------------------------- | ---------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| **🟫 Landing Lake (Bronze)** | per-Agency Neon project (`{agency}-landing`)   | PostgreSQL schema `landing`              | 所有原始数据**完整保留**的着陆点；PII 列字段级加密，非 PII 列明文；immutable；业务/AI 禁读                           |
| **🔒 Raw PII Lake**          | per-Agency Neon project (`{agency}-raw-pii`)   | PostgreSQL schema `raw_secure`           | **从 Landing 派生的 PII 维表**；仅持 `raw_secure.users` + `<source>_pii_fields` + `pii_access_log` 三表；非 PII 不进 |
| **✓ Processed Lake**         | per-Agency Neon project (`{agency}-processed`) | PostgreSQL schema `processed` + pgvector | **从 Landing 派生的非 PII 业务路径**；dbt 5 层（raw → staging → canonical → marts → ai_context）；完全无明文 PII     |
| **Bronze 标语**              | "整条 record / full record"                    | 同左                                     | Landing 的核心特征——完整保留原始 record                                                                              |
| **PII 字段 only**            | 同左                                           | 同左                                     | Raw PII Lake 仅持 PII 字段                                                                                           |
| **dbt 5 层**                 | 同左                                           | 同左                                     | Processed Lake 内的 dbt 转换层数                                                                                     |

### 5.2 PII Boundary 与软分隔

| 元素                               | 含义                                                                                                                |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| **🔐 PII BOUNDARY**（粗红虚线）    | **硬隔离**——仅在 Raw PII Lake 与 Processed Lake 之间；不同 Neon project + 独立 KMS + 独立 VPC + mTLS + DLP 持续扫描 |
| **"同 PII zone"**（细虚线 + 文字） | **软分隔**——在 Landing 与 Raw PII 之间；两者位于同一 PII trust boundary（同等加密、访问控制）                       |
| **🔒 锁图标**（白色 SVG）          | Raw PII Lake 的视觉标识                                                                                             |
| **🟫 砖块**（隐含）                | Landing Lake (Bronze) 的视觉标识                                                                                    |

### 5.3 缓存与对象存储

| 元素               | 生产                  | 开发             | 含义                                      |
| ------------------ | --------------------- | ---------------- | ----------------------------------------- |
| **Redis**          | Redis Cloud (managed) | Redis (docker)   | 内存 K-V 存储；用作 cache + Celery broker |
| **Cache + broker** | —                     | —                | Redis 的双重角色                          |
| **MinIO**          | —                     | docker container | S3 兼容的对象存储（dev 替代 AWS S3）      |
| **AWS S3**         | cloud                 | —                | AWS 对象存储；存 PDF、CSV、加密文件       |

### 5.4 TENANT ISOLATION 徽章（L5 右侧）

| 元素                          | 含义                                                                                             |
| ----------------------------- | ------------------------------------------------------------------------------------------------ |
| **🏢 Agency**                 | Agency = **物理隔离单位**；per-Agency 独立 Neon project + 独立 KMS 密钥                          |
| **👤 Client**                 | Client = **逻辑隔离**；同 Agency 内通过 `client_id` RLS 限制可见性（保留跨 Agency benchmarking） |
| **物理隔离**                  | 不同 Neon project / 不同 KMS 主密钥 / 不同 VPC subnet —— 跨 Agency 物理不可达                    |
| **逻辑隔离**                  | Postgres ROW LEVEL SECURITY policy 强制 client_id 过滤                                           |
| **per-Agency project + KMS**  | 每 Agency 独立的 Neon project 与 KMS master key                                                  |
| **client_id RLS (in-Agency)** | 同一 Agency 数据库内 Client 间的 RLS 隔离                                                        |

### 5.5 Tool tags 含义

| Tag                | 出现位置           | 含义                                                      |
| ------------------ | ------------------ | --------------------------------------------------------- |
| **HIPAA 6y · 90d** | Landing            | HIPAA 客户保留 6 年，非 HIPAA 保留 90 天                  |
| **per-Agency KMS** | Raw PII            | 每 Agency 独立 KMS 主密钥（与 Landing 的密钥独立）        |
| **Fernet 加密**    | Raw PII (dev)      | Python `cryptography` 库的对称加密（AES-128-CBC + HMAC）  |
| **dev: PG schema** | Landing (dev)      | 开发环境用 schema 模拟 Landing Lake（生产是独立 project） |
| **RLS per Client** | Processed          | 行级安全 per Client（Client Viewer 只看自己）             |
| **managed**        | Redis Cloud / Neon | 厂商托管服务（无运维负担）                                |
| **cloud**          | AWS S3             | 云端 SaaS                                                 |
| **docker**         | dev Redis          | Docker 容器（开发环境本地）                               |
| **self-hosted**    | MinIO              | 自托管                                                    |

---

## 6. LAYER 6 · 外部服务层（External Services）

### 6.1 LLM STACK 区（双 Gateway）

平台采用**双 LLM Gateway** 设计——默认走 OpenRouter；HIPAA / BAA 客户的 PHI workload 强制走 AWS Bedrock：

| 元素              | 含义                                                                                                                  |
| ----------------- | --------------------------------------------------------------------------------------------------------------------- |
| **OpenRouter**    | **默认网关**——多厂商 LLM 路由（Anthropic / Google / OpenAI 等）；统一 API + 成本对比 + 失败回退；非 HIPAA workload 用 |
| **AWS Bedrock**   | **HIPAA / BAA 网关**——AWS 托管的 Claude，含 BAA 合同；HIPAA 客户的 PHI / PII workload 由 LLM Router 强制路由到这里    |
| **路由策略**      | LLM Router 按 `tenant.hipaa_flag` + `purpose` 决定走哪条；审计日志记录每次的网关选择 + 模型 + token 使用              |
| **Claude Opus**   | Anthropic 最强推理模型（Persona Agent 默认）                                                                          |
| **Claude Sonnet** | Anthropic 平衡推理 / 成本模型（Creative / Attribution / Media Agent 默认）                                            |
| **Gemini Flash**  | Google 低延迟模型（备选 · 成本敏感场景，仅经 OpenRouter）                                                             |

### 6.2 OBSERVABILITY 区

| 元素                 | 含义                                                                  |
| -------------------- | --------------------------------------------------------------------- |
| **Langfuse**         | LLM 应用全链路可观测平台；记录每次调用的 prompt / token / 成本 / 延迟 |
| **Sentry**           | 应用错误监控；前后端异常聚合 + 实时告警                               |
| **LLM call tracing** | LLM 调用追踪                                                          |
| **Error monitoring** | 错误监控                                                              |

### 6.3 DATA SOURCES (CATEGORIES) 区

按业务类目分组展示 14 个 P1 外部数据源（具体 Adapter 列表见 §4.2）。

---

## 7. LAYER 7 · 部署层（Infrastructure / Deployment）

### 7.1 生产：Render Managed PaaS

| 元素                      | 含义                                               |
| ------------------------- | -------------------------------------------------- |
| **Render PaaS**           | 托管 PaaS 平台；自动部署 / 自动扩缩容 / 托管数据库 |
| **Web Service (FastAPI)** | Render 上的后端服务实例（auto-scale）              |
| **Worker (Celery)**       | Render 上的异步任务 worker                         |
| **Static Site (React)**   | Render 静态站点托管（前端）                        |
| **Cron 任务**             | Render Cron 调度（计划任务）                       |
| **Web (Airflow)**         | Airflow webserver 服务                             |
| **Worker (Airflow)**      | Airflow worker 节点                                |
| **→ Neon 3-Lake**         | 连接到 Neon Postgres 三 Lake                       |
| **→ AWS S3**              | 连接到 AWS S3                                      |
| **→ Redis Cloud**         | 连接到托管 Redis                                   |
| **Docker**                | 容器构建运行时；Render 后端用 Docker 镜像部署      |
| **GitHub**                | 源码托管 + webhook 触发 Render 自动部署            |

### 7.2 开发：Coolify

| 元素                           | 含义                                                                                                                                         |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------- |
| **Coolify**                    | 自托管的图形化 PaaS（开源）；单机管理多个 docker 服务                                                                                        |
| **COOLIFY-MANAGED CONTAINERS** | Coolify 管理的容器组                                                                                                                         |
| **Docker**                     | 容器运行时（开发用 `docker compose` 一键启动全栈）                                                                                           |
| **GitHub**                     | 源码 + webhook                                                                                                                               |
| **容器组（隐含）**             | 开发环境包含后端（FastAPI / Worker）· 前端（Frontend）· 数据（PostgreSQL / Redis / MinIO）· 编排（Airflow Web / Worker）· 可观测（Langfuse） |

---

## 8. 视觉元素与配色

### 8.1 7 色 band 标签

| Layer | 颜色      | 角色                   |
| ----- | --------- | ---------------------- |
| L1    | 🟦 Sky    | Presentation（呈现层） |
| L2    | 🟦 Cyan   | API Gateway            |
| L3    | 🟪 Pink   | Application + AI       |
| L4    | 🟦 Blue   | ELT                    |
| L5    | 🟪 Violet | Data Storage           |
| L6    | 🟦 Sky    | External Services      |
| L7    | 🟥 Red    | Infrastructure         |

### 8.2 数据 / 控制流箭头颜色

| 颜色       | 类型                               |
| ---------- | ---------------------------------- |
| 🟦 Sky     | 用户流（HTTP/WS）                  |
| 🟪 Pink    | AI 调用流（→ OpenRouter / Agents） |
| 🟩 Emerald | 数据流（ELT / 仓库读写）           |
| 🟧 Amber   | 合规流（PII 检测 / 审计）          |
| 🟥 Red     | PII 边界 / 部署流                  |

### 8.3 环境徽章

| 元素               | 含义               |
| ------------------ | ------------------ |
| **✓ PROD**（绿色） | 生产环境右上角徽章 |
| **🛠 DEV**（橙色） | 开发环境右上角徽章 |

### 8.4 ⭐ 标注

| 含义        | 出现位置                                                              |
| ----------- | --------------------------------------------------------------------- |
| ⭐ 重点突出 | L4「ELT 管道」标题 + L7「部署层」标题 —— 强调这两层与传统架构差异最大 |

---

## 9. 端到端调用示例（生产环境）

> 场景：Agency Operator 在 Creative Engine 中点击 "为 Campaign Y 生成 5 个素材变体"

| 步  | 涉及层  | 动作                                                                                  |
| --- | ------- | ------------------------------------------------------------------------------------- |
| 1   | L1 → L2 | React 前端发 `POST /creative/generate` 到 FastAPI                                     |
| 2   | L2      | CORS → SecurityHeaders → HIPAA SessionGuard → RequestLogging → 路由到 Creative router |
| 3   | L3      | Creative Service 调 AI Brain；AI Brain 经 LLM Router 选 Claude Sonnet                 |
| 4   | L3 → L5 | Context Builder 从 Processed Lake `ai_context.*` 召回历史素材表现（PII-safe）         |
| 5   | L3 → L6 | AI Brain 经 httpx 调 OpenRouter → 路由到 Anthropic API；Langfuse 全程追踪             |
| 6   | L3 → L5 | 生成结果写回 `marts.creative_variants` (Processed Lake)                               |
| 7   | L3 → L1 | 通过 WebSocket 推送 "生成完成" 到前端，Operator 看到结果                              |
| 8   | 横切    | L7 Render 监控所有服务健康；Sentry 捕获异常；audit_events 记录全程                    |

---

## 10. 关联文档

- [Technical Solution (CN)](../psd/technical-solution.md) · [(EN)](../psd/technical-solution-en.md) — 技术方案完整描述
- [Network Diagram Explained](../psd/network-diagram-explained.md) — 网络数据流图释义
- [Architecture Schema Explained](../psd/architecture-schema-explained.md) — 架构方案图释义
- [ELT-ORCHESTRATION-PRIORITY](../ELT-ORCHESTRATION-PRIORITY.md) — Airflow vs Dagster 选型
- [ADR-002 Neon Tenancy](../ADR-002-NEON-TENANCY-OPTIMAL.md) — 多租户隔离决策
- [PII-DESIGN-SOLUTION](../PII-DESIGN-SOLUTION.md) — PII 设计方案
