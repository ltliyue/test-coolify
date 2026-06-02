# Experian 接口清单(MVP)

> _Last updated: **2026-05-20**_
>
> **背景**:developer.experian.com 公开的产品目录约 117 个,其中绝大多数面向信贷/决策/欺诈/车辆等场景,**与 B2C 营销无关**。本文档已剔除全部不相关项目,只保留**对 ReceptivIQ 平台真正有用的 7 个接口家族**——其中 2 个进入 MVP,5 个登记为 Phase 2+ 备选(每个均有明确的触发条件)。
>

---

## 0. 官方入口(便于客户/法务同步核对)

| 类别                   | 入口                              |
| ---------------------- | --------------------------------- |
| 全球开发者门户         | https://developer.experian.com/   |
| Aperture(数据质量平台) | https://docs.experianaperture.io/ |

> 具体 endpoint 路径与计费 SKU **以客户合同 + Experian CSM 提供的最终文档为准**。

---

## 0a. 营销相关接口总览(共 7 类,已筛选信贷/B2B/车辆等无关项)

| #   | 接口家族                            | MVP 决策    | 触发条件 / 备注                                | 详见                                            |
| --- | ----------------------------------- | ----------- | ---------------------------------------------- | ----------------------------------------------- |
| 1   | **Combined API(`ue-ov`)**           | ✅ MVP      | 已上线,复核授权范围 + 月度配额                 | [§1](#1-combined-api-ue-ov-现状基线复核-)       |
| 2   | **Suppression Files**               | ✅ MVP      | 合规硬门槛;未签 = Audience Export 不能上线     | [§2](#2-suppression-files--mvp-合规硬门槛-p0)   |
| 3   | Universal Enrichment(UE)独立调用    | 📋 Phase 2+ | Combined API 月度配额触顶,需要拆分计费         | [§3.1](#31-universal-enrichmentue独立调用)      |
| 4   | Address Hygiene(Cleanse + Validate) | 📋 Phase 2+ | F-14 CSV 导入匹配率 < 阈值                     | [§3.2](#32-address-hygiene地址清洗)             |
| 5   | Email / Phone Hygiene               | 📋 Phase 2+ | Audience Export 目标平台 match rate < 60%      | [§3.3](#33-email--phone-hygiene联系方式质检)    |
| 6   | TrueTouch Communication Preferences | 📋 Phase 2+ | Media Agent 进入自动化渠道选择阶段             | [§3.4](#34-truetouch-communication-preferences) |
| 7   | Health & Wellness Segments(HIPAA)   | 📋 Phase 2+ | 签署 BAA + 启动 HIPAA Lane(医疗/保险/制药客户) | [§3.5](#35-health--wellness-segmentshipaa)      |

**已筛选项**(与平台场景关系不大,不登记):

- OV 独立调用 — Combined API 已含 OV 能力,独立 SKU 价值低
- ConsumerView 独立调用 — Combined API 的 UE 段已覆盖 ConsumerView 字段
- Mosaic 独立调用 — Combined API 的 UE 段已可选订阅 Mosaic
- Identity Graph / HHID 独立调用 — Combined API 已返回 HHID
- Premier Attribute(单字段查询)— 调用次数估算难以触顶,Combined API 已是性价比最优
- Activation / Onboarding — 平台已自建 LiveRamp / DV360 / Meta / TTD adapter,无替代必要
- B2B Marketing Solutions — 当前平台聚焦 B2C,B2B 拓展属业务方向变更,届时再单独评估
- WorldView API / Microcells API — 与现有 UE 重叠且覆盖面更小

---

## 1. Combined API(`ue-ov`)· 现状基线复核 ✅

**接口**:`POST /marketing-services/targeting/v1/ue-ov`(Hygiene + OmniView + Universal Enrichment + Data Lookup 四合一)
**状态**:已上线,详见 [`EXPERIAN-DATA-ROLE.md`](EXPERIAN-DATA-ROLE.md)
**官方文档**:[ConsumerView API Developer Guide (PDF)](https://developer.experian.com/system/files/2022-03/consumerview-api-developer-guide.pdf)

### 1.1 客户确认事项(对齐当前授权范围)

| 问题                                                                            | 选项                                                               |
| ------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| 当前合同涵盖的 UE segment 类别                                                  | ☐ Demographics ☐ Lifestyle ☐ Interests ☐ Auto ☐ Financial ☐ Mosaic |
| 月度调用配额                                                                    | **\_\_\_** 次/月                                                   |
---

## 2. Suppression Files · MVP 合规硬门槛 ⚠️(P0)

**接口家族**:DNM(Do Not Mail) / DNC(Do Not Call) / DNO(Do Not Email,opt-out) / Deceased / Prison
**官方文档**:[Aperture Suppression Data](https://docs.experianaperture.io/address-validation/batch-api/using-our-data/suppression-data/)

### 2.1 为什么必须在 MVP 完成

- 任何 CRM 营销或 Audience Export 必须先与最新 DNM/DNC/DNO/Deceased 比对,否则违反 **CAN-SPAM / TCPA / DMA 自律规范**——这是法务能否签发上线许可的硬门槛。
- 平台侧已规划 `shared_reference.suppression_lists` 表,Audience Export translator 在导出前强制 JOIN,命中即剔除,并写入审计。

### 2.2 客户确认事项

| 问题                                                                        | 选项                                               |
| --------------------------------------------------------------------------- | -------------------------------------------------- |
| 当前是否已订阅 Suppression Files?                                           | ☐ 全部 5 类 / ☐ 部分(**\_\_\_**) / ☐ 暂无          |
| 暂无时:是否同意在合同补充 Suppression 条款?**未签 = 平台不能上线 CRM 营销** | ☐ 同意追加 / ☐ 暂不(则需阻塞 Audience Export 上线) |
| 刷新频率                                                                    | ☐ 每日全量 / ☐ 每周全量 / ☐ 实时 API 调用          |
| 数据交付方式                                                                | ☐ Aperture Batch API / ☐ SFTP 文件 / ☐ 实时 REST   |

### 2.3 平台实现要点

- 入仓表:`shared_reference.suppression_lists`(`identifier_hash`, `suppression_type`, `effective_at`, `expires_at`)
- 强制流程:每日 cron 拉取 → 增量 MERGE → Audience Export translator JOIN 时 `WHERE NOT EXISTS (suppression)`
- 审计:每次 Audience Export 记录"剔除条数 / 剔除来源"到 `audit_events`,DSAR / 合规审计可证

---

## 3. Phase 2+ 备选(MVP 不做,触发条件满足后再激活)

### 3.1 Universal Enrichment(UE)独立调用

- **接口**:`POST /marketing-services/targeting/v1/ue`
- **官方文档**:[ConsumerView API Developer Guide (PDF)](https://developer.experian.com/system/files/2022-03/consumerview-api-developer-guide.pdf)
- **价值**:已有 `experian_hhid` 时跳过 OmniView,只做画像增强,降本约 30-40%
- **触发条件**:Combined API 月度配额触顶,且 ≥ 60% 的调用其实只需要画像不需要身份解析

### 3.2 Address Hygiene(地址清洗)

- **接口**:`POST /address/cleanse`(USPS 标准化)/ `POST /address/validate`(轻量校验)
- **官方文档**:[Experian Address Validation](https://docs.experianaperture.io/address-validation/experian-address-validation/)
- **价值**:CSV 导入的脏地址规范化后,OmniView 匹配率提升 15–30%
- **触发条件**:F-14 历史数据导入大批量上线后,实际匹配率 < 70%

### 3.3 Email / Phone Hygiene(联系方式质检)

- **接口**:`POST /email/validate`(可达性 + 风险评分)/ `POST /phone/validate`(在网状态 + line type)
- **官方文档**:[Email Validation](https://docs.experianaperture.io/email-validation/experian-email-validation-v2) · [Phone Validation](https://docs.experianaperture.io/phone-validation/experian-phone-validation)
- **价值**:Audience Export 前置质检,提升广告平台 match rate,避免被标记为低质量种子
- **触发条件**:任一主要 DSP(Meta/DV360/TikTok)报告 match rate < 60%

### 3.4 TrueTouch Communication Preferences

- **接口**:需找 Experian CSM 索取(未公开发布 Swagger)
- **官方文档**:产品页 https://www.experian.com/marketing-services/truetouch
- **价值**:返回受众更可能响应的渠道(Email / Direct Mail / Mobile / Social / TV)与时段,供 Media Agent 自动分配预算
- **触发条件**:Media Agent 进入自动化投放阶段,需要数据驱动的渠道组合推荐

### 3.5 Health & Wellness Segments(HIPAA)

- **接口**:`POST /health/segments`(产品页 https://www.experian.com/healthcare/)
- **强制前置**:必须签署 BAA;PHI 不进 Processed Lake,仅走 Raw PII Lake + PII Access Service
- **价值**:服务医疗 / 保险 / 制药 Agency 客户时的画像专供
- **触发条件**:业务方向纳入医疗垂直行业 + 三方 BAA 签署完成 + 平台开通 HIPAA Lane

---

## 4. 相关文档

- 现状 baseline:[`docs/EXPERIAN-DATA-ROLE.md`](EXPERIAN-DATA-ROLE.md)
- PII 边界设计:[`docs/PII-DESIGN-SOLUTION.md`](PII-DESIGN-SOLUTION.md)
- ELT 8 步管道:[`docs/ELT-8-STEP-DESIGN.md`](ELT-8-STEP-DESIGN.md)
- 架构审计:[`docs/ARCHITECTURE-AUDIT-2026Q2.md`](ARCHITECTURE-AUDIT-2026Q2.md)
