# 架构方案图释义（Architecture Schema Explained）

> 配套图：[architecture-schema.svg](./architecture-schema.svg) · [architecture-schema-en.svg](./architecture-schema-en.svg)
> 关联：[Technical Solution](./technical-solution.md) · [Network Diagram Explained](./network-diagram-explained.md)
> 视角：**端到端平台架构视图** —— 7 层 + 右侧合规面板 + 底部关键技术约束。比网络图更全（含基础设施、可观测、合规面板）。

---

## 1. 阅读指南

### 1.1 整体结构

7 层水平 band + 右侧合规侧栏 + 底部约束条：

```
LAYER 1 · 客户 / 门户（4 User Types）
         ↓ ① User → Pillar
LAYER 2 · 功能 Pillars（MVP 5 大模块）
         ↓ ② Pillar → Core AI Brain
LAYER 3 · Core AI Brain（6 组件 + 4 Agent）
         ↓ ③ AI 触发 ELT / 召回数据
LAYER 4 · ELT 转换管道（5 阶段 + Dagster/Airflow 编排）
         ↓ ④ ELT 写入仓库
LAYER 5 · 三 Lake 仓库（🟫 Landing | 🔴 Raw PII | 🟢 Processed · Medallion on Neon）
         ⇡ ⑤ 仓库 ← 数据采集（注意方向：L6 → L5）
LAYER 6 · 外部数据源（14 P1 集成）
         ↓ ⑥ 全栈运行于基础设施
LAYER 7 · 基础设施（Compute · Observability · Secrets · CI/CD）

[右侧] Compliance Panel：合规 4 法规 + 12 核心能力（横线连接每一层）
[底部] KEY CONSTRAINTS：6 项关键技术约束
```

6 个**流向条**放在 band 间，明确每对相邻层的关系。⑤ 是**向上箭头**，因为采集方向是 L6 → L5（数据从源进入仓库）。

### 1.2 与网络图的差异

| 视角 | 网络数据流图                        | 架构方案图                                       |
| ---- | ----------------------------------- | ------------------------------------------------ |
| 主线 | 严格"自上而下数据流"                | "组件分层视图"                                   |
| 顺序 | 源 → ELT → 仓库 → AI → Agent → 门户 | 门户 → Pillars → AI → ELT → 仓库 → 源 → 基础设施 |
| 范围 | 只画数据/AI 主链                    | 加上基础设施、合规面板、约束条                   |
| 流向 | 5 条向下流向条                      | 6 条流向条（含 1 条反向上箭头 + 1 条横切）       |

> **要点**：架构方案图是"分层视图"——同一份系统从用户视角自上而下看的层级，**不是严格的数据时序**。流向条上的方向箭头表示**主请求/控制方向**或**关系方向**。

### 1.3 颜色语义

| 颜色      | 含义              | 层                    |
| --------- | ----------------- | --------------------- |
| 🟦 Sky    | 用户 / 门户       | L1                    |
| 🟦 Cyan   | 功能 Pillars      | L2                    |
| 🟪 Pink   | AI Brain / Agents | L3                    |
| 🟦 Blue   | ELT 转换          | L4                    |
| 🟪 Violet | 仓库              | L5                    |
| 🟦 Sky    | 外部源            | L6                    |
| 🟥 Red    | 基础设施          | L7                    |
| 🟧 Amber  | 合规面板 / 横切   | 右侧 spine + 流向条 ⑥ |

---

## 2. 逐层名词与流程

### 2.1 LAYER 1 · 客户 / 门户（Client / Portal · 4 User Types）

4 类用户角色（**3 级权限层级**）：

| 用户类型                 | 层级 | 解释                                                |
| ------------------------ | ---- | --------------------------------------------------- |
| **Platform Super Admin** | L1   | 平台总管理员，跨 Agency 聚合做 benchmarking         |
| **Agency Admin**         | L2   | Agency 管理员，管理本 Agency 下所有 Client + 数据源 |
| **Agency Operator**      | L2   | Agency 日常操作员（投放/创意/报告）                 |
| **Client Viewer**        | L3   | 客户端用户，**RLS 强制只看本 Client 数据**          |

**白标**：每个 Agency 可定制 logo / 主题色，Client 看不到平台品牌。

---

### 2.2 流向条 ① · User → Pillar

L1 → L2，青色条：

```
Agency / Client 用户在门户中触发 5 大业务模块
```

**关键名词**：

- **触发** — 用户在 UI 点击按钮 / 提交表单 → 前端调 REST API → 后端路由到对应 Pillar 服务
- **RLS 注入** — 每次请求自动注入 `agency_id` 和 `client_id`（Client Viewer 角色）作为查询过滤条件

---

### 2.3 LAYER 2 · 功能 Pillars（MVP 5 大业务模块）

| Pillar              | 解释                                     |
| ------------------- | ---------------------------------------- |
| **Market Research** | 受众画像 + 市场洞察（调 Persona Agent）  |
| **Creative Engine** | 创意生成 + A/B（调 Creative Agent）      |
| **Media Buying**    | 跨平台投放采买优化（调 Media Agent）     |
| **Attribution**     | 跨渠道归因 / ROI（调 Attribution Agent） |
| **Client Portal**   | 客户成果消费界面（聚合上述四者输出）     |

每个 Pillar 是一组 FastAPI 端点 + 后台任务，**不直接调用 LLM**——所有 AI 能力必经 Core AI Brain。

---

### 2.4 流向条 ② · Pillar → Core AI Brain

L2 → L3，粉色条：

```
5 Pillars 通过统一编排层调用 6 组件 + 4 Agent
```

**关键名词**：

- **统一编排层** — 即 Core AI Brain，是平台唯一的 LLM 出入口
- **6 组件** — Context Builder · LLM Router · Agent Orchestrator · Tool Executor · Memory & Retrieval · Audit & Cost

**为什么不直连 LLM**：

1. **合规可追溯** — 集中审计 prompt / token / 成本
2. **模型可替换** — Pillar 不依赖具体模型
3. **PII-safe** — 上下文组装时统一脱敏

---

### 2.5 LAYER 3 · Core AI Brain（6 组件 + 4 Agent）

**上行：6 大核心组件**

| 组件                   | 解释                                                 |
| ---------------------- | ---------------------------------------------------- |
| **Context Builder**    | 从仓库收集 tenant-safe / role-safe / PII-safe 上下文 |
| **LLM Router**         | 按 agent / 成本 / 延迟 / 合规 / 租户策略选模型       |
| **Agent Orchestrator** | 协调 4 个 Pillar Agent，串/并联                      |
| **Tool Executor**      | 调用受批准的读 / 写工具；写操作经审批门              |
| **Memory · Retrieval** | summary 上下文 + pgvector 向量召回                   |
| **Audit · Cost**       | Prompt / token / 成本 / 审计全记录                   |

**下行：4 Pillar Agent** —— Persona / Creative / Attribution / Media ★（同网络图 §2.9）

---

### 2.6 流向条 ③ · AI 触发 ELT / 召回数据

L3 → L4，蓝色条：

```
Agent 通过 Tool Executor 调用 ELT 增量计算 + 仓库读取
```

**关键名词**：

- **Tool Executor** — Core AI Brain 中负责调用外部能力的组件（数据库读、写、调 ELT 任务、调第三方 API）
- **增量计算** — Agent 可触发"只重算最近 7 天数据"而非全量 backfill
- **审批门** — Media Agent 的写回操作必须 human approve 才能调 Step Functions 审批流

**流程**：Agent 想要 fresh 数据 → Tool Executor 触发 Dagster/Airflow 的 ELT 任务 → 完成后从仓库读结果。

---

### 2.7 LAYER 4 · ELT 转换管道（5 in-warehouse stages）

#### 2.7.1 顶部 ORCHESTRATION 横条

| 元素                      | 角色         | 解释                                             |
| ------------------------- | ------------ | ------------------------------------------------ |
| 🟪 **Dagster OSS**        | 主调度可选 A | Asset Graph · dagster-dbt · per-Agency Partition |
| 🟦 **Apache Airflow**     | 主调度可选 B | 1000+ Provider · 团队普及                        |
| 🟧 **AWS Step Functions** | 辅助         | AI 写回审批 · DSAR 长流程                        |

#### 2.7.2 5 STEP 转换阶段

| STEP | 阶段               | 解释                             |
| ---- | ------------------ | -------------------------------- |
| 1    | **Normalize**      | 字段标准化（dbt staging models） |
| 2    | **Deduplicate**    | 跨平台去重                       |
| 3    | **Validate**（🔴） | PHI 扫描 + Schema 验证           |
| 4    | **Enrich**         | JOIN + 第三方查询                |
| 5    | **Index**          | 物化视图 + pgvector              |

> 注：Extract / Classify / Load 在上游（L6 → L4 之间，由 connector 完成），本层只展示**仓库内** 5 个 Transform。

---

### 2.8 流向条 ④ · ELT 写入仓库 Write

L4 → L5，紫色条：

```
Normalize → Dedup → Validate → Enrich → Index → marts / ai_context
```

**关键名词**：

- **marts** — Processed Lake 的报表层 schema（业务直接消费）
- **ai_context** — Processed Lake 的 AI 召回层 schema（向量 + 摘要）

**流程**：ELT 输出按 schema 分发——marts 给报表/门户，ai_context 给 AI Brain。

---

### 2.9 LAYER 5 · 三 Lake 仓库（3-Lake Medallion on Neon Postgres）

**子标题**：`🟫 Landing → 🔴 Raw PII → 🟢 Processed`

L5 横向三 Lake 布局（左中右），上方 PII trust boundary 内的 Landing 与 Raw PII 之间用**软分隔**（"同 PII zone"），Raw PII 与 Processed Lake 之间用**硬 PII Boundary**（粗红虚线 + 🔐）。

#### 2.9.1 左：🟫 Landing Lake (Bronze)（砖块图标）

**所有原始数据的完整着陆点**——STAGE 1 的写入目标。

2 张关键表：

- 📦 `landing.<source>_records` — 整条 record · PII 列加密 · 非 PII 列明文 · immutable
- 🔖 `landing.sync_state` — cursor / watermark 状态（增量续抓）

**⚠ 业务/AI 完全禁读**。仅 ELT 服务账号 + 合规审计员可访问。保留期 HIPAA 6y / 非 HIPAA 90d。重处理 / DSAR / 法律取证的源头副本。

#### 2.9.2 软分隔：Landing ↔ Raw PII（"同 PII zone"）

两者位于**同一 PII trust boundary**——独立 KMS 各自的密钥、独立 VPC subnet，但 ELT Worker 可在它们之间走 mTLS。视觉上用细虚线 + "同 PII zone" 标签，不是硬隔离。

#### 2.9.3 中：🔴 Raw PII-Segregated Lake（🔒）

**从 Landing 派生的 PII 维表层**——STAGE 3 派生 A 的写入目标。

3 张表：

- 👤 `raw_secure.users` — 主体维表（email_encrypted / phone_encrypted / hashes / pii_token）
- 📇 `raw_secure.<source>_pii_fields` — 源 PII 字段抽取（含 record_id 反查键，无非 PII 字段）
- 📝 `raw_secure.pii_access_log` — PII Access Service 每次调用的行级审计

**⚠ 仅持 PII 字段**——非 PII 字段从不进此 Lake；整条 record 在 Landing。

#### 2.9.4 硬分隔：PII BOUNDARY（粗红虚线 + 🔐）

仅在 Raw PII Lake 与 Processed Lake 之间。不同 Neon project + 独立 KMS + 独立 VPC + mTLS 网络隔离 + DLP 持续扫描。

#### 2.9.5 右：🟢 Processed Lake（✓）

**从 Landing 派生的非 PII 业务路径**——STAGE 3 派生 B + STAGE 4 dbt 4 层的写入目标。

5 个层级（横向流，含小箭头）：

- 📥 `raw.<source>` — 非 PII 原始 + pii_token（STAGE 1 的非 PII 副本）
- 📦 `staging` — dbt 标准化中间产物 · 30d
- 🧱 `canonical` — 13 个标准实体 · 3y
- 📊 `marts` — 业务报表聚合 · 3-7y
- 🧠 `ai_context` — AI 召回向量 + 摘要 · 1y

**✓ 完全无明文 PII**——仅持 `pii_token` 不可逆 hash。业务 / AI / 报表 / 门户均可读。

右上角图标：**Neon Postgres** —— 产品锁定仓库选型（serverless · per-Agency project）。

#### 2.9.6 L5 下半部分 · 数据完整生命周期流程带（DATA LIFECYCLE）

L5 band 的**下半部分**（约 200px 高）是一条专门用于展示数据全流程的**大型流程带**，外圈为 amber 虚线大框，标题 "▸ 数据完整生命周期 · DATA LIFECYCLE"。它**与上方的三 Lake 通过彩色虚线连接**：

- 🟥 **红色虚线** 从 Raw PII Lake 底部 → 流程带顶部，标注 "PII 字段加密落盘 ↓"
- 🟪 **紫色虚线** 从 Processed Lake 底部 → 流程带顶部，标注 "非 PII + pii_token 写入 ↓"

流程带内部从左到右是 **4 个 STAGE 大卡片 + 3 个粗实线箭头**：

| STAGE                                     | 颜色框        | 内部条目                                                                                             | 脚注                                                                             |
| ----------------------------------------- | ------------- | ---------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| **STAGE 1 · LAND**（原始数据着陆）        | 🟥 红         | `raw_secure.<source>_raw`（整条原始 record · PII 加密）· `raw_secure.users`（email_enc + pii_token） | immutable · 支撑 DSAR / 重处理                                                   |
| **STAGE 2 · CLASSIFY**（PII/PHI 分类）    | 🟦 蓝         | PHI Detector（HIPAA 18-id 扫描）· PII Classifier（L0/L1/L2/L3 打标签）                               | 输出 classification_manifest                                                     |
| **STAGE 3 · SPLIT**（PII 边界分流）       | 🟧 橙         | PII 字段（留 Raw PII Lake）· 非 PII + pii_token（→ Processed.staging）                               | pii_token = SHA-256(email_hash + agency_salt)                                    |
| **STAGE 4 · TRANSFORM**（dbt 4 层流水线） | 🟪 紫（更宽） | 内部含 4 个 sub-layer 子卡片，详见下表                                                               | audit schema 横切伴随 · INSERT-only 6 年 · DSAR / 重处理 / 审计可沿 lineage 回溯 |

**STAGE 4 内部 4 个 sub-layer**（横向流，3 个细右向箭头连接）：

| Sub-layer         | 颜色    | 内容                                                  | 保留期 |
| ----------------- | ------- | ----------------------------------------------------- | ------ |
| 📦 **staging**    | 🟦 青   | 非 PII + pii_token 中间产物                           | 30d    |
| 🧱 **canonical**  | 🟪 紫   | 13 个 Canonical Entities                              | 3y     |
| 📊 **marts**      | 🟪 淡紫 | 业务报表聚合 · 面向 dashboard/API/Pillar              | 3-7y   |
| 🧠 **ai_context** | 🟪 粉   | AI-safe 摘要 + pgvector 向量 · Context Builder 召回源 | 1y     |

#### 2.9.5 各 STAGE 输出落到哪个 Lake（明确归属）

**关键问题：数据完整生命周期 4 个 STAGE 中，哪些属于 Raw PII Lake？** 答：**只有 STAGE 3 写 Raw PII Lake**（且仅写 PII 字段）。其他全在 Processed Lake 或仅是处理过程。

| STAGE                                          | 是否落 Lake | 🔴 Raw PII Lake 写入                                                                   | 🟢 Processed Lake 写入                                      | 🚦 仅处理（不落盘）                                 |
| ---------------------------------------------- | ----------- | -------------------------------------------------------------------------------------- | ----------------------------------------------------------- | --------------------------------------------------- |
| **STAGE 1 LAND**（外部 API → 解析 → 等待分流） | 否          | —                                                                                      | —                                                           | ✓ 解析 + 生成 record_id；整条 record 仅在内存事务中 |
| **STAGE 2 CLASSIFY**（字段分级打标签）         | 否          | —                                                                                      | —                                                           | ✓ 输出 field_classification_manifest（不落仓库）    |
| **STAGE 3 SPLIT**（按字段原子双写）            | **是**      | ✅ `raw_secure.users` · `raw_secure.<source>_pii_fields` · `raw_secure.pii_access_log` | ✅ `processed.raw.<source>_records`                         | —                                                   |
| **STAGE 4 TRANSFORM**（dbt 5 层）              | **是**      | —                                                                                      | ✅ `staging.*` → `canonical.*` → `marts.*` → `ai_context.*` | —                                                   |

**所以"Raw PII Lake 里到底放了什么"**：

- 🔴 `raw_secure.users` — 主体维表（email_encrypted / phone_encrypted / hashes / pii_token）
- 🔴 `raw_secure.<source>_pii_fields` — 源特定 PII 字段抽取（含 record_id 反查键）
- 🔴 `raw_secure.pii_access_log` — PII Access Service 每次调用的行级审计

**Raw PII Lake 永远不放**：整条原始 record · campaign_id / impressions / clicks 等非 PII 业务字段 · ingest_metadata · audit_events · staging/canonical/marts/ai_context 任何层。

#### 2.9.6 DEDUP ① "增量续抓 Cursor"是什么意思

**Cursor**（游标）= ELT 调度记录"**上次拉到哪一条 / 哪个时间点**"的位置标记。下次再跑时**从 cursor 之后续抓**，不重头拉。

**例子**：

```
首次拉 Meta API：拿到 1000 条（id 1~1000）
  → 写入仓库
  → sync_state 记录: last_cursor = "2026-05-18T14:30:00Z"

1 小时后再跑：
  → 读 sync_state 取 last_cursor
  → 调 Meta API: "给我 2026-05-18T14:30:00 之后的数据"
  → 拿到新增 50 条 (id 1001~1050)
  → 写入仓库（id 1~1000 完全不被重抓）
  → sync_state 更新: last_cursor = "2026-05-18T15:30:00Z"
```

**没有 Cursor 的话**：每次都从头抓 → 同一条 record 被写入 N 次 → 重复数据爆炸。

业内同义词：**Incremental Sync** · **Watermark Extraction** · **Delta Loading**。

DEDUP 横条另外 4 个机制是 cursor 的兜底（防止 cursor 失效或被绕过时仍有保护）：

- ② **内容指纹去重** — 每条 record 算 `SHA-256(canonical_fields)`，仓库表上 `UNIQUE(record_hash)` 强制不接重复
- ③ **MERGE Upsert** — dbt 用 `MERGE ... ON business_key`（不是 `INSERT`），同一 campaign 5 次拉取只保留 1 条
- ④ **固定刷新周期** — B 类共享数据按供应商周期 / A 类同源 5min 内不重复触发
- ⑤ **行数审计** — 每批 ingest 记 `(new_count, skipped_count)`，可证明无重复

---

### 2.10 流向条 ⑤ · 仓库 ⇡ 数据采集（反向上箭头）

L5 ↑ L6，蓝色条 + **向上箭头**：

```
ELT 反向拉取 14 P1 外部数据源（采集方向为 L6 → L5）
```

**为什么是向上箭头**：在分层视图中，外部源被放在仓库**下方**（L6），但数据流方向是 L6 → L5（源进入仓库）。向上箭头明确这一**关系方向**，避免误读。

---

### 2.11 LAYER 6 · 外部数据源（14 P1 集成）

同网络图 §2.1，按 6 个类目分组：

- **Audience / CRM**：Experian · TransUnion · LiveRamp · HubSpot
- **Measurement**：Nielsen · Placer IQ
- **Ad Platforms**：DV360 · Meta · TikTok · Trade Desk · StackAdapt
- **Analytics**：GA4
- **Advocacy**：Quorum
- **Compliant CRM**：Tresorit

---

### 2.12 流向条 ⑥ · 全栈运行于基础设施 Runs On

L6 → L7，红色条：

```
Compute · Observability · Secrets · CI/CD 横切支撑 L1-L6
```

**关键名词**：横切（cross-cutting）—— 基础设施服务整个栈，而非只服务 L6。

---

### 2.13 LAYER 7 · 基础设施（Infrastructure · Cross-Cutting）

| 元素            | 解释                                    |
| --------------- | --------------------------------------- |
| **Render PaaS** | 生产计算平台（multi-region，BAA 支持）  |
| **Coolify**     | 开发环境计算（self-host PaaS）          |
| **Langfuse**    | LLM 全链路追踪（prompt / token / 成本） |
| **Sentry**      | 错误监控 / 异常告警                     |
| **AWS KMS**     | 密钥管理服务（per-Agency 独立密钥）     |
| **GitHub**      | 源码 + CI/CD 流水线                     |

---

## 2.X 原始数据 → 业务数据库的全流程（4 阶段生命周期）

> 架构示意图的 **L4（ELT）+ L5（三 Lake）** 合起来覆盖 PSD §3.6 描述的完整 4 阶段生命周期。本节把架构图上的元素与 4 阶段一一对应。

### 4 阶段在架构示意图上的位置

| 阶段                                | 在图中的位置                                                                              | 关键产物                                                        |
| ----------------------------------- | ----------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| **STAGE 1 · LAND**（着陆）          | L5 底部 6-schemas 横条最左端 — **raw_secure** 红框                                        | `raw_secure.<source>_raw` + `raw_secure.users`（PII 加密落盘）  |
| **STAGE 2 · CLASSIFY**（分类）      | L4 顶部 ORCHESTRATION 横条下方的 STEP 3 **Validate**（红色多边形，含"PHI 扫描 + Schema"） | classification_manifest（per-record × per-field）               |
| **STAGE 3 · SPLIT**（分流写入）     | L4 → L5 流向条 ④（"ELT 写入仓库 Write"）+ L5 中柱 PII Boundary 红虚线                     | PII 字段留 Raw Lake / 非 PII + pii_token → Processed Lake       |
| **STAGE 4 · TRANSFORM**（dbt 4 层） | L5 底部横条中 4 个 schema 之间的**右向小箭头**（图中已加）                                | `raw_secure ──► staging ──► canonical ──► marts ──► ai_context` |
| **横切 · AUDIT**                    | L5 底部横条最右端的 **audit**（amber），通过 spine 连接到所有层                           | INSERT-only audit_events，6 年保留                              |

### L5 底部 schema 横条 = 4 阶段的可视化压缩

```
[L5 底部 schema 条 · 自左向右]

  raw_secure  ─►  staging  ─►  canonical  ─►  marts  ─►  ai_context     │ audit
   🟥红           🟦蓝          🟪紫          🟪紫        🟪粉           │ 🟧amber
   STAGE 1       STAGE 4.1     STAGE 4.2     STAGE 4.3   STAGE 4.4      │ 横切
   LAND          源标准化       统一实体       业务报表    AI 召回         │ 全程审计
   90d/6y        30d           3y            3-7y       1y              │ 6y
```

**4 个右向箭头**（图中实际渲染）依次表示：

1. `raw_secure → staging`：经 STAGE 2 Classification Gate 拆出非 PII 字段 + 计算 `pii_token`
2. `staging → canonical`：跨 14 个 source 映射到 13 个 Canonical Entities
3. `canonical → marts`：聚合到面向 dashboard / API / Pillar 的业务报表
4. `marts → ai_context`：抽取摘要 + 生成 pgvector 向量索引（给 Core AI Brain 召回）

**audit** schema 单独存在于横条最右——**不在主链路上**，但通过 spine 与所有 7 层连接，记录前 5 个 schema 的所有访问与变更。

### 与 L4 ELT 5 阶段的对应

L4 中 5 个箭头形状的 STEP 是 **STAGE 4 dbt TRANSFORM** 内部的 5 个步骤；它们在 dbt 中以**模型类型**呈现：

| L4 STEP                | dbt 实现                                | 输出落到 L5 哪层                            |
| ---------------------- | --------------------------------------- | ------------------------------------------- |
| STEP 1 **Normalize**   | staging dbt models                      | `staging.stg_<source>`                      |
| STEP 2 **Deduplicate** | staging incremental models              | `staging.stg_<source>`（uniq business key） |
| STEP 3 **Validate**    | dbt tests + asset checks + PHI Detector | classification_manifest                     |
| STEP 4 **Enrich**      | intermediate + canonical dbt models     | `canonical.<entity>`                        |
| STEP 5 **Index**       | mart dbt models + Python post-hook      | `marts.*` + `ai_context.*`（含 pgvector）   |

### 三条数据进入仓库的路径（A / B / C 类）

| 路径                    | 数据例子                                | 落到哪                                                                                                                                                                      |
| ----------------------- | --------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **A. Tenant-Private**   | Meta / GA4 / HubSpot 等                 | per-Agency Neon project 的 raw_secure → staging → canonical → marts → ai_context                                                                                            |
| **B. Shared Reference** | Experian / Nielsen / Placer IQ / Quorum | 平台级 Shared Reference Lake（独立 Neon project，未在图上独立画 band，按 §3.5 设计）→ 通过 FDW read-only 映射进每个有 license 的 Agency 的 Processed Lake `shared.*` schema |
| **C. Tenant-Derived**   | Agency 把 A 与 B JOIN 后的衍生结果      | 写回该 Agency 的 marts                                                                                                                                                      |

详见 [TSD §3.5](./technical-solution.md#35-数据分类与共享参考数据策略tenant-scoping--shared-reference) 与 [§3.6](./technical-solution.md#36-原始数据生命周期与处理后分区raw-data-lifecycle--post-processing-division)。

### 反向流：PII Access Service（不沿主数据链）

明文 PII 不沿 STAGE 1→4 的主链路出 Raw PII Lake。Pillar 需要明文 PII 的 13 个场景（Meta CA / DV360 / TikTok / TTD / StackAdapt 受众上传 · LiveRamp 解析 · DSAR locate/export · CCPA Opt-Out · 法律 export · SMTP/SMS 通知）走**独立路径**：

```
L5 Raw PII Lake.raw_secure.users
       ↓ purpose-bound token (≤15 min)
PII Access Service（in-memory 解密 + 即时变换）
       ↓ 直接出站，不经 Processed Lake / AI Brain / 业务日志
External API（Meta / DV360 / LiveRamp / SMTP / DSAR 邮件）
```

详见 [PII-DESIGN-SOLUTION](../PII-DESIGN-SOLUTION.md)。

---

## 3. 右侧 Compliance Panel（合规侧栏）

通过 spine（纵线）+ 横向虚线锚点连接 7 层，表示**合规是横切关注**。

### 3.1 上卡片：COMPLIANCE

| 项            | 解释                                                |
| ------------- | --------------------------------------------------- |
| **GDPR**      | EU 通用数据保护条例 · DSAR 30 天 · 违规 72 小时通知 |
| **CCPA**      | 加州消费者隐私法 · DSAR 45 天                       |
| **HIPAA**     | 美国医疗隐私法 · 违规 60 天通知 · 需签 BAA          |
| **SOC 2**     | Type II 审计 · 5 项 Trust Service Principles        |
| **Residency** | Per-Tenant Region 数据驻留                          |

### 3.2 下卡片：核心能力（12 项）

| 能力                            | 解释                          |
| ------------------------------- | ----------------------------- |
| **PHI Detector · 18-id 扫描**   | HIPAA Safe Harbor 18 类标识符 |
| **Anonymizer · SHA-256 + salt** | 不可逆哈希匿名化              |
| **Agency Salt 隔离**            | 每 Agency 独立盐值            |
| **IP 截断 (v4/24 · v6/48)**     | IPv4 → /24，IPv6 → /48        |
| **Fernet 字段加密**             | 字段级对称加密                |
| **Audit Log · 6y INSERT-only**  | 6 年不可篡改                  |
| **DSAR (30 / 45 / 30 d)**       | GDPR / CCPA / HIPAA SLA       |
| **Retention 引擎**              | 自动按法规过期清理            |
| **Breach 通知 (72h / 60d)**     | GDPR / HIPAA 告警             |
| **BAA 状态追踪**                | HIPAA 客户协议状态            |
| **密钥轮换 per-Agency**         | 独立 KMS + 定期轮换           |
| **数据驻留 DLP 检查器**         | 防跨 region 泄漏              |

---

## 4. 底部 KEY CONSTRAINTS（6 项关键技术约束）

| 约束             | 解释                                                         |
| ---------------- | ------------------------------------------------------------ |
| **Residency**    | Per-tenant region；跨 region 禁止                            |
| **Encryption**   | AES-256 静态 · TLS 1.3 传输 · per-tenant KMS                 |
| **Auth**         | MVP: JWT + Google OAuth · Post-MVP: Office 365               |
| **LLM Routing**  | OpenRouter 默认 · HIPAA → Bedrock BAA                        |
| **Audit**        | INSERT-only · HIPAA 6 年 · 财务 7 年                         |
| **Multi-Tenant** | 物理：per-tenant Neon project + KMS；RLS 作 defense-in-depth |

---

## 5. 端到端示例：一个完整 Pillar 调用链

> 场景：Agency Operator 在 Creative Engine 中点击"为 Campaign Y 生成 5 个素材变体"

| 步  | 层 / 流向条    | 动作                                                                        |
| --- | -------------- | --------------------------------------------------------------------------- |
| 1   | L1 → ① → L2    | Operator 在 Creative Engine UI 提交，路由到 `/creative/generate`            |
| 2   | L2 → ② → L3    | Creative Engine 调 Core AI Brain，传入 campaign_id + brand_guidelines       |
| 3   | L3 内          | Context Builder 召回 brand voice / 过往 A/B 结果（PII-safe）                |
| 4   | L3 → ③ → L4    | Tool Executor 触发 Dagster 增量重算（如最近 7 天的 audience persona）       |
| 5   | L4 → ④ → L5    | ELT 运行 5 STEP，写回 marts.persona / ai_context.embeddings                 |
| 6   | L5 → 反向 → L3 | Context Builder 召回 fresh embeddings                                       |
| 7   | L3 内          | LLM Router 选 Claude Sonnet（Creative Agent 默认模型），扣 token 预算       |
| 8   | L3 → L2 → L1   | 5 个素材变体返回 Creative Engine，渲染到 UI                                 |
| 9   | 全程           | 横切：Langfuse 追踪 · audit_events 记录 · 合规检查在 spine 连接的所有层执行 |
| 10  | 基础设施       | L7：Render PaaS 跑后端 · AWS KMS 提供密钥 · Sentry 监控错误                 |

---

## 6. 关联文档

- [Network Diagram Explained](./network-diagram-explained.md) — 网络数据流图释义（姊妹文档）
- [Technical Solution](./technical-solution.md) — 技术方案文字版（完整 11 节）
- [ADR-002 Neon Tenancy](../ADR-002-NEON-TENANCY-OPTIMAL.md) — 多租户隔离决策
- [ELT-ORCHESTRATION-PRIORITY](../ELT-ORCHESTRATION-PRIORITY.md) — Dagster vs Airflow 编排选型
- [PSD-LLM-SELECTION-DECISION](../PSD-LLM-SELECTION-DECISION.md) — LLM 选型决策
