# Technical Solution Description · 技术方案描述

> 状态：PSD 正式交付物（优化版 v3 — 锁定 Neon Postgres + 双调度可选）
> 关联图：[Network Diagram](./network-diagram.svg)（[释义](./network-diagram-explained.md)） · [Architecture Schema](./architecture-schema.svg)（[释义](./architecture-schema-explained.md)）
> 关联决策：[ELT-ORCHESTRATION-PRIORITY](../ELT-ORCHESTRATION-PRIORITY.md) · [ADR-002 Neon 多租户](../ADR-002-NEON-TENANCY-OPTIMAL.md) · [ADR-003 Dagster vs Airflow](../ADR-003-DAGSTER-VS-AIRFLOW.md) · [PSD-LLM-SELECTION-DECISION](../PSD-LLM-SELECTION-DECISION.md) · [Solution Package](../receptiviq-solution-package/)

---

## 1. Executive Summary · 方案定位

ReceptivIQ 是面向营销代理商（agency）与品牌客户（brand）的 **AI-native marketing operating platform**。平台的目标不是单一报表工具，而是把 **市场研究 · 创意生成 · 媒体投放 · 归因分析 · 客户门户** 统一到一个受合规约束的数据与智能层之上。

**核心架构原则：**

1. **数据先统一，再进入 AI** — 所有外部数据先经过标准化、去重、校验、富集，再进入可查询的统一仓库
2. **PII 与非 PII 从摄取阶段开始分离** — 敏感个人信息不直接混入通用分析仓库
3. **AI Brain 作为统一智能编排层** — 所有 Persona / Creative / Attribution / Media Agent 通过同一个 Core AI Brain 访问数据、路由模型、执行工具和记录审计
4. **多租户隔离作为基础能力** — 租户隔离、权限控制、审计、数据驻留和密钥策略需要在 Sprint 1 之前固化

**架构核心要素：**

- **三 Lake Medallion 数据策略**：🟫 Landing Lake (Bronze) + 🔴 Raw PII-Segregated Lake + 🟢 Processed Lake（物理隔离 · 3 个独立 Neon project · 独立 KMS · mTLS 网络）—— 原始数据先完整落入 Landing，再派生 PII / 非 PII 到两侧
- **多租户数据仓库**（**Neon Postgres** — 产品锁定）：每 Agency 独立 Neon project + 独立 KMS + 独立 compute endpoint；3 档粒度（Standard / Enterprise / Regulated）；Neon Branching（git-style 零拷贝克隆）；每租户数据驻留。**Client 级仅做 RLS 逻辑隔离**（保留跨 Agency benchmarking 能力）
- **ELT 八步管道**：Extract → Classify → Load → Normalize → Deduplicate → Validate → Enrich → Index（+ 全程 Audit）
- **编排引擎**（**主调度二选一**）：🟪 **Dagster OSS**（推荐 · 原生血缘 + dagster-dbt）或 🟦 **Apache Airflow**（普及 · 1000+ Provider）；🟧 **AWS Step Functions** 辅助 AI 写回审批 + DSAR 长流程
- **Core AI Brain**：6 个核心组件（Context Builder · LLM Router · Agent Orchestrator · Tool Executor · Memory & Retrieval · Audit & Cost）+ 4 个 Pillar Agent（Persona / Creative / Attribution / Media）
- **Priority 1 集成**：14 个外部数据源 + Tresorit 合规传输
- **合规姿态**：GDPR · CCPA · HIPAA · SOC 2 + 每租户数据驻留 + PII Access Service 受控明文出口
- **SSO**（post-MVP）：Google Workspace + Office 365 / Entra ID
- **MVP 功能 pillars**：Market Research · Creative Engine · Media Buying · Attribution · Client Portal
- **Autonomy Boundary**：MVP 阶段强制 **human-in-the-loop**（预算调整、广告启停、平台写回必须人工确认）

> 📊 **端到端流（5 阶段，与 Network Diagram 流向条对应）**：
> ① Extract（采集 · TLS+OAuth）→ ② Classify·Transform·Load（分类/变换/写入 · raw_pii→Raw Lake / staging+canonical→Processed Lake）→ ③ PII-safe Context Retrieval（AI 仅读 Processed Lake）→ ④ Agent Orchestrate（LLM Router + Token 预算 + Langfuse 追踪）→ ⑤ Deliver（4 Agent 输出 → Agency / Client 门户）

---

## 2. Architectural Principles · 架构原则

### 2.1 Privacy by Design

合规嵌入架构而非事后补丁。PII / PHI 在进入仓库前必须经匿名化或隔离；审计日志默认全量、INSERT-only；密钥与数据物理分离。AI 默认**不消费明文 PII**，需经 Context Builder 过滤后才能进入 prompt。

### 2.2 3-Lake (Medallion) Data Strategy · 三 Lake 数据策略

平台采用业界标准 **Medallion 三层架构**：

- 🟫 **Landing Lake (Bronze)**：所有原始数据**完整保留**的着陆点（PII 列加密 / 非 PII 列明文）—— 重处理 / DSAR / 法律取证的源头副本；业务/AI 禁读
- 🔴 **Raw PII-Segregated Lake (Silver-PII)**：从 Landing 派生的 PII 维表（subject dim + per-source PII 字段抽取）—— PII Access Service 的唯一明文出口源
- 🟢 **Processed Lake (Silver+Gold)**：从 Landing 派生的非 PII 业务路径（raw → staging → canonical → marts → ai_context）—— 完全无明文 PII，业务 / AI / 报表读

**Trust boundary**：Landing 与 Raw PII 位于同一 PII trust boundary（同等加密、同等访问控制）；Processed Lake 是独立的业务 trust boundary（无 PII，由 **PII Segregation Boundary** 隔开）。跨 Lake 关联通过 **`pii_token = SHA-256(email_hash + agency_salt)`** 不可逆 hash 实现，明文 PII 永不出 PII zone。

### 2.3 Multi-Tenant Isolation（物理隔离 + 角色层级）

**角色三层级 + 隔离两层次：**

| 层级    | 角色                             | 数据可见范围                                                | 隔离方式                                                   |
| ------- | -------------------------------- | ----------------------------------------------------------- | ---------------------------------------------------------- |
| L1 平台 | **Platform Super Admin**（内部） | 跨所有 Agency 的**聚合/元数据**（不可越界查询明文业务数据） | 通过 secure aggregation view 跨 Agency 汇总                |
| L2 租户 | **Agency**（Operator / Admin）   | 该 Agency 下所有 Client 的全部数据                          | **物理隔离单位**：独立 Neon project + 独立 KMS 密钥        |
| L3 品牌 | **Client**（Viewer）             | 仅自己被授权的 client_id 数据子集                           | 在 Agency 数据库内通过 RLS / 视图限制（Agency 内逻辑隔离） |

**核心原则：**

- **租户 = Agency**：物理隔离边界设在 Agency 层。每个 Agency 独立 Neon project + 独立 KMS 密钥 + 独立 compute endpoint（Enterprise/Regulated 档）
- **Client 不是物理隔离对象**：同一 Agency 下的多个 Client 共享该 Agency 的数据库，通过 `client_id` RLS + 视图实现 Agency 内的逻辑隔离
- **Super Admin 不能越界看明文 PII/PHI**：跨 Agency 视图只暴露聚合指标（活跃 Agency 数、总 token 用量、平台健康），明文业务数据仍受 Agency-level KMS 保护
- **应用层**：`agency_id` 强制过滤 + `client_id` RLS（仓库层）+ 物理隔离 三层叠加（defense-in-depth）

零拷贝克隆支持按需为单 Agency 拉起独立分析副本，不影响其他 Agency。

### 2.4 LLM-Native Orchestration

Core AI Brain 是平台的**统一智能编排层**——业务功能不直连 LLM，所有 AI 能力（Persona / Creative / Attribution / Media 等 Agent）都从这一层进出。该层统一负责：上下文组装（PII-safe）、模型路由、token 预算、Agent 编排、工具调用审批和审计。这样可以确保模型可替换、成本可观测、合规可追溯，并避免"每个功能各自接 LLM"导致的数据泄漏与重复造轮子。

### 2.5 Autonomy Boundary · 自治边界

MVP 阶段采用 **human-in-the-loop**：

- AI 可以生成建议、解释和计划
- AI 可以准备可执行 payload
- **涉及预算调整、投放启动、暂停广告、写回外部平台的动作必须人工确认**
- 每个 tenant 可配置 autonomy level（保守 / 平衡 / 激进）

---

## 3. 3-Lake (Medallion) Data Strategy · 三 Lake 数据策略

平台**三个独立 Neon project 构成三层 Lake**——所有原始数据先完整落入 Landing，再按字段分类派生到 Raw PII Lake 与 Processed Lake。

### 3.0 Landing Lake（Bronze · 原始数据着陆湖）

**所有外部源响应的第一站**。整条 record 原样保留，PII 列字段级 Fernet 加密、非 PII 列明文。

**关键策略：**

- 写入 `landing.<source>_records`（整条 record + record_id UUID + ingest_metadata）
- PII 列在写入时立即 Fernet + per-Agency KMS 加密；非 PII 列明文
- **immutable** —— 不修改、不覆盖、不删除（除 DSAR / 保留期到期）
- 业务用户 / AI Brain / dashboard / Pillar **全部禁读**；仅 ELT 服务账号 + 合规审计员可访问
- `landing.sync_state` 持每 source 的 cursor / watermark，支撑增量续抓

**合规定位**：Landing 与 Raw PII Lake 位于**同一 PII trust boundary**（同等独立 KMS / VPC / mTLS / 访问控制）。审计师视角：Landing 是"原始数据的真实副本"，与 Raw PII Lake 合在一起满足 GDPR Art. 25 / HIPAA §164.312 / SOC 2 CC6 的"原始数据可追溯 + 受保护"双重要求。

| 属性   | 设计                                                                           |
| ------ | ------------------------------------------------------------------------------ |
| 内容   | 14 P1 源 + Tresorit 上传的完整原始 record（PII 列加密 + 非 PII 列明文）        |
| 存储   | per-Agency 独立 Neon project (`{agency}-landing`) · 独立 KMS key               |
| 保留期 | HIPAA 6y / 非 HIPAA 90d                                                        |
| 访问   | ELT 服务账号（写 + 重处理读）+ 合规审计员（只读）。业务 / AI / Portal 一律禁止 |
| 用途   | 重处理 / DSAR 定位 / 法律取证 / 审计追溯                                       |

### 3.1 Raw PII-Segregated Lake（PII 维表湖）

**从 Landing Lake 派生**——STAGE 3 SPLIT 把 Landing 中分类为 L2/L3（PII/PHI）的字段抽出，写入此 Lake。仅持 PII 字段（**不持整条 record**，整条 record 在 Landing），是 PII Access Service 唯一明文出口源。

**关键策略：**

- 仅 3 张表：`raw_secure.users`（主体维表）· `raw_secure.<source>_pii_fields`（源 PII 字段抽取）· `raw_secure.pii_access_log`（出口审计）
- PII 字段持续 Fernet + per-Agency KMS 加密（独立于 Landing 的密钥）
- 对分析需要的标识符生成 **`pii_token = SHA-256(email_hash + agency_salt)`**——跨 Lake 关联的不可逆主体标识
- 原始 PII **不直接暴露给 AI prompt**，不进入通用报表，不进入默认 processed schema
- 所有访问写入 `pii_access_log`（用户 / 租户 / 数据类型 / 用途 / 时间 / 结果）—— PII Access Service 走这条路径

| 属性   | 设计                                                                                                        |
| ------ | ----------------------------------------------------------------------------------------------------------- |
| 内容   | 主体维表（email/phone enc + hashes + pii_token）+ 源 PII 字段抽取 + 出口审计                                |
| 存储   | per-Agency 独立 Neon project (`{agency}-raw-pii`) · 独立 KMS                                                |
| 保留期 | 默认 90 天；HIPAA 客户 6 年；GDPR 财务 7 年                                                                 |
| 访问   | ETL 服务账号（写）+ PII Access Service（受控读）+ 合规审计员（只读）。业务用户 / AI Brain / Portal 一律禁止 |
| 审计   | 任何 SELECT / EXPORT 写入 INSERT-only 审计表，自动告警                                                      |

### 3.2 Processed Lake（处理后湖）

**从 Landing Lake 派生**——STAGE 3 SPLIT 把 Landing 中分类为 L0/L1（非 PII）的字段抽出，写入此 Lake 的 `processed.raw.<source>_records`，随后由 dbt 4 层流水线（staging → canonical → marts → ai_context）转换为可分析、可检索、可供 AI 使用的数据。**完全无明文 PII**，仅持 `pii_token` 不可逆 hash 供跨 Lake 关联。

**典型数据：**

- `processed.raw.<source>_records`：源原始非 PII 字段 + pii_token + ingest_metadata（immutable，HIPAA 6y / 非 HIPAA 90d）
- 广告平台 Campaign / Ad Group / Line Item / Creative / Spend / Impression / Click / Conversion
- GA4 事件、Session、Traffic Source、Conversion、Ecommerce 指标
- Experian / TransUnion / Nielsen 等数据供应商的人群分层、人口统计、心理图谱和市场信号
- Placer IQ / Quorum 等地理、行为、受众与线下信号
- 归因、媒体表现、Persona blueprint、Creative performance 的衍生指标

### 3.3 PII Segregation Boundary（Hard Isolation）

> **设计原则**：**PII zone**（Landing Lake + Raw PII Lake）与 **Processed Lake** 之间是**硬隔离 (hard isolation)**，**不是** "同一个 Lake 内通过 partition / schema 软隔离"。仅通过 schema / partition 区分**无法**满足 GDPR / CCPA / HIPAA / SOC 2 的"reasonable security"与"physical safeguard"条款。Landing 与 Raw PII 同属一个 PII trust boundary（同等加密、访问控制），它们与 Processed Lake 之间才有 PII Boundary。

跨 PII Boundary 的策略边界由 6 层防护构成：

| #   | 层         | 实施                                                                                                                                                                               |
| --- | ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | **存储层** | PII zone（Landing + Raw PII，2 个 Neon project）与 Processed Lake（独立 Neon project）部署在 **不同的物理存储集群** —— 不同 endpoint + 独立存储，**不可** 同一集群下用 schema 切分 |
| 2   | **加密层** | PII zone 与 Processed Lake 的 KMS 主密钥**完全独立**；Processed Lake 的服务账号**永远不持有** PII zone 的解密密钥                                                                  |
| 3   | **网络层** | 私有 VPC subnet 隔离，仅 ELT Worker 跨段（双向 mTLS）；Processed Lake 网络不可路由到 Raw Lake 存储端点                                                                             |
| 4   | **身份层** | 服务账号最小权限；跨 Lake 调用 short-lived purpose-bound token（≤ 15 min）；不存在长期凭证                                                                                         |
| 5   | **数据层** | 跨 Lake 写入必须经 `anonymize_record_for_warehouse()`；任何包含原始 PII 字段的 record **存储层拒绝**（schema constraints + 写入 hook）                                             |
| 6   | **审计层** | 全部跨 Lake 流量与异常 INSERT-only 审计，6 年保留；DLP 持续扫描 Processed Lake 防 PII 渗漏                                                                                         |

**关联机制**：三 Lake 之间通过 **`pii_token` hash join key**（SHA-256(email_hash + agency_salt)）安全关联——Processed Lake 持 hash，可与 Landing / Raw PII Lake 内同 hash 的记录关联，但 hash **不可逆**，明文 PII 不流出 PII zone（Landing + Raw PII）。`record_id` (UUID) 用于 Landing ↔ Raw PII / Processed 之间的同 record 反查（重处理 / DSAR 定位场景）。

**合规属性证明（如何满足 4 大法规）：**

| 法规 / 条款                                                                  | 本方案如何满足                                                             |
| ---------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| **GDPR** Art. 32 "Security of processing"                                    | 加密、独立密钥、最小权限、审计、DLP — 全部具备                             |
| **GDPR** Art. 25 "Privacy by Design"                                         | PII 默认不进入分析与 AI 路径                                               |
| **HIPAA** §164.312(a) "Access control" + §164.312(e) "Transmission security" | 独立服务账号、mTLS、purpose-bound token；BAA 客户 KMS 隔离                 |
| **HIPAA** §164.308 "Administrative safeguards"                               | INSERT-only 审计 6 年、Workforce clearance（合规审计员独占 Raw Lake 读权） |
| **CCPA / CPRA** §1798.81.5 "Reasonable security"                             | 多层物理 / 网络 / 加密隔离；DLP；DSAR 流程                                 |
| **SOC 2 Type II** CC6 "Logical and physical access controls"                 | 物理存储分离、独立 KMS、审计追溯 → 通过控制矩阵证据采集                    |

> 若 PII zone 与 Processed Lake 在同一数据库实例下仅靠 schema 切分，则审计师会认定为 **同一 trust boundary 内**，无法独立证明"physical safeguard"——**这是本设计明确拒绝的方案**。

### 3.4 PII Access Service（明文 PII 的受控出口）

某些下游业务必须使用**明文 PII**作为输入：

| 业务场景                            | 为什么需要明文                                                                                                                                                                |
| ----------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Lookalike 建模 / Seed list 导出** | 平台（Meta / DV360 / LiveRamp / Trade Desk）通常接受 SHA-256 哈希后的邮箱/电话作为 seed；**哈希必须从明文计算**——若 Processed Lake 只存 salted hash，无法重新生成平台特定哈希 |
| **Meta Custom Audience 上传**       | 接受 SHA-256(email/phone)；上传前必须从明文计算（每平台 hash 协议可能不同）                                                                                                   |
| **GDPR / CCPA DSAR — 数据主体定位** | 必须能凭借姓名/邮箱/电话定位某个体的全部记录（"this person's data")                                                                                                           |
| **法律请求 / 合规调查**             | 监管或司法请求要求精确到自然人                                                                                                                                                |

**设计：PII Access Service 作为 Raw PII Lake 的唯一受控明文出口**

```
        ┌──────────────────────────────────────────────────┐
        │           Raw PII-Segregated Lake                │
        │  (encrypted; per-Agency KMS; restricted access)  │
        └────────────────────┬─────────────────────────────┘
                             │
                             ▼ purpose-bound token (≤15min, audited)
        ┌──────────────────────────────────────────────────┐
        │          PII Access Service                      │
        │  • 凭据：scoped + purpose-bound + time-limited   │
        │  • 操作：read-decrypt → in-memory transform      │
        │  • 出口：仅平台-specific hash 或 DSAR 响应包      │
        │  • 全程审计：who / what / why / when / which row  │
        └────┬──────────────┬──────────────────┬──────────┘
             │              │                  │
             ▼              ▼                  ▼
       Meta CA 上传    DV360 / LiveRamp     DSAR 响应
       (SHA-256)       Seed list           (subject data)
```

**关键安全属性：**

- **明文 PII 永不离开此 service 的内存**：service 读 → 解密 → 内存中哈希/打包 → 出口仅含变换后的产物（hash list / DSAR JSON）
- **purpose-bound token**：每次操作必须声明用途（`audience.upload.meta` / `dsar.lookup` / `compliance.investigation`）并签发对应 scope 的短期凭据
- **operation allow-list**：service 不暴露通用 SQL，仅支持白名单操作（`build_audience_hash_list`、`dsar_locate_subject`、`legal_export` 等）
- **审计粒度到行**：记录读取了哪些 record_id、为何、被授权者、对应输出 hash 数量；6 年保留
- **不与 Processed Lake / AI Brain 互联**：service 出口直连外部平台 API / 客户邮箱（DSAR），明文 PII **从不进入** Processed Lake / Context Builder / Agent

**业务用户视角**：业务团队（Campaign Manager 等）触发"上传受众到 Meta"时，他们看不到明文 PII；UI 仅显示"已导出 1234 条哈希身份"。受 Agency Admin 角色控制谁能触发哪类 PII Access。

**Agency 级隔离仍成立**：service 对每个 Agency 有独立的 KMS 解密上下文，跨 Agency 不可调用。

### 3.5 数据分类与共享参考数据策略（Tenant Scoping & Shared Reference）

> **客户问题（Matt）**：数据进入仓库时是否从摄取那一刻起就 tenant-scoped？像 Nielsen / Experian / 受众平台这样的跨租户数据源怎么办？平台不想重复采集 Experian 这种数据。

**回答**：摄取时按数据**性质**分三类，而非一刀切按 Agency 物理隔离。

#### 3.5.1 三类数据分类

| 类别                              | 定义                                                                                           | 例子                                                                                                                                                      | 落地位置                                                                          | 摄取频次                                                             |
| --------------------------------- | ---------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| **A. Tenant-Private**             | 属于某一 Agency / Client 的私有数据（含或不含 PII）                                            | Meta / DV360 / TikTok / GA4 投放与转化数据；HubSpot CRM；Tresorit 上传的客户 CSV                                                                          | **per-Agency Neon project**（含 Raw PII Lake + Processed Lake）                   | per-Agency, 按 Agency 的同步计划                                     |
| **B. Shared Reference**           | 平台许可的、跨租户的**纯参考数据**（无 individual-level PII，或 PII 在源头即已被供应商匿名化） | Experian 人口画像 taxonomy / segment 定义；Nielsen panel-level reach；Placer IQ POI 标签；Quorum 立法监控元数据；广告平台公开 taxonomy（行业 / 地域代码） | **Shared Reference Lake**（独立的、平台级 Neon project，read-only 暴露给 Agency） | 平台级，单次摄取（按供应商刷新周期，如 Experian 月度、Nielsen 双周） |
| **C. Tenant-Derived from Shared** | Agency 把 Shared Reference 与自己的 Tenant-Private 数据 JOIN 后产生的衍生结果                  | "Client X 的受众段按 Experian taxonomy 打分后的结果"                                                                                                      | 写入**该 Agency 的 Processed Lake**，**不写回** Shared Reference Lake             | 衍生即写，按需重算                                                   |

> **关键转折**：从 "3-Lake per Agency"（Landing + Raw PII + Processed）扩展为 "**3-Lake per Agency + 1 Shared Reference Lake（平台级）**"。共享部分单次摄取、单次付费、共享存储；私有部分仍按 Agency 物理隔离。

#### 3.5.2 Shared Reference Lake 设计

```text
┌─────────────────── Shared Reference Lake (平台级 Neon project) ─────────────────┐
│  · 单独的 Neon project：shared_reference                                          │
│  · schema: shared_experian / shared_nielsen / shared_placeriq / shared_quorum / │
│            shared_taxonomy（IAB / DMA / 行业代码 / ISO 区域）                     │
│  · 无 individual-level PII —— 供应商在源头已聚合 / 匿名（行业合同条款约束）       │
│  · 读访问通过 license-gated views 暴露到每个 Agency 的 Processed Lake             │
└──────────────────────────────────────────────────────────────────────────────────┘
                              │
                              │  ① 平台 ELT 单次摄取
                              │     Dagster asset = single source of truth
                              │     content-hash dedup（详 §3.5.4）
                              ▼
        ┌─────────────────────────────────────────────────────────────┐
        │  License Gate（每 Agency 的可见性矩阵）                       │
        │   agency_id │ experian │ nielsen │ placeriq │ quorum         │
        │   ─────────┼──────────┼─────────┼──────────┼───────          │
        │   ACME      │   ✓      │   ✓     │    ✗     │   ✗            │
        │   BETA      │   ✓      │   ✗     │    ✓     │   ✓            │
        └─────────────────────────────────────────────────────────────┘
                              │
                              │  ② 按 license 矩阵暴露 read-only view
                              │     view 中过滤掉未授权类目
                              ▼
        ┌─────────── ACME 的 Processed Lake ──────────┐  ┌── BETA 的 ─────┐
        │  shared.experian → READ ONLY               │  │   …            │
        │  shared.nielsen  → READ ONLY               │  │                │
        │  shared.placeriq → 403 (no license)         │  └────────────────┘
        │  (Agency 自己的 marts / canonical 仍在本地) │
        └────────────────────────────────────────────┘
```

**实现要点**：

| 要点             | 实施                                                                                                                                                                                            |
| ---------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **物理位置**     | Shared Reference Lake = 一个独立的 Neon project（与所有 Agency project 平级），**只读**暴露                                                                                                     |
| **暴露机制**     | 跨 Neon project 通过 **postgres_fdw**（Foreign Data Wrapper）或预生成的 read-only logical replica，落在 Agency Processed Lake 的 `shared.*` schema 下                                           |
| **License 强制** | `license_grants` 表持 `(agency_id, source, valid_until, contract_id)`；FDW view 上挂 RLS：`USING (current_setting('app.agency_id') IN (SELECT agency_id FROM license_grants WHERE source=...))` |
| **JOIN 模式**    | Agency 的 ELT 在自己的 Processed Lake 中执行 `JOIN shared.experian_segments` —— 数据**不复制**到 Agency，只在查询时联表                                                                         |
| **审计**         | 每次跨 project 的 SELECT 记 audit_event（agency_id · source · rows_read · query_id）；6 年保留                                                                                                  |
| **PII 边界**     | Shared Reference Lake **不含 individual-level PII**，故无需走 PII Boundary；供应商合同条款里这一点写明                                                                                          |
| **HIPAA 客户**   | 仍可读 Shared Reference（参考数据不含 PHI）；写回的 Tenant-Derived 结果仍受 BAA 客户的 region binding 约束                                                                                      |

#### 3.5.3 14 个 P1 集成的分类映射

| 集成                                                | 类别                                    | 摄取频次                     | 落地                                                                   | 备注                                                |
| --------------------------------------------------- | --------------------------------------- | ---------------------------- | ---------------------------------------------------------------------- | --------------------------------------------------- |
| **Meta / DV360 / TikTok / Trade Desk / StackAdapt** | A. Tenant-Private                       | per-Agency, 实时/小时级      | Agency 的 Raw PII Lake（含 user_id / device_id 散列） + Processed Lake | 每个 Agency 持有自己的广告账户凭证                  |
| **GA4**                                             | A. Tenant-Private                       | per-Agency, 日级             | Agency 的 Raw PII Lake（cookie / client_id）+ Processed Lake           | Agency 拥有自己的 GA4 property                      |
| **HubSpot**                                         | A. Tenant-Private                       | per-Agency, 小时级           | Agency 的 Raw PII Lake（email / phone）+ Processed Lake                | 每个 Agency 自己的 HubSpot account                  |
| **Tresorit**                                        | A. Tenant-Private                       | per-Agency, 触发式           | Agency 的 Raw PII Lake                                                 | 客户端上传，本就是私有                              |
| **Quorum**（立法监控）                              | B. Shared Reference                     | 平台级，日级                 | Shared Reference Lake `shared_quorum`                                  | 立法数据本就公开，license 控制谁能查                |
| **Experian**（人口画像）                            | B. Shared Reference                     | 平台级，月级                 | Shared Reference Lake `shared_experian`                                | **关键节省点**——避免 N 次 license / N 次摄取        |
| **TransUnion**（信用 + 人口）                       | B. Shared Reference + C. Tenant-Derived | 平台级月级 + per-Agency 查询 | Shared 存 taxonomy；Agency lookup 结果落 Processed                     | TransUnion 部分查询是基于 Agency 上传 list 的       |
| **LiveRamp**（身份解析）                            | **C. Tenant-Derived only**              | per-Agency, 按需             | Agency 的 Raw PII Lake（IDR 结果）                                     | LiveRamp 不是参考数据，是基于 Agency 名单的查询服务 |
| **Nielsen**                                         | B. Shared Reference                     | 平台级，双周                 | Shared Reference Lake `shared_nielsen`                                 | Panel 数据本就 aggregate                            |
| **Placer IQ**                                       | B. Shared Reference                     | 平台级，月级                 | Shared Reference Lake `shared_placeriq`                                | POI / 人流量本就 aggregate                          |

> **节省估算**：单 Experian license 约 $80k-$200k/年。若 50 Agency 都各自走 license，平台无法 sustainable；统一摄取后由平台持 master license、按 Agency 计 license 分账，可降低 70-90% 数据成本。

#### 3.5.4 重复数据处理（Dedup at Ingestion）

无论 A / B 类，所有 ELT Extract 都遵循 **idempotent + content-hash dedup**：

| 机制                               | 解释                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| ---------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **① 增量续抓 Cursor（Watermark）** | **Cursor = ELT 调度记录"上次拉到哪一条 / 哪个时间点"的位置标记**。每个 source × tenant（A 类）或每个 source（B 类）维护 `sync_state` 表：`(source, scope_id, last_cursor, last_run_at)`。Extract 总是从 `last_cursor` 之后续抓，不重头拉。<br>**例子**：首次拉 Meta API 拿到 1000 条 → `last_cursor = 2026-05-18T14:30`；1 小时后再跑 → API 请求 `since=2026-05-18T14:30` → 只拿新增 50 条，原 1000 条**不重抓**。<br>业内同义词：Incremental Sync · Watermark Extraction · Delta Loading |
| **② Content Hash**                 | 每条 record 入仓库前计算 `record_hash = SHA-256(canonical_field_subset)`；表上 `UNIQUE(tenant_id_or_null, source, record_hash)` —— 同内容再来不入库（Cursor 失效时的兜底）                                                                                                                                                                                                                                                                                                                |
| **③ Upsert by Business Key**       | Transform 阶段 dbt 用 `MERGE ... ON business_key` 而不是 `INSERT`——同一 campaign 的 5 次拉取只产生 1 条 canonical 记录                                                                                                                                                                                                                                                                                                                                                                    |
| **④ Source Refresh Cadence**       | B 类共享数据：固定批次（Experian 月、Nielsen 双周），不允许 ad-hoc 重抓；A 类按 Agency 配置但有最小间隔（同一 source 5 分钟内不重复触发）                                                                                                                                                                                                                                                                                                                                                 |
| **⑤ DSAR Delete 仅作用于 A 类**    | 删除主体必影响 A 类的 Raw PII；B 类无 individual PII 无需 DSAR 处理（合同条款约束）                                                                                                                                                                                                                                                                                                                                                                                                       |
| **⑥ 内容指纹审计**                 | 每次 ingest 记 `(source, scope_id, record_hash_count_new, record_hash_count_skipped)`，可证明无重复                                                                                                                                                                                                                                                                                                                                                                                       |

**对 Experian 这种 B 类的具体流程**：

```text
Day 1 (月初):
  Dagster asset: shared.experian.refresh
    → 单次调 Experian API（平台 master credential）
    → 写入 shared_reference Neon project
    → license_grants 已包含 ACME, BETA, DELTA → 三家都能查
    → 总成本：1× API 调用 + 1× 存储

Day 15 (Agency ACME 临时想刷新):
  ACME UI: "Refresh Experian segments"
    → 拒绝：B 类共享数据按平台周期刷新（next refresh: Day 30）
    → 或：Platform Super Admin 才能触发跨平台 refresh

Day 30:
  Dagster asset: shared.experian.refresh
    → content-hash dedup：上次有 1,200,000 segment 行，本次 1,200,030 行
    → 仅写入 30 条新 hash，其余复用
    → 总写入量：< 1% 存储增量
```

**对 Meta / GA4 这种 A 类的具体流程**：

```text
ACME @ Hour T:
  Dagster asset: meta.acme.ad_insights[partition=today]
    → 用 ACME 的 OAuth token 拉取
    → 写入 ACME 的 Raw PII Lake（ad_id 等是 ACME 私有）
    → 与 BETA 完全独立

ACME @ Hour T+1:
  同上但 cursor 从 T 续抓
    → content-hash dedup：去掉 T-1 ~ T 这段已写过的行
```

#### 3.5.5 关键安全 / 合规属性

- **PII 始终留在 Tenant-Private**：B 类共享数据按合同/技术双重保证无 individual-level PII；不需要走 PII Boundary
- **License compliance**：未授权的 Agency 通过 RLS 在 view 层被拒，**物理上仍可见数据但逻辑上 zero rows**——这是行业标准做法，配合 contract audit 即可满足供应商合规要求
- **跨租户聚合 benchmarking 不受影响**：Platform Super Admin 仍可基于 A 类做跨 Agency aggregation（如 "TikTok ROAS 中位数"）；Shared Reference 的存在不破坏 Agency 间物理隔离
- **DSAR 不波及 Shared Reference**：删除请求只作用于 A 类 Raw PII Lake，B 类参考数据按合同不存 individual

#### 3.5.6 决策摘要

| 维度                          | 客户问题答案                                                                                                                         |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| 摄取时是否 tenant-scoped？    | **A 类是**（per-Agency project 物理隔离从 ingest 开始）；**B 类不是**（平台级单次摄取）；**C 类是**（衍生结果落 Agency 自己的 Lake） |
| Experian / Nielsen 怎么处理？ | **B 类**——单次平台摄取，license-gated read views 暴露给授权 Agency，物理隔离按 license 矩阵控制可见性                                |
| 怎么防止重复数据？            | 5 层：cursor 续抓 + record_hash dedup + business-key upsert + 固定刷新周期 + 平台单点共享                                            |
| 成本影响                      | Experian/Nielsen 等 B 类年度 license 与存储成本可降 70-90%                                                                           |
| 合规影响                      | 无（B 类按合同无 PII；Tenant-Private 仍物理隔离；License gate 由 RLS + audit 双保险）                                                |

### 3.6 原始数据生命周期与处理后分区（Raw Data Lifecycle & Post-Processing Division）

> **客户问题**：包含所有数据的原始数据怎么处理？处理后的数据怎么划分？

外部源返回的原始 record 通常是"PII + 业务字段 + 元数据"的混合体（例如 Meta API 一条 ad_insights 同时含 `user_id`、`campaign_id`、`impressions`、`age_breakdown`）。**所有原始 record 必须先完整落入 🟫 Landing Lake（Bronze 层）保存**，然后才被分类、按字段拆分，分别派生进 🔴 Raw PII Lake 与 🟢 Processed Lake。这就是业界标准的 **Medallion Architecture（奖牌架构）** —— 客户/审计师都熟悉这套模式，且重处理、DSAR、法律取证都更易实施。

> **架构（Landing-First / Medallion）**：
>
> - **第 1 步**：所有源响应先**完整**写入 🟫 Landing Lake（PII 字段 Fernet 加密 / 非 PII 明文）—— 这是"原始数据真实副本"
> - **第 2 步**：分类引擎读 Landing，按字段类别派生进 🔴 PII Lake（仅 PII 字段）与 🟢 Processed Lake（仅非 PII 字段 + pii_token）
> - **合规论证**：Landing Lake 与 Raw PII Lake **位于同一 PII trust boundary**（独立 Neon project + 独立 KMS + 独立 VPC + mTLS）。两者合在一起满足 GDPR Art. 25 + HIPAA §164.312 + SOC 2 CC6 全部条款。

#### 3.6.1 四阶段处理流程

```text
┌──────────── STAGE 1: LAND（整条 record 落入 Bronze 层）────────────┐
│ 外部 API 响应 → 解析 → **完整写入 🟫 Landing Lake**                │
│                                                                    │
│  · 表名: landing.<source>_records                                  │
│  · 保留整条 record 全部字段                                         │
│    - PII 列 (email, phone, ssn …) → Fernet 字段级加密              │
│    - 非 PII 列 (campaign_id, impressions …) → 明文                 │
│  · 系统生成 record_id (UUID) 作为跨 Lake 关联键                    │
│  · ingest_metadata: source, batch_id, fetched_at, record_hash      │
│  · immutable · HIPAA 6y / 非 HIPAA 90d                              │
│  · 访问：仅 ELT 服务账号 + 合规审计员                              │
│  · 🚫 业务用户 / AI / dashboard 完全禁止读 Landing Lake             │
└────────────────┬───────────────────────────────────────────────────┘
                 │
                 ▼
┌──────────── STAGE 2: CLASSIFY（读 Landing，逐字段打标）───────────┐
│ 读 landing.<source>_records，对每个字段打数据分级标签               │
│                                                                    │
│  · L0 Public:       campaign_id, ad_set_id, creative_name           │
│  · L1 Internal:     spend, impressions, clicks, account_id          │
│  · L2 PII:          email, phone, IP, full_name, address            │
│  · L3 PHI:          health-related fields (HIPAA 客户场景)          │
│  · 输出: field_classification_manifest（每字段一行）                │
│  · L2/L3 触发 PII/PHI Detector 双扫描；写 audit_event              │
│  · 🚦 仅处理 · 不落仓库                                            │
└────────────────┬───────────────────────────────────────────────────┘
                 │
                 ▼
┌──────────── STAGE 3: SPLIT（读 Landing，按字段派生到两侧）────────┐
│ 按 manifest，从 Landing 派生 PII 与非 PII 两侧（两个 Neon project） │
│                                                                    │
│  ┌─ 🔴 派生 A：PII 字段 → Raw PII Lake（per-Agency）                  │
│  │    · raw_secure.users — 主体维表 UPSERT                          │
│  │      （email_enc / phone_enc / hashes / pii_token）              │
│  │    · raw_secure.<source>_pii_fields — 源特定 PII 字段抽取         │
│  │      （record_id 反查键，不含非 PII 字段）                       │
│  │    · 字段级 Fernet + per-Agency KMS（独立于 Landing 的密钥）     │
│  │                                                                  │
│  └─ 🟢 派生 B：非 PII 字段 → Processed Lake（per-Agency）             │
│       · processed.raw.<source>_records                              │
│         — 非 PII 字段 + pii_token + record_id + ingest_metadata    │
│       · immutable · HIPAA 6y / 非 HIPAA 90d                         │
│       · 没有任何 L2/L3 字段；DLP 持续扫描防渗漏                      │
│                                                                    │
│  关联: pii_token = SHA-256(email_hash + agency_salt)                │
│  ⚠ Landing 仍保留全部字段——这是合规与重处理的源头                  │
└────────────────┬───────────────────────────────────────────────────┘
                 │
                 ▼
┌──────────── STAGE 4: TRANSFORM（Processed Lake 内 dbt 4 层）──────┐
│ raw → staging → canonical → marts → ai_context                     │
│                                                                    │
│  processed.raw.<source>_records  (STAGE 3 写入；dbt source)        │
│       │                                                            │
│       ▼                                                            │
│  staging.stg_<source>    dbt 标准化中间产物                        │
│       │                                                            │
│       ▼                                                            │
│  canonical.*         跨 source 统一到 13 个 Canonical Entities      │
│                      （campaign / persona / touchpoint 等）         │
│                      · pii_token 在此 JOIN 出 unified user 实体     │
│                      · 但 user 实体本身无明文                       │
│       │                                                            │
│       ▼                                                            │
│  marts.*             业务报表用聚合表                                │
│                      · 面向 dashboard / API / Pillar 服务           │
│                      · pii_token 在此通常已被聚合掉（GROUP BY）    │
│       │                                                            │
│       ▼                                                            │
│  ai_context.*        AI-safe 摘要 + pgvector 向量                   │
│                      · Context Builder 召回的唯一数据源              │
│                      · 不含 pii_token（已二次脱敏到 segment 级）    │
└────────────────────────────────────────────────────────────────────┘
```

#### 3.6.2 处理后分区一览（What Lives Where · 4-Lake 架构）

> **架构**：每 Agency **3 个独立 Neon project**（Landing / Raw PII / Processed）+ 平台级 1 个 Shared Reference Lake。Landing 与 Raw PII 位于同一 PII trust boundary（两者都含 PII，受同等保护）；Processed Lake 是业务/AI 路径，**完全无明文 PII**。

| Schema / 表                      | 所在 Lake                            | 数据形态                                                                      | 保留期                  | 谁能读                                          |
| -------------------------------- | ------------------------------------ | ----------------------------------------------------------------------------- | ----------------------- | ----------------------------------------------- |
| `landing.<source>_records`       | **🟫 Landing Lake (Bronze)**         | **整条原始 record**（PII 列加密 + 非 PII 列明文）· 全字段保留 · immutable     | HIPAA 6y / 非 HIPAA 90d | ELT 服务账号 · 合规审计员（业务/AI **禁止读**） |
| `landing.sync_state`             | **🟫 Landing Lake**                  | 每 source 的 cursor / watermark / last_run_at（增量续抓状态）                 | 永久                    | ELT 服务账号                                    |
| `raw_secure.users`               | **🔴 Raw PII Lake**                  | 主体维表：email_encrypted / phone_encrypted / hashes / pii_token              | HIPAA 6y / 非 HIPAA 90d | PII Access Service · 合规审计员                 |
| `raw_secure.<source>_pii_fields` | **🔴 Raw PII Lake**                  | 源特定 PII 字段抽取（含 record_id 关联键，**无非 PII 字段**）                 | 同上                    | 同上                                            |
| `raw_secure.pii_access_log`      | **🔴 Raw PII Lake**                  | PII Access Service 每次调用的行级审计                                         | HIPAA 6y                | 合规审计员                                      |
| `processed.raw.<source>_records` | **🟢 Processed Lake**                | 非 PII 字段 + pii_token + ingest_metadata（"非 PII 原始数据副本"，immutable） | HIPAA 6y / 非 HIPAA 90d | dbt · ELT 服务账号 · 业务 read-only             |
| `staging.stg_<source>`           | **🟢 Processed Lake**                | dbt 标准化中间产物                                                            | 30 天                   | dbt · ELT 服务账号                              |
| `canonical.<entity>`             | **🟢 Processed Lake**                | 13 个标准实体（pii_token JOIN 后）                                            | 3 年                    | 业务 / AI / 报表                                |
| `marts.<report>`                 | **🟢 Processed Lake**                | 业务报表聚合（pii_token 多已 GROUP BY 掉）                                    | 3 年 / 财务 7 年        | 业务 / AI / 报表 / 门户                         |
| `ai_context.*`                   | **🟢 Processed Lake**                | 摘要 + pgvector 向量（segment 级）                                            | 1 年                    | Core AI Brain · Context Builder                 |
| `audit.audit_events`             | **🟢 Processed Lake**（独立 schema） | 全平台 INSERT-only 审计                                                       | HIPAA 6y / 财务 7y      | 合规审计员 · Platform Super Admin               |
| `shared_*.*`                     | **🟣 Shared Reference Lake**         | B 类参考数据（无 individual PII）                                             | 按供应商合同            | 持 license 的 Agency（FDW read-only）           |

#### 3.6.2.1 各 STAGE 写入哪个 Lake（Lake 归属矩阵 · 4-Lake 架构）

> **客户常问**：4 个 STAGE 各属于哪个 Lake？答：**STAGE 1 写 Landing；STAGE 3 派生写 PII Lake + Processed Lake；STAGE 4 在 Processed Lake 内部转换**。

| STAGE                                          | 🟫 Landing Lake                                                                                | 🔴 Raw PII Lake                                                                        | 🟢 Processed Lake                                           | 🚦 仅处理                                          |
| ---------------------------------------------- | ---------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- | ----------------------------------------------------------- | -------------------------------------------------- |
| **STAGE 1 LAND**（整条 record 完整落 Bronze）  | ✅ `landing.<source>_records`（整条 record · PII 列加密）· `landing.sync_state`（cursor 状态） | —                                                                                      | —                                                           | —                                                  |
| **STAGE 2 CLASSIFY**（读 Landing，逐字段打标） | 读 Landing                                                                                     | —                                                                                      | —                                                           | ✓ 输出 `field_classification_manifest`（不落仓库） |
| **STAGE 3 SPLIT**（读 Landing，派生到两侧）    | 读 Landing                                                                                     | ✅ `raw_secure.users` · `raw_secure.<source>_pii_fields` · `raw_secure.pii_access_log` | ✅ `processed.raw.<source>_records`                         | —                                                  |
| **STAGE 4 TRANSFORM**（dbt 5 层）              | —                                                                                              | —                                                                                      | ✅ `staging.*` → `canonical.*` → `marts.*` → `ai_context.*` | —                                                  |

**🟫 Landing Lake 永远不放**：派生表 / staging / canonical / marts / ai_context / audit_events —— 仅持原始 record + sync_state。
**🔴 Raw PII Lake 永远不放**：整条原始 record · 非 PII 业务字段（campaign_id / impressions 等）· ingest_metadata · audit_events · staging/canonical/marts/ai_context 任何层。
**🟢 Processed Lake 永远不放**：明文 PII 字段（email / phone / full_name / address / IP / SSN）—— 仅持 pii_token 不可逆 hash。

#### 3.6.3 一条 Meta Ad Insight 的完整流转示例

```text
1) 外部源返回（明文 JSON）：
   { "ad_id":"123", "campaign_id":"456", "user_id":"meta_hash_abc",
     "email":"john@example.com", "spend":12.50, "impressions":1500 }

2) STAGE 1 写入 raw_secure.meta_ads_raw：
   ad_id=123, campaign_id=456,
   user_id=meta_hash_abc (L1, 明文),
   email_encrypted=Fernet(john@example.com) (L2, 加密),
   email_hash=SHA-256("john@example.com"+salt) (用于查找),
   spend=12.50, impressions=1500,
   ingest_metadata={batch_id, fetched_at, record_hash}

3) STAGE 2 分类：
   ad_id, campaign_id, spend, impressions = L0/L1
   email_encrypted, email_hash = L2 → PII manifest 写一行

4) STAGE 3 分流：
   · email_encrypted 保留在 raw_secure（不出 Raw Lake）
   · pii_token = SHA-256(email_hash + agency_salt) 计算
   · 写入 staging.stg_meta_ads：
       ad_id=123, campaign_id=456, user_id=meta_hash_abc,
       pii_token=<token>, spend=12.50, impressions=1500
   · 注意：staging 行无 email，只有 pii_token

5) STAGE 4 dbt 转换：
   · canonical.touchpoint: pii_token + campaign_id + ts + event_type
   · marts.campaign_perf: GROUP BY campaign_id → 不含 pii_token
   · ai_context.audience_summary: pii_token 聚合到 segment 级别

6) 下游消费：
   · 报表/dashboard 读 marts.* （看不到任何 PII）
   · AI Brain 读 ai_context.*（看不到 pii_token）
   · 上传到 Meta CA：UI 调 PII Access Service → service 读
     raw_secure.users 解密 email → 计算 Meta 协议 SHA-256 → API 出站
```

#### 3.6.4 一条 HubSpot Contact 同步示例（CRM 含 email/phone）

```text
1) HubSpot API: { "id":"hub-789", "email":"jane@acme.com",
                  "phone":"+1-415-…", "company":"Acme", "lifecycle":"MQL" }

2) STAGE 1 raw_secure.hubspot_contacts_raw:
   id=hub-789,
   email_encrypted=Fernet(jane@acme.com), email_hash=SHA-256(...),
   phone_encrypted=Fernet(+1415...), phone_hash=SHA-256(...),
   company="Acme" (L0), lifecycle="MQL" (L1)

3) STAGE 2: email/phone = L2, company/lifecycle = L0/L1

4) STAGE 3:
   · raw_secure.users UPSERT: pii_token = SHA-256(email_hash + agency_salt)
   · staging.stg_hubspot_contacts:
       hubspot_id=hub-789, pii_token=<token>, company="Acme",
       lifecycle="MQL" — 完全没有 email/phone

5) STAGE 4:
   · canonical.persona JOIN raw_secure.users via pii_token
     得到 unified persona 实体（仍无 email 字段）
   · marts.lead_funnel 按 lifecycle 聚合
   · ai_context.crm_summary：脱敏到 segment 级别

6) 下游：
   · 报表显示 "Acme · MQL"
   · Email 营销发送时：Pillar 调 PII Access Service →
     service 读 raw_secure.users → SMTP 出站 →
     业务团队从未在 UI 看到 jane@acme.com
```

#### 3.6.5 一条 Experian Segment 刷新示例（B 类共享数据）

```text
1) 平台 master credential 调 Experian API：
   segments 共 1,200,030 行（人口画像 taxonomy + 段定义）
   注意：API 返回是 segment-level aggregates，不含 individual PII

2) STAGE 1 写入 Shared Reference Lake.shared_experian.segments_raw：
   · 整条 record 明文存（无 PII 可加密）
   · ingest_metadata: refresh_cycle=2025-01, content_hash

3) STAGE 2 分类：
   全部字段 L0（公开 taxonomy 数据）

4) STAGE 3 分流：
   · 不需要分流——本身无 PII
   · content_hash dedup：1,200,000 行复用，30 行新增

5) STAGE 4：
   · shared_experian.segments_canonical
   · 通过 FDW 暴露给持 Experian license 的 Agency 的 Processed Lake

6) 下游：
   · ACME 的 marts.persona JOIN shared.experian_segments via segment_id
     → 得到 "Client X 的受众在 Experian taxonomy 下的画像"
   · 衍生结果（C 类）落 ACME 自己的 marts.persona_with_experian
```

#### 3.6.6 重处理与 DSAR 联动（为什么必须保留 raw_secure）

| 场景                  | 操作                                      | 依赖 raw_secure 的什么                                                                                                                                                     |
| --------------------- | ----------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **PII Detector 升级** | 新增 SSN 检测规则，要重扫历史数据         | raw_secure.\*\_raw 全字段还原（含原本未识别的字段）                                                                                                                        |
| **业务字段规则变更**  | canonical 实体改了 schema                 | 从 raw_secure → staging → canonical 重跑 dbt                                                                                                                               |
| **DSAR 删除请求**     | 主体 john@example.com 要求删除            | PII Access Service: SHA-256(email+salt) → 定位所有含此 pii_token 的 row（raw_secure / staging / canonical / marts），按法规要求删除或匿名化；audit_events 保留删除痕迹本身 |
| **法律调查**          | 监管要求"提供此人所有数据"                | PII Access Service: 同上逻辑 → 输出 DSAR JSON                                                                                                                              |
| **数据质量问题排查**  | marts 报表数字异常                        | 沿 dbt lineage 反查到 raw_secure 的原始 record                                                                                                                             |
| **审计师抽样核查**    | SOC 2 审计师要看"原始数据 → 报表"完整链路 | raw_secure → staging → canonical → marts 全链路可重现                                                                                                                      |

> **设计要点**：`raw_secure.*_raw` 是 immutable "事实的真实副本"——一旦 ingest 就不修改、不覆盖、不删除（除非 DSAR / 保留期到期）。`pii_token` 是跨 4 层 schema 的"主体定位主键"，使 DSAR / 重处理可以**在不解密 PII 的前提下**定位主体并联动操作。

#### 3.6.7 保留期分级

| 数据层                           | Lake             | 保留期                                      | 法规依据                   |
| -------------------------------- | ---------------- | ------------------------------------------- | -------------------------- |
| `raw_secure.*_raw`（HIPAA 客户） | Raw PII          | **6 年**                                    | HIPAA §164.530(j)          |
| `raw_secure.*_raw`（非 HIPAA）   | Raw PII          | **90 天**                                   | GDPR 数据最小化            |
| `raw_secure.users`               | Raw PII          | 合同期 + 30 天                              | GDPR Art. 5(1)(e)          |
| `staging.*`                      | Processed        | **30 天**                                   | 中间产物，可重算           |
| `canonical.*`                    | Processed        | **3 年**                                    | 业务保留                   |
| `marts.*`                        | Processed        | **3 年** / 财务相关 **7 年**                | GDPR + 财务合规            |
| `ai_context.*`                   | Processed        | **1 年**（按需刷新）                        | 内容衍生，可重新生成       |
| `audit.audit_events`             | Processed        | **6 年** / 财务 **7 年**                    | HIPAA + 财务合规（最严值） |
| `shared_*.*`                     | Shared Reference | 按供应商合同（多为永久 / refresh-on-cycle） | 供应商 contract            |

#### 3.6.8 决策摘要

| 问题                     | 答案                                                                                                                                             |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| 原始数据存哪？           | `raw_secure.*_raw` in **Raw PII Lake**（per-Agency Neon project），PII 字段加密，非 PII 明文，整条 record 不丢字段                               |
| 为什么要保留原始？       | DSAR / 重处理 / 法律调查 / 审计追溯 4 大场景必需                                                                                                 |
| 处理后怎么划分？         | 4 层 dbt schema：`staging`（30d 中间）→ `canonical`（3y 标准实体）→ `marts`（3y 业务报表）→ `ai_context`（1y AI 召回）—— 全在 **Processed Lake** |
| PII 还在不在 Processed？ | **否**。Processed 4 层只持 `pii_token`（不可逆 hash），明文 PII 永远只在 Raw PII Lake                                                            |
| 怎么跨 Lake 关联？       | `pii_token = SHA-256(email_hash + agency_salt)` —— 同 Agency 内 Processed 可与 Raw 关联，跨 Agency 因 salt 不同而无法关联                        |
| B 类共享数据怎么放？     | Shared Reference Lake 独立 schema，无个体 PII，license-gated FDW 暴露                                                                            |

---

## 4. Multi-Tenant 数据仓库（Neon Postgres）

### 4.0 仓库选型：Neon Postgres（产品锁定）

> **产品决策**：仓库统一采用 **Neon Postgres（serverless Postgres）**。基于客户偏好（Matt）+ 本架构的物理隔离 / Branching / 应用层零迁移成本三大要求，Neon 为本产品**唯一仓库选型**，不再保留 Snowflake 作为备选。详见 [ADR-002-NEON-TENANCY-OPTIMAL](../ADR-002-NEON-TENANCY-OPTIMAL.md)。

**Neon 关键能力**：

| 能力                | 实现方式                                                           |
| ------------------- | ------------------------------------------------------------------ |
| **物理隔离单位**    | 每 Agency 独立 **Project**（独立计算 + 存储 + 端点 + KMS）         |
| **计算-存储分离**   | Serverless Postgres，独立 compute endpoint                         |
| **零拷贝复制**      | **Branching**（git-style branch，按需克隆，秒级创建）              |
| **行级安全（RLS）** | Postgres native `ROW LEVEL SECURITY` + policy                      |
| **数据驻留**        | Region-scoped project（us-east / eu-central / ap-\* 等）           |
| **应用层兼容**      | 标准 Postgres 协议；FastAPI / SQLAlchemy 零迁移成本                |
| **成本模型**        | 按存储 + 计算用量（serverless 友好，闲置租户自动 scale-to-zero）   |
| **生态扩展**        | pgvector（向量索引）· pg_partman（分区）· pg_audit（审计）原生可用 |

本文余下章节的 SQL / 实现细节均基于 Neon Postgres。

### 4.1 物理隔离模型（3 档）— 每 Agency 独立 Project / Database

**租户 = Agency**。每个 Agency 物理隔离，下属 **Client 在 Agency 数据库内通过 RLS 逻辑隔离 — 明确不做 per-Client 物理隔离**。

> **重要决策**：不向 Client 层延伸物理隔离。
> 客户明确要求保留**跨 Agency 性能 benchmark** 能力（Rose 提出），per-Client 物理隔离会使该能力难以实现。Client 之间仅通过 `client_id` RLS 在 Agency 数据库内逻辑隔离即可满足合规与数据保护要求。

**不存在"共享 Agency + RLS only"档**——RLS 始终作为 defense-in-depth，不是主防线（同 §4.4）。

| Agency 级别    | Neon 实现                                                       | 加密 / 计算                                         | 适用对象                      |
| -------------- | --------------------------------------------------------------- | --------------------------------------------------- | ----------------------------- |
| **Standard**   | 独立 **Neon Project**（per-Agency）+ 独立 database + role       | 独立 KMS 密钥；共享 Neon org；自动伸缩 compute 配额 | 普通代理商                    |
| **Enterprise** | 独立 Project + 独立 **compute endpoint**（dedicated）+ role 池  | 独立 KMS；独立计算端点；资源配额可观测              | 大客户、高数据量、SLA 要求高  |
| **Regulated**  | 独立 Project + **region-bound deployment**（独立 region / VPC） | project-level 独立密钥；BAA / DPA 必签              | HIPAA · 强数据驻留 · 合同要求 |

**关键设计原则：**

- **每个 Agency 的数据在物理层就不可达**：跨 Agency 查询从存储层直接失败（不依赖应用层或行级过滤）
- **Client 级别在 Agency 内逻辑隔离**：同一 Agency 下的所有 Client 共享 Agency 数据库，通过 `client_id` RLS 限制可见性。**保留跨 Agency benchmarking 能力**（Super Admin 可对所有 Agency 的聚合指标做横向对比）
- **Super Admin 跨 Agency 视图**：只暴露聚合指标的 secure aggregation view（不可解出明文 PII / PHI / 业务数据）
- 提升隔离档（Standard → Enterprise → Regulated）通过 zero-copy clone / branching 平滑迁移
- 每 Agency 密钥独立持有 → 即使一个 Agency 密钥泄露，其他 Agency 的加密数据仍不可解

### 4.2 推荐 Schema 结构

| Schema       | 用途                                                              |
| ------------ | ----------------------------------------------------------------- |
| `raw_secure` | 引用加密 PII 文件 + 受限元数据（不含明文敏感字段）                |
| `staging`    | 按源系统的标准化中间表                                            |
| `canonical`  | 跨平台统一实体（campaign / persona / touchpoint 等）              |
| `marts`      | 面向报表的业务聚合表（campaign / persona / attribution / portal） |
| `ai_context` | AI 安全的 summary、embedding、retrieved context、prompt citation  |
| `audit`      | 数据访问、ELT 运行、AI 请求、合规事件                             |

### 4.3 Canonical Entities · 标准实体

| 实体                 | 说明                                     |
| -------------------- | ---------------------------------------- |
| `tenant`             | 租户主表（agency + 配置）                |
| `client`             | Brand / Client（agency 的客户）          |
| `data_source`        | 数据源注册表（GA4 / Meta / Experian 等） |
| `campaign`           | 跨平台统一活动                           |
| `media_placement`    | Ad Group / Line Item 统一抽象            |
| `creative_asset`     | 创意素材（文案 + 图 + 视频）             |
| `audience_segment`   | 受众段（匿名化）                         |
| `persona`            | Persona 画像                             |
| `touchpoint`         | 触点（曝光 / 点击 / 访问）               |
| `conversion_event`   | 转化事件                                 |
| `attribution_result` | 归因结果                                 |
| `report`             | 报表实例                                 |
| `audit_event`        | 审计事件                                 |

### 4.4 Row-Level Security（双重职责）

RLS 在物理隔离架构中有**两类不同用途**：

#### 4.4.1 跨 Agency 防护（Defense-in-Depth）

跨 Agency 物理隔离已由独立 database 保证，RLS 只作为额外保险：

- **共享元数据 / 平台审计表**（如平台级 `audit_event`、`agency_directory`、`token_usage`）：跨 Agency 但只对 Super Admin 暴露聚合视图
- **Standard 档共享 warehouse**：防止误配置导致跨 database 查询
- **合规审计员**临时查询：自动按 `agency_context` 收敛

#### 4.4.2 Agency 内 Client 级隔离（主要用途）

**这是 RLS 的核心用武之地**：同一 Agency 的多个 Client 共享 Agency 数据库，必须用 RLS 实现 Client Viewer 只看自己的数据。

**Neon Postgres 实现：**

```sql
-- 在 Agency database 的每个 fact / dim 表启用 RLS
ALTER TABLE marts.campaign_performance ENABLE ROW LEVEL SECURITY;

CREATE POLICY client_isolation ON marts.campaign_performance
  USING (
    current_setting('app.role') IN ('AGENCY_ADMIN', 'AGENCY_OPERATOR')  -- Agency 角色看全部 client
    OR client_id = current_setting('app.client_id')::uuid                 -- Client Viewer 只看自己
  );
```

`app.role` 与 `app.client_id` 通过 `SET LOCAL` 在每个查询事务前由应用层注入。**三层叠加**：

1. **Agency 物理隔离**：跨 Agency 不可达（独立 database）
2. **Agency 内 Client RLS**：Client Viewer 只看自己的 `client_id` 数据
3. **App 层过滤**：API 端点强制 `agency_id` + `client_id` 校验

### 4.5 Zero-Copy Cloning

用例：

- **租户 onboarding**：快速复制基础数据模型、空 schema 和示例配置
- **Enterprise 隔离副本**：为大客户创建逻辑隔离实例
- **QA / UAT / 回归测试**：接近生产结构的环境
- **Region migration / 备份**：低成本副本
- **客户争议回溯**：合规审计员核对历史快照

> ⚠️ Zero-copy clone **不能替代合规删除流程**。涉及 PII/PHI 的数据仍需遵守保留、删除、审计和密钥销毁策略。

### 4.6 Per-Tenant Data Residency · 每租户数据驻留

每个租户在 onboarding 时绑定**主区域**（`us-east-1` · `eu-central-1` · `ap-southeast-1` …）。所有该租户的数据：

- Raw Lake / Processed Lake 物理存储于绑定区域
- KMS 密钥与备份同区域
- AI 推理调用就近选择 LLM 区域（HIPAA + EU 客户走 AWS Bedrock 同区）
- 跨区数据流必须经 **数据驻留检查器（DLP 规则引擎）** 拦截

EU / Canada / healthcare / government-adjacent 租户需要单独评估 region-locking。

---

## 5. ELT Pipeline · 八步管道

```text
Extract            ┐
  → Classify        │  Pipeline (调度器：Dagster OSS / Apache Airflow 二选一)
  → Load            │
  → Transform in Warehouse (Neon Postgres)
       → Normalize  │
       → Deduplicate│
       → Validate   │  ← PHI Detector 在此扫描
       → Enrich     │
       → Index      │
  → Audit (全程伴随，INSERT-only · 6 年保留)
```

采用 **ELT**（不是 ETL）是因为仓库（Neon Postgres）更适合作为可扩展的转换执行层，并且便于保留可审计的 raw / staging 记录。

**与 Network Diagram 流向条的对应**：

- **流向条 ① Extract** = §5.1
- **流向条 ② Classify · Transform · Load** = §5.2–5.8（八步中的 7 步在仓库内完成）
- **横切 Audit** = §5.9 调度器的 asset materialization + audit_events 表

### 5.1 Extract — 抽取

- API 抽取（OAuth / API key / service account）+ 加密文件 intake（Tresorit / SFTP）
- 凭证存于 **Credential Vault**（per-tenant 加密）
- 失败重试 + 指数退避

### 5.2 Classify — 分类（PII/PHI 路由）

- 自动检测：HIPAA Safe Harbor 18 类标识符 + GDPR PII 字段
- 路由：PII/PHI → Raw PII Lake；非 PII → 直接进 ELT staging
- 路由策略记录可解释（哪条字段命中哪条规则）

### 5.3 Load — 加载

- 安全 raw / staging 数据加载到仓库（Neon Postgres）；敏感原始数据加载到 PII-segregated lake
- 可审计的批次 ID + 来源指纹

### 5.4 Normalize — 字段标准化

跨平台字段映射到统一 canonical schema：

| Source                                                                 | Target Canonical Entity |
| ---------------------------------------------------------------------- | ----------------------- |
| Meta Campaign / TikTok Campaign / DV360 Insertion Order / TTD Campaign | `campaign`              |
| Meta Ad Set / TikTok Ad Group / DV360 Line Item / TTD Ad Group         | `media_placement`       |
| GA4 / Meta / DV360 / TTD conversions                                   | `conversion_event`      |

### 5.5 Deduplicate — 去重

覆盖场景：API 增量同步重复、文件重复上传、多 report 重复、CRM 多系统重复。

策略：source-native primary key + tenant-scoped external ID + hash fingerprint + ingestion batch ID + latest-write-wins / source-priority merge rule。

### 5.6 Validate — 校验

- Schema：字段类型、必填、值域
- 业务规则：金额非负、日期不在未来、货币 / 时区 / 平台枚举可识别
- **PII/PHI 误入 processed layer 检测**：命中即拦截

校验失败的数据进入 **quarantine queue**，不直接进入主仓库。

### 5.7 Enrich — 富集

- Campaign 与 client / brand 的映射
- 地理、行业、受众分层标签补全
- GA4 conversion 与媒体 touchpoint 的可归因关系
- Experian / TransUnion / Nielsen 等第三方画像与匿名受众 key 的关联
- Placer IQ / Quorum 线下行为信号与市场区域的关联

### 5.8 Index — 索引

- 结构化索引：`tenant_id` · `client_id` · `campaign_id` · `date` · `source_system`
- 语义索引：persona narrative · creative brief · market research note · campaign insight summary
- 向量索引：用于 RAG，**但不得存储明文 PII**

### 5.9 调度（Orchestration）

**主调度引擎：Dagster OSS 与 Apache Airflow 二选一**（详见 [ELT-ORCHESTRATION-PRIORITY](../ELT-ORCHESTRATION-PRIORITY.md)）。两者都可承载本平台 ELT 八步管道，按团队偏好与项目阶段决定：

| 维度               | 🟪 Dagster OSS                              | 🟦 Apache Airflow                          |
| ------------------ | ------------------------------------------- | ------------------------------------------ |
| **数据血缘**       | ✅ 原生 Asset Graph                         | 🟡 需 OpenLineage 外挂                     |
| **dbt 一等集成**   | ✅ `dagster-dbt`（每个 model 自动成 asset） | 🟡 `dbt-airflow` provider                  |
| **多租户**         | ✅ Partition Key = Agency                   | 🟡 DAG 参数化                              |
| **Connector 生态** | 🟡 ~300 集成                                | ✅ 1000+ Provider                          |
| **学习曲线**       | ⚠️ Asset 心智需 1-2 周                      | ✅ 业内最普及                              |
| **合规**           | ✅ Code Location per-region                 | ✅ 自托管任意 region                       |
| **推荐场景**       | 血缘 / 多租户 / dbt-heavy / AI asset 可追溯 | 团队已熟 / 1000+ Connector / 传统 DAG 心智 |

> 详细评估见 [ELT-ORCHESTRATION-PRIORITY §4](../ELT-ORCHESTRATION-PRIORITY.md)。从最优视角推荐 Dagster OSS；若团队已熟 Airflow 且短期不需要原生血缘，Airflow 同样可承载本平台 ELT。

**辅助调度**：

- **AWS Step Functions** — 仅用于 AI 写回审批工作流（Media Agent → Meta / DV360 / TikTok 写回必须 human approval）与 DSAR 长流程（受理 → PII Access Service → 数据导出 → 邮件投递 → 客户确认），由主调度器（Dagster / Airflow）触发。
- **AWS Glue** — 仅用于大数据 backfill 子任务（GB+ 级历史数据），由主调度器调用，不作主调度。

**规模化升级路径**：若选 Dagster OSS，客户数 ≥ 10 Agency / 团队 ≥ 8 人 → 升级到 **Dagster Cloud Hybrid**（控制面云端、计算面自托管，含 RBAC / SSO / 内置审计 6 年）；若选 Airflow，可升级到 self-host HA 集群或 MWAA。

每步符合：**幂等 · 可断点 · 可回滚 · 全审计**（asset materialization / DAG run history + audit_events 表）。

---

## 6. Core AI Brain

### 6.1 六大核心组件

| 组件                     | 职责                                                                                  |
| ------------------------ | ------------------------------------------------------------------------------------- |
| **Context Builder**      | 从仓库（Neon Postgres）收集 tenant-safe / role-safe / PII-safe 上下文（不含明文 PII） |
| **LLM Router**           | 按 agent / cost / latency / 合规 / 租户策略选模型                                     |
| **Agent Orchestrator**   | 协调 4 个 Pillar Agent，串/并联调用                                                   |
| **Tool Executor**        | 调用受批准的读 / 写工具；写回操作经审批门                                             |
| **Memory & Retrieval**   | 使用 summary + 向量检索，无明文 PII                                                   |
| **Audit & Cost Control** | 记录 prompt / 输出 / token / 数据访问 / 模型决策                                      |

### 6.2 LLM Router 路由策略

- **任务匹配**：Persona deep reasoning → Claude Opus；Creative / Attribution / Media → Claude Sonnet
- **合规路由**：HIPAA 客户走 AWS Bedrock 直连 + BAA（旁路 OpenRouter）
- **成本/延迟**：按 token budget / latency / cost tier 路由
- **可移植性**：OpenAI / Anthropic / OpenRouter / 企业私有模型间切换
- 详见 [PSD-LLM-SELECTION-DECISION.md](../PSD-LLM-SELECTION-DECISION.md)

### 6.3 四个 Pillar Agent

| Agent                 | 用途                                                                   | 主模型                    | 输入                             | 产出                                  |
| --------------------- | ---------------------------------------------------------------------- | ------------------------- | -------------------------------- | ------------------------------------- |
| **Persona Agent**     | 根据市场数据、人群画像、第三方 audience signals 生成 persona blueprint | Claude Opus 4.7（1M ctx） | Canonical 数据 + 业务目标        | Persona blueprint、人口画像、向量嵌入 |
| **Creative Agent**    | 根据品牌、persona、历史表现生成创意方向、文案、素材建议                | Claude Sonnet 4.6         | Brand voice + 历史 CTR + Persona | 多版本文案（标题/正文/CTA）+ 评分     |
| **Attribution Agent** | 分析 touchpoints、conversion、媒体表现，生成归因解释和优化建议         | Claude Sonnet 4.6         | Touchpoints + 转化事件           | 归因权重、渠道贡献、ROI 排名、解释    |
| **Media Agent**       | 读取媒体表现、预算、pacing，提出或执行投放优化建议（写回需审批）       | Claude Sonnet 4.6         | 预算、目标受众、平台费率         | 跨平台预算分配、出价建议、buying plan |

### 6.4 Audit & Cost Control

- 每次调用入参 / 出参 / token / 调用模型 / 数据访问全量写 `audit.ai_request`
- Token 预算：per-tenant `monthly_token_budget`，耗尽 → HTTP 429
- 重试：3 次指数退避，60 s 总超时
- Langfuse：每次调用产生 trace + score

---

## 7. Priority 1 Integrations · 优先级 1 集成

### 7.1 数据供应商 / CRM / 市场信号

| 集成           | 类别                 | 用途                                                 | 接入方式               | 优先价值                                             |
| -------------- | -------------------- | ---------------------------------------------------- | ---------------------- | ---------------------------------------------------- |
| **Experian**   | 受众数据 Audience    | Mosaic、人群画像、人口统计、心理图谱                 | 文件/API（取决于合同） | Persona 和市场研究核心数据                           |
| **TransUnion** | 受众数据 Audience    | 身份、受众、线下/线上连接数据                        | API/文件               | 受众增强、匹配、归因                                 |
| **LiveRamp**   | 身份解析 Identity    | RampID 跨设备身份图谱、第一/二方受众激活、匹配率提升 | API（双向 RampID）     | 跨平台身份连接、受众激活                             |
| **HubSpot**    | CRM                  | 客户/Lead/Deal/Marketing 自动化数据；CRM 主数据来源  | OAuth + API（Hub API） | 客户画像、Lead → conversion 完整归因、营销自动化数据 |
| **Nielsen**    | 媒介测量 Measurement | 媒体消费、受众测量、市场数据                         | API/文件               | 市场规模、媒体偏好、benchmark                        |
| **Placer IQ**  | 地理 / 线下 Offline  | 地理位置、门店/区域客流、线下行为                    | API/导出文件           | 离线行为与地理洞察                                   |
| **Quorum**     | 倡导 Advocacy        | 政治、社区、地理或受众相关信号                       | API/导出文件           | 区域与人群洞察                                       |

### 7.2 媒体 / DSP 平台

| 集成               | 用途                                                      | 关键数据                                                                                                 |
| ------------------ | --------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| **DV360**          | Google Display & Video 360 投放                           | Advertiser / Campaign / Insertion Order / Line Item / Creative / Spend / Impression / Click / Conversion |
| **Meta**           | Facebook/Instagram paid media + audience                  | Campaign / Ad Set / Ad / Insight / Pixel Event / Custom Audience                                         |
| **TikTok**         | TikTok Ads 投放与 creative performance                    | Advertiser / Campaign / Ad Group / Ad / Spend / Click / Conversion / Creative                            |
| **The Trade Desk** | Programmatic DSP + open web buying                        | Advertiser / Campaign / Ad Group / Creative / Bid / Spend / Conversion                                   |
| **StackAdapt**     | Programmatic 多渠道 DSP（Display/Native/Video/CTV/Audio） | Advertiser / Campaign / Ad Group / Creative / Spend / Impression / Click / Conversion                    |
| **GA4**            | 第一方网站与 App analytics                                | Event / Session / User Property / Traffic Source / Conversion / Ecommerce                                |

### 7.3 Tresorit · 合规 CRM 传输

用于合规 CRM transfer 和敏感文件交换。在 MVP 中定位为安全文件进入 **Raw PII-Segregated Lake** 的入口之一。

适用场景：

- 客户上传 CRM export
- 上传包含 email / phone / customer list 的受众文件
- 上传需要合规链路的 healthcare / regulated client 数据
- 客户无法提供 API 时的安全替代方案

---

## 8. 合规与数据驻留

### 8.1 GDPR

- **DSAR**：访问 / 删除 / 导出 / 更正 / 限制处理 SLA ≤ **30 天**
- **数据保留**：营销 3 年、财务 7 年（与最严值对齐）
- **违规通知**：72 小时内通知监管机构
- **DPA**：与所有数据处理方签署 Data Processing Agreement
- **EU 客户数据**：默认 `eu-central-1` 或 `eu-west-1` 区域驻留

### 8.2 CCPA

- **DSAR SLA ≤ 45 天**
- **Opt-Out**："Do Not Sell My Personal Information" 客户门户可见
- **数据销售追踪**：第三方共享记录

### 8.3 HIPAA

- **BAA**：所有 HIPAA 客户必签 Business Associate Agreement，状态系统追踪
- **18 类 Safe Harbor 标识符** 自动检测与匿名化（PHI Detector）
- **AES-256 静态加密** + **TLS 1.3 传输加密**
- **会话超时**：15 分钟不活动
- **审计日志**：6 年 INSERT-only
- **违规通知**：60 天内通知 HHS
- **LLM 路径**：HIPAA 客户走 AWS Bedrock + BAA 旁路

### 8.4 SOC 2 Type II

针对 5 个 Trust Service Principles 设计控制：

| Principle            | 控制要点                              |
| -------------------- | ------------------------------------- |
| Security             | RBAC、MFA、密钥管理、定期渗透测试     |
| Availability         | SLO 99.9%、多可用区、灾备演练         |
| Processing Integrity | 数据完整性校验、变更审计、事务一致性  |
| Confidentiality      | 数据分级（4 级）、最小权限、加密      |
| Privacy              | DSAR、保留策略、隐私通知、Cookie 管理 |

年度 Type II 审计，证书提供给企业客户。

### 8.5 Per-Tenant Data Residency

参见 §4.6。

### 8.6 PII Segregation Boundary

参见 §3.3。

---

## 9. Auth & SSO Boundary

> MVP 阶段保留基础登录、RBAC、tenant isolation 和 audit logging。Google / Office365 SSO 标记为 post-MVP。

| 能力                               | MVP | Post-MVP     |
| ---------------------------------- | --- | ------------ |
| 邮箱密码登录 + JWT                 | ✓   | ✓ (fallback) |
| Google Workspace SSO               | —   | ✓            |
| Microsoft Office365 / Entra ID SSO | —   | ✓            |
| SCIM provisioning                  | —   | ✓            |
| Enterprise SAML                    | —   | ✓            |
| RBAC + 租户隔离 + 审计             | ✓   | ✓            |
| MFA（通过 IdP）                    | —   | ✓            |

**MVP 不应因为 SSO 延后而牺牲租户隔离、权限边界或审计。**

---

## 10. MVP Functional Pillars · MVP 功能 Pillars

| Pillar              | 描述                                            | 主要 Agent        | 关键数据源                                                  |
| ------------------- | ----------------------------------------------- | ----------------- | ----------------------------------------------------------- |
| **Market Research** | 受众画像、市场洞察、竞品分析、Persona blueprint | Persona Agent     | Experian / TransUnion / GA4 / Nielsen                       |
| **Creative Engine** | 创意文案与素材生成、A/B 实验、品牌调性约束      | Creative Agent    | Brand voice + 历史 CTR                                      |
| **Media Buying**    | 跨平台预算分配与采买策略；写回需人工审批        | Media Agent       | DV360 / Meta / TikTok / Trade Desk / StackAdapt / Placer IQ |
| **Attribution**     | 跨渠道归因与 ROI 分析、归因报表叙述             | Attribution Agent | GA4 / LiveRamp / 所有广告平台                               |
| **Client Portal**   | 白标仪表板、AI 摘要、报告访问、按角色过滤可见性 | （无 Agent）      | 上述四个 pillar 的产出                                      |

### 10.1 Portal 用户角色

**三级角色层级**（从上到下，数据可见范围由大到小）：

| 层级          | 用户类型                         | 主要体验                                                   | 数据可见范围                                          |
| ------------- | -------------------------------- | ---------------------------------------------------------- | ----------------------------------------------------- |
| **L1 平台**   | **Platform Super Admin**（内部） | 跨 Agency 平台总览、Agency 开通、平台健康、计费 & 用量统计 | 所有 Agency 的**聚合 / 元数据**（不可解明文业务数据） |
| **L2 Agency** | **Agency Admin**                 | Agency 设置、Client 管理、用户管理、集成、审计             | 该 Agency 下**所有 Client 的全部数据**                |
| **L2 Agency** | **Agency Operator**              | 日常 campaign 健康、研究、创意、媒体和归因工作流           | 该 Agency 下所有 Client（按业务角色裁剪）             |
| **L3 Client** | **Client Viewer**                | 白标摘要、性能报表、批准的洞察                             | 仅本 Client 的数据（Agency 内 RLS 过滤）              |

**关键边界：**

- **Platform Super Admin** 只看跨 Agency 的 secure aggregation view（活跃 Agency 数、总 token 用量、平台健康），**不可越界查询任何 Agency 的明文业务数据**——Agency-level KMS 密钥不对平台总管理员开放
- **Agency Admin / Operator** 在该 Agency 的物理 database 内全权操作所有 Client
- **Client Viewer** 通过 Agency 数据库内的 `client_id` RLS 过滤，只看自己的数据子集

---

## 11. MVP Technical Decision Summary

| 主题            | 决策                                                                                                                                             |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| 数据策略        | Raw PII-Segregated Lake + Processed Lake                                                                                                         |
| 仓库            | **Neon Postgres**（per-Agency project · serverless · Branching）                                                                                 |
| 隔离            | **物理隔离**：每租户独立 Neon project + 独立 KMS 密钥；Enterprise 增加独立 compute endpoint；Regulated 独立 region。RLS 作为 defense-in-depth    |
| PII             | 不进入通用 processed warehouse，不进入默认 AI prompt                                                                                             |
| ELT             | extract → classify → load → normalize → dedup → validate → enrich → index                                                                        |
| AI              | Core AI Brain（6 components）+ LLM Router + 4 agent orchestration                                                                                |
| Agents          | Persona · Creative · Attribution · Media                                                                                                         |
| Autonomy        | Human-in-the-loop（预算/写回必须人工）                                                                                                           |
| Priority 1 集成 | Experian · TransUnion · LiveRamp · HubSpot · Nielsen · Placer IQ · Quorum · DV360 · Meta · TikTok · The Trade Desk · StackAdapt · GA4 · Tresorit |
| 合规            | GDPR · CCPA · HIPAA · SOC 2                                                                                                                      |
| 数据驻留        | per-tenant requirement                                                                                                                           |
| SSO             | Google + Office365 post-MVP                                                                                                                      |

---

## 12. MVP 实施时序（10 步）

| #   | 阶段                            | 内容                                                               |
| --- | ------------------------------- | ------------------------------------------------------------------ |
| 1   | **基础架构**                    | 租户模型、合规边界、canonical schema、Neon Postgres 仓库结构       |
| 2   | **安全摄取**                    | Credential vault、文件 intake、Tresorit 流、API connector 框架     |
| 3   | **优先读取连接器**              | Experian sample · GA4 · Meta · DV360 · TikTok · The Trade Desk     |
| 4   | **Processed Lake + marts**      | campaign performance · audience/persona · attribution-ready tables |
| 5   | **Core AI Brain**               | LLM Router · Context Builder · Audit · Token budget                |
| 6   | **Market Research pillar**      | Persona Agent + audience blueprint workflow                        |
| 7   | **Attribution + Client Portal** | 报表 · AI 摘要 · 白标视图                                          |
| 8   | **Creative + Media 建议**       | Agent 生成建议（read-only）                                        |
| 9   | **写回自动化**                  | Media actions with approval gates                                  |
| 10  | **企业 Auth (post-MVP)**        | Google SSO · Office365 SSO · SCIM / SAML                           |

---

## 13. Technical Constraints · 关键约束

| 约束                                               | 影响                                                      |
| -------------------------------------------------- | --------------------------------------------------------- |
| Unified canonical schema 必须早期锁定              | 集成与 Agent 建成后再改成本极高                           |
| PII segregation 是架构级而非可选                   | 影响 ingestion、storage、AI context、audit 和删除流程     |
| Neon RLS 必须在租户数据入仓前设计                  | 防止跨租户泄漏，支撑 Enterprise readiness                 |
| Data residency 是 per-tenant                       | 影响 Neon region、对象存储、备份、模型供应商路由          |
| 数据源合同可能晚于技术工作                         | Experian / TransUnion / Nielsen 等需 sample-file fallback |
| 媒体平台写访问可能延迟                             | MVP 先支持 read/reporting，写回操作必须 gate              |
| GA4 / 媒体历史数据需 batch backfill                | onboarding 期望要明确处理时长沟通                         |
| Tresorit 是安全传输路径，**不是规范化 CRM schema** | CRM 文件 ingestion 仍需 mapping、validation 和 PII 处理   |
| SSO 是 post-MVP                                    | MVP 仍须含 secure auth、RBAC、tenant isolation、audit     |
| AI 默认不消费明文 PII                              | 需 AI-safe context builder + redaction/tokenization 规则  |

---

## 14. Technical Dependencies · 关键依赖

| 依赖                              | 用途                            | 优先级                    |
| --------------------------------- | ------------------------------- | ------------------------- |
| Tenant model + 隔离策略           | 所有产品 pillar                 | **P0**                    |
| Canonical marketing schema        | ELT · 报表 · AI agents          | **P0**                    |
| PII 分类 + 路由                   | 合规 · CRM transfer · AI safety | **P0**                    |
| Neon project · region · role 设计 | 仓库 + 数据驻留                 | **P0**                    |
| Credential vault                  | 所有 API 集成                   | **P0**                    |
| ELT orchestration + monitoring    | 集成与数据新鲜度                | **P0**                    |
| Experian sample data              | Market Research MVP             | **P0**                    |
| GA4 + 媒体历史 export             | Attribution + onboarding demo   | **P0**                    |
| DV360/Meta/TikTok/TTD API access  | Media Buying + reporting        | **P0/P1**（取决于写访问） |
| Tresorit transfer process         | 合规 CRM intake                 | **P0**                    |
| LLM provider 决策                 | Core AI Brain + 成本控制        | **P0**                    |
| Human approval workflow           | 媒体写回、预算变更              | **P1**                    |
| Google / Office365 SSO            | 企业 auth                       | **Post-MVP**              |

---

## 15. 引用与延伸阅读

**配套图与释义**：

- [Network Diagram](./network-diagram.svg) — 网络数据流图（6 层 + 5 条流向条）
- [Network Diagram Explained](./network-diagram-explained.md) — 网络图逐层名词与流程释义
- [Architecture Schema](./architecture-schema.svg) — 平台架构示意图（7 层 + 6 条流向条 + 合规面板）
- [Architecture Schema Explained](./architecture-schema-explained.md) — 架构图逐层名词与流程释义

**关键决策与 ADR**：

- [ELT-ORCHESTRATION-PRIORITY.md](../ELT-ORCHESTRATION-PRIORITY.md) — Dagster vs Airflow vs AWS ELT 选型（结论：二选一）
- [ADR-002-NEON-TENANCY-OPTIMAL.md](../ADR-002-NEON-TENANCY-OPTIMAL.md) — Neon Postgres 多租户隔离（产品锁定）
- [ADR-003-DAGSTER-VS-AIRFLOW.md](../ADR-003-DAGSTER-VS-AIRFLOW.md) — 编排引擎主决策
- [ADR-003-SUPP-OTHER-ORCHESTRATORS.md](../ADR-003-SUPP-OTHER-ORCHESTRATORS.md) — 其他编排引擎对比
- [PSD-LLM-SELECTION-DECISION.md](../PSD-LLM-SELECTION-DECISION.md) — LLM 选型决策

**其他**：

- [Solution Package · 主索引](../receptiviq-solution-package/README.md)
- [ARCHITECTURE-DEEP-DIVE.md](../ARCHITECTURE-DEEP-DIVE.md) — 整体架构深度

---

## 16. 关键约束清单（供优先级工具评估）

| 约束类别               | 内容                                                                                                                                                                                                                                                                                   |
| ---------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **数据驻留**           | 每租户区域绑定；跨区禁止                                                                                                                                                                                                                                                               |
| **加密**               | AES-256 at rest；TLS 1.3 in transit；per-tenant KMS key                                                                                                                                                                                                                                |
| **认证**               | MVP：JWT + 基础登录；Post-MVP：Google + Office 365 SSO                                                                                                                                                                                                                                 |
| **合规**               | GDPR / CCPA / HIPAA（含 BAA）/ SOC 2 Type II                                                                                                                                                                                                                                           |
| **PII 边界**           | Raw Lake 不开放给业务/AI；处理后 Lake 已匿名化；tokenized join 跨界                                                                                                                                                                                                                    |
| **多租户**             | **物理隔离 = Agency 层**（Neon Postgres）：per-Agency Neon project + per-Agency KMS 密钥（baseline）；Enterprise 独立 compute endpoint；Regulated 独立 region。**Client 仅 RLS 逻辑隔离**（不做 per-Client 物理隔离 → 保留跨 Agency benchmarking 能力）。Neon Branching 用于副本与迁移 |
| **PII 出口**           | 明文 PII 仅经 **PII Access Service**（purpose-bound · 短期 token · 内存哈希 · 不入 Processed Lake / AI Brain）出口到 Meta CA / DV360 / LiveRamp / DSAR 响应。Lake 之间 **hard isolation**（独立存储集群 + 独立 KMS）                                                                   |
| **LLM 路由**           | OpenRouter 默认；HIPAA → AWS Bedrock BAA 旁路                                                                                                                                                                                                                                          |
| **Autonomy**           | Human-in-the-loop（预算 / 写回 / 暂停广告）                                                                                                                                                                                                                                            |
| **审计**               | INSERT-only；HIPAA 6 年；GDPR 财务 7 年                                                                                                                                                                                                                                                |
| **DSAR SLA**           | GDPR 30d / CCPA 45d / HIPAA 30d                                                                                                                                                                                                                                                        |
| **违规通知**           | GDPR 72h / HIPAA 60d                                                                                                                                                                                                                                                                   |
| **集成 P1**            | 14 个：Experian · TransUnion · LiveRamp · HubSpot · Nielsen · Placer IQ · Quorum · DV360 · Meta · TikTok · The Trade Desk · StackAdapt · GA4 · Tresorit                                                                                                                                |
| **MVP Pillars**        | Market Research · Creative Engine · Media Buying · Attribution · Client Portal                                                                                                                                                                                                         |
| **Canonical Schemas**  | 6 个：raw_secure · staging · canonical · marts · ai_context · audit                                                                                                                                                                                                                    |
| **Canonical Entities** | 13 个：tenant · client · data_source · campaign · media_placement · creative_asset · audience_segment · persona · touchpoint · conversion_event · attribution_result · report · audit_event                                                                                            |
