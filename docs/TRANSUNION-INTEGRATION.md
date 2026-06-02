# TransUnion 接入文档

> **文档类型**:知识文档 / 接入参考
> _Last updated: **2026-05-21**_
> **目标读者**:工程师 / 接入工程师 / 产品 / 运营对接人 / 客户 IT / 合规
> **目的**:理解 TransUnion 是什么、能做什么、怎么接入、本项目里怎么用
>
> **现状**:🟡 **Adapter 尚未实现** — TransUnion 在 ReceptivIQ 路线图位于 **P2 备选**(`docs/ARCHITECTURE-AUDIT-2026Q2.md` §11 Workstream B 之后),触发条件:**有客户明确要求 + 合同签订**。本文档为**接入前的预备研究**。

---

## 目录

- [Part 1:TransUnion 平台](#part-1transunion-平台)
  - [1.1 是什么](#11-是什么)
  - [1.2 作用 / 用途](#12-作用--用途)
  - [1.3 关键网址](#13-关键网址)
  - [1.4 核心概念(必懂)](#14-核心概念必懂)
  - [1.5 能拿到哪些数据](#15-能拿到哪些数据)
  - [1.6 怎么集成(开发视角)](#16-怎么集成开发视角)
  - [1.7 怎么操作(用户视角)](#17-怎么操作用户视角)
  - [1.8 API 配额与限制](#18-api-配额与限制)
  - [1.9 常见踩坑](#19-常见踩坑)
- [Part 2:在 ReceptivIQ 项目中的实现(规划)](#part-2在-receptiviq-项目中的实现规划)
  - [2.1 Adapter 现状 = 未实现](#21-adapter-现状--未实现)
  - [2.2 商业前置:合同与凭证申请](#22-商业前置合同与凭证申请)
  - [2.3 客户接入流程(设计草案)](#23-客户接入流程设计草案)
  - [2.4 数据落仓 · 字段映射(设计)](#24-数据落仓--字段映射设计)
  - [2.5 合规与数据分级](#25-合规与数据分级)
  - [2.6 错误处理 & 监控](#26-错误处理--监控)
  - [2.7 验收测试清单](#27-验收测试清单)
  - [2.8 与 Experian 的关系](#28-与-experian-的关系)
- [附录:速查表与进阶资料](#附录速查表与进阶资料)

---

# Part 1:TransUnion 平台

## 1.1 是什么

**TransUnion(NYSE: TRU)** = 美国"三大征信局"之一,营销板块 2021 年收购 **Neustar**(身份解析头部公司,作价 $31 亿)后,把 Neustar 资产并入 **TruAudience** 营销解决方案。

### 一句话定义

> TransUnion TruAudience = "一个隐私优先的**身份图(Identity Graph)+ 受众定向 + 数据增强 + 跨渠道激活 + 归因测量**的营销基础设施,凭借 TransUnion 征信级数据 + Neustar 跨设备身份能力,在 **98% 美国成年人 / 1.27 亿家庭 / 8000 万联网家庭** 范围内做身份解析与受众建模"。

### 与同类厂商对比

| 维度            | **TransUnion TruAudience**                                      | Experian Marketing Services                   | LiveRamp                                 |
| --------------- | --------------------------------------------------------------- | --------------------------------------------- | ---------------------------------------- |
| 核心定位        | Identity Graph + Audience + Attribution 三件套                  | Identity + Attributes + Hygiene + Suppression | Identity Resolution + Activation Network |
| 数据基底        | TransUnion 信贷数据 + Neustar 行为 + ID 图谱                    | Experian 信贷 + ConsumerView 营销数据         | 自建身份图 + 客户合作伙伴                |
| 主要产品        | Identity Resolution · Appends · ID Translation · Graph Extracts | Combined API(`ue-ov`)· ConsumerView · Mosaic  | RampID 解析 · ATS · Distribution         |
| 覆盖范围        | 98% US adults · 1.27 亿户                                       | 全球 30+ 国 · 美国家庭级                      | 全球 200+ 国 · 跨设备                    |
| 客户类型        | 大型 Agency / 广告主 / 媒体公司 / 数据平台                      | 同上(平台型客户多)                            | 全行业                                   |
| 接入门槛        | **合同 + 凭证申请(60-120 天)** · 与 Experian 同级               | 合同(60-90 天)                                | 合同(60-90 天)                           |
| AWS Marketplace | ✅ 提供 ID Resolution & Enrichment Listing                      | ❌                                            | 部分                                     |
| Databricks 集成 | ✅ Data Intelligence Platform partner                           | ❌                                            | ✅                                       |

---

## 1.2 作用 / 用途

ReceptivIQ 平台消费 TransUnion 数据的潜在场景:

| 场景                             | 用途                                                                                            |
| -------------------------------- | ----------------------------------------------------------------------------------------------- |
| **Persona Agent · 人群画像增强** | TransUnion 个人 attribute appends(收入段、家庭组成、生活方式)— 与 Experian 形成**双数据源比对** |
| **Identity Resolution 跨源去重** | 客户上传的 CRM / Web cookie / Mobile MAID,通过 TUID(TransUnion ID)统一到同一个体或家庭          |
| **Audience Building**            | 基于 TransUnion 人口学 + 行为 segment,生成预制受众段(Lookalike / Affinity / In-market)          |
| **ID Translation**               | 平台已有的 cookie / MAID / hashed-email,翻译为 TUID(或反向),与下游 DSP / SSP 互通               |
| **Attribution & Measurement**    | 跨设备归因(Neustar 老牌强项)· brand lift study · 媒介组合优化                                   |
| **Activation 跨渠道激活**        | 把 Persona Agent 生成的受众 → TruAudience Activation → 投放到 100+ DSP / SSP / CTV / TV 平台    |

### 主要使用方向 = 与 Experian 形成"双源互补"

| 数据维度          | Experian 强                    | TransUnion 强                               |
| ----------------- | ------------------------------ | ------------------------------------------- |
| 信贷与风险        | 商用 + 个人                    | 商用 + 个人 + 反欺诈(TruValidate)           |
| 家庭画像          | ConsumerView · Mosaic 71 group | 较弱                                        |
| **跨设备身份**    | OmniView 中                    | **Neustar 强项** ✅                         |
| **TV / CTV 归因** | 一般                           | **Neustar 强项** ✅(Neustar 是电视归因鼻祖) |
| 全球覆盖          | **强(30+ 国)** ✅              | 美国强,国际较弱                             |

> **结论**:对 ReceptivIQ 的 Agency 客户而言,**TransUnion 不是替代 Experian,而是补充** — 特别是 **CTV / 电视归因 + 跨设备身份** 场景。

---

## 1.3 关键网址(均已实测可打开)

### 1.3.1 商业入口

| 类别                             | 网址                                                       |
| -------------------------------- | ---------------------------------------------------------- |
| **TruAudience 产品总览**         | https://www.transunion.com/solution/truaudience            |
| TruAudience Identity             | https://www.transunion.com/solution/truaudience/identity   |
| TruAudience Audiences            | https://www.transunion.com/solution/truaudience/audiences  |
| TruAudience Activation           | https://www.transunion.com/solution/truaudience/activation |
| TruAudience 登录入口(已签约客户) | https://truaudience.tru-signal.com/                        |
| 主站(集团)                       | https://www.transunion.com/                                |

### 1.3.2 开发者 / 技术资源

| 类别                                         | 网址                                                                                                  |
| -------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| **Client Technical Services 主门户**         | https://techservices.transunion.com/                                                                  |
| 文档库 Doc Repository                        | https://techservices.transunion.com/doc-repository                                                    |
| 连接性 / 认证指南                            | https://techservices.transunion.com/system-coding/connectivity-access                                 |
| **TUXML 代码样例**(legacy XML 协议)          | https://techservices.transunion.com/ctsportal/techservices/public/docrepository/tuxmlCodeSamples.page |
| AWS Marketplace · ID Resolution & Enrichment | https://aws.amazon.com/marketplace/pp/prodview-lywfhmotosrp4                                          |
| Status / 健康                                | 走 CSM 通知,无公开 status 页                                                                          |

### 1.3.3 行业新闻(理解产品演进)

| 来源                           | 链接                                                                                                                                                                        |
| ------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **TruAudience 发布公告(2021)** | https://newsroom.transunion.com/transunion-introduces-truaudience-marketing-solutions--to-power-privacy-centric-identity-and-data-capabilities-for-omnichannel-advertising/ |
| 增强 Identity Graph 公告(2024) | https://www.globenewswire.com/news-release/2024/01/04/2803967/0/en/TransUnion-Announces-Enhanced-Identity-Graph-for-Marketing-Solutions.html                                |
| MarTech 分析                   | https://martech.org/transunion-expands-truaudience-marketing-solutions/                                                                                                     |

### 1.3.4 三方接入说明(便于客户 IT 参考)

| 三方                         | 链接                                                             |
| ---------------------------- | ---------------------------------------------------------------- |
| API Tracker 索引             | https://apitracker.io/a/transunion                               |
| SourceForge TruAudience 评测 | https://sourceforge.net/software/product/TransUnion-TruAudience/ |

---

## 1.4 核心概念(必懂)

### 1.4.1 产品架构

```
TransUnion TruAudience(营销板块)
├─ Identity Graph(基础)— 跨设备 / 跨标识符 / 跨渠道
│   ├─ TUID(TransUnion ID · 单一个体)
│   └─ HHID(Household ID · 家庭群组)
├─ Identity Resolution    — 去重 + 跨源关联
├─ Identity Appends       — 补齐缺失的标识符(email/phone/postal)
├─ Attribute Appends      — 补齐人口学 + 行为属性
├─ ID Translation         — TUID ↔ cookie / MAID / RampID / etc.
├─ Graph Extracts         — 客户自建 first-party 身份图
├─ Audiences              — 预制 segment(Lookalike / Affinity / In-market)
├─ Activation             — 推送到 100+ DSP / SSP / TV / CTV
└─ Attribution            — 跨设备 + 跨渠道归因(Neustar 老牌)
```

### 1.4.2 与 Experian 的标识符差异

| 维度                | Experian                        | TransUnion                               |
| ------------------- | ------------------------------- | ---------------------------------------- |
| 个体 ID             | `experian_pid`                  | `TUID`                                   |
| 家庭 ID             | `experian_hhid`                 | `HHID`                                   |
| ID Translation 目标 | LiveRamp RampID · Cookie · MAID | RampID · Cookie · MAID · OEM ID · CTV ID |
| 翻译方式            | Combined API 的 OV 段           | TruAudience ID Translation API           |

> ⚠️ **TUID 与 experian_pid 不能跨平台互换** — 若客户同时接两家,需要在我们仓库内**通过 hashed_email + postal address 做二次 link**(实质就是 LiveRamp 模式)。

### 1.4.3 接入协议代际

TransUnion 历史上有**多代接入协议**,接入时一定要确认:

| 代际        | 协议                                                     | 典型用法                                   | 备注                                                         |
| ----------- | -------------------------------------------------------- | ------------------------------------------ | ------------------------------------------------------------ |
| Legacy      | **TUXML**(自定义 XML over HTTPS)                         | 老牌信贷 API · TUDF 表单                   | 仍在用;`techservices.transunion.com/tuxmlCodeSamples` 有样例 |
| Modern      | **REST + JSON over mTLS**                                | TruAudience 营销 API · Identity Resolution | **ReceptivIQ 应优先选这个**                                  |
| 数据交付    | **Databricks Delta Share / AWS Data Exchange / S3 drop** | 批量受众导出 / 大规模 attribute appends    | 大客户走这条                                                 |
| Marketplace | **AWS Marketplace SaaS**                                 | ID Resolution & Enrichment as a service    | 信用卡支付,但仍需先签 MSA                                    |

### 1.4.4 认证方式 = mTLS(双向 TLS)

不是简单的 Bearer Token — TransUnion **要求 mTLS**:

- 客户(我们)申请 **客户端数字证书**(TransUnion-minted client certificate)
- 每次 HTTPS 请求**同时验证服务端证书 + 客户端证书**(双向)
- IP 白名单 + 限定来源域
- Token / API Key 是次级凭据,叠加在 mTLS 之上

**这是 TransUnion 比 HubSpot / StackAdapt 严格得多的地方**,源于他们处理的是金融级 PII。

---

## 1.5 能拿到哪些数据

### 1.5.1 身份解析(Identity Resolution)

输入任意已知标识符(email / phone / postal / cookie / MAID),输出:

- TUID(个体)+ HHID(家庭)
- 可信度评分(0-100,基于多源验证)
- 关联标识符全集(同一个人 / 同一家庭其他已知 ID)

### 1.5.2 Attribute Appends(属性增强)

按已知 TUID 拉取的常用属性:

| 类别   | 字段示例                                                                         |
| ------ | -------------------------------------------------------------------------------- |
| 人口学 | age_bucket · gender · estimated_income · education · occupation · marital_status |
| 家庭   | household_size · children_present · home_owner · estimated_home_value            |
| 行为   | online_shopping_frequency · streaming_subscriber · vehicle_type · pet_owner      |
| 财务   | credit_card_holder · investment_segment · digital_banking_usage                  |
| 媒体   | tv_viewing_pattern · device_usage · social_engagement                            |
| 兴趣   | 几百个 affinity segment(汽车 / 旅游 / 健身 / 时尚 / …)                           |

### 1.5.3 预制 Audiences

- **Demographic**(年龄段 / 性别 / 收入段)
- **Behavioral**(In-market for X · Lookalike of Y)
- **Lifestyle**(健身房会员 / 户外爱好者 / …)
- **Custom**(基于客户提供种子受众建模)

### 1.5.4 ID Translation

| 输入              | 输出                             |
| ----------------- | -------------------------------- |
| hashed_email      | TUID / RampID / Cookie / MAID    |
| 任一 cookie       | TUID + 其他 cookie / MAID        |
| MAID(IDFA / GAID) | TUID · cross-device              |
| TUID              | 任意目标 ID(reverse translation) |

### 1.5.5 Activation(写出能力)

- 把 Persona Agent 生成的种子受众 → TruAudience 平台
- 一键推送到 **100+ 投放渠道**:Meta · Google · TikTok · Trade Desk · DV360 · LiveRamp · CTV(Roku · Hulu · Samsung Ads) · Programmatic TV
- Suppression(不投放给某群体)

### 1.5.6 Attribution / Measurement

- Cross-device · Cross-channel 归因(Neustar 老牌)
- Brand Lift Study(品牌提升研究)
- MMM(Marketing Mix Modeling)
- TV / CTV 归因(Neustar 强项)

---

## 1.6 怎么集成(开发视角)

### 1.6.1 前置条件(全部门槛较高)

1. **签订 MSA + DPA**(60-90 天谈判)
2. **付费**(年费起步通常 $100K+ USD,按数据卷收)
3. 申请 **mTLS 客户端证书** + IP 白名单 + API Key
4. 通过 **TransUnion Client Technical Services(CTS)** 团队的接入审批
5. 完成 **UAT 环境**联调测试,再开通生产环境

### 1.6.2 mTLS 调用样板

```bash
curl -X POST https://api.truaudience.transunion.com/v1/identity/resolve \
  --cert /etc/ssl/truaudience/client.pem \
  --key /etc/ssl/truaudience/client.key \
  --cacert /etc/ssl/truaudience/ca-bundle.pem \
  -H "Authorization: Bearer ${TU_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "identifiers": [
      {"type": "hashed_email", "value": "..."},
      {"type": "hashed_phone", "value": "..."}
    ],
    "options": {"include_household": true}
  }'
```

返回示例(简化):

```json
{
  "request_id": "abc-123",
  "results": [
    {
      "tuid": "TU-99887766",
      "hhid": "HH-12345",
      "confidence": 87,
      "linked_ids": [
        { "type": "rampid", "value": "RAMP_..." },
        { "type": "cookie", "value": "..." }
      ]
    }
  ]
}
```

### 1.6.3 大批量数据交付(优于 API 实时调用)

大客户(每月 >100M 行)走**数据交付**而不是 API 实时:

| 模式                       | 说明                                                                                                                    |
| -------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| **Databricks Delta Share** | 客户在自己 Databricks workspace 直接订阅 TransUnion shared catalog,无需手动拷贝                                         |
| **AWS Data Exchange**      | 通过 ADX 订阅 TruAudience 数据集,落进客户自己的 S3                                                                      |
| **SFTP / S3 drop**         | 批量按客户提供的清单做 enrichment,产物以加密 CSV / Parquet drop                                                         |
| **AWS Marketplace SaaS**   | https://aws.amazon.com/marketplace/pp/prodview-lywfhmotosrp4 上的 ID Resolution & Enrichment listing,信用卡支付即可 PoC |

### 1.6.4 推荐 SDK

**TransUnion 不提供官方多语言 SDK**(数据厂商通病)— 客户自己用 `httpx` / `requests` 包装 mTLS 调用。
ReceptivIQ 实现时需要自己写 `transunion_client.py`(参照 `experian_client.py` 模式)。

---

## 1.7 怎么操作(用户视角)

### 1.7.1 客户(终端 Agency / 品牌)如何拿到 API 凭证

这是**最关键且最慢的一步** — TransUnion 不像 SaaS 工具可以自助注册:

```
[Step 1] 客户联系 TransUnion 销售
            ↓
[Step 2] 销售评估业务用例 · 数据量 · 用途 · 合规审查
            ↓ (1-2 周)
[Step 3] 报价 + MSA(主服务协议)+ DPA(数据处理协议)谈判
            ↓ (4-8 周)
[Step 4] 客户签合同 + 预付款
            ↓
[Step 5] TransUnion CTS 团队介入 · 开通 UAT 账户
            ↓
[Step 6] 客户(或 ReceptivIQ 代为)生成 CSR · TU 签发 mTLS 客户端证书
            ↓ (1-2 周)
[Step 7] UAT 联调 · 数据样本验证
            ↓
[Step 8] 生产环境凭证下发
            ↓
[Step 9] 客户把凭证(cert + key + API key)交给 Agency / ReceptivIQ
```

**全流程典型 60-120 天**。

### 1.7.2 客户可访问的后台

签约后:登录 https://truaudience.tru-signal.com/ — 这是 TruAudience SaaS 的运营面板(查询配额 / 看活动状态 / 下载报表),**不是 API key 生成入口**(API 凭证只通过 CTS 工单下发)。

### 1.7.3 撤销凭证

- 客户在 ReceptivIQ 平台 **Integrations → TransUnion → Disconnect** → 平台停同步、加密凭证标记为 revoked
- **或**客户联系 TransUnion CTS 撤销证书 / API key
- 完全终止合作:走合同 termination 流程(typically 30-90 天 notice period)

---

## 1.8 API 配额与限制

### 1.8.1 标准配额(按合同分级)

| 计划                               | 月度请求数(典型)                                       |
| ---------------------------------- | ------------------------------------------------------ |
| **Starter(年费 $100K-$200K)**      | 1-5M 个体识别 / 月                                     |
| **Professional(年费 $200K-$500K)** | 5-20M / 月 + ID Translation + Attribute Appends        |
| **Enterprise(年费 $500K+)**        | 自定义,通常含 Activation + Attribution + Graph Extract |

> 数值是行业惯例参考,实际以合同为准。**TransUnion 不公开列价**。

### 1.8.2 速率限制

- 单租户默认 **100-200 req/sec**(API key 级)· 可申请上调
- Batch endpoint 单批 1000-10000 行
- mTLS 握手开销限制并发连接数 → 推荐 **连接池 + keep-alive**

### 1.8.3 数据延迟

- **Identity Graph 刷新**:每月或每季度(取决于合同)
- **Attribute Appends**:实时返回,但底层属性 1-2 月新鲜度
- **Activation 推送到下游 DSP**:24-48 小时

### 1.8.4 历史回溯

- TruAudience Identity Graph 提供**当前快照**;不含历史时间序列
- Attribution / Measurement 产品有自己的回溯能力(通常 12-24 个月)

---

## 1.9 常见踩坑

| 踩坑                                       | 解决                                                                           |
| ------------------------------------------ | ------------------------------------------------------------------------------ |
| **mTLS 证书过期没发现**                    | 证书有效期通常 1 年;**到期前 60 天告警**;走 CTS 续签需 1-2 周                  |
| 客户证书 / 私钥**明文落代码**              | 必须走 Secret Manager(AWS Secrets Manager / Hashicorp Vault);**严禁 git 提交** |
| 把 `Authorization` 误写成 `Bearer ${cert}` | mTLS 证书是 transport 层,API Key 是应用层,两者**并存而非二选一**               |
| IP 白名单未更新 → 403                      | 平台换 IP / 加 region 时,**提前 5 天**通知 TU CTS 加白                         |
| Identity Resolution **批量请求超 timeout** | 改 batch endpoint;或拆小批;或用 Databricks Delta Share 模式                    |
| **TUID 与 experian_pid 误当同源**          | 不能混用!必须 hashed_email + postal 二次 link                                  |
| Attribute 字段名未提前对齐                 | 不同合同字段可用性不同;签约前**走样本数据 review**                             |
| **未过 SOC 2 + HIPAA 客户拿不到 BAA**      | 如果客户业务含 PHI(医疗),需要单独走 BAA 路径,延期 1-2 月                       |
| **客户在 EU/UK**                           | GDPR 限制 → TransUnion 在 EU 数据资产较弱,建议优先 Experian / LiveRamp         |

---

# Part 2:在 ReceptivIQ 项目中的实现(规划)

## 2.1 Adapter 现状 = 未实现

| 项           | 状态                                                                     |
| ------------ | ------------------------------------------------------------------------ |
| Adapter 文件 | ❌ `backend/app/services/etl/adapters/transunion.py` **不存在**          |
| Mock 模式    | ❌                                                                       |
| 数据表       | ❌ 仓库内无 `raw_transunion_*` schema                                    |
| 在路线图位置 | `docs/ARCHITECTURE-AUDIT-2026Q2.md` §11 · **P2 备选(workstream B 之后)** |
| 触发条件     | 客户明确要求 **且** 合同就位 **且** Experian 已稳定运行                  |

## 2.2 商业前置:合同与凭证申请

**ReceptivIQ 平台层面的工作必须在客户合同前到位**:

1. **决定接入主体**:由客户与 TransUnion 直签(推荐)· 还是 ReceptivIQ 集中签约由各 Agency 客户分账(企业版)
2. **设计合同条款**:每月数据卷上限 · 数据保留 · sub-processor 列入(ReceptivIQ 必须列出来)
3. **配套 BAA**(若客户是医疗/保险 Agency)
4. **预算锁定**:典型起步 $100K-$200K/年

**ReceptivIQ 工程层面的工作**(合同签订后启动):

1. 申请 mTLS 客户端证书 · 配置 Secret Manager 存放
2. 配 IP 白名单(平台出口 IP)
3. 在 UAT 环境跑通 ≤ 1 万行 identity resolution 样本
4. 数据格式对齐(`raw_transunion_identity` 表 schema 设计)
5. 上 production

## 2.3 客户接入流程(设计草案)

不同于 HubSpot / StackAdapt 的"客户输入 API key → 一分钟跑通",TransUnion 走**重资产签约模式**:

```
客户 / Agency Admin                  ReceptivIQ
       │                                  │
       │  1. 联系 TU 销售签约(60-120 天)│
       │  ────────────────────────────►   │ (并行) 申请 mTLS 客户端证书
       │                                  │ 配 Secret Manager · IP 白名单
       │                                  │
       │  2. 客户在 UAT 收到凭证          │
       │                                  │
       │  3. UI: Integrations → TransUnion → Connect (Enterprise)
       │     录入:cert (PEM) + key (PEM) + API key + endpoint host
       │     (合同许可的 product:identity / appends / activation 等)
       ├────────────────────────────────►│
       │                                  │
       │                                  │  4. 单次 mTLS 探活
       │                                  │     POST /v1/health → 200
       │                                  │     · 失败:凭证不入库,UI 报错
       │                                  │     · 成功:Fernet 加密入 credentials 表
       │                                  │
       │                                  │  5. Celery 任务异步触发首次同步
       │                                  │     · 默认走 PII Access Service 出口
       │                                  │     · 写入 raw_transunion_identity
       │                                  │       (per-Agency 物理库 · L2 PII 加密)
       │                                  │
       │  6. WebSocket 推送                │
       │  ◄──── "sync_complete" ──────────│
       │                                  │
       │  7. Agency 在 Persona Agent 中可启用 "TransUnion enrichment"
       │     从此 Persona/Audience 输出会带 TUID/HHID + 属性增强
```

## 2.4 数据落仓 · 字段映射(设计)

设计 4 张 raw 表(全部进 **per-Agency 物理库 · Raw PII Lake**):

### 2.4.1 `raw_transunion_identity`(Identity Resolution 结果)

| 列                        | 类型          | 备注                                                |
| ------------------------- | ------------- | --------------------------------------------------- |
| `record_id`               | `UUID v7`     | 平台主键                                            |
| `input_identifier_hash`   | `TEXT(64)`    | 输入 ID 的 SHA-256(防止存明文)                      |
| `input_identifier_type`   | `TEXT`        | `hashed_email` · `hashed_phone` · `cookie` · `maid` |
| `tuid`                    | `TEXT`        | TransUnion 个体 ID(L2 PII)                          |
| `hhid`                    | `TEXT`        | TransUnion 家庭 ID(L2 PII)                          |
| `confidence`              | `INT`         | 0-100                                               |
| `linked_ids_json`         | `JSONB`       | 关联标识符全集(L2 PII)                              |
| `resolved_at`             | `TIMESTAMPTZ` | API 返回时间                                        |
| `agency_id` / `client_id` | `UUID`        | 多租户 + 客户级 RLS                                 |

### 2.4.2 `raw_transunion_attributes`(Attribute Appends)

| 列                        | 类型          | 备注                                 |
| ------------------------- | ------------- | ------------------------------------ |
| `tuid`                    | `TEXT`        | FK 到 `raw_transunion_identity.tuid` |
| `attribute_code`          | `TEXT`        | 字段编码(如 `age_bucket`)            |
| `attribute_value`         | `TEXT`        | 值                                   |
| `confidence`              | `INT`         |                                      |
| `appended_at`             | `TIMESTAMPTZ` |                                      |
| `agency_id` / `client_id` | `UUID`        |                                      |

### 2.4.3 `raw_transunion_audiences`(Audience 命中)

| 列              | 类型   |
| --------------- | ------ |
| `tuid`          | `TEXT` |
| `audience_id`   | `TEXT` |
| `audience_name` | `TEXT` |
| `confidence`    | `INT`  |
| `as_of_date`    | `DATE` |

### 2.4.4 `raw_transunion_id_translation`

| 列                | 类型                                     |
| ----------------- | ---------------------------------------- |
| `tuid`            | `TEXT`                                   |
| `target_id_type`  | `TEXT`(`rampid` · `cookie` · `maid` · …) |
| `target_id_value` | `TEXT`(L2 PII)                           |
| `translated_at`   | `TIMESTAMPTZ`                            |

**下游 dbt 模型**:

- `stg_transunion_*` 系列(STEP 4 Normalize)
- `shared.identity_bridge` 把 Experian / LiveRamp / TUID 三方 ID 合并(关键中间表)
- `mart_persona_signals` 把 TU + Experian 双源属性 union,Persona Agent 拿合并视图

## 2.5 合规与数据分级

| 数据                                              | 平台分级                    | 处理                                                      |
| ------------------------------------------------- | --------------------------- | --------------------------------------------------------- |
| TUID / HHID                                       | **L2 PII**                  | Fernet 加密入 Raw PII Lake · 仅 PII Access Service 可读   |
| 关联标识符(linked_ids)                            | **L2 PII**                  | 同上                                                      |
| Attribute appends(age_bucket / income_segment 等) | **L0 / L1**(取决于具体字段) | 聚合层进 Processed Lake;敏感字段(如准确收入)留 PII Lake   |
| Audience 命中                                     | **L0**                      | Processed Lake                                            |
| mTLS 证书 / 私钥 / API Key                        | **L2 高度敏感**             | **必须 Secret Manager**(不进 credentials 表;只存证书指纹) |

### 2.5.1 GDPR / CCPA / HIPAA 约束

- **TransUnion 是 Data Processor**;客户是 Controller;ReceptivIQ 是 Sub-processor
- **客户 DPA 必须列出 ReceptivIQ** + TransUnion sub-processor chain
- **CCPA**:TransUnion 数据来源含商业数据共享,DSAR delete 触发时需调 TU API 同步删除
- **HIPAA**:若客户业务含 PHI,必须签 BAA;**TransUnion 的 BAA 不是标配,需单独申请**
- **GDPR**:TU 在 EU 数据资产较弱 + 跨境传输 = 优先级 ↓;欧盟客户优先 Experian / LiveRamp

### 2.5.2 DSAR / Right to Delete

终端用户向 Agency 提 DSAR delete → 平台 DSAR 流程:

1. 从 `raw_transunion_*` 系列表删除该 `tuid` / `email_hash` 对应行
2. **同时**调 TransUnion `/v1/dsar/delete` API 通知 TU 端删除(若合同含此服务)
3. audit 留痕(必须)

## 2.6 错误处理 & 监控

| 错误                               | 平台响应                                                               |
| ---------------------------------- | ---------------------------------------------------------------------- |
| **mTLS 握手失败**(证书过期 / 吊销) | 凭证状态 → expired · 告警 Agency Admin + SRE oncall · 阻断所有 TU 请求 |
| 401 Unauthorized                   | API key 失效 · 同上                                                    |
| 403 Forbidden(IP 不在白名单)       | 通知 SRE 与 TU CTS 更新白名单                                          |
| 429 Rate Limited                   | 退避 + 重试;持续 → 申请上调配额                                        |
| `confidence < 阈值` 的解析结果     | 不算错误;但写 audit 标记 "low_confidence"                              |
| 数据接收方 schema 漂移             | 平台 schema 强制校验;漂移立刻报警                                      |

## 2.7 验收测试清单

### 2.7.1 UAT 环境联调

```
[ ] TU CTS 已开通 UAT 凭证
[ ] mTLS 握手在本地 curl 成功
[ ] /v1/identity/resolve 单条解析返回 TUID + confidence
[ ] Batch endpoint 1000 行解析 < 60 秒
[ ] Attribute Appends 抽样验证字段名 / 值与合同 schema 一致
[ ] DSAR delete API 走通(如合同含此能力)
[ ] PII Access Service 出口审计行落地 audit_logs
```

### 2.7.2 生产数据对账

| 校验                       | 方法                                | 误差         |
| -------------------------- | ----------------------------------- | ------------ |
| 月度调用数                 | 平台 `sync_logs` SUM vs TU 后台计量 | ±2%          |
| Identity Resolution 成功率 | 平台计数 vs TU UAT 返回行数         | 0            |
| Confidence 分布            | 抽样 1000 条 · 与 TU 提供基准对比   | 数据分布一致 |

## 2.8 与 Experian 的关系

ReceptivIQ 同时接入两家时的**架构设计**:

```
                  ┌─ Persona Agent → 拉合并属性
                  │
Source: CRM       │
   ↓              ▼
hashed_email ──► PII Access Service(单一受控出口)
                  │
       ┌──────────┼──────────┐
       ▼          ▼          ▼
   Experian   TransUnion   LiveRamp
       │          │          │
       ▼          ▼          ▼
   experian_   TUID/HHID   RampID
   pid/hhid      │           │
       │          │           │
       └──────► identity_bridge ◄───
              (dbt shared model)
              `tuid_to_experian_pid` JOIN
              `tuid_to_rampid` JOIN
                  │
                  ▼
            Processed Lake
            (per-Agency)
                  │
                  ▼
        Persona / Audience / Attribution Agents
```

**关键点**:三方 ID **不能盲信相等**,要在 `identity_bridge` 用 hashed_email + postal 做二次 link,保留每条 link 的 confidence + source。这是合规审计能跟踪的关键。

---

# 附录:速查表与进阶资料

## A.1 接入前商业 + 工程清单

```
商业:
[ ] 1. 客户业务用例评估(身份解析 / 属性增强 / 归因 / 激活)
[ ] 2. 数据量估算(每月解析行数)→ 影响报价
[ ] 3. 决定签约主体(客户直签 vs ReceptivIQ 集中签)
[ ] 4. 行业合规:是否需要 BAA(医疗/保险)
[ ] 5. 地理:美国 only?有 EU 客户走 Experian 替代

工程(合同签订后):
[ ] 6. 申请 mTLS 客户端证书 + 私钥 + CA bundle
[ ] 7. AWS Secrets Manager / HashiCorp Vault 配证书存储
[ ] 8. 配置平台出口 IP 白名单(给 TU CTS)
[ ] 9. UAT 环境联调 + 样本数据 review
[ ] 10. 设计 raw_transunion_* 4 张表 schema
[ ] 11. 实现 transunion_client.py(mTLS-aware httpx wrapper)
[ ] 12. 实现 TransUnionAdapter(继承 BaseAdapter)
[ ] 13. 写 dbt stg_transunion_* + identity_bridge
[ ] 14. 跑 SOC 2 / DSAR 流程验证
```

## A.2 常用 API 端点(基于公开 TUXML + REST 文档推断)

```
# Identity Resolution
POST /v1/identity/resolve
POST /v1/identity/batch-resolve

# Attribute Appends
POST /v1/attributes/append
POST /v1/attributes/batch

# ID Translation
POST /v1/translate

# Graph Extract(企业级)
POST /v1/graph/extract

# DSAR delete
POST /v1/dsar/delete

# Activation
POST /v1/activation/segment/push

# 配额查询
GET  /v1/usage/current-period
```

**字段名以 TU CTS 提供的合同 schema 为准**,以上为常见命名示意。

## A.3 关联文档

- [INTEGRATION-GUIDE-GA4-DV360](./INTEGRATION-GUIDE-GA4-DV360.md) — 同款知识文档模板
- [STACKADAPT-INTEGRATION](./STACKADAPT-INTEGRATION.md) · [HUBSPOT-INTEGRATION](./HUBSPOT-INTEGRATION.md) — 同结构兄弟文档
- [EXPERIAN-DATA-ROLE](./EXPERIAN-DATA-ROLE.md) — Experian 接入(与 TU **互补**,共存设计)
- [EXPERIAN-APIS-TO-CONFIRM](./EXPERIAN-APIS-TO-CONFIRM.md) — Experian 接口范围确认
- [PII-DESIGN-SOLUTION](./PII-DESIGN-SOLUTION.md) — PII Access Service 设计(TU 必走此出口)
- [MULTI-TENANT-DB](./MULTI-TENANT-DB.md) — `raw_transunion_*` 在每 Agency 物理库内
- [ARCHITECTURE-AUDIT-2026Q2](./ARCHITECTURE-AUDIT-2026Q2.md) — TU 在 P2 路线图位置

## A.4 风险提示

- **TransUnion 不公开列价**:报价靠销售给,客户预算 < $100K/年基本拿不到 API 访问
- **接入周期 60-120 天**:从客户合同启动到生产环境跑通的**典型 lead time**;ReceptivIQ 不能按 SMB SaaS 接入节奏规划
- **mTLS 证书过期 = 全线断流** · 必须有自动告警 + 60 天前续签流程
- **TUID ≠ experian_pid**:跨厂商 ID 不能盲信相等
- **欧盟客户优先级 ↓**:TU 在 EU 数据资产较弱,GDPR 跨境合规复杂;**优先 Experian / LiveRamp**
- **PHI / HIPAA 客户**:TU BAA 不是标配,需单独申请,延期 1-2 月
- **AWS Marketplace 路径不能跳过 MSA**:Marketplace 仅简化付款,核心合规审查仍走 TU 销售 + 法务
- **Phase 优先级**:除非有非常明确的客户需求(CTV/TV 归因 · 双源比对),否则**先把 Experian 跑稳定再考虑 TU**

## A.5 决策建议

| 场景                                        | 是否引入 TransUnion                 |
| ------------------------------------------- | ----------------------------------- |
| Agency 客户主要做 Meta / Google 数字广告    | ❌ 不需要,Experian + LiveRamp 够用  |
| 客户做 **CTV / OTT / Programmatic TV 投放** | ✅ TU(Neustar)优势明显,**值得**接入 |
| 客户做**跨设备归因**作为差异化              | ✅ 同上                             |
| 客户希望**双数据源比对**(避免单源偏差)      | ✅ 与 Experian 互补                 |
| 客户在 EU/UK                                | ❌ TU 在欧洲覆盖弱                  |
| 客户预算 < $100K/年                         | ❌ 接不进来 · 走 Experian 即可      |
| 客户业务含 PHI 且需 HIPAA BAA               | 🟡 可以,但要单独 BAA · 周期 +1-2 月 |
