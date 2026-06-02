# PSD 架构图释义 · 网络架构图 + 架构方案图

> 状态：术语 / 元素 / 颜色释义 · 与 [Network Diagram](./network-diagram.svg) · [Architecture Schema](./architecture-schema.svg) · [Technical Solution](./technical-solution.md) 配套
> 用途：把图中每个词、每个色块、每条线都解释清楚，方便客户 / 投资人 / 新加入工程师快速读懂

---

## 0. 阅读指南：通用视觉约定

### 0.1 配色语义（两图统一）

| 颜色          | 十六进制  | 语义                   | 出现位置                         |
| ------------- | --------- | ---------------------- | -------------------------------- |
| 🟦 Sky / Cyan | `#0EA5E9` | 外部源 / 输入          | L1 外部数据源                    |
| 🟩 Emerald    | `#10B981` | ELT 数据管道 / 转换    | ELT 八步 / 5 个转换阶段          |
| 🟪 Violet     | `#8B5CF6` | 仓库 / 持久化          | Two-Lake / Processed Lake        |
| 🟥 Red        | `#EF4444` | PII / PHI / 隔离边界   | Raw PII Lake · PII Boundary      |
| 🟧 Amber      | `#F59E0B` | 合规 / 审批 / 横切     | Compliance 面板 · Step Functions |
| 🟪 Indigo     | `#4F43DC` | 编排器（Dagster OSS）  | L4 / L2 顶部 ORCHESTRATION 条    |
| 🟪 Pink       | `#EC4899` | AI Brain / Agents      | Core AI Brain · 4 Pillar Agents  |
| ⬜ Slate      | `#94A3B8` | 加密 / 审计 / 中性辅助 | 数据加密箭头 · Audit             |

### 0.2 边线语义（网络图）

| 线型                  | 含义                                         |
| --------------------- | -------------------------------------------- |
| 实线箭头 + 灰色       | 普通数据流（已匿名化）                       |
| 实线箭头 + 红色       | 含 PII / PHI 的受控数据流                    |
| 实线箭头 + 粉色       | AI 调用（LLM / Agent）                       |
| 虚线箭头 + 蓝色       | 用户访问流（门户/API）                       |
| 粗虚线 + 红色（垂直） | **PII Segregation Boundary**（PII 隔离边界） |
| 整图外圈 amber 虚线   | **Compliance Boundary**（合规外圈）          |

### 0.3 加密标记

任何跨层的数据流箭头默认 **AES-256 静态加密 + TLS 1.3 传输加密**（在 Legend 中以浅灰色样例标出）。

---

## 1. 网络数据流图（Network Diagram）

> 共 6 层 horizontal band。自上而下：**外部源 → ELT → Two-Lake → Core AI Brain → Pillar Agents → 客户门户**。

### 1.1 LAYER 1 · 外部数据源（External Sources / 14 个 Priority-1 集成）

按业务类目分 4 组。每个 chip = 一个第三方平台。

| 类目               | 集成           | 数据形态             | 用途                         |
| ------------------ | -------------- | -------------------- | ---------------------------- |
| 受众 / CRM         | **Experian**   | 第三方人口画像       | 受众扩展（look-alike）       |
|                    | **TransUnion** | 信用 + 人口画像      | 受众扩展 + 风险分层          |
|                    | **LiveRamp**   | 身份解析 / IDR       | 跨设备身份打通               |
|                    | **HubSpot**    | CRM                  | 客户旅程数据                 |
| 媒介测量           | **Nielsen**    | 受众规模与曝光测量   | 跨媒介 reach/frequency       |
|                    | **Placer IQ**  | 线下人流量数据       | OOH 媒介归因                 |
| 广告平台           | **DV360**      | Google 程序化广告    | 投放执行 + 报告              |
|                    | **Meta**       | Facebook / Instagram | 投放执行 + 报告              |
|                    | **TikTok**     | TikTok Ads           | 投放执行 + 报告              |
|                    | **Trade Desk** | DSP 程序化           | 投放执行 + 报告              |
|                    | **StackAdapt** | DSP（中型代理偏好）  | 投放执行 + 报告              |
| 分析 / 倡导 / 传输 | **GA4**        | Google Analytics 4   | 网站行为分析                 |
|                    | **Quorum**     | 政治倡导 / 立法监控  | 政府关系类客户               |
|                    | **Tresorit**   | 端到端加密文件传输   | HIPAA-compliant 客户数据传输 |

**+More** 表示同类下还有可扩展位（roadmap）。

### 1.2 LAYER 2 · ELT 八步管道（Ingestion + Transform）

子标题 "编排可选：Dagster OSS / Apache Airflow" 表明主调度二选一（详见 §1.2.3）。

**1.2.1 第一行：4 个 Gate（数据入仓前的门）**

| Gate                       | 解释                                                                      |
| -------------------------- | ------------------------------------------------------------------------- |
| 🔑 **Credential Vault**    | OAuth Token / API Key / Service Account 的加密保险柜，per-tenant 隔离加密 |
| 🧭 **Classification Gate** | 数据进入前自动识别 PII / PHI；命中则路由进 Raw Lake，否则进 ELT staging   |
| ⚠ **Quarantine Queue**     | 校验失败的脏数据进入隔离队列，不污染主仓库；可重处理或人工核查            |
| 📝 **Audit Log**           | Extract / Classify / Load / Transform 每步都写 INSERT-only 审计           |

**1.2.2 第二行：5 个变换阶段（5 Transforms）**

| STEP | 阶段名               | 解释                                                                                 |
| ---- | -------------------- | ------------------------------------------------------------------------------------ |
| 1    | **Normalize**        | 字段标准化：把 14 个源的不同 schema 映射到 Canonical schema（13 个统一实体）         |
| 2    | **Deduplicate**      | 跨平台 / 跨日去重：基于业务键（campaign_id + date + platform）合并重复行             |
| 3    | **Validate**（红色） | Schema 验证 + 业务规则 + **PHI Detector 扫描**（命中则路由进 raw_secure 或隔离队列） |
| 4    | **Enrich**           | JOIN canonical 实体 + 第三方查询（Experian 反查 / Nielsen reach 测算）+ 特征工程     |
| 5    | **Index**            | 物化视图（marts 报表）+ pgvector 向量化（ai_context 给 AI 用）                       |

ELT 八步 = Extract → Classify → Load + 上述 5 Transforms = 共 8 步。前 3 步发生在 Gate 行（Extract/Classify/Load）。

**1.2.3 底部：ORCHESTRATION 横条（主调度二选一 + 辅助）**

| 元素                      | 角色             | 解释                                                                                                                                                     |
| ------------------------- | ---------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 🟪 **Dagster OSS**        | 主调度（可选 A） | `Asset Graph` = 原生数据血缘；`dagster-dbt` = dbt model 一等集成；`per-Agency Partition` = 多租户隔离；`Code Location per-region` = HIPAA region binding |
| 🟦 **Apache Airflow**     | 主调度（可选 B） | 业内最普及的 DAG 编排器；1000+ Provider connector 生态；适合已熟练 Airflow 的团队，或短期不需要原生血缘的场景                                            |
| 🟧 **AWS Step Functions** | 辅助调度         | 仅用于：AI 写回审批工作流（Media Agent → 广告平台写回必须 human approval）+ DSAR 长流程（受理→PII Access→导出→邮件→确认）。由主调度器触发。              |

> 详见 [ELT-ORCHESTRATION-PRIORITY](../ELT-ORCHESTRATION-PRIORITY.md)。

### 1.3 LAYER 3 · Two-Lake 仓库（双 Lake 仓库）

中间一条粗红虚线 = **PII Segregation Boundary**（物理隔离边界）。

**1.3.1 左：Raw PII-Segregated Lake**（红色 + 🔒 锁图标）

- 含可识别字段的原始数据
- 子文字：「原始数据 · 含可识别字段 · 严格隔离」
- 4 个 chip：
  - **AES-256 加密** · 每租户独立 KMS（密钥管理服务）
  - **仅 ELT + 审计员** · 业务用户 / AI 禁止访问
  - **INSERT-only 审计** · 所有读写记录不可篡改
  - **HIPAA 6y · 通用 90d** · 分级保留策略

**1.3.2 中：PII Segregation Boundary（粗红虚线 + 🔐 PII 徽章）**

整张图最关键的合规设计：左右两侧物理隔离，使用不同物理存储集群 + 独立 KMS + mTLS 网络，**Processed Lake 永远拿不到明文 PII**。需要明文 PII 时走专门的 PII Access Service（详见 TSD §3.4）。

**1.3.3 右：Processed Lake**（紫色 + ✓ 图标）

- 匿名化 / 哈希化的可分析数据
- 子文字：「Per-Tenant DB · Canonical · Zero-Copy · 业务可用」
- 4 个 chip：
  - **SHA-256 + Agency Salt** · 每租户独立盐值
  - **业务 + AI 可读** · 标准访问层
  - **canonical / marts / ai_context** · 3 个用途明确的 schema
  - **Per-Tenant DB** · 每 Agency 独立数据库

### 1.4 LAYER 4 · Core AI Brain（核心 AI 大脑）

并排 2 节点：

| 节点                        | 解释                                                                                     |
| --------------------------- | ---------------------------------------------------------------------------------------- |
| **LLM Router (OpenRouter)** | 统一 LLM 网关：模型路由（Opus/Sonnet/Haiku）+ 成本控制 + 合规边界（HIPAA → Bedrock BAA） |
| **Agent Orchestrator**      | 编排 4 个 Pillar Agent 的串/并联调用；token 预算控制；Langfuse 全链路追踪                |

### 1.5 LAYER 5 · Pillar Agents（4 个柱子 Agent）

| Agent                 | 模型（默认）  | 职责                                                     |
| --------------------- | ------------- | -------------------------------------------------------- |
| **Persona Agent**     | Claude Opus   | 受众画像构建（深度推理）→ 输出受众段                     |
| **Creative Agent**    | Claude Sonnet | 创意生成 + A/B 提案（文案 + 视觉提示）                   |
| **Attribution Agent** | Claude Sonnet | 跨渠道归因 / ROI 解释                                    |
| **Media Agent ★**     | Claude Sonnet | 媒介采买优化（NEW · 需 human approval 才能写回广告平台） |

★ 标记 = 写回类 Agent，受 Step Functions 审批流保护。

### 1.6 LAYER 6 · Application / Portal（应用与门户）

| 元素                        | 解释                                                       |
| --------------------------- | ---------------------------------------------------------- |
| **Agency Portal**           | Agency 工作台：管理本 Agency 下所有 Client / 数据源 / 报表 |
| **Client Portal**           | 客户白标门户：Client 仅能看自己的数据（RLS 强制）          |
| **API Gateway**             | 程序化访问入口：JWT + scope token                          |
| **WebSocket Notifications** | 实时通知：Agent 完成 / 审批 / 报告就绪                     |

### 1.7 横切元素

- **Compliance Boundary** —— 整张图外圈 amber 虚线，左上角徽章 "GDPR · CCPA · HIPAA · SOC 2 · Data Residency"
- **加密标记** —— 跨层箭头默认 AES-256 + TLS 1.3
- **SSO 旁注** —— "Google OAuth（MVP）/ Office 365（Post-MVP）"

---

## 2. 架构方案图（Architecture Schema）

> 7 层 band + 右侧 Compliance Panel + 底部 Key Constraints。自上而下：**门户 → 功能 Pillars → AI Brain → ELT → Two-Lake → 外部源 → 基础设施**。比网络图更全（包含基础设施、可观测、合规面板）。

### 2.1 LAYER 1 · 客户 / 门户（4 User Types · 白标）

4 类用户角色（3 级权限层级）：

| 用户类型                 | 层级 | 解释                                                |
| ------------------------ | ---- | --------------------------------------------------- |
| **Platform Super Admin** | L1   | 平台总管理员，可跨 Agency 聚合做 benchmarking       |
| **Agency Admin**         | L2   | Agency 管理员，管理本 Agency 下所有 Client + 数据源 |
| **Agency Operator**      | L2   | Agency 日常操作员（投放/创意/报告）                 |
| **Client Viewer**        | L3   | 客户端用户，**RLS 强制只看本 Client 数据**          |

详见 TSD §10.1。

### 2.2 LAYER 2 · 功能 Pillars（MVP 5 大业务模块）

| Pillar              | 解释                |
| ------------------- | ------------------- |
| **Market Research** | 受众画像 + 市场洞察 |
| **Creative Engine** | 创意生成 + A/B 测试 |
| **Media Buying**    | 跨平台投放采买优化  |
| **Attribution**     | 跨渠道归因 / ROI    |
| **Client Portal**   | 客户成果消费界面    |

### 2.3 LAYER 3 · Core AI Brain（6 组件 + 4 Agent）

**2.3.1 上行：6 大核心组件**

| 组件                   | 解释                                                |
| ---------------------- | --------------------------------------------------- |
| **Context Builder**    | 上下文组装：注入 tenant / role / PII-safe 提示      |
| **LLM Router**         | 模型路由：成本 / 合规 / 能力匹配                    |
| **Agent Orchestrator** | 4 Agent 串/并联编排                                 |
| **Tool Executor**      | 工具调用：读 / 写 / 审批门（写回 = human approval） |
| **Memory · Retrieval** | 上下文摘要 + pgvector 向量召回                      |
| **Audit · Cost**       | Prompt / Token 全审计 + 成本预算                    |

**2.3.2 下行：4 个 Pillar Agent** —— 同网络图 §1.5。

### 2.4 LAYER 4 · ELT 转换管道（5 in-warehouse stages）

顶部 ORCHESTRATION 横条 + 5 个箭头形状的转换步骤。

- **顶部 ORCHESTRATION 横条**：Dagster OSS / Apache Airflow 主调度二选一 + Step Functions 审批 —— 同网络图 §1.2.3
- **5 STEP**：Normalize / Deduplicate / **Validate**（红色，含 PHI 扫描） / Enrich / Index —— 同网络图 §1.2.2

> 注：Extract / Classify / Load 在上游 L6 与 L5 之间发生，本层只展示仓库内 5 个 Transform。

### 2.5 LAYER 5 · 双 Lake 仓库（Two-Lake on Neon Postgres）

子标题："物理隔离 · Per-Tenant DB · Branch Clone"

**2.5.1 左：Raw PII-Segregated Lake**（红色锁）

5 chips：raw*pii_ga4 / raw_pii_meta / raw_pii_experian / raw_pii_transunion / raw_pii*…

**2.5.2 中柱：PII BOUNDARY**（粗红虚线 + 🔐 徽章）

**2.5.3 右：Processed Lake**（紫色 ✓）

5 chips：canonical / marts / pgvector / redis cache / branch clone

- **canonical** = 跨平台统一实体表
- **marts** = 业务报表用聚合表
- **pgvector** = PostgreSQL 向量索引扩展（给 AI 召回用）
- **redis cache** = 热数据缓存层
- **branch clone** = Neon Branching（git-style 零拷贝克隆，按需复制租户数据，不占额外存储）

右上角图标：**Neon Postgres** —— 产品仓库选型（serverless Postgres，per-Agency project）

**2.5.4 底部 6-schemas 横条**（在 L5 band 内）

| Schema         | 颜色         | 用途                                       |
| -------------- | ------------ | ------------------------------------------ |
| **raw_secure** | 红           | PII 引用 · 限访问（仅 ELT + 审计员）       |
| **staging**    | 绿（ELT 色） | 源系统标准化（dbt staging models）         |
| **canonical**  | 紫           | 跨平台统一实体（13 个 Canonical Entities） |
| **marts**      | 紫           | 报表 + persona（业务可用）                 |
| **ai_context** | 粉（AI 色）  | AI-safe 摘要 + 向量（给 AI Brain）         |
| **audit**      | amber        | 访问 + ELT + AI 全审计（INSERT-only 6y）   |

### 2.6 LAYER 6 · 外部数据源（14 Priority-1 集成）

同网络图 §1.1，按 6 个类目分组：Audience/CRM · Measurement · Ad Platforms · Analytics · Advocacy · Compliant CRM。

### 2.7 LAYER 7 · 基础设施（Infrastructure · Cross-Cutting）

| 元素            | 解释                                    |
| --------------- | --------------------------------------- |
| **Render PaaS** | 生产计算平台（multi-region，BAA 支持）  |
| **Coolify**     | 开发环境计算（self-host PaaS）          |
| **Langfuse**    | LLM 全链路追踪（prompt / token / 成本） |
| **Sentry**      | 错误监控 / 异常告警                     |
| **AWS KMS**     | 密钥管理服务（per-Agency 独立密钥）     |
| **GitHub**      | 源码 + CI/CD 流水线                     |

### 2.8 右侧 Compliance Panel（合规侧栏）

通过 spine（中间纵线）+ 横向虚线锚点连接每一层，表示**合规是横切关注，不属于任何单层**。

**2.8.1 上卡片：COMPLIANCE（4 法规 + 1 驻留）**

| 项            | 解释                                                |
| ------------- | --------------------------------------------------- |
| **GDPR**      | EU 通用数据保护条例 · DSAR 30 天 · 违规 72 小时通知 |
| **CCPA**      | 加州消费者隐私法 · DSAR 45 天                       |
| **HIPAA**     | 美国医疗隐私法 · 违规 60 天通知 · 需签 BAA          |
| **SOC 2**     | Type II 审计 · 5 项 Trust Service Principles        |
| **Residency** | Per-Tenant Region 数据驻留                          |

**2.8.2 下卡片：核心能力（12 项）**

| 能力                            | 解释                                      |
| ------------------------------- | ----------------------------------------- |
| **PHI Detector · 18-id 扫描**   | HIPAA Safe Harbor 18 类标识符自动识别     |
| **Anonymizer · SHA-256 + salt** | 不可逆哈希匿名化                          |
| **Agency Salt 隔离**            | 每 Agency 独立盐值，跨 Agency 不可关联    |
| **IP 截断 (v4/24 · v6/48)**     | IPv4 截断到 /24，IPv6 到 /48              |
| **Fernet 字段加密**             | 字段级对称加密（email / full_name）       |
| **Audit Log · 6y INSERT-only**  | 6 年不可篡改审计日志                      |
| **DSAR (30 / 45 / 30 d)**       | GDPR 30 天 / CCPA 45 天 / HIPAA 30 天 SLA |
| **Retention 引擎**              | 自动按法规过期清理                        |
| **Breach 通知 (72h / 60d)**     | GDPR 72h / HIPAA 60d 自动告警             |
| **BAA 状态追踪**                | HIPAA 客户的商业伙伴协议状态 + 到期       |
| **密钥轮换 per-Agency**         | 每租户独立 KMS 密钥 + 定期轮换            |
| **数据驻留 DLP 检查器**         | 防止数据跨 region 泄漏                    |

### 2.9 底部 KEY CONSTRAINTS（关键技术约束）

| 约束             | 解释                                               |
| ---------------- | -------------------------------------------------- |
| **Residency**    | Per-tenant region；跨 region 禁止                  |
| **Encryption**   | AES-256 静态 · TLS 1.3 传输 · per-tenant KMS       |
| **Auth**         | MVP: JWT + Google OAuth · Post-MVP: Office 365     |
| **LLM Routing**  | OpenRouter 默认 · HIPAA → Bedrock BAA              |
| **Audit**        | INSERT-only · HIPAA 6 年 · 财务 7 年               |
| **Multi-Tenant** | 物理：per-tenant DB + KMS；RLS 作 defense-in-depth |

---

## 3. 通用术语表（按字母序）

### A

- **AES-256** — 256-bit 高级加密标准，静态数据加密标准
- **Agency** — 平台租户主体（一个广告 / 营销代理公司）；**物理隔离单元**
- **Agency Salt** — 每 Agency 独立的哈希盐值，保证跨 Agency 不可关联
- **Apache Airflow** — Task/DAG-centric 数据编排器（主调度可选项 B，1000+ Provider 生态）
- **Asset Graph** — Dagster 的数据资产血缘图（每个数据产物为一个 asset）
- **Audit Log** — INSERT-only 审计日志表
- **Auth0** / **OAuth** — 第三方身份认证协议

### B

- **BAA** — Business Associate Agreement，HIPAA 要求与处理 PHI 的伙伴签署
- **Bedrock** — AWS 托管 LLM 服务（含 Claude），可签 BAA 用于 HIPAA 场景

### C

- **Canonical** — 跨平台统一实体 schema（13 个标准实体）
- **CCPA** — California Consumer Privacy Act
- **Code Location** — Dagster 的代码部署单元，可绑定特定 region
- **Coolify** — Self-host PaaS（开发环境用）

### D

- **Dagster** — Asset-centric 数据编排器（主调度可选项 A，原生血缘 + dagster-dbt 一等集成）
- **dagster-dbt** — Dagster 与 dbt 的一等集成包
- **dbt** — Data Build Tool，SQL-based 转换框架
- **DSAR** — Data Subject Access Request（数据主体权利请求）
- **DSP** — Demand-Side Platform（广告需求方平台）
- **DV360** — Google Display & Video 360

### E

- **ELT** — Extract Load Transform（vs ETL：先 Load 再 Transform）

### F

- **Fernet** — Python `cryptography` 库的对称加密方案

### G

- **GA4** — Google Analytics 4
- **GDPR** — General Data Protection Regulation（EU 通用数据保护条例）

### H

- **HIPAA** — Health Insurance Portability and Accountability Act（美国医疗隐私法）
- **HubSpot** — CRM 平台

### I

- **IDR** — Identity Resolution（身份解析）

### J

- **JWT** — JSON Web Token（认证令牌）

### K

- **KMS** — Key Management Service（密钥管理服务）

### L

- **Langfuse** — LLM 应用全链路可观测性平台
- **LiveRamp** — 身份解析 / IDR 提供商
- **LLM** — Large Language Model

### M

- **mTLS** — Mutual TLS（双向 TLS 认证）
- **MWAA** — AWS Managed Workflows for Apache Airflow（**永久排除**）

### N

- **Neon** — Serverless Postgres（**产品唯一仓库选型**，per-Agency project + Branching）

### O

- **OpenRouter** — LLM 多提供商路由网关

### P

- **PHI** — Protected Health Information（受保护健康信息，HIPAA 定义）
- **PII** — Personally Identifiable Information（可识别个人信息）
- **PII Access Service** — 受控明文 PII 访问服务（purpose-bound · time-limited token）
- **PII Boundary** — PII Segregation Boundary（PII 物理隔离边界）
- **PII Segregation** — 把含 PII 数据物理隔离到 Raw Lake，业务 / AI 拿不到明文
- **pgvector** — PostgreSQL 向量索引扩展
- **Placer IQ** — 线下人流量数据
- **Pillar Agent** — 4 个核心业务 AI Agent（Persona/Creative/Attribution/Media）
- **Prefect** — 另一个数据编排器（Plan B，仅当 Dagster Spike 失败时启用）

### Q

- **Quorum** — 政治倡导 / 立法监控数据源

### R

- **Render** — Multi-region PaaS（生产环境用）
- **RLS** — Row-Level Security（行级安全策略，PostgreSQL 原生 `ROW LEVEL SECURITY` + policy）
- **ROAS** — Return on Ad Spend（广告投放回报率）

### S

- **SHA-256** — 256-bit 安全哈希算法（用于不可逆匿名化）
- **Snowflake** — 云数仓（**不再使用**，产品已锁定 Neon Postgres）
- **SOC 2** — Service Organization Control 2 审计（5 项 Trust Service Principles）
- **SSO** — Single Sign-On（单点登录）
- **StackAdapt** — 中型代理偏好的 DSP
- **Step Functions** — AWS 工作流引擎（用于 AI 写回审批 + DSAR 长流程）

### T

- **TLS 1.3** — Transport Layer Security 1.3（传输加密）
- **Trade Desk** — 主流 DSP
- **TransUnion** — 信用 / 人口画像数据
- **Tresorit** — 端到端加密文件传输（HIPAA-compliant）
- **Two-Lake** — 双数据湖架构（Raw PII Lake + Processed Lake，物理隔离）

### V

- **Vault** — Credential Vault，加密保险柜

### Z

- **Zero-Copy Cloning / Branching** — Neon 的 git-style branch 特性：按需复制租户数据，不占额外物理存储

---

## 4. 关联文档

- [Technical Solution](./technical-solution.md) — 详细技术方案文字版
- [Network Diagram](./network-diagram.svg) — 网络数据流图（CN）
- [Network Diagram EN](./network-diagram-en.svg) — Network Diagram (EN)
- [Architecture Schema](./architecture-schema.svg) — 架构方案图（CN）
- [Architecture Schema EN](./architecture-schema-en.svg) — Architecture Schema (EN)
- [ELT-ORCHESTRATION-PRIORITY](../ELT-ORCHESTRATION-PRIORITY.md) — Dagster vs Airflow vs AWS 编排选型
- [ADR-002 Neon Tenancy](../ADR-002-NEON-TENANCY-OPTIMAL.md) — 多租户隔离架构决策
- [ADR-003 Dagster vs Airflow](../ADR-003-DAGSTER-VS-AIRFLOW.md) — 编排引擎主决策
