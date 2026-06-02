# 架构审计报告 · 2026 Q2

> 状态：内部架构审计 · 双轮深度排查产物
> _Last updated: **2026-05-21**_(初版 2026 Q2,本次为进度刷新版)
> 关联:[Technical Solution](./psd/technical-solution.md) · [ELT-8-STEP-DESIGN](./ELT-8-STEP-DESIGN.md) · [EXPERIAN-DATA-ROLE](./EXPERIAN-DATA-ROLE.md) · [PII-DESIGN-SOLUTION](./PII-DESIGN-SOLUTION.md) · [MULTI-TENANT-DB](./MULTI-TENANT-DB.md)
> 适用读者:技术决策者 · 架构师 · 工程经理 · 投资人 · 客户/审计师
> 一句话总结:**当前实现度 ~70%(↑ 从 50% 起步)。多租户硬隔离 + 可配置 RBAC + 审计闭环 + Frontend MVP 已落地;距 PSD 终态(3-Lake ELT + Experian + Media Agent + 合规自动化)还有约 11-13 周关键路径。**

---

## 0. 更新日志 · 2026-05-21

自初版(2026 Q2)以来已完成的关键工作:

| 类别                        | 进度            | 关键提交                                                                                                   |
| --------------------------- | --------------- | ---------------------------------------------------------------------------------------------------------- |
| **多租户物理隔离**          | 50% → **95%**   | `fa9758b` 每 Agency 独立 Postgres + TenantSessionRouter + Fernet 加密 DSN                                  |
| **审计 + RLS by client_id** | 新增            | `668b5cc` 统一 `audit_event`、`audit_logs` INSERT-only 触发器、9 张表 RLS                                  |
| **可配置 RBAC**             | 新增 → **100%** | `99caea9` + `e777d8e` 46 权限码 + 5 内置 + 自定义角色 + Shadow/Enforce + 等级守卫                          |
| **审计日志查看器**          | 新增 → **100%** | `142cd71` `/settings/audit` + `/platform/audit` + Member/Client/Event/Date 筛选                            |
| **Frontend Portal**         | 10% → **70%**   | `99d43fc` Vite+React+TS+Tailwind 完整框架 · 登录/注册 · 14+ 业务页面 · Sidebar 按 tier+permission 双段过滤 |
| **多角色 + Client 管理**    | 新增            | `a5cc7e9` `2465135` Team/Clients UI · 邀请流 · 角色矩阵 · 跨 Agency 审计                                   |
| **代码中文清理**            | 完成            | `7d197af` + `5c909d6` 所有 in-scope 代码 CJK 归零;docs/diagrams 中英双版本                                 |

**累计提交**:~25 个合并到 main · 新文件 80+ · 重构端点 90+ · 数据库迁移 022-028 共 7 个。

**新增能力(初版审计未涵盖的)**:

- 三层租户身份(Platform / Agency / Client)前后端贯通,登录页/中间页/角色/权限/审计完整闭环
- 自定义角色 + 等级守卫(rank hierarchy) — 防越权 + 合规可审计
- Tier-aware UI(平台用户继承全部 46 个权限码也只看到 Platform 工具;自动隐藏 Agency-scoped 菜单)
- 跨租户审计查看(批量 JOIN 解析 member/client/agency 名称,UUID 不再裸露)

---

## 1. Executive Summary

ReceptivIQ Platform 当前代码库**已具备生产级多租户基础**(FastAPI + 每 Agency 独立 Postgres + 46 权限码 RBAC + 完整审计闭环 + Vite/React Frontend),与初版 2026 Q2 审计相比有重大跃迁。但与 PSD 设计的**Landing-First Medallion 3-Lake 架构 + 8 步 ELT + 4 个 Pillar Agent + Experian 集成 + 14 个 P1 adapter + 完整合规自动化**之间仍存在 **约 22 项可识别缺失**(从初版 34 项已闭合 12 项),跨越数据架构、AI Brain、合规自动化、外部数据源 4 大类。

**关键判断(更新)**:

- 🟢 **多租户与权限基础完整**(从 50% 升至 ~95%)—— 每 Agency 物理库、RLS by client_id、RBAC + 等级守卫、审计不可篡改全部就位,可承接 SOC 2 / GDPR 关键控制项
- 🟢 **Frontend MVP 已上线** —— 完整登录/注册流、角色/权限/审计三大管理面、Agency/Client 双门户分流
- 🔴 **核心数据架构仍需重构** —— `raw_*` 单层 → Landing/Raw PII/Processed 三 Lake 未启动;**仍是最高优先级**
- 🔴 **Experian + Media Agent + Bedrock + 5 个 P1 adapter 仍缺失** —— 直接影响 Persona/Audience/Attribution 上限
- 🟡 **合规执行引擎仍待完善** —— 表骨架 + audit_event 已稳;DSAR / Retention / 72h 通知 cron 仍未实现

**结论**:MVP 已可服务"基础广告报表 + 完整多租户运营"场景;要交付 PSD 描述的"AI 驱动的合规多租户营销平台",**剩余 11-13 周完成 P0+P1 即可上线 V1**。

---

## 2. 评估方法

### 2.1 双轮深度排查

| 轮次        | 覆盖范围                                                                                                                                           | 发现项数    |
| ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------- | ----------- |
| **Round 1** | 7 维度：3 Lake 架构 · 8 步 ELT · 编排器 · PII Access Service · Shared Reference · AI Brain · 合规执行                                              | 20 项缺失   |
| **Round 2** | 12 维度：多租户隔离 · SSO · WebSocket · PDF · Brand Onboarding · 合规自动化 · Frontend · Observability · CI/CD · 测试 · 14 adapter · DLP/Residency | 14 项新缺失 |
| **合计**    | 19 个独立维度                                                                                                                                      | **34 项**   |

### 2.2 评分方法

每项缺失按三维度评估：

| 维度           | 标准                                                           |
| -------------- | -------------------------------------------------------------- |
| **技术可行性** | 🟢 成熟方案 / 🟡 需 POC / 🔴 高复杂度                          |
| **优先级**     | **P0**（阻塞核心架构） / **P1**（关键功能） / **P2**（优化项） |
| **工作量**     | 周为单位 · 含设计 + 实施 + 测试                                |

### 2.3 证据来源

所有缺失项**附文件路径证据**（哪个文件应该存在但不存在 · 哪个表已建但执行代码缺失）。

---

## 3. 当前实现度评分(2026-05-21 刷新)

| 维度                                 | 初版(2026 Q2) | 当前        | 关键现状                                                           | 关键差距                                                                |
| ------------------------------------ | ------------- | ----------- | ------------------------------------------------------------------ | ----------------------------------------------------------------------- |
| **多租户物理隔离**                   | 🟡 50%        | 🟢 **95%**  | 每 Agency 独立 Postgres + TenantSessionRouter + Fernet 加密 DSN    | 缺 per-Agency KMS 派生(单一全局 Fernet 密钥)                            |
| **RBAC + 等级守卫**                  | —             | 🟢 **100%** | 46 权限码 + 5 内置 + 自定义角色 + rank hierarchy + Shadow/Enforce  | 完成                                                                    |
| **审计日志(写入 + 不可篡改 + 查看)** | 🟡 30%        | 🟢 **95%**  | `audit_event` 统一入口 · UPDATE/DELETE 触发器拒绝 · 跨租户查看器   | 缺 CloudTrail / 长期归档 export                                         |
| **RLS by client_id**                 | —             | 🟢 **100%** | 9 张 client_id 表 ENABLE + FORCE RLS + GUC 注入                    | 完成                                                                    |
| **Frontend / Portal**                | 🔴 10%        | 🟢 **70%**  | Vite+React+TS+Tailwind · 登录/注册 · 14+ 业务页 · 双段过滤 Sidebar | 缺数据真实接入(部分 stub)· Client Portal 仅骨架 · 白标 brand_color 应用 |
| **SSO & Auth**                       | 🟡 70%        | 🟡 **85%**  | Google OAuth · JWT · 限流 · `role_label/role_rank` 返回            | 缺 Office 365 SSO                                                       |
| **三 Lake 仓库架构**                 | 🔴 15%        | 🔴 **15%**  | 仅 `raw_*` 单层                                                    | **未启动**:Landing / Raw PII / Processed 三层 schema                    |
| **ELT 八步管道**                     | 🟡 55%        | 🟡 **55%**  | STEP 1/4/5 OK                                                      | STEP 2/3/8 仍缺;STEP 6/7 部分                                           |
| **PII Access Service**               | 🔴 20%        | 🔴 **20%**  | 单体内零散实现                                                     | 仍缺独立 service + 6 operation allow-list                               |
| **Shared Reference + Experian**      | 🔴 5%         | 🔴 **5%**   | 几乎从零                                                           | 全部待补;Experian 合同需先签                                            |
| **AI Brain & Agents**                | 🟡 60%        | 🟡 **60%**  | 3/4 Agent · 4/6 组件                                               | 缺 Media Agent + Tool Executor + Memory & Retrieval + Bedrock           |
| **合规自动化**                       | 🟡 50%        | 🟡 **65%**  | 表骨架完整 · audit_event 已稳                                      | DSAR / Retention / 72h 通知 cron 仍缺                                   |
| **WebSocket 通知**                   | 🟢 80%        | 🟢 **80%**  | /ws 端点 + agency_id 隔离                                          | 部分通知类型未接                                                        |
| **PDF 报表**                         | 🟢 90%        | 🟢 **90%**  | weasyprint + Celery 完整                                           | 白标参数硬编码                                                          |
| **Brand/Field/Historical**           | 🟡 70%        | 🟢 **90%**  | 后端 + Frontend 表单都在                                           | 数据真实回流可再校验                                                    |
| **Observability**                    | 🟡 60%        | 🟡 **65%**  | Sentry + Langfuse + 结构化 audit 日志(stdout)                      | 缺 CloudTrail · 应用日志聚合                                            |
| **CI/CD & Infra**                    | 🔴 30%        | 🔴 **30%**  | docker-compose 在                                                  | 仍缺 GitHub Actions · IaC · 备份策略                                    |
| **测试覆盖**                         | 🟡 40%        | 🟡 **40%**  | pytest 文件覆盖核心                                                | 缺 RLS 跨租户 · 性能基准 · dbt tests · RBAC 测试                        |
| **14 P1 adapter**                    | 🟡 64%        | 🟡 **64%**  | 8 个已实现                                                         | 缺 Trade Desk · Tresorit · Experian · TransUnion · Nielsen · Placer IQ  |
| **数据驻留 + DLP**                   | 🔴 5%         | 🔴 **5%**   | 无 region 配置                                                     | 缺 per-tenant region binding · DLP scanner · `forbid_pii_columns`       |
| **总体**                             | **🟡 ~50%**   | **🟢 ~70%** | 多租户与权限基础完整 · 数据架构待重构                              | **距 PSD 终态约 11-13 周(P0+P1)**                                       |

---

## 4. 缺失项完整清单（34 项）

### 4.1 🔴 P0 缺失（阻塞核心架构 · 12 项）

| #         | 维度     | 缺失项                                                                               | 影响                                                                    | 工作量                    | 文件路径证据                                                            |
| --------- | -------- | ------------------------------------------------------------------------------------ | ----------------------------------------------------------------------- | ------------------------- | ----------------------------------------------------------------------- |
| **P0-1**  | 3 Lake   | **Landing Lake schema**（`landing.<source>_records`）                                | 原始数据无 immutable 着陆点；不满足 GDPR Art. 5 / SOC 2                 | 1 周                      | `infra/migrations/019_landing_schema.sql`（缺）                         |
| **P0-2**  | 3 Lake   | **Raw PII Lake 3 张表**（`raw_secure.users` + `*_pii_fields` + `pii_access_log`）    | 当前 `raw_*` 直写 = 整条 record 进 PII Lake = 过度分类 = 违反数据最小化 | 1 周                      | `backend/app/core/warehouse_client.py` 仅有 raw\_\* 白名单              |
| **P0-3**  | 3 Lake   | **Processed Lake 重构**（`processed.raw.<source>_records`）                          | 非 PII 数据无独立 Lake                                                  | 0.5 周                    | dbt models 缺 raw/ 层                                                   |
| **P0-4**  | 3 Lake   | **record_id (UUID v7) + pii_token 体系**                                             | 跨 Lake 无关联键；DSAR 主体定位困难；跨源去重失败                       | 1 周                      | `backend/app/core/pii_token.py`（缺）+ ETLRunner 改造                   |
| **P0-5**  | ELT      | **STEP 3 Load 原子双写改造**（替代直写 raw\_\*）                                     | 当前单层 ETL；不符合 Landing-First 设计                                 | 2 周                      | `backend/app/services/etl/runner.py` 重构 + `field_classifier.py`（新） |
| **P0-6**  | ELT      | **STEP 2 Classify**：`field_classification_manifest` + L0/L1/L2/L3 4 级              | STEP 2 无独立产物；合规审计无证据                                       | 1 周                      | audit schema + classifier 服务（缺）                                    |
| **P0-7**  | ELT      | **sync_state 表 + cursor 续抓持久化**                                                | 重抓时无法防重复；浪费 API 配额                                         | 0.5 周                    | `infra/migrations/0XX_sync_state.sql`（缺）                             |
| **P0-8**  | dbt      | **缺 raw 层 + ai_context 层**（当前 3 层 → 应 5 层）                                 | AI Context Builder 无召回源                                             | 1.5 周                    | `dbt/models/raw/` + `dbt/models/ai_context/`（缺）                      |
| **P0-9**  | Experian | **Experian Combined API adapter**                                                    | Persona/Audience/Attribution 模块缺画像基础                             | 2 周                      | `backend/app/services/etl/adapters/experian.py`（缺）                   |
| **P0-10** | Experian | **Experian 5 张落表**（hygiene / identity / attributes / segments / pii_access_log） | 同上                                                                    | 0.5 周                    | migrations + dbt models（缺）                                           |
| **P0-11** | Experian | **dim_field_codes 字典 + Mosaic 段定义**（B 类共享数据）                             | 无法解释 raw_value 含义                                                 | 1 周（含合同等待 + 入库） | `dbt/models/shared/experian/`（缺）                                     |
| **P0-12** | Frontend | **Agency Portal + Client Portal 双门户骨架**                                         | 客户看不到任何 UI                                                       | 4-6 周                    | `frontend/src/` 骨架空                                                  |

**P0 合计工作量**：~15-18 周（部分并行可压到 10-12 周）

### 4.2 🟡 P1 缺失（关键功能 · 15 项）

| #         | 维度        | 缺失项                                                      | 影响                                           | 工作量             |
| --------- | ----------- | ----------------------------------------------------------- | ---------------------------------------------- | ------------------ |
| **P1-1**  | PII Service | **PII Access Service 独立化 + 6 operation allow-list**      | 不满足合规"唯一受控出口"原则                   | 2 周               |
| **P1-2**  | AI Brain    | **Media Agent**（4 Pillar Agent 缺第 4 个）                 | 媒介采买优化能力缺失                           | 1.5 周             |
| **P1-3**  | AI Brain    | **Tool Executor**（AI Brain 6 组件之一）                    | Agent 无法调用工具 / 写回                      | 1 周               |
| **P1-4**  | AI Brain    | **Memory & Retrieval**（含 pgvector）                       | 无长期记忆 / 上下文召回                        | 1.5 周             |
| **P1-5**  | AI Brain    | **AWS Bedrock HIPAA Gateway**                               | HIPAA 客户 LLM 路径不合规（OpenRouter 无 BAA） | 1 周               |
| **P1-6**  | 合规        | **DSAR 自动工作流**（Step Functions 或 Celery FSM）         | 当前仅手动 API；GDPR 30 天 SLA 风险            | 1.5 周             |
| **P1-7**  | 合规        | **Retention 自动 purge 引擎**                               | retention_policies 表已建但无执行              | 1 周               |
| **P1-8**  | 合规        | **72h/60d Breach 通知自动 Celery task**                     | 通知 SLA 风险                                  | 0.5 周             |
| **P1-9**  | 合规        | **sub_processor_notifications 表 + 30 天通知**              | GDPR DPA 要求                                  | 0.5 周             |
| **P1-10** | dbt         | **DLP macro `forbid_pii_columns`**                          | 无法持续扫描防 PII 渗漏 Processed              | 0.5 周             |
| **P1-11** | 多租户      | **per-Agency KMS key 派生**（当前单一 Fernet key）          | 跨 Agency 加密未隔离；不满足 KMS rotation      | 1.5 周             |
| **P1-12** | Auth        | **JWT scope 分级**（guest/user/admin）                      | 权限粒度不够细                                 | 0.5 周             |
| **P1-13** | CI/CD       | **GitHub Actions 工作流**（test/build/deploy）              | 部署手动；回归风险                             | 1 周               |
| **P1-14** | Adapter     | **TikTok / Trade Desk / StackAdapt 媒介补齐**（部分已实现） | 媒介覆盖不全                                   | 1 周（视已有进度） |
| **P1-15** | 测试        | **RLS 跨租户隔离测试 + dbt tests**                          | 多租户安全无回归保证                           | 1 周               |

**P1 合计工作量**：~16 周（部分可并行）

### 4.3 🟢 P2 缺失（优化项 · 7 项）

| #        | 维度                  | 缺失项                                                    | 工作量                          |
| -------- | --------------------- | --------------------------------------------------------- | ------------------------------- |
| **P2-1** | UUID                  | UUID v7（当前 v4）                                        | 0.5 周                          |
| **P2-2** | 编排器                | Dagster Asset Graph 评估迁移（当前 Airflow + Celery）     | 评估 1 周 + 迁移 4-6 周（可选） |
| **P2-3** | Shared Reference Lake | 平台级独立 Neon project + license_grants RLS              | 1.5 周                          |
| **P2-4** | Adapter               | Tresorit / TransUnion / Nielsen / Placer IQ 补齐          | 2-3 周                          |
| **P2-5** | Auth                  | Office 365 / Entra ID SSO（post-MVP）                     | 1 周                            |
| **P2-6** | 数据驻留              | per-tenant region binding 配置 + agency.brand region 字段 | 1 周                            |
| **P2-7** | Observability         | CloudTrail 集成 + 应用日志聚合（ELK/Datadog）             | 1.5 周                          |

**P2 合计工作量**：~9-15 周（视范围）

---

## 5. 各维度细分缺失（按文件路径定位）

### 5.1 三 Lake 仓库架构 🔴

| 缺失                  | 应该有的文件 / 表                                                                             |
| --------------------- | --------------------------------------------------------------------------------------------- |
| Landing Lake schema   | `infra/migrations/019_landing_schema.sql` · `landing.<source>_records` · `landing.sync_state` |
| Raw PII Lake schema   | `raw_secure.users` · `raw_secure.<source>_pii_fields` · `raw_secure.pii_access_log`           |
| Processed Lake raw 层 | `processed.raw.<source>_records`（dbt source）                                                |
| pii_token helper      | `backend/app/core/pii_token.py`（含 `compute_pii_token` / `verify_token`）                    |
| 跨 Lake 关联          | `record_id` (UUID v7) 字段在所有表                                                            |

### 5.2 ELT 八步管道 🟡

| 步骤               | 状态            | 缺失                                                                   |
| ------------------ | --------------- | ---------------------------------------------------------------------- |
| STEP 1 Extract     | ✅ 9/14 adapter | 缺 Experian / TransUnion / Nielsen / Placer IQ / Tresorit / Trade Desk |
| STEP 2 Classify    | ❌              | `field_classifier.py` + `field_classification_manifest` 表             |
| STEP 3 Load        | ❌              | 原子双写改造（替代直写 raw\_\*）                                       |
| STEP 4 Normalize   | ✅              | dbt staging 已有                                                       |
| STEP 5 Deduplicate | 🟡              | 缺 content_hash UNIQUE 约束 + audit 行数指纹                           |
| STEP 6 Validate    | 🟡              | 缺 quarantine schema + DLP macro                                       |
| STEP 7 Enrich      | 🟡              | 缺 Shared Reference Lake JOIN + Experian enrichment                    |
| STEP 8 Index       | ❌              | 缺 `dbt/models/ai_context/` + pgvector                                 |

### 5.3 PII Access Service 🔴

| 缺失                      | 应该有的                                                                                                                                                            |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 独立 container            | `services/pii-access/` 目录 · stateless FastAPI · tmpfs noexec                                                                                                      |
| 6 个 operations           | `build_audience_hash_list` · `dsar_locate_subject` · `dsar_export_subject` · `liveramp_resolve` · `legal_export` · `send_notification` · **`experian_enrich_list`** |
| Purpose-bound JWT         | scoped claim · ≤ 15 min TTL · 与 operation 一一映射                                                                                                                 |
| `pii_access_log` 行级审计 | 含 actor / purpose / rows_decrypted / output_fingerprint / external_response_id                                                                                     |

### 5.4 AI Brain 6 组件 🟡

| 组件               | 状态                                                 |
| ------------------ | ---------------------------------------------------- |
| Context Builder    | ✅ `build_shared_context()`                          |
| LLM Router         | 🟡 仅 OpenRouter（缺 Bedrock 路由分支 + HIPAA flag） |
| Agent Orchestrator | 🟡 中心分发（缺 token 预算 + Langfuse 完整追踪）     |
| Tool Executor      | ❌ 目录空                                            |
| Memory & Retrieval | ❌ 无 vector DB / 记忆层                             |
| Audit & Cost       | ✅ TokenUsage + audit_logs                           |

### 5.5 4 Pillar Agent 🟡

| Agent             | 状态        |
| ----------------- | ----------- |
| Persona Agent     | ✅          |
| Creative Agent    | ✅          |
| Attribution Agent | ✅          |
| **Media Agent**   | ❌ 完全缺失 |

### 5.6 Frontend Portal 🔴

| 模块                  | 状态                                            |
| --------------------- | ----------------------------------------------- |
| frontend/src/ 骨架    | 🟡 仅空目录（apps/components/hooks/store 全空） |
| Agency Portal         | ❌ 无                                           |
| Client Portal         | ❌ 无                                           |
| RBAC 前端消费         | ❌                                              |
| 白标 brand_color 应用 | ❌                                              |
| WebSocket 客户端      | ❌                                              |

### 5.7 合规自动化 🟡

| 项                 | 表状态                              | 执行代码状态                |
| ------------------ | ----------------------------------- | --------------------------- |
| DSAR               | ✅ dsar_requests 表                 | ❌ 手动 API；无自动工作流   |
| Retention          | ✅ retention_policies 表            | ❌ 无 purge 引擎            |
| Breach 通知        | ✅ breach_incidents 表              | ❌ 无 72h/60d 自动触发      |
| Consent            | ✅ consent_records 表               | 🟡 部分用                   |
| BAA 追踪           | ✅ business_associate_agreements 表 | ✅ 完整                     |
| Sub-processor 通知 | ❌ 表缺                             | ❌ 全缺                     |
| API cost quota     | 🟡 TokenUsage 部分                  | ❌ per-Agency 月度 quota 缺 |

### 5.8 CI/CD & Infrastructure 🔴

| 项                   | 状态                                 |
| -------------------- | ------------------------------------ |
| `.github/workflows/` | ❌ 完全缺失                          |
| Render / Coolify IaC | ❌ 无 Terraform / Pulumi             |
| Neon Terraform       | ❌ `infra/terraform/neon*.tf` 不存在 |
| 备份策略             | ❌ pg_dump / Neon branching 无 IaC   |
| Docker Compose       | ✅                                   |

### 5.9 测试覆盖 🟡

| 类型               | 状态                             |
| ------------------ | -------------------------------- |
| pytest 单元测试    | 🟡 20 个文件，覆盖率不明         |
| RLS 跨租户隔离测试 | ❌ 仅 test_campaigns.py 部分覆盖 |
| 性能基准测试       | ❌ 无                            |
| dbt tests          | ❌ `dbt/tests/` 不存在           |
| 端到端集成测试     | 🟡 部分                          |

### 5.10 14 P1 Adapter 完整性 🟡

| Adapter                                                                             | 状态            |
| ----------------------------------------------------------------------------------- | --------------- |
| GA4 · Meta Ads · HubSpot · DV360 · StackAdapt · LeadRX · LiveRamp · Quorum · TikTok | ✅ 9 个         |
| **Trade Desk · Tresorit · Experian · TransUnion · Nielsen · Placer IQ**             | ❌ 6 个完全缺失 |
| BaseAdapter 框架                                                                    | ✅              |

---

## 6. 推荐补齐路径（14-16 周）

```
Week  1-3 · P0 基础设施
  • 三 Lake schema 迁移（Landing / Raw PII / Processed）
  • record_id (UUID v7) + pii_token helper
  • sync_state 表 + cursor 持久化
  • ETLRunner 原子双写改造
  • field_classifier + L0/L1/L2/L3 4 级分类

Week  4-6 · P0 dbt 5 层 + Experian
  • dbt raw/ + ai_context/ 层
  • DLP macro forbid_pii_columns
  • Experian adapter + 5 张表 + dim_field_codes 字典
  • Experian Field Code Dictionary 入库

Week  7-9 · P1 服务化 + AI 完善
  • PII Access Service 独立容器化 + 6 operation
  • Media Agent + Tool Executor + Memory & Retrieval
  • AWS Bedrock HIPAA 路由

Week 10-11 · P1 合规自动化
  • DSAR Step Functions 工作流
  • Retention 自动 purge 引擎
  • 72h/60d Breach 通知 Celery task
  • sub_processor_notifications 表

Week 12-14 · P1 Frontend Portal + CI/CD
  • Agency Portal 骨架（dashboard / campaigns / personas / reports）
  • Client Portal（RLS-aware · 白标支持）
  • WebSocket 客户端 + 通知中心
  • GitHub Actions（test / build / deploy）

Week 15-16 · P2 优化 + 验收
  • per-Agency KMS 派生
  • 6 个剩余 adapter（Trade Desk / TransUnion 等）
  • RLS 跨租户测试 + 性能基准
  • 端到端验收 + 合规审计预演（SOC 2 / HIPAA / GDPR）
```

**关键依赖关系**：

- P0-9/10/11（Experian）依赖 **合同签字 + 字典文件**（建议 Week 0 启动谈判，6-8 周交付期）
- P0-12（Frontend）可与 P0 后端工作**并行**（Week 1-12）
- P1-2/3/4（AI Brain 补完）依赖 P0-1/2/3（Lake 架构）完成
- P1-6/7/8（合规自动化）依赖 P0-1/2（数据架构稳定）

---

## 7. 风险与缓解

| 风险                                      | 概率 | 影响  | 缓解                                                                  |
| ----------------------------------------- | ---- | ----- | --------------------------------------------------------------------- |
| Lake 架构重构破坏现有 ETL                 | 中   | 🔴 高 | 双写过渡期（保留旧 raw\_\*）+ shadow run + 数据对账 1 周              |
| Experian 合同延迟（30-90 天）             | 高   | 🔴 高 | Week 0 立刻启动合同；Phase 0-2 用 mock dictionary 跑通集成            |
| Frontend 工作量被低估                     | 高   | 🟡 中 | 复用 shadcn/ui + Tailwind 模板；先 MVP（dashboard + campaigns）再扩展 |
| Media Agent + Tool Executor 设计未成型    | 中   | 🟡 中 | 先做 spike POC（1 周）验证模式                                        |
| HIPAA 客户审计 / BAA 谈判延期             | 中   | 🟡 中 | 非 HIPAA 客户先上线（Phase 1-4 即可）；HIPAA 走 Phase 5+              |
| 14-16 周时间表过紧                        | 高   | 🔴 高 | 优先级严格 P0 > P1 > P2；P2 项可推至 V2                               |
| 团队学习曲线（Dagster · Neon · dbt 5 层） | 中   | 🟡 中 | 培训 + Phase 0 spike + Anthropic / Neon 官方资源                      |

---

## 8. 关键决策点（需 stakeholder 拍板）

在启动补齐工作前，需要明确以下 **5 个核心决策**：

| #      | 决策                                                   | 选项                                                                           | 影响                  |
| ------ | ------------------------------------------------------ | ------------------------------------------------------------------------------ | --------------------- |
| **D1** | 是否**重构数据架构**（Landing-First Medallion）？      | A. 全面重构（推荐） · B. 增量加层 · C. 保持现状                                | 决定整个 P0 路径      |
| **D2** | 编排器**是否切换 Dagster**？                           | A. 保 Airflow + Celery · B. 切 Dagster（推荐 · 见 ELT-ORCHESTRATION-PRIORITY） | 影响 Phase 2-3 工作量 |
| **D3** | **Experian 合同**何时启动？                            | A. 立即（推荐） · B. Phase 4 前 · C. 延后                                      | 决定 P0-9 是否阻塞    |
| **D4** | **PII Access Service** 独立 container vs 单体 module？ | A. 独立 container（推荐 · 合规友好） · B. 单体内 module（成本低）              | 影响 P1-1 工作量      |
| **D5** | **Frontend** 何时启动？                                | A. 与后端并行（推荐） · B. 后端完成后 · C. 用第三方 BI 工具替代                | 决定上线时间表        |

---

## 9. 实施建议

### 9.1 立即可启动（Week 0）

1. **合同先行**：Experian Combined API MLA 谈判（60-90 天交付期）
2. **决策评审**：召集架构师 + 产品 + 合规 review 5 个决策点
3. **团队培训**：Dagster / Neon multi-project / dbt 5 层架构
4. **基线测量**：跑现有覆盖率 / 性能基准，确认起点

### 9.2 短期产出（Week 1-3）

- ADR-004 "3-Lake migration plan"
- ADR-005 "Frontend tech stack & layout"
- 已合并的 P0-1/P0-2/P0-3 schema 迁移 PR
- 基线 pytest 单元测试增加（pii_token / field_classifier 覆盖）

### 9.3 中期里程碑（Week 4-9）

- **Week 6**：Landing → Raw PII / Processed 双写端到端跑通
- **Week 9**：Experian adapter + PII Access Service 端到端 enrichment 成功

### 9.4 上线节奏（Week 10-16）

- **Week 13**：合规自动化（DSAR / Retention / 72h）就绪 · 可承接非 HIPAA 客户
- **Week 16**：Frontend Portal Beta + 端到端合规审计预演 · SOC 2 Type II 控制矩阵证据采集完成

---

## 10. 总结(2026-05-21 刷新)

> **当前 ReceptivIQ Platform 处于"功能性 MVP 70% 完成 · 多租户与权限基础已生产级 · 数据架构与外部数据源待补"的状态。** 多租户硬隔离(每 Agency 独立 Postgres)、46 权限码 RBAC、自定义角色与等级守卫、不可篡改审计 + 跨租户查看器、Frontend MVP 全部就位。剩余工作集中在**数据架构(Landing-First 三 Lake)、Experian 等外部源、Media Agent + AI Brain 补全、合规执行 cron**。
>
> **推荐剩余 11-13 周 P0+P1 路径** —— 见 [§11 Next Steps](#11-next-steps--自-2026-05-21-起的优先级建议) 的 6 个工作流(Workstream)。**Week 0 立即启动:Experian 合同谈判 + 数据架构 ADR 拍板**,是后续工作不阻塞的关键。
>
> 完成后,平台将真正满足 PSD 描述的"AI 驱动的合规多租户营销平台"愿景,**可承接 SOC 2 Type II / HIPAA BAA / GDPR / CCPA 全面审计**,并具备**对 Agency 的差异化价值**(小 Agency 也用得起 Experian 等顶级数据源)。

---

## 11. Next Steps · 自 2026-05-21 起的优先级建议

按交付价值 + 解锁顺序排列,**6 个并行 Workstream**。括号内为预计工作日数。

### Workstream A · Landing-First 三 Lake 数据架构(P0,5-6 周)

> 阻塞 Experian 集成与合规审计 — **必须先做**。

| 步骤 | 交付物                                                                       | 备注                                                              |
| ---- | ---------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| A1   | 写 ADR-004 "3-Lake migration plan",评审通过                                  | 1 周;锁定 record_id (UUID v7)、pii_token 算法、schema 切分边界    |
| A2   | `infra/migrations/029_landing_schema.sql` + `030_raw_pii_schema.sql`         | Landing / Raw PII / Processed 三 schema 落地;FK + RLS 同步设计    |
| A3   | `backend/app/core/pii_token.py`(compute / verify)+ `record_id` 入 21 张主表  | 反查关键;影响 dbt staging 模型                                    |
| A4   | `ETLRunner` 原子双写改造 — Landing → Raw PII + Processed                     | 替代当前直写 `raw_*`;shadow run 验证                              |
| A5   | `field_classifier.py` + `field_classification_manifest` 表(L0/L1/L2/L3 4 级) | STEP 2 独立产物;合规审计证据                                      |
| A6   | dbt 从 3 层 → 5 层:`dbt/models/{raw, ai_context}/` 新增                      | 含 `forbid_pii_columns` macro;ai_context 为 pgvector embedding 源 |

### Workstream B · Experian Combined API + 共享参考数据(P0,3-4 周;含合同等待)

> 与 A 部分并行 — 合同先行可避免阻塞。

| 步骤 | 交付物                                                                       | 备注                      |
| ---- | ---------------------------------------------------------------------------- | ------------------------- |
| B1   | Experian Combined API MLA 合同(60-90 天交付)                                 | **Week 0 立即启动谈判**   |
| B2   | `backend/app/services/etl/adapters/experian.py` + `dim_field_codes` 字典入库 | 含 Mosaic 段定义          |
| B3   | 5 张落表(hygiene / identity / attributes / segments / pii_access_log)        | 加密入 Raw PII Lake       |
| B4   | dbt `shared/experian/` 模型 + `processed.shared_experian_attributes`         | License-gated RLS         |
| B5   | Persona / Audience / Attribution Agent 接入 Experian enrichment              | 提升 ICP 命中率与归因质量 |

### Workstream C · PII Access Service 独立化(P1,2 周)

> 合规"唯一受控出口"原则;放在 Experian 之后(B5 依赖此 service 做 enrich_list)。

| 步骤 | 交付物                                                                                                                                 |
| ---- | -------------------------------------------------------------------------------------------------------------------------------------- |
| C1   | `services/pii-access/` 独立 FastAPI · tmpfs · purpose-bound JWT ≤ 15min                                                                |
| C2   | 6 operation allow-list: `audience_hash` / `dsar_locate` / `dsar_export` / `liveramp_resolve` / `legal_export` / `experian_enrich_list` |
| C3   | `pii_access_log` 行级审计 + DLP 出口扫描                                                                                               |

### Workstream D · 合规自动化 cron 引擎(P1,2 周)

> 表骨架早已就位,只缺执行;落地后可承接 SOC 2 审计。

| 步骤 | 交付物                                                                         |
| ---- | ------------------------------------------------------------------------------ |
| D1   | DSAR 自动工作流(Step Functions 或 Celery FSM)— 30 天 SLA 计时与状态机          |
| D2   | Retention 自动 purge 引擎(读 `retention_policies` 表,按 occurred_at 归档/删除) |
| D3   | 72h / 60d Breach 通知 Celery task — 触发条件 + 模板邮件 + audit 留痕           |
| D4   | `sub_processor_notifications` 表 + 30 天 advance notice 自动发                 |

### Workstream E · AI Brain 完整 6 组件 + 4 Pillar Agent(P1,3 周)

> 数据架构(A)就绪后启动。

| 步骤 | 交付物                                                                        |
| ---- | ----------------------------------------------------------------------------- |
| E1   | **Media Agent** 落地(第 4 Pillar)— 媒介采买优化 + 预算分配                    |
| E2   | **Tool Executor** — Agent 工具调用网关(write-back + side-effect 审计)         |
| E3   | **Memory & Retrieval** — pgvector embedding + Context Builder 召回路径        |
| E4   | **AWS Bedrock HIPAA Gateway** — `LLM_ROUTER_MODE=bedrock` 分支;HIPAA 客户专用 |

### Workstream F · 上线就绪 + 收尾(P1+P2,2-3 周,并行)

> 与上述并行,确保 V1 可上线。

| 步骤 | 交付物                                                                                        |
| ---- | --------------------------------------------------------------------------------------------- |
| F1   | `.github/workflows/` CI/CD(pytest + npm build + docker build + Render deploy)                 |
| F2   | **per-Agency KMS 派生**(单一 Fernet → 每 Agency 独立密钥;与 `db_dsn` Fernet 列对齐)           |
| F3   | RLS 跨租户集成测试 + RBAC 边界测试 + dbt tests                                                |
| F4   | Frontend 数据真实接入(Personas / Creatives / Campaigns / Reports 全部 wire 到真实端点)        |
| F5   | Client Portal 白标 brand_color 应用(从骨架到生产可用)                                         |
| F6   | 6 个剩余 adapter:Trade Desk · Tresorit · TransUnion · Nielsen · Placer IQ · (Trade Desk 优先) |

### 11.0 Week-by-Week 推荐节奏

```
Week  1     · A1 ADR-004 · B1 Experian 合同启动 · F1 GitHub Actions
Week  2-3   · A2 三 Lake schema · A3 record_id + pii_token · F2 per-Agency KMS
Week  4-5   · A4 ETLRunner 双写 · A5 field_classifier · F3 跨租户 / RBAC 测试
Week  6     · A6 dbt 5 层 + DLP macro 验证 · 数据对账
Week  7-8   · B2-B5 Experian adapter + 落表 + dbt + Agent 接入
Week  9     · C1-C3 PII Access Service 独立化(依赖 B 完成)
Week 10-11  · D1-D4 合规自动化 cron(DSAR / Retention / 72h)
Week 12-13  · E1-E4 Media Agent + Tool Executor + Memory + Bedrock
Week 12-13  · F4-F5 Frontend 数据接入 + Client Portal 白标(并行)
Week 14+    · F6 剩余 adapter · 端到端验收 · SOC 2 控制矩阵证据采集
```

**关键里程碑**:

- **Week 6** 三 Lake 端到端跑通 + DLP 验证 ✅
- **Week 9** Experian + PII Access Service 端到端 enrichment 成功 ✅
- **Week 11** 合规自动化全套 ready,可承接非 HIPAA 客户 ✅
- **Week 13** Frontend 数据真实闭环 + AI 完整 ✅
- **Week 14+** V1 上线,SOC 2 / HIPAA / GDPR / CCPA 全面审计就绪 ✅

### 11.1 优先级速读(给 stakeholder)

| 维度        | 必做(P0,11 周内)                                                                      | 建议(P1)                                       | 可延后(P2)                       |
| ----------- | ------------------------------------------------------------------------------------- | ---------------------------------------------- | -------------------------------- |
| 数据架构    | 三 Lake schema · record_id + pii_token · ETLRunner 双写 · field_classifier · dbt 5 层 | DLP macro                                      | UUID v4 → v7 升级                |
| 外部数据    | Experian Combined API + 字典                                                          | Trade Desk · Tresorit                          | TransUnion · Nielsen · Placer IQ |
| AI Brain    | —                                                                                     | Media Agent · Tool Executor · Memory · Bedrock | —                                |
| 合规        | —                                                                                     | DSAR / Retention / 72h / sub_processor cron    | per-tenant region · CloudTrail   |
| 多租户/安全 | —                                                                                     | per-Agency KMS 派生                            | Office 365 SSO                   |
| 基础设施    | GitHub Actions CI                                                                     | RLS + RBAC 测试                                | Dagster 评估 · IaC · 备份策略    |
| Frontend    | —(MVP 已上)                                                                           | 数据真实接入 · Client Portal 白标              | —                                |

---

## 附录 A · 缺失项快速索引

```
P0 (12 项 · 阻塞)
├─ 数据架构 (4): Landing schema · Raw PII 3 表 · Processed raw 层 · pii_token 体系
├─ ELT (3):     双写改造 · field_classifier · sync_state
├─ dbt (1):     raw + ai_context 层
├─ Experian (3): adapter · 5 张落表 · 字典 + Mosaic
└─ Frontend (1): Agency + Client Portal 双门户

P1 (15 项 · 关键)
├─ PII Service (1): 独立化 + 6 operation
├─ AI Brain (4):    Media Agent · Tool Executor · Memory · Bedrock
├─ 合规 (4):        DSAR 工作流 · Retention purge · 72h 通知 · sub_processor
├─ 数据质量 (1):    DLP macro
├─ 多租户 (1):      per-Agency KMS
├─ Auth (1):        JWT scope
├─ CI/CD (1):       GitHub Actions
├─ Adapter (1):     TikTok/TTD/StackAdapt 补齐
└─ 测试 (1):        RLS + dbt tests

P2 (7 项 · 优化)
├─ UUID v7
├─ Dagster 迁移评估
├─ Shared Reference Lake 独立 project
├─ 4 个剩余 adapter (Tresorit/TransUnion/Nielsen/Placer IQ)
├─ Office 365 SSO
├─ Per-tenant region binding
└─ CloudTrail + 日志聚合
```

## 附录 B · 关联文档

- [Technical Solution (CN)](./psd/technical-solution.md) · [(EN)](./psd/technical-solution-en.md)
- [ELT-8-STEP-DESIGN](./ELT-8-STEP-DESIGN.md)
- [EXPERIAN-DATA-ROLE](./EXPERIAN-DATA-ROLE.md)
- [PII-DESIGN-SOLUTION](./PII-DESIGN-SOLUTION.md)
- [ELT-ORCHESTRATION-PRIORITY](./ELT-ORCHESTRATION-PRIORITY.md)
- [ADR-002 Neon Tenancy](./ADR-002-NEON-TENANCY-OPTIMAL.md)
- [ADR-003 Dagster vs Airflow](./ADR-003-DAGSTER-VS-AIRFLOW.md)
- 架构图：[Network Diagram](./psd/network-diagram.svg) · [Architecture Schema](./psd/architecture-schema.svg) · [Prod Stack](./diagrams/prod-stack-layered.svg) · [Dev Stack](./diagrams/dev-stack-layered.svg)
- features 目录：16 个模块的 COMPLETION.md
