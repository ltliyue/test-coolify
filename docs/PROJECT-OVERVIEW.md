# ReceptivIQ Platform — 项目详细说明文档

> **版本**：v1.0 | **日期**：2026-04-01
> **定位**：AI-native Agency OS — GDPR · CCPA · HIPAA 合规的营销代理智能运营平台

---

## 一、项目概述

### 1.1 项目背景

营销代理公司日常使用 50+ 个独立工具（Google Analytics、Meta Ads Manager、HubSpot、TikTok Ads 等），导致数据孤岛、手工协调成本高、跨平台归因困难。ReceptivIQ 通过统一数据仓库 + AI Agent 架构，将 **研究 → 创意 → 投放 → 归因** 完整营销链路自动化。

### 1.2 核心价值

| 价值主张      | 说明                                                                                 |
| ------------- | ------------------------------------------------------------------------------------ |
| **统一数据**  | GA4 / Meta Ads / HubSpot 等多平台数据自动 ETL 到统一仓库，消除数据孤岛               |
| **AI 三支柱** | Persona Agent（受众洞察）+ Creative Agent（创意生成）+ Attribution Agent（归因分析） |
| **合规优先**  | GDPR / CCPA / HIPAA 三法规同时满足，Privacy by Design 嵌入每一层                     |
| **多租户**    | Agency → Client 二级租户体系，完整的数据隔离和白标支持                               |

### 1.3 技术栈一览

```
后端框架    ：Python 3.9 + FastAPI（async）+ SQLAlchemy 2.0
任务队列    ：Celery + Redis
ETL 调度    ：Apache Airflow 2.9
数据转换    ：dbt（staging → canonical → marts 三层）
数据仓库    ：DuckDB（开发）/ Snowflake（生产）
业务数据库  ：PostgreSQL 14+（本地）/ Neon Serverless（生产）
对象存储    ：MinIO（本地）/ S3（生产）
AI 模型路由 ：OpenRouter（统一接入 Claude / GPT / Gemini）
LLM 追踪   ：Langfuse
错误监控    ：Sentry
前端        ：React 19 + TypeScript + Vite + Ant Design（规划中）
部署        ：Docker Compose（本地）→ Render（生产）
```

---

## 二、系统架构

### 2.1 整体分层

```
┌─────────────────────────────────────────────────────────────┐
│  Frontend Layer                                              │
│  React SPA（Ops View + Client Portal）                       │
│  ↕ REST API / WebSocket                                      │
├──────────────────────────────────────────────────────────────┤
│  API Layer — FastAPI (/api/v1)                               │
│  61 端点 · 15 路由模块 · JWT 认证 · RBAC                     │
│  ┌────────────────────────────────────────────────────┐      │
│  │ 中间件栈（洋葱模型，外层先注册 = 最后执行）          │      │
│  │ SecurityHeaders → RequestLogging → SessionGuard     │      │
│  │ → CORS → 路由处理                                   │      │
│  └────────────────────────────────────────────────────┘      │
├──────────────────────────────────────────────────────────────┤
│  Service Layer                                               │
│  ┌──────────┐ ┌───────────┐ ┌──────────┐ ┌──────────────┐  │
│  │ AI Brain │ │ ETL Runner│ │ Field    │ │ Notification │  │
│  │ ├ Persona│ │ ├ GA4     │ │ Mapping  │ │ ├ Dispatcher │  │
│  │ ├Creative│ │ ├ Meta    │ │ Engine   │ │ └ WS Manager │  │
│  │ └Attrib. │ │ └ HubSpot│ │          │ │              │  │
│  └──────────┘ └───────────┘ └──────────┘ └──────────────┘  │
├──────────────────────────────────────────────────────────────┤
│  Compliance Layer（合规层 — 嵌入所有层）                      │
│  PHI Detector · Anonymizer · SessionGuard · PII Crypto       │
│  Audit Logger · Consent Manager · DSAR Handler               │
├──────────────────────────────────────────────────────────────┤
│  Data Layer                                                  │
│  ┌────────────┐  ┌──────────────┐  ┌──────────┐            │
│  │ PostgreSQL │  │ Snowflake /  │  │  MinIO   │            │
│  │ (业务数据) │  │ DuckDB(仓库) │  │ (文件)   │            │
│  └────────────┘  └──────────────┘  └──────────┘            │
├──────────────────────────────────────────────────────────────┤
│  Infrastructure Layer                                        │
│  Redis · Celery · Airflow · Sentry · Langfuse                │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 数据流架构

```
                     ┌─── GA4 API ───┐
                     │               │
用户请求 ──→ FastAPI │── Meta Ads ───├──→ ETL Runner
                     │               │      │
                     └── HubSpot ────┘      ↓
                                     PHI 检测 → 匿名化
                                            │
                                            ↓
                                    ┌───────────────┐
                                    │  DuckDB /     │
                                    │  Snowflake    │
                                    │  (RAW 层)     │
                                    └───────┬───────┘
                                            │ dbt
                                    ┌───────┴───────┐
                                    │  staging →    │
                                    │  canonical →  │
                                    │  marts        │
                                    └───────┬───────┘
                                            │
                    ┌───────────────────────┼─────────────────┐
                    │                       │                 │
            ┌───────┴───────┐  ┌────────────┴──┐  ┌──────────┴───┐
            │ Persona Agent │  │Creative Agent │  │ Attribution  │
            │ (Claude Opus) │  │(Claude Sonnet)│  │ Agent(Sonnet)│
            └───────────────┘  └───────────────┘  └──────────────┘
```

### 2.3 多租户架构

```
Agency（代理公司） ← 顶层租户
  ├── brand_config JSONB（品牌配置）
  ├── monthly_token_budget（AI Token 预算）
  │
  ├── Client A（客户品牌）
  │     ├── brand_config JSONB（白标覆盖）
  │     └── verticals: ["B2B SaaS", "Fintech"]
  │
  ├── Client B
  │     └── ...
  │
  ├── Users
  │     ├── agency_admin — 全权管理
  │     ├── agency_ops   — 运营操作（无删除权限）
  │     └── client_viewer — 客户只读（门户视图）
  │
  └── Integrations / Credentials / Personas / Creatives ...
        └── 所有表均含 agency_id（强制 NOT NULL），查询必须过滤
```

**租户隔离规则**：

- 所有 ORM 模型的 `agency_id` 为 NOT NULL（L-01 合规修复）
- 所有 API 端点从 `current_user.agency_id` 提取租户标识，不接受前端传入
- WebSocket 连接以 `{agency_id}:{user_id}` 为 key，防止跨租户消息泄露
- 数据仓库按 `agency_id` 分区隔离

---

## 三、后端详细架构

### 3.1 目录结构

```
backend/
├── app/
│   ├── main.py                     # FastAPI 应用入口 + 中间件注册
│   ├── worker.py                   # Celery 应用入口
│   ├── api/v1/                     # REST API 路由（15 个模块）
│   │   ├── router.py              # 路由聚合（/api/v1 前缀）
│   │   ├── auth.py                # 认证（登录/OAuth/刷新/登出/me）
│   │   ├── tenants.py             # Agency + Client CRUD
│   │   ├── credentials.py         # 凭证加密存储
│   │   ├── integrations.py        # 平台连接/断开/同步触发
│   │   ├── oauth_callback.py      # 平台 OAuth 回调（HMAC CSRF）
│   │   ├── compliance.py          # GDPR/CCPA/HIPAA 合规 API
│   │   ├── ai.py                  # AI Chat + Token 用量查询
│   │   ├── brands.py              # 品牌配置 CRUD
│   │   ├── imports.py             # CSV 历史数据导入
│   │   ├── field_mappings.py      # 字段映射 CRUD + 版本管理
│   │   ├── personas.py            # Persona CRUD + AI 生成
│   │   ├── creatives.py           # AI 创意生成
│   │   ├── attribution.py         # AI 归因分析
│   │   ├── portal.py              # 客户门户只读视图
│   │   ├── notifications.py       # 通知 CRUD
│   │   ├── health.py              # 深度健康检查
│   │   └── ws.py                  # WebSocket 实时连接
│   │
│   ├── core/                       # 基础设施
│   │   ├── config.py              # Pydantic Settings（所有配置集中管理）
│   │   ├── database.py            # SQLAlchemy 异步引擎（asyncpg）
│   │   ├── sync_database.py       # 同步引擎（Celery Worker 用）
│   │   ├── security.py            # JWT 创建/解码/撤销 + bcrypt
│   │   ├── encryption.py          # Fernet 对称加密（凭证 + PII）
│   │   ├── pii_crypto.py          # 用户 PII 加密/哈希
│   │   ├── deps.py                # FastAPI 依赖注入（认证 + 授权）
│   │   ├── audit.py               # 审计日志写入
│   │   ├── monitoring.py          # Sentry + Langfuse + RequestLogging
│   │   ├── warehouse_client.py    # DuckDB / Snowflake 双后端
│   │   ├── storage.py             # MinIO 对象存储
│   │   ├── health.py              # 三组件健康检查
│   │   └── compliance/            # 合规组件
│   │       ├── anonymizer.py      # PII 匿名化工具集
│   │       ├── phi_detector.py    # HIPAA PHI 检测器
│   │       └── session_guard.py   # HIPAA 会话超时中间件
│   │
│   ├── models/                     # SQLAlchemy ORM（16 个模型）
│   │   ├── agency.py              # Agency（status/plan/brand_config/token_budget）
│   │   ├── client.py              # Client（verticals/brand_config 白标）
│   │   ├── user.py                # User（PII 加密 + email_hash 查找）
│   │   ├── credential.py          # Credential（Fernet 加密存储）
│   │   ├── integration.py         # Integration（12 平台 + 连接状态）
│   │   ├── sync_log.py            # SyncLog（ETL 同步追踪）
│   │   ├── consent.py             # ConsentRecord（GDPR 同意记录）
│   │   ├── dsar.py                # DSARRequest（数据主体请求）
│   │   ├── audit_log.py           # AuditLog（INSERT-only 不可变）
│   │   ├── token_usage.py         # TokenUsage（LLM Token 用量）
│   │   ├── field_mapping.py       # FieldMapping + Version（版本管理）
│   │   ├── persona.py             # Persona（心理画像 + 渠道偏好）
│   │   ├── creative.py            # Generation + GenerationResult
│   │   ├── attribution.py         # AttributionReport
│   │   ├── notification.py        # Notification（分类/严重度/已读）
│   │   └── enums.py               # 共享枚举（12 平台/6 同意目的/6 DSAR 类型）
│   │
│   ├── schemas/                    # Pydantic 请求/响应模型（14 个模块）
│   │
│   ├── services/                   # 业务逻辑层
│   │   ├── ai/                    # AI Agent 服务
│   │   │   ├── brain.py           # 中心路由器（请求分发 + Token 计费）
│   │   │   ├── context.py         # 共享上下文组装（品牌 + 预算）
│   │   │   └── agents/
│   │   │       ├── base.py        # Agent 抽象基类
│   │   │       ├── persona.py     # Persona Agent（Claude Opus）
│   │   │       ├── creative.py    # Creative Agent（Claude Sonnet）
│   │   │       └── attribution.py # Attribution Agent（Claude Sonnet）
│   │   │
│   │   ├── etl/                   # ETL 管道
│   │   │   ├── base.py            # BaseAdapter 抽象接口
│   │   │   ├── runner.py          # ETLRunner（4 阶段管道）
│   │   │   ├── historical_importer.py # CSV 导入
│   │   │   └── adapters/
│   │   │       ├── ga4.py         # Google Analytics 4 适配器
│   │   │       ├── meta_ads.py    # Meta Ads 适配器
│   │   │       └── hubspot.py     # HubSpot CRM 适配器
│   │   │
│   │   ├── field_mapping/         # 字段映射服务
│   │   │   ├── canonical_schema.py # 46 个标准字段定义
│   │   │   ├── transform.py       # TransformEngine（4 种变换）
│   │   │   ├── template_loader.py # 平台模板加载
│   │   │   └── templates/         # 6 个平台默认模板 JSON
│   │   │
│   │   ├── notifications/         # 通知服务
│   │   │   ├── manager.py         # WebSocket ConnectionManager
│   │   │   └── dispatcher.py      # 通知创建 + 自动推送
│   │   │
│   │   ├── oauth/
│   │   │   └── token_refresh.py   # OAuth Token 自动刷新
│   │   └── platform_registry.py   # 12 平台注册表
│   │
│   └── tasks/                      # Celery 异步任务
│       └── etl_tasks.py           # ETL 同步 + dbt 转换任务
│
├── dags/                           # Airflow DAG 定义
│   └── etl_sync_dag.py           # GA4/Meta/HubSpot 并行 → dbt
│
├── tests/                          # 测试套件（16 个文件，135 用例）
├── Dockerfile                     # 容器镜像（Python 3.9-slim）
├── requirements.txt               # Python 依赖
└── pytest.ini                     # 测试配置
```

### 3.2 API 端点清单（61 个端点）

| 路由模块            | 前缀                  | 端点数 | 认证      | 说明                                                       |
| ------------------- | --------------------- | ------ | --------- | ---------------------------------------------------------- |
| `auth.py`           | `/auth`               | 5      | 部分      | 登录（M-10 限流）/Google OAuth/刷新/登出（C-04 撤销）/me   |
| `tenants.py`        | `/tenants`            | 5      | ✅        | Agency + Client CRUD（admin 权限）                         |
| `credentials.py`    | `/credentials`        | 3      | ✅        | 凭证 Fernet 加密 CRUD                                      |
| `integrations.py`   | `/integrations`       | 4      | ✅        | 平台连接/断开/列表/同步触发（Celery 分发）                 |
| `oauth_callback.py` | `/integrations/oauth` | 2      | ✅        | OAuth 授权 URL + 回调（C-01 HMAC CSRF）                    |
| `compliance.py`     | `/compliance`         | 5      | ✅        | Consent 管理 + DSAR 工作流（M-06 租户隔离）                |
| `ai.py`             | `/ai`                 | 2      | ✅        | AI Chat（OpenRouter）+ 月度 Token 用量                     |
| `brands.py`         | `/brands`             | 3      | ✅        | 品牌配置 GET/PUT/DELETE + 审计日志                         |
| `imports.py`        | `/import`             | 1      | ✅        | CSV 上传（三平台自动检测 + PHI 扫描）                      |
| `field_mappings.py` | `/field-mappings`     | 10     | ✅        | CRUD + 版本 + 回滚 + 预览 + 模板                           |
| `personas.py`       | `/personas`           | 6      | ✅        | 手动/AI 创建 + CRUD + 软删除                               |
| `creatives.py`      | `/creatives`          | 3      | ✅        | AI 多平台创意生成 + 列表 + 详情                            |
| `attribution.py`    | `/attribution`        | 3      | ✅        | AI 归因报告生成 + 列表 + 详情                              |
| `portal.py`         | `/portal`             | 5      | ✅        | 客户门户只读（dashboard/brand/personas/creatives/reports） |
| `notifications.py`  | `/notifications`      | 4      | ✅        | 列表/未读计数/标记已读/全部已读                            |
| `health.py`         | `/health`             | 1      | ❌        | 深度健康检查（DB + Redis + Warehouse）                     |
| `ws.py`             | `/ws`                 | 1      | JWT Query | WebSocket 实时连接（ping/pong 心跳）                       |

### 3.3 中间件栈

中间件遵循 Starlette 洋葱模型（外层先注册 = 最后执行），请求从外到内，响应从内到外：

```
请求 ──→ SecurityHeaders ──→ RequestLogging ──→ HIPAASessionGuard ──→ CORS ──→ 路由
响应 ←── SecurityHeaders ←── RequestLogging ←── HIPAASessionGuard ←── CORS ←── 路由
```

| 中间件                      | 职责                                                                 | 合规标记 |
| --------------------------- | -------------------------------------------------------------------- | -------- |
| `SecurityHeadersMiddleware` | HSTS / X-Frame-Options:DENY / nosniff / Referrer-Policy              | M-11     |
| `RequestLoggingMiddleware`  | X-Request-Id 注入 + 结构化访问日志（method/path/status/duration）    | —        |
| `HIPAASessionGuard`         | 15 分钟 PHI 端点超时 / 60 分钟普通超时（Redis + 内存 LRU 双层）      | M-05     |
| `CORSMiddleware`            | 环境变量 `CORS_ORIGINS` 控制，限定 GET/POST/PUT/PATCH/DELETE/OPTIONS | M-01     |

### 3.4 认证与授权体系

```
┌──────────────────────────────────────────────────────┐
│                    认证流程                            │
│                                                       │
│  登录 → JWT（含 jti）→ Authorization: Bearer <token>  │
│                                                       │
│  ┌──────────────────────────────────────────────┐    │
│  │ get_current_user()                            │    │
│  │   1. 提取 Bearer Token                        │    │
│  │   2. decode_token() → 校验签名+过期+jti黑名单 │    │
│  │   3. 查数据库 → User(is_active=True)          │    │
│  │   4. 注入 request.state.user_id/agency_id     │    │
│  └──────────────────────────────────────────────┘    │
│                                                       │
│  角色权限                                             │
│  ┌──────────────┬────────────────────────────────┐   │
│  │ agency_admin │ 全权（CRUD + 管理 + 集成配置）  │   │
│  │ agency_ops   │ 运营操作（创建/查看，无删除）   │   │
│  │ client_viewer│ 只读（/portal 门户视图）        │   │
│  └──────────────┴────────────────────────────────┘   │
│                                                       │
│  安全增强                                             │
│  · M-10: IP 限流（5 次/5 分钟 → 锁定 15 分钟）       │
│  · C-04: JWT jti + Redis 黑名单（logout 即失效）      │
│  · C-01: OAuth state HMAC 签名 + 10 分钟过期          │
│  · C-05: 生产启动校验 SECRET_KEY ≥ 32 字符            │
└──────────────────────────────────────────────────────┘
```

---

## 四、AI Agent 架构

### 4.1 AI Brain 路由器

所有 AI 调用通过中心路由器 `brain.py` 分发，统一管理模型选择、Token 计费和审计。

```
用户请求
    │
    ▼
┌──────────────────────────────────────────────────┐
│  AI Brain (brain.py)                              │
│                                                    │
│  1. 组装 SharedContext（品牌配置 + Token 预算）     │
│  2. 检查 Agency 月度 Token 预算（超限 → 429）       │
│  3. 路由到对应 Agent                                │
│  4. 调用 OpenRouter API                             │
│  5. 记录 TokenUsage（agency/model/agent 维度）      │
│  6. 写入审计日志                                    │
│  7. 返回 AgentResponse                              │
└──────┬───────────────────────────────────────────┘
       │
       ├──→ Persona Agent（Claude Opus — 深度推理）
       │     └─ 输出：结构化 Persona 对象（人口属性/心理画像/渠道偏好）
       │
       ├──→ Creative Agent（Claude Sonnet — 高效生成）
       │     └─ 输出：四平台文案（Meta/Google/TikTok/Display）
       │
       └──→ Attribution Agent（Claude Sonnet）
             └─ 输出：多触点归因报告（渠道贡献度/ROAS/建议）
```

### 4.2 OpenRouter 集成

| 配置项           | 环境变量                | 默认值                        | 说明               |
| ---------------- | ----------------------- | ----------------------------- | ------------------ |
| API 密钥         | `OPENROUTER_API_KEY`    | —（空则 mock 模式）           | OpenRouter API Key |
| Persona 模型     | `PERSONA_MODEL`         | `anthropic/claude-opus-4-6`   | 深度推理           |
| Creative 模型    | `CREATIVE_MODEL`        | `anthropic/claude-sonnet-4-6` | 高效生成           |
| Attribution 模型 | `ATTRIBUTION_MODEL`     | `anthropic/claude-sonnet-4-6` | 分析推理           |
| 通用模型         | `OPENROUTER_TEXT_MODEL` | `anthropic/claude-sonnet-4-6` | AI Chat            |

**Token 预算控制**：

```
每个 Agency 有 monthly_token_budget（默认 1,000,000）
  ├── 每次 AI 调用记录到 token_usage 表
  ├── 查询当月累计用量
  ├── 超限 → 返回 HTTP 429
  └── GET /api/v1/ai/usage/monthly 查看详情
      → { total_tokens, total_cost_usd, budget_remaining, by_model, by_agent }
```

### 4.3 SharedContext

每次 AI 调用自动组装上下文，注入品牌信息和预算状态：

```python
SharedContext:
  agency_id, client_id          # 租户标识
  brand_name                    # 品牌名称（来自 Agency.brand_config）
  brand_voice                   # 品牌调性
  industry                      # 行业
  target_audience               # 目标受众
  monthly_token_budget           # 月度预算
  tokens_used_this_month         # 当月已用（从 TokenUsage 聚合）
  budget_remaining               # 剩余预算
  extra: Dict                   # Agent 专属上下文
```

---

## 五、ETL 数据管道

### 5.1 管道流程

```
┌──────────────────────────────────────────────────────────────┐
│  ETL Pipeline（4 阶段）                                       │
│                                                               │
│  1. Extract — adapter.fetch(start_date, end_date, cursor)    │
│     ├── GA4 Adapter     → Google Analytics Data API v1       │
│     ├── Meta Ads Adapter → Facebook Graph API v19             │
│     └── HubSpot Adapter  → CRM v3 Contacts API              │
│                                                               │
│  2. Compliance —                                              │
│     ├── PHI 检测：scan_record() HIPAA Safe Harbor 18 类       │
│     ├── 匿名化：hash_identifier() + truncate_ip()            │
│     └── PII 字段哈希（email/phone/name + 租户盐值）           │
│                                                               │
│  3. Load — warehouse.insert_many(table, records)              │
│     ├── SQL 前缀白名单校验（H-02/H-03 防注入）               │
│     ├── 表名白名单 + 列名正则校验                              │
│     └── 写入 DuckDB（开发）或 Snowflake（生产）               │
│                                                               │
│  4. State — warehouse.update_sync_state(cursor, count)       │
│     └── 支持断点续传（游标分页）                               │
└──────────────────────────────────────────────────────────────┘
```

### 5.2 触发方式

| 方式                 | 入口                                  | 说明                                          |
| -------------------- | ------------------------------------- | --------------------------------------------- |
| **API 手动触发**     | `POST /api/v1/integrations/{id}/sync` | 分发 Celery 任务                              |
| **Airflow 定时调度** | `dags/etl_sync_dag.py`                | 每日触发：GA4/Meta/HubSpot 并行 → dbt 转换    |
| **CSV 导入**         | `POST /api/v1/import/upload`          | 上传文件 → 自动检测平台 → PHI 扫描 → 写入仓库 |

### 5.3 适配器接口

```python
class BaseAdapter(ABC):
    platform: str                    # "ga4" | "meta_ads" | "hubspot"
    credentials: dict                # OAuth token / API key
    agency_id: str
    client_id: Optional[str]

    @abstractmethod
    def fetch(self, start_date, end_date, cursor) -> tuple[list[dict], Optional[str]]:
        """拉取原始数据，返回 (records, next_cursor)"""

    @abstractmethod
    def get_raw_table(self) -> str:
        """对应的仓库原始表名"""

    def transform(self, record: dict) -> Optional[dict]:
        """可选：记录级变换（默认直通）"""
```

### 5.4 dbt 转换层

```
RAW 层（ETL 直接写入）
  ├── raw_ga4_events
  ├── raw_meta_ads
  └── raw_hubspot_contacts
          │
          ↓ dbt staging（View 物化，1:1 映射）
  ├── stg_ga4        — 标准化列名 + 类型转换
  ├── stg_meta_ads   — spend → spend_usd，link_clicks → clicks
  └── stg_hubspot    — deal_stage → event_type，contact 去标识化
          │
          ↓ dbt canonical（Incremental，跨平台统一）
  └── canonical_events — UNION ALL 三平台，46 个标准字段
          │
          ↓ dbt marts（Table 物化，业务聚合）
  ├── mart_campaign_performance — campaign 维度性能汇总（CTR/CPC/ROAS）
  ├── mart_persona_signals      — 受众信号聚合（Persona Agent 输入）
  └── mart_attribution          — 渠道归因（贡献度/花费占比/ROAS）
```

---

## 六、合规架构（GDPR · CCPA · HIPAA）

### 6.1 五层合规体系

```
Layer 5  Compliance API (/api/v1/compliance)
         DSAR 工作流 · 同意管理 · 违规通知
         ─────────────────────────────────
Layer 4  Application Middleware
         SessionGuard · SecurityHeaders · 登录限流
         ─────────────────────────────────
Layer 3  Service Layer
         PHI Detector · Anonymizer · PII Crypto · Audit
         ─────────────────────────────────
Layer 2  Data Layer
         字段加密 · email_hash 查找 · INSERT-only 审计表
         ─────────────────────────────────
Layer 1  Infrastructure
         TLS · AES-256 · Redis 加密连接 · 密钥管理
```

### 6.2 合规控制点清单（36 项，4 轮审计全部通过）

#### 数据加密与隐私

| ID   | 控制点                  | 实现                                       |
| ---- | ----------------------- | ------------------------------------------ |
| M-02 | 用户 email 加密存储     | Fernet 加密，email_hash SHA-256 查找       |
| M-03 | 用户 full_name 加密存储 | Fernet 加密，API 返回时解密                |
| M-04 | IP 地址截断             | consent_records.ip_address 截断为 /24 网段 |
| C-03 | DSAR 数据最小化         | subject_email_hash 哈希，不存明文姓名      |
| M-08 | 日志不暴露 PII          | HubSpot API 错误只记录异常类名             |

#### 认证安全

| ID   | 控制点     | 实现                                  |
| ---- | ---------- | ------------------------------------- |
| M-10 | 登录限流   | 5 次/5 分钟失败 → IP 锁定 15 分钟     |
| C-04 | JWT 撤销   | jti + Redis 黑名单（TTL 自动清理）    |
| C-01 | OAuth CSRF | HMAC 签名 state + 10 分钟过期         |
| C-05 | 弱密钥阻止 | 生产启动校验 SECRET_KEY ≥ 32 字符     |
| M-01 | CORS 限制  | 环境变量控制来源 + 方法/头部白名单    |
| M-11 | 安全响应头 | HSTS / X-Frame-Options:DENY / nosniff |

#### HIPAA 专项

| ID   | 控制点     | 实现                                          |
| ---- | ---------- | --------------------------------------------- |
| M-05 | 会话超时   | 15 分钟 PHI / 60 分钟普通（Redis + 内存 LRU） |
| —    | PHI 检测   | Safe Harbor 18 类标识符扫描                   |
| —    | ETL 匿名化 | hash_identifier + truncate_ip + 递归 dict     |

#### 数据安全

| ID        | 控制点       | 实现                                            |
| --------- | ------------ | ----------------------------------------------- |
| H-02/H-03 | SQL 注入防护 | warehouse_client SQL 前缀白名单 + 表名/列名正则 |
| L-01      | 租户隔离     | Persona.agency_id NOT NULL                      |
| L-02      | 输入限制     | transform config 4KB + 200 条/次                |
| L-03      | 审计完整性   | extra_data 字段名修复                           |
| H-06      | 弱凭证防护   | Airflow 无默认用户名密码                        |
| H-10      | 错误信息安全 | dbt 子进程只返回通用错误                        |

### 6.3 数据库合规表

```sql
consent_records      — GDPR/CCPA 同意记录（subject_hash 匿名化）
dsar_requests        — 数据主体访问请求（SLA: GDPR=30天/CCPA=45天/HIPAA=30天）
retention_policies   — 数据保留策略（审计日志 6 年，会话日志 90 天）
breach_incidents     — 违规事件记录（severity/affected_records/通知状态）
business_associate_agreements — BAA 追踪（HIPAA 供应商管理）
data_processing_agreements    — DPA 追踪（GDPR 数据处理协议）
data_flow_mappings   — 数据流映射（GDPR DPIA 输入）
```

---

## 七、数据库设计

### 7.1 PostgreSQL 迁移脚本（16 个）

| 编号 | 文件                           | 说明                                                        |
| ---- | ------------------------------ | ----------------------------------------------------------- |
| 001  | `001_multi_tenant.sql`         | agencies + clients 表，pgvector 扩展，set_updated_at 触发器 |
| 002  | `002_auth.sql`                 | users 表，user_role 枚举（admin/ops/client_viewer）         |
| 003  | `003_credential_vault.sql`     | credentials 表（Fernet 加密存储）                           |
| 004  | `004_audit_log.sql`            | audit_logs 表（INSERT-only，contains_phi 标记）             |
| 005  | `005_token_usage.sql`          | token_usage 表（BIGSERIAL PK，月度聚合索引）                |
| 006  | `006_integrations.sql`         | integrations + sync_logs 表（12 平台）                      |
| 007  | `007_brand_config.sql`         | agencies/clients 添加 brand_config JSONB                    |
| 008  | `008_field_mapping_agency.sql` | field_mappings 添加 agency_id + platform                    |
| 009  | `009_persona_agent.sql`        | personas 添加 agency_id/source/model_used                   |
| 010  | `010_creative_agent.sql`       | generations 添加 agency_id/agent_type                       |
| 011  | `011_compliance.sql`           | 7 张合规核心表                                              |
| 012  | `012_attribution_agent.sql`    | attribution_reports 表                                      |
| 013  | `013_notifications.sql`        | notifications 表 + 索引                                     |
| 014  | `014_remove_pii_columns.sql`   | C-03：去除 consent/DSAR 明文 PII 列                         |
| 015  | `015_encrypt_user_pii.sql`     | M-02/M-03：email_hash 列 + UNIQUE 索引                      |

### 7.2 关键模型关系

```
Agency (1) ──< Client (N)
Agency (1) ──< User (N)
Agency (1) ──< Integration (N) ──< Credential (1)
Agency (1) ──< Persona (N)
Agency (1) ──< Generation (N) ──< GenerationResult (N)
Agency (1) ──< AttributionReport (N)
Agency (1) ──< FieldMapping (N) ──< FieldMappingVersion (N)
Agency (1) ──< ConsentRecord (N)
Agency (1) ──< DSARRequest (N)
User   (1) ──< Notification (N)
User   (1) ──< AuditLog (N)
User   (1) ──< TokenUsage (N)
```

### 7.3 数据仓库架构

| 环境      | 数据库          | 配置                                                        |
| --------- | --------------- | ----------------------------------------------------------- |
| 本地开发  | DuckDB 内存模式 | `WAREHOUSE_BACKEND=duckdb`，零配置                          |
| 线上生产  | Snowflake       | `WAREHOUSE_BACKEND=snowflake`，需配置 account/user/password |
| 本地 OLTP | PostgreSQL      | `localhost:5432`                                            |
| 线上 OLTP | Neon Serverless | `?sslmode=require`，自动伸缩                                |

---

## 八、外部服务集成

### 8.1 集成平台注册表（12 个平台）

| 平台                   | 认证方式  | ETL 适配器        | 状态         |
| ---------------------- | --------- | ----------------- | ------------ |
| **Google Analytics 4** | OAuth 2.0 | ✅ GA4Adapter     | 已实现       |
| **Meta Ads**           | OAuth 2.0 | ✅ MetaAdsAdapter | 已实现       |
| **HubSpot**            | OAuth 2.0 | ✅ HubSpotAdapter | 已实现       |
| **TikTok Ads**         | OAuth 2.0 | 📋 待实现         | 平台注册就绪 |
| **DV360**              | API Key   | 📋 待实现         | 平台注册就绪 |
| **StackAdapt**         | API Key   | 📋 待实现         | 平台注册就绪 |
| **LeadRX**             | API Key   | 📋 待实现         | 平台注册就绪 |
| **LiveRamp**           | API Key   | 📋 待实现         | 平台注册就绪 |
| **Quorum**             | API Key   | 📋 待实现         | 平台注册就绪 |
| **Canva**              | OAuth 2.0 | 📋 待实现         | Phase 3      |
| **Adobe Firefly**      | API Key   | 📋 待实现         | Phase 3      |
| **Icon.app**           | API Key   | 📋 待实现         | Phase 3      |

### 8.2 基础设施服务

| 服务           | 用途                                    | 本地                    | 生产           |
| -------------- | --------------------------------------- | ----------------------- | -------------- |
| **Redis**      | Celery Broker + JWT 黑名单 + HIPAA 会话 | Docker `localhost:6379` | Render Redis   |
| **MinIO**      | 文件存储（创意资产 / 导出文件）         | Docker `localhost:9000` | S3 兼容        |
| **Airflow**    | ETL 定时调度                            | Docker `localhost:8080` | 自托管 / MWAA  |
| **Langfuse**   | LLM 调用追踪                            | Docker `localhost:3100` | Langfuse Cloud |
| **Sentry**     | 错误监控                                | —                       | Sentry Cloud   |
| **OpenRouter** | LLM API 路由                            | Mock 模式（无 Key）     | `sk-or-v1-...` |

---

## 九、实时通知系统

### 9.1 WebSocket 架构

```
前端 ──→ /ws?token=<JWT>
              │
              ↓
      ┌───────────────────┐
      │ JWT 认证           │
      │ → user_id          │
      │ → agency_id        │
      └────────┬──────────┘
               │
      ┌────────┴──────────┐
      │ ConnectionManager  │ （内存级全局单例）
      │                    │
      │ {                  │
      │   "agency:user1": [ws1, ws2],  ← 同一用户多设备
      │   "agency:user2": [ws3],
      │ }                  │
      └────────────────────┘
               │
               ↓
      消息推送（Notification Dispatcher）
      ┌────────────────────┐
      │ create_notification │
      │ 1. 写入 DB         │
      │ 2. WebSocket 推送   │
      │ 3. 失败静默降级     │
      └────────────────────┘
```

### 9.2 消息格式

```json
{
  "type": "notification",
  "id": "uuid",
  "title": "ETL 同步完成",
  "message": "GA4 数据已更新：1,200 条记录",
  "category": "etl",
  "severity": "info",
  "created_at": "2026-04-01T10:30:00Z"
}
```

---

## 十、部署与运维

### 10.1 本地开发（Docker Compose）

```bash
# 启动全部服务
docker-compose up --build

# 服务端口
# FastAPI:  http://localhost:8000
# 前端:     http://localhost:5173
# API 文档: http://localhost:8000/docs
# Airflow:  http://localhost:8080
# MinIO:    http://localhost:9001
# Langfuse: http://localhost:3100
```

### 10.2 生产部署（Render）

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│ Render Web  │───▶│ Neon Postgres│    │  Snowflake  │
│ (FastAPI)   │    │ (Serverless) │    │  (仓库)     │
└──────┬──────┘    └──────────────┘    └──────▲──────┘
       │                                      │
       ├──▶ Render Redis（Broker + Session）   │
       ├──▶ Render Worker（Celery）────────────┘
       ├──▶ Airflow（ETL → dbt）
       ├──▶ OpenRouter（LLM）
       ├──▶ Langfuse Cloud（追踪）
       └──▶ Sentry（监控）

┌─────────────┐
│ Render      │
│ Static Site │──▶ React SPA
└─────────────┘
```

### 10.3 环境变量清单

#### 必须配置（生产）

| 变量                 | 说明                                                          |
| -------------------- | ------------------------------------------------------------- |
| `DATABASE_URL`       | `postgresql+asyncpg://...@xxx.neon.tech/...?sslmode=require`  |
| `SYNC_DATABASE_URL`  | `postgresql+psycopg2://...@xxx.neon.tech/...?sslmode=require` |
| `SECRET_KEY`         | JWT 签名密钥（≥ 32 字符，C-05 启动校验）                      |
| `ENCRYPTION_KEY`     | Fernet 密钥（`Fernet.generate_key()`）                        |
| `OPENROUTER_API_KEY` | OpenRouter LLM API Key                                        |
| `AIRFLOW_USERNAME`   | Airflow 管理员（H-06：无默认值）                              |
| `AIRFLOW_PASSWORD`   | Airflow 密码（H-06：无默认值）                                |
| `CORS_ORIGINS`       | 允许的前端域名（逗号分隔）                                    |

#### 可选配置

| 变量                  | 说明                    | 默认值                      |
| --------------------- | ----------------------- | --------------------------- |
| `REDIS_URL`           | Redis 连接              | `redis://localhost:6379/0`  |
| `GOOGLE_CLIENT_ID`    | Google OAuth            | —（空则禁用 OAuth）         |
| `SENTRY_DSN`          | Sentry 错误追踪         | —（空则跳过）               |
| `LANGFUSE_PUBLIC_KEY` | Langfuse LLM 追踪       | —（空则跳过）               |
| `WAREHOUSE_BACKEND`   | `duckdb` 或 `snowflake` | `duckdb`                    |
| `PERSONA_MODEL`       | Persona Agent 模型      | `anthropic/claude-opus-4-6` |

### 10.4 健康检查

```
GET /health
→ {
    "status": "healthy",          // healthy | degraded | unhealthy
    "database": "ok",             // PostgreSQL 连接
    "redis": "ok",                // Redis 连接
    "warehouse": "ok",            // DuckDB / Snowflake 连接
    "timestamp": "2026-04-01T..."
  }
```

---

## 十一、测试

### 11.1 测试套件（135 用例）

```bash
cd backend
PYTHONPATH=. python3 -m pytest tests/ -v
# 期望结果：135 passed
```

| 测试文件                 | 用例数 | 覆盖模块                         |
| ------------------------ | ------ | -------------------------------- |
| `test_auth.py`           | 6      | JWT 登录/登出/me/无效 token      |
| `test_tenants.py`        | 5      | Agency/Client CRUD               |
| `test_compliance.py`     | 10     | Consent/DSAR/PHI/匿名化          |
| `test_integrations.py`   | 6      | 平台连接/断开/凭证               |
| `test_etl.py`            | 11     | 三适配器 + ETL Runner + PHI      |
| `test_warehouse.py`      | 7      | DuckDB schema/insert/query/sync  |
| `test_ai.py`             | 7      | AI Chat/预算/用量                |
| `test_observability.py`  | 10     | Health/Sentry/Langfuse/RequestId |
| `test_brands.py`         | 7      | 品牌配置 CRUD                    |
| `test_imports.py`        | 9      | CSV 三平台 + 自动检测            |
| `test_field_mappings.py` | 14     | CRUD + 版本 + 回滚 + 预览        |
| `test_personas.py`       | 9      | 手动/AI + CRUD + 过滤            |
| `test_creatives.py`      | 8      | 生成 + 平台过滤                  |
| `test_attribution.py`    | 9      | 报告生成 + 日期范围              |
| `test_portal.py`         | 8      | 仪表板 + 白标 + 精简视图         |
| `test_notifications.py`  | 9      | CRUD + 未读计数 + 标记已读       |

---

## 十二、功能模块状态

| 编号 | 模块                             | 优先级 | 状态                  | 测试  |
| ---- | -------------------------------- | ------ | --------------------- | ----- |
| F-00 | 合规基础层（GDPR/CCPA/HIPAA）    | P0     | ✅ 已完成（4 轮审计） | 27/27 |
| F-01 | 多租户基础设施                   | P0     | ✅ 已完成             | 5/5   |
| F-02 | 认证与授权（Auth + RBAC）        | P0     | ✅ 已完成             | 6/6   |
| F-03 | 凭证保险库                       | P0     | ✅ 已完成             | 6/6   |
| F-04 | 审计日志                         | P0     | ✅ 已完成             | 10/10 |
| F-05 | 平台集成管理（12 平台）          | P0     | ✅ 已完成             | 6/6   |
| F-06 | ETL 数据管道（GA4/Meta/HubSpot） | P0     | ✅ 已完成             | 11/11 |
| F-07 | Canonical Schema + dbt           | P0     | ✅ 已完成             | —     |
| F-08 | 数据仓库（DuckDB/Snowflake）     | P0     | ✅ 已完成             | 7/7   |
| F-09 | Core AI Brain                    | P1     | ✅ 已完成             | 7/7   |
| F-10 | Persona Agent（Pillar 1）        | P1     | ✅ 已完成             | 9/9   |
| F-11 | Creative Agent（Pillar 2）       | P1     | ✅ 已完成             | 8/8   |
| F-12 | Attribution Agent（Pillar 3）    | P1     | ✅ 已完成             | 9/9   |
| F-13 | 品牌入驻系统                     | P1     | ✅ 已完成             | 7/7   |
| F-14 | 历史数据 CSV 导入                | P1     | ✅ 已完成             | 9/9   |
| F-15 | 字段映射系统                     | P1     | ✅ 已完成             | 14/14 |
| F-16 | 客户门户                         | P2     | ✅ 已完成             | 8/8   |
| F-17 | 实时通知（WebSocket）            | P2     | ✅ 已完成             | 9/9   |
| F-18 | 监控与可观测性                   | P2     | ✅ 已完成             | 10/10 |

**后端 19/19 模块已完成，135/135 测试通过。**

---

## 十三、后续规划

### Phase 2（短期）

| 任务               | 说明                                                          |
| ------------------ | ------------------------------------------------------------- |
| 前端 React 实现    | React 19 + TypeScript + Vite + Ant Design，对接 61 个后端 API |
| PostgreSQL RLS     | 数据库行级安全策略，加固多租户隔离                            |
| dbt 数据质量测试   | uniqueness / not_null / referential integrity 校验            |
| 登录限流升级 Redis | 当前内存级限流替换为 Redis 分布式限流                         |

### Phase 3（中期）

| 任务                       | 说明                                      |
| -------------------------- | ----------------------------------------- |
| Canva / Adobe Firefly 集成 | Creative Agent 图片生成                   |
| DSAR 自动化执行            | access/delete/export 全自动处理           |
| 数据保留定时任务           | Celery Beat + retention_policies 自动清理 |
| 违规事件告警               | GDPR 72h / HIPAA 60 天自动通知            |
| 跨境传输控制               | EU 数据路由到对应 Snowflake 区域          |
| 每 Agency 独立加密密钥     | 密钥与数据物理分离 + 90 天轮换            |
| 更多 ETL 适配器            | TikTok Ads / DV360 / StackAdapt / LeadRX  |

---

## 附录

### A. 文档索引

| 文档         | 路径                                  | 说明                            |
| ------------ | ------------------------------------- | ------------------------------- |
| 项目 README  | `README.md`                           | 快速参考（目录结构 + 启动指南） |
| 项目详细说明 | `docs/PROJECT-OVERVIEW.md`            | 本文档                          |
| 开发框架     | `features/DEV-FRAMEWORK.md`           | 19 模块状态追踪                 |
| 总开发计划   | `features/PROJECT-PLAN.md`            | 技术栈决策 + 功能清单           |
| 合规架构     | `features/compliance/architecture.md` | 10 节合规设计（三法规对照）     |
| 合规完成报告 | `features/compliance/COMPLETION.md`   | 36 项控制点 + 4 轮审计          |

### B. 各模块完成报告

| 模块                   | 完成报告                                            | 测试报告                                                            |
| ---------------------- | --------------------------------------------------- | ------------------------------------------------------------------- |
| P0 核心基础层          | `features/p0-core/COMPLETION.md`                    | `features/p0-core/test/test-execution-report.md`                    |
| P1 ETL/仓库/AI         | `features/p1-etl-warehouse-ai/COMPLETION.md`        | `features/p1-etl-warehouse-ai/test/test-execution-report.md`        |
| F-10 Persona Agent     | `features/f10-persona-agent/COMPLETION.md`          | `features/f10-persona-agent/test/test-execution-report.md`          |
| F-11 Creative Agent    | `features/f11-creative-agent/COMPLETION.md`         | `features/f11-creative-agent/test/test-execution-report.md`         |
| F-12 Attribution Agent | `features/f12-attribution-agent/COMPLETION.md`      | `features/f12-attribution-agent/test/test-execution-report.md`      |
| F-13 品牌入驻          | `features/f13-brand-onboarding/COMPLETION.md`       | `features/f13-brand-onboarding/test/test-execution-report.md`       |
| F-14 历史导入          | `features/f14-historical-import/COMPLETION.md`      | `features/f14-historical-import/test/test-execution-report.md`      |
| F-15 字段映射          | `features/f15-field-mapping/COMPLETION.md`          | `features/f15-field-mapping/test/test-execution-report.md`          |
| F-16 客户门户          | `features/f16-client-portal/COMPLETION.md`          | `features/f16-client-portal/test/test-execution-report.md`          |
| F-17 实时通知          | `features/f17-realtime-notifications/COMPLETION.md` | `features/f17-realtime-notifications/test/test-execution-report.md` |
| F-18 可观测性          | `features/f18-observability/COMPLETION.md`          | `features/f18-observability/test/test-execution-report.md`          |
| 合规基础层             | `features/compliance/COMPLETION.md`                 | `features/compliance/test/test-execution-report.md`                 |
