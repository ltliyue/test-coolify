# ReceptivIQ Platform — 分层架构图说明

> 配套图：`dev-stack-layered.svg` / `.png`（含中文层名）
> 英文版：`dev-stack-layered-en.svg` / `.png`
> 设计原则：自上而下 7 层、ELT 模式（先保存后转换）、Coolify 统一管控

---

## 整体流程（端到端）

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. 用户在浏览器登录 ReceptivIQ                                  │
│    React/Vite/MUI + Google OAuth                                 │
└────────────────────────┬────────────────────────────────────────┘
                         ↓ HTTP/WS（认证 token）
┌─────────────────────────────────────────────────────────────────┐
│ 2. FastAPI 接收请求 → CORS → Security → HIPAA SessionGuard      │
│    → 路由分发到 21 个 router 之一                                │
└────────────────────────┬────────────────────────────────────────┘
                         ↓ auth + agency_id 过滤
┌─────────────────────────────────────────────────────────────────┐
│ 3. 业务服务执行：AI Brain 调 Agent，或业务 Service 查/写数据     │
│    ◇ AI 请求 ──── httpx ───→ OpenRouter（L6）→ Claude/Gemini    │
│    ◇ 业务请求 ── ORM ────→ PostgreSQL（L5）                     │
└────────────────────────┬────────────────────────────────────────┘
                         ↓ 数据 / 任务
┌─────────────────────────────────────────────────────────────────┐
│ 4. ELT 管道（独立调度）：                                        │
│    (1) Airflow 触发 → 9 个 Adapter 从外部平台 EXTRACT 原始数据   │
│    (2) 经 PHI/PII 合规过滤 → LOAD（写入 raw_* 表，不做业务转换）│
│    (3) dbt 在仓库内部 TRANSFORM：raw → staging → canonical → mart│
│    ◇ Celery 处理异步任务：PDF 生成、受众导出、预算告警           │
└────────────────────────┬────────────────────────────────────────┘
                         ↓ 保存 + 转换后
┌─────────────────────────────────────────────────────────────────┐
│ 5. 数据存储：PostgreSQL（业务）+ DuckDB（仓库，dev 唯一）        │
│    + Redis（缓存/队列）+ MinIO（PDF/凭证文件）                   │
└─────────────────────────────────────────────────────────────────┘

底层：Coolify 管控所有上述 Docker 服务（CI/CD、监控、密钥、备份）
```

---

## Layer 1 — Presentation 呈现层

**用户面对的 Web SPA**

| 框                                     | 含义                                                                                            |
| -------------------------------------- | ----------------------------------------------------------------------------------------------- |
| **React 19**                           | UI 框架（Component + Hooks）。19 是 2025 年发布的最新稳定版，含 React Compiler                  |
| **Vite**                               | 前端开发服务器和构建工具。比 webpack 快，热重载毫秒级                                           |
| **MUI (Material-UI)**                  | Google Material Design 风格的 React 组件库，全球最广泛使用的国际化 UI 库，企业 B2B 项目认可度高 |
| **Google OAuth**                       | 谷歌账号登录（第三方认证），不用自己存密码                                                      |
| **USER TYPES：Staff / Client / Admin** | 3 种角色——内部员工、客户、管理员，决定登录后看到的内容                                          |

---

## Layer 2 — API Gateway 接入层

**HTTP/WebSocket 入口 + 安全中间件**

| 框            | 含义                                                                |
| ------------- | ------------------------------------------------------------------- |
| **FastAPI**   | Python 异步 Web 框架，21 个 router 模块（auth/personas/reports 等） |
| **Uvicorn**   | ASGI 服务器，跑 FastAPI 应用的进程                                  |
| **WebSocket** | 长连接通道，`/ws` 端点用于实时通知（生成完成、告警等）              |

### 中间件链（每个 HTTP 请求依序经过）

| 中间件                 | 作用                                                 |
| ---------------------- | ---------------------------------------------------- |
| **CORS**               | 跨域控制——只允许配置的前端域名访问 API               |
| **Security Headers**   | 注入 `X-Frame-Options`、`HSTS`、`CSP` 等浏览器安全头 |
| **HIPAA SessionGuard** | 医疗合规要求：15 分钟不活动自动登出（Redis 跟踪）    |
| **Request Logging**    | 给每个请求注入 `request_id`，结构化日志便于追溯      |

---

## Layer 3 — Application 应用服务层

**AI 编排 + 9 个业务服务**

### AI 部分

| 框                              | 含义                                                                                        |
| ------------------------------- | ------------------------------------------------------------------------------------------- |
| **AI Brain**                    | LLM 路由器（`services/ai/brain.py`），收到请求 → 选 agent → 调 OpenRouter → 记录 token 用量 |
| **Persona**                     | 受众画像生成 agent（用 Claude Opus 4.7）                                                    |
| **Creative**                    | 创意/广告文案生成 agent（用 Claude Sonnet 4.6）                                             |
| **Attribution**                 | 归因分析 agent（用 Claude Sonnet 4.6）                                                      |
| **httpx → OpenRouter (direct)** | **不用 LangChain**，直接用 httpx 库调 OpenRouter HTTP API；JSON 输出强制约束                |
| **Langfuse SDK**                | 每次 LLM 调用的 prompt/completion/延迟/cost 追踪上报                                        |

### Business Services（9 个）

| 框                  | 含义                                                     |
| ------------------- | -------------------------------------------------------- |
| **Reports**         | PDF 报告生成（接 Celery + weasyprint）                   |
| **Audience Export** | 把 Persona 导出为 Meta/DV360 自定义受众                  |
| **Campaign**        | 跨平台 campaign 统一视图（查仓库 mart_campaign_unified） |
| **Budget Pacing**   | 预算节奏检测，偏离触发告警                               |
| **Notifs**          | 通知 CRUD + WebSocket 推送                               |
| **Brand**           | 品牌配置（颜色/字体/语调/禁用词）CRUD                    |
| **Field Mapping**   | 字段映射规则 CRUD + 4 种 transform                       |
| **OAuth**           | 平台 OAuth token 自动刷新（GA4/Meta/HubSpot/TikTok）     |
| **Platform Reg**    | 12 个集成平台的元数据注册表                              |

---

## Layer 4 — ELT Pipeline ⭐ 转换层

**Extract-Load-Transform：先保存原始数据，再在仓库内部转换**

### 编排器（Orchestration）

| 框          | 含义                                                                                                                                   |
| ----------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| **Airflow** | ETL DAG 调度器（webserver + scheduler），按日/小时自动触发同步                                                                         |
| **Celery**  | 异步任务队列。**用途**：PDF 生成（weasyprint 耗时数秒）、受众导出（外部 API 慢）、预算告警（定时 Celery beat）、报告调度（每小时检查） |

### 9 个 Extract Adapters

每个 adapter 实现 `fetch()` → `transform()` → `get_raw_table()` 三个方法：

| Adapter        | 平台类型   | 用途                                 |
| -------------- | ---------- | ------------------------------------ |
| **GA4**        | 分析       | Google Analytics 4 网站/App 数据     |
| **Meta**       | 广告       | Facebook/Instagram 广告 campaign     |
| **HubSpot**    | CRM        | 联系人/Lead/Deal 数据                |
| **DV360**      | 程序化广告 | Google Display & Video 360           |
| **StackAdapt** | 程序化广告 | 原生广告投放平台                     |
| **LeadRX**     | 归因       | 多触点归因数据（conversion_id 哈希） |
| **LiveRamp**   | 身份解析   | 跨设备身份匹配（segment_id 哈希）    |
| **Quorum**     | 受众行为   | 政治/倡导活动行为数据                |
| **TikTok**     | 视频广告   | TikTok Ads campaign                  |

### 合规过滤（Compliance）

| 框                            | 含义                                                                                                           |
| ----------------------------- | -------------------------------------------------------------------------------------------------------------- |
| **PHI Detector + Anonymizer** | 入仓前**强制**通过：扫描 HIPAA 18 类标识符 + SHA-256 哈希 PII + IP 截断（IPv4→/24，IPv6→/48）；agency 盐值隔离 |

### dbt（仓库内转换）

| 框                      | 含义                                                                                                                                                                                                         |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **dbt Core**            | 在数据仓库内执行 SQL 转换（不下载到本地），编排"清洗 → 合并 → 映射 → 聚合"四阶段管道                                                                                                                         |
| **清洗 (Clean)** 🔻     | 把各平台 `raw_*` 表的原始字段标准化（统一字段名/格式），如 Meta 的 `spend` 和 GA4 的 `cost` 都映射为 canonical 的 `cost_usd`                                                                                 |
| **合并 (Merge)** ◇      | 跨平台事件合并去重到统一表，把多个广告平台 + CRM 的同一用户行为整合到一条时间线                                                                                                                              |
| **映射 (Map)** 🔗       | **三方原始字段 → 业务实体字段**的映射规则。每个平台的字段通过映射表转换为内部业务实体的字段（direct 直传 / value_mapping 值映射 / unit_conversion 单位转换 / formula 公式）。Phase 2+ 计划支持租户自定义实体 |
| **聚合 (Aggregate)** 📊 | 生成业务面向的报表数据：campaign performance / attribution / persona signals 等                                                                                                                              |

---

## Layer 5 — Data Storage 数据层

**OLTP + OLAP + 缓存 + 对象存储**

| 框                | 含义                                                                                                   |
| ----------------- | ------------------------------------------------------------------------------------------------------ |
| **PostgreSQL 18** | 业务库（OLTP）。最新稳定版（2025-09 发布），含 `pgvector` 扩展支持向量嵌入。19 个 ORM 模型 / 18 个迁移 |
| **DuckDB**        | 数据仓库（单文件、进程内、零运维）。**开发环境唯一仓库**，生产环境后续可扩展为 Snowflake 等 OLAP       |
| **Redis 7**       | 多用途：缓存层、Celery broker（任务队列）、JWT 黑名单、HIPAA session 跟踪。db0/1/2 分配                |
| **MinIO**         | S3 兼容对象存储，存 PDF 报告 + 凭证文件（开发用 MinIO，生产可换 AWS S3）                               |

**字段提示**：

- `19 ORM models` — SQLAlchemy 模型数量
- `18 migrations` — 数据库迁移脚本数（`infra/migrations/001_.._018_`）
- `Dev environment (DuckDB only)` — 开发期不部署 Snowflake，DuckDB 单文件即可
- `Encrypted @ rest (AES-256)` — Fernet 加密敏感字段（email/凭证）

---

## Layer 6 — External Services 外部服务层

**LLM + 可观测性 + 9 个数据源平台**

### LLM Stack

| 框                    | 含义                                                                               |
| --------------------- | ---------------------------------------------------------------------------------- |
| **OpenRouter**        | LLM 统一网关，一个 API key 调多家模型供应商                                        |
| **Claude Opus 4.7**   | Anthropic 顶级模型（1M context），用于 Persona Agent 深度推理                      |
| **Claude Sonnet 4.6** | Anthropic 高效模型（200K context），用于 Creative/Attribution Agent 和默认文本任务 |
| **Gemini 2.5 Flash**  | Google 多模态模型，用于图像处理任务                                                |

### Observability

| 框           | 含义                                                         |
| ------------ | ------------------------------------------------------------ |
| **Langfuse** | LLM 调用追踪 dashboard（每个 prompt/completion/cost 都可查） |
| **Sentry**   | 应用错误监控（异常自动上报 + 性能追踪）                      |

### Data Sources（9 个，同 Layer 4 的 Adapter 对应）

GA4 / Meta / HubSpot / DV360 / StackAdapt / TikTok / LeadRX / LiveRamp / Quorum

---

## Layer 7 — Infrastructure ⭐ 部署层

**Coolify 统一管控所有 Docker 服务**

| 框          | 含义                                                                                               |
| ----------- | -------------------------------------------------------------------------------------------------- |
| **Coolify** | **开源 PaaS 控制平面**——图形界面管理服务器/应用/数据库/Docker/环境变量/CI/CD。团队不用手写运维脚本 |
| **Docker**  | 容器运行时（所有 9 个服务跑在容器内）                                                              |
| **GitHub**  | 源码托管 + Webhook 触发 Coolify 自动部署                                                           |

### Coolify 管的 4 件事

| 能力                 | 说明                                            |
| -------------------- | ----------------------------------------------- |
| Docker orchestration | 一键启停所有容器，管理 docker-compose-like 编排 |
| GitOps CI/CD         | GitHub push → 自动 build → 滚动部署             |
| Env vars + DB backup | 环境变量集中管理 + PostgreSQL/Redis 一键备份    |
| Monitoring + Logs    | 容器健康检查 + 日志聚合                         |

### Coolify-Managed Containers（9 个）

| 容器            | 服务                       |
| --------------- | -------------------------- |
| `backend`       | FastAPI 应用               |
| `celery`        | Celery worker              |
| `frontend`      | Vite dev server / 静态文件 |
| `redis`         | 缓存 + 队列                |
| `minio`         | 对象存储                   |
| `langfuse`      | LLM 观测 dashboard         |
| `airflow-init`  | DB schema 初始化（一次性） |
| `airflow-web`   | Airflow Web UI             |
| `airflow-sched` | Airflow 调度器             |

### COOLIFY MANAGEMENT BOUNDARY（虚线框）

虚线大框覆盖 Layer 2-7，表示这些层的所有容器化服务都由 Coolify 统一管理。

---

## 数据流箭头说明

| 箭头颜色                    | 含义                   | 路径                                                                   |
| --------------------------- | ---------------------- | ---------------------------------------------------------------------- |
| 🔵 **青色 (User Traffic)**  | 用户 HTTP/WS 请求      | L1 → L2 → L3                                                           |
| 🟣 **粉色 (LLM Calls)**     | AI Agent 调 OpenRouter | L3 Agent → 左侧通道 → L6 OpenRouter                                    |
| 🟢 **绿色 (ETL/ELT Data)**  | 数据流的三步骤         | (1) EXTRACT (L6→L4)、(2) LOAD raw\_\* (L4→L5)、TRANSFORM (L4 dbt 内部) |
| 🟪 **紫色 (Compliance)**    | 合规过滤路径           | 在 Layer 4 内部                                                        |
| 🟡 **橙色 (Deploy/Manage)** | Coolify 管控           | 虚线大框                                                               |

**特殊：**

- `ORM writes`（紫色虚线）：业务服务直接写 PostgreSQL，跳过 ELT 管道（事务型写入）
- `httpx → LLM`（粉色，走左侧高速通道 x=252）
- `(1) EXTRACT` 和 `(2) LOAD raw_*`（绿色，走右侧高速通道 x=1620）

---

## ELT 三步流程（重点）

```
┌───────────────────┐  (1) EXTRACT
│ L6 External APIs  │ ──────────────→  L4 Adapter.fetch()
└───────────────────┘                    │
                                         │ PHI scan + anonymize
                                         ↓ (强制合规过滤)
                              ┌──────────────────────┐  (2) LOAD
                              │ raw record (cleaned) │ ─→ INSERT into raw_*
                              └──────────────────────┘     │
                                                            ↓
                                          ┌────────────────────────────┐
                                          │ L5 DuckDB (dev warehouse)   │
                                          │   raw_ga4_events            │
                                          │   raw_meta_ads              │
                                          │   raw_hubspot_contacts      │
                                          │   raw_quorum / leadrx / ... │
                                          └────────────────────────────┘
                                                            ↑ 仓库内 SQL
                                                            │ (3) TRANSFORM
                              ┌──────────────────────────────────────┐
                              │ dbt models (in-warehouse SQL)         │
                              │   staging (view)                      │
                              │     ↓                                 │
                              │   canonical_events (incremental)      │
                              │     ↓                                 │
                              │   marts/* (table)                     │
                              └──────────────────────────────────────┘
```

**ELT vs ETL**：本平台是 ELT（先 Load 后 Transform）。adapter 只做最小合规处理然后立刻保存原始数据，所有业务转换（join/聚合/字段映射）都在仓库内用 dbt SQL 完成。优势：

1. 原始数据保留，转换出错可重跑
2. 转换利用仓库的并行计算能力（DuckDB 列存，生产可扩展 Snowflake MPP）
3. 数据分析师能直接写 SQL 调整 mart 层逻辑

---

## 平台统计

| 指标         | 数值                                                                      |
| ------------ | ------------------------------------------------------------------------- |
| API Routers  | 21                                                                        |
| ORM Models   | 19                                                                        |
| Migrations   | 18                                                                        |
| ETL Adapters | 9                                                                         |
| dbt Models   | 13（9 staging + 1 canonical + 3 marts，加上 mart_campaign_unified 共 14） |
| Tests        | 189                                                                       |

---

## 关键设计决策

| 决策                    | 理由                                                             |
| ----------------------- | ---------------------------------------------------------------- |
| **不用 LangChain**      | 直接 httpx 调 OpenRouter 更可控，避免不必要抽象层                |
| **ELT 而非 ETL**        | 保留原始数据 + 利用仓库算力 + dbt 是行业标准                     |
| **开发环境只用 DuckDB** | 单文件零运维，无需 Snowflake 账号和成本；生产环境后续可扩展      |
| **Coolify 替代 Render** | 自托管 PaaS，避免厂商锁定 + 数据本地化（合规要求）               |
| **PostgreSQL 18**       | 最新稳定版含异步 I/O / UUIDv7 / 虚拟生成列改进                   |
| **Celery 仅承担 async** | 不做 ETL（ETL 由 Airflow 调度），只处理 user-blocking 的耗时任务 |
| **per-tenant 加密**     | Fernet + agency_id 盐，跨租户数据物理隔离                        |

---

> 生成脚本：`dev-stack-layered.py`（中文层名）+ `dev-stack-layered-en.py`（纯英文）
> 重新生成：`cd docs/diagrams && python3 dev-stack-layered.py`
