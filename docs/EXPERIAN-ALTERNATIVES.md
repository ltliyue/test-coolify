# Experian 替代方案调研 · 第三方数据供应商对比

_Last updated: **2026-05-26**_

> **文档类型**:供应商选型调研
> **目标读者**:产品 / 客户技术负责人 / 采购 / 后端工程
> **目的**:列出可在本项目中**替代 Experian** 的第三方消费者数据供应商,逐家给出优缺点、对接难度、官网与开发者文档,供选型与议价参考。
> **重要前提**:所有官网 / 开发者文档链接均在 2026-05 经联网检索核实可访问;商业条款(价格、覆盖率)请以与供应商签约时的报价为准。

---

## ⚠️ 0. 合规第一 · 选型前置硬门槛(PASS / FAIL)

> **本项目铁律:必须同时满足 GDPR + CCPA + HIPAA + SOC 2。供应商先过合规,再谈数据能力、价格、对接难度。**
> **任何一项 FAIL → 该供应商直接淘汰,不进入后续技术评估。** 数据再全、API 再好用、再便宜,都不例外。

### 0.1 七道合规闸门(逐项打勾才能进下一步)

| #      | 合规闸门                          | 通过标准(PASS)                                      | 不通过(FAIL = 淘汰)         | 法规依据               |
| ------ | --------------------------------- | --------------------------------------------------- | --------------------------- | ---------------------- |
| **G1** | **合法数据来源举证**              | 供应商能提供其数据持有的合法 consent 链路证明       | 说不清数据从哪来 / 拒绝举证 | GDPR Art. 6/7 · CCPA   |
| **G2** | **签署 DPA(数据处理协议)**        | 提供可签署的 DPA,明确双方角色(controller/processor) | 无 DPA 或拒签               | GDPR Art. 28           |
| **G3** | **签署 BAA(若客户为 HIPAA 实体)** | 愿意签 Business Associate Agreement                 | HIPAA 客户场景下拒签 BAA    | HIPAA                  |
| **G4** | **用途限定条款**                  | 合同写明"仅营销用途,**不得**用于信贷/雇佣/保险决策" | 用途不受限(触发 FCRA 风险)  | FCRA · GLBA            |
| **G5** | **数据主体权利可执行(DSAR)**      | 支持删除/更正回传,我方 DSAR 能级联到该供应商        | 数据进去就拿不回、删不掉    | GDPR Art. 15-17 · CCPA |
| **G6** | **合规抑制可兜底**                | Deceased / DNC / opt-out 抑制名单有等价覆盖         | 无任何抑制能力且无替代兜底  | TCPA · CAN-SPAM · DMA  |
| **G7** | **安全认证 + 加密传输**           | SOC 2 Type II / ISO 27001 + TLS/mTLS                | 无安全认证 / 明文传输       | SOC 2                  |

> **执行方式**:任何供应商进入 POC 之前,采购 + 法务先用这 7 项打分;**7 项全 PASS 才允许工程接入**。结果存档,作为审计证据。

### 0.2 各供应商合规初判(签约前须复核)

| 供应商               | G1 来源           | G2 DPA | G3 BAA      | G4 用途限定         | G5 DSAR   | G6 抑制 | G7 安全认证    | 合规初判                 |
| -------------------- | ----------------- | ------ | ----------- | ------------------- | --------- | ------- | -------------- | ------------------------ |
| **TransUnion**       | ✅ 征信局合规底座 | ✅     | ⚠️ 需谈     | ✅ FCRA 经验丰富    | ✅        | ⚠️ 需配 | ✅ SOC2 + mTLS | 🟢 强                    |
| **Acxiom/LiveRamp**  | ✅                | ✅     | ⚠️ 需谈     | ✅                  | ✅        | ⚠️ 弱   | ✅ SOC2        | 🟢 强                    |
| **Equifax**          | ✅ 征信局         | ✅     | ⚠️          | ✅ FCRA 原生        | ✅        | ⚠️      | ✅             | 🟢 强                    |
| **Epsilon**          | ✅                | ✅     | ⚠️          | ✅                  | ✅        | ⚠️      | ✅             | 🟢 强                    |
| **Verisk/Infutor**   | ✅                | ✅     | ⚠️          | ✅ Jornaya 同意验证 | ✅        | ⚠️      | ✅             | 🟢 强                    |
| **Versium REACH**    | ⚠️ 须索取来源证明 | ✅     | ❌ 通常不签 | ⚠️ 须确认           | ⚠️ 须确认 | ❌ 无   | ⚠️ 须确认      | 🟡 中(非 HIPAA 场景可用) |
| **People Data Labs** | ⚠️ 须索取         | ✅     | ❌          | ⚠️ 偏 B2B           | ⚠️        | ❌      | ⚠️             | 🟡 中                    |
| **FullContact**      | ⚠️ 须索取         | ✅     | ❌          | ⚠️                  | ⚠️        | ❌      | ⚠️             | 🟡 中                    |
| **Data Axle**        | ✅                | ✅     | ⚠️          | ✅                  | ⚠️        | ⚠️      | ✅             | 🟡 中-强                 |
| **LexisNexis(抑制)** | ✅                | ✅     | ✅          | ✅                  | ✅        | ✅ 专长 | ✅             | 🟢 强                    |

> **图例**:✅ 通常满足 · ⚠️ 需在签约前书面确认 · ❌ 通常不满足。
> **关键判断**:
>
> - **HIPAA 客户**(健康类品牌)→ 只能选 G3 BAA 能签的全栈巨头 + LexisNexis;**API 优先厂商(Versium/PDL/FullContact)一律淘汰**(不签 BAA)。
> - **非 HIPAA 的普通营销客户** → API 优先厂商在补齐 G1/G4/G5/G7 书面确认后可用。
> - **合规抑制(G6)永远不能省** → 即使主数据换成 API 厂商,Deceased/DNC 必须由 LexisNexis/AccuData 兜底。

### 0.3 接入后必须落地的合规动作(代码侧,无例外)

1. **入仓前哈希** — 任何供应商数据进仓库前一律 `hash_identifier(value, agency_salt)`,**禁止明文 PII 落仓**。
2. **审计每次调用** — 写 `enrichment.<provider>.completed` 事件(match_score、计费、record_id),失败写 5xx 不静默。
3. **凭据加密** — 供应商 API key / 证书经 Fernet 加密存 `credentials.encrypted_data`,禁止明文出现在日志/Sentry。
4. **DSAR 级联** — 新供应商接入 `dsar.py` 的删除/导出级联清单;DSAR 删除时一并通知该供应商删除。
5. **consent 校验** — 调用第三方增强前,先查 `consent_records` 确认该 subject 未撤回 marketing 同意。
6. **数据来源存证** — 供应商 DPA / 合规证明存档,关联 `data_source_attestation`,6 年留存。

> **CI/流程守卫**:新增 adapter 若未写 `enrichment.*` 审计、或明文落仓、或未挂 DSAR 级联 → 视为阻塞性问题,不允许合并。

---

## 0.5 先搞清楚:我们到底用 Experian 做什么

替代方案能不能"换得掉",取决于它能否覆盖我们对 Experian 的**两类核心用途**:

| Experian 产品(本项目用到)                              | 干什么                                                           | 数据流阶段                        | 替代难度       |
| ------------------------------------------------------ | ---------------------------------------------------------------- | --------------------------------- | -------------- |
| **Combined API**(Hygiene + OmniView + UE + DataLookup) | ① 身份解析(邮箱→真人)② 画像增强(年龄/收入/Mosaic/兴趣)③ 地址清洗 | ⑥ Enrich / ⑦ Persona / ⑧ Audience | 中-高          |
| **Suppression Files**(DNM / DNC / DNO / Deceased)      | 合规黑名单过滤,禁止触达                                          | ⑨ Suppression Filter              | 中(法务硬门槛) |

> 详见 [`END-TO-END-DATA-FLOW.md`](./END-TO-END-DATA-FLOW.md) §6 / §9 与 [`EXPERIAN-APIS-TO-CONFIRM.md`](./EXPERIAN-APIS-TO-CONFIRM.md)。
>
> **结论先行**:没有任何一家能"一对一无缝替换" Experian 的全部能力。实际选型通常是**"画像增强用一家 + 身份解析用一家 + 合规抑制用一家"** 的组合,或选 TransUnion / Acxiom 这类同样全栈的巨头做主力。

---

## 1. 一图速览 · 候选供应商定位

```
                  覆盖能力(广) ▲
                              │   Experian ●        ● Acxiom/LiveRamp
                              │      ● TransUnion
            全栈巨头           │   ● Equifax   ● Epsilon
        (合同制·重)           │      ● Verisk(Infutor)
   ───────────────────────────┼──────────────────────────────►
            API 优先           │   ● Data Axle                对接易用度(高)
        (开发者友好·轻)        │
                              │  ● People Data Labs  ● FullContact
                              │      ● Versium REACH
                  覆盖能力(窄) ▼
```

- **右下角(API 优先)**:Versium / PDL / FullContact — REST API + SDK,几天能跑通,但消费者画像深度不如征信局。
- **左上角(全栈巨头)**:Experian / TransUnion / Acxiom / Equifax / Epsilon — 数据最全,但合同制、对接重、周期 60-120 天。

---

## ⭐ 1.9 结论:最合适的替代(直接看这里)

> 🟢 **2026-05 更新 · 已对齐 Sprint 0 官方决策**:Whale Song 与 Experian 工程团队尽调后确认 **Experian Combined API 只能"增强已有名单",无法"按条件发现人群"**(Persona Engine 真正需要的查询能力),唯一路径是 license Consumer View 平面文件并自建查询引擎 —— 商业成本高且形成单一供应商锁定。**官方结论:Pillar 1 地基改为下面的"四源合成栈",Experian 降级到 Phase 2/3 enrichment。** 详见 [`PILLAR1-DATA-FOUNDATION-DECISION.md`](./PILLAR1-DATA-FOUNDATION-DECISION.md)。

### 🏆 官方首选 · 四源合成栈(Pillar 1 地基)

| 数据源                     | 角色          | 贡献                                                                                             | 替代的 Experian 能力                           |
| -------------------------- | ------------- | ------------------------------------------------------------------------------------------------ | ---------------------------------------------- |
| **TransUnion TruAudience** | 🔧 锚(anchor) | 人口基础 + 渠道倾向 + 身份解析;覆盖 98% 美国成人 / 1.27 亿家庭;**已有商业关系**                  | 身份解析 + 人口画像 + 渠道倾向(替代 TrueTouch) |
| **Claritas PRIZM Premier** | 心理分群      | 68 个 household segment / 11 Lifestage / 14 Social Group;**与 Mosaic 在 publisher/DSP 层可互换** | Mosaic 心理分群                                |
| **GWI**                    | 态度/文案信号 | 1.4M+ always-on 调研 / 52+ 市场;驱动"为什么买",让 Pillar 3 文案 Agent 在 Phase 1 即可演示        | (Experian 无对等)—— 增量能力                   |
| **LiveRamp**               | 身份 + 激活   | RampID 跨源匹配 + 180+ 数据市场(含 Experian/TransUnion 段);**项目已集成**                        | 身份解析 + 激活 + 通过市场按段买 Experian      |

> **护城河逻辑**:四家中没有任何一家是"承重"的,ReceptivIQ 的价值在于把它们**合成**为 persona / 渠道倾向 / 文案匹配 —— 这是竞品买不到的。单一 Experian 地基会让平台沦为"Experian 的 UI"。

**这个四源栈是项目官方方向;下面 §1.9 旧版"3 选择"作为通用调研结论保留,供横向对照。**

---

### (通用调研版)最合适的替代

> 结合**合规优先(§0)+ 项目已有基础设施 + 改动成本**,最合适的只有 3 个。注意:不是"三选一",而是**"主力画像/身份 1 家 + 合规抑制 1 家"组合**。

### 🥇 第一选择 · TransUnion TruAudience —— 能力对等 + 合规最强

- **能力与 Experian 最对等**:身份解析(TUID/HHID)+ 跨设备 + 画像增强 + 受众市场,几乎一对一覆盖 Combined API。
- **合规最强**:征信局底座,G1-G7 基本全过,**能签 BAA → HIPAA 客户也能用**。
- **项目已有现成调研**:`TRANSUNION-INTEGRATION.md` 已写好,P2 已规划,切换成本最低。
- **唯一短板**:mTLS 证书 + 合同周期长(8-16 周);抑制需额外配。
- **适用**:想"一家顶替 Experian 主力"、客户里有健康类(HIPAA)品牌。

### 🥈 第二选择 · Acxiom InfoBase(经 LiveRamp Marketplace)—— 改动最小

- **工程改动最小**:项目**已集成 LiveRamp**(RampID 身份桥),把 InfoBase 挂在 LiveRamp Data Marketplace 上,不用新建身份通道。
- **画像库业界最大之一**:数千个消费者属性,深度够。
- **合规强**:G1-G7 基本全过。
- **短板**:抑制能力弱,需 LexisNexis 兜底。
- **适用**:想"最快落地、改动最少"。

### 🥉 必配项 · LexisNexis —— 合规抑制兜底(不是二选一,是必须)

- 换掉 Experian 画像可以,但 **Deceased / DNC / opt-out 抑制是法务硬门槛(G6),不能省**。
- 60+ 年数据底座,抑制专长,能签 BAA,合规最强。
- 上面两家(TransUnion/Acxiom)抑制都偏弱 → **必须由 LexisNexis 补这一环**,与任一主力组合使用。

### 推荐组合方案(按场景)

| 场景                                          | 推荐组合                                             | 合规前提                               |
| --------------------------------------------- | ---------------------------------------------------- | -------------------------------------- |
| **能力对等 + 有 HIPAA 客户**                  | TransUnion(主力)+ LexisNexis(抑制)                   | G3 BAA 必须 PASS                       |
| **最快落地 / 改动最小**                       | Acxiom InfoBase via LiveRamp(主力)+ LexisNexis(抑制) | G1-G7 全 PASS                          |
| **预算有限 + 纯营销(非 HIPAA)+ 可接受画像浅** | Versium REACH(画像)+ LexisNexis(抑制)                | 仅限非 HIPAA;须补 G1/G4/G5/G7 书面确认 |

> **一句话**:首选 **TransUnion**(能力对等 + 合规最强),想省事就 **Acxiom**(复用 LiveRamp),两者都**必须配 LexisNexis** 兜底合规抑制。纯 API 厂商(Versium/PDL/FullContact)只适合非 HIPAA 的轻量场景。

---

## 2. 全栈巨头(可做 Experian 主力替代)

### 2.1 TransUnion(TruAudience)🟢 首选替代

| 维度                       | 说明                                                                                                                                   |
| -------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| **能替代的 Experian 能力** | ✅ 身份解析(TUID/HHID)✅ 跨设备 ✅ 画像增强 ✅ 受众市场(Data Marketplace)⚠️ 抑制需额外配                                               |
| **优点**                   | 与 Experian 同级的全栈征信局数据;TruAudience 专为营销/广告设计;跨设备身份图强;本项目**已规划 P2 对接**(见 `TRANSUNION-INTEGRATION.md`) |
| **缺点**                   | 合同 + mTLS 证书门槛;企业级定价;对接周期长                                                                                             |
| **对接难度**               | 🔴 高 — mTLS 双向证书认证,非简单 API key                                                                                               |
| **官网**                   | https://www.transunion.com/solution/truaudience                                                                                        |
| **开发者文档**             | 需签约后经客户成功经理(CSM)开通 developer portal(无公开文档)                                                                           |

> **为什么列首选**:它是与 Experian 能力最对等的一家,且本项目已有集成文档与调研,切换成本相对最低。

### 2.2 Acxiom + LiveRamp(InfoBase + AbiliTec/RampID)🟢 强替代

| 维度                       | 说明                                                                                                                                   |
| -------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| **能替代的 Experian 能力** | ✅ 画像增强(InfoBase 数千个消费者属性)✅ 身份解析(AbiliTec / RampID)✅ 受众激活 ⚠️ 抑制能力弱                                          |
| **优点**                   | InfoBase 是业界最大的消费者画像库之一;**本项目已集成 LiveRamp**(RampID 身份桥),复用现有合同/通道成本低;people-based marketing 生态成熟 |
| **缺点**                   | Acxiom 与 LiveRamp 同属一个体系但产品线分散;数据采买为合同制;直接 API 不如纯 API 厂商友好                                              |
| **对接难度**               | 🟡 中 — 若复用现有 LiveRamp 通道则较低;新接 InfoBase 数据采买需合同                                                                    |
| **官网**                   | https://www.acxiom.com / https://liveramp.com                                                                                          |
| **开发者文档**             | LiveRamp:https://docs.liveramp.com ;Acxiom InfoBase 经 LiveRamp Data Marketplace 分发                                                  |

> **协同优势**:项目里已经有 LiveRamp,把 Acxiom InfoBase 当作"画像数据源"挂在 LiveRamp Marketplace 上,是改动最小的一条路。

### 2.3 Equifax 🟡 可选替代

| 维度                       | 说明                                                                                |
| -------------------------- | ----------------------------------------------------------------------------------- |
| **能替代的 Experian 能力** | ✅ 身份/反欺诈 ✅ 收入/财务画像(IXI 数据独家)⚠️ 营销画像不如 Experian/Acxiom 丰富   |
| **优点**                   | 三大征信局之一;**IXI 财务/资产数据是独家**(高净值人群定位强);反欺诈与身份验证能力强 |
| **缺点**                   | 营销侧产品线弱于 Experian Marketing Services;偏信贷/风控用途;合同制                 |
| **对接难度**               | 🔴 高 — 企业合同 + 合规审查                                                         |
| **官网**                   | https://www.equifax.com/business/                                                   |
| **开发者文档**             | https://developer.equifax.com/                                                      |

### 2.4 Epsilon(Publicis)🟡 可选替代

| 维度                       | 说明                                                                       |
| -------------------------- | -------------------------------------------------------------------------- |
| **能替代的 Experian 能力** | ✅ 画像增强 ✅ 受众/激活(CORE ID 身份)⚠️ 偏 CRM/忠诚度营销                 |
| **优点**                   | 交易数据(transactional data)强,购买行为预测准;Publicis 生态;CORE ID 身份图 |
| **缺点**                   | 更像"营销服务公司"而非"数据 API 供应商";自助式 API 能力有限,偏托管服务     |
| **对接难度**               | 🔴 高 — 合同 + 托管对接                                                    |
| **官网**                   | https://www.epsilon.com/                                                   |
| **开发者文档**             | 无公开开发者门户,经客户团队对接                                            |

### 2.5 Verisk Marketing Solutions(原 Infutor + Jornaya)🟡 可选替代

| 维度                       | 说明                                                                                    |
| -------------------------- | --------------------------------------------------------------------------------------- |
| **能替代的 Experian 能力** | ✅ 消费者身份解析(Infutor)✅ TCPA 同意验证(Jornaya 独家)✅ 画像                         |
| **优点**                   | **Jornaya 的 TCPA/同意验证是独家合规能力**(对 lead-gen 客户极有价值);消费者身份管理专精 |
| **缺点**                   | 品牌经多次并购整合(Infutor→Verisk Consumer Insights),产品线命名混乱;合同制              |
| **对接难度**               | 🟡 中 — 合同 + API                                                                      |
| **官网**                   | https://www.verisk.com/marketing/                                                       |
| **开发者文档**             | 经签约后开通(无完全公开门户)                                                            |

---

## 3. API 优先厂商(开发者友好 · 快速对接 · 画像深度较浅)

> 这一类是"几天能跑通"的轻量选择,适合**画像增强**场景,但消费者数据深度(尤其离线财务/Mosaic 级)不如征信局。**不能替代合规抑制**。

### 3.1 Versium REACH 🟢 对接最易

| 维度                       | 说明                                                                                                                |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| **能替代的 Experian 能力** | ✅ Demographic Append(年龄/性别/收入/房产/车辆/兴趣/政治倾向)✅ Contact Append ✅ 身份解析(B2B2C)❌ 不做合规抑制    |
| **优点**                   | **REST API + 交互式文档 + Google Sheets 插件 + MCP**,开发者体验业内顶级;按调用计费,无重合同;有专门的人口属性 4 大类 |
| **缺点**                   | 数据覆盖率/深度不如征信局;画像粒度中等;主打中小企业                                                                 |
| **对接难度**               | 🟢 低 — API key,几天可上线                                                                                          |
| **官网**                   | https://versium.com/                                                                                                |
| **开发者文档**             | https://api-documentation.versium.com/                                                                              |

### 3.2 People Data Labs(PDL)🟢 文档最佳

| 维度                       | 说明                                                                                                               |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| **能替代的 Experian 能力** | ✅ Person Enrichment(人口/职业/社交)⚠️ 偏 B2B/职业画像,消费者营销属性较弱 ❌ 不做合规抑制                          |
| **优点**                   | **文档与 SDK 业内最干净**(Python/Node/Ruby/Go/Java);可预测 JSON schema;1 credit/次成功调用,定价透明($0.20-0.28/次) |
| **缺点**                   | 偏 B2B 人物画像(职位/公司),消费者侧(收入/Mosaic/房产)弱;不适合纯 B2C 品牌                                          |
| **对接难度**               | 🟢 低 — `POST /v5/person/enrich`,API key                                                                           |
| **官网**                   | https://www.peopledatalabs.com/                                                                                    |
| **开发者文档**             | https://docs.peopledatalabs.com/docs/reference-person-enrichment-api                                               |

### 3.3 FullContact 🟢 实时身份解析

| 维度                       | 说明                                                                                                   |
| -------------------------- | ------------------------------------------------------------------------------------------------------ |
| **能替代的 Experian 能力** | ✅ 身份解析(email/phone→人物画像 + 社交 + 跨设备)✅ 实时(<200ms)⚠️ 画像偏社交/数字身份 ❌ 不做合规抑制 |
| **优点**                   | 实时 RESTful API;Insight Bundles 可选购;Snowflake External Functions 集成;有 Node SDK                  |
| **缺点**                   | 消费者离线画像深度不如征信局;更擅长"身份拼合"而非"画像增强"                                            |
| **对接难度**               | 🟢 低 — HTTPS POST + JSON,API key                                                                      |
| **官网**                   | https://www.fullcontact.com/                                                                           |
| **开发者文档**             | https://docs.fullcontact.com/                                                                          |

### 3.4 Data Axle 🟡 消费者+本地商户数据库

| 维度                       | 说明                                                                  |
| -------------------------- | --------------------------------------------------------------------- |
| **能替代的 Experian 能力** | ✅ 消费者画像库(2.8 亿+ 美国消费者)✅ 本地商户数据 ⚠️ 抑制需额外配    |
| **优点**                   | 消费者 + 商户双数据库;直邮/电话营销数据传统强项;有 API 与批量两种交付 |
| **缺点**                   | 数字身份/跨设备弱于纯 identity 厂商;API 现代化程度中等                |
| **对接难度**               | 🟡 中 — 合同 + API                                                    |
| **官网**                   | https://www.data-axle.com/                                            |
| **开发者文档**             | 经签约后提供(无完全公开门户)                                          |

### 3.5 Resonate 🟡 AI 心理/动机画像(差异化补充源)

| 维度                       | 说明                                                                                                                                                                         |
| -------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **能替代的 Experian 能力** | ✅ 画像增强(2.5 亿+ 消费者 · **15,000+ 属性**)✅ **心理/动机/价值观层**(Experian 弱项)✅ 实时信号 ❌ 不做合规抑制 ❌ 身份解析非强项                                          |
| **优点**                   | 自有 **rAI** 引擎,预测"为什么买"而非只给人口标签;2026 新品 **Cortex(agentic AI)/ Ignition(代理商全链路)/ Predictive Install(数据灌入自有环境)** 与我们的受众洞察场景高度契合 |
| **缺点**                   | 偏"受众平台"而非原始数据 API,自助深度集成能力需确认;无合规抑制;**与本项目定位部分重叠(见下)**                                                                                |
| **对接难度**               | 🟡 中 — 平台/合同制,API 深度需确认                                                                                                                                           |
| **官网**                   | https://www.resonate.com/                                                                                                                                                    |
| **开发者文档**             | 数据产品见 https://www.resonate.com/data/ ;无完全公开开发者门户,经签约开通                                                                                                   |
| **合规初判**               | 🟡 中 — G1/G4/G5/G7 须书面确认;**BAA 能力待确认 → 默认仅非 HIPAA 场景**;G6 抑制必须由 LexisNexis 兜底                                                                        |

> ⚠️ **双重身份提醒**:Resonate 不只是数据供应商,它的 **Cortex + Ignition** 正在做"AI 帮 Agency 从受众洞察到一键投放全链路",**与 ReceptivIQ 核心定位直接竞争**。详见 [`COMPETITIVE-LANDSCAPE.md`](./COMPETITIVE-LANDSCAPE.md)。选它做数据源前,需评估"把数据/受众能力交给一个潜在竞争对手"的战略风险。

### 3.6 Claritas PRIZM Premier 🟢 心理分群(官方四源栈成员)

| 维度                       | 说明                                                                                                                                                                                    |
| -------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **能替代的 Experian 能力** | ✅ **Mosaic 等价的心理分群**(68 个 household segment / 11 Lifestage / 14 Social Group)⚠️ 不做个体级身份解析 ❌ 不做合规抑制                                                             |
| **优点**                   | **与 Mosaic 在 publisher/DSP 层功能可互换**(Rose 在 Session 2 已确认)→ persona 可无损携带到 StackAdapt / Trade Desk / Basis / Viant / Meta;数据底座含 Epsilon/Valassis/Data Axle/TomTom |
| **缺点**                   | 主要是"分群标签"而非全量属性;需配 TransUnion 提供个体级身份与人口数据                                                                                                                   |
| **对接难度**               | 🟡 中 — 合同 + 样本文件                                                                                                                                                                 |
| **官网**                   | https://claritas.com/prizm-premier/                                                                                                                                                     |
| **开发者文档**             | 段落说明见 https://claritas360.claritas.com/mybestsegments/ ;数据交付经签约                                                                                                             |
| **合规初判**               | 🟢 较强 — 分群为聚合标签,PII 暴露面小;G6 抑制仍需 LexisNexis 兜底                                                                                                                       |

### 3.7 GWI 🟢 态度/文案信号(官方四源栈成员)

| 维度                       | 说明                                                                                                                                                                          |
| -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **能替代的 Experian 能力** | (Experian 无对等)—— **增量能力**:态度、价值观、媒介习惯、品牌好感、"为什么买"                                                                                                 |
| **优点**                   | 1.4M+ always-on 调研 / 52+ 市场 / 250K+ profiling points;**直接驱动 Pillar 3 文案 Agent 的"信息接受度"层**,让其在 Phase 1 即可演示;**提供公开 API + MCP 连接器**(可接 Claude) |
| **缺点**                   | 调研型样本(非全量人口普查级),需与 TransUnion/Claritas 的确定性数据互补;不做身份/抑制                                                                                          |
| **对接难度**               | 🟢 低-中 — **有公开 Platform API + MCP**,工程友好;数据授权需合同                                                                                                              |
| **官网**                   | https://www.gwi.com/                                                                                                                                                          |
| **开发者文档**             | https://www.gwi.com/api ;API 入门 https://api.globalwebindex.com/docs/platform-api/getting-started/introduction                                                               |
| **合规初判**               | 🟢 较强 — 调研聚合数据,PII 风险低;G6 抑制仍需兜底                                                                                                                             |

---

## 4. 合规抑制(Suppression)专项替代

> Experian Suppression Files(DNM/DNC/Deceased)是**法务硬门槛**,上面的 API 厂商都**不覆盖**。需单独选这一类供应商。

| 供应商                         | 覆盖                                   | 优点                                     | 对接难度             | 官网                               |
| ------------------------------ | -------------------------------------- | ---------------------------------------- | -------------------- | ---------------------------------- |
| **LexisNexis**                 | Deceased / 信息抑制 / DNC              | 60+ 年数据底座;权威                      | 🔴 高(合同+合规)     | https://risk.lexisnexis.com/       |
| **AccuData**                   | Deceased / DMA Pander / TPS            | 基于 LexisNexis 数据;非营利/直邮场景成熟 | 🟡 中                | https://www.accudata.com/          |
| **Webbula**                    | Email Hygiene(spam trap/蜜罐/无效邮箱) | Email 侧威胁检测强                       | 🟢 低                | https://webbula.com/email-hygiene/ |
| **DMA/ANA + FTC DNC Registry** | 行业 Pander / 国家级 DNC               | 行业标准合规名单                         | 🟡 中(注册+周期更新) | https://www.ftc.gov/ (DNC)         |

> **建议**:Deceased + DNC 用 LexisNexis 或 AccuData;Email 投放额外挂 Webbula 做卫生检测。

---

## 5. 选型决策矩阵

> **前置条件:下表所有推荐均假设该供应商已通过 §0 的 7 道合规闸门。合规未过 → 不论诉求,直接排除。**

| 如果客户的核心诉求是…                | 推荐替代                                         | 理由                        | 合规前提                                   |
| ------------------------------------ | ------------------------------------------------ | --------------------------- | ------------------------------------------ |
| **HIPAA 健康类客户**                 | TransUnion / Acxiom / Equifax(+ LexisNexis 抑制) | 只有能签 BAA 的全栈巨头合规 | **G3 BAA 必须 PASS**                       |
| **与 Experian 全栈对等**             | TransUnion TruAudience                           | 能力最对等,项目已有集成调研 | G1-G7 全 PASS                              |
| **复用现有 LiveRamp、改动最小**      | Acxiom InfoBase(经 LiveRamp Marketplace)         | 不新增身份通道              | G1-G7 全 PASS                              |
| **高净值 / 财务定位**                | Equifax(IXI 数据)                                | 财务画像独家                | G4 FCRA 用途限定须明确                     |
| **Lead-gen / TCPA 合规**             | Verisk(Jornaya)                                  | 同意验证独家                | G1/G4                                      |
| **快速上线、预算有限、可接受画像浅** | Versium REACH / PDL / FullContact                | API 友好、按量计费          | **仅限非 HIPAA;须补 G1/G4/G5/G7 书面确认** |
| **只缺合规抑制**                     | LexisNexis / AccuData + Webbula                  | 专项补齐                    | G6 兜底,任何方案都不能省                   |

---

## 6. 对接难度总览(给工程排期参考)

| 供应商              | 认证方式             | 预估对接周期 | 计费模式     |
| ------------------- | -------------------- | ------------ | ------------ |
| Versium REACH       | API key              | **2-5 天**   | 按调用量     |
| People Data Labs    | API key              | **2-5 天**   | 按 credit    |
| FullContact         | API key              | **2-5 天**   | 按调用量     |
| Data Axle           | API key + 合同       | 2-4 周       | 合同         |
| Acxiom(经 LiveRamp) | 复用 LiveRamp        | 1-3 周       | 数据采买合同 |
| Verisk / Epsilon    | 合同 + API           | 4-8 周       | 合同         |
| Equifax             | 合同 + 合规审查      | 8-12 周      | 合同         |
| TransUnion          | 合同 + **mTLS 证书** | 8-16 周      | 合同         |
| LexisNexis(抑制)    | 合同 + 合规          | 8-12 周      | 合同         |

> 本项目 `BaseAdapter` 模式(见 `CLAUDE.md` · ETL Adapter Pattern)对**纯 API 厂商**最友好:新增一个 `services/etl/adapters/<provider>.py` 即可,几天能接。合同制巨头的瓶颈在**法务/采购周期**,不在代码。

---

## 7. 合规提醒(选任何替代都适用)

1. **数据来源合法性举证** — 任何第三方数据商必须能证明其数据持有合法 consent(GDPR/CCPA);签约前索取其 DPA / 合规证明,存档 `data_source_attestation`。
2. **用途限定** — 合同须写明"仅用于营销,不用于信贷/雇佣决策"(避免触发 FCRA)。
3. **入仓仍须哈希** — 无论换哪家,进数据仓库前一律 `hash_identifier()`,禁止明文 PII 落仓(见 `CLAUDE.md` 数据仓库入仓规则)。
4. **抑制不可省** — 换掉 Experian 画像可以,但 Deceased/DNC 抑制是法务硬门槛,必须有等价供应商兜底。
5. **审计留痕** — 每次第三方调用写 `enrichment.<provider>.completed` 审计事件,记录 match_score 与计费。

---

## 8. 相关文档

- 端到端数据流:[`END-TO-END-DATA-FLOW.md`](./END-TO-END-DATA-FLOW.md)
- Experian 接口清单:[`EXPERIAN-APIS-TO-CONFIRM.md`](./EXPERIAN-APIS-TO-CONFIRM.md)
- TransUnion 集成:[`TRANSUNION-INTEGRATION.md`](./TRANSUNION-INTEGRATION.md)
- 竞品全景:[`COMPETITIVE-LANDSCAPE.md`](./COMPETITIVE-LANDSCAPE.md)

---

## 来源(已核实链接)

- [Top 12 Experian Competitors & Alternatives 2026 — Latterly](https://www.latterly.org/experian-competitors/)
- [Top 5 Equifax Alternatives 2026 — Compliancely](https://compliancely.com/blog/equifax-alternatives/)
- [Versium REACH API Reference](https://api-documentation.versium.com/reference/welcome)
- [Versium Demographic Append API](https://api-documentation.versium.com/reference/demographic-append-api)
- [People Data Labs — Person Enrichment API docs](https://docs.peopledatalabs.com/docs/reference-person-enrichment-api)
- [FullContact Developer Docs](https://docs.fullcontact.com/)
- [Acxiom Identity Services](https://www.acxiom.co.uk/what-we-do/identity-services/)
- [Verisk — LiveRamp Partner Directory](https://partner-directory.liveramp.com/partners/verisk)
- [LexisNexis Risk Solutions](https://risk.lexisnexis.com/)
- [Webbula Email Hygiene](https://webbula.com/email-hygiene/)
- [Best Data Enrichment APIs 2026 — Databar](https://databar.ai/blog/article/best-data-enrichment-apis-2026-technical-guide-for-developers)
