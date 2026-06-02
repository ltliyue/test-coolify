# ELT Orchestration 引擎选型与优先级

> **结论摘要**：主调度 **Dagster OSS 与 Apache Airflow 二选一**（架构图与 PSD 同时保留两者作为可选方案）。本文档从"对项目最优"视角推荐 Dagster OSS 为首选，但 Airflow 作为业内最普及方案同样可承载本平台 ELT，团队可按熟悉度与项目阶段选择。

> 状态：决策草案 · 与 [ADR-003](./ADR-003-DAGSTER-VS-AIRFLOW.md) · [ADR-003-SUPP](./ADR-003-SUPP-OTHER-ORCHESTRATORS.md) · [PSD-TECHNICAL-SOLUTION §5](./psd/technical-solution.md) 关联
> 范围：ReceptivIQ Platform 的 ELT 八步管道（Extract → Classify → Load → Normalize → Deduplicate → Validate → Enrich → Index）的调度/编排引擎选型
> **立场**：本文档**不考虑当前已部署的 Airflow 沉没成本**，纯粹按"对项目最优"做选型。

---

## 1. Context · 背景

ReceptivIQ 是一个 **AI-native、多租户、合规优先（GDPR + HIPAA + CCPA + SOC 2）、dbt-driven** 的营销数据平台。编排引擎是 ELT 八步管道、4 个 Pillar Agent、PII Access Service、DSAR 长流程的中枢，选型决定了血缘、审计、多租户、AI 可解释性的天花板。

候选范围：

- **A. Apache Airflow**（自托管 / AWS MWAA）
- **B. Dagster**（OSS / Cloud Hybrid）
- **C. AWS 原生**（Glue / Step Functions）
- **D. Prefect 3**（补充）

---

## 2. 项目对编排引擎的硬需求

按重要性排序（★ 越多越关键）：

| #   | 需求                                                                                                                                                                                | 权重  | 来源                                     |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----- | ---------------------------------------- |
| 1   | **数据血缘 / Asset Model** — 用于 DSAR 主体定位、SOC 2 审计、AI 输出可解释性                                                                                                        | ★★★★★ | PSD §3.3 hard isolation · §8.1 GDPR DSAR |
| 2   | **dbt 一等集成** — 8 步 ELT 后半段全部在 dbt 内执行（staging → canonical → marts）                                                                                                  | ★★★★★ | PSD §5 ELT pipeline                      |
| 3   | **多租户 awareness** — per-Agency 独立 partition / code location，跨 Agency 完全隔离                                                                                                | ★★★★★ | PSD §2.3 物理隔离                        |
| 4   | **Python-native** — 团队全栈 Python；agent.py / brain.py / adapter base 全部 Python                                                                                                 | ★★★★  | 团队 / brain.py                          |
| 5   | **14 P1 数据源 connector**（Experian · TransUnion · LiveRamp · HubSpot · Nielsen · Placer IQ · Quorum · DV360 · Meta · TikTok · Trade Desk · StackAdapt · GA4 · Tresorit） + 可扩展 | ★★★★  | PSD §7                                   |
| 6   | **HIPAA / 数据驻留** — region-bound 执行，BAA 客户走独立 region                                                                                                                     | ★★★★  | PSD §4.6 / §8.3                          |
| 7   | **审计 6 年** — Run history INSERT-only、可追溯                                                                                                                                     | ★★★★  | PSD §8.3 HIPAA                           |
| 8   | **PII Access Service 集成** — 编排器可调用受控明文 PII 出口                                                                                                                         | ★★★   | PSD §3.4                                 |
| 9   | **AI Agent 调度 + 审批 gates** — Media Agent 写回必须人工 approve                                                                                                                   | ★★★   | PSD §2.5 Autonomy Boundary               |
| 10  | **成本可控** — 月成本可预测，启动期 < $500/月                                                                                                                                       | ★★★   | 财务约束                                 |
| 11  | **跨 Agency benchmarking** — 平台 Super Admin 能跨 Agency 聚合                                                                                                                      | ★★★   | PSD §4.1 + Rose's input                  |
| 12  | **学习曲线 / 团队 ramp-up**                                                                                                                                                         | ★★    | 团队 ~3 人                               |
| 13  | **小众 connector**（Quorum / LeadRX / Tresorit）                                                                                                                                    | ★★    | PSD §7.1                                 |

---

## 3. 候选引擎清单

| ID     | 引擎                            | 托管形态                  | 简评                                           |
| ------ | ------------------------------- | ------------------------- | ---------------------------------------------- |
| **A1** | **Apache Airflow**（自托管）    | self-host                 | 调度成熟，但 Task-centric 心智、血缘需外挂     |
| **A2** | **AWS MWAA**（Managed Airflow） | AWS managed               | 仍是 Airflow，运维卸载到 AWS                   |
| **B1** | **Dagster OSS**（自托管）       | self-host                 | Asset-centric，原生血缘 + dagster-dbt 一等集成 |
| **B2** | **Dagster Cloud**（Hybrid）     | Elementl managed          | 控制面云端、计算面自托管；含 RBAC / 审计 / SSO |
| **C1** | **AWS Glue**                    | AWS serverless            | Spark-based，AWS-centric，非 Python-first      |
| **C2** | **AWS Step Functions + Lambda** | AWS serverless            | 通用工作流编排，擅长长流程审批，弱于数据语义   |
| **C3** | AWS Data Pipeline               | AWS（已弃用）             | ❌ 不予考虑                                    |
| **D**  | **Prefect 3**                   | self-host / Prefect Cloud | DX 现代，生态较小，血缘需外挂                  |

---

## 4. 评估矩阵

每个候选 vs 13 项需求评分（✅ = 强 / 🟡 = 中 / ⚠️ = 弱 / ❌ = 不支持）：

| #   | 维度                       | A1 Airflow                    | A2 MWAA             | **B1 Dagster OSS**                                         | **B2 Dagster Cloud**                | C1 AWS Glue                | C2 Step Fn                      | D Prefect 3          |
| --- | -------------------------- | ----------------------------- | ------------------- | ---------------------------------------------------------- | ----------------------------------- | -------------------------- | ------------------------------- | -------------------- |
| 1   | 数据血缘 / Asset           | ⚠️ 需 OpenLineage 外挂        | ⚠️ 同上             | ✅ **原生 Asset Model**                                    | ✅ 原生                             | 🟡 Glue Data Catalog（弱） | ❌ 无数据语义                   | ⚠️ 需 OpenLineage    |
| 2   | dbt 集成                   | 🟡 dbt-airflow provider       | 🟡 同上             | ✅ **dagster-dbt 一等集成**（每个 dbt model = 一个 asset） | ✅ 同上                             | 🟡 通过 Spark job          | ❌ 不直接集成                   | 🟡 prefect-dbt       |
| 3   | 多租户 awareness           | 🟡 DAG 参数化，无原生概念     | 🟡 同上             | ✅ Partition / Code Location 天然隔离                      | ✅ 同上 + multi-deployment          | ❌ Job-level 概念，无租户  | ❌ 无                           | 🟡 Work Pool         |
| 4   | Python-native              | ✅ DAG 即 Python              | ✅ 同上             | ✅ Decorator (@asset) 纯 Python                            | ✅ 同上                             | ⚠️ PySpark / Glue Studio   | 🟡 Lambda 内可写 Python         | ✅ @flow 纯 Python   |
| 5   | 14 P1 connector            | ✅ 1000+ Provider；小众需自写 | ✅ 同上             | 🟡 ~300 集成；小众需自写 IO Manager                        | 🟡 同上                             | ⚠️ AWS-centric             | ⚠️ 不是 ETL 专用                | 🟡 ~50 集成          |
| 6   | HIPAA / 数据驻留           | ✅ 自托管任意 region          | ✅ AWS region 选定  | ✅ Code Location per-region                                | ✅ Hybrid（计算自托管，控制面云端） | ✅ AWS region + BAA        | ✅ AWS region + BAA             | 🟡 自托管或 Cloud    |
| 7   | 审计 6 年                  | 🟡 Metadata DB 自己持久化     | ✅ MWAA 自带 export | 🟡 需配 audit hook                                         | ✅ Cloud 内置                       | ✅ CloudTrail              | ✅ CloudTrail                   | 🟡 self-managed      |
| 8   | PII Access Service 调用    | ✅ PythonOperator             | ✅ 同上             | ✅ asset 内 Python 调用                                    | ✅ 同上                             | 🟡 跨服务复杂              | ✅ Lambda 调用                  | ✅ task 调用         |
| 9   | AI Agent 调度 + 审批 gates | ⚠️ 自写审批 sensor            | ⚠️ 同上             | 🟡 Tool Executor + 外挂 approval                           | 🟡 同上 + UI 审批                   | ⚠️ 不擅长                  | ✅ **原生 human approval task** | 🟡 sensor 实现       |
| 10  | 成本 < $500/月             | ✅ self-host                  | ⚠️ MWAA $400+/月    | ✅ self-host                                               | ❌ Pro $1500/月起                   | ✅ pay-per-run             | ✅ pay-per-state-transition     | ✅ self-host 免费    |
| 11  | 跨 Agency benchmarking     | 🟡 跨 DAG 自行 SQL            | 🟡 同上             | ✅ secure view + Dagster catalog 聚合                      | ✅ 同上 + multi-deployment UI       | 🟡 Glue catalog 跨账号     | ❌ 无数据语义                   | 🟡 跨 deployment SQL |
| 12  | 学习曲线                   | ✅ 业内普及                   | ✅ 同 Airflow       | ⚠️ Asset 心智（1-2 周）                                    | ⚠️ 同上 + Cloud 概念                | ⚠️ Glue + PySpark          | ⚠️ State machine JSON           | 🟡 与 Airflow 相近   |
| 13  | 小众 connector             | ✅ Python 自写 adapter        | ✅ 同上             | ✅ 同上（@asset wrap）                                     | ✅ 同上                             | ❌ 不易接入                | 🟡 Lambda 自写                  | ✅ @flow 自写        |

**评分汇总**（每项 ✅=2 / 🟡=1 / ⚠️=0.5 / ❌=0）：

| 候选                  | 总分（最高 26） | 强项                               | 弱项                               |
| --------------------- | --------------- | ---------------------------------- | ---------------------------------- |
| **B1 Dagster OSS**    | **24** ⭐       | 血缘 · dbt · 多租户 · 成本 · 合规  | 学习曲线 · 小众 connector          |
| **B2 Dagster Cloud**  | 22              | 同 OSS + 托管 + 审批 UI + 审计内置 | 成本                               |
| **A1 Airflow**        | 19              | connector 生态 · 团队普及 · 成本   | 血缘弱 · 多租户弱 · 审批           |
| **D Prefect 3**       | 19              | Python DX 最佳 · 成本 · 区域灵活   | 血缘弱 · 生态比 Airflow 小         |
| **A2 MWAA**           | 18              | 同 Airflow + 审计 + AWS 集成       | 成本                               |
| **C2 Step Functions** | 14              | 成本 · 审批 · 合规 · AWS 集成      | 不擅长数据 · 无血缘 · 无 dbt       |
| **C1 AWS Glue**       | 13              | 合规 · 自动伸缩 · 审计             | 非 Python-first · connector 偏 AWS |

---

## 5. 优先级排名（最优方案视角）

> 不考虑当前已部署的 Airflow，仅以"对 ReceptivIQ 最优"为准。

### 🥇 第 1 选：Dagster OSS（自托管）— **直接采用**

**为什么是最优解：**

1. **数据血缘是 ReceptivIQ 的命脉，不是 nice-to-have**
   - DSAR（GDPR 30d / CCPA 45d）要求"按主体定位所有衍生数据"。Dagster Asset Graph 天然就是答案；Airflow 需要额外维护 OpenLineage + Marquez 才能勉强达成，且仍弱于原生 Asset 模型。
   - SOC 2 CC6 审计要求"任一指标可追溯到原始来源"。Dagster UI 直接交付，省下大量审计配合时间。
   - AI 输出可解释性：客户问"PDF 报告里这条 ROAS 怎么算的"，Dagster 可一路从 marts → canonical → staging → raw 回溯。

2. **dagster-dbt 是 8 步 ELT 后 5 步（Normalize → Deduplicate → Validate → Enrich → Index）的事实标准**
   - dbt model 自动注册为 asset，与上游 Python adapter asset 形成统一 DAG
   - dbt test = Dagster asset check，验证与编排一体
   - Airflow 的 dbt 集成是"额外 operator 调用 CLI"，丢失血缘上下文

3. **多租户原生：Partition Key = Agency**
   - "重算 Agency X 上周数据" 是一行 CLI / 一次 UI 点击
   - per-Agency 失败重试不会影响其他 Agency
   - Code Location 隔离支持 BAA 客户单独 region 部署

4. **Python-native + 成本可控**
   - `@asset` decorator 与 BaseAdapter / Pillar Agent 同语言
   - 自托管仅基础设施成本，月成本远低于 MWAA / Dagster Cloud

5. **AI Agent 友好**
   - Pillar Agent 输出可注册为 asset（persona_v3 / creative_brief_v2），版本化 + 可追溯
   - 与 Tool Executor 模式天然契合

**短板与缓解：**

| 短板                            | 缓解                                                     |
| ------------------------------- | -------------------------------------------------------- |
| Asset 心智学习曲线 1-2 周       | Dagster University 免费课程；前 2 周 spike 验证 DX       |
| 小众 connector（Quorum/LeadRX） | 沿用 BaseAdapter 自写 IO Manager，与任何引擎等效工作量   |
| 审计 hook 需自写                | 复用 audit_simple()；或后期升级到 Dagster Cloud 内置审计 |
| AI 写回审批 UI 弱               | 用 Step Functions 处理审批子流程，由 Dagster 触发        |

### 🥈 第 2 选：Dagster Cloud（Hybrid）— 规模上来后升级

**何时升级（不是 Day 0）：**

- 客户数 ≥ 10 Agency / 团队规模 ≥ 8 人 → 需要 RBAC / SSO / 审计 UI
- 不想再自运维 Dagster 控制面
- HIPAA 客户要求"控制面有 SOC 2 attestation"

**门槛：** Pro $1500/月起。Day 0 用 OSS，营收/团队规模到位再升级，迁移零成本（同一代码库）。

### 🥉 第 3 选：AWS Step Functions — **专用于审批 / 长流程**

**用于（与 Dagster 互补，不替代）：**

- **AI 写回审批工作流**：Media Agent 写回 Meta / DV360 / TikTok 必须 human approval。Step Functions 的 `Wait for human approval` 状态机原生支持，比自写 Airflow / Dagster sensor 更稳。
- **DSAR 长流程**：受理 → PII Access Service → 数据导出 → 邮件投递 → 客户确认（跨天、跨服务）

**Day 0 是否需要：** 否。MVP 阶段可用 Dagster sensor + 简易审批 UI 临时替代；待 Media Agent 上线、DSAR 量产再引入。

### 第 4 选：Apache Airflow — **不主动采用**

**结论**：在"不考虑沉没成本"前提下，**没有任何维度 Airflow 优于 Dagster OSS**。仅在以下情况保留：

- 团队对 Dagster Spike 强烈反弹（极小概率）
- 公司战略锁 AWS 且不接受 Dagster Cloud（→ 用 MWAA）

### 第 5 选：Prefect 3 — **Plan B**

**用于：** 如果 Dagster Spike（2 周）后团队明确不适应 Asset 心智，切换到 Prefect 3 作为现代化 Task-centric 方案。仍优于 Airflow，但血缘需外挂。

### 第 6 选：AWS Glue — **大数据子任务调用**

**用于：** Backfill 历史数据（GB+ 级广告平台数据）等 Spark workload。由 Dagster 触发 Glue Job，不作为主调度。

### 第 7 选（不推荐）：AWS MWAA

仍然是 Airflow + 月成本 $400+ + AWS 锁定。在"最优方案"视角下，没有任何理由选它。

### 排除：AWS Data Pipeline

AWS 已停止新投入，不予考虑。

---

## 6. 推荐落地路径（Day 0 起）

| 时间窗             | 阶段                    | 行动                                                                                            |
| ------------------ | ----------------------- | ----------------------------------------------------------------------------------------------- |
| **第 1-2 周**      | **Dagster Spike**       | 搭建 Dagster OSS + dagster-dbt + 1 个示例 asset（GA4），验证团队 DX                             |
| **第 3-6 周**      | **核心 asset 化**       | 9 个 ETL Adapter 全部以 `@asset` 重写；dbt 13 个模型接入 dagster-dbt；建立 per-Agency partition |
| **第 7-10 周**     | **AI Agent + 审计**     | 4 个 Pillar Agent 输出注册为 asset；接入 PII Access Service；自写 audit hook 写入 audit_events  |
| **第 11-14 周**    | **生产化**              | Code Location per-region（HIPAA）；监控告警；SLO 定义；上线生产                                 |
| **2026 H2**        | **Step Functions 引入** | Media Agent 写回审批流 + DSAR 长流程切换到 Step Functions（Dagster 触发）                       |
| **2026 Q4 / 2027** | **Dagster Cloud 升级**  | 团队 / 客户规模到位后从 OSS 升级到 Cloud Hybrid（同一代码库，零迁移成本）                       |

**关键差异 vs 沉没成本路径**：

- 不再"MVP 保留 Airflow → Q3/Q4 启动迁移"，**Day 0 直接 Dagster**，省下未来 6-9 个月的双跑 / 迁移成本
- 9 个现有 Adapter 重写为 `@asset` 的工作量约 1-2 周，远低于"先用 Airflow 跑半年再迁移"的总成本
- 血缘 / 多租户 / 审计能力提前 6-9 个月到位，对 GDPR / SOC 2 Type II 准备至关重要

---

## 7. 决策矩阵速查

| 场景                                         | 推荐                                      |
| -------------------------------------------- | ----------------------------------------- |
| **新项目 Day 0 选型（本项目）**              | **Dagster OSS（自托管）** ⭐              |
| **客户数 ≥ 10 / 团队 ≥ 8 / 需要 RBAC + SSO** | 升级 Dagster Cloud Hybrid                 |
| **AI 写回审批 / DSAR 长流程**                | AWS Step Functions（Dagster 触发）        |
| **Spark workload / 大数据 backfill**         | AWS Glue（Dagster 触发）                  |
| **HIPAA 强 region binding**                  | Dagster Hybrid 或 OSS + 多 Code Location  |
| **团队对 Asset 心智强烈反弹**                | Prefect 3 作为 Plan B（不要回退 Airflow） |
| **永久排除**                                 | AWS MWAA · AWS Data Pipeline              |

---

## 8. 与 PSD §5 ELT Pipeline 的映射

PSD §5 定义的 8 步 ELT 管道：

| ELT Step      | **Dagster 实现（推荐）**       | Airflow 实现                  | AWS Glue 实现                |
| ------------- | ------------------------------ | ----------------------------- | ---------------------------- |
| 1 Extract     | `@asset` per source            | PythonOperator + BaseAdapter  | Glue Crawler / Job           |
| 2 Classify    | `@asset` with metadata         | PythonOperator + PHI Detector | Glue PII detection (limited) |
| 3 Load        | `@asset` with IO Manager       | PythonOperator → warehouse    | Glue Job DataFrame.write     |
| 4 Normalize   | **dagster-dbt 原生**           | dbt run via DbtOperator       | Glue + PySpark               |
| 5 Deduplicate | **dagster-dbt**                | dbt run                       | Glue + PySpark               |
| 6 Validate    | **dagster-dbt + asset checks** | dbt test                      | Glue Data Quality            |
| 7 Enrich      | **dagster-dbt**                | dbt run                       | Glue + 自定义脚本            |
| 8 Index       | `@asset` with deps             | PostgreSQL / Snowflake script | Glue Crawler 更新 catalog    |
| **Audit**     | 自写 hook / Cloud 内置         | 自写 hook                     | CloudTrail                   |

Dagster 在第 4-8 步直接打通 dbt，是核心差异化。

---

## 9. 风险与备选

| 风险                                   | 概率 | 影响 | 缓解                                                               |
| -------------------------------------- | ---- | ---- | ------------------------------------------------------------------ |
| 团队 Dagster Asset 心智不适应          | 中   | 高   | 第 1-2 周 Spike 反向验证；如反弹切换 Prefect 3（仍不回退 Airflow） |
| Dagster OSS 大规模生产案例少           | 中   | 中   | 参考 Cherry / GitLab / Mux 等用户；必要时升级 Cloud Hybrid         |
| 小众 connector 社区缺乏                | 高   | 低   | BaseAdapter 自写，与任何引擎等效                                   |
| Dagster Cloud 涨价 / 路线变化          | 中   | 低   | OSS 完全可用，不依赖 Cloud                                         |
| AWS Step Functions 锁定 AWS            | 中   | 低   | 仅审批子流程，可替换为 Temporal                                    |
| Spike 期临时 9 个 Adapter 改造影响进度 | 中   | 中   | 改造工作量 1-2 周，可与设计文档评审并行                            |

---

## 10. 最终建议

| 项                         | 推荐                                             |
| -------------------------- | ------------------------------------------------ |
| **主调度（Day 0 起）**     | **Dagster OSS（自托管）** ⭐                     |
| **AI 写回审批流**          | AWS Step Functions（专用，由 Dagster 触发）      |
| **大数据 backfill 子任务** | AWS Glue（按需，由 Dagster 触发）                |
| **DSAR / 合规长流程**      | AWS Step Functions 或 Dagster sensor + 人工 task |
| **规模化升级路径**         | Dagster Cloud Hybrid（10+ Agency / 8+ 团队后）   |
| **Plan B（Spike 失败）**   | Prefect 3                                        |
| **永久排除**               | Airflow · MWAA · AWS Data Pipeline               |

**核心决策**：**Day 0 直接采用 Dagster OSS，不走"Airflow 过渡 → Dagster 迁移"的双轨路径**。AWS Step Functions / Glue 作为辅助 AWS 工具按需集成进 Dagster，永远不作为主调度。

> 与上一版差异：上一版考虑了"Airflow 已部署"沉没成本，建议 MVP 保留 Airflow。本版从纯最优出发，结论是**没有任何理由 Day 0 选 Airflow**——血缘、多租户、dbt 集成、AI 友好性、合规 6 维全面落后于 Dagster；唯一优势"已部署"在"不考虑沉没成本"前提下被抵消。

---

## 11. 关联文档

- [ADR-003 Dagster vs Airflow](./ADR-003-DAGSTER-VS-AIRFLOW.md) — 主决策
- [ADR-003-SUPP 其他编排引擎](./ADR-003-SUPP-OTHER-ORCHESTRATORS.md) — Prefect / Kestra / Mage 评估
- [PSD §5 ELT Pipeline](./psd/technical-solution.md) — 8 步管道定义
- [PSD §2.5 Autonomy Boundary](./psd/technical-solution.md) — Human-in-the-loop 审批要求
- [dev-stack-layered](./diagrams/dev-stack-layered.svg) · [prod-stack-layered](./diagrams/prod-stack-layered.svg) — L4 已并列展示 Airflow + Dagster 可选关系
