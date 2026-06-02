# ReceptivIQ 技术方案包

## 1. 方案概述

ReceptivIQ 是一个面向营销代理商和品牌客户的 AI-native marketing operating platform。平台的核心目标是把市场研究、创意生成、媒体投放、归因分析和客户门户统一到一个合规、安全、可扩展的数据与 AI 架构之上。

本方案采用以下已确认的技术方向：

- 双湖数据策略：Raw PII-Segregated Lake + Processed Lake。
- Snowflake 作为核心数据仓库。
- ELT：先抽取和加载，再在 Snowflake 内完成转换。
- Core AI Brain 作为统一智能编排层。
- Persona、Creative、Attribution、Media agents 通过 Core AI Brain 统一访问数据和模型。
- 合规覆盖 GDPR、CCPA、HIPAA、SOC 2。
- 数据驻留作为 per-tenant requirement。
- Google 与 Office365 SSO 属于 post-MVP。

## 2. 双湖数据策略

| 数据层 | 作用 | 典型数据 | 访问原则 |
| --- | --- | --- | --- |
| Raw PII-Segregated Lake | 原始敏感数据隔离区 | CRM 文件、邮箱、电话、客户名单、PHI、受监管身份字段 | 租户级密钥、最小权限、强审计 |
| Processed Lake | 标准化分析数据区 | 匿名化受众、广告指标、GA4 事件、归因结果、persona 洞察 | 面向报表、AI 检索和业务分析 |

PII/PHI 从摄取阶段开始进入隔离路径，不直接进入通用 processed lake，也不默认进入 AI prompt。分析和归因所需的关联通过租户级 hash 或 tokenized join key 完成。

## 3. Snowflake 数据仓库

Snowflake 承载 processed data、canonical schema、semantic layer、AI retrieval index 和报表 mart。

推荐隔离模型：

| 租户级别 | 隔离方式 | 适用场景 |
| --- | --- | --- |
| Standard | 共享 account，tenant_id + Row-Level Security | 普通 SaaS 租户 |
| Enterprise | 独立 database/schema、role、warehouse | 企业租户 |
| Regulated | 独立 Snowflake account 或 region-bound deployment | HIPAA、强数据驻留、受监管客户 |

Snowflake zero-copy cloning 用于：

- 新租户 onboarding。
- Enterprise tenant 复制隔离环境。
- QA/UAT 环境。
- 租户复制、区域迁移和回归测试。

## 4. ELT 管道

本项目应采用 ELT。原因是 Snowflake 适合作为大规模转换执行层，且 raw/staging 数据留在仓库或隔离湖中更利于审计和回放。

标准流程：

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

关键处理：

- Normalize：统一 DV360、Meta、TikTok、The Trade Desk、GA4 等字段。
- Deduplicate：处理 API 重复页、重复文件上传、重复报表导出。
- Validate：校验字段、类型、枚举、时间窗口和 PII/PHI 安全。
- Enrich：补充 tenant/client mapping、地理、行业、受众标签和归因关系。
- Index：建立结构化索引、语义索引和 AI retrieval index。

## 5. Core AI Brain

Core AI Brain 是平台的智能中枢。

| 组件 | 作用 |
| --- | --- |
| Context Builder | 从 Snowflake 获取租户安全、角色安全、PII-safe 的上下文 |
| LLM Router | 根据任务、成本、延迟、合规要求选择模型 |
| Agent Orchestrator | 编排 Persona、Creative、Attribution、Media agents |
| Tool Executor | 执行经过授权的工具调用，写回外部平台需要人工确认 |
| Audit and Budget | 记录 prompt、模型、token、数据访问和输出 |

MVP 阶段建议采用 human-in-the-loop：AI 可以生成建议和可执行 payload，但预算调整、广告暂停、投放启动、写回外部平台等操作必须人工确认。

## 6. Agents

| Agent | 职责 |
| --- | --- |
| Persona Agent | 生成 audience blueprint、市场洞察、人群画像 |
| Creative Agent | 生成创意方向、文案、品牌语气建议 |
| Attribution Agent | 分析 touchpoint、conversion、渠道贡献和优化建议 |
| Media Agent | 监控媒体表现、预算 pacing，并提出优化建议 |

## 7. Priority 1 Integrations

| 集成 | 类型 | 主要用途 |
| --- | --- | --- |
| Experian | 数据供应商 | Mosaic、人群画像、人口统计、心理图谱 |
| TransUnion | 数据供应商 | 受众增强、身份连接、线下线上匹配 |
| Nielsen | 数据供应商 | 媒体消费、受众测量、市场 benchmark |
| Placer IQ | 位置与线下信号 | 地理、门店、区域客流和线下行为 |
| Quorum | 区域/受众信号 | 区域洞察、社区信号、市场研究 |
| DV360 | DSP | Campaign、Insertion Order、Line Item、Creative、Report |
| Meta | Paid media | Campaign、Ad Set、Ad、Insight、Pixel Event |
| TikTok | Paid media | Campaign、Ad Group、Ad、Creative performance |
| The Trade Desk | DSP | Programmatic campaign、bid、spend、conversion |
| GA4 | Analytics | Event、Session、Traffic Source、Conversion、Ecommerce |
| Tresorit | 合规文件传输 | CRM 文件、客户名单、敏感文件安全传输 |

## 8. 合规姿态

| 合规域 | 要求 |
| --- | --- |
| GDPR | 数据最小化、DSAR、删除、限制处理、数据驻留 |
| CCPA | Do Not Sell/Share、消费者访问和删除、数据分类 |
| HIPAA | PHI 隔离、最小必要访问、审计、会话超时、BAA |
| SOC 2 | 访问控制、日志、监控、变更管理、供应商管理 |

数据驻留是 per-tenant requirement。每个 tenant onboarding 时必须记录区域要求，并影响 Snowflake region、对象存储 region、备份 region 和模型处理区域。

## 9. MVP 功能柱

| Pillar | MVP 作用 |
| --- | --- |
| Market Research | 受众研究、persona blueprint、市场洞察 |
| Creative Engine | 创意概念、文案变体、品牌语气建议 |
| Media Buying | 媒体表现监控、pacing、优化建议 |
| Attribution | 多触点归因、渠道贡献、报告叙事 |
| Client Portal | 白标 dashboard、AI 摘要、报告访问、角色过滤 |

## 10. 关键依赖

| 依赖 | 影响 |
| --- | --- |
| Canonical schema | 所有集成、报表和 AI agents 的基础 |
| Tenant isolation | 多租户安全、RLS、权限、合规 |
| PII segregation | CRM transfer、AI 安全、DSAR、HIPAA |
| Snowflake role/region design | 数据驻留、企业隔离、RLS |
| Credential vault | 所有 API 集成 |
| ELT orchestration | 数据新鲜度、失败重试、监控 |
| LLM provider decision | 模型路由、成本、合规限制 |
| Media write access | Media Agent 是否可执行写回 |
| SSO | Post-MVP，Google 和 Office365 |

## 11. 推荐 MVP 顺序

1. Foundation：tenant model、PII boundary、canonical schema、Snowflake structure。
2. Secure ingestion：credential vault、Tresorit、API connector framework。
3. Priority read connectors：Experian、GA4、Meta、DV360、TikTok、The Trade Desk。
4. Processed lake and marts：campaign、audience、attribution、portal tables。
5. Core AI Brain：LLM router、context builder、audit、token budget。
6. Market Research：Persona Agent 和 audience blueprint。
7. Attribution + Client Portal。
8. Creative + Media recommendation。
9. Human-approved write-back automation。
10. Google / Office365 SSO。
