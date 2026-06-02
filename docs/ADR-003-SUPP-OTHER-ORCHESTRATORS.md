# ADR-003 补充 · 其他开源编排引擎调研

> **状态**：补充说明
> **关联**：ADR-003 · Dagster vs Airflow
> **目的**：评估除 Airflow / Dagster 之外，是否存在更适合 ReceptivIQ Platform 的开源编排引擎

---

## 1. 候选引擎一览（2026）

| 引擎                        | 首发           | 语言        | 范式          | 主流定位         | 社区规模 (★)   |
| --------------------------- | -------------- | ----------- | ------------- | ---------------- | -------------- |
| **Prefect 3**               | 2018 / 2024 v3 | Python      | 命令式 + 动态 | 通用数据编排     | 16k+           |
| **Kestra**                  | 2019 GA 2022   | Java + 任意 | 声明式 YAML   | 现代多语言编排   | 14k+           |
| **Mage AI**                 | 2022           | Python      | 笔记本 + DAG  | 数据团队首选 ETL | 8k+            |
| **Flyte**                   | 2020 (Lyft)    | Python + Go | 强类型 + K8s  | ML 流水线        | 6k+            |
| **Argo Workflows**          | 2018           | YAML on K8s | 容器原生      | K8s job 编排     | 16k+           |
| **Windmill**                | 2022           | Rust + 任意 | 脚本 + UI     | 内部工具 + 编排  | 12k+           |
| **Apache DolphinScheduler** | 2019           | Java        | 可视化拖拽    | 国内大数据团队   | 14k+           |
| **Luigi**                   | 2012 (Spotify) | Python      | 命令式        | 老牌 ETL         | 17k+（已停滞） |
| **n8n**                     | 2019           | TypeScript  | 节点拖拽      | 业务集成         | 67k+           |

---

## 2. 对当前项目仍有竞争力的 4 个

排除标准：①必须 K8s（Flyte / Argo 不适配当前 Docker Compose）；②已停滞维护（Luigi 提交频率低）；③偏业务集成而非数据/ML（n8n）。

下面 4 个有真实考察价值。

### 2.1 Prefect 3 ⭐ 推荐重点关注

**优点：**

- 纯 Python，decorator (`@flow` / `@task`) 上手 < 30 分钟；学习曲线远低于 Dagster
- v3 起完全重构：原生异步、动态 flow、subflow、results cache、retries、concurrency limits 内建
- 本地 DX 极好：`prefect server start` 起 UI + API，flow 函数直接 `python my_flow.py` 跑
- dbt 集成（`prefect-dbt`）+ Snowflake / DuckDB / S3 / Slack / Email 等 50+ collection
- Work Pool / Worker 模型：worker 拉任务，天然支持多租户隔离 + 资源分组
- Prefect Cloud 免费层 250k task runs/月，自托管 OSS 功能完整
- 多语言 SDK（Go / TypeScript / Python）日趋成熟
- 团队从 Airflow 迁移阻力最小（任务模型相近，DX 跨代提升）

**缺点：**

- **没有"资产/血缘"一等模型**（这是 vs Dagster 的核心差距）
  - dbt 模型可作为 flow 步骤跑，但血缘需在 Prefect UI 外查 dbt docs
- 跨 flow 数据 lineage 需自己写 metadata + 用 OpenLineage 集成
- 多租户 partition 概念较弱（无 Dagster 那种 partition keys）
- 社区比 Airflow 小，比 Dagster 大（中等）

**对 ReceptivIQ 契合度：**

- ✅ 9 ETL Adapter → 9 个 `@flow`，结构与现有 BaseAdapter 几乎平移
- ✅ AI Agent 调用（Persona / Creative / Attribution）作为 task，自带 retry / timeout / cache
- ⚠️ dbt 血缘对客户报告至关重要，需要 OpenLineage 补足（与 Airflow 同等情况）
- ✅ 团队学习曲线最低，迁移最快（预估 2-3 周 vs Dagster 5-6 周）

### 2.2 Kestra ⭐ 黑马候选

**优点：**

- 完全声明式 YAML，UI 可视编辑 + Git 同步（GitOps 友好）
- 多语言原生：Python / Shell / Node / SQL / Bash 都是一等公民，不像 Airflow 都得通过 PythonOperator
- 内置插件生态（500+）：dbt / Snowflake / Postgres / GA4 / Slack / S3 等覆盖广
- 性能强：Java + Kafka 后端，可水平扩展，社区基准比 Airflow 快 5-10×
- Web UI 现代化（React），有完整 task 日志、metrics、blueprints 库
- 多租户在 Enterprise 版（OSS 单租户，但代码隔离用 namespaces 模拟）
- 默认包含 RBAC、Secrets 管理、API 触发

**缺点：**

- YAML 主导，复杂 Python 逻辑需嵌入 `io.kestra.plugin.scripts.python.Script` 或外部脚本，**与项目"代码即真理"的 Python 风格不完全契合**
- 数据资产模型也没有（同 Prefect / Airflow）
- dbt 集成是 plugin，但不是核心血缘
- 团队需要学习全新 DSL（kestra YAML schema 不薄）
- Java 后端，运维体验与 Python 团队习惯不同
- 中文资料较少

**对 ReceptivIQ 契合度：**

- ✅ 9 ETL Adapter 包成 plugin 调用 → YAML 配置化，运营人员可改调度而无需改代码
- ⚠️ Python BaseAdapter 内部逻辑需保留在 Python 文件，Kestra 只负责调度
- ⚠️ 团队"全栈型，Python 偏好"与 Kestra 心智模型有距离
- 适合"DevOps + 数据团队"协作场景，不适合"开发主导一切"

### 2.3 Mage AI

**优点：**

- 专为数据团队设计：blocks（loader / transformer / exporter）+ pipelines，开箱即用
- 笔记本式 UI + 代码两种视图，调试体验近 Jupyter
- 原生 dbt + Snowflake + DuckDB + 9 大广告平台 connector
- Python 优先，代码即配置
- 安装一条命令：`pip install mage-ai && mage start`
- 多语言（Python / R / SQL）和 streaming 都支持

**缺点：**

- 社区相对小（虽增长快）
- 多租户原生不强，需自行隔离
- AI Agent / 后台任务调度场景不是设计核心（强于"数据 pipeline"）
- 资产血缘比 Dagster 弱
- 公司 (Mage) 近年增长 + 商业化压力，未来路线不确定

**对 ReceptivIQ 契合度：**

- ✅ ETL Pipeline 9 平台 → 用 Mage block 一对一翻译，速度最快
- ⚠️ AI Agent 调度不是强项
- ⚠️ 商业稳定性比 Dagster / Prefect 弱

### 2.4 Windmill

**优点：**

- 极轻量（Rust 后端，部署 < 100MB）
- 脚本即任务：Python / TypeScript / Go / Bash / SQL 都可作为 step
- UI 自动生成表单（每个脚本自动得 Web 触发界面）
- 性能极强（基准比 Airflow / Temporal 快 10-100×）
- 内置 secrets / variables / approvals 等企业功能
- AGPL 开源 + 商业 Enterprise 版

**缺点：**

- 不是专为数据编排设计（更像"内部工具平台 + 编排"）
- 数据生态薄弱：无原生 dbt 集成，无 Snowflake 优化
- 社区比 Prefect / Dagster 小
- AGPL 协议对部分商业场景不友好

**对 ReceptivIQ 契合度：**

- ⚠️ 调度可行，但缺少数据/dbt 一等支持，定位错配
- 适合"工具脚本 + 流程审批"场景，不适合复杂数据/AI 流水线

---

## 3. 与 Airflow / Dagster 加入综合排名

针对 ReceptivIQ 的核心需求（dbt 血缘 + 9 平台 ETL + AI Agent + 多租户 + 合规审计）：

| 排名 | 引擎                | 核心优势                                                 | 主要顾虑                                     |
| ---- | ------------------- | -------------------------------------------------------- | -------------------------------------------- |
| 🥇 1 | **Dagster**         | 资产血缘 + 多租户 partition + AI asset 可追溯 + dbt 原生 | 学习曲线 + 迁移成本                          |
| 🥈 2 | **Prefect 3**       | DX 最佳 + Python 纯净 + 迁移成本最低                     | 无资产血缘（需 OpenLineage 外挂）            |
| 🥉 3 | **Airflow**（现状） | 已部署 + 生态最大 + 沉没成本                             | DX 老旧 + 血缘弱                             |
| 4    | **Mage AI**         | 数据 pipeline 专用 + 最快上手                            | 商业稳定性 + AI agent 弱                     |
| 5    | **Kestra**          | YAML 声明 + 多语言 + UI 优秀                             | 团队 Python 习惯不契合                       |
| 6    | **Windmill**        | 极快 + 极轻                                              | 数据生态薄弱                                 |
| 7    | Flyte / Argo        | ML 流水线强 / K8s 原生                                   | 项目当前用 Docker Compose，不切换 K8s 不适用 |

---

## 4. 修订建议（覆盖 ADR-003）

**ADR-003 原结论保持：长期推荐 Dagster，短期保留 Airflow。**

**但加入"中间方案"备选：**

> 如果团队认为 Dagster 学习曲线过陡，或希望在 1-2 周内完成迁移并立刻获得 DX 提升，**Prefect 3 是次优选择**。Prefect 牺牲了 Dagster 的资产血缘原生能力，但换来更快迁移、更小心智负担、与现有 Python BaseAdapter 几乎无缝对接。
>
> 牺牲的"数据血缘"用 OpenLineage + Marquez 补足（与 Airflow 方案同等成本，约 2-3 天集成）。

### 4.1 三档路线选择

| 路线           | 引擎组合                               | 适用场景                                | 总迁移周期           |
| -------------- | -------------------------------------- | --------------------------------------- | -------------------- |
| **A. 保守**    | Airflow（保持）+ OpenLineage + Marquez | 团队精力紧、新功能优先                  | 1 周（仅加 lineage） |
| **B. 中庸** ⭐ | Prefect 3 + OpenLineage + Marquez      | 想要现代 DX 但不想深学新模型            | 3-4 周               |
| **C. 激进**    | Dagster + dagster-dbt                  | 长期数据可信度、AI 资产血缘为核心竞争力 | 5-6 周               |

### 4.2 决策辅助问题

按以下顺序回答即可定位：

1. **"客户/审计师追问数据血缘"是否会在 6 个月内常态化发生？**
   - 是 → 跳到第 2 题
   - 否 → 路线 A（Airflow 保持）

2. **团队是否愿意投入 1-2 周学习新的"资产模型"心智？**
   - 是 → 路线 C（Dagster）
   - 否 → 路线 B（Prefect 3）

3. **是否需要在 1 个月内完成迁移并见效？**
   - 是 → 路线 B（Prefect 3，最快）
   - 否 → 路线 C（Dagster，长期价值更高）

---

## 5. 结论

**没有比 Dagster 更适合 ReceptivIQ 的引擎**（在合规 + 血缘维度），但 **Prefect 3 是性价比最高的替代方案**，DX 跃迁明显且迁移最快。

其他引擎（Kestra / Mage / Windmill / Flyte / Argo）各有专长，但与项目当前定位（Python 主导、Docker Compose、营销 SaaS、合规驱动）匹配度均不及前述三者。

**实务建议**：

- 立即可做：Airflow 加 OpenLineage（路线 A），1 周内获 80% 血缘价值
- 2026 Q3 启动 Prefect 3 Spike（路线 B 备选）
- 2026 Q4 评估是否升级到 Dagster（路线 C），以"AI asset 可追溯 + 客户报告血缘"为决策依据

---

## 6. 关联文档

- [ADR-003 · Dagster vs Airflow 主决策](./ADR-003-DAGSTER-VS-AIRFLOW.md)
- [ARCHITECTURE-DIAGRAM.md](./ARCHITECTURE-DIAGRAM.md)
- [diagrams/dev-stack-layered.md](./diagrams/dev-stack-layered.md)
