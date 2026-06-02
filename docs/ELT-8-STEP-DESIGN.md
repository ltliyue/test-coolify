# ELT 八步管道设计（Greenfield · 2026 最佳实践）

> 状态：架构设计书 + 实施路线图
> 关联：[Technical Solution §5](./psd/technical-solution.md) · [§3.6 Lifecycle](./psd/technical-solution.md#36-原始数据生命周期与处理后分区raw-data-lifecycle--post-processing-division) · [ELT-ORCHESTRATION-PRIORITY](./ELT-ORCHESTRATION-PRIORITY.md) · [PII-DESIGN-SOLUTION](./PII-DESIGN-SOLUTION.md) · [ADR-002 Neon](./ADR-002-NEON-TENANCY-OPTIMAL.md)
> 视角：**"如果今天从零开始建，应该怎么建"**——按 2026 业内最佳实践设计每一步的组件、模式、合规属性与交付节奏。非 gap-analysis。

---

## 1. Executive Summary

ReceptivIQ 的数据底座采用 **ELT 八步管道**（Extract → Classify → Load → Normalize → Deduplicate → Validate → Enrich → Index）—— 不是传统 ETL，而是"原始数据先完整落仓库、再在仓库内转换"的现代模式。

**核心架构**：**Landing-First 3-Lake Medallion**（Bronze Landing · 🔴 Raw PII · 🟢 Processed），落地于 **per-Agency Neon Postgres project**，由 **Dagster OSS**（Asset Graph + dagster-dbt）编排，**dbt 5 层**完成仓库内 Normalize/Dedup/Validate/Enrich/Index。明文 PII 由独立 **PII Access Service** 受控出口（purpose-bound JWT ≤ 15min），共享参考数据（Experian / Nielsen 等）由平台级 Shared Reference Lake 经 license-gated FDW 暴露。

**关键技术选型**：Dagster + Neon + dbt + dlt + Fernet + pgvector + AWS Step Functions（审批）。

**交付节奏**：Phase 0-5 共 **11-15 周**完成 MVP；Phase 6（HIPAA BAA / 性能调优）按客户合同节奏。所有八步**满足 GDPR Art.32/25/17 + HIPAA §164.312/308 + CCPA §1798.81.5 + SOC 2 Type II CC6**——合规约束在 schema constraint / dbt test / encryption / RLS / audit 5 个层面**编码到架构内**，而非事后补丁。

---

## 2. 设计原则（8 项）

| 原则                               | 含义                                                                        | 在八步中的体现                                           |
| ---------------------------------- | --------------------------------------------------------------------------- | -------------------------------------------------------- |
| **Landing-First**                  | 原始数据先完整落盘、永不丢字段（Bronze 层 immutable 保留）                  | STEP 3 整条 record 写 Landing Lake                       |
| **Field-level Classification**     | 字段级分级（L0/L1/L2/L3）而非记录级——避免对整条 record 过度分类             | STEP 2 输出 `field_classification_manifest`              |
| **Immutable & Auditable**          | 落盘即不可变；所有读写写 INSERT-only audit                                  | STEP 1-8 全程 `audit_events` · 6 年保留                  |
| **Idempotent by Design**           | 多次重跑不重复入库；任一步骤可幂等重放                                      | STEP 1 cursor + STEP 5 content-hash + business-key MERGE |
| **PII Isolation by Hard Boundary** | PII 走独立 Neon project + KMS + VPC + mTLS；Processed Lake 仅持 `pii_token` | STEP 3 双写 Raw PII Lake；Processed Lake 永无明文 PII    |
| **dbt-Centric Transform**          | 仓库内 dbt 5 层（raw → staging → canonical → marts → ai_context）           | STEP 4-8 全部 dbt 模型 + dagster-dbt 原生集成            |
| **Asset Lineage First**            | 编排器原生数据血缘——DSAR / SOC 2 审计 UI 直接交付                           | Dagster Asset Graph 自动追踪 dbt model 到 raw 表         |
| **Composable Compliance**          | 合规嵌入架构而非事后补丁                                                    | PII Boundary + Audit + Retention + DSAR 跨步骤强制       |

**为什么是这 8 原则**：每一条都直接对应一个合规法规要求（GDPR Art. 25 "Privacy by Design" → Field-level Classification + Hard Boundary；HIPAA §164.312 → Immutable & Auditable；SOC 2 CC6.6 → Hard Boundary）。架构师无须额外补丁就能拿到 SOC 2 attestation。

---

## 3. 推荐技术栈

| 层                     | 推荐选型                                                                              | 替代方案                 | 关键理由                                                                                              |
| ---------------------- | ------------------------------------------------------------------------------------- | ------------------------ | ----------------------------------------------------------------------------------------------------- |
| **编排器**             | 🟪 **Dagster OSS**                                                                    | Apache Airflow           | Asset Graph 原生血缘 + dagster-dbt 一等集成 + Code Location per-region (HIPAA) + per-Agency Partition |
| **辅助调度**           | 🟧 **AWS Step Functions**                                                             | Temporal                 | 仅用 Media Agent 写回审批 + DSAR 长流程（人工 approve）；不替代主调度                                 |
| **仓库**               | 🟦 **Neon Postgres**                                                                  | Snowflake                | Serverless · per-Agency project 物理隔离 · git-style branching（零拷贝克隆）· scale-to-zero 闲置租户  |
| **Connector 框架**     | 🟩 **dlt (data load tool, OSS)** + 自研 BaseAdapter                                   | Airbyte / Fivetran       | dlt 提供 cursor / schema evolution / dedup 基础；BaseAdapter 控制 PII 路径                            |
| **Transform**          | 🟦 **dbt Core** + dagster-dbt                                                         | Native SQL / Apache Beam | dbt model = Dagster asset 自动血缘；dbt tests 即 asset checks                                         |
| **PII 检测**           | 🟥 **自研 PHI Detector（HIPAA 18 标识符）+ Microsoft Presidio (OSS) fallback**        | AWS Comprehend           | 自研保留路由控制；Presidio 兜底 50+ 实体类型                                                          |
| **字段级加密**         | 🟨 **Fernet (AES-128-CBC + HMAC) · per-Agency KMS** + AWS KMS                         | AES-256-GCM              | Python `cryptography` 库成熟；每 Agency 独立 master key                                               |
| **向量索引**           | 🟪 **pgvector**（Neon 原生）                                                          | Pinecone / Weaviate      | 与 Processed Lake 同 Neon project；无跨服务调用；HNSW 索引                                            |
| **PII Access Service** | 🟥 **独立 stateless container（FastAPI · tmpfs noexec · purpose-bound JWT ≤ 15min）** | AWS Lambda + API Gateway | 受控明文出口的唯一路径；6 个 operation allow-list                                                     |
| **审计**               | 🟨 INSERT-only `audit_events` 表 + Langfuse（LLM 调用）+ CloudTrail（AWS）            | Datadog / Splunk         | Postgres 表自带备份；Langfuse 专攻 LLM；CloudTrail 满足 AWS 合规                                      |
| **DSAR / Retention**   | 🟧 **Step Functions 工作流 + Dagster sensor**                                         | 自定义 Airflow DAG       | Step Functions 原生 human-approval；Dagster sensor 触发                                               |

**为什么 Dagster 而非 Airflow**：见 [ELT-ORCHESTRATION-PRIORITY](./ELT-ORCHESTRATION-PRIORITY.md)——血缘 / 多租户 / dbt 集成 / Python-native 4 维领先。Airflow 作为团队熟悉度兜底，二者代码可并存（dagster-airflow 适配器）。

**为什么 Neon 而非 Snowflake**：见 [ADR-002](./ADR-002-NEON-TENANCY-OPTIMAL.md)——per-Agency 独立 project 是开箱即用的物理隔离；标准 Postgres 协议；scale-to-zero 显著降低多租户成本。Snowflake 在 100 GB+ 单表 backfill 场景仍可作为辅助（由 Dagster 调用 Glue Job）。

---

## 4. 八步逐项设计

每一步统一以 **6 段式**呈现：职责 / 输入 输出 / 组件 设计模式 / 合规属性 / Idempotent 保证 / 失败处理。

### 4.1 STEP 1 · Extract（抽取）

**职责**：按 cursor 从外部源拉取增量数据。

**输入 / 输出**：

- 输入：外部 API / SFTP / Tresorit 加密文件
- 输出：内存中的 raw record 流（**未持久化**——等 STEP 2/3 完成后原子双写）

**推荐组件 / 设计模式**：

- **dlt** (data load tool) 提供 schema evolution / state management / cursor pagination 基础
- 自研 `BaseAdapter` 子类（每个 P1 源一个）实现 `fetch(start, end, cursor) → (records, next_cursor)`
- **Credential Vault**：AWS Secrets Manager + per-Agency 加密上下文；ELT 服务账号仅能取自己 tenant 的 secret
- **Cursor 持久化**：`sync_state` 表 `(source, scope_id, last_cursor, last_run_at)`；Dagster Partition 二级保险

**合规属性**：

- 凭证存储：满足 SOC 2 CC6.1（认证 + 授权）
- TLS 1.3 出站：满足 HIPAA §164.312(e) Transmission security
- Audit：每次 Extract run 写 `audit_events` (actor=service / purpose=extract / source / records_fetched)

**Idempotent 保证**：cursor 续抓——下次 run 从 `last_cursor` 之后开始；同 cursor 不重复抓。

**失败处理**：指数退避（1s/2s/4s）· 最大 3 次重试 · 第 4 次失败 → Sentry 告警 + Dagster asset 标 `failed` + 不推进 cursor（下次 run 重试同段）。

---

### 4.2 STEP 2 · Classify（字段级分类）

**职责**：对每条 record 的**每个字段**打数据分级标签（L0 / L1 / L2 / L3），输出 `field_classification_manifest`，作为 STEP 3 双写决策依据。

**输入 / 输出**：

- 输入：STEP 1 内存 record 流
- 输出：`audit.field_classification_manifest` 行（一字段一行：`source / record_id / field_name / class / detector / decision_at`）

**推荐组件 / 设计模式**：

- 自研 `backend/app/core/compliance/field_classifier.py`：基于字段名启发式（`email` / `phone` / `ssn` / `dob`）+ 内容正则
- **PHI Detector**（自研）：HIPAA Safe Harbor 18 类标识符
- **Microsoft Presidio** (OSS) fallback：50+ 实体类型（NRIC / IBAN / 信用卡 / 医保号等），catch 自研未覆盖的
- **分级定义**：
  - L0 Public：campaign_id · ad_set_id · creative_name
  - L1 Internal：spend · impressions · clicks · account_id
  - L2 PII：email · phone · IP · full_name · address
  - L3 PHI：health_condition · diagnosis · prescription（HIPAA 客户场景）

**合规属性**：

- 满足 GDPR Art. 25 "Privacy by Design"——分级是后续硬隔离的前提
- L3 命中触发 PHI Detector 双扫描 + 立即 `audit_event: phi_detected` 告警

**Idempotent 保证**：纯函数——同一条 record 多次分类得到同一 manifest。

**失败处理**：分类器异常 → record 整体进 quarantine（保守安全态，不进任一 Lake）+ alert。

---

### 4.3 STEP 3 · Load（双写 · Landing-First）

**职责**：按 STEP 2 manifest，在**同一原子事务**内写三处：Landing Lake（完整 record）+ Raw PII Lake（PII 字段）+ Processed Lake（非 PII 字段）。

**输入 / 输出**：

- 输入：STEP 1 record 流 + STEP 2 manifest
- 输出：
  - 🟫 `landing.<source>_records`：整条原始 record · PII 列 Fernet 加密 · 非 PII 列明文 · `record_id` UUID v7
  - 🔴 `raw_secure.users`：主体维表 UPSERT（`email_encrypted` / `phone_encrypted` / `email_hash` / `phone_hash` / `pii_token`）
  - 🔴 `raw_secure.<source>_pii_fields`：源 PII 字段抽取（含 `record_id` 反查键）
  - 🟢 `processed.raw.<source>_records`：非 PII 字段 + `pii_token` + `record_id` + `ingest_metadata`

**推荐组件 / 设计模式**：

- 原子事务跨 schema：Postgres 单事务可跨 schema；跨 Neon project 用 **两阶段提交**（dlt 内建）+ 失败回滚
- **关联键体系**：
  - `record_id = UUID v7`（timestamp-prefixed，可按时间排序，跨 Lake 反查）
  - `pii_token = SHA-256(lower(email) + agency_salt)` —— 不可逆 hash，跨 Lake JOIN 不破坏 PII Boundary
- 加密：Python `cryptography.Fernet` + per-Agency KMS-derived master key

**合规属性**：

- 满足 GDPR Art. 32 (Security of processing)：字段级加密 + 独立密钥 + 跨 trust boundary
- 满足 HIPAA §164.312(a) Access Control + §164.310 Physical safeguards：3 个独立 Neon project = 3 个 trust boundary
- 满足 SOC 2 CC6.6：物理隔离（独立 endpoint + 存储集群）+ 程序隔离（service account 最小权限）

**Idempotent 保证**：

- `record_id` 在 STEP 1 生成（UUID v7）；同源数据多次 Load 不会产生重复 `record_id`
- `content_hash = SHA-256(canonical_field_subset)`；表上 `UNIQUE(tenant_id, source, content_hash)` 阻挡重复

**失败处理**：原子事务保证三处全成功或全回滚；中间状态不存在。事务失败 → record 进 `quarantine.<source>` + audit_event。

---

### 4.4 STEP 4 · Normalize（字段标准化）

**职责**：跨 14 个源的异构 schema 映射到统一 canonical 命名规范（snake_case · UTC 时间 · UUID id · ISO 4217 货币 · IANA 时区）。

**输入 / 输出**：

- 输入：`processed.raw.<source>_records`（STEP 3 派生 B）
- 输出：`staging.stg_<source>`（30 天中间产物 · dbt incremental model）

**推荐组件 / 设计模式**：

- **dbt staging models**（`dbt/models/staging/stg_<source>.sql`）—— 每源一个模型
- **dbt yaml + macros**：字段映射规则（`source_field → canonical_field`）声明式定义
- 类型对齐：所有 id → UUID；所有 timestamp → `TIMESTAMPTZ UTC`；所有金额 → `NUMERIC(18,4)`
- dbt model 标注 `materialized='incremental'` + `unique_key='record_id'`

**合规属性**：

- 满足 GDPR 数据最小化原则——staging 仅保留分析所需字段
- DLP 持续扫 `staging.*`：发现 PII 模式 = P0 告警（检测 STEP 3 是否泄漏）

**Idempotent 保证**：dbt incremental + `unique_key=record_id`——同 record 多次 build 不重复行。

**失败处理**：dbt run 失败 → Dagster 标 asset failed → 不推进下游 STEP 5；不影响其他源（每源独立 asset）。

---

### 4.5 STEP 5 · Deduplicate（5 层防重复）

**职责**：覆盖 5 类重复场景：① API 增量重复 ② 文件重复上传 ③ 多 report 重复 ④ 跨平台同 entity ⑤ 内部回滚后重抓。

**输入 / 输出**：

- 输入：`staging.stg_<source>`
- 输出：`canonical.<entity>`（13 Canonical Entities · 3 年）

**推荐组件 / 设计模式 · 5 层防重复**：

| 层                        | 机制                                                                                           | 实施位置             |
| ------------------------- | ---------------------------------------------------------------------------------------------- | -------------------- |
| ① **Cursor 续抓**         | 从 `last_cursor` 之后抓，避免重抓历史段                                                        | STEP 1（已防）       |
| ② **Content Hash UNIQUE** | `content_hash = SHA-256(canonical_field_subset)`；表 `UNIQUE(tenant_id, source, content_hash)` | STEP 3 存储层        |
| ③ **Business-key MERGE**  | dbt incremental + `unique_key=business_key`（如 `campaign_id + date + platform`）              | STEP 5 dbt model     |
| ④ **Source 刷新周期**     | B 类共享数据按供应商节奏（Experian 月）；A 类 5 min 最小间隔                                   | STEP 1 调度          |
| ⑤ **行数审计指纹**        | 每批记 `(source, new_count, skipped_count, run_id)` 到 audit_events                            | STEP 5 dbt post-hook |

**合规属性**：

- 数据质量是 SOC 2 CC1.4 "Demonstrates a commitment to integrity" 的核心
- 审计指纹（⑤）作为审计师抽样核查的证据

**Idempotent 保证**：5 层叠加——任一层失效另一层兜底；多次执行最终 canonical 状态一致。

**失败处理**：dbt merge conflict（理论不应出现，但作为防御）→ 记录冲突到 `audit.dedup_conflicts` + 不阻塞下游。

---

### 4.6 STEP 6 · Validate（校验）

**职责**：Schema 校验 + 业务规则 + DLP 扫描（防 PII 渗漏到 Processed）。

**输入 / 输出**：

- 输入：`canonical.<entity>`
- 输出：通过 → 进 STEP 7；失败 → `quarantine.<entity>` + alert

**推荐组件 / 设计模式**：

- **dbt tests**：`not_null` · `unique` · `accepted_values` · `relationships`（行业标配）
- **dbt asset checks**（Dagster 集成）：业务规则——`spend >= 0` · `event_date <= now()` · `currency IN ISO 4217` · `timezone IN IANA`
- **DLP macro `forbid_pii_columns`**（自研）：扫描 `processed.*` schema 下所有表的 string 列，匹配 email/phone/SSN 正则；命中 = P0 告警
- **Quarantine schema**：`quarantine.<entity>` 隔离失败行，保留原始字段 + 失败原因，不阻塞主链路

**合规属性**：

- 满足 GDPR Art. 5(1)(d) 数据准确性——dbt test 是行业标准
- DLP 是合规审计师**强问的问题**："如何防止 PII 流出 PII Lake？"——本步是技术答案

**Idempotent 保证**：dbt test 纯检查，不修改数据；多次跑结果一致。

**失败处理**：行级失败 → quarantine + alert；模型级失败 → Dagster 标 asset failed + 阻塞下游 + 通知 on-call。

---

### 4.7 STEP 7 · Enrich（富集）

**职责**：cross-source JOIN + 第三方画像 + Shared Reference Lake 联表 → 业务可用的 marts 报表层。

**输入 / 输出**：

- 输入：`canonical.<entity>` + `shared_*` (FDW)
- 输出：`marts.<report>`（campaign_performance · attribution · persona_signals · funnel · 等 · 3 年 / 财务 7 年）

**推荐组件 / 设计模式**：

- **dbt mart models**——每个业务报表一个模型
- **pii_token JOIN**：跨 Lake unified user 实体（仅 hash，无明文）
- **Shared Reference Lake JOIN**：postgres_fdw + `license_grants` RLS（如 Experian 画像 JOIN——见 PSD §3.5）
- **第三方 enrichment**：LiveRamp / TransUnion 通过 PII Access Service 触发（不直接在 dbt 内调外部 API）

**合规属性**：

- 满足 GDPR Art. 25——所有 enrichment 经 pii_token 不可逆 hash，明文 PII 不出 PII zone
- License gating（RLS）确保 Agency 仅看授权数据源

**Idempotent 保证**：dbt incremental + unique_key；上游不变则下游不变。

**失败处理**：FDW 不可达 → enrichment 字段标 `NULL` + audit_event；不阻塞 mart 主流程。

---

### 4.8 STEP 8 · Index（索引）

**职责**：结构化索引（B-tree / GIN）+ 全文索引（pg_trgm）+ 语义索引（pgvector embeddings）—— 为 Core AI Brain Context Builder 提供召回源。

**输入 / 输出**：

- 输入：`marts.<report>`
- 输出：`ai_context.*`（1 年 · pgvector embeddings + summary text · segment 级二次脱敏）

**推荐组件 / 设计模式**：

- **dbt + Python post-hook**：调 OpenRouter Claude Sonnet 生成 segment-level summary → 写 `ai_context.<entity>_summary`
- **pgvector embeddings**：OpenAI `text-embedding-3-small` (1536 dim) 或本地 BGE 模型；写 `ai_context.<entity>_vec` 表 (id, vec vector(1536), metadata jsonb)
- **HNSW 索引**：`CREATE INDEX ... USING hnsw (vec vector_cosine_ops)` 加速召回
- **物化视图**：按 (tenant_id, date) 分区，提速租户查询
- **segment 级二次脱敏**：所有 pii_token 在 ai_context 内**二次聚合到 segment**（如 "高价值受众段 v2"），不暴露 individual hash

**合规属性**：

- 满足 GDPR Art. 25——AI prompt 永不消费明文 PII
- 满足 HIPAA §164.514 De-identification—— segment 级聚合
- DLP 持续扫 ai_context：发现 PII 模式 = P0 + 自动 truncate

**Idempotent 保证**：embedding 模型确定性 + dbt incremental——同输入同输出。

**失败处理**：OpenRouter 不可达 → fallback to local BGE 模型；embedding 失败行进 quarantine；不阻塞 marts 数据交付。

---

## 5. 横切设计要素

### 5.1 3-Lake Medallion 实施

**Neon 3 project per Agency**（landing / raw-pii / processed），每个 project 独立 KMS master key + 独立 VPC subnet。Landing 与 Raw PII 位于同一 PII trust boundary（同等访问控制），与 Processed Lake 之间设硬 PII Boundary（粗红虚线 · mTLS · DLP 持续扫描）。

Shared Reference Lake 作为**平台级第 4 个 project**，无个体 PII；通过 postgres_fdw + license_grants RLS 映射到各 Agency Processed Lake 的 `shared.*` schema。

**Terraform 模块**：`infra/terraform/neon_agency.tf`（per-Agency 3 project + KMS）+ `infra/terraform/neon_shared.tf`（平台级 1 project）。

---

### 5.2 record_id + pii_token 体系

**record_id = UUID v7**（timestamp-prefixed）——跨 Lake 反查同一原始 record；按时间排序友好；Postgres `uuid_v7()` 扩展或应用层生成。

**pii_token = SHA-256(lower(email) + agency_salt)**——不可逆 hash · per-Agency salt 隔离 · Processed Lake / canonical / marts 持此 token 做跨表 JOIN · 跨 Agency 因 salt 不同而无法关联（**保留 Agency 隔离 + 允许 Agency 内分析**）。

**helper**：`backend/app/core/pii_token.py` 暴露 `compute_pii_token(email, agency_id) -> bytes` · `verify_token(token, email, agency_id) -> bool`。

---

### 5.3 Shared Reference Lake

**单点摄取**：平台 master credential 调供应商 API（Experian / Nielsen / Placer IQ / Quorum）单次写入 Shared Reference Lake 的 `shared_*` schema。

**license-gated 暴露**：

- `license_grants(agency_id, source, valid_until, contract_id)` 表
- postgres*fdw 把 shared*\* 映射到 Agency Processed Lake
- FDW view 上挂 RLS：`USING (current_setting('app.agency_id') IN (SELECT agency_id FROM license_grants WHERE source = '...'))`

**节省**：单 Experian license $80k-200k/年；50 Agency × N 次摄取变 1 次平台级摄取，license + 存储成本降 70-90%。

---

### 5.4 PII Access Service

**独立 stateless container**（FastAPI · tmpfs noexec · 部署 Render Web Service / AWS Fargate）。

**6 个 operation allow-list**（不暴露通用 SQL）：

1. `build_audience_hash_list(audience_id, platform)` → Meta CA / DV360 / TikTok / TTD / StackAdapt 上传
2. `dsar_locate_subject(email_or_phone)` → 主体定位
3. `dsar_export_subject(subject_id, format)` → DSAR JSON 包
4. `liveramp_resolve(seed_list_id)` → IDR
5. `legal_export(subject_id, case_id)` → 法律请求
6. `send_notification(subject_id, template_id)` → SMTP / SMS

**安全属性**：明文绝不落盘（tmpfs）· purpose-bound JWT ≤ 15 min · 行级 audit · per-Agency KMS context · 不与 Processed Lake / AI Brain 互联。

---

## 6. 合规映射（4 法规 × 8 步）

| 法规 / 条款                                  | 关键要求                              | 在哪些 STEP 强制      | 强制机制                                                   |
| -------------------------------------------- | ------------------------------------- | --------------------- | ---------------------------------------------------------- |
| **GDPR Art. 32** Security of processing      | 加密 · 最小权限 · 访问控制 · 定期测试 | STEP 1 / 3 / 8        | Fernet 字段加密 + per-Agency KMS + DLP 扫描 + 季度 pentest |
| **GDPR Art. 25** Privacy by Design           | 默认最小数据                          | STEP 2 / 3 / 7 / 8    | 字段级分类 + 双写隔离 + ai_context segment 级脱敏          |
| **GDPR Art. 17** Right to erasure            | 30 天内响应删除                       | STEP 1-8（DSAR 触发） | PII Access Service `dsar_locate_subject` + 删除 hook       |
| **HIPAA §164.312(a)** Access control         | 唯一标识 · 加密 · 自动登出            | STEP 1 / 3            | 服务账号 + Fernet + session timeout                        |
| **HIPAA §164.312(e)** Transmission security  | 传输加密                              | STEP 1 / 3            | TLS 1.3 + mTLS 跨 Lake                                     |
| **HIPAA §164.308** Administrative safeguards | Workforce clearance + 6 年审计        | STEP 1-8              | RBAC + INSERT-only `audit_events` 6y                       |
| **HIPAA §164.310** Physical safeguards       | 物理访问控制                          | STEP 3 / 5            | 3 个独立 Neon project = 等价物理边界                       |
| **CCPA §1798.81.5** Reasonable security      | 加密 + 访问控制 + 销毁规程            | 同 GDPR Art. 32       | 同上 + retention 引擎                                      |
| **CCPA §1798.105** Right to delete           | 45 天内响应                           | DSAR 路径             | 同 GDPR Art. 17                                            |
| **SOC 2 CC6.1** Logical access               | 认证 + 授权 + 监控                    | STEP 1-8              | JWT + purpose-bound scope + audit_events                   |
| **SOC 2 CC6.6** Logical/physical access      | 边界保护 + 网络分段                   | STEP 3                | VPC subnet + mTLS + 拒绝跨 trust boundary                  |
| **SOC 2 CC6.7** Restricted transmission      | 传输加密 + 数据分级                   | STEP 1 / 3 / 8        | TLS 1.3 + L0/L1/L2/L3 分级 + 出口控制                      |

**审计师视角**：上表的每一行都可在代码 / DDL / 配置中找到对应实现；这是 SOC 2 Type II 期望的"控制矩阵证据采集"标准模式。

---

## 7. 6 阶段实施路线图（greenfield）

| 阶段                                                | 周期   | 目标                                                  | 主要交付                                                                                                                                                                                                                     | 验证方法                                                                                                           |
| --------------------------------------------------- | ------ | ----------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| **Phase 0 · Foundation**                            | 1-2 周 | Bootstrap 基础设施 + CI/CD                            | Terraform 基线（Neon 3 project + AWS Secrets Manager + KMS）· GitHub Actions CI/CD · Dagster + Postgres skeleton · 首个 dbt project · 1 个 hello-world Dagster asset · 1 个 dbt model                                        | `dagster dev` + `dbt build` 全绿；`terraform plan` 无差异                                                          |
| **Phase 1 · Landing + Identifier**                  | 1-2 周 | record_id + pii_token + Landing schema + audit_events | `landing.<source>_records` 表 schema · `pii_token` helper · `sync_state` 表 · `audit_events` 表 · `content_hash UNIQUE` 约束                                                                                                 | pytest 单元测试 + 集成测试（同源 2 次抓 → 第 2 次 0 入库 + audit 行级证据）                                        |
| **Phase 2 · Extract + Classify + Load**             | 3 周   | 八步前 3 步落地 + 14 个 P1 adapter                    | dlt + BaseAdapter 框架 · 14 个 adapter（Meta / DV360 / TikTok / TTD / StackAdapt / GA4 / HubSpot / Experian / TransUnion / Nielsen / Placer IQ / Quorum / Tresorit / LiveRamp）· `field_classifier.py` · 原子双写 ETL Runner | 端到端：Meta API 拉 1000 条 → 3 表验证字段拆分 + record_id 关联 + pii_token 不可逆 + 跨 Agency salt 不同           |
| **Phase 3 · dbt 5 层 Transform**                    | 3 周   | STEP 4-8 全部落地                                     | dbt models 5 层：`raw.*` / `staging.*` / `canonical.*` (13 entities) / `marts.*` (4 reports) / `ai_context.*` (pgvector embeddings) + 全套 dbt tests + DLP macro `forbid_pii_columns`                                        | `dbt build` 全绿 + DLP 扫 Processed 命中 0 PII + Dagster Asset Graph UI 可视化血缘 + ai_context 表有 1536-dim 向量 |
| **Phase 4 · Shared Reference + License Gating**     | 1-2 周 | B 类共享数据架构                                      | 平台级 Neon project · `license_grants` 表 · postgres_fdw 配置 · dbt shared models（Experian / Nielsen / Placer IQ / Quorum）· License API                                                                                    | RLS 测试：无 license Agency 查 `shared_experian` → 0 行；有 license → 真实数据 + audit_event                       |
| **Phase 5 · PII Access Service + DSAR + Retention** | 2-3 周 | 受控明文出口 + 自动化合规执行                         | 独立 container `services/pii-access/`（FastAPI · tmpfs）· 6 operation allow-list · retention 引擎（cron 按法规清理）· DSAR Step Functions 工作流                                                                             | DSAR 模拟请求 30d 内自动响应 + retention 按计划 purge + audit_events 行级证据 + PII Access Service 渗透测试        |

**总周期**：11-15 周完成 Phase 0-5（MVP 可上线 standard 客户）。

**Phase 6+ 可选**（不计入 MVP 关键路径）：

- HIPAA BAA 客户上线（AWS Bedrock + Anthropic BAA · region binding）
- 性能调优（HNSW 索引 tuning · Neon compute size）
- Dagster Cloud 升级（≥ 10 Agency / ≥ 8 团队规模）
- Snowflake 辅助（如需 100 GB+ 单表 backfill）

---

## 8. 验证 / 测试策略

| 测试层             | 范围                                                                                            | 工具 / 命令                                               |
| ------------------ | ----------------------------------------------------------------------------------------------- | --------------------------------------------------------- |
| **单元测试**       | `pii_token` helper · `field_classifier` · cursor 续抓 · content_hash 唯一性                     | pytest + coverage ≥ 90%                                   |
| **集成测试**       | 端到端 ELT run → Landing / Raw PII / Processed.raw 三表行数 + record_id JOIN + pii_token 不可逆 | docker-compose 起 3 Neon-like Postgres + pytest           |
| **dbt 测试**       | 所有 dbt model 的 schema / business rule                                                        | `dbt build` + `dbt test`（含 `forbid_pii_columns` macro） |
| **合规测试**       | DLP 扫 Processed → 0 PII；DSAR 模拟 30d；retention 模拟 6 年后 purge                            | 专用 `tests/compliance/` suite · 模拟时间 freezegun       |
| **性能基准**       | 单 Agency 100 万行 Meta data 端到端 < 30 min；Dagster Asset Graph 1000 asset 加载 < 5s          | locust + pytest-benchmark                                 |
| **跨租户隔离测试** | Agency A 的 pii_token 在 Agency B 数据无意义；FDW 跨 Agency 不可达                              | 2 个 Agency fixture + 显式 cross-tenant 查询尝试          |

**自动化频率**：单元 / 集成 / dbt 测试在每个 PR 跑；合规 / 性能 / 跨租户测试每周 nightly 跑；季度 pentest 由外部团队执行。

---

## 9. 风险与缓解

| 风险                                               | 概率 | 影响 | 缓解                                                                                                                  |
| -------------------------------------------------- | ---- | ---- | --------------------------------------------------------------------------------------------------------------------- |
| Neon serverless cold-start 影响首请求延迟          | 中   | 中   | 热点 Agency 启用 always-on compute · 首请求 SLO ≤ 3s · pgbouncer 连接池                                               |
| dbt 5 层（含 ai_context + pgvector）首次实现复杂度 | 中   | 高   | Phase 3 留 buffer · 先 ai_context Schema POC 跑通再 scale · 用 OSS embedding 模型降本                                 |
| Dagster 团队学习曲线（Asset 心智）                 | 中   | 中   | Dagster University 培训（免费）· Phase 0 spike 验证团队接受度 · 失败可回退 Airflow                                    |
| Shared Reference Lake License 合同延迟             | 中   | 低   | Phase 4 可推到合同签订后 · 不阻塞 Phase 0-3 · 用 mock 数据先做集成测试                                                |
| PII Access Service 微服务化运维负担                | 中   | 中   | 先单体内 module 化 · 规模到位（≥ 10 Agency）再拆 container · 复用现有 FastAPI 鉴权层                                  |
| 14 个 P1 adapter 工作量被低估                      | 高   | 高   | dlt 框架复用 · 分批交付（Phase 2 先 3 核心：Meta / GA4 / HubSpot） · 小众源（Quorum / Tresorit）可推迟到 Phase 4+     |
| HIPAA BAA 与 OpenRouter 不兼容                     | 高   | 高   | LLM Router 默认 OpenRouter · HIPAA 客户强制 AWS Bedrock + Anthropic BAA · 在 LLM Router 加 tenant.hipaa_flag 路由分支 |

---

## 10. 引用与延伸阅读

**PSD 主体**：

- [psd/technical-solution.md §3 数据策略](./psd/technical-solution.md) — 3-Lake Medallion 设计
- [psd/technical-solution.md §5 ELT Pipeline](./psd/technical-solution.md) — 八步管道原始定义
- [psd/technical-solution.md §3.6 Lifecycle](./psd/technical-solution.md) — 4 阶段生命周期

**关键决策与 ADR**：

- [ELT-ORCHESTRATION-PRIORITY.md](./ELT-ORCHESTRATION-PRIORITY.md) — Dagster vs Airflow 选型
- [PII-DESIGN-SOLUTION.md](./PII-DESIGN-SOLUTION.md) — PII 边界设计
- [ADR-002-NEON-TENANCY-OPTIMAL.md](./ADR-002-NEON-TENANCY-OPTIMAL.md) — Neon 多租户
- [ADR-003-DAGSTER-VS-AIRFLOW.md](./ADR-003-DAGSTER-VS-AIRFLOW.md) — 编排引擎主决策

**可视化**：

- [psd/network-diagram.svg](./psd/network-diagram.svg) — 网络数据流图
- [psd/architecture-schema.svg](./psd/architecture-schema.svg) — 架构方案图

**释义文档**：

- [psd/network-diagram-explained.md](./psd/network-diagram-explained.md)
- [psd/architecture-schema-explained.md](./psd/architecture-schema-explained.md)
- [diagrams/env-stack-glossary.md](./diagrams/env-stack-glossary.md)

---

## 附录：关键术语索引

| 术语                              | 定义                                                                                      |
| --------------------------------- | ----------------------------------------------------------------------------------------- |
| **record_id**                     | UUID v7 · 跨 Lake 同一 record 反查键                                                      |
| **pii_token**                     | SHA-256(lower(email) + agency_salt) · 不可逆 hash · 跨 Lake JOIN 主键                     |
| **Landing Lake (Bronze)**         | per-Agency Neon project · 整条原始 record · immutable · STEP 3 着陆点                     |
| **Raw PII Lake**                  | per-Agency Neon project · 仅 PII 字段抽取 · PII Access Service 出口源                     |
| **Processed Lake**                | per-Agency Neon project · 非 PII 字段 + pii_token · dbt 5 层                              |
| **Shared Reference Lake**         | 平台级 Neon project · B 类共享参考数据 · license-gated FDW                                |
| **PII Access Service**            | 独立 stateless container · 受控明文 PII 出口 · 6 operation allow-list · purpose-bound JWT |
| **Cursor / Watermark**            | sync_state 表持久化 last_cursor · 增量续抓                                                |
| **content_hash**                  | SHA-256(canonical_field_subset) · 表上 UNIQUE 约束 · 防重复入库                           |
| **field_classification_manifest** | STEP 2 输出 · 每字段一行 (record_id / field_name / class) · STEP 3 双写决策依据           |
