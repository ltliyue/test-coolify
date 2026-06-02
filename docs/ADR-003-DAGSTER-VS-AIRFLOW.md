# ADR-003 · 编排引擎选型：Dagster vs Airflow

> **状态**：决策中（草案）
> **日期**：2026-05-14
> **决策范围**：ReceptivIQ Platform 数据/ML 工作流编排引擎
> **现状**：项目当前使用 Apache Airflow（dev-stack 已部署 webserver + scheduler 2 容器）

---

## 1. 背景与项目特征

ReceptivIQ Platform 是多租户营销/AI SaaS，编排引擎承担三类工作负载：

| 工作负载                                                                                                | 频率        | 触发方式     | 关键依赖                              |
| ------------------------------------------------------------------------------------------------------- | ----------- | ------------ | ------------------------------------- |
| **ETL 同步**（9 平台：GA4 / Meta / HubSpot / DV360 / StackAdapt / LeadRX / LiveRamp / Quorum / TikTok） | 每日 / 小时 | 定时 + 手动  | `raw_{platform}` 表写入 + 增量 cursor |
| **dbt 转换**（staging → canonical → marts，13 模型）                                                    | ETL 完成后  | 上游成功触发 | DuckDB（dev）/ Snowflake（prod）      |
| **AI Agent 后台任务**（Persona / Creative / Attribution + PDF 报告 + Audience Export）                  | 按需        | 用户 / API   | OpenRouter + Langfuse + 业务数据      |

**技术约束**：

- Python 3.9，FastAPI 后端，Celery 处理短时异步任务
- 多租户：每个 DAG 必须按 `agency_id` 隔离，PHI 数据强制走 `phi_detector + anonymizer`
- 三大法规合规（GDPR / CCPA / HIPAA），审计日志 INSERT-only 6 年
- 双仓库后端（DuckDB / Snowflake），通过 `WAREHOUSE_BACKEND` 切换

---

## 2. Airflow 评估

### 2.1 优点

| 维度              | 说明                                                                                                                                    |
| ----------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| **生态成熟**      | 2014 由 Airbnb 开源，2019 进入 Apache 顶级项目；社区最大，第三方 Provider 包数百个（snowflake / dbt / s3 / openai / sentry 等开箱即用） |
| **运维稳定性**    | 大规模生产部署案例最多（Lyft / Robinhood / Snowflake / Adobe / Reddit），KubernetesExecutor / CeleryExecutor 高可用方案久经考验         |
| **现有沉淀**      | 当前项目 Airflow 已搭建（webserver + scheduler 容器，DAG 目录已建），切换有沉没成本                                                     |
| **学习资源**      | 文档、博客、StackOverflow 答案最多；多数数据工程师默认掌握                                                                              |
| **托管选项**      | MWAA (AWS) / Cloud Composer (GCP) / Astronomer 多家托管，可降低运维                                                                     |
| **operator 生态** | 21+ 内置 operator + 1000+ Provider operator；GA4Hook / SnowflakeOperator / DbtCloudOperator 现成可用                                    |

### 2.2 缺点

| 维度                    | 说明                                                                                                                                  |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| **DAG 即代码限制**      | DAG 在 Python 顶层执行（每次 scheduler 扫描），副作用/外部调用容易在编译期执行导致问题；动态生成 DAG 反模式                           |
| **本地开发体验**        | DAG 必须放 `dags/` 目录由 scheduler 加载；本地单步调试需 `airflow tasks test` 命令行，缺少类型检查、缺少在 IDE 内直接运行 task 的能力 |
| **类型安全弱**          | Task 输入输出靠 XCom 传 dict/string，无类型签名，重构容易碎；复杂依赖图肉眼难追溯                                                     |
| **数据资产建模缺失**    | Airflow 编排"任务"而非"数据资产"；表/模型/特征之间的血缘需用 OpenLineage + Marquez 额外搭建                                           |
| **依赖版本冲突**        | 单 Airflow 进程加载所有 DAG，不同 DAG 间 Python 依赖冲突需用 PythonVirtualenvOperator/Docker 隔离，增加复杂度                         |
| **Web UI 数据视图**     | UI 以 DAG/Task 为中心，没有"表 / dataset"视图，dbt 模型血缘需要插件                                                                   |
| **Backfill / 重试粒度** | 重跑历史只能按 DAG run 维度，难以精确选择"只重算受影响的下游资产"                                                                     |

### 2.3 与当前项目契合度

✅ 已部署 → 改动成本低
✅ 9 平台 ETL 用 PythonOperator + 现有 BaseAdapter 跑通直接可用
⚠️ dbt 血缘需手动维护 + OpenLineage 插件
⚠️ Persona / Creative / Attribution Agent 触发用 PythonOperator 调 brain.py，但 token 预算/Langfuse trace 关联需手写

---

## 3. Dagster 评估

### 3.1 优点

| 维度                                    | 说明                                                                                                              |
| --------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| **资产为先（Software-Defined Assets）** | 一等公民是"数据资产"（表/模型/特征/报表），不是任务；自动追踪每个资产的生成代码、上游依赖、物化历史               |
| **类型安全 + IO 抽象**                  | `@asset` 函数有 Python 类型注解 + Pydantic 配置；IO Manager 解耦"如何存储"（DuckDB / Snowflake / S3）与"如何计算" |
| **本地开发优秀**                        | `dagster dev` 一条命令起开发栈；`@asset` 函数可直接当 Python 函数调用调试，IDE 类型检查；单元测试简洁             |
| **dbt 一等支持**                        | `dagster-dbt` 自动把每个 dbt 模型映射成 Dagster asset，血缘 + UI 视图原生集成，无需 OpenLineage                   |
| **Partition + Backfill 精细化**         | 资产按时间分区（每日/每小时），可单独物化任意分区；重跑只算受影响下游                                             |
| **Sensor + 资产驱动调度**               | 上游资产更新 → 下游自动重算；事件驱动 + cron 混合模式                                                             |
| **Code Location 隔离**                  | 每个团队/项目独立 Python 环境（Dagster Daemon 远程加载），依赖冲突天然解决                                        |
| **Pipes（Dagster Pipes）**              | 跨语言/跨进程编排，外部脚本（Spark / Databricks / Argo）可作为 asset 步骤，回传 metadata                          |
| **Cloud 选项**                          | Dagster Cloud（Elementl）托管 + Hybrid 模式（控制面云端、计算面自托管，合规友好）                                 |

### 3.2 缺点

| 维度                     | 说明                                                                                                                                                            |
| ------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **生态较新**             | 2019 GA，社区比 Airflow 小 5-10 倍；第三方 Provider 数量少（但官方核心 Provider 覆盖了 dbt / Snowflake / S3 / BigQuery / Databricks / Spark / Pandas / Polars） |
| **学习曲线**             | "资产模型"心智模型与传统 task DAG 不同；团队需要 1-2 周适应；Job vs Asset vs Op 三层概念入门时容易混淆                                                          |
| **生产规模案例少**       | 大规模生产部署案例不如 Airflow 多（但 Cherry / GitLab / Mux / Vimeo / Drizly 等已用）                                                                           |
| **托管贵**               | Dagster Cloud 起价 $90/月（Pro 起 $1500/月），自托管运维负担与 Airflow 相当                                                                                     |
| **operator 数量**        | 比 Airflow Provider 少。一些小众数据源（Quorum / LeadRX）需自己写 resource                                                                                      |
| **重构现有 Airflow DAG** | 已写的 9 个 ETL Adapter 需重写为 `@asset` 模式（结构相似但接口不同），有迁移成本                                                                                |
| **HA / 多租户**          | Dagster Open Source 单实例为主，多 deployment / 多 code location 需 Cloud 或自己搭 Kubernetes                                                                   |

### 3.3 与当前项目契合度

✅ 9 平台 ETL 转换为 9 个 `@asset`，dbt 13 模型自动接入 → 一张完整血缘图
✅ DuckDB (dev) → Snowflake (prod) 通过 IO Manager 切换，比 `WAREHOUSE_BACKEND` env 切换更优雅
✅ AI Agent 输出（Persona / Creative / Attribution）作为"AI asset"，可追溯哪个 brand / 哪段数据生成
✅ Partition 按 agency_id 多租户切片，重跑某个客户的数据精确可控
⚠️ 团队学习曲线 + Airflow 已部署需迁移

---

## 4. 关键维度直接对比

| 维度             | Airflow                                  | Dagster                                    | 优胜方     |
| ---------------- | ---------------------------------------- | ------------------------------------------ | ---------- |
| 调度粒度         | Task                                     | Asset / Partition                          | 🟢 Dagster |
| dbt 集成         | 第三方 Provider，血缘需 OpenLineage 插件 | 官方 `dagster-dbt`，自动血缘               | 🟢 Dagster |
| 类型安全         | XCom 弱类型                              | 强类型 + Pydantic                          | 🟢 Dagster |
| 本地开发体验     | 需起 webserver + scheduler，调试靠 CLI   | `dagster dev` 一条命令，asset 直接当函数调 | 🟢 Dagster |
| 数据血缘 UI      | 任务流向，无表级血缘                     | 资产图自带血缘 + 物化历史                  | 🟢 Dagster |
| Backfill         | DAG run 粒度，全量重跑                   | Partition 级，只重算受影响下游             | 🟢 Dagster |
| 社区生态         | 最大（数千 Provider）                    | 较小（数百）                               | 🟢 Airflow |
| 生产稳定性       | 久经考验（10+ 年）                       | 较新（5 年）                               | 🟢 Airflow |
| 托管成熟度       | MWAA / Composer / Astronomer             | Dagster Cloud（贵）                        | 🟢 Airflow |
| 多团队代码隔离   | DAG 文件加载，依赖冲突                   | Code Location 独立环境                     | 🟢 Dagster |
| 跨语言/外部任务  | Operator 调度                            | Dagster Pipes 双向通信                     | 🟢 Dagster |
| 学习曲线         | 中等，资料多                             | 较陡，心智模型新                           | 🟢 Airflow |
| **当前迁移成本** | 零（已部署）                             | 重写 ETL Adapter 为 asset，约 1-2 周       | 🟢 Airflow |
| 合规审计         | DAG run 表 + 自写审计 hook               | Asset 物化日志 + 自写审计 hook             | 🟡 持平    |

---

## 5. 针对 ReceptivIQ 的决策矩阵

### 5.1 业务/技术驱动因素权重

| 因素                                                   | 权重  | 现状                       |
| ------------------------------------------------------ | ----- | -------------------------- |
| dbt 血缘对客户报告至关重要（PDF 报告须能解释数据来源） | ★★★★★ | Dagster 原生赢             |
| 多租户 agency 数据隔离 + 局部回填                      | ★★★★  | Dagster Partition 模型更优 |
| 团队规模（≈2-3 人，全栈型，Python/SQL 熟）             | ★★★   | Dagster 学习曲线可承受     |
| AI Agent 调用作为可追溯资产                            | ★★★★  | Dagster Asset 模型自然贴合 |
| 当前 Airflow 已部署，切换成本                          | ★★★   | Airflow 有沉没成本优势     |
| 合规审计要求详细数据血缘                               | ★★★★★ | Dagster 原生血缘更友好     |
| 与 Celery 协作（短时异步）                             | ★★    | 两者皆可                   |

### 5.2 推荐方案

> **结论：长期建议迁移到 Dagster；短期 Airflow 可暂留。**

**理由：**

1. **dbt 血缘是合规刚需**：客户/审计师追问"这份 PDF 报告里的 ROAS 数据从哪个 raw 表来"时，Dagster UI 一目了然；Airflow 需要外挂 OpenLineage + Marquez 才能勉强达到同等可见性。这是营销 SaaS 的核心可信度。

2. **多租户 partition 天然契合**：每个 agency_id 可作为 Dagster asset 的 partition key，"重新计算某 Brand 上周的数据"成为一次性命令；Airflow 需自写参数化 DAG。

3. **AI 资产可追溯**：Persona / Creative / Attribution 的输出可注册为 Dagster asset，自动记录"用什么模型 / 哪个 token 预算 / Langfuse trace ID"作为 metadata，与上游数据形成完整血缘，符合 HIPAA / GDPR 的"决策可解释"原则。

4. **本地开发体验直接提升团队效率**：当前 ETL Adapter 调试需要在 Docker Compose 起 Airflow webserver + scheduler；Dagster 用 `dagster dev` 5 秒启动，asset 可直接当 Python 函数测试。

**短期 Airflow 暂留的合理性：**

- 已部署，没有正在拖延的痛点
- 9 个 ETL Adapter 已按 BaseAdapter 写好，可继续运行
- 团队精力在功能开发期，不宜启动平台迁移

### 5.3 渐进式迁移路线（如决定迁）

| 阶段        | 工作                                                                  | 周期       |
| ----------- | --------------------------------------------------------------------- | ---------- |
| **Phase 0** | Spike：搭 Dagster + dagster-dbt + 1 个示例 asset（GA4），验证开发体验 | 3 天       |
| **Phase 1** | 把 dbt 13 模型接入 Dagster（最大价值最小代码）                        | 1 周       |
| **Phase 2** | 把 9 ETL Adapter 转为 Dagster asset，partition 按日期 + agency_id     | 2-3 周     |
| **Phase 3** | AI Agent 输出注册为 asset，绑定 Langfuse trace metadata               | 1 周       |
| **Phase 4** | Airflow 下线，更新文档 / dev-stack 图 / CLAUDE.md                     | 3 天       |
| **总计**    |                                                                       | **5-6 周** |

迁移期间双跑（Airflow + Dagster 并行），按子领域逐步切换，可随时回滚。

---

## 6. 替代方案（不建议但需备注）

| 方案                                        | 为何不选                                                                 |
| ------------------------------------------- | ------------------------------------------------------------------------ |
| **Prefect 2/3**                             | 优秀但生态比 Dagster 还小，dbt 集成不如 Dagster 原生；社区资源更少       |
| **Temporal**                                | 偏向应用级 workflow（订单、支付），不是数据编排，缺少 dbt / 仓库一等支持 |
| **n8n / Activepieces**                      | 低代码工具，不适合复杂数据血缘场景                                       |
| **AWS Step Functions / GCP Workflows**      | 锁云，且 dbt 集成弱                                                      |
| **保持 Airflow + 加 OpenLineage + Marquez** | 可行但等效达到 Dagster 70% 能力却需运维 3 个组件                         |

---

## 7. 最终建议

| 时间窗             | 行动                                                    |
| ------------------ | ------------------------------------------------------- |
| **现在 ~ 2026 Q3** | 保留 Airflow；9 ETL Adapter 不动；新增 DAG 仍走 Airflow |
| **2026 Q3**        | 启动 Dagster Spike（Phase 0），团队预先培训             |
| **2026 Q4**        | 启动 dbt 接入 Dagster（Phase 1）+ 双跑试运行            |
| **2027 Q1**        | 完成 ETL Adapter 迁移（Phase 2-3）→ Airflow 下线        |

**首次评审节点**：Phase 0 Spike 结束后，根据团队实际体验决定是否继续推进。如果团队反馈"Dagster 心智模型适应困难"或"项目优先级变化"，则保留 Airflow 长期使用，并补 OpenLineage 满足血缘需求。

---

## 8. 风险与缓解

| 风险                                                        | 缓解                                                                                                    |
| ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| Dagster Cloud 价格高，自托管运维负担                        | 自托管够用；社区版功能完整。如未来上规模再升级 Cloud                                                    |
| 团队 Dagster 经验不足                                       | Phase 0 投入培训 + 官方 University 免费课程；Spike 阶段邀请有经验者评审                                 |
| 迁移期间双系统维护成本                                      | 限定 5-6 周窗口，明确每阶段验收标准；不接受无限期双跑                                                   |
| Quorum / LeadRX 等小众数据源 Dagster 无 Provider            | 沿用现有 BaseAdapter 类，包一层 `@asset` 装饰器即可                                                     |
| 现有 Celery 异步任务（PDF / 受众导出 / 预算告警）是否一起迁 | **不迁**。Celery 处理用户触发的短时任务（毫秒-秒级），Dagster 处理调度型批处理（分钟-小时级），各司其职 |

---

## 9. 决策记录

- **提案人**：Guangchao
- **草案日期**：2026-05-14
- **下一动作**：分发给团队评审，2 周内确认是否启动 Phase 0 Spike
- **关联 ADR**：ADR-001（LLM 选型）· ADR-002（Neon 多租户）
