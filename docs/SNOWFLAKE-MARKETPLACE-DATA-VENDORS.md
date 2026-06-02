# Snowflake Marketplace 数据供应商选型(B2B + B2C 双侧)

_Last updated: **2026-05-26**_

> **文档类型**:供应商选型调研(Snowflake Marketplace 通道)
> **目标读者**:后端 / 数据 / 产品 / 采购 / 合规
> **目的**:列出可通过 **Snowflake Marketplace** 直接接入的数据供应商,**两类合并覆盖**:
>
> - **§1-2 B2B / PDL 类**(人物/公司增强,职业身份)
> - **§2-bis B2C / 类 Experian**(消费者画像,12 家)
>
> 逐家给出优缺点、对接难度、官网与文档,并说明在 ReceptivIQ 中的工程/合规优势。
> **前提**:所有 Snowflake Marketplace listing 链接均在 2026-05 经联网检索核实。商业条款以签约时为准。

---

## 0. 为什么单独写这份(关键)

> **Snowflake Marketplace = 数据界的 App Store**:供应商把数据以 **Secure Data Sharing** 形式挂上去,你订阅后,数据**直接以共享 schema 出现在你的 Snowflake 账户里 —— 零拷贝、零 ETL、SQL 即可 JOIN**。

对比传统 REST API / SFTP 交付,这是一次代际升级,**特别契合我们项目** —— 生产环境 `WAREHOUSE_BACKEND = snowflake`,意味着我们可以**绕过为每个 vendor 写 BaseAdapter** 的传统成本,把工程精力放在合成层(护城河)。

详见后文 §3 项目优势。

---

## 1. 候选清单(7 家)

| #   | 供应商                                    | 数据焦点                             | Snowflake Marketplace    | 主合规等级         |
| --- | ----------------------------------------- | ------------------------------------ | ------------------------ | ------------------ |
| 1   | **People Data Labs(PDL)**                 | 30 亿+ 个人 + 公司(B2B/职业偏强)     | ✅                       | 🟡 中              |
| 2   | **Experian Marketing Services**           | 2.5 亿美国消费者 + Mosaic + 垂直深度 | ✅ ConsumerView + Health | 🟢 强              |
| 3   | **ZoomInfo Data-as-a-Service**            | B2B 联系人 + 公司 + 意向数据         | ✅                       | 🟡 中(GDPR 需配置) |
| 4   | **Clearbit(HubSpot Breeze Intelligence)** | B2B 公司 + 人物增强                  | ⚠️(经 HubSpot)           | 🟡 中              |
| 5   | **Cognism**                               | B2B 联系人(EMEA + GDPR 友好)         | 部分通过合作             | 🟢 强(GDPR 内生)   |
| 6   | **Apollo.io**                             | B2B 销售联系人 + 意向                | ⚠️(主推 API)             | 🟡 中              |
| 7   | **Data Axle(Business)**                   | 商户/消费者数据库                    | ✅                       | 🟡 中-强           |
| 8   | **AnalyticsIQ**                           | 消费者营销数据                       | ✅                       | 🟡 中              |

> 第 1、2 家已在 [`EXPERIAN-ALTERNATIVES.md`](./EXPERIAN-ALTERNATIVES.md) 详述,这里聚焦 Snowflake 通道下的工程视角对比。
>
> ⚠️ **本节(§1-2)偏 B2B / PDL 类**(职业身份增强);**消费者侧 12 家**(TransUnion / Acxiom / Resonate / Numerator / Circana / Cuebiq 等类 Experian B2C 数据源)单独列在 [§2-bis](#2-bis-消费者侧数据源b2c--类-experian)。

---

## 2. 各家详解

### 2.1 People Data Labs(PDL)— 基准

| 维度                 | 说明                                                                                     |
| -------------------- | ---------------------------------------------------------------------------------------- |
| **数据规模**         | 30 亿+ 个人画像 · 全量公司数据集(免费 Company Dataset 可热身)                            |
| **数据特色**         | **B2B/职业画像最强**(职位、技能、公司关联);消费者营销侧弱                                |
| **Snowflake 通道**   | ✅ Marketplace listing(可用 Snowflake committed spend 直购)                              |
| **API 通道**         | ✅ 文档与 SDK 业内最佳(Python/Node/Ruby/Go/Java)                                         |
| **优点**             | 文档清晰;价格透明 $0.20-0.28/credit;零 ETL JOIN 即用;免费 Company Dataset 试水           |
| **缺点**             | B2B 偏向,消费者深度不足;**不签 BAA → HIPAA 客户淘汰**;不做合规抑制;G1 数据来源需书面确认 |
| **对接难度**         | 🟢 Snowflake 路径 1 天 / API 路径 2-5 天                                                 |
| **官网**             | https://www.peopledatalabs.com/                                                          |
| **Snowflake 集成页** | https://www.peopledatalabs.com/integrations/snowflake                                    |
| **API 文档**         | https://docs.peopledatalabs.com/docs/reference-person-enrichment-api                     |
| **适用**             | B2B 营销 / ABM / 快速 POC / 验证合成层逻辑                                               |

### 2.2 Experian Marketing Services — 消费者深度第一

| 维度                  | 说明                                                                                                                      |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| **数据规模**          | 2.5 亿美国消费者 · ~2,300 属性 · 6,339 个营销字段字典(见我们之前的 Excel 分析)                                            |
| **数据特色**          | Mosaic / TrueTouch / Auto / Finance 垂直深度无可替代                                                                      |
| **Snowflake 通道**    | ✅ `Experian Marketing Services: ConsumerView` + `Experian Marketing Services: Health`                                    |
| **2026 强化**         | Aperture Data Studio 集成(2026.02)+ Identity Graph 在 Snowflake Data Clean Rooms GA                                       |
| **优点**              | 数据深度业界第一;**能签 BAA(HIPAA 可用)**;Data Clean Room 原生支持;绕过传统季度 S3 文件死路                               |
| **缺点**              | 价格重(企业合同 $25K-500K/年);Mosaic 输出可识别 → vendor lock-in 风险仍存在;只有 1,355/6,339 字段是 FLA Friendly,用前要筛 |
| **对接难度**          | 🟡 Snowflake listing 订阅 + 法务合同 2-4 周                                                                               |
| **官网**              | https://www.experian.com/                                                                                                 |
| **Snowflake listing** | https://app.snowflake.com/marketplace/listing/GZSTZNOU5/experian-marketing-services-consumerview                          |
| **Health listing**    | https://app.snowflake.com/marketplace/listing/GZSTZNOVE                                                                   |
| **2026 集成新闻**     | https://www.experianplc.com/newsroom/press-releases/2026/experian-announces-integration-with-snowflake-s-ai-data-cloud    |
| **适用**              | B2C 主战场 / 健康类 HIPAA 客户 / Phase 2 enrichment(非 Pillar 1 地基)                                                     |

### 2.3 ZoomInfo Data-as-a-Service — B2B 联系人之王

| 维度                  | 说明                                                                                         |
| --------------------- | -------------------------------------------------------------------------------------------- |
| **数据规模**          | 数亿 B2B 联系人 + 公司全景 + 意向数据                                                        |
| **数据特色**          | B2B 联系人覆盖最深;意向(intent)信号原生;企业级                                               |
| **Snowflake 通道**    | ✅ Marketplace listing                                                                       |
| **优点**              | B2B 行业标杆;Snowflake 路径成熟;集成生态广                                                   |
| **缺点**              | 价格贵(企业合同);GDPR 合规需特别配置;数据更新频率信息需签约后确认                            |
| **对接难度**          | 🟡 Snowflake 订阅 + 合同                                                                     |
| **官网**              | https://www.zoominfo.com/                                                                    |
| **Snowflake listing** | https://app.snowflake.com/marketplace/listing/GZSNZ1DPLO/zoominfo-zoominfo-data-as-a-service |
| **适用**              | 重 B2B Agency / ABM 场景 / 销售-营销协同需求                                                 |

### 2.4 Clearbit(HubSpot Breeze Intelligence)— 与 HubSpot 同源

| 维度                 | 说明                                                                           |
| -------------------- | ------------------------------------------------------------------------------ |
| **数据特色**         | 实时 B2B 公司 + 人物增强;HubSpot 收购后整合为 Breeze Intelligence              |
| **Snowflake 通道**   | ⚠️ 经 HubSpot 数据集成路径(非独立 listing);确认走 HubSpot adapter 还是直接增强 |
| **优点**             | **项目已集成 HubSpot adapter** → 路径最短;实时增强;数据质量稳定                |
| **缺点**             | 独立 Snowflake listing 不明确;HubSpot 客户绑定较深                             |
| **对接难度**         | 🟢 经 HubSpot 已有路径 / 🟡 独立访问需另谈                                     |
| **官网**             | https://www.hubspot.com/products/breeze-intelligence                           |
| **HubSpot 集成参考** | [`HUBSPOT-INTEGRATION.md`](./HUBSPOT-INTEGRATION.md)                           |
| **适用**             | 客户主要用 HubSpot CRM 的场景 / 实时 lead 增强                                 |

### 2.5 Cognism — GDPR 友好的 B2B(EMEA 强)

| 维度               | 说明                                                      |
| ------------------ | --------------------------------------------------------- |
| **数据特色**       | B2B 联系人 + 手机号验证;**GDPR 合规内生**(EMEA 首选)      |
| **Snowflake 通道** | ⚠️ 部分通过合作,直接 listing 待确认                       |
| **优点**           | **GDPR 合规最强**;DNC 主动筛查(欧洲 27 国);手机号验证率高 |
| **缺点**           | 北美覆盖不如 ZoomInfo;Snowflake 直连路径未完全公开        |
| **对接难度**       | 🟡 合同 + API,Snowflake 通道需确认                        |
| **官网**           | https://www.cognism.com/                                  |
| **适用**           | 有 EMEA 客户 / GDPR 严格场景 / 手机号触达需求             |

### 2.6 Apollo.io — B2B 销售型联系人

| 维度               | 说明                                                                |
| ------------------ | ------------------------------------------------------------------- |
| **数据特色**       | 2.7 亿+ B2B 联系人;主打 sales engagement(不只是数据,还有触达工作流) |
| **Snowflake 通道** | ⚠️ 主推 REST API(Snowflake 通道有限)                                |
| **优点**           | 价格亲民;API 友好;销售-数据一体                                     |
| **缺点**           | 数据质量在 PDL/ZoomInfo 之下;非纯数据公司,部分功能与营销平台重叠    |
| **对接难度**       | 🟢 API + key                                                        |
| **官网**           | https://www.apollo.io/                                              |
| **适用**           | 中小 Agency 验证 / 销售工作流增强                                   |

### 2.7 Data Axle Business — 消费者 + 商户双库

| 维度                  | 说明                                                      |
| --------------------- | --------------------------------------------------------- |
| **数据特色**          | 2.8 亿+ 美国消费者 + 商户数据库;直邮/电话营销传统强项     |
| **Snowflake 通道**    | ✅ Marketplace listing(Data Axle: Business Data)          |
| **优点**              | 消费者 + 商户双数据库;Snowflake 通道成熟                  |
| **缺点**              | 数字身份 / 跨设备弱于纯 identity 厂商                     |
| **对接难度**          | 🟡 Snowflake 订阅 + 合同                                  |
| **官网**              | https://www.data-axle.com/                                |
| **Snowflake listing** | https://app.snowflake.com/marketplace/listing/GZSTZ49OTF5 |
| **适用**              | 直邮 / 电话营销 / 本地商户营销                            |

### 2.8 AnalyticsIQ — 消费者画像新锐

| 维度                  | 说明                                                         |
| --------------------- | ------------------------------------------------------------ |
| **数据特色**          | 消费者营销画像 · 心理 + 人口 + 行为                          |
| **Snowflake 通道**    | ✅ Marketplace listing(AnalyticsIQ: Consumer Marketing Data) |
| **优点**              | 心理画像独家方法论 · Snowflake 通道现成                      |
| **缺点**              | 品牌知名度不如 Experian/TransUnion · 数据覆盖广度待评估      |
| **对接难度**          | 🟢 Snowflake 订阅                                            |
| **官网**              | https://analytics-iq.com/                                    |
| **Snowflake listing** | (在 Marketplace 搜 `AnalyticsIQ`)                            |
| **适用**              | 寻找 Experian Mosaic 之外的"心理画像"补充源                  |

---

## 2-bis. 消费者侧数据源(B2C / 类 Experian)

> §1-2 偏 B2B / PDL 类(职业身份);**本节专门列与 Experian 同侧的 B2C 消费者数据源**,均在 Snowflake Marketplace 可直连 / 已合作上架。所有 listing 已联网核实。

### 2-bis.1 候选清单(12 家)

| #   | 供应商                             | 数据类型                                     | Snowflake 通道                         | 与 Experian 关系                       |
| --- | ---------------------------------- | -------------------------------------------- | -------------------------------------- | -------------------------------------- |
| C1  | **TransUnion TruIQ / TruAudience** | 人口 + 信贷脱敏 + 身份 + 渠道倾向            | ✅ TruIQ Data Enrichment listing       | 🟢 最对等(Pillar 1 锚)                 |
| C2  | **Acxiom InfoBase**                | 消费者画像数千属性 + 身份(AbiliTec)          | ✅ Snowflake "Leader in Identity" 2026 | 🟢 与 Experian 同级巨头                |
| C3  | **Resonate**                       | AI 心理 / 动机画像 · 2.5 亿消费者 / 15K 属性 | ✅ 2023 上线                           | 🟡 补 Mosaic 弱项(心理层)⚠️ 同时是竞品 |
| C4  | **AnalyticsIQ**(已在 §2.8)         | 消费者营销画像 · 心理 + 人口                 | ✅                                     | 🟡 心理画像补充源                      |
| C5  | **Numerator**                      | 消费者购买面板 · OmniPanel                   | ✅ Snowflake 合作                      | 🟡 补"实际购买"——Experian 弱项         |
| C6  | **Circana**(原 IRI + NPD)          | 零售 / CPG 销售 + 消费者面板                 | ✅ Snowflake 合作                      | 🟡 零售 POS 强项                       |
| C7  | **Catalina**                       | 商超购物者营销 + 优惠券                      | ✅ Snowflake Data Cloud 合作           | 🟡 杂货/CPG 触达                       |
| C8  | **Cuebiq**                         | 移动位置 / 客流 / 到店                       | ✅ Brand Affinity listing              | 🟢 补线下行为——Experian 几乎为零       |
| C9  | **Data Axle Consumer**(已在 §2.7)  | 2.8 亿消费者 + 商户                          | ✅                                     | 🟡 直邮/电话强项                       |
| C10 | **Alliant**                        | 多渠道交易数据(消费者合作社)                 | ✅(也是 Experian 市场伙伴)             | 🟡 交易行为补充                        |
| C11 | **Attain**                         | 真实购买/消费(panel-based)                   | ✅ Snowflake 合作                      | 🟡 实际花销数据                        |
| C12 | **Webbula**                        | Email Hygiene(蜜罐/无效邮箱)                 | ✅ Snowflake                           | 🟡 投放前 email 卫生(非画像)           |

### 2-bis.2 按"补 Experian 哪个弱项"分组

| 弱项                                  | 推荐补强                                                         |
| ------------------------------------- | ---------------------------------------------------------------- |
| 🟢 **可主力替代** Experian            | **TransUnion TruIQ**(Pillar 1 锚)· **Acxiom InfoBase**(改动最小) |
| 🟡 补 **心理 / 动机层**(Mosaic 之外)  | **Resonate** ⭐ · **AnalyticsIQ**                                |
| 🟡 补 **实际购买行为**(Experian 最弱) | **Numerator** · **Circana** · **Attain** · **Catalina**          |
| 🟡 补 **线下 / 位置 / 到店**          | **Cuebiq**(主推 Snowflake)· Placer.ai(P2 路线)                   |
| 🟡 补 **多渠道交易行为**              | **Alliant**                                                      |
| 🟡 投放前 **Email 卫生**              | **Webbula**(注意:不是合规抑制,抑制仍需 LexisNexis)               |

### 2-bis.3 各家详解(关键 4 家)

#### C1 · TransUnion TruIQ / TruAudience(已是 Pillar 1 锚)

- **数据**:身份 TUID/HHID + 数百人口属性 + 跨设备 + 渠道倾向;覆盖 98% 美国成人 / 1.27 亿家庭
- **Snowflake**:TruIQ Data Enrichment listing,**脱敏信贷数据按需访问**
- **优点**:Snowflake 通道让原本 mTLS + 合同的重接入大幅简化;可签 BAA → HIPAA 可用
- **官网**:https://www.transunion.com/lp/identity-snowflake
- **新闻稿**:https://newsroom.transunion.com/transunion-partners-with-snowflake-to-provide-on-demand-access-to-pseudonymized-credit-data/
- **法务说明**:https://www.transunion.com/legal/snowflake-marketplace
- 详见 [`TRANSUNION-INTEGRATION.md`](./TRANSUNION-INTEGRATION.md)

#### C2 · Acxiom InfoBase

- **数据**:InfoBase 数千个消费者属性 + AbiliTec 身份解析;**全球覆盖**
- **Snowflake**:2026 被 Snowflake 评为 **"Leader in Identity & Onboarding"** + "One to Watch in Collaboration"
- **优点**:与 Experian 同级数据深度;项目已集成 LiveRamp → 复用通道再加 Snowflake listing,**改动成本最小**
- **缺点**:数据合同仍重(企业级)
- **官网**:https://www.acxiom.com/
- **Snowflake listing**:https://app.snowflake.com/marketplace/listings/Acxiom
- **2026 认证**:https://www.acxiom.com/news/snowflake-modern-marketing-data-stack/

#### C3 · Resonate ⚠️(数据源 + 竞品双重身份)

- **数据**:2.5 亿美国消费者 / **15,000+ rAI 预测属性** · 心理 / 价值观 / 动机层
- **Snowflake**:2023 上线 Marketplace,提供个体级隐私安全数据
- **优点**:**Experian Mosaic 不提供的"为什么买"层**;Cortex / Ignition 2026 新品强化 agentic AI
- ⚠️ **双重身份**:同时是 ReceptivIQ 的潜在竞品(详见 [`COMPETITIVE-LANDSCAPE.md` §2.8](./COMPETITIVE-LANDSCAPE.md));采购前评估"把心理洞察依赖给竞争对手"的战略风险
- **官网**:https://www.resonate.com/
- **Snowflake 发布**:https://www.resonate.com/newsroom/resonate-launches-access-to-industry-spanning-privacy-safe-proprietary-ai-powered-data-on-snowflake-marketplace/

#### C5+C6+C11 · Numerator / Circana / Attain(购买行为三件套)

- **共同价值**:**Experian 几乎不提供"实际购买"数据**,这三家用 panel + POS + 收据建模填补:
  - **Numerator** —— 消费者购物面板,擅长 omni-channel(线上+线下+电商)
  - **Circana**(2023 IRI + NPD 合并)—— 零售 POS + 出货数据,CPG/快消行业标准
  - **Attain** —— panel-based 真实花销,可看到信用卡级别消费
- **Snowflake**:都在 Marketplace,可直接 JOIN
- **优点**:补 Persona Engine 的 "buying signals" 维度;Pillar 6 Attribution Agent 的离线转化数据来源
- **缺点**:panel 是抽样,**不要当成 universe 数据用**;Resonate 风险也适用(部分公司有自己的 AI 营销产品)
- **官网**:
  - Numerator: https://www.numerator.com/
  - Circana: https://www.circana.com/
  - Attain: https://www.attaindata.io/

#### C8 · Cuebiq(线下到店)

- **数据**:移动位置 / 客流 / Brand Affinity(到店行为推测品牌偏好)
- **Snowflake**:Brand Affinity dataset 已在 Marketplace
- **优点**:**Experian / TransUnion / Claritas 都几乎不覆盖线下到店行为**;Cuebiq 是 Snowflake 通道下改动最小的填补方式;支持 O2O 归因
- **缺点**:数据是基于 MAID(移动广告 ID)推断,iOS 14+ 隐私变化后覆盖率下降需评估
- **官网**:https://cuebiq.com/
- **Snowflake 案例**:https://cuebiq.com/blog/snowflake_marketplace_brand_affinity/

### 2-bis.4 其他补充

- **C7 Catalina** —— 杂货/快消行业的购物者营销标杆,Snowflake Retail Data Cloud 合作伙伴。Loyalty/优惠券触达场景使用
- **C10 Alliant** —— 多渠道消费者合作社数据,常作为 Experian 市场伙伴出现;独立 Snowflake 通道也有
- **C12 Webbula** —— Email Hygiene(检测蜜罐 / 无效邮箱);**注意**:这是邮件投递质量,**不是 G6 合规抑制**(Deceased/DNC 仍需 LexisNexis)

### 2-bis.5 给项目的客户类型 → 推荐组合

| 客户类型              | 推荐补 Experian 的 Snowflake 消费者数据源               |
| --------------------- | ------------------------------------------------------- |
| **CPG / 零售 / 快消** | Numerator + Circana + Catalina(购买行为) + Cuebiq(到店) |
| **DTC / 数字原生**    | Resonate(心理) + Numerator(购买) + Cuebiq(位置)         |
| **金融 / 保险**       | TransUnion(锚) + Acxiom + Alliant                       |
| **健康 / HIPAA**      | Acxiom(能签 BAA) + Experian Health listing              |
| **本地实体店**        | Cuebiq + Catalina + Data Axle                           |
| **EMEA 客户**         | Acxiom(全球覆盖)+ Cognism(GDPR)                         |

### 2-bis.6 合规速查(本节 12 家共同适用)

- 所有 vendor 仍走 [§0 七闸门](./EXPERIAN-ALTERNATIVES.md);Snowflake 通道在 G5/G7 天然加分
- **G3 BAA(HIPAA)**:Acxiom / TransUnion 通常可谈;Resonate / Numerator / Cuebiq 默认不签 → HIPAA 客户慎用
- **G6 抑制**:本节 12 家**都不覆盖**,**必须 LexisNexis 兜底**
- **G1 数据来源**:每家 listing 上架前已过 Snowflake 审核,但签约前仍索取其 DPA + consent 链路证明
- **panel-based 数据(Numerator/Attain/Circana)**:注意"面板代表性"问题,**不要当作 universe 数据**用于个体级触达

---

## 3. 在 ReceptivIQ 中的核心优势 ⭐

### 3.1 与项目架构契合 —— 零 adapter 工程

项目 `WAREHOUSE_BACKEND` 设计本就**支持 Snowflake 生产后端**:

```
开发期: WAREHOUSE_BACKEND=duckdb
生产期: WAREHOUSE_BACKEND=snowflake
        ↓
Snowflake Marketplace 订阅数据 = 直接以共享 schema 出现
        ↓
写 SQL JOIN 即可,无须写 BaseAdapter
```

→ **省掉本来要为每家写的 `services/etl/adapters/<vendor>.py`**(原本 2-5 天/家)。

### 3.2 与四源合成栈协同(Pillar 1)

| 四源栈成员                             | 是否在 Snowflake Marketplace |
| -------------------------------------- | ---------------------------- |
| TransUnion TruAudience                 | ✅                           |
| Claritas PRIZM                         | ✅(数据合作)                 |
| GWI                                    | ⚠️(主推 API + MCP)           |
| LiveRamp                               | ✅(深度集成,Data Clean Room) |
| Experian / PDL / ZoomInfo /...(本文档) | ✅                           |

→ **整个四源栈 + 补充画像源都能在 Snowflake 内做 SQL 合成**,不必为每家维护 adapter / 监控 / 凭据。

### 3.3 合规优势(对照 §0 七闸门)

| 闸门            | Snowflake 通道的天然加分                                                     |
| --------------- | ---------------------------------------------------------------------------- |
| G1 数据来源     | listing 上架已经过 Snowflake provider 审核                                   |
| G2 DPA          | Snowflake 标准合同 + provider DPA 双重保障                                   |
| G5 DSAR         | 数据停留在 provider 域,数据主体删除时只需通知 provider,不必跨多个 ETL 仓清理 |
| G7 安全         | 全程 SOC 2 加密,无公网传输                                                   |
| Data Clean Room | 跨方做 lookalike / 归因不动 PII —— **天然满足 G1/G5/G7**                     |

> ⚠️ **G3 BAA**(HIPAA)仍要逐家确认 —— Snowflake 通道**不自动赋予 BAA 能力**,Experian Health listing 是显式例外。
> ⚠️ **G6 合规抑制**(Deceased/DNC)仍需 **LexisNexis 兜底** —— 上述 8 家都不覆盖。

### 3.4 工程成本对比

| 集成方式                       | 单家工作日   | 维护成本                           |
| ------------------------------ | ------------ | ---------------------------------- |
| 传统 REST API + adapter        | 2-5 天       | 每家一套监控 + 凭据 + 错误重试     |
| 传统 SFTP + 季度回放           | 1-2 周       | 文件版本管理 + 回灌逻辑            |
| **Snowflake Marketplace 订阅** | **0.5-1 天** | **统一 Snowflake 监控 + 单一凭据** |

### 3.5 给我们项目的关键决策

| 决策点                                     | 建议                                        |
| ------------------------------------------ | ------------------------------------------- |
| **生产 warehouse 升级到 Snowflake 优先级** | 提到 Phase 1 / Sprint 0-1,解锁本通道        |
| **POC 数据源首选**                         | **PDL**(便宜、零 ETL、文档好)               |
| **B2C 主力增强**                           | Experian ConsumerView on Snowflake(Phase 2) |
| **HIPAA 客户**                             | Experian Health listing(可签 BAA)           |
| **EMEA / GDPR 严格**                       | Cognism(独立通道,补 PDL/ZoomInfo)           |
| **抑制(必配)**                             | LexisNexis(Snowflake 路径无替代)            |

---

## 4. 选型决策矩阵(按场景)

| 场景                 | 推荐                                | 备注                |
| -------------------- | ----------------------------------- | ------------------- |
| **B2B / ABM 验证**   | PDL → ZoomInfo → Apollo             | 价格阶梯            |
| **B2C 营销主战场**   | Experian ConsumerView + AnalyticsIQ | Mosaic + 心理补充   |
| **HIPAA 健康类**     | Experian Health(能签 BAA)           | 唯一通过 G3         |
| **EMEA / GDPR 严格** | Cognism + PDL                       | GDPR 友好双源       |
| **HubSpot 客户主导** | Clearbit / Breeze Intelligence      | 走已有 HubSpot 通道 |
| **本地商户 + 直邮**  | Data Axle Business                  | Marketplace 直连    |
| **预算优先**         | PDL + Apollo + Cognism              | API 厂商组合        |

> **任何场景都必须配 LexisNexis 抑制(G6 兜底),Snowflake 路径不影响这一项。**

---

## 5. 实施顺序建议

| 阶段         | 行动                                                                  |
| ------------ | --------------------------------------------------------------------- |
| **Sprint 0** | 评估 Snowflake 生产环境就绪度;搭建 `WAREHOUSE_BACKEND=snowflake` 测试 |
| **Sprint 1** | 订阅 PDL 免费 Company Dataset,验证 SQL JOIN 流程跑通                  |
| **Phase 1**  | 按 Pillar 1 决策接入 TransUnion + Claritas + GWI + LiveRamp           |
| **Phase 2**  | 按客户行业补 Experian ConsumerView / ZoomInfo / Cognism / Data Axle   |
| **任何阶段** | LexisNexis 抑制不可省                                                 |

---

## 6. 合规复核(签约前每家必做)

> 完整 7 道闸门见 [`EXPERIAN-ALTERNATIVES.md` §0](./EXPERIAN-ALTERNATIVES.md)。

| 步骤 | 内容                                                             |
| ---- | ---------------------------------------------------------------- |
| 1    | 索取该 vendor 的 DPA / SOC 2 报告 / GDPR/CCPA 合规证明           |
| 2    | HIPAA 客户:确认 BAA 可签(只有少数 vendor 可)                     |
| 3    | 用途限定写入合同(仅营销 / 不用于信贷/雇佣)                       |
| 4    | 确认 DSAR 删除可级联(数据主体行权时,可通知 provider 删除其数据)  |
| 5    | 凭据 / share token Fernet 加密存 `credentials`,禁止明文落日志    |
| 6    | 写 `enrichment.<vendor>.completed` 审计事件(record 数、调用费用) |
| 7    | 存档 `data_source_attestation`(6 年留存)                         |

---

## 7. 关联文档

- Experian 替代方案对比:[`EXPERIAN-ALTERNATIVES.md`](./EXPERIAN-ALTERNATIVES.md)
- Pillar 1 数据地基决策:[`PILLAR1-DATA-FOUNDATION-DECISION.md`](./PILLAR1-DATA-FOUNDATION-DECISION.md)
- 四源合成栈架构:[`PILLAR1-FOUR-SOURCE-STACK.md`](./PILLAR1-FOUR-SOURCE-STACK.md)
- TransUnion 集成:[`TRANSUNION-INTEGRATION.md`](./TRANSUNION-INTEGRATION.md)
- Claritas PRIZM 集成:[`CLARITAS-PRIZM-INTEGRATION.md`](./CLARITAS-PRIZM-INTEGRATION.md)
- GWI 集成:[`GWI-INTEGRATION.md`](./GWI-INTEGRATION.md)
- HubSpot 集成:[`HUBSPOT-INTEGRATION.md`](./HUBSPOT-INTEGRATION.md)
- 端到端数据流:[`END-TO-END-DATA-FLOW.md`](./END-TO-END-DATA-FLOW.md)

---

## 来源(已核实链接)

- [Snowflake Marketplace 主入口](https://app.snowflake.com/marketplace)
- [Snowflake Marketplace 介绍](https://www.snowflake.com/en/product/features/marketplace/)
- [People Data Labs × Snowflake](https://www.peopledatalabs.com/integrations/snowflake)
- [PDL Snowflake 博客文章](https://blog.peopledatalabs.com/post/pdl-on-the-snowflake-data-marketplace)
- [Experian ConsumerView listing](https://app.snowflake.com/marketplace/listing/GZSTZNOU5/experian-marketing-services-consumerview)
- [Experian Health listing](https://app.snowflake.com/marketplace/listing/GZSTZNOVE)
- [Experian × Snowflake 2026 集成](https://www.experianplc.com/newsroom/press-releases/2026/experian-announces-integration-with-snowflake-s-ai-data-cloud)
- [ZoomInfo Data-as-a-Service listing](https://app.snowflake.com/marketplace/listing/GZSNZ1DPLO/zoominfo-zoominfo-data-as-a-service)
- [Data Axle Business listing](https://app.snowflake.com/marketplace/listing/GZSTZ49OTF5)
- [Bombora × Snowflake 案例](https://bombora.com/case-studies/snowflake/)
- [Snowflake Data Clean Rooms 2026](https://www.snowflake.com/en/blog/snowflake-data-clean-rooms-privacy-first-era/)
- [HubSpot Breeze Intelligence](https://www.hubspot.com/products/breeze-intelligence)
- [Cognism 主站](https://www.cognism.com/)
- [Apollo.io 主站](https://www.apollo.io/)
- [AnalyticsIQ Consumer Marketing Data on Snowflake](https://apps-api.c1.us-west-2.aws.app.snowflake.com/marketplace/listing/GZT0ZSR7MY0)
