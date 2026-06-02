# 网络数据流图释义（Network Diagram Explained）

> 配套图：[network-diagram.svg](./network-diagram.svg) · [network-diagram-en.svg](./network-diagram-en.svg)
> 关联：[Technical Solution](./technical-solution.md) · [Architecture Schema Explained](./architecture-schema-explained.md)
> 视角：**自上而下的端到端数据流** —— 从外部数据源进入 → 经合规处理 → 落入三 Lake（🟫 Landing → 🔴 Raw PII → 🟢 Processed）→ 上溯到 AI 大脑 → 派发 Agent → 最终交付给客户门户

---

## 1. 阅读指南

### 1.1 整体结构

6 层水平 band，自上而下：

```
LAYER 1 · 外部数据源 (External Sources)
         ↓  ① Extract（数据采集）
LAYER 2 · ELT 八步管道
         ↓  ② Classify · Transform · Load（分类 + 变换 + 写入）
LAYER 3 · 三 Lake 仓库（🟫 Landing | 🔴 Raw PII | 🟢 Processed · Medallion）
         ↓  ③ PII-safe 上下文召回
LAYER 4 · Core AI Brain
         ↓  ④ Agent Orchestrate（编排）
LAYER 5 · 4 Pillar Agents
         ↓  ⑤ Deliver（结果交付）
LAYER 6 · 客户 / 门户
```

5 个**流向条**（圆角胶囊 + 3 个叠放箭头）放在相邻 band 之间，明确每段的关系与契约。

### 1.2 颜色语义

| 颜色       | 含义              | 出现位置                         |
| ---------- | ----------------- | -------------------------------- |
| 🟦 Sky     | 外部源 / 输入     | L1                               |
| 🟩 Emerald | ELT 数据管道      | L2 + ① 流向条                    |
| 🟪 Violet  | 仓库 / 持久化     | L3 + ② 流向条                    |
| 🟪 Pink    | AI Brain / Agents | L4 / L5 + ③④ 流向条              |
| 🟦 Sky     | 门户 / 用户层     | L6 + ⑤ 流向条                    |
| 🟥 Red     | PII / 隔离边界    | L3 中柱、Raw Lake、Validate 阶段 |
| 🟧 Amber   | 合规外圈          | 整图大框 + Compliance Banner     |

### 1.3 箭头与边线

| 元素                 | 含义                                    |
| -------------------- | --------------------------------------- |
| 实线箭头 + 灰        | 已匿名化的数据流                        |
| 实线箭头 + 红        | 含 PII / PHI 的受控数据流               |
| 实线箭头 + 粉        | AI 调用 / Agent 调度                    |
| 虚线 + 蓝            | 用户访问 / 门户回流                     |
| **粗红虚线（垂直）** | **PII Segregation Boundary**（L3 中柱） |
| **amber 虚线外圈**   | **Compliance Boundary**（整图）         |

---

## 2. 逐层名词与流程

### 2.1 LAYER 1 · 外部数据源（External Sources · 14 P1 集成）

按 4 类目分组：

| 类目                   | 集成       | 数据形态             | 业务用途                 |
| ---------------------- | ---------- | -------------------- | ------------------------ |
| **受众 / CRM**         | Experian   | 第三方人口画像       | 受众扩展（look-alike）   |
|                        | TransUnion | 信用 + 人口画像      | 受众扩展 + 风险分层      |
|                        | LiveRamp   | 身份解析 / IDR       | 跨设备身份打通           |
|                        | HubSpot    | CRM                  | 客户旅程                 |
| **媒介测量**           | Nielsen    | 曝光 / reach 测量    | 跨媒介 reach + frequency |
|                        | Placer IQ  | 线下人流量           | OOH 媒介归因             |
| **广告平台**           | DV360      | Google 程序化广告    | 投放执行 + 报告          |
|                        | Meta       | Facebook / Instagram | 投放执行 + 报告          |
|                        | TikTok     | TikTok Ads           | 投放执行 + 报告          |
|                        | Trade Desk | DSP 程序化           | 投放执行 + 报告          |
|                        | StackAdapt | DSP（中型代理偏好）  | 投放执行 + 报告          |
| **分析 / 倡导 / 传输** | GA4        | Google Analytics 4   | 网站行为                 |
|                        | Quorum     | 政治倡导 / 立法监控  | 政府关系类客户           |
|                        | Tresorit   | 端到端加密文件传输   | HIPAA 客户数据通道       |

"+More" 表示同类下还有可扩展位（roadmap）。

---

### 2.2 流向条 ① · Extract（数据采集）

L1 → L2，绿色条：

```
TLS 1.3 + OAuth · per-source Credential Vault · 14 P1 数据源
```

**关键名词**：

- **TLS 1.3** — 传输层加密协议，所有外部 API 调用必须走 HTTPS / TLS 1.3
- **OAuth** — 第三方授权协议（Meta / DV360 / GA4 等都使用）
- **Credential Vault** — 加密保险柜，per-tenant 隔离存储 OAuth Token / API Key / Service Account
- **per-source** — 每个数据源独立凭证，不共用

**流程**：调度器（Dagster OSS 或 Apache Airflow）按 schedule 触发对应 connector → 从 Vault 取凭证 → 经 TLS 调用外部 API 拉取数据 → 进入 L2 处理。

---

### 2.3 LAYER 2 · ELT 八步管道

**子标题**：`编排可选：Dagster OSS / Apache Airflow`

#### 2.3.1 第一行 4 个 Gate（数据入仓前的"门"）

| Gate                       | 解释                                                                |
| -------------------------- | ------------------------------------------------------------------- |
| 🔑 **Credential Vault**    | per-tenant 加密保险柜                                               |
| 🧭 **Classification Gate** | 自动识别 PII / PHI；命中则路由进 Raw Lake，否则进 Processed staging |
| ⚠ **Quarantine Queue**     | 校验失败的脏数据进入隔离队列，不污染主仓库                          |
| 📝 **Audit Log**           | Extract / Classify / Load / Transform 每步均写 INSERT-only 审计     |

#### 2.3.2 第二行 5 个变换阶段

| STEP | 名称                    | 解释                                                                           |
| ---- | ----------------------- | ------------------------------------------------------------------------------ |
| 1    | **Normalize**           | 字段标准化 — 14 个源的异构 schema 映射到 Canonical Schema（13 个统一实体）     |
| 2    | **Deduplicate**         | 跨平台 / 跨日去重 — 按业务键合并重复行                                         |
| 3    | **Validate**（🔴 红色） | Schema + 业务规则验证 + **PHI Detector 扫描**（HIPAA Safe Harbor 18 类标识符） |
| 4    | **Enrich**              | JOIN canonical 实体 + 第三方查询 + 特征工程                                    |
| 5    | **Index**               | 物化视图（marts 报表）+ pgvector 向量化（ai_context）                          |

> **ELT 八步 = Extract → Classify → Load + 上述 5 Transforms**。前 3 步由 Gate 行完成，后 5 步在仓库内由 dbt 模型完成。

#### 2.3.3 底部 ORCHESTRATION 横条（主调度二选一）

| 元素                      | 角色         | 解释                                                              |
| ------------------------- | ------------ | ----------------------------------------------------------------- |
| 🟪 **Dagster OSS**        | 主调度可选 A | 原生 Asset Graph 血缘、dagster-dbt 一等集成、per-Agency Partition |
| 🟦 **Apache Airflow**     | 主调度可选 B | 1000+ Provider 生态、团队普及、DAG 心智                           |
| 🟧 **AWS Step Functions** | 辅助调度     | 仅用于 AI 写回审批 + DSAR 长流程                                  |

详见 [ELT-ORCHESTRATION-PRIORITY](../ELT-ORCHESTRATION-PRIORITY.md)。

---

### 2.4 流向条 ② · Classify · Transform · Load

L2 → L3，紫色条：

```
raw_pii → Raw Lake（隔离） · staging/canonical → Processed Lake
```

**关键名词**：

- **raw_pii** — 仓库中 `raw_secure` schema 的表前缀，存放 PII 引用
- **staging / canonical** — Processed Lake 的 dbt schema 层级
- **Raw Lake / Processed Lake** — 两个物理隔离的数据湖（详见下节）

**流程**：Classification Gate 决定流向 — 含 PII 字段进 Raw Lake（红线），匿名化后的可分析数据进 Processed Lake（紫线）。两条线由 L3 中央的 **PII Segregation Boundary** 物理隔开。

---

### 2.5 LAYER 3 · 三 Lake 仓库（3-Lake Medallion on Neon Postgres）

**关键设计**：横向 3 个 Lake——🟫 **Landing**（左）→ 🔴 **Raw PII**（中）→ 🟢 **Processed**（右）。Landing 与 Raw PII 位于**同一 PII trust boundary**（软分隔，"同 PII zone"）；Raw PII 与 Processed 之间是**硬 PII Boundary**（粗红虚线 + 🔐）。L3 直接可视化了 PSD §3.6 的"原始数据 → 处理后业务数据"4 阶段生命周期：

- 🟫 **Landing Lake** 是 **STAGE 1 · LAND** 的物理落地点（整条 record 完整保留）
- 🔴 **Raw PII Lake** 是 **STAGE 3 派生 A** 的目标（仅 PII 字段）
- 🟢 **Processed Lake** 是 **STAGE 3 派生 B + STAGE 4 dbt** 的目标（非 PII 业务路径）
- STAGE 2 CLASSIFY 仅处理（读 Landing 输出 manifest，不落 Lake）

#### 2.5.1 左：🟫 Landing Lake (Bronze) · STAGE 1 LAND

**所有原始数据的完整着陆点**（图中显示为两张棕边卡片 + 砖块图标）：

| 表                         | 内容                                             | 关键约束                                                                                                      |
| -------------------------- | ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------- |
| `landing.<source>_records` | 整条 record · PII 列 Fernet 加密 · 非 PII 列明文 | **immutable** — 永不修改、永不覆盖、永不删除（除非 DSAR / 保留期到期）；含 `record_id` UUID + ingest_metadata |
| `landing.sync_state`       | 每 source 的 cursor / watermark / last_run_at    | 支撑增量续抓（详见 DEDUP ①）                                                                                  |

**⚠ 业务用户 / AI / dashboard / Pillar 完全禁读**——仅 ELT 服务账号 + 合规审计员可访问。保留 HIPAA 6y / 非 HIPAA 90d。**这是审计师追溯 "raw → report" 与 DSAR 主体定位、重处理、法律取证的源头副本**。

#### 2.5.2 软分隔：Landing ↔ Raw PII（"同 PII zone"）

Landing 与 Raw PII 位于**同一 PII trust boundary**——独立 KMS 各自密钥、独立 VPC subnet，但 ELT Worker 可在它们之间走 mTLS。视觉上用细虚线 + "同 PII zone" 标签，**不是硬隔离**（两者都受 PII 边界保护、有同等合规属性）。

#### 2.5.3 中：🔴 Raw PII-Segregated Lake · STAGE 3 派生 A

**从 Landing 派生的 PII 维表层**（仅持 PII 字段，不持整条 record）：

| 表                               | 内容                                                                                        |
| -------------------------------- | ------------------------------------------------------------------------------------------- |
| `raw_secure.users`               | 主体维表：`email_encrypted` + `email_hash` + `phone_encrypted` + `phone_hash` + `pii_token` |
| `raw_secure.<source>_pii_fields` | 源特定 PII 字段抽取（含 `record_id` 反查键，无非 PII 字段）                                 |
| `raw_secure.pii_access_log`      | PII Access Service 每次调用的行级审计                                                       |

是 **PII Access Service 的唯一明文出口源**。`pii_token = SHA-256(email_hash + agency_salt)` 是跨 Lake 关联的不可逆主键。

> 为什么必须保留 Landing + 拆分到 Raw PII？4 个场景需要：DSAR 主体定位（PII Access Service） · PII Detector 规则升级后重扫历史 · 业务 schema 变更后重跑 dbt · 审计师 "raw → report" 完整链路追溯。

#### 2.5.4 硬分隔：PII Segregation Boundary（粗红虚线 + 🔐 PII 徽章）

**整张图最关键的合规设计**——仅在 🔴 Raw PII 与 🟢 Processed 之间：

- 两侧使用**不同 Neon project**（独立 endpoint + 独立存储 + 独立 KMS）+ 独立 VPC subnet + mTLS 网络
- Processed Lake **永远拿不到明文 PII**
- 需要明文 PII 时走专门的 **PII Access Service**（purpose-bound · time-limited token · operation allow-list）— 详见 [PII-DESIGN-SOLUTION](../PII-DESIGN-SOLUTION.md)
- 跨 Lake 关联仅通过 `pii_token`（SHA-256 不可逆 hash）— 同 Agency 内 Processed 可与 Raw 关联，跨 Agency 因 salt 不同而无法关联

#### 2.5.5 右：🟢 Processed Lake · STAGE 3 派生 B + STAGE 4 TRANSFORM

**从 Landing 派生的非 PII 业务路径**（图中显示为 5 行向下流的紫边卡片）：

| 层                    | 内容                                                                                                                  | 保留期                  | 谁能读                              |
| --------------------- | --------------------------------------------------------------------------------------------------------------------- | ----------------------- | ----------------------------------- |
| **📥 raw.\<source\>** | 非 PII 原始字段 + `pii_token` + `record_id` + ingest_metadata（STAGE 3 派生 B 的写入目标，"非 PII 原始数据真实副本"） | HIPAA 6y / 非 HIPAA 90d | dbt · ELT 服务账号 · 业务 read-only |
| **📦 staging**        | dbt 标准化中间产物；字段命名 / 时间统一 / 去重                                                                        | 30 天                   | dbt · ELT 服务账号                  |
| **🧱 canonical**      | 13 个标准实体（campaign / persona / touchpoint 等）；跨 source 统一；以 `pii_token` JOIN 出 unified user 实体         | 3 年                    | 业务 / AI / 报表                    |
| **📊 marts**          | 业务报表聚合（campaign_perf / lead_funnel 等）；`pii_token` 大多已被 `GROUP BY` 聚合掉                                | 3 年 / 财务 7 年        | 业务 / AI / 报表 / 门户             |
| **🧠 ai_context**     | AI-safe 摘要 + pgvector 向量；脱敏到 segment 级别；**无 pii_token**                                                   | 1 年（按需刷新）        | Core AI Brain · Context Builder     |

**层间小箭头**：图中相邻层之间有小向下箭头，明示 dbt run 的数据流方向 `raw → staging → canonical → marts → ai_context`。

**关键属性**：

- 全 5 层 **永不含明文 PII** — 只有 `pii_token`（前 4 层）或聚合到 segment（最后一层）
- 来源都可追溯到 🟫 `landing.<source>_records`（通过 `record_id` 反查 + dbt lineage）
- 任一层重处理时可从 Landing 回放（idempotent）

#### 2.5.6 仓库标识（右上角）

🪨 **Neon Postgres** — 产品锁定的唯一仓库选型（serverless Postgres，per-Agency project，git-style Branching）。详见 [ADR-002](../ADR-002-NEON-TENANCY-OPTIMAL.md)。

---

### 2.6 流向条 ③ · PII-safe Context Retrieval

L3 → L4，粉色条：

```
AI 仅读 Processed Lake · 永不接触明文 PII · 经 PII Access Service 受控
```

**关键名词**：

- **PII-safe context** — 从 ai_context schema 召回的、已脱敏的 LLM 上下文
- **PII Access Service** — 需要明文 PII 的少数场景（如发邮件给客户）走的**受控出口**，purpose-bound token、time-limited、全程审计

**流程**：AI Brain 的 Context Builder 组件从 `processed.ai_context` schema 召回向量索引 + 标量上下文，**不直接读 Raw Lake**。

---

### 2.7 LAYER 4 · Core AI Brain（核心 AI 大脑）

并排 2 节点：

| 节点                        | 解释                                                                                         |
| --------------------------- | -------------------------------------------------------------------------------------------- |
| **LLM Router (OpenRouter)** | 统一 LLM 网关：模型路由（Opus / Sonnet / Haiku）+ 成本控制 + 合规边界（HIPAA → Bedrock BAA） |
| **Agent Orchestrator**      | 编排 4 个 Pillar Agent 的串/并联调用 + token 预算控制 + Langfuse 全链路追踪                  |

---

### 2.8 流向条 ④ · Agent Orchestrate

L4 → L5，粉色条：

```
LLM Router · Token 预算 · 串/并联 4 Agent · Langfuse 全链路追踪
```

**关键名词**：

- **Token 预算** — 每 Agency 月度 token 限额（`monthly_token_budget` 字段）
- **串/并联** — Persona/Creative/Attribution/Media Agent 之间可串行（Persona → Creative）或并行（同时跑 Attribution + Media）
- **Langfuse** — LLM 应用全链路可观测性平台（prompt / token / 成本 / 错误）

**流程**：Orchestrator 根据业务请求拆解为多个 Agent 任务 → 经 LLM Router 选模型 → 并/串调用 → 记录到 Langfuse。

---

### 2.9 LAYER 5 · 4 Pillar Agents

| Agent                 | 默认模型      | 职责                                      |
| --------------------- | ------------- | ----------------------------------------- |
| **Persona Agent**     | Claude Opus   | 受众画像构建（深度推理）                  |
| **Creative Agent**    | Claude Sonnet | 创意生成 + A/B 提案                       |
| **Attribution Agent** | Claude Sonnet | 跨渠道归因 / ROI 解释                     |
| **Media Agent ★**     | Claude Sonnet | 媒介采买优化（写回类，需 human approval） |

★ 标记 = 写回类 Agent，受 Step Functions 审批流保护。

---

### 2.10 流向条 ⑤ · Deliver

L5 → L6，蓝色条：

```
Persona / Creative / Attribution / Media 输出 → Agency · Client 门户
```

**流程**：Agent 输出（受众段、创意稿、归因报告、采买建议）→ 持久化到 marts / reports 表 → 通过 API + WebSocket 推送到门户。

---

### 2.11 LAYER 6 · 客户 / 门户

| 元素                        | 解释                                                       |
| --------------------------- | ---------------------------------------------------------- |
| **Agency Portal**           | Agency 工作台：管理本 Agency 下所有 Client / 数据源 / 报表 |
| **Client Portal**           | 白标门户：Client 仅看自己的数据（RLS 强制）                |
| **API Gateway**             | 程序化访问入口：JWT + scope token                          |
| **WebSocket Notifications** | 实时通知：Agent 完成 / 审批 / 报告就绪                     |

---

## 2.X 原始数据 → 业务数据库的全流程（4 阶段生命周期）

> 图中 L2（ELT 八步管道）+ L3（三 Lake 仓库）合起来构成 PSD §3.6 描述的完整 4 阶段生命周期。本节把图上的元素与 4 阶段一一对应，方便从图反查到 §3.6。

### 阶段对应图上位置

| 阶段                                | 在图中的位置                                                                                   | 关键产物                                          |
| ----------------------------------- | ---------------------------------------------------------------------------------------------- | ------------------------------------------------- |
| **STAGE 1 · LAND**（着陆）          | L3 左侧 Raw PII Lake 内 — 标题下方 "STAGE 1 · LAND" 标记 + 2 张红边表卡片                      | `raw_secure.<source>_raw` + `raw_secure.users`    |
| **STAGE 2 · CLASSIFY**（分类）      | L2 第一行 4 个 Gate 中的 **🧭 Classification Gate**                                            | classification_manifest（per-record × per-field） |
| **STAGE 3 · SPLIT**（分流写入）     | L2 → L3 的流向条 ②（"分类 + 变换写入"）+ 中柱 PII Boundary 红虚线                              | PII 字段留 Raw / 非 PII + pii_token → Processed   |
| **STAGE 4 · TRANSFORM**（dbt 4 层） | L3 右侧 Processed Lake 内 — 标题下方 "STAGE 4 · TRANSFORM" 标记 + 4 行紫边卡片（向下箭头连接） | staging → canonical → marts → ai_context          |

### 一条 Meta Ad Insight 的完整流转（与图中元素对应）

```
[1] L1 外部源 · Meta API
        ↓ ① 数据采集（流向条 ①）
[2] L2 ELT · 🔑 Vault → 🧭 Classification Gate → STEP 1-5
        ↓ ② 分类 + 变换写入（流向条 ②）
[3] L3 Raw PII Lake / Processed Lake
    ├─ 左：raw_secure.meta_ads_raw（明文 ad_id, campaign_id, ...
    │       + 加密 email_encrypted）         ← STAGE 1
    │      ↓ Classification Gate 计算 pii_token
    │      ↓ SPLIT
    └─ 右：Processed Lake（per-Agency Neon project）
           ↓ STAGE 4 dbt 4 层（图中向下箭头）
           📦 staging.stg_meta_ads（pii_token + 非 PII 字段，30d）
           🧱 canonical.touchpoint（JOIN unified user via pii_token，3y）
           📊 marts.campaign_perf（GROUP BY campaign_id，3-7y）
           🧠 ai_context.audience_summary（segment 级 + 向量，1y）
        ↓ ③ PII-safe Context Retrieval（流向条 ③）
[4] L4 Core AI Brain 读 ai_context
        ↓ ④ Agent Orchestrate
[5] L5 Pillar Agent 输出（Persona / Creative / Attribution / Media）
        ↓ ⑤ Deliver（流向条 ⑤）
[6] L6 门户呈现给 Agency / Client 用户
```

### 反向流：PII Access Service 路径（不经主数据链）

明文 PII 不沿上述主链路流出 Raw PII Lake。下游需要明文 PII 的场景（Meta CA 上传 / DSAR / LiveRamp / SMTP）走**独立路径**：

```
L3 Raw PII Lake.raw_secure.users
     ↓ 短期 purpose-bound token (≤15 min)
PII Access Service（in-memory 解密 → 即时变换）
     ↓ 直接出站，不经 Processed Lake / AI Brain / 业务日志
External API（Meta / DV360 / LiveRamp / SMTP）
```

详见 [PII-DESIGN-SOLUTION](../PII-DESIGN-SOLUTION.md)。

### 共享参考数据路径（B 类 · 旁路）

Experian / Nielsen / Placer IQ / Quorum 等 B 类共享参考数据走**第三条路径**——**Shared Reference Lake**（图中未单独画 band，但在 PSD §3.5 / §3.6 中定义）：

```
L1 External Source（平台 master credential）
   ↓ 单次摄取
[Shared Reference Lake · 平台级 Neon project]
   shared_experian / shared_nielsen / …
   ↓ FDW + license_grants RLS
[L3 各 Agency Processed Lake]
   shared.* schema（read-only mount）
```

详见 [TSD §3.5](./technical-solution.md#35-数据分类与共享参考数据策略tenant-scoping--shared-reference)。

---

## 3. 横切元素

### 3.1 Compliance Boundary（amber 虚线外圈）

整图外圈 amber 虚线 + 顶部 Banner：

```
🛡 COMPLIANCE BOUNDARY · GDPR · CCPA · HIPAA · SOC 2 · Per-Tenant Data Residency
```

含义：**合规是横切关注，所有 6 层共同遵守**。

### 3.2 加密标记

所有跨层数据流默认 **AES-256 静态加密 + TLS 1.3 传输加密**（Legend 标出）。

### 3.3 SSO 旁注

`Google OAuth（MVP）/ Office 365（Post-MVP）`

---

## 4. 端到端示例：一个完整请求

> 场景：Agency Operator 在门户中点击"为 Client X 生成下季度受众扩展报告"

| 步  | 在图中的位置                | 动作                                                                                |
| --- | --------------------------- | ----------------------------------------------------------------------------------- |
| 1   | L6 Agency Portal            | Operator 点击按钮，前端发 POST `/personas/expand`                                   |
| 2   | ⑤ 反向（用户请求方向）      | API Gateway 鉴权 + 注入 `agency_id`/`client_id`                                     |
| 3   | L4 Core AI Brain            | Agent Orchestrator 拆解：Persona Agent → 召回历史受众段，再调 Creative Agent 写描述 |
| 4   | ③ 反向（数据召回）          | Context Builder 从 `processed.ai_context` 召回 PII-safe 向量上下文                  |
| 5   | L3 Processed Lake           | 仅读 marts.persona / canonical.audience_segment（**不**碰 Raw Lake）                |
| 6   | L4 → ④                      | Orchestrator 选模型（Opus for Persona, Sonnet for Creative）+ 扣 token 预算         |
| 7   | L5 Persona / Creative Agent | LLM 输出存入 marts.persona_v_next                                                   |
| 8   | ⑤ Deliver                   | 结果通过 WebSocket 推回 L6 Portal，Operator 看到完成通知                            |
| 9   | 横切                        | 全程经 Langfuse 追踪、写 audit_events                                               |

---

## 5. 关联文档

- [Technical Solution](./technical-solution.md) — 技术方案文字版（完整 11 节）
- [Architecture Schema Explained](./architecture-schema-explained.md) — 架构方案图释义（姊妹文档）
- [ELT-ORCHESTRATION-PRIORITY](../ELT-ORCHESTRATION-PRIORITY.md) — Dagster vs Airflow 编排选型
- [ADR-002 Neon Tenancy](../ADR-002-NEON-TENANCY-OPTIMAL.md) — 多租户隔离决策
