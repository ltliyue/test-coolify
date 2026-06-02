# 真正的难点与注意事项 · 客户沟通版

> **文档类型**:客户沟通材料 / 项目风险提示
> _Last updated: **2026-05-21**_
> **目标读者**:客户 stakeholder · 客户技术负责人 · 客户合规法务 · 客户采购
> **范围说明**:本文档**不**列举"需要工程时间但能做"的事(比如三 Lake 重构、Media Agent、Frontend 数据接入 — 那些都在 [`ARCHITECTURE-AUDIT-2026Q2.md`](./ARCHITECTURE-AUDIT-2026Q2.md) §11 工程路线图里,**只是时间问题**)。本文档**只列**:
>
> 1. **真正的难点** — 加多少人 / 加多少钱 / 加多少周也解决不了的事(节奏、外部、合规、技术天花板)
> 2. **注意事项** — 即使能解,但若客户/我们某一方疏忽就会踩坑的点
>
> 这些都需要客户在决策前理解 — **代码不是答案**。

---

## 0. 速读

### 0.1 5 个真正的难点(代码改不了)

| #   | 难点                                           | 本质                                                                | 客户能做的                                                    |
| --- | ---------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------- |
| 1   | **外部数据源合同期 60-120 天**                 | Experian/TransUnion/Nielsen 没有自助开通通道                        | **本周启动法务谈判**,合同期与工程并行                         |
| 2   | **第三方 API 速率上限 + 弃用节奏不在我们手里** | HubSpot 250K/天 · StackAdapt REST 即将停服 · Meta App Review 2-4 周 | 调整业务节奏适配第三方;**不能堆代码绕过**                     |
| 3   | **HIPAA BAA 四方互锁**                         | Anthropic + AWS + 客户 + ReceptivIQ 任一方拖延就阻塞                | **客户与各方平行启动 BAA**,不是串行                           |
| 4   | **跨厂商个体 ID 行业级不可互通**               | TUID ≠ experian_pid ≠ RampID ≠ MAID,**没有任何 SDK 能"解决"**       | 接受 fuzzy link + confidence score;**不要要求 100% 匹配**     |
| 5   | **AI LLM 输出本质非确定性**                    | 同一 prompt 不同结果;不能用传统 QA 工具 100% 覆盖                   | 接受 "human-in-the-loop" 必要性;**不要追求"AI 全自动无监督"** |

### 0.2 不算难点(但也不快)的事

下列**不在本文档范围**,因为它们是"加时间就能做完"的标准工程,详见 [`ARCHITECTURE-AUDIT-2026Q2.md`](./ARCHITECTURE-AUDIT-2026Q2.md) §11:

- 三 Lake 数据架构重构(5-6 周)
- Media Agent + Tool Executor + Memory & Retrieval(3 周)
- 合规自动化 cron(DSAR / Retention / 72h)(2 周)
- Frontend 数据真实接入(1-2 周)
- 剩余 6 个 adapter(Trade Desk · Tresorit · Experian · TransUnion · Nielsen · Placer IQ)

> 这些不是"难",是"工程量大但路径清晰"。

---

## 1. 真正的难点

### 1.1 难点 · 外部数据源合同 = 项目时间表上唯一的硬阻塞

**本质**:Experian / TransUnion / Nielsen / Placer IQ / Trade Desk 是 B2B 关系驱动型数据厂商。

**为什么改不了**:

- ❌ 没有"信用卡注册立即用"的自助通道
- ❌ 销售评估 → MSA → DPA → 法务 → 商务谈判 → 合规审查 → 凭证下发,**全流程 60-120 天**
- ❌ 加钱不能加快(他们的内部流程就是这么慢)
- ❌ ReceptivIQ 工程团队**完全不能加速**任何一步

**典型节奏对照**:

| 数据厂商               | 谈判到凭证下发     | 备注                                  |
| ---------------------- | ------------------ | ------------------------------------- |
| Experian Combined API  | 60-90 天           | 行业惯例;有 CSM 介入可能加速到 60 天  |
| TransUnion TruAudience | **60-120 天**      | 含 mTLS 证书申请,通常比 Experian 更慢 |
| Trade Desk             | 2-4 周(若已是客户) | 客户的 TTD AM 主导                    |
| Nielsen                | 60-90 天           | 含数据样本交付协议                    |
| Placer IQ              | 30-60 天           | 较快,但仍需合同                       |
| Tresorit(企业版)       | 1-2 周             | 仅是企业账号采购                      |

**客户能做的(也是必须做的)**:

- ✅ **本周内启动法务谈判** — 6 家平行启动(不是串行)
- ✅ 提前准备 DPA · 把 ReceptivIQ 列为 sub-processor
- ✅ 给销售明确数据量估算 → 否则报价拖延

**接受现实**:**这是 V1 时间表的唯一硬阻塞** — 工程团队 11-13 周可上线,但若 Experian 合同拖到第 12 周才签,Persona Agent 这部分 V1 上线会延期。

---

### 1.2 难点 · 第三方 API 速率上限 / 弃用节奏 / 政策变化

**本质**:我们消费的第三方 API,**他们说什么节奏就是什么节奏**,代码做不了任何改变。

**典型的不可控**:

| 类别                  | 例子                                                                              | 我们能做什么                                        |
| --------------------- | --------------------------------------------------------------------------------- | --------------------------------------------------- |
| **API 速率上限**      | HubSpot 250K req/天(Free/Starter)· StackAdapt 60 req/min · Search API 5 req/sec   | 调度时分散到全天 · 申请加购但**取决于第三方批准**   |
| **API 弃用通知**      | StackAdapt 2025-05-13 起 REST API 已 deprecate,**预计 2026 年内停服**             | **必须按对方节奏迁移到 GraphQL** · 否则同步全线断流 |
| **新 API 客户审核期** | Meta App Review 2-4 周 · TikTok App 审核 1-2 周 · HubSpot Marketplace App 2-4 周  | 提前申请;**审核结果不在我们手里**                   |
| **政策变化**          | Apple ATT 让 iOS MAID 几乎不可用 · Cookie 3rd party deprecation · GA4 强制取代 UA | 跟随调整数据架构;**我们能预判但不能阻止**           |
| **API 服务中断**      | 三方 status page 显示 outage,我们重试也救不了                                     | 退避 + 告警 + 等恢复 · **客户必须接受偶发降级**     |

**客户能做的**:

- ✅ 接受 SLA 不是 100%(取决于第三方加权值)
- ✅ 业务节奏适配 — 例如 HubSpot 250K/天是 Free 配额,客户升级到 Pro 才能拿 650K
- ✅ 提前 6 个月跟我们一起 review 第三方 API roadmap → 共同规划升级

**不能做的**:

- ❌ 用更多代码绕过速率上限 — 这是合同条款而非技术限制
- ❌ 阻止第三方弃用老 API — 唯一办法是迁移

---

### 1.3 难点 · HIPAA BAA 四方互锁,任一方拖延都阻塞

**本质**:HIPAA 客户上线需要**同时**满足:

```
       ┌────────────────────┐
       │  Anthropic BAA     │ ← AWS Bedrock 走的是 Anthropic Claude
       └────────────────────┘
                  ↑
                  │ 四方 BAA 必须互相串联
                  │
       ┌────────────────────┐    ┌────────────────────┐
       │  AWS BAA            │ ←→ │  ReceptivIQ BAA    │
       └────────────────────┘    └────────────────────┘
                  ↑
                  │
       ┌────────────────────┐
       │  客户(医疗实体) │
       └────────────────────┘
```

**为什么这是难点**:

- ❌ 任一方拒签 → 上线阻塞 100%
- ❌ 任一方拖延(典型法务 review 1-2 月)→ 总周期 = 最慢的那一方
- ❌ ReceptivIQ 不能"垫" — 必须直接客户与 AWS / Anthropic 签
- ❌ 拒签往往是"非技术原因"(法律解释不一致、客户内部审批层级、保险条款分歧),工程团队无法干预

**典型节奏**:

| 步骤                                          | 谁主导                 | 周期                         |
| --------------------------------------------- | ---------------------- | ---------------------------- |
| 客户法务启动 BAA review                       | 客户                   | 2-4 周                       |
| AWS BAA 申请(via AWS Health Customer Success) | 客户                   | 2-4 周                       |
| Anthropic Enterprise Plan + BAA               | 客户 + Anthropic Sales | 4-8 周                       |
| ReceptivIQ ↔ 客户 BAA                         | 客户 + 我们            | 2-4 周                       |
| 全部互锁就绪                                  | —                      | **典型 6-12 周(最慢方决定)** |

**客户能做的**:

- ✅ **平行启动**所有 4 方(不是串行)
- ✅ 提前一份 BAA 模板给所有方,减少多次 review
- ✅ 把 HIPAA 上线时间定在合同启动 12 周后(给充分缓冲)

**不能做的**:

- ❌ 让 ReceptivIQ 单独"代签" Anthropic / AWS 的 BAA — 法律上不允许
- ❌ 用"假数据"绕过 — 一旦生产数据进入,任何一方未签都是违规

---

### 1.4 难点 · 跨厂商个体 ID 不可互通(行业级根本问题)

**本质**:营销数据生态里,**每个数据厂商都有自己的 ID 体系**,且**互不识别**:

```
Experian       experian_pid     experian_hhid
TransUnion     TUID             HHID
LiveRamp       RampID           RampID household
Cookie 域      cookie_id (per domain)
Mobile         IDFA / GAID
CTV            Roku ID / Samsung TIFA / Hulu ID
Meta           FBC / FBP / Pixel ID
Google         Click ID / GA Client ID
```

**为什么改不了**:

- ❌ 行业历史问题 — 没有任何 SDK / 平台能"统一"它们
- ❌ 各家有商业利益维护自己的 ID(锁定客户)
- ❌ LiveRamp 提供"中介 RampID"是商业解决方案,但仍是**一对多 fuzzy link**,不是 100% 准确
- ❌ Apple ATT + Cookie deprecation 让情况**更复杂**

**典型场景**:

| 客户期望                                         | 现实                                                                             |
| ------------------------------------------------ | -------------------------------------------------------------------------------- |
| "把 Experian 的画像 + TransUnion 的归因合在一起" | 必须用 hashed_email + postal_address 二次 link,**带 confidence score**,不是 100% |
| "Persona 这条人在 Meta 上对应哪个 cookie?"       | 唯一办法是客户登录或 Meta CAPI 上传 hashed_email                                 |
| "把 CTV 看过广告的人在 GA4 上追踪"               | RampID 中介可做但仍是 fuzzy;**永远不是真值**                                     |
| "提个 person 跨设备"                             | 跨设备身份图(Neustar 等)概率,**不是物理唯一**                                    |

**我们怎么处理**:

```sql
-- shared.identity_bridge 中间表
CREATE TABLE identity_bridge (
  hashed_email      TEXT,
  experian_pid      TEXT,
  tuid              TEXT,
  ramp_id           TEXT,
  cookie_ids        TEXT[],
  maids             TEXT[],
  confidence        INT,         -- 0-100
  source            TEXT,        -- "email+postal" / "ramp" / "experian_ov"
  resolved_at       TIMESTAMPTZ
);
```

每条 link 都带**置信度 + 来源**,合规审计可追溯。

**客户能做的**:

- ✅ 接受 fuzzy link 的本质 — 不要求"两个 ID 一定指同一人"
- ✅ 在受众投放时容忍 ±10-20% 错配率(行业基线)
- ✅ 关键业务决策需要"高置信度 link"时,**单独走 LiveRamp ATS** 而不是 fuzzy bridge

**不能做的**:

- ❌ 要求"实时 100% 准确" — 任何平台都做不到
- ❌ 期望 "Persona Agent 给出的客户群与 Meta Audience 完全一致" — 误差是物理性的

---

### 1.5 难点 · AI / LLM 输出本质非确定性

**本质**:LLM 是**生成式**模型,**同一 prompt 多次跑可能给不同答案**:

| 维度   | 传统软件            | LLM                                            |
| ------ | ------------------- | ---------------------------------------------- |
| 确定性 | 同输入 → 同输出     | 同输入 → **每次结果可能不同**(temperature > 0) |
| 测试   | unit test 100% 覆盖 | 难以 100% 覆盖;只能统计性验证                  |
| 调试   | 看代码 + 看日志     | "为什么这次输出错了" → 不可重现                |
| 错误率 | 0(理论)             | 5-15% 不准确(行业平均)                         |
| 监督   | 不需要              | **必须 human-in-the-loop**                     |

**为什么这是难点**:

- ❌ 不能用传统 QA / 单元测试套件 100% 覆盖
- ❌ 客户期望"AI 全自动" → 不切实际
- ❌ 一旦 LLM 输出在合规边界出错(如建议给禁忌人群投放),没有"调试代码"的概念
- ❌ 模型升级(Claude 4.0 → 4.5)可能让某些表现变好但另一些变差

**典型场景**:

| 客户期望                               | 现实                                           |
| -------------------------------------- | ---------------------------------------------- |
| Persona Agent 同一客户每次跑出同样画像 | 大体相同,细节会变 — **建议固定 temperature=0** |
| Creative Agent 完全替代 copywriter     | 80% 场景可用 · 20% 需要人工 review             |
| Attribution Agent "解释" 归因结果      | 解释合理但**不是真因果** — 仍需人工判断        |
| Media Agent 全自动调整预算             | **MVP 强制 human-in-the-loop**(PSD 已明确)     |

**我们怎么处理**:

- ✅ Temperature 设为 0(稳定性优先)
- ✅ Langfuse 追踪每次调用 — 可回看 prompt 与 response
- ✅ Token 预算硬上限(防 runaway cost)
- ✅ 高敏感场景(媒介采买写回 / 预算调整 / 受众导出)**强制人工审批**
- ✅ 输出含置信度评分 + 不确定性提示

**客户能做的**:

- ✅ 接受 "AI 是助理而非替代" 的定位
- ✅ 给 Agency Operator 留 review 时间(不要把 SLA 卡到分钟级)
- ✅ 关键场景**永远保留人工复核**入口

**不能做的**:

- ❌ 要求 "AI 输出 100% 准确无监督"
- ❌ 用 AI 替代法务 / 合规判断(尤其医疗 / 金融)

---

## 2. 注意事项(需要客户和我们都警惕)

下列**不算难点**,但若客户或我们某一方疏忽就会踩坑。

### 2.1 凭证与密钥类(7 条)

| 注意事项                                           | 影响                                                                                       |
| -------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| **HubSpot Private App token 只显示一次**           | 创建时关闭弹窗就再也看不到完整 token · 必须立即记录;丢了只能 delete app 重建               |
| **HubSpot 创建 Private App 需要 Super Admin 权限** | 普通 portal user 看不到入口;客户 IT 需提前授权                                             |
| **StackAdapt 2025-05-13 起需要新 GQL Key**         | 老 REST Key 不能用于 GraphQL;升级时需重新申请,不是直接 swap                                |
| **TransUnion mTLS 客户端证书有效期通常 1 年**      | 到期前 60 天必须续签 · CTS 工单需 1-2 周;到期当天 = 全线断流                               |
| **OAuth state 参数必须 HMAC 签名**                 | 否则可被 CSRF / cross-tenant 攻击;ReceptivIQ 已用 C-01 防护,客户对接其他 OAuth 也要遵循    |
| **API Key 误推送到 git**                           | 即使是 private repo,token 已被视为泄漏 · 必须立即 revoke + 重发;`pre-commit` hook 强制检查 |
| **凭证轮换季度建议**                               | 长期不变 token 是合规审计低分项;建议季度 rotate                                            |

### 2.2 数据语义类(8 条)

| 注意事项                                         | 影响                                                                                               |
| ------------------------------------------------ | -------------------------------------------------------------------------------------------------- |
| **币种不同 → 报表合并错位**                      | StackAdapt 默认按 advertiser 设的币种(USD/CAD/EUR);客户合并报表前**必须按汇率统一**                |
| **时区跨源不一致**                               | HubSpot 按 portal 时区;Meta 按 ad account 时区;**ReceptivIQ 统一 UTC** 落仓,客户报表需在显示层转换 |
| **HubSpot lifecyclestage 客户自定义**            | 默认 7 阶段,客户后台可改/增 → ReceptivIQ 必须先拉 schema 再映射,**不要硬编码**                     |
| **HubSpot email 强制小写存储**                   | 客户端比对 hash 时必须 `lowercase + trim` · 否则 hash 对不齐                                       |
| **自定义属性默认不返回**                         | HubSpot 必须显式 `?properties=fname1,fname2` 才返回 · 否则字段缺失                                 |
| **转化数据 30 天归因窗口**                       | StackAdapt 的 `conversion_value` 会回算 30 天 → 历史回灌窗口必须包含                               |
| **TransUnion TUID 与 Experian PID 不能盲信相等** | 必须二次 link(hashed_email + postal),且**仅在 identity_bridge 中表达**关系                         |
| **Search API 5 req/sec(HubSpot 特例)**           | 不要用 Search 跑批量;改用 GET list + `properties=`                                                 |

### 2.3 合规与法务类(8 条)

| 注意事项                                         | 影响                                                                                                                            |
| ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------- |
| **GDPR 删除不是物理 purge**                      | 必须保留审计行(Art. 30 要求);删除 = 标记 deleted + 屏蔽业务读取;但 audit 不动                                                   |
| **客户 DPA 必须列 ReceptivIQ 为 sub-processor**  | 未列 = 客户违反 GDPR Art. 28;接入前 review                                                                                      |
| **Sub-processor 链 30 天通知**                   | ReceptivIQ 增加新数据厂商(如新签 Nielsen)前 30 天通知所有客户 · cron 自动化中                                                   |
| **HIPAA 客户的 PHI 不能进 OpenRouter LLM**       | OpenRouter 无 BAA;必须走 AWS Bedrock 路由;**默认 OpenRouter,HIPAA 客户强制切换**                                                |
| **Experian Suppression Files 是 CRM 营销硬门槛** | 未签 = **不能上线 Audience Export**(CAN-SPAM / TCPA 风险) · 详见 [`EXPERIAN-APIS-TO-CONFIRM.md`](./EXPERIAN-APIS-TO-CONFIRM.md) |
| **欧盟客户 → TransUnion 弱**                     | TU 在 EU 数据资产较弱 + 跨境合规复杂;**EU 客户优先 Experian / LiveRamp**                                                        |
| **数据驻留承诺**                                 | 客户合同可能写 "data stays in EU";per-tenant region binding 未实现 → 严格客户暂不能承接                                         |
| **删除请求 30 天 SLA**                           | GDPR 30 天 / CCPA 45 天 / HIPAA 30 天;自动化 cron 落地前**手动达 SLA 风险高**                                                   |

### 2.4 跨平台 ID 与受众类(5 条)

| 注意事项                                               | 影响                                                                        |
| ------------------------------------------------------ | --------------------------------------------------------------------------- |
| **Experian + TransUnion 同时接入需要 identity_bridge** | 否则两套 ID 在仓库内不可关联;请提前规划                                     |
| **LiveRamp ATS 不等于 RampID 中介**                    | ATS 是身份解析服务;Cookie 时代后 RampID 实际可用率下降 ~30%                 |
| **CTV ID(Roku/Samsung/Hulu)各自独立**                  | 跨设备追踪需要 Neustar / TransUnion 概率匹配;**不是真实唯一**               |
| **Meta CAPI hashed_email 与你存的 hash 不同**          | Meta 用 SHA-256(lowercase + trim),我们必须用同样规范化,否则 match rate 暴跌 |
| **Audience 投放 match rate 60%-80% 是行业基线**        | 不要要求 100%;match rate < 50% 时检查 hash 一致性                           |

### 2.5 运维与监控类(7 条)

| 注意事项                              | 影响                                                                               |
| ------------------------------------- | ---------------------------------------------------------------------------------- |
| **每 Agency 物理库需要单独备份**      | Postgres pg_dump 需 per-database 配置;**不能漏租户**                               |
| **per-Agency KMS 派生尚未实现**       | 当前所有 Agency 共用一个全局 Fernet key;轮换 = 全 Agency 同时影响;**Phase 2 升级** |
| **审计日志增长率高**                  | 每请求至少 1 条 audit;3 Agency × 6 个月 ≈ 数百万行;需要分区策略                    |
| **dbt 模型修改影响所有 Agency**       | canonical layer 一改 = 全租户重跑;升级流程必须 review 影响范围                     |
| **Agency 暂停 → cron 必须真停**       | 否则继续消耗 API 配额 + 数据更新;sync_logs.status='suspended' 必须双向检查         |
| **客户提供的 CRM 文件格式不可控**     | 五花八门;字段映射要灵活;F-15 模块负责,但**首次接入需 1-2 周客户配合**              |
| **第三方 status page 不在我们监控里** | 客户报告"数据不更新"时,先去对方 status page 排查;然后我们 sync_logs                |

### 2.6 客户配合类(6 条)

| 注意事项                                        | 影响                                                                |
| ----------------------------------------------- | ------------------------------------------------------------------- |
| **客户法务 review DPA 通常 2-4 周**             | 不要假设"客户当周回复"                                              |
| **客户 IT 给我们 mTLS 证书需要客户内部审批**    | TransUnion 这类需走客户内部安全流程 1-2 周                          |
| **HubSpot 创建 Private App 找客户 Super Admin** | 不是所有 portal user 都能做;客户 IT 提前明确                        |
| **StackAdapt GQL Key 申请需通过 CSM**           | 客户自己提工单 + CSM 审批,24-72 小时 · 我们催不来                   |
| **Experian Combined API 凭证必须客户自己签名**  | 不能"代签"                                                          |
| **客户后台数据质量直接影响我们效果**            | HubSpot 里 lifecyclestage 没维护,Persona Agent 就生成不出有意义画像 |

---

## 3. 给客户的清晰预期

### 3.1 我们能保证什么

- ✅ 工程节奏可控:11-13 周完成 V1 内部工程(假设外部合同 Week 0 启动)
- ✅ 现有 8 个 connector 数据持续入仓
- ✅ 多租户 + 权限 + 审计 + Frontend MVP 已生产可用
- ✅ 透明度:每周更新 sync_logs · audit_logs · 性能指标

### 3.2 我们不能保证什么

- ❌ Experian / TU / Nielsen 合同 X 月底前签下来(取决于客户法务)
- ❌ Meta / TikTok App Review 通过(取决于平台)
- ❌ HIPAA BAA 全部签完(取决于 Anthropic / AWS / 客户)
- ❌ AI Agent 输出 100% 准确无监督
- ❌ 跨厂商 ID 100% 一致匹配
- ❌ 第三方 API 永远可用(取决于他们的 SLA)

### 3.3 客户需要立即决策的(本周)

| 决策                                        | 选项                                                  |
| ------------------------------------------- | ----------------------------------------------------- |
| **是否本周启动 Experian 合同?**             | ☐ 是 / ☐ 否(自承担延期)                               |
| **是否承接 HIPAA 客户(V1 范围内)?**         | ☐ 是 → 启动 4 方 BAA · 周期 +6-12 周 / ☐ 否 → V2 再说 |
| **二级数据源(TU/Nielsen/Placer IQ)谁先签?** | 按客户业务需求评估 · 不要一次签全部                   |
| **AI Agent 输出失误时容忍度?**              | "AI 是助理"(推荐) / "AI 完全替代"(不切实际)           |

---

## 4. 关联文档

- [`docs/psd/technical-solution.md`](./psd/technical-solution.md) — PSD 原文
- [`docs/ARCHITECTURE-AUDIT-2026Q2.md`](./ARCHITECTURE-AUDIT-2026Q2.md) — 内部工程审计 · §11 Next Steps(**工程层的"易但慢"的事在这里**)
- [`docs/EXPERIAN-APIS-TO-CONFIRM.md`](./EXPERIAN-APIS-TO-CONFIRM.md) — Experian 接口范围客户确认
- [`docs/TRANSUNION-INTEGRATION.md`](./TRANSUNION-INTEGRATION.md) · [`docs/HUBSPOT-INTEGRATION.md`](./HUBSPOT-INTEGRATION.md) · [`docs/STACKADAPT-INTEGRATION.md`](./STACKADAPT-INTEGRATION.md) · [`docs/INTEGRATION-GUIDE-GA4-DV360.md`](./INTEGRATION-GUIDE-GA4-DV360.md) — 各家 adapter 注意事项详情
- [`docs/MULTI-TENANT-DB.md`](./MULTI-TENANT-DB.md) — 多租户隔离设计
- [`docs/PII-DESIGN-SOLUTION.md`](./PII-DESIGN-SOLUTION.md) — PII 边界 + 凭证加密

---

## 5. 一段话总结(给客户决策者)

> **真正的难点不是"我们改不了代码",而是"代码也改不了的东西"**:外部数据厂商合同期(60-120 天)· 第三方 API 速率与弃用节奏(不在我们手里)· HIPAA BAA 四方互锁 · 跨厂商个体 ID 行业级不可互通 · AI LLM 输出本质非确定性 — 这 5 条**没有任何工程方案能"加速"或"绕过"**,只能用合理的项目节奏与客户预期管理它们。
>
> 注意事项 41 条(分 6 类)是"能解但需要双方警惕"的点 — 凭证管理 · 数据语义 · 合规法务 · 跨平台 ID · 运维监控 · 客户配合 — 任一类的疏忽都会带来事故。
>
> **本周客户的关键动作**:启动 Experian 合同 + 决定 HIPAA 是否承接 + 决定二级数据源签约顺序。这 3 个决策直接决定 V1 时间表。
