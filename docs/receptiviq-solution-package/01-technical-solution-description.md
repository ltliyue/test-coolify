# Technical Solution Description

## 1. 方案定位

ReceptivIQ 是面向营销代理商与其品牌客户的 AI-native marketing operating platform。平台目标不是只做一个报表工具，而是把市场研究、创意生成、媒体投放、归因分析和客户门户统一到一个受合规约束的数据与智能层之上。

本方案采用以下核心架构原则：

- 数据先统一，再进入 AI：所有外部数据先经过标准化、去重、校验和富集，再进入可查询的统一仓库。
- PII 与非 PII 从摄取阶段开始分离：敏感个人信息不直接混入通用分析仓库。
- AI Brain 作为统一智能编排层：所有 Persona、Creative、Attribution、Media agents 通过同一个 Core AI Brain 访问数据、路由模型、执行工具和记录审计。
- 多租户隔离作为基础能力：租户隔离、权限控制、审计、数据驻留和密钥策略需要在 Sprint 1 前固化。

## 2. Two-Lake Data Strategy

平台采用双湖数据策略：

| 数据区 | 作用 | 典型数据 | 访问原则 |
| --- | --- | --- | --- |
| Raw PII-Segregated Lake | 原始敏感数据隔离区 | CRM 文件、姓名、邮箱、手机号、健康相关属性、受监管身份字段 | 最小权限访问，租户级密钥，加密存储，严格审计 |
| Processed Lake | 标准化分析数据区 | 匿名化受众、广告投放指标、站点事件、聚合转化、非 PII 市场数据 | 面向分析、AI 检索、报表和归因 |

### 2.1 Raw PII-Segregated Lake

Raw PII-Segregated Lake 用于接收和隔离敏感数据，尤其是来自 CRM、客户上传文件、Tresorit 合规传输、以及可能包含 PII/PHI 的第三方数据。该层保留原始输入的可追溯性，但不作为普通分析查询的默认来源。

关键策略：

- 所有文件与记录进入时先进行数据分类：Public、Internal、PII、PHI。
- PII/PHI 使用租户级密钥加密，密钥与数据分离。
- 对分析流程需要的标识符生成不可逆哈希或 tokenized join key。
- 原始 PII 数据不直接暴露给 AI prompt，不进入通用报表，不进入默认 processed schema。
- 所有访问写入审计日志，包括用户、租户、数据类型、用途、时间和结果。

### 2.2 Processed Lake

Processed Lake 用于承载可分析、可检索、可供 AI 使用的数据。该层只保留业务分析所需字段，并对个人标识符做匿名化、哈希化或聚合化处理。

典型数据包括：

- 广告平台 Campaign、Ad Group、Line Item、Creative、Spend、Impression、Click、Conversion。
- GA4 事件、Session、Traffic Source、Conversion、Ecommerce 指标。
- Experian、TransUnion、Nielsen 等数据供应商的人群分层、人口统计、心理图谱和市场信号。
- Placer IQ、Quorum 等地理、行为、受众与线下信号。
- 归因、媒体表现、persona blueprint、creative performance 的衍生指标。

## 3. Snowflake Data Warehouse

Snowflake 作为 ReceptivIQ 的核心数据仓库，承载 processed analytical data、统一语义层、归因模型输入和 AI 检索索引。

### 3.1 多租户隔离模型

建议采用混合隔离模型：

| 租户级别 | 隔离方式 | 适用对象 |
| --- | --- | --- |
| Standard | 共享 Snowflake account，按 tenant_id + Row-Level Security 隔离 | 普通代理商客户 |
| Enterprise | 每租户独立 database 或 schema，独立 role/warehouse | 大客户、高数据量客户 |
| Regulated | 独立 Snowflake account 或 region-bound deployment | HIPAA、强数据驻留、合同要求客户 |

### 3.2 Row-Level Security

所有共享表必须具备租户隔离字段，例如：

- `tenant_id`
- `client_id`
- `source_system`
- `data_classification`
- `region`

并使用 Snowflake row access policy 限制查询结果。应用层仍保留 `tenant_id` 过滤，但不能只依赖应用层过滤。

### 3.3 Zero-Copy Cloning

Snowflake zero-copy cloning 用于：

- 新租户 onboarding 时快速复制基础数据模型、空 schema 和示例配置。
- 为 enterprise tenant 创建隔离副本。
- 为 QA、UAT、回归测试创建接近生产结构的环境。
- 对 tenant replication 或 region migration 做低成本准备。

注意：zero-copy clone 不能替代合规删除流程。涉及 PII/PHI 的数据仍需遵守保留、删除、审计和密钥销毁策略。

## 4. ELT Pipeline

ELT 管道负责把外部来源先安全抽取并加载到隔离区或 Snowflake staging，再在仓库内完成标准化、去重、校验、富集和索引。采用 ELT 是因为 Snowflake 更适合作为可扩展的转换执行层，并且便于保留可审计的 raw/staging 记录。

```text
Extract
  -> Classify
  -> Load
  -> Transform in Snowflake
      -> Normalize
      -> Deduplicate
      -> Validate
      -> Enrich
      -> Index
  -> Audit
```

### 4.1 Normalize

将不同平台的字段映射到统一 canonical schema。例如：

- Meta Campaign / TikTok Campaign / DV360 Insertion Order / The Trade Desk Campaign 统一映射为 `campaign`.
- Meta Ad Set / TikTok Ad Group / DV360 Line Item 统一映射为 `media_placement`.
- GA4 conversions、Meta conversions、DV360 conversions 统一映射为 `conversion_event`.

### 4.2 Deduplicate

去重逻辑需要覆盖：

- API 增量同步重复页。
- 文件重复上传。
- 同一 campaign 在多个 report export 中重复出现。
- 同一 CRM contact 在多系统之间重复。

建议使用：

- source-native primary key。
- tenant-scoped external ID。
- hash fingerprint。
- ingestion batch ID。
- latest-write-wins 或 source-priority merge rule。

### 4.3 Validate

校验内容包括：

- 必填字段完整性。
- 数据类型和范围。
- 时间窗口是否异常。
- 货币、时区、平台枚举是否可识别。
- PII/PHI 是否误入 processed layer。

校验失败的数据进入 quarantine queue，不直接进入主仓库。

### 4.4 Enrich

富集逻辑包括：

- Campaign 与 client/brand 的映射。
- 地理、行业、受众分层标签补全。
- GA4 conversion 与媒体 touchpoint 的可归因关系。
- Experian/TransUnion/Nielsen 等第三方画像与匿名受众 key 的关联。
- Placer IQ/Quorum 线下行为信号与市场区域的关联。

### 4.5 Index

索引用于支持 AI 检索和低延迟查询：

- 结构化索引：tenant_id、client_id、campaign_id、date、source_system。
- 语义索引：persona narrative、creative brief、market research note、campaign insight summary。
- 向量索引：用于 RAG，但不得存储明文 PII。

## 5. Core AI Brain Layer

Core AI Brain 是 ReceptivIQ 的统一智能控制层，负责模型路由、上下文组装、agent 编排、权限检查、成本控制和审计。

### 5.1 LLM Router

LLM Router 的职责：

- 根据任务类型选择模型：persona deep reasoning、creative generation、attribution analysis、summary generation。
- 根据租户合规要求限制模型供应商。
- 根据 token budget、latency、cost tier 做路由。
- 支持 future portability：OpenAI、Anthropic、OpenRouter 或企业私有模型。

### 5.2 Agent Orchestration

Core AI Brain 编排以下 agents：

| Agent | 职责 |
| --- | --- |
| Persona Agent | 根据市场数据、人群画像、第三方 audience signals 生成 persona blueprint |
| Creative Agent | 根据品牌、persona、历史表现生成创意方向、文案、素材建议 |
| Attribution Agent | 分析 touchpoints、conversion、媒体表现，生成归因解释和优化建议 |
| Media Agent | 读取媒体表现、预算、pacing，提出或执行投放优化建议 |

### 5.3 Autonomy Boundary

MVP 阶段建议采用 human-in-the-loop：

- AI 可以生成建议、解释和计划。
- AI 可以准备可执行 payload。
- 涉及预算调整、投放启动、暂停广告、写回外部平台的动作必须人工确认。
- 每个 tenant 可配置 autonomy level。

## 6. Priority 1 Integrations

### 6.1 数据供应商与市场信号

| 集成 | 用途 | 接入方式 | 优先价值 |
| --- | --- | --- | --- |
| Experian | Mosaic、人群画像、人口统计、心理图谱 | 文件/API，取决于合同 | Persona 和市场研究核心数据 |
| TransUnion | 身份、受众、线下/线上连接数据 | API/文件，合同确认 | 受众增强、匹配、归因 |
| Nielsen | 媒体消费、受众测量、市场数据 | API/文件，合同确认 | 市场规模、媒体偏好、benchmark |
| Placer IQ | 地理位置、门店/区域客流、线下行为 | API/导出文件 | 离线行为与地理洞察 |
| Quorum | 政治、社区、地理或受众相关信号 | API/导出文件 | 区域与人群洞察 |

### 6.2 媒体与 DSP 平台

| 集成 | 用途 | 关键数据 |
| --- | --- | --- |
| DV360 | Google Display & Video 360 投放、line item、creative、reporting | Advertiser、Campaign、Insertion Order、Line Item、Creative、Spend、Impression、Click、Conversion |
| Meta | Facebook/Instagram paid media 与 audience | Campaign、Ad Set、Ad、Insight、Pixel Event、Custom Audience |
| TikTok | TikTok Ads 投放与 creative performance | Advertiser、Campaign、Ad Group、Ad、Spend、Click、Conversion、Creative |
| The Trade Desk | Programmatic DSP 与 open web media buying | Advertiser、Campaign、Ad Group、Creative、Bid、Spend、Conversion |
| GA4 | 第一方网站与 App analytics | Event、Session、User Property、Traffic Source、Conversion、Ecommerce |

### 6.3 Tresorit

Tresorit 用于合规 CRM transfer 和敏感文件交换。MVP 中建议将 Tresorit 定位为安全文件进入 Raw PII-Segregated Lake 的入口之一。

适用场景：

- 客户上传 CRM export。
- 上传包含 email、phone、customer list 的受众文件。
- 上传需要合规链路的 healthcare 或 regulated client 数据。
- 作为客户无法提供 API 时的安全替代方案。

## 7. Compliance Posture

平台合规姿态覆盖：

| 合规域 | 方案要求 |
| --- | --- |
| GDPR | 数据最小化、DSAR、删除/限制处理、数据驻留、处理目的记录 |
| CCPA | Do Not Sell/Share、消费者访问与删除、数据分类 |
| HIPAA | PHI 隔离、最小必要访问、审计日志、会话超时、BAA 跟踪 |
| SOC 2 | 安全控制、访问管理、变更管理、日志、监控、供应商管理 |

数据驻留是 per-tenant requirement：

- 每个 tenant onboarding 时必须记录数据驻留区域。
- Snowflake region、对象存储 region、备份 region、模型供应商处理区域都需要进入租户配置。
- 对 EU、Canada、healthcare 或 government-adjacent tenants，需要单独评估 region-locking。

## 8. Auth and SSO Boundary

MVP 阶段保留基础登录、RBAC、tenant isolation 和 audit logging。

Google SSO 与 Office365 SSO 标记为 post-MVP：

- Google Workspace SSO
- Microsoft Office365 / Entra ID SSO
- SCIM provisioning
- Enterprise SAML

MVP 不应因为 SSO 延后而牺牲租户隔离、权限边界或审计。

## 9. MVP Technical Decision Summary

| 主题 | 决策 |
| --- | --- |
| 数据策略 | Raw PII-Segregated Lake + Processed Lake |
| 仓库 | Snowflake |
| 隔离 | tenant_id + RLS，企业租户可独立 database/account |
| PII | 不进入通用 processed warehouse，不进入默认 AI prompt |
| ELT | extract、classify、load、normalize、deduplicate、validate、enrich、index |
| AI | Core AI Brain + LLM Router + agent orchestration |
| Agents | Persona、Creative、Attribution、Media |
| Priority 1 集成 | Experian、TransUnion、Nielsen、Placer IQ、Quorum、DV360、Meta、TikTok、The Trade Desk、GA4、Tresorit |
| 合规 | GDPR、CCPA、HIPAA、SOC 2 |
| 数据驻留 | per-tenant requirement |
| SSO | Google & Office365 post-MVP |
