# 竞品调研 · ReceptivIQ Platform

> _Last updated: **2026-05-26**_
>
> **定位锚点**:ReceptivIQ 是 **"AI 原生 · 多租户 · 合规优先"的 Agency 操作系统(Agency OS)** — 把 Persona / Creative / Attribution / Media 四个 AI Agent + 9-14 个营销数据源 ELT + 每 Agency 独立 Postgres 物理库 + GDPR/CCPA/HIPAA/SOC 2 合规栈打成一个白标平台,卖给营销 Agency,让小型 Agency 也能给客户提供顶级数据 / AI / 合规能力。
>
> 因此**竞品横跨 5-6 个相邻品类**,没有任何单一对手做了我们正在做的全部事。下面按"价值主张重叠度"分层列出,**每条都给出官网 · 重叠点 · 差异点**,方便逐项深挖。

---

## 1. 速读表 · 重叠度最高的 8 家(优先调研)

| #   | 竞品              | 类别                     | 与我们重叠点                         | 与我们差异(我们的优势)                                          |
| --- | ----------------- | ------------------------ | ------------------------------------ | --------------------------------------------------------------- |
| 1   | **Madgicx**       | AI 营销自动化平台        | AI Creative + Audience + 媒介采买    | 仅 Meta/Google 系;无多租户 Agency OS;无 HIPAA                   |
| 2   | **Improvado**     | Agency 数据中台          | 多源 ELT + 报表 + 白标               | 偏数据 pipeline 工具;无 AI Agent;无客户门户白标深度             |
| 3   | **Funnel.io**     | 营销数据平台             | 多源 connector + 数据建模            | 报表仪表盘工具;无 AI 创意 / Persona / 归因 Agent                |
| 4   | **NinjaCat**      | Agency 报表 + dashboards | Agency 多客户 + 白标客户门户         | 报表为主,无 AI Agent · 无 Persona / 归因引擎                    |
| 5   | **AdCreative.ai** | AI 广告创意              | Creative Agent · 跨平台素材          | 仅创意生成;无数据中台 / 归因 / Agency 多租户                    |
| 6   | **Persado**       | 企业级 AI 营销语言       | Creative Agent · 文案优化            | 仅文案,不做数据/归因/Agent 编排;企业级价位                      |
| 7   | **Albert.ai**     | 自主投放 AI              | Media Agent · 自动化采买             | 仅媒介采买,无 Persona/Creative/Attribution 闭环                 |
| 8   | **GoHighLevel**   | Agency SaaS 全家桶       | 多租户 Agency 模型 + 白标 + 客户门户 | CRM / 营销自动化为主;无 AI Agent · 无数据中台 · 无 HIPAA 级合规 |

> **关键洞察**:**没有竞品同时具备**"AI Agent 闭环 + 数据中台 + Agency 多租户 + 合规栈"四个支柱。GoHighLevel 是 Agency 多租户标杆但缺 AI 与数据;Improvado/Funnel.io 是数据标杆但缺 AI Agent;Persado/Madgicx 是 AI 标杆但缺 Agency OS。**我们正好踩在交叉中心**。

---

## 2. 按品类细分清单

### 2.1 🎯 Agency OS / 多租户 Agency 平台(直接竞品 · 优先调研)

> 与我们"Agency 多租户 + 客户门户白标 + 报表分发"重叠度最高。

| 竞品                | 网站                | 核心                                                           | 客户群              | 重叠 ✅ / 差异 ⚠️                                                                                                |
| ------------------- | ------------------- | -------------------------------------------------------------- | ------------------- | ---------------------------------------------------------------------------------------------------------------- |
| **GoHighLevel**     | gohighlevel.com     | Agency SaaS 全家桶(CRM + 邮件 + Funnels + Voicemail + Booking) | SMB 营销代理        | ✅ 多租户 Agency · 客户门户白标 · API/Webhook 完整<br>⚠️ 偏 CRM 与销售自动化;无 AI Agent;无营销数据中台;无 HIPAA |
| **AgencyAnalytics** | agencyanalytics.com | Agency 报表 + dashboard(80+ 集成)                              | 数字代理 / SEO 代理 | ✅ 多客户管理 · 白标报表 · 50+ 营销连接器<br>⚠️ 仅 BI / 报表层;无写回 / 投放 / AI / 合规栈                       |
| **NinjaCat**        | ninjacat.io         | Agency BI + 自动化报表                                         | 数字代理            | ✅ 多客户白标 · 多源数据汇总<br>⚠️ 报表为主;无 AI · 无归因模型 · 无创意生成                                      |
| **DashThis**        | dashthis.com        | 报表自动化                                                     | 中小代理            | ✅ 多客户白标报表<br>⚠️ 几乎只是报表工具                                                                         |
| **Whatagraph**      | whatagraph.com      | Agency 多渠道报表                                              | 数字代理            | ✅ 客户门户 · 自动化报表<br>⚠️ 同上,无 AI 层                                                                     |
| **Swydo**           | swydo.com           | Agency 报表 + 项目管理                                         | 中型代理            | ✅ 客户门户白标<br>⚠️ 项目管理 + 简单报表,无 AI                                                                  |
| **Reportz**         | reportz.io          | 客户报表 dashboard                                             | 小代理              | ✅ 白标 dashboard<br>⚠️ 报表自动化为主                                                                           |
| **SocialPilot**     | socialpilot.co      | 社交媒体 + Agency 多账户                                       | SMB 代理            | ✅ 多客户管理<br>⚠️ 仅社交渠道                                                                                   |
| **Reporting Ninja** | reportingninja.com  | Agency 报表 + 客户门户                                         | 数字代理            | ✅ 白标客户门户<br>⚠️ 报表导出工具                                                                               |

**调研重点**:GoHighLevel(估值 $1B+,SMB 代理事实标杆) · NinjaCat(Agency BI 头部) · AgencyAnalytics(80+ 连接器,数据广度参照)。

---

### 2.2 📊 营销数据中台 / 数据 Pipeline / Reverse ETL

> 与我们 "9-14 个 adapter + ETL + dbt + 仓库" 重叠。

| 竞品             | 网站             | 核心                                       | 重叠 ✅ / 差异 ⚠️                                                                                  |
| ---------------- | ---------------- | ------------------------------------------ | -------------------------------------------------------------------------------------------------- |
| **Improvado**    | improvado.io     | 企业营销数据 pipeline + 报表               | ✅ 多源 connector(500+)· 仓库写入 · 白标 dashboard<br>⚠️ 偏 ETL 工具;无 AI Agent;无创意 / 归因引擎 |
| **Funnel.io**    | funnel.io        | 营销数据收集 + 转换 + 输出                 | ✅ 500+ connector · 数据规范化<br>⚠️ 工具型,客户自建报表;无 AI                                     |
| **Adverity**     | adverity.com     | 企业营销数据集成                           | ✅ 600+ connector · 数据治理 · API 输出<br>⚠️ 偏数据 ops,无 AI 应用层                              |
| **SuperMetrics** | supermetrics.com | 营销数据连接器(Sheets / BigQuery / Looker) | ✅ 100+ connector<br>⚠️ 工具型,无应用层                                                            |
| **Windsor.ai**   | windsor.ai       | 营销数据连接器 + 归因 SDK                  | ✅ 多源 connector · 归因模型<br>⚠️ 小型,无 AI Agent                                                |
| **Fivetran**     | fivetran.com     | 通用 ELT                                   | ✅ Connector 完整<br>⚠️ 通用工具,不针对营销                                                        |
| **Airbyte**      | airbyte.com      | 开源 ELT                                   | ✅ 多源 connector<br>⚠️ 通用 ELT,需自建营销层                                                      |
| **Hightouch**    | hightouch.com    | Reverse ETL(仓库 → SaaS)                   | ✅ 受众激活到广告平台<br>⚠️ 仅 reverse ETL,不解决数据进来 + AI                                     |
| **Census**       | getcensus.com    | Reverse ETL + Audience Hub                 | ✅ 受众激活<br>⚠️ 同上                                                                             |

**调研重点**:Improvado(估值 $1.5B,**最像我们的数据层 + 报表层**) · Funnel.io(数据规范化) · Hightouch(受众激活模式参照)。

---

### 2.3 🤖 AI 创意 / 文案生成

> 与我们 **Creative Agent** 重叠。

| 竞品              | 网站           | 核心                                | 重叠 ✅ / 差异 ⚠️                                                         |
| ----------------- | -------------- | ----------------------------------- | ------------------------------------------------------------------------- |
| **Jasper AI**     | jasper.ai      | 企业 AI 写作 + Brand Voice          | ✅ Brand Voice · 多平台创意输出<br>⚠️ 仅文案,无图像 · 无投放闭环 · 无归因 |
| **Copy.ai**       | copy.ai        | 营销文案 AI                         | ✅ 文案模板库<br>⚠️ 仅文案                                                |
| **Anyword**       | anyword.com    | AI 预测性文案 + A/B                 | ✅ Brand voice · 投放前预测<br>⚠️ 仅文案;不做 Persona/归因                |
| **Persado**       | persado.com    | 企业级 AI 营销语言(Motivation AI)   | ✅ 高级文案优化(消息基因)<br>⚠️ 仅文案,企业级,无数据中台;价位 $50K+/年    |
| **Omneky**        | omneky.com     | AI 广告创意 + 跨平台投放优化        | ✅ Creative + 投放联动<br>⚠️ 仅创意 + 简单优化,无 Persona / Agency 多租户 |
| **Pencil**        | trypencil.com  | AI 广告创意(收购自 Brave Bison)     | ✅ 跨平台素材生成<br>⚠️ 仅创意                                            |
| **AdCreative.ai** | adcreative.ai  | AI 广告 banner / 视频生成           | ✅ 跨平台素材 + Brand 风格学习<br>⚠️ 仅创意,无数据 / 归因                 |
| **Smartly.io**    | smartly.io     | 程序化创意(DCO)+ 投放               | ✅ 创意自动化 + 跨平台投放<br>⚠️ 偏大客户;无 Agency 多租户深度            |
| **Movable Ink**   | movableink.com | 实时个性化创意(邮件 / web / mobile) | ✅ 创意 + 个性化<br>⚠️ 触达层为主                                         |

**调研重点**:Jasper(品牌 AI 标杆) · Persado(企业级营销 AI 鼻祖) · AdCreative.ai(SMB 创意自动化最像我们 Creative Agent)。

---

### 2.4 📈 归因 / 营销分析(MMM + MTA)

> 与我们 **Attribution Agent** 重叠。

| 竞品               | 网站              | 核心                          | 重叠 ✅ / 差异 ⚠️                                                                           |
| ------------------ | ----------------- | ----------------------------- | ------------------------------------------------------------------------------------------- |
| **Northbeam**      | northbeam.io      | DTC 全渠道归因(MTA + MMM)     | ✅ 多触点归因 · 增量测试 · 多源数据<br>⚠️ 仅归因 · 不做 Persona / 创意 · 不做 Agency 多租户 |
| **Triple Whale**   | triplewhale.com   | Shopify-first 归因            | ✅ 归因 + Pixel · 创意分析<br>⚠️ 偏 DTC + Shopify · 不做 Agency 多租户                      |
| **Rockerbox**      | rockerbox.com     | MTA + MMM                     | ✅ 跨渠道归因<br>⚠️ 仅归因                                                                  |
| **Measured**       | measured.com      | 增量 MMM                      | ✅ 增量测试<br>⚠️ 企业级 · 价位高 · 仅归因                                                  |
| **AppsFlyer**      | appsflyer.com     | 移动归因                      | ✅ Mobile 归因<br>⚠️ 仅 mobile                                                              |
| **Adjust**         | adjust.com        | 移动归因                      | ✅ Mobile 归因<br>⚠️ 仅 mobile                                                              |
| **LeadsRx**        | leadsrx.com       | 多触点归因(被 SmarterHQ 收购) | ✅ MTA + 自服务<br>⚠️ 仅归因                                                                |
| **Wicked Reports** | wickedreports.com | DTC 归因                      | ✅ 多源归因<br>⚠️ 偏 DTC · 仅归因                                                           |

**调研重点**:Northbeam(归因新一代标杆) · Triple Whale(Shopify 生态 · 估值 $500M) · Rockerbox(MTA + MMM 双修)。

---

### 2.5 👥 CDP / 受众建立 / Persona 引擎

> 与我们 **Persona Agent + Audience Export** 重叠。

| 竞品                 | 网站             | 核心                       | 重叠 ✅ / 差异 ⚠️                                                     |
| -------------------- | ---------------- | -------------------------- | --------------------------------------------------------------------- |
| **Segment (Twilio)** | segment.com      | 企业 CDP · 事件收集 + 受众 | ✅ Audience 计算 + 激活<br>⚠️ 工具型;无 AI Persona 生成;无创意 / 归因 |
| **mParticle**        | mparticle.com    | 企业 CDP                   | ✅ 事件 + 受众 + 治理<br>⚠️ 同上                                      |
| **Tealium**          | tealium.com      | 企业 CDP + Tag Management  | ✅ CDP 全栈<br>⚠️ 工具型                                              |
| **Lytics**           | lytics.com       | AI-First CDP               | ✅ AI Persona + 受众<br>⚠️ 偏数据治理 · 无创意 / 归因                 |
| **Treasure Data**    | treasuredata.com | 企业 CDP                   | ✅ 受众建立<br>⚠️ 同上                                                |
| **BlueConic**        | blueconic.com    | CDP + 受众激活             | ✅ Audience + 激活<br>⚠️ 同上                                         |
| **Amperity**         | amperity.com     | CDP + Identity Resolution  | ✅ Identity + 受众<br>⚠️ 企业级零售为主                               |
| **ActionIQ**         | actioniq.com     | 企业 CDP                   | ✅ 同上<br>⚠️ 企业级                                                  |
| **Heap**             | heap.io          | 自动事件埋点 + 分析        | ✅ 事件数据<br>⚠️ 偏 product analytics                                |

**调研重点**:Segment(CDP 事实标准) · Lytics(AI-first CDP,最像我们 Persona Agent) · BlueConic(中型 CDP)。

---

### 2.6 🛡️ 隐私优先 / 数据洁净室 / 合规优势平台

> 与我们 **HIPAA + GDPR + CCPA + per-Agency 物理库 + PII Access Service** 的合规栈重叠。

| 竞品                            | 网站                       | 核心                        | 重叠 ✅ / 差异 ⚠️                                                    |
| ------------------------------- | -------------------------- | --------------------------- | -------------------------------------------------------------------- |
| **LiveRamp**                    | liveramp.com               | 身份解析 + 数据协作         | ✅ Identity 解析 · 数据合作<br>⚠️ 我们已集成它,不是替代;面向更大客户 |
| **InfoSum**                     | infosum.com                | 数据洁净室                  | ✅ 隐私优先数据合作<br>⚠️ 仅数据洁净室,不做营销应用层                |
| **Habu (LiveRamp Clean Rooms)** | habu.com                   | 数据洁净室                  | ✅ 跨方数据合作 + PII 保护<br>⚠️ 仅 clean room                       |
| **AWS Clean Rooms**             | aws.amazon.com/clean-rooms | AWS clean room              | ✅ 隐私安全合作<br>⚠️ 同上                                           |
| **Snowflake Data Clean Room**   | snowflake.com              | Snowflake-native clean room | ✅ 同上<br>⚠️ 同上                                                   |
| **Optable**                     | optable.co                 | 隐私优先 CDP + 数据合作     | ✅ Identity + 合规<br>⚠️ 偏数据合作                                  |

**调研重点**:LiveRamp / Habu(数据合作 · 隐私基础设施事实标杆) · InfoSum / Optable(隐私 CDP 新代)。

---

### 2.7 🏥 医疗 / HIPAA-专用营销(BAA 差异化路径)

> 我们的 **HIPAA Lane + BAA + Bedrock 路由** 切入这里。

| 竞品             | 网站             | 核心                      | 重叠 ✅ / 差异 ⚠️                                               |
| ---------------- | ---------------- | ------------------------- | --------------------------------------------------------------- |
| **DeepIntent**   | deepintent.com   | 医疗 HCP / 患者程序化广告 | ✅ HIPAA-compliant · 医疗营销<br>⚠️ 仅程序化投放,不做 Agency OS |
| **PulsePoint**   | pulsepoint.com   | 健康营销平台              | ✅ HIPAA · 处方数据应用<br>⚠️ 大型平台,不做 Agency 多租户       |
| **Crossix**      | crossix.com      | 医疗营销分析 + 归因       | ✅ HIPAA · 归因<br>⚠️ 仅医疗归因                                |
| **Swoop**        | swoop.com        | 医疗精准营销              | ✅ HIPAA · 患者画像<br>⚠️ 大型 health publisher 平台            |
| **PatientPoint** | patientpoint.com | 院内医疗营销              | ✅ HIPAA<br>⚠️ 院内场景,不重叠                                  |
| **Phreesia**     | phreesia.com     | 患者参与 + 营销           | ✅ HIPAA<br>⚠️ 患者前台为主                                     |

**调研重点**:DeepIntent(规模化 HIPAA 营销标杆) · Crossix(医疗归因) — 主要参考"HIPAA 营销平台是怎么过审的"。

---

### 2.8 🤖 AI-原生 / Autonomous Marketing(与我们四 Agent 闭环最相似)

| 竞品                             | 网站           | 核心                                                  | 重叠 ✅ / 差异 ⚠️                                                                                                                                                                                                |
| -------------------------------- | -------------- | ----------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Resonate (Cortex / Ignition)** | resonate.com   | AI 消费者智能 + agentic 营销(2.5 亿消费者 · 15K 属性) | ✅✅ **最接近**:Cortex 用自然语言出受众→一键投放;Ignition 给**独立 Agency** 全链路(洞察→受众→激活→measurement)<br>⚠️ 自带 15K 属性数据(我们靠三方);但**无多租户物理隔离 · 无 HIPAA BAA Lane · 无白标 Agency OS** |
| **Albert.ai**                    | albert.ai      | 全自动数字营销(投放 + 优化)                           | ✅ Media Agent · 自动投放<br>⚠️ 仅投放,不做 Persona/Creative/归因闭环;不做 Agency 多租户                                                                                                                         |
| **Madgicx**                      | madgicx.com    | AI Meta/Google 广告 + 创意 + 受众                     | ✅ Creative + Audience + Media · 三件套<br>⚠️ 仅 Meta/Google 生态;不做 Agency 多租户                                                                                                                             |
| **Mutiny**                       | mutinyhq.com   | B2B 网站 AI 个性化                                    | ✅ AI 个性化<br>⚠️ 仅 B2B 网站                                                                                                                                                                                   |
| **Cresta**                       | cresta.com     | 销售 / 客服 AI Agent                                  | ✅ AI Agent 架构参考<br>⚠️ 客服销售,不重叠                                                                                                                                                                       |
| **HubSpot AI / Breeze**          | hubspot.com    | HubSpot 内置 AI                                       | ✅ AI 营销助手<br>⚠️ 仅 HubSpot 用户;无多租户 Agency · 无数据中台                                                                                                                                                |
| **Salesforce Einstein**          | salesforce.com | Salesforce 内 AI                                      | ✅ AI 营销层<br>⚠️ 仅 Salesforce 客户                                                                                                                                                                            |
| **Adobe Mosaic / Sensei**        | adobe.com      | Adobe 内 AI                                           | ✅ 创意 + 受众 AI<br>⚠️ 仅 Adobe 生态                                                                                                                                                                            |

**调研重点**:**Resonate(Cortex/Ignition)— 当前最像我们的对手**(agentic AI + 自有消费者数据 + 明确面向独立 Agency,2026 连发 3 款新品),优先深挖;Albert.ai · Madgicx — 离 AI Agent 闭环也近,但都是单点。我们的护城河是 **4 Agent + 数据中台 + 每 Agency 物理库隔离 + HIPAA BAA Lane + 白标 Agency OS** 的完整闭环,这些 Resonate 都不具备。

> 💡 Resonate 同时也是潜在的**第三方画像数据供应商**(见 [`EXPERIAN-ALTERNATIVES.md`](./EXPERIAN-ALTERNATIVES.md) §3.5)——"既是供应商又是竞品",采买其数据前需评估战略风险。

---

## 3. 我们的差异化定位(竞品分析后的反推)

> 把上述竞品全部投影到一张图,我们站在的交叉点:

```
                  AI Agent 闭环
                       ▲
        Albert/Madgicx │   Persado/Jasper
            ▍          │           ▍
            ▍   ★ ReceptivIQ      ▍
            ▍                      ▍
─────────────────────────────────────►  Agency 多租户 / 白标
            ▍                      ▍
            ▍                      ▍
        Improvado/      │      GoHighLevel/
        Funnel.io       │      NinjaCat
                       ▼
                  数据中台 + 合规栈
```

我们的**护城河**(独有组合):

1. **AI Agent 完整闭环 4 件套**(Persona → Creative → Attribution → Media)— **没有任何竞品做 4 件**
2. **每 Agency 独立 Postgres 物理库**(PSD 标准)— Improvado/Funnel.io 走 schema 隔离;GoHighLevel 走逻辑隔离;**只有我们做了物理隔离**
3. **PII Access Service + 6 operation 白名单**(GDPR 受控出口)— 行业首创级别
4. **HIPAA Lane + Bedrock 路由**(医疗 BAA 客户专用)— 通用营销平台几乎都不做(避开)
5. **可配置 RBAC + 自定义角色 + 等级守卫 + 不可篡改审计**(SOC 2 / GDPR Art. 30 一站式)
6. **小型 Agency 也能给客户用 Experian / TransUnion / Nielsen**(共享参考湖 + license-gated RLS)— **目前没有平台做到**

---

## 4. 调研建议优先级 · 怎么往下做

### 4.1 Phase 1 · 直接对手深挖(本月)

调研 **5 家**,每家 1 周做完:

| Rank   | 竞品              | 调研重点                                                               |
| ------ | ----------------- | ---------------------------------------------------------------------- |
| **#1** | **GoHighLevel**   | Agency 多租户的事实标杆;看他们的客户门户白标深度 · 价格分层 · API 生态 |
| **#2** | **Improvado**     | 数据 pipeline + 报表的"高端版";我们的数据中台层标杆                    |
| **#3** | **NinjaCat**      | Agency BI + 客户门户白标的中型代理标杆;价格分层 · 报表广度             |
| **#4** | **Madgicx**       | AI Creative + Audience + Media 三件套最像我们 AI Agent 闭环;价格分层   |
| **#5** | **AdCreative.ai** | AI 创意生成在 SMB Agency 的渗透;PMF 数据点                             |

### 4.2 Phase 2 · 横向品类参考(下月)

| Rank    | 竞品                 | 调研重点                                  |
| ------- | -------------------- | ----------------------------------------- |
| **#6**  | **Northbeam**        | DTC 全渠道归因怎么定价 · 销售给谁         |
| **#7**  | **Persado / Jasper** | 企业级 AI 营销文案的"价格上限"参考        |
| **#8**  | **Hightouch**        | Reverse ETL + Audience Hub 的定位         |
| **#9**  | **DeepIntent**       | HIPAA 营销平台怎么过审 · 客户案例         |
| **#10** | **Albert.ai**        | 自主投放 AI 的客户反馈 · "黑盒"信任度问题 |

### 4.3 调研维度(对每家)

| 维度                     | 具体问                                                 |
| ------------------------ | ------------------------------------------------------ |
| **价格**                 | 起步 / 进阶 / 企业三档;按 seat / agency / volume 哪种  |
| **客户群**               | SMB Agency / 中型 / 企业 / DTC / B2B / 医疗 — 各占多少 |
| **集成生态**             | Connector 数量 / 类别 · 是否做 Reverse ETL             |
| **AI 能力**              | 单点 AI(创意 only)vs 多 Agent 闭环 vs 无               |
| **多租户**               | 逻辑隔离 / schema / 物理库 / 独立项目;白标深度         |
| **合规**                 | GDPR / CCPA / HIPAA / SOC 2 哪些过了                   |
| **价格阶梯**             | 起步价 · 进阶价 · 企业价 · 是否按 client/seat 收费     |
| **客户案例 / 公开评价**  | G2 / Capterra / Reddit / Twitter 评分;客户访谈摘录     |
| **API / 开发者生态**     | 是否有公开 API · webhook · 文档质量                    |
| **融资 / 估值 / ARR**    | 估值与 ARR 倍数 · 增长率 · 上一轮领投                  |
| **创始人 / 团队背景**    | 领导层来自哪;过往出口                                  |
| **离开他们用我们的理由** | 我们能给的他们没有的;具体话术                          |

### 4.4 推荐工具

- **G2 / Capterra / TrustRadius** — 客户评论 + 评分
- **SimilarWeb / Semrush** — 流量 · 关键词
- **BuiltWith** — 客户技术栈反查(他们的客户用了什么)
- **Crunchbase / PitchBook** — 融资 / 估值
- **LinkedIn Sales Navigator** — 团队规模 / 客户 logo
- **官网定价页 + 文档站** — 直接看产品边界

### 4.5 输出物建议

每家产出 **1 页 SWOT** + **1 页价格 / 客户群 / 集成 / 合规 表**(共 2 页 PDF / 飞书文档),累计 5-10 家后产出 **1 份对标分析报告**(15-25 页),用来:

- 销售话术差异点提炼
- 价格分层制定
- 产品路线图优先级反向校准
- 投资人 pitch deck 第 3 页"Why Now / Why We Win"

---

## 6. 免费调研工具箱(零成本路径)

无需付费即可完成 §4 的 12 个调研维度。按调研侧重排列,⭐ 标记"必看"。

### 6.1 客户评价 & 评分 ⭐

| 工具                | 状态     | 用法                                                      |
| ------------------- | -------- | --------------------------------------------------------- |
| **G2.com** ⭐       | 免费阅读 | 5000+ SaaS 真实评价 · 类目对比矩阵 · "Switched From" 字段 |
| **Capterra**        | 完全免费 | Gartner 旗下,SMB 评价为主                                 |
| **TrustRadius**     | 完全免费 | 中型企业评价,内容质量高                                   |
| **GetApp**          | 完全免费 | Gartner 系,产品对比工具                                   |
| **Software Advice** | 完全免费 | Gartner 系                                                |
| **Trustpilot**      | 完全免费 | 偏负面投诉,看真实痛点                                     |
| **Reddit** ⭐       | 完全免费 | `r/SaaS / r/marketing / r/agency / r/PPC` 搜 `[A] vs [B]` |
| **Hacker News**     | 完全免费 | `news.ycombinator.com/news?` + 工具名;Show HN 反馈犀利    |

### 6.2 网站流量 & SEO

| 工具                       | 免费档                               |
| -------------------------- | ------------------------------------ |
| **SimilarWeb**             | 月访问量 · 国家分布 · 流量来源(部分) |
| **Ubersuggest**            | 每日 3 次免费查询(关键词 · 反链)     |
| **Semrush**                | 限制免费查询                         |
| **Ahrefs Webmaster Tools** | 自己站完全免费                       |
| **Google Trends** ⭐       | 完全免费 · 品牌词搜索趋势对比        |
| **SimilarTech**            | 部分免费                             |

### 6.3 技术栈反查 ⭐

| 工具                 | 用法                                                                |
| -------------------- | ------------------------------------------------------------------- |
| **BuiltWith.com** ⭐ | 输入竞品域名,看 Stripe / Segment / Datadog / React 框架等(~3 次/天) |
| **Wappalyzer** ⭐    | 浏览器插件,免费 · 实时看任何网站的技术栈                            |
| **StackShare** ⭐    | 完全免费 · 公司主动披露的技术栈                                     |
| **whatcms.org**      | 免费查 CMS                                                          |

### 6.4 融资 / 公司情报

| 工具                      | 免费档                                       |
| ------------------------- | -------------------------------------------- |
| **Crunchbase**            | 基础公司主页免费                             |
| **SEC EDGAR** ⭐          | 完全免费 · 上市公司 10-K / S-1 招股书        |
| **Owler**                 | 部分免费(对手追踪 · 新闻 · 营收估计)         |
| **AngelList / Wellfound** | 早期公司融资 + 团队 + 招聘                   |
| **LinkedIn** ⭐           | 免费看团队人数变化、招聘节奏(融资和扩张信号) |

### 6.5 招聘信号 = 路线图泄露 ⭐

| 工具                          | 看什么                                                            |
| ----------------------------- | ----------------------------------------------------------------- |
| **LinkedIn Jobs** ⭐          | 按公司搜职位 → 招什么 = 在投资什么方向(招 Compliance Eng = HIPAA) |
| **Greenhouse / Lever Boards** | `boards.greenhouse.io/[company]` 直接访问                         |
| **Indeed**                    | 多渠道职位汇总                                                    |
| **Glassdoor**                 | 薪资 + 员工评价(culture 信号)                                     |
| **Levels.fyi**                | 工程师薪资 → 估算团队规模和成本结构                               |

### 6.6 直接从竞品官网 ⭐(最高 ROI)

| 资源                           | 用法                                                       |
| ------------------------------ | ---------------------------------------------------------- |
| **官网 /pricing**              | 价格分层 · 按 seat/agency/volume 哪种                      |
| **官网 /customers**            | 客户 Logo · 行业分布 · 案例研究                            |
| **官网 /docs**                 | API 完整度 · webhook · 集成数 · 开发者生态成熟度           |
| **官网 /blog**                 | 产品方向 · 思想领导 · 教育内容质量                         |
| **官网 /security · /trust**    | SOC 2 / HIPAA / ISO 等合规清单                             |
| **status.[company].com** ⭐    | 故障历史 · 可用性 SLA · 后端栈线索                         |
| **Internet Archive Wayback**   | `web.archive.org/web/*/[company.com]` → 历史定价、定位演变 |
| **官网 newsletter / Substack** | 匿名订阅看营销/产品节奏                                    |

### 6.7 社交监听

| 平台            | 搜索关键词模式                                           |
| --------------- | -------------------------------------------------------- |
| **Twitter/X**   | `"[竞品]" filter:replies` · `"switched from [A] to [B]"` |
| **LinkedIn**    | `"we use [X]"` 帖子搜索 · 客户高管动态                   |
| **Reddit**      | Google 搜 `site:reddit.com [A] vs [B]`                   |
| **YouTube**     | 评测视频、客户案例视频 · 评论区是金矿                    |
| **ProductHunt** | launch 时的真实反馈 + 排名                               |

### 6.8 行业报告(免费片段)

| 来源                                     | 找法                                                                 |
| ---------------------------------------- | -------------------------------------------------------------------- |
| **Gartner Magic Quadrant**               | Google `"Magic Quadrant" "[category]" filetype:pdf` · 竞品官网常转发 |
| **Forrester Wave**                       | 同上                                                                 |
| **IDC MarketScape**                      | 同上                                                                 |
| **The Drum / AdExchanger / MarTech.org** | 免费行业新闻 · 趋势分析                                              |
| **CB Insights**                          | 部分免费报告(Top 100 等)                                             |
| **a16z / Bessemer / Sequoia 博客**       | VC 的 SaaS 分析,质量极高,完全免费                                    |

### 6.9 专利 / IP

| 工具                       | 用法                                               |
| -------------------------- | -------------------------------------------------- |
| **USPTO Patent Search** ⭐ | `patft.uspto.gov` · 完全免费 · assignee = 竞品公司 |
| **Google Patents** ⭐      | `patents.google.com` · 同上,UI 更好                |

### 6.10 开发者信号

| 工具                 | 看什么                             |
| -------------------- | ---------------------------------- |
| **GitHub**           | 组织 star 数 · contributor 活跃度  |
| **npm trends**       | `npmtrends.com` 对比 SDK 下载量    |
| **PyPI Stats**       | `pypistats.org` 对比 Python 包下载 |
| **DockerHub**        | 公共镜像 pull 数                   |
| **GitHub Octoverse** | 年度报告,完全免费                  |

### 6.11 销售情报(免费档)

| 工具            | 免费额度                         |
| --------------- | -------------------------------- |
| **Apollo.io**   | 每月 50 credits 免费(查找联系人) |
| **Hunter.io**   | 每月 25 次免费(查找邮箱)         |
| **RocketReach** | 月 5 次免费                      |

---

### 6.12 推荐"零成本"调研工作流(每家 80 分钟)

```
Step 1 (10 min) — 官网三件套
  · /pricing /customers /security 三页 → 价格分层 + 客户群 + 合规清单

Step 2 (15 min) — 技术栈 + 招聘
  · Wappalyzer 看官网技术栈
  · LinkedIn Jobs 看招什么职位 → 推路线图

Step 3 (20 min) — 客户口碑
  · G2 + Capterra 各 10 分钟,Pros / Cons / Switched From
  · Reddit 搜 `[product] vs` 看真实对比

Step 4 (15 min) — 财务 + 团队
  · Crunchbase 看融资轮 + 估值
  · LinkedIn 看团队规模 + 高管背景

Step 5 (10 min) — 流量信号
  · SimilarWeb 看月访问量趋势
  · Google Trends 对比品牌词

Step 6 (10 min) — 输出
  · 一页 SWOT + 一页 价格/客户群/集成/合规 四象限表
```

10 家做完仅需 ~13 工时,合计可产出 15-25 页对标分析报告。

---

## 7. 关联文档

- [PSD Technical Solution](./psd/technical-solution.md) — 平台技术定位
- [ARCHITECTURE-AUDIT-2026Q2](./ARCHITECTURE-AUDIT-2026Q2.md) — 当前实现度 · 下一步路线图
- [MULTI-TENANT-DB](./MULTI-TENANT-DB.md) — 多租户物理库隔离(差异化护城河之一)
- [EXPERIAN-DATA-ROLE](./EXPERIAN-DATA-ROLE.md) — Experian 集成(差异化护城河之一)
