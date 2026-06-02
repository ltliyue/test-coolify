# 端到端数据流 · 第三方数据如何贯穿全平台

> **文档类型**:全栈数据生命周期说明
> _Last updated: **2026-05-21**_
> **目标读者**:产品 / 客户技术负责人 / 业务对接 / 投资人 / 内部工程经理
> **目的**:把 **Experian / TransUnion / GA4 / HubSpot / Meta / DV360 / StackAdapt / LiveRamp / Nielsen / Placer IQ / Quorum / Trade Desk** 等所有第三方数据串成一条**完整的旅程** — 从客户数据进来,到最终投放出去 + 报表回流,**每一步用谁、存哪儿、怎么处理、谁来读**。
>
> **场景设定**:贯穿全文用一个具体例子 — Agency 为"AcmeFitness"(DTC 健身品牌)做一次"30-45 岁高收入女性的 Q3 新品广告"。这样所有抽象数据都有可触摸的具体值。

---

## 0. 一图见全 · 10 阶段端到端流程

```
   ╔═══════════════════════════════════════════════════════════════════════╗
   ║                  ReceptivIQ 端到端数据生命周期                          ║
   ╠═══════════════════════════════════════════════════════════════════════╣

   ① Ingestion                  ② Landing                ③ Classify
   ─────────────                ──────────                ───────────
    CRM(HubSpot)                                          每字段分级
    Web(GA4)                  整条 record                L0 / L1 / L2 / L3
    DSP(Meta/DV360/        →  immutable           →     ↓
    StackAdapt/TTD)            落入 Landing             field_classifier
    Experian/TU                Lake(Bronze)
    Nielsen/Placer/Quorum                                ↓
    Tresorit(批量 CSV)                                  路由分流
                                                          │
                       ┌──────────────────┬──────────────┘
                       ▼                  ▼
                   ④ Raw PII Lake      ④ Processed Lake
                   ────────────         ─────────────────
                   email/姓名加密       email→pii_token
                   仅 PII Access        无 PII · 可跨源
                   Service 可读         分析
                       │                  │
                       │                  ▼
                       │              ⑤ Normalize + Dedup (STEP 4-5)
                       │                  ↓
                       │              ⑥ Enrich(关键阶段)
                       │                  ↓
                       │           ┌──────┴──────┐
                       │           ▼             ▼
                       │       Experian      TransUnion(可选)
                       │       enrichment    identity bridge
                       │       Mosaic        TUID/HHID
                       │       segments
                       │           │             │
                       │           └─────┬───────┘
                       │                 ▼
                       │            Processed.canonical
                       │            (含画像属性)
                       │                 │
                       │                 ▼
                       │           ⑦ Persona Agent
                       │           生成"30-45 岁高收入女性"
                       │           ICP 画像
                       │                 │
                       │                 ▼
                       │           ⑧ Audience Build
                       ▼           ────────────
                  PII Access      hashed_email/cookie/MAID
                  Service         种子受众(可投放清单)
                  (受控明文出口)        │
                       │                 ▼
                       │           ⑨ Suppression Filter
                       │           ────────────
                       │           Experian DNM/DNC/Deceased
                       │           过滤掉禁触达
                       │                 │
                       │                 ▼
                       │           ⑩ Creative Agent
                       │           ────────────
                       │           生成"Reach Your Best Self"
                       │           文案 + 多平台素材
                       │                 │
                       │                 ▼
                       │           ⑪ Media Agent
                       │           ────────────
                       │           分配预算到 Meta/DV360/
                       │           StackAdapt/TTD
                       │           (HITL 人工审批)
                       └─────┬───────────┴─────────┐
                             │                     ▼
                             ▼                ⑫ Activation
                       PII Access            ────────────
                       Service              投放到 100+ DSP
                       audience_hash_list   (LiveRamp 中介)
                              ↑                    │
                              │                    ▼
                              │              ⑬ 数据回流
                              │              ────────────
                              │              impressions / clicks /
                              │              conversions / video_views
                              │                    │
                              │                    ▼
                              │              ⑭ Attribution Agent
                              │              ────────────
                              │              MTA + MMM
                              │              跨 DSP / 跨设备
                              │              (TU/Nielsen 增强)
                              │                    │
                              │                    ▼
                              │              ⑮ Client Portal
                              └──────────►   ────────────
                                             白标 dashboard
                                             PDF 报表
                                             AI 摘要叙述
   ╚═══════════════════════════════════════════════════════════════════════╝
```

### 0.1 一句话读图(自上而下)

从最上方 14 个三方数据源源源不断地"进来",经过 5 道**自动化清洗管道**,再经过 3 个 **AI Agent** 的智能加工,最后**精准投放出去**并把回流数据**还原成报表**呈现给客户 — 整条链路上没有一个字段是"裸奔"的,每一步都有租户隔离、字段分级、加密和审计护栏。

### 0.2 三条主线读法

**主线 A · 数据本身的旅程(蓝线)**
**进来 → 落地 → 分流 → 提纯 → 增强 → 出去 → 回来 → 展示**

> ① 数据进来 → ② 整条 immutable 落 Landing Lake(原始可回溯)→ ③ 按 L0/L1/L2/L3 分级 → ④ PII 字段进 Raw PII Lake(加密)、非 PII 字段进 Processed Lake(可分析)→ ⑤ 标准化 + 跨源去重 → ⑥ Experian/TU **增强画像** → ⑦ Persona Agent 生成 ICP → ⑧ 构建受众清单 → ⑨ Suppression 过滤掉禁触达 → ⑩ Creative Agent 出文案/素材 → ⑪ Media Agent 分配预算(人工审批)→ ⑫ 通过 LiveRamp 投放到 100+ DSP → ⑬ 数据回流 → ⑭ Attribution Agent 算归因 → ⑮ 客户在 Portal 看仪表盘和 PDF。

**主线 B · PII 的旅程(红线 / 高敏感)**
**PII 在整条链路上只在两个 Lake 里待过 — Raw PII Lake(加密)和 PII Access Service 的临时出口**。中间所有 AI/分析/Persona/Creative 算法,看到的都是 `pii_token` 哈希,不接触明文。只有在最终⑫ Activation 时才由 **PII Access Service** 在严格的 purpose-bound JWT(≤15 min)护送下短暂解密为 hashed_email,直接灌进 DSP 的 audience list,**全程零落盘**。

**主线 C · 三方数据的作用面(灰线)**
**不是"接进来摆着",而是各司其职贯穿多个阶段**:

| 三方                   | 在哪些阶段被用                                                                                                   |
| ---------------------- | ---------------------------------------------------------------------------------------------------------------- |
| **Experian**           | ⑥ 增强画像(Mosaic 段)/ ⑨ Suppression 过滤(DNM·DNC·Deceased)/ ⑪ ID Bridge(EID)/ ⑭ 归因(线下转化)/ ⑮ DSAR 反向删除 |
| **TransUnion**         | ⑥ 跨设备 TUID 桥接 / ⑭ 归因增强                                                                                  |
| **HubSpot / GA4**      | ① 第一方种子数据 → 全链路用                                                                                      |
| **DSP(Meta/DV360 等)** | ① 历史绩效输入 / ⑫ 投放出口 / ⑬ 回流来源                                                                         |
| **Nielsen / Placer**   | ⑥ 媒介计划基准 / ⑭ 离线归因校准                                                                                  |
| **LiveRamp**           | ⑫ 投放的"中间路由器"(把我们的 hashed_email 桥到任何 DSP)                                                         |
| **Tresorit**           | ① 加密文件传输通道(不是数据源,客户主动塞 CSV 用)                                                                 |

### 0.3 关键节点的"为什么"(防止误读)

- **为什么 Landing Lake 是 Immutable?** — 合规要求(GDPR Art. 30 处理活动登记)+ 任何下游算法错了都能从 Landing 回灌,**原始数据是平台的"黑匣子"**。
- **为什么要分 Raw PII Lake 和 Processed Lake?** — 让 90% 的分析查询**根本接触不到 PII**,把"可能泄露的攻击面"缩到只有 PII Access Service 一个出口;DSAR 删除时也只需要删 Raw PII Lake 一处即可全链路失效。
- **为什么 Persona/Creative/Attribution 三个 Agent 是分开的?** — 单一巨型 prompt 不可控也不可观测;分成三个 Agent 后,**每个 Agent 都有独立 prompt、独立 token budget、独立 audit**,客户可随时关闭某一个(例如不允许 AI 出文案,只用 AI 做归因)。
- **为什么 Media Agent 必须有 HITL(人工审批)?** — 投放涉及真金白银的预算分配,**LLM 非确定性不能直接动钱**;Media Agent 出"建议方案",AM 一键 approve / 拒绝 / 改 → 才进入 Activation。
- **为什么 Suppression 一定要排在 Persona/Audience 之后、Creative 之前?** — 如果先 suppression 再 persona,被过滤的人就不会进画像,**模型会偏**;必须先建立完整画像和受众,再做最后一道"禁触达"过滤,既保画像准确又保合规。

### 0.4 客户最关心的三个数字

| 问题                      | 答案                                                                                                   |
| ------------------------- | ------------------------------------------------------------------------------------------------------ |
| **从原始数据到投放多久?** | 一次完整流程(Persona → Creative → Media → Activation)**通常 6–24 小时**,其中人工审批占大头(可压缩)。   |
| **PII 被多少环节看到?**   | 明文只在 Raw PII Lake 与 PII Access Service 临时令牌期(≤15 min)内可见,**全链路其余 11 个环节零接触**。 |
| **数据出问题能查到吗?**   | 是。每条记录从 ① 到 ⑮ 都带同一个 `record_id`(UUID v7),配合不可篡改的 `audit_logs`,**全链路可追溯**。   |

### 0.5 跟着一条记录走完全程 · "Sarah Lee" 的 15 步轨迹

> 用**同一条数据**贯穿 15 个阶段,看它在每一步**长什么样、谁动了它、存到哪里**。这是最快理解全平台的方法。

**背景**:AcmeFitness(健身 DTC 品牌)在 Q3 推新款瑜伽垫;HubSpot 里有个 lead 叫 Sarah Lee,Q2 留过资但没下单。她将作为受众样本之一被纳入本次投放。

---

#### ① Ingestion · 进来(10:00:00)

ETL Runner 触发 HubSpot Contacts Adapter 拉取 Sarah 的资料,API 原始返回:

```json
{
  "id": "1234567",
  "properties": {
    "email": "sarah.lee@gmail.com",
    "firstname": "Sarah",
    "lastname": "Lee",
    "phone": "+1-415-555-8821",
    "lifecyclestage": "marketingqualifiedlead",
    "lead_source": "website_form_q2_promo",
    "createdate": "2026-03-15"
  }
}
```

**审计**:`integration.fetch.completed`(adapter=hubspot, agency_id=acme_fitness, rows=1)

---

#### ② Landing Lake · 整条入库(10:00:01)

整条 JSON **不做任何修改**写入 `landing.hubspot_records`,并附上技术字段:

| 字段           | 值                                        |
| -------------- | ----------------------------------------- |
| `record_id`    | `01933e8a-...-7c91`(UUID v7 · 全链路血缘) |
| `agency_id`    | `acme_fitness`                            |
| `client_id`    | `null`(Agency 直跑,不属于子客户)          |
| `ingested_at`  | `2026-05-21T10:00:01Z`                    |
| `content_hash` | `sha256:8f3a...c2e1`(防重复)              |
| `payload`      | 上面那段 JSON 原文                        |

Landing 表有 **BEFORE UPDATE/DELETE 触发器**,任何改动都会被 RAISE EXCEPTION 拒掉 — Sarah 这条记录从此**不可篡改**。

---

#### ③ Classify · 字段分级(10:00:02)

`field_classifier` 扫一遍这条 JSON,逐字段打标签:

| 字段             | 级别              | 处置                           |
| ---------------- | ----------------- | ------------------------------ |
| `email`          | **L2 — PII**      | → Raw PII Lake(Fernet 加密)    |
| `firstname`      | **L2 — PII**      | → Raw PII Lake                 |
| `lastname`       | **L2 — PII**      | → Raw PII Lake                 |
| `phone`          | **L2 — PII**      | → Raw PII Lake                 |
| `lifecyclestage` | L0 — Public       | → Processed Lake               |
| `lead_source`    | L0 — Public       | → Processed Lake               |
| `createdate`     | L1 — Internal     | → Processed Lake               |
| `id`             | L1 — External ref | → Processed Lake(作为 join 键) |

**审计**:`classify.completed`(record_id=01933e8a..., l2_fields=4)

---

#### ④a Raw PII Lake · 4 个 PII 字段加密入库(10:00:03)

`raw_pii.contacts` 写入一行:

```
record_id: 01933e8a-...-7c91
agency_id: acme_fitness
email_enc:    Fernet(sarah.lee@gmail.com, key=acme_dek_v3)
email_hash:   sha256(sarah.lee@gmail.com + acme_salt)
              = a5f1c8...d92b   ← 这就是 pii_token
firstname_enc: Fernet(Sarah)
lastname_enc:  Fernet(Lee)
phone_enc:     Fernet(+1-415-555-8821)
```

**关键**:从此 Raw PII Lake 只能由 **PII Access Service** 配合 purpose-bound JWT(≤15min)读取,任何普通查询连接都看不见这张表的解密视图。

---

#### ④b Processed Lake · 非 PII 字段 + pii_token 入库(10:00:03)

`processed.contacts_canonical` 写入一行:

```
record_id:        01933e8a-...-7c91
agency_id:        acme_fitness
pii_token:        a5f1c8...d92b   ← Raw PII Lake 那行的索引
hubspot_id:       1234567
lifecyclestage:   marketingqualifiedlead
lead_source:      website_form_q2_promo
createdate:       2026-03-15
```

**自此往后的所有分析、画像、AI 处理都只读 Processed Lake**,看到的是 `pii_token = a5f1c8...d92b`,**不再接触 Sarah 的明文邮箱**。

---

#### ⑤ Normalize + Dedup · 跨源合并(10:00:04)

`dedup_worker` 用 `pii_token` 把多源数据关联起来,发现 Sarah 在 GA4 里也有踪迹:

```
GA4 events    ─┐
  user_pseudo_id 1234567890.abcde   (Sarah 在浏览器里的 GA4 ID)
  + hashed_email a5f1c8...d92b      (一次"已登录购物车"事件带回了哈希邮箱)
                 ↓
processed.identity_graph 新增一行
  pii_token:       a5f1c8...d92b
  hubspot_id:      1234567
  ga4_pseudo_id:   1234567890.abcde
  events_30d:      [page_view, add_to_cart, abandoned_checkout]
```

Sarah 的 **HubSpot 身份** 与 **GA4 行为** 通过 `pii_token` 串到一起。

---

#### ⑥ Enrich · Experian 增强画像(10:00:08)

`enrichment_worker` 调 **Experian Combined API**(用 PII Access Service 临时解密的 hashed_email 作为 query key):

请求:`POST https://api.experian.com/combined/v1/append`(载荷为哈希邮箱)
返回:

```json
{
  "match_score": 0.94,
  "mosaic_segment": "C12 · Striving Single Suburbans",
  "household_income_band": "$75K-$100K",
  "age_band": "30-39",
  "gender": "F",
  "interests": ["fitness", "wellness", "outdoor_recreation"],
  "experian_id": "EID-4F8A-..."
}
```

`processed.contacts_canonical` 那行被 **UPDATE**(注意 — 是 processed 表可以 update,不是 landing):

```
mosaic_segment:        C12
household_income_band: $75K-$100K
age_band:              30-39
experian_id:           EID-4F8A-...
```

**审计**:`enrichment.experian.completed`(record_id=01933e8a, match_score=0.94)
**计费**:Experian API 这次调用计 1 次,扣 Agency 月度 token budget。

---

#### ⑦ Persona Agent · 生成 ICP(11:30:00 · 客户营销人员触发)

营销人员在 Portal 点"为 Q3 瑜伽垫活动生成 ICP",Persona Agent 调 GPT-4o,**输入是聚合的 Processed Lake 数据**(包括 Sarah 这一条 + 其他 8,452 条 lead):

输出 Persona JSON:

```json
{
  "persona_id": "p_acme_q3_yoga",
  "persona_name": "Wellness-Driven Suburban Mom",
  "age_band": "30-45",
  "income_band": "$75K-$150K",
  "key_segments": ["Mosaic C12", "Mosaic D15"],
  "interests": ["fitness", "wellness", "mindfulness"],
  "buying_signals": ["abandoned_checkout in last 30d", "browsed yoga category"],
  "estimated_reach": 142000
}
```

存表 `personas.persona_definitions`。Sarah **正好匹配** Mosaic C12 + abandoned_checkout 信号,**自动入围下一步受众**。

---

#### ⑧ Audience Build · 构建受众清单(11:30:05)

`audience_builder` 按 Persona 的 SQL 谓词扫 Processed Lake:

```sql
SELECT pii_token FROM processed.contacts_canonical
WHERE mosaic_segment IN ('C12','D15')
  AND age_band IN ('30-39','40-44')
  AND pii_token IN (
    SELECT pii_token FROM processed.identity_graph
    WHERE 'abandoned_checkout' = ANY(events_30d)
  )
```

返回 14,238 个 pii_token,Sarah 的 `a5f1c8...d92b` 在列。
存表 `audiences.audience_members`(只存 token 列表 · 不存 PII)。

---

#### ⑨ Suppression Filter · 禁触达过滤(11:30:07)

`suppression_worker` 用同一组 pii_token 反查 **Experian Suppression Lake**(DNM/DNC/Deceased 名单):

- Sarah 的 `a5f1c8...d92b` **不在** DNM/Deceased 名单 → ✅ 保留
- 队列里另有 312 个 pii_token 命中 → 剔除

最终受众:14,238 − 312 = **13,926 人**。
**审计**:`suppression.applied`(audience_id=aud_acme_q3, removed=312, source=experian_dnm)

---

#### ⑩ Creative Agent · 生成文案 + 多平台素材(11:32:00)

Creative Agent 读 Persona + 客户品牌指引,**不读受众清单(零 PII)**,GPT-4o + DALL-E 生成:

```
Headline: "Your Q3 reset starts on the mat."
Body:     "30-min flows for the busy weekday. Carbon-neutral materials.
           Free shipping on orders $79+."
Variants:
  - Meta(1080x1080 + 1080x1920 Story · 3 文案变体)
  - DV360(300x250 + 728x90 banner · 2 文案变体)
  - StackAdapt(native 800x600 · 3 文案变体)
  - TikTok(竖屏 9:16 视频脚本)
```

存表 `creatives.creative_assets`。**审计**:`creative.generate.completed`(persona_id=p_acme_q3_yoga, variants=11)

---

#### ⑪ Media Agent · 预算分配(11:40:00 · 输出待 HITL 审批)

Media Agent 读历史 ROAS、库存、价格,**给出建议预算分配**:

| 渠道       | 建议预算 | 预估展现 | 预估转化 |
| ---------- | -------- | -------- | -------- |
| Meta       | $18,000  | 1.2M     | 380      |
| DV360      | $12,000  | 800K     | 220      |
| StackAdapt | $6,000   | 350K     | 95       |
| TikTok     | $4,000   | 600K     | 110      |
| **合计**   | $40,000  | 2.95M    | 805      |

**AM 在 Portal 上一键审批**(也可以改、可以拒)。
**审计**:`media.plan.approved`(plan_id=mp_acme_q3, approver=user_am_42)
**这是全链路唯一的人工节点。**

---

#### ⑫ Activation · 投放到 DSP(11:45:00)

`activation_worker` 现在需要把受众落给各 DSP:

1. 找 PII Access Service 申请一次性临时令牌(scope=`audience_export_meta`,TTL=10min)
2. 凭令牌从 Raw PII Lake **批量** decrypt 13,926 个 pii_token → 还原成 `sha256(email)`(注意:不是明文邮箱,是哈希邮箱 — 这是 DSP 接受的格式)
3. 经 **LiveRamp** 路由,分别推到:
   - Meta Custom Audience API
   - DV360 Customer Match
   - TikTok Audience API
4. **令牌过期 → 内存里的解密结果立刻销毁,零落盘**

Sarah 的 sha256_email 现在在 Meta 的一个 Custom Audience 里,Meta 投手什么也不知道她叫什么。
**审计**:`activation.dsp_push.completed`(dsp=meta, audience_size=13926, token_id=t_xxx)

---

#### ⑬ 数据回流 · DSP 把绩效数据打回来(2026-05-25 起 · 每小时)

Meta Insights API 报:

```
campaign_id: 23859876543
ad_id:       23859876544
impressions: 142
clicks:      8
conversions: 1     ← 其中一个是 Sarah(她从 Instagram 广告点进去下单了)
spend_usd:   3.20
```

但 Meta **不会告诉我们**那一个转化是 Sarah,**只给汇总数字**。落 `landing.meta_ads_records`,同样 immutable。

---

#### ⑭ Attribution Agent · 跨渠道归因(每天凌晨跑)

Attribution Agent 把所有 DSP 的回流 + GA4 的 conversion 事件 + Sarah 的 abandoned_checkout 历史串起来:

- 5/22 12:00 — Sarah 看到 Meta 广告 1 次(impression)
- 5/23 14:00 — Sarah 看到 DV360 banner 1 次(impression)
- 5/24 09:00 — Sarah 在 TikTok 看到视频,点了链接(click)
- 5/24 09:03 — Sarah 在 GA4 触发 purchase 事件 · $89.00

**MTA 模型分配权重**:Meta 28% / DV360 12% / TikTok 60% → $89 收入按权重分摊到三家。
**审计**:`attribution.compute.completed`(model=mta_data_driven, journey_count=805)

---

#### ⑮ Client Portal · 客户看到结果(随时刷新)

AcmeFitness 营销负责人登录 Portal,看到:

- **本次活动 ROAS:4.2x**(花了 $40K · 带来 $168K)
- **805 转化里 · TikTok 贡献最高**
- **AI 摘要**:"TikTok 视频在年轻段表现远超预期,建议下次活动加码 TikTok 至 30%。"
- 一键导出 PDF 报告(含 Persona/受众/Creative/媒介/归因全链)

如果未来 Sarah 行使 GDPR/CCPA 删除权,DSAR 工作流会:① 删 Raw PII Lake 那一行 → ② Processed 表 pii_token 自然失效 → ③ Audience 表里 token 失联 → 但 audit_logs 保留(合规要求),report_history 也保留(已发送给客户的不能改)。

---

> **小结**:一条 HubSpot lead,15 个阶段,**只有 ④a 那一行存了她的明文邮箱**(还是加密的);其余所有阶段都用 `pii_token = a5f1c8...d92b` 流转。整条链路一旦发生事故,凭 `record_id = 01933e8a-...-7c91` 一查到底。

---

### 0.6 通俗版 · Experian 到底在干嘛?(给非技术听众)

> 这一节专门解释最常被问到的问题:**"为什么要花钱接 Experian?它具体做什么?"**

#### 一句话比喻

**你给 Experian 一张只有"邮箱"的纸条,它还给你一份"这个人的素描像"。**

#### 增强前 vs 增强后(看得见的差别)

**增强前 · 你手里只有 HubSpot 的 lead 信息:**

```
email:           sarah.lee@gmail.com
lifecyclestage:  marketingqualifiedlead
lead_source:     website_form_q2_promo
```

这点信息**根本投不准广告** — 你不知道 Sarah 多大、住哪儿、收入多少、喜欢什么。

**Experian 增强后 · 同一个 Sarah 突然立体了:**

```
age_band:         30-39                              ← Experian 告诉你的
gender:           F                                   ← Experian
household_income: $75K-$100K                          ← Experian
mosaic_segment:   C12 · Striving Single Suburbans    ← Experian 的"人群标签"
interests:        [fitness, wellness, outdoor]        ← Experian
zip_code:         94110                               ← Experian
home_owner:       false                               ← Experian
match_score:      0.94                                ← Experian 自评"94% 把握同一人"
```

**就这一步,Sarah 从一个"邮箱"变成了一个"人物画像"。**

#### Experian 凭什么能做到?

Experian 是美国最大的征信局之一,它有 **3 亿+ 美国消费者的档案**(信用卡历史 / 信贷申请 / 公开记录 / 数十家数据合作商喂数据)。你给它一个邮箱或姓名+地址,它在自己内部数据库做身份解析(matching),命中后把这个人的画像属性返回给你。

类比:**它就是营销圈的"天眼查 + 央行征信 + 大数据画像"三合一。**

#### 增强完以后做什么?五件事环环相扣

```
增强后的 Sarah(processed.contacts_canonical 那一行)
        │
        ├──► ⑦ Persona Agent 用她做"原料"
        │      她和另外 8,452 条 lead 一起塞给 GPT-4o
        │      → AI 生成 ICP:"30-45 岁高收入郊区女性,关注健身"
        │
        ├──► ⑧ Audience Build 用她做"筛选目标"
        │      SQL 一筛:"Mosaic C12 + age 30-44 + abandoned_checkout"
        │      → Sarah 入围,生成 14,238 人的受众清单
        │
        ├──► ⑨ Suppression 反过来用 Experian 做"过滤"
        │      Experian 的 DNM/Deceased 名单查一遍
        │      → Sarah 不在禁触达名单,留下
        │
        ├──► ⑩ Creative Agent 用画像写文案
        │      "针对 30-45 岁、关心健身、有时间压力的女性"
        │      → 出 11 条跨平台素材变体(Meta/DV360/TikTok)
        │
        └──► ⑫ Activation 把 Sarah 这一组人精准投放
               哈希邮箱推到 Meta Custom Audience
               → Sarah 在 Instagram 刷到这则广告
               → 点击 → 下单 → ROAS 4.2x
```

#### 一句话总结价值

| 场景                   | 转化率  | 广告预算效率                                        |
| ---------------------- | ------- | --------------------------------------------------- |
| **没有 Experian 增强** | 0.5%–1% | 只能"广撒网"投给所有留过资的 lead                   |
| **有 Experian 增强**   | 3%–5%   | 挑出"最像理想客户的那 10%",**广告预算花得有的放矢** |

而且这套画像不仅用于"找人",还同时用于:

- **AI 写文案** — 知道对方是郊区健身女性 → 文案不写都市精英风
- **预算分配** — 知道这群人 TikTok 重度 → Media Agent 把预算 60% 砸 TikTok
- **归因分析** — 知道这群人通常多设备购物 → Attribution 模型加权跨设备路径
- **合规过滤** — 同一份 Experian 数据还提供 DNM/Deceased 名单,防止给已故/拒接触者发广告
- **跨设备识别** — Experian EID 把同一个人在手机 / iPad / 浏览器上的足迹串成一条

> **核心结论**:Experian **不是"加点信息这么简单"**,它是 Persona、Audience、Creative、Media、Attribution 五个核心环节共同的"底座数据"。**没有它,整条 AI 链路虽然能跑,但精度会大幅下降**,从"精准营销"退化为"广撒网"。

---

### 0.7 用户数据到底从哪儿来?(4 层数据来源)

> 这是最常被问到的"灵魂拷问":**"你们这些用户数据,都从哪儿搞来的?合法吗?"**
> 答案是 — **数据不是一个来源,而是分 4 层按合规流程"喂"进来的。**

#### 4 大渠道(按"谁拥有"分层)

```
┌──────────────────────────────────────────────────────────┐
│  Tier 1 · 客户自己的第一方数据(First-Party)            │
│  ──────────────────────────────────────                  │
│  • HubSpot CRM    ← 客户留资的 lead / contact            │
│  • GA4 / Web SDK  ← 客户官网的访客行为                   │
│  • Tresorit CSV   ← 客户手动上传的历史名单               │
│  • Shopify/订单系统(P2 路线)                          │
│  归属:客户 100% 拥有,合法来源,数据最干净               │
└──────────────────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│  Tier 2 · 广告平台回流数据(Second-Party)               │
│  ──────────────────────────────────────                  │
│  • Meta Ads       ← 投过广告的曝光/点击/转化             │
│  • DV360          ← Google 生态的展示/视频               │
│  • StackAdapt     ← Native/Display                       │
│  • The Trade Desk ← 全渠道程序化                         │
│  • TikTok Ads     ← 短视频广告回流                       │
│  • LeadRX         ← 跨渠道归因事件                       │
│  归属:广告平台向客户报告"你花的钱效果如何"              │
│  关键:只有"汇总数据",平台不会告诉你"哪个具体用户转化"  │
└──────────────────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│  Tier 3 · 第三方数据商买来的(Third-Party · 付费)       │
│  ──────────────────────────────────────                  │
│  • Experian       ← 给一个邮箱,返回画像 + segment        │
│  • TransUnion     ← TUID 身份解析 + 跨设备                │
│  • Nielsen        ← 电视/CTV 收视基准                     │
│  • Placer IQ      ← 实体到店客流                          │
│  • Quorum         ← 行为/政治舆情(特定客户)             │
│  归属:数据商自己沉淀(几十年累积),客户付费"借用"        │
│  关键:从来不是"用户主动给我们",是数据商通过合规渠道汇集 │
└──────────────────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│  Tier 4 · 身份桥接服务(Identity Bridge)                │
│  ──────────────────────────────────────                  │
│  • LiveRamp       ← 把哈希邮箱翻译成各 DSP 能用的 ID      │
│  归属:中介,不沉淀用户画像,只做"翻译"                   │
└──────────────────────────────────────────────────────────┘
```

#### 用 Sarah Lee 举例 · 她的画像各部分从哪儿来?

```
Sarah Lee 在 Processed Lake 里的最终画像
─────────────────────────────────────────
email: sarah.lee@gmail.com         ← Tier 1 · HubSpot(她自己填的留资表)
firstname / lastname               ← Tier 1 · HubSpot
lifecyclestage: MQL                ← Tier 1 · HubSpot
events: [abandoned_checkout, ...]  ← Tier 1 · GA4(她访问官网的行为)
─────────────────────────────────────────
age_band: 30-39                    ← Tier 3 · Experian(数据商画像)
gender: F                          ← Tier 3 · Experian
income: $75K-$100K                 ← Tier 3 · Experian
mosaic_segment: C12                ← Tier 3 · Experian
interests: [fitness, wellness]     ← Tier 3 · Experian
─────────────────────────────────────────
ga4_pseudo_id                      ← Tier 1 · GA4 cookie
TUID(跨设备)                      ← Tier 3 · TransUnion
RampID                             ← Tier 4 · LiveRamp(投放时用)
─────────────────────────────────────────
impressions_meta: 1                ← Tier 2 · Meta Ads(广告平台报)
clicks_tiktok: 1                   ← Tier 2 · TikTok Ads
conversion: $89.00                 ← Tier 2 · 综合 GA4 + DSP
```

**这就是为什么 Sarah 的画像这么立体 — 不是一家给的,是 4 个渠道叠加的结果。**

#### 关键合规问题:用户同意了吗?

| 渠道                  | 用户怎么"同意"的                                                                    | 我们的合规义务                                                                                             |
| --------------------- | ----------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| **Tier 1 · 第一方**   | 用户在客户网站填表 / 用 cookie 时勾选"接受隐私条款"                                 | 客户负责拿到 consent,我们存 `consent_records`                                                              |
| **Tier 2 · 广告回流** | 用户在 Meta/TikTok 注册时已经同意了那些平台的隐私条款                               | 平台负责,我们只拿到脱敏汇总                                                                                |
| **Tier 3 · 三方数据** | 数据商通过自己的网络(信贷历史 / 公开记录 / 合作商)汇集 — 用户的"同意"在那些原始场景 | **我们必须能证明 Experian 持有合法 consent**;Experian 自己 GDPR/CCPA 合规;我们存 `data_source_attestation` |
| **Tier 4 · LiveRamp** | LiveRamp 自己的合规网络保证                                                         | 看 LiveRamp 的 BAA / DPA                                                                                   |

**最敏感的是 Tier 3** — 这就是为什么 Experian 要求每次调用都带 **client_id + use_case 声明**,我们要在合同里保证"只用于营销 / 不用于信贷决策"。

#### 一句话总结

> **用户数据不是"我们去抓的",而是 4 个渠道按合规流程"喂"给我们的:**
> ① 客户自己 CRM 里的留资(第一方) +
> ② 投广告时平台报回来的数据(第二方) +
> ③ 数据商付费买来的画像(第三方) +
> ④ 投放时身份桥接服务做翻译。
>
> **我们平台不直接面向消费者抓数据**,我们是"汇集 + 处理 + 智能化"的中台。

---

### 0.8 Experian 两条路径并存 · DSP 目录 vs 直接 API

> 这是另一个常被混淆的点:**"StackAdapt/TTD 目录里那 6,391 个 Experian segment,跟我们平台直接调 Experian Combined API 是同一件事吗?"**
> 答案是 — **完全不同的两条路径,两条都用,各司其职。**

#### 一句话区分

| 维度       | DSP 目录里的 6,391 个 Experian segment | 平台直接调 Experian Combined API    |
| ---------- | -------------------------------------- | ----------------------------------- |
| 是什么     | DSP 预上架的"现成人群包"               | 我们后端按需调用的"原料 API"        |
| 怎么用     | 投手在 DSP 后台勾选"投这个 segment"    | 后端拿邮箱 → 换 Experian 画像字段   |
| 谁拿到数据 | **DSP 拿到**(我们看不到具体名单)       | **我们平台拿到**(进 Processed Lake) |
| 粒度       | 粗(几百万-几亿人的大池子)              | 细(单条记录的属性)                  |
| 用途       | 面向 Experian 大池子做 prospecting     | 丰富我已有的 lead 画像              |

#### 6,391 个 segment 具体用在三种场景

**场景 A · 冷启动 / Prospecting(从零找新客)**

AcmeFitness 是新品牌,自己 CRM 只有 8,452 个 lead。投手在 StackAdapt 后台勾选:

- ☑️ `Experian > Demographics > Age 30-44 Female`(8,200 万人)
- ☑️ `Experian > Interests > Health & Fitness Enthusiasts`(4,600 万人)
- ☑️ `Experian > Mosaic > C12 Striving Single Suburbans`(1,100 万人)

→ StackAdapt 取三个池子交集(约 600 万人)→ 直接投广告。
**我们根本不需要这群人的邮箱、不进自己的库**。

**场景 B · 受众扩展(Lookalike)**

把 8,452 个第一方 lead 上传给 StackAdapt → DSP 在 Experian 大池子里找"行为/属性匹配度高"的人 → 扩到 50 万 lookalike → 投放。
**目录在这里是"母池子"供 lookalike 算法挑相似人**。

**场景 C · 库存填充**

第一方受众清单 13,926 人,Meta 一晚上只能 deliver 给 3,200 人。剩余预算 Meta 自动从 Experian segment 里补类似画像的人继续投。

#### 目录的四大局限 vs 平台的解法

| DSP 目录局限                | 客户真实需求                                                    | 我们平台的解法                                                                       |
| --------------------------- | --------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| **粒度太粗**(7700 万人池子) | "加州沿海高净值家庭里有 5 岁以下孩子且 90 天搜过亲子度假的人"   | 直接调 Combined API 拿原始属性 → 自己写 SQL 自由组合(在 ⑥ Enrich 阶段)               |
| **维度组合受限**            | A AND B AND NOT C 的布尔逻辑                                    | Experian 属性写进 `processed.contacts_canonical`,用任意 SQL 自由组合                 |
| **数据维度受限**            | Experian 内部 800+ attribute(目录只暴露 80)                     | 直接走 API,拿到 full attribute set(看合同覆盖范围)                                   |
| **没有第一方数据混合**      | "我 CRM 的 abandoned_checkout + Experian Mosaic C12 + GA4 浏览" | 三方数据汇进 Processed Lake 后,和第一方一起做 SQL join — 这正是 §0.7 4-tier 叠加价值 |

#### 两条路径在 AcmeFitness 的真实链路并存

```
┌──────────────────────────────────────────────────┐
│  路径 1 · 走 Experian Combined API(精准)        │
│  ─────────────────────────────────────────       │
│  HubSpot 8,452 lead                              │
│    → 每条 lead 调 Combined API                   │
│    → 拿到 age/income/mosaic/interests           │
│    → 写进 Processed Lake                         │
│    → SQL join GA4 行为                           │
│    → 筛出 14,238 个"高质量种子"                  │
│    → 推到 Meta Custom Audience(哈希邮箱投放)   │
│                                                  │
│  适合:已有 lead 的"高意向再营销"                │
└──────────────────────────────────────────────────┘
                       +
┌──────────────────────────────────────────────────┐
│  路径 2 · 投手在 StackAdapt 勾 Experian segment   │
│  ─────────────────────────────────────────       │
│  StackAdapt 目录                                  │
│    → 勾 Mosaic C12 + 健身爱好者(交集 600 万人) │
│    → 这 600 万人的身份我们不知道                  │
│    → 但广告精准投到这群"类似画像的陌生人"        │
│                                                  │
│  适合:冷启动找新客(prospecting)               │
└──────────────────────────────────────────────────┘
```

**两条路径同时存在、互补**:

- **路径 1**(精准 + 第一方混合)→ 解决"投得准"
- **路径 2**(目录大池子)→ 解决"投得多"

#### 一句话总结

> StackAdapt 目录里的 **6,391 个 Experian segment 是给 DSP 投放层做"广撒网式 prospecting"用的现成包**,它**不进我们平台的数据库**,我们也"看不见"具体名单。
>
> 我们平台真正用 Experian 做**精细画像增强**走的是 **Combined API**(§6 增强阶段)— 那条路径才能突破"粒度粗 / 组合受限 / 维度受限 / 无法混合第一方"四大局限。
>
> **两条路径同时启用 = "找得多 × 投得准"** = 真正的精准营销。

---

### 0.9 归因(Attribution)用哪条数据路径?

> 常被问到:**"归因模型用的是路径 1 还是路径 2?三方数据在归因里到底干嘛?"**
> 答案 — **归因只能用路径 1 + DSP 回流(Tier 2),用不上路径 2 的目录数据。**

#### 为什么归因不能用路径 2(DSP 目录)?

**因为路径 2 的人我们"看不见"**:

- DSP 目录的 600 万 prospect,我们只知道"投出去多少展现/点击",**不知道每个人是谁**
- Meta 报回来的只是聚合数字:`impressions: 1.2M / clicks: 4,800 / conversions: 142`
- **无法把"某次点击"和"某个具体用户"对应起来 → 无法算个人级归因**

归因模型(MTA · Multi-Touch Attribution)的核心需求是 **"同一用户在多渠道的多次接触,要能串成一条 journey"**。路径 2 数据是"匿名汇总",串不起来。

#### 归因 Agent 的真正数据来源(三层叠加)

```
┌────────────────────────────────────────────────────────┐
│  Attribution Agent · 每天凌晨跑                         │
└────────────────────────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼

  ① 第一方行为     ② DSP 回流       ③ 三方校准
  ─────────────    ─────────────    ─────────────
  GA4 events       Meta Insights    TransUnion(跨设备)
  HubSpot events   DV360 reports    Nielsen(电视/CTV)
  Shopify orders   StackAdapt API   Placer IQ(到店)
  (Tier 1)         TikTok API       Experian EID(身份桥)
                   (Tier 2)         (Tier 3)
        │              │              │
        └──────────────┼──────────────┘
                       ▼
                  pii_token 关联
                       ▼
              ┌─────────────────┐
              │ user_journeys   │ ← 归因模型的真正输入
              │ ──────────────  │
              │ pii_token: a5f1c8...d92b
              │ touchpoints:
              │  - 5/22 Meta impression
              │  - 5/23 DV360 impression
              │  - 5/24 TikTok click  ← 促成购买
              │  - 5/24 GA4 purchase  $89
              └─────────────────┘
                       ▼
                MTA 模型分配权重
                Meta 28% / DV360 12% / TikTok 60%
```

#### 用 Sarah 看 5 次接触如何串成一条 journey

| 时间       | 接触点                  | 留下的 ID                      | 来源                     |
| ---------- | ----------------------- | ------------------------------ | ------------------------ |
| 5/22 12:00 | Instagram 刷到广告      | Meta user_id(我们看不到)       | Tier 2 · Meta            |
| 5/23 14:00 | YouTube 看到 banner     | DV360 cookie                   | Tier 2 · DV360           |
| 5/24 09:00 | TikTok 点击视频         | TikTok click_id                | Tier 2 · TikTok          |
| 5/24 09:03 | 跳转到 AcmeFitness 官网 | GA4 `user_pseudo_id`           | Tier 1 · GA4             |
| 5/24 09:05 | 下单(已登录)            | hashed_email = `a5f1c8...d92b` | Tier 1 · Shopify/HubSpot |

**串联的三套 ID 桥**:

1. **第一方 hashed_email** — 投放时给 Meta 的就是这个,Meta 回流时带回 → 串得起
2. **TransUnion TUID + Experian EID** — 把不同设备/cookie 关联到同一个人
3. **GA4 user_pseudo_id ↔ hashed_email** — Sarah 登录时 GA4 自动绑定

→ 最终 Sarah 的完整 user_journey,**5 次接触归到同一个 pii_token**。

#### 三方数据在归因里的具体角色

| 三方                               | 归因里的作用                                                                    | 没有它会怎样                            |
| ---------------------------------- | ------------------------------------------------------------------------------- | --------------------------------------- |
| **TransUnion**                     | 跨设备身份桥 — 手机看 Meta、iPad 点 TikTok,TUID 把两设备绑成同一人              | 跨设备 journey 断掉,Meta 那次曝光归不上 |
| **Experian EID**                   | 同上,作为 TU 的补充身份图                                                       | 同上                                    |
| **Nielsen**                        | 电视广告曝光增量基准 — 投了 CTV 时告诉我们"这一波 CTV 带来多少新流量"           | 离线/电视渠道归因为零(高估了数字渠道)   |
| **Placer IQ**                      | 到店客流校准 — 有线下店时告诉我们"广告后到店增量"                               | 漏掉 O2O 转化                           |
| **Experian Combined API**(§6 已抓) | **画像属性当模型 feature** — 模型知道"高收入+健身兴趣"的人转化路径更短,加权调整 | 模型变成"看不见用户特征"的黑盒,精度下降 |

**§6 Combined API 那次调用是"画像 + 归因"双重收益,一次付费两处用。**

#### 一句话总结

> 归因**只用路径 1**(平台拿到完整身份的精细数据)+ DSP 回流(Tier 2),**用不上路径 2 的 DSP 目录**(匿名大池子,无法串 user journey)。
>
> §6 用 Combined API 抓到的画像属性,在 §14 归因阶段会被**二次利用为模型 feature** — 同一次 Experian 调用,既丰富画像又提升归因精度。

---

## 1. 阶段 ① · Ingestion(数据进来)

### 1.1 14 个 P1 数据源 · 谁拉什么 · 频率

| 数据源                            | 拉取内容                                                                         | 频率                  | 触发方式               |
| --------------------------------- | -------------------------------------------------------------------------------- | --------------------- | ---------------------- |
| **HubSpot**                       | Contacts(email + 生命周期阶段 + 来源)+ Companies + Deals                         | 每小时 / Webhook      | 客户 Private App token |
| **GA4**                           | Web 用户事件流(pageview · scroll · form_submit · conversion)+ acquisition source | 每 6 小时             | OAuth                  |
| **Meta Ads**                      | Campaign / Adset / Ad 日级指标 + audience insights                               | 每小时                | OAuth + App Review     |
| **DV360**                         | Campaign / Line Item / Creative 指标 + 受众数据                                  | 每小时                | OAuth + GCP project    |
| **StackAdapt**                    | Native / Display / Video 跨渠道指标                                              | 每小时                | GraphQL Key(CSM 申请)  |
| **The Trade Desk**                | Programmatic 全渠道指标 + Audience                                               | 每小时                | TTD AM 申请            |
| **TikTok Ads**                    | Campaign 指标 + Spark Ads + audience                                             | 每小时                | OAuth + App Review     |
| **LiveRamp**                      | RampID 解析 + 跨设备身份桥接                                                     | 实时 + 批量           | 合同                   |
| **LeadRX**                        | 归因事件流                                                                       | 每小时                | API key                |
| **Quorum**                        | 行为/政治舆情数据(特定客户)                                                      | 每周                  | API key                |
| **🔴 Experian Combined API**      | **Hygiene + OmniView(身份解析)+ UE(画像)+ DataLookup**                           | 按需(批量 + 实时调用) | **合同 + CSM**         |
| **🔴 Experian Suppression Files** | DNM / DNC / DNO / Deceased(合规黑名单)                                           | 每日批量              | **合同(法务硬门槛)**   |
| **🟡 TransUnion TruAudience**     | TUID/HHID + 跨设备身份 + 属性增强                                                | 实时 + 批量           | **合同 + mTLS 证书**   |
| **🟡 Nielsen**                    | 电视/CTV 收视基准                                                                | 月级                  | 合同                   |
| **🟡 Placer IQ**                  | 实体客流(地理围栏 + 到店数据)                                                    | 每周                  | 合同                   |
| **Tresorit**                      | 加密 CRM 批量文件传输路径(不是数据源)                                            | 客户发起              | 客户企业账号           |

### 1.2 AcmeFitness 示例 · 进来的数据长什么样

```
HubSpot Contact 样本(L2 PII):
  {
    "id": "1234567",
    "email": "sarah.lee@gmail.com",
    "firstname": "Sarah",
    "lastname": "Lee",
    "lifecyclestage": "marketingqualifiedlead",
    "lead_source": "website_form_q2_promo",
    "createdate": "2026-03-15"
  }

GA4 Event 样本(L0 — 已经匿名化):
  {
    "user_pseudo_id": "1234567890.abcde",
    "event_name": "purchase",
    "event_timestamp": "2026-05-20T14:32:00Z",
    "page_location": "/products/yoga-mat-pro",
    "value_usd": 89.00,
    "acquisition_source": "google_organic"
  }

Meta Ads Campaign 样本(L0):
  {
    "campaign_id": "23851234567",
    "campaign_name": "Q2 Yoga Mat Conversion",
    "spend_usd": 4500.00,
    "impressions": 230000,
    "clicks": 4800,
    "conversions": 142
  }

Experian Combined API 调用(出现在 ⑥ Enrichment 阶段,不在 ① Ingestion)
```

---

## 2. 阶段 ② · Landing Lake(原始数据 immutable 着陆)

### 2.1 落仓策略

整条 record(含所有字段 · 未做任何 transformation)写入 **`landing.<source>_records`**:

| 表                           | 例子                       |
| ---------------------------- | -------------------------- |
| `landing.hubspot_records`    | 整条 HubSpot Contact JSON  |
| `landing.ga4_events`         | 整条 GA4 event JSON        |
| `landing.meta_ads_records`   | 整条 Meta Ads insight JSON |
| `landing.experian_responses` | 整条 Experian API 响应     |

**为什么这样设计**:

- 合规审计要求**原始数据可回溯**(GDPR Art. 30)
- 后期发现某个字段被误丢 · 可以从 Landing 回灌
- **Immutable** — 一旦落,不能 update / delete(触发器拒绝)

### 2.2 关键技术字段

每条 Landing record 都加:

```
- record_id      UUID v7        (平台主键 · 跨 Lake 关联用)
- agency_id      UUID           (硬租户隔离键)
- client_id      UUID (nullable)(子租户隔离键)
- ingested_at    timestamptz    (摄入时间戳)
- content_hash   SHA-256        (防重复 · 同条 record 二次抓拒入)
```

> 这是后续所有 Lake 关联的"血缘起点"。

---

## 3. 阶段 ③ · Classify(字段分级)

`field_classifier.py` 对每条 record 的**每个字段**打标签:

| Level  | 名称     | 例子                                                       | 后续路由                         |
| ------ | -------- | ---------------------------------------------------------- | -------------------------------- |
| **L0** | Public   | campaign_id · impressions · clicks · spend · page_location | → Processed Lake                 |
| **L1** | Internal | lifecyclestage · campaign_name · advertiser_id             | → Processed Lake                 |
| **L2** | PII      | email · phone · firstname · ip · cookie · MAID             | → Raw PII Lake(加密)             |
| **L3** | PHI      | health_condition · diagnosis · medication                  | → Raw PII Lake(加密 + HIPAA tag) |

**产物**:`field_classification_manifest`(audit schema,与 Landing 同步生成),每行一条字段决策,合规审计可证。

### 3.1 AcmeFitness 示例 · HubSpot Contact 的分级结果

| 字段             | 值                       | Level  | 去向                                |
| ---------------- | ------------------------ | ------ | ----------------------------------- |
| `id`             | `1234567`                | L0     | Processed                           |
| `email`          | `sarah.lee@gmail.com`    | **L2** | **Raw PII Lake** + 生成 `pii_token` |
| `firstname`      | `Sarah`                  | **L2** | Raw PII Lake                        |
| `lastname`       | `Lee`                    | **L2** | Raw PII Lake                        |
| `lifecyclestage` | `marketingqualifiedlead` | L1     | Processed                           |
| `lead_source`    | `website_form_q2_promo`  | L0     | Processed                           |
| `createdate`     | `2026-03-15`             | L0     | Processed                           |

---

## 4. 阶段 ④ · 双 Lake 分流(原子双写)

### 4.1 Raw PII Lake(`raw_secure.*`)

只有 **L2 / L3 字段**进这里 + `record_id`:

```sql
raw_secure.users:
  user_id        UUID PK
  email_encrypted    bytea         -- Fernet(per-Agency KMS)
  email_hash         text(64)      -- SHA-256(lowercase(email)) · 查询用
  firstname_encrypted bytea
  lastname_encrypted  bytea
  agency_id          UUID

raw_secure.hubspot_pii_fields:
  record_id          UUID FK → landing.hubspot_records.record_id
  user_id            UUID FK → raw_secure.users.user_id
  email_encrypted    bytea
  ...
```

**严格访问**:

- 普通 endpoint **不能读** Raw PII Lake
- 只有 `PII Access Service` 用 purpose-bound JWT 短期 token(≤ 15 min)能读
- 每次读写一条 `pii_access_log` 行级审计

### 4.2 Processed Lake(`processed.raw.*`)

非 PII 字段 + `record_id` + `pii_token` 进这里:

```sql
processed.raw.hubspot_records:
  record_id          UUID PK
  pii_token          text(64)      -- SHA-256(email_hash + agency_salt)
  contact_id         text          -- HubSpot 原 id
  lifecycle_stage    text
  lead_source        text
  create_date        date
  agency_id          UUID
```

**关键**:`pii_token` 是反查 PII 的**唯一钥匙**,但本身不可逆。

### 4.3 AcmeFitness 示例 · 同一个 Sarah 在三个 Lake 里

| Lake      | 表                              | 内容                                                                                                                      |
| --------- | ------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| Landing   | `landing.hubspot_records`       | 整条 Contact JSON(immutable)                                                                                              |
| Raw PII   | `raw_secure.users`              | `email_encrypted = Fernet(sarah.lee@gmail.com)` · `email_hash = SHA-256(sarah.lee@gmail.com)`                             |
| Processed | `processed.raw.hubspot_records` | `pii_token = SHA-256(email_hash + acme_agency_salt)` · `lifecycle_stage = "marketingqualifiedlead"` · **没有 email/姓名** |

**跨 Lake 关联**:用 `record_id` 在三个 Lake 间 JOIN;用 `pii_token` 在 Processed Lake 内做"同人聚合"(不用暴露 email)。

---

## 5. 阶段 ⑤ · Normalize + Dedup(STEP 4-5)

### 5.1 dbt staging(STEP 4)

`processed.raw.*` → `processed.staging.*`:

- 字段名 snake_case 规范
- 时间统一 UTC
- 货币转换(按 Agency 偏好币种统一)
- ID 类型对齐 UUID
- 空值标准化

**产物**:`stg_hubspot.sql` · `stg_ga4.sql` · `stg_meta_ads.sql` 等。

### 5.2 五层去重(STEP 5)

```
1. Cursor 续抓(STEP 1)            — 同源不会重复拉
2. content_hash UNIQUE 约束        — Postgres 存储层拒重复
3. business-key MERGE(dbt)         — UPDATE OR INSERT by 业务键
4. 跨源去重(canonical event)      — Meta + DV360 + GA4 三方 attribute 一致性合并
5. 行数审计指纹                    — 每次同步记 new/skipped count
```

### 5.3 AcmeFitness 示例 · 跨源同人去重

```
HubSpot   Contact 1234567       email_hash = abc123...   →  pii_token = TOK_001
GA4       user_pseudo_id .abcde                          (匿名,无邮箱)
Meta Ads  Custom Audience match  hashed_email = abc123... →  pii_token = TOK_001 ✓ 同人

dbt model:  identity_bridge
  pii_token   external_id            source
  TOK_001     hubspot:1234567         hubspot
  TOK_001     ga4:.abcde              ga4 (probabilistic match by IP+UA, conf=0.7)
  TOK_001     meta:audience:9988      meta
```

→ Persona Agent 拿到的是**一个 Sarah · 三个数据源关联**,不是三个独立人。

---

## 6. 阶段 ⑥ · Enrich(关键阶段 · Experian 出场)

### 6.1 ⭐ Experian Combined API 调用流程

这是 **Experian 数据进入项目的关键时刻**。

```
触发条件:Agency 在 Persona Agent 启用 "Experian enrichment"

Persona Agent (内部)
   │
   │ "我有一批 hashed_email,需要画像增强"
   ▼
PII Access Service(单一受控出口)
   │
   │ 1. 验证 purpose-bound JWT(operation="experian_enrich_list")
   │ 2. 从 Raw PII Lake 解密拿 plaintext email/postal
   │ 3. 调用 Experian Combined API
   ▼
POST https://api.experian.com/marketing-services/targeting/v1/ue-ov
   {
     "subjects": [{"email": "sarah.lee@gmail.com", "postal_code": "10001"}, ...],
     "include": ["hygiene", "omniview", "ue", "data_lookup"]
   }
   │
   ▼
Experian 返回 4 段数据
   ┌─────────────────────────────────────────────────────────────┐
   │ ① Hygiene · 地址清洗                                          │
   │    "10001" → "10001-2345"(USPS 标准化 + DPV 验证)            │
   │                                                              │
   │ ② OmniView · 身份解析                                         │
   │    experian_pid = "EXP-12345"(个体)                          │
   │    experian_hhid = "HH-67890"(家庭)                          │
   │                                                              │
   │ ③ Universal Enrichment · 画像增强(只要 Agency 订阅的 segment) │
   │    age_bucket = "35-39"                                      │
   │    estimated_income = "$75K-$100K"                           │
   │    home_owner = "yes"                                        │
   │    children_present = "no"                                   │
   │    mosaic_segment = "Group K · Significant Singles"          │
   │    fitness_interest = "high"                                 │
   │    streaming_subscriber = "netflix,hulu"                     │
   │                                                              │
   │ ④ Data Lookup · segment 命中                                 │
   │    DTC_yoga_buyer = TRUE                                     │
   │    in_market_athleisure = TRUE                               │
   └─────────────────────────────────────────────────────────────┘
   │
   │ PII Access Service 把这些数据按分级路由:
   │   - experian_pid / experian_hhid → Raw PII Lake(L2)
   │   - 画像属性(age_bucket / income / mosaic / segments)→ Processed Lake(L0/L1)
   │ 写入 pii_access_log + audit_logs
   │
   ▼
processed.shared_experian_attributes(每 Agency 物理库内 · 跨客户共享)
   pii_token       age_bucket   income       mosaic                fitness_interest
   TOK_001         35-39        $75K-$100K   Significant Singles   high
   TOK_002         40-44        $100K-$150K  Cultural Connoisseurs medium
   ...
```

### 6.2 TransUnion 增强(可选 · 双源)

如果客户同时签了 TransUnion · 类似流程走 TU Combined API:

```
processed.shared_transunion_attributes:
  pii_token   TUID         HHID       age_bucket  ctv_viewer    cross_device_id_count
  TOK_001     TU-99887766  HH-12345   35-40       roku+samsung  4

processed.shared.identity_bridge(关键 · 跨厂商 ID 桥接):
  pii_token   experian_pid   experian_hhid   tuid           hhid_tu       confidence   source
  TOK_001     EXP-12345      HH-67890        TU-99887766    HH-12345      0.92         email+postal
```

### 6.3 Suppression Files 入仓(批量 · 每日)

```
processed.shared.suppression_lists:
  identifier_hash  type      effective_at  expires_at
  abc123hash       deceased  2026-01-15    never
  def456hash       dnc       2026-02-03    2027-02-03
  ...
```

**关键**:Audience Export 时强制 JOIN 这张表过滤,**未签 Suppression 合同 = Audience Export 不能上线**。

### 6.4 其他第三方数据的 enrichment 时点

| 数据源        | 时点                            | 落仓表                                |
| ------------- | ------------------------------- | ------------------------------------- |
| **Nielsen**   | 月级批量 · 与 Attribution 跑前  | `processed.shared.nielsen_tv_ratings` |
| **Placer IQ** | 周级批量 · 实体客流归因         | `processed.shared.placeriq_visits`    |
| **Quorum**    | 周级 · 行为舆情画像辅助         | `processed.quorum_signals`            |
| **LiveRamp**  | 实时 · audience activation 阶段 | 不入仓 · 仅作 ID 中介                 |

---

## 7. 阶段 ⑦ · Persona Agent 生成画像

### 7.1 Context Builder 组装上下文

```
Shared Context(给 Persona Agent 的"作业本"):
  ├─ Brand voice                  (HubSpot brand_config + Agency 配置)
  ├─ 历史 campaign 效果            (canonical.events 聚合)
  ├─ 历史 conversion 用户特征      (processed.shared_experian_attributes JOIN canonical)
  │     · 30-45 岁占 65%
  │     · 高收入($75K+)占 78%
  │     · Mosaic "Significant Singles" 占 41%
  │     · CTV 观看者占 60%
  ├─ Active suppression count    (Experian DNM/DNC 大小)
  └─ 平台 token 预算            (Agency monthly_token_budget)
```

### 7.2 Persona Agent 输出

```
Persona "AcmeFitness Q3 ICP":
  {
    "name": "Active Single Sarah",
    "demographics": {
      "age": "30-45",
      "gender": "female",
      "income": "$75K-$150K",
      "household": "single or DINK",
      "location": "Tier 1 cities"
    },
    "psychographics": {
      "mosaic_group": "Significant Singles",
      "fitness_interest": "high",
      "streaming_habit": "netflix + hulu",
      "wellness_segments": ["yoga_buyer", "in_market_athleisure"]
    },
    "recommended_channels": ["instagram", "youtube_ctv", "podcast"],
    "estimated_reach": 1_800_000,
    "data_sources": ["experian_ue", "transunion_attributes", "ga4_conversion"],
    "confidence": 0.87,
    "generated_at": "2026-05-21T10:30:00Z"
  }
```

**关键**:Agent 看到的**始终是 `pii_token` 级别**的画像 · **从不接触明文 email/姓名**。

---

## 8. 阶段 ⑧ · Audience Build(可投放清单)

### 8.1 把 Persona 翻译成投放种子

`AudienceExportService.translator`:

```
Persona "Active Single Sarah"
   ↓
SQL:
SELECT pii_token
FROM processed.shared_experian_attributes
WHERE age_bucket IN ('30-34','35-39','40-44')
  AND estimated_income >= '$75K'
  AND mosaic_segment = 'Significant Singles'
  AND fitness_interest = 'high'
   ↓
匹配到 1,800,000 个 pii_token
```

### 8.2 通过 PII Access Service 解析为可投放 ID

```
PII Access Service (operation="build_audience_hash_list")
   │ purpose-bound JWT,≤ 15min
   ▼
对 1.8M 个 pii_token:
  - 查 Raw PII Lake 拿 plaintext email
  - 重新 SHA-256(lowercase(email))生成"投放规范" hashed_email
  - 用 LiveRamp ATS 解析 → RampID
   ▼
audience_hash_list(临时文件 · 仅内存或 tmpfs):
  [hashed_email_1, hashed_email_2, ...]
  [ramp_id_1, ramp_id_2, ...]
```

### 8.3 ⚠️ 应用 Experian Suppression Filter(合规硬门槛)

```
audience_hash_list                processed.shared.suppression_lists
  hashed_email_1                       hashed_email_3  (DNC)
  hashed_email_2                       hashed_email_5  (Deceased)
  hashed_email_3      WHERE NOT IN
  hashed_email_4
  hashed_email_5
   ↓                  →               过滤后:
   1,800,000          →                1,750,000(剔除 50K)

audit_events 记录:
  剔除条数:50,000
  剔除来源:experian_suppression_dnc:30K + deceased:20K
  agency_id, client_id, audience_id, timestamp
```

→ DSAR / 合规审计可证"我们确实做了 suppression"。

---

## 9. 阶段 ⑨ · Creative Agent 生成文案

### 9.1 输入

```
Creative Agent input:
  ├─ Persona blueprint           (来自 ⑦)
  │     · "Active Single Sarah" · Mosaic Significant Singles · 健身 + 健康 + 流媒体
  ├─ Brand voice                 ("Confident · Warm · Empowering")
  ├─ 历史高 CTR 创意                (canonical.creatives top performers)
  ├─ Platform format constraints  (Instagram square 1:1 · YouTube 16:9 · Meta carousel ...)
  └─ A/B 实验变量                 (3 个文案 / 2 个 hook / 2 个 CTA = 12 个 variant)
```

### 9.2 输出

```
Creative Variants(每平台 · 多 variant):
[
  {
    platform: "INSTAGRAM",
    format: "feed",
    copy_text: "Reach Your Best Self. The new YogaPro arrives this fall.",
    cta: "Shop Now",
    image_prompt: "confident woman 35, yoga studio, golden hour, premium mat...",
    variant_id: "creative_v1_instagram_a"
  },
  ...12 个 variants
]
```

### 9.3 写回与审计

- 不写回任何明文 PII(Persona 输入已经是 pii_token 级)
- Langfuse 追踪每次 LLM 调用 · 含 prompt + completion + token cost
- `audit_logs` 记 `creative.generate` · `model: claude-sonnet` · `tokens_used: 4500`

---

## 10. 阶段 ⑩ · Media Agent 媒介采买

### 10.1 输入

```
Media Agent input:
  ├─ Audience(⑧ 输出 · 已 suppression 过滤)
  ├─ Creative Variants(⑨ 输出 · 12 个)
  ├─ Budget(客户合同 · 季度 $200K)
  ├─ Channel preferences(来自 Persona · 推荐 IG / YouTube CTV / Podcast)
  ├─ TrueTouch comm preferences(若 Experian 含此) · "best time: Sun 6-9pm"
  └─ Nielsen TV ratings           (CTV 时段优化)
```

### 10.2 输出 · 分配方案(等待 HITL 审批)

```
Recommended Budget Split:
  Meta(IG)              $80K  · 4 variants · estimated reach 800K
  YouTube CTV           $60K  · 3 variants · estimated reach 500K
  TikTok                $30K  · 2 variants · estimated reach 200K
  StackAdapt Native     $20K  · 2 variants · estimated reach 200K
  Trade Desk Podcast    $10K  · 1 variant  · estimated reach 100K
                         ──────
  Total                 $200K

Estimated CPM by channel ↑↑ 已根据历史 mart 计算
Estimated CTR by Mosaic segment ↑↑ Significant Singles 历史 CTR 1.8% (vs benchmark 1.2%)
```

### 10.3 ⚠️ Human-in-the-loop 强制审批

PSD §10.1 明确要求:**预算调整 / 写回 / Campaign 启停必须人工确认**。

```
平台 UI:
  ┌──────────────────────────────────────┐
  │ Media Agent 提议:                    │
  │   Meta $80K · YouTube CTV $60K · ... │
  │                                      │
  │   [✓ Approve & Launch]               │
  │   [Edit Allocation]                  │
  │   [Decline & Provide Feedback]       │
  └──────────────────────────────────────┘

Approval audit:
  approver_id: agency_admin_xxx
  approved_at: 2026-05-21T11:42:00Z
  allocation_locked: {...}
```

---

## 11. 阶段 ⑪ · Activation(投放出去)

### 11.1 跨 DSP 推送

```
audience_hash_list(已 suppression)
   │
   ├──► Meta Custom Audience API
   │       POST /audiences/CA_<id>/users  · hashed_email[]
   │
   ├──► DV360 Customer Match
   │       POST /customermatch/upload     · hashed_email[]
   │
   ├──► TikTok Custom Audience
   │
   ├──► StackAdapt Audience Hub
   │
   └──► The Trade Desk First-Party Data
           via LiveRamp RampID 中介
```

**每次推送都 audit_logs 一行**:`audience.push.<platform>` · 行数 · status_code · external_audience_id

### 11.2 Creative 发布

Creative variants 发布到对应 DSP 的 ad object:

```
Meta Ads:
  POST /act_<account>/ads
  body: { creative_id: meta_cr_001, audience_id: CA_001, budget: $80K, ... }
```

---

## 12. 阶段 ⑫ · 数据回流(Attribution 输入)

### 12.1 各 DSP 回报指标(每小时)

```
连续 14 天 ·  每小时同步:
  Meta       → raw_meta_ads.records(impressions / clicks / spend / conversions)
  DV360      → raw_dv360.records
  TikTok     → raw_tiktok_ads.records
  StackAdapt → raw_stackadapt.records
  Trade Desk → raw_trade_desk.records
  GA4        → raw_ga4_events(conversion / purchase events)
```

### 12.2 dbt mart 聚合

```
mart_campaign_unified:
  campaign_id  platform   date         impressions  clicks  spend    conversions  conversion_value
  AcmeQ3_001   meta       2026-08-01   125,000      2,500   $4,200   38           $3,400
  AcmeQ3_001   dv360      2026-08-01   90,000       1,800   $3,500   25           $2,200
  AcmeQ3_001   stackadapt 2026-08-01   45,000       900     $1,800   12           $1,100
  ...
```

---

## 13. 阶段 ⑬ · Attribution Agent 归因分析

### 13.1 输入

```
Attribution Agent input:
  ├─ mart_campaign_unified            (各 DSP 聚合)
  ├─ raw_ga4_events                   (转化路径详情)
  ├─ identity_bridge                  (TUID/experian_pid 链)
  ├─ LiveRamp RampID 时间序列          (跨设备触点)
  ├─ TransUnion cross-device          (CTV ↔ Mobile ↔ Desktop)
  ├─ Nielsen TV ratings               (TV/CTV 增强基准)
  └─ Placer IQ store visits           (实体到店 · 零售客户)
```

### 13.2 输出 · MTA + MMM 归因

```
Attribution Report:
  Touch sequence (一个 Sarah 转化路径):
    1. YouTube CTV 看 video → Roku TV
    2. Instagram Story 看素材 → iPhone
    3. Google Search "yoga mat pro" → MacBook
    4. Conversion: 89 USD purchase → MacBook + acme.com

  Multi-Touch Attribution(线性):
    YouTube CTV: 25% credit
    Meta IG    : 35% credit
    Google     : 40% credit

  Marketing Mix Modeling:
    每 $1 Meta = 1.4 USD revenue
    每 $1 YouTube CTV = 1.8 USD revenue   ← TV/CTV 增强(Nielsen 加持)
    每 $1 StackAdapt Native = 0.9 USD     ← 应减少投入

  Insights (LLM-narrated):
    "Q3 第 6 周看到 YouTube CTV 单位回报率明显高于其他渠道(1.8x · 高于 1.4x Meta 基准)。
     建议将 StackAdapt 30% 预算迁移到 CTV。
     潜在影响:净 ROAS +12-15%。需 Media Agent 审批后调整。"
```

### 13.3 ⚠️ 关键合规点

- Attribution 的所有跨设备链都是 **pii_token-level**,从不暴露 email
- 跨设备身份基于 TUID/HHID + LiveRamp + GA4 概率匹配,**带 confidence**
- LLM "insight 解释"是辅助,**不替代人工业务决策**

---

## 14. 阶段 ⑭ · Client Portal(白标交付)

### 14.1 给 Client Viewer 看的内容

```
Client Portal · AcmeFitness Q3 Dashboard
  ┌──────────────────────────────────────────────┐
  │ AcmeFitness · 白标 logo + 主色调               │
  ├──────────────────────────────────────────────┤
  │  Reach              Engagement     Conversions │
  │  1,750,000 users    44,000 clicks   1,250      │
  │                                                │
  │  Total Spend: $200K        ROAS: 1.62          │
  │                                                │
  │  Top Insight (AI-generated):                   │
  │    "YouTube CTV 是本次 campaign 的明星 channel" │
  │                                                │
  │  Channel Breakdown(图表)                     │
  │  Time Series                                  │
  │  Persona Match Rate(隐去具体身份图谱)        │
  │  Suppression Compliance:50,000 records 已过滤  │
  │                                                │
  │  [Download Q3 PDF Report]                      │
  └──────────────────────────────────────────────┘
```

### 14.2 数据访问边界

- Client viewer 只通过 **RLS by client_id** 看到自己 client 的数据
- 不能看到 Agency 其他 client 的对比
- 不能看到底层 pii_token / identity_bridge
- 不能直接调用任何 PII Access Service operation

---

## 15. 阶段 ⑮ · DSAR / 数据删除(逆向流程)

终端用户(Sarah)向 Agency 提"删除我的数据"请求:

```
Agency Admin 收到 DSAR delete request
   ↓
平台 DSAR FSM(自动工作流 · 30 天 SLA)
   ↓
   ├─ Step 1: 用 email_hash 反查 raw_secure.users(L2 PII)
   │            → 拿到 user_id + pii_token
   ↓
   ├─ Step 2: 跨 Lake 删除(用 record_id + pii_token 反查)
   │   ├─ landing.*(标记 deleted=true · 不物理 purge · 审计保留)
   │   ├─ raw_secure.*(物理 delete · audit 保留)
   │   └─ processed.*(标记 deleted · audit 保留)
   ↓
   ├─ Step 3: 通知第三方源同步删除
   │   ├─ Experian /v1/dsar/delete
   │   ├─ TransUnion /v1/dsar/delete(若合同含)
   │   ├─ HubSpot     /contacts/{id}(可选 · 客户主导)
   │   └─ Meta CAPI 删除该 hashed_email
   ↓
   ├─ Step 4: 删除 pgvector embedding(Memory & Retrieval · V2)
   ↓
   ├─ Step 5: audit_logs 记录全部步骤
   │            (audit 行不能删 · GDPR Art. 30)
   ↓
   └─ Step 6: 通知客户 "DSAR completed"
              + 30 天前完成 SLA 证明
```

---

## 16. 总览 · 一张表看完所有第三方数据的去向

| 数据源                       | 进入阶段                        | 落仓位置                                                         | 主要被谁消费                                           | 出去阶段                 |
| ---------------------------- | ------------------------------- | ---------------------------------------------------------------- | ------------------------------------------------------ | ------------------------ |
| **HubSpot**                  | ① Ingest                        | landing + raw_secure(email) + processed                          | Persona / Audience / Attribution                       | ⑪ Meta Custom Audience   |
| **GA4**                      | ① Ingest                        | landing + processed.ga4_events                                   | Attribution / Persona                                  | ⑭ Client Portal          |
| **Meta Ads**                 | ① Ingest                        | landing + processed.meta_ads                                     | Attribution                                            | ⑭                        |
| **DV360**                    | ① Ingest                        | landing + processed.dv360                                        | Attribution                                            | ⑭                        |
| **StackAdapt**               | ① Ingest                        | landing + processed.stackadapt                                   | Attribution                                            | ⑭                        |
| **Trade Desk**               | ① Ingest                        | landing + processed.trade_desk                                   | Attribution                                            | ⑭                        |
| **TikTok Ads**               | ① Ingest                        | landing + processed.tiktok                                       | Attribution                                            | ⑭                        |
| **🔴 Experian Combined API** | ⑥ Enrich                        | processed.shared_experian_attributes(画像)+ raw_secure(pid/hhid) | **Persona Agent**(主)+ Audience(种子)+ Attribution(次) | ⑧ Audience build         |
| **🔴 Experian Suppression**  | ① Ingest(批量)                  | processed.shared.suppression_lists                               | **Audience Export 强制 JOIN**                          | ⑨ Suppression filter     |
| **🟡 TransUnion**            | ⑥ Enrich(+ ⑬ Attribution input) | processed.shared_transunion_attributes + identity_bridge         | Attribution(跨设备)+ Persona(双源)                     | ⑪ Activation(via RampID) |
| **LiveRamp**                 | ⑧ Audience build + ⑪ Activation | 不入仓 · 实时中介                                                | Audience Export · Attribution                          | ⑪ DSP 推送               |
| **🟡 Nielsen**               | ⑥ Enrich(月级)                  | processed.shared.nielsen_tv_ratings                              | Attribution(TV/CTV 增强)                               | ⑭                        |
| **🟡 Placer IQ**             | ⑥ Enrich(周级)                  | processed.shared.placeriq_visits                                 | Attribution(实体到店)                                  | ⑭                        |
| **Quorum**                   | ⑥ Enrich(周级)                  | processed.quorum_signals                                         | Persona(政治/舆情画像辅助)                             | ⑦ Persona Agent          |
| **LeadRX**                   | ① Ingest(实时)                  | landing + processed.leadrx                                       | Attribution                                            | ⑭                        |
| **Tresorit**                 | ① Ingest(批量传输路径)          | landing(CSV/Excel 文件)                                          | ETL importer                                           | ⑤ Normalize              |

---

## 17. 关键合规节点 · 全程审计如何贯穿

每一个阶段都写 `audit_event(...)` 到 `public.audit_logs`:

| 阶段                     | audit event                                                                             |
| ------------------------ | --------------------------------------------------------------------------------------- |
| ① Ingest                 | `integration.<source>.sync_start` · `.sync_complete` · `.sync_failed`                   |
| ② Landing                | `lake.landing.record_written` · `.idempotent_skipped`                                   |
| ③ Classify               | `field_classifier.decision`                                                             |
| ④ Lake split             | `lake.raw_pii.write` · `lake.processed.write`                                           |
| ⑥ Experian/TU enrichment | `experian.enrich_called` · `pii_access.read_decrypt`                                    |
| ⑦ Persona                | `persona.generate` · `model: ...` · `tokens: ...`                                       |
| ⑧ Audience build         | `audience.build` · `seed_count: 1.8M`                                                   |
| ⑨ Suppression filter     | `audience.suppression_applied` · `removed: 50K` · `source: dnc + deceased`              |
| ⑩ Creative               | `creative.generate`                                                                     |
| ⑩ Media Agent            | `media.allocation.proposed` · `media.allocation.approved`(人工)                         |
| ⑪ Activation             | `audience.push.<platform>` · `external_audience_id: ...`                                |
| ⑬ Attribution            | `attribution.report.generate`                                                           |
| ⑭ Portal view            | `portal.dashboard.accessed`(client viewer)                                              |
| ⑮ DSAR                   | `dsar.requested` · `dsar.lake.deleted` · `dsar.third_party.notified` · `dsar.completed` |

合规审计师可以从 `audit_logs` 一条 `dsar.requested` 链路追溯到所有被删除的 Lake 行,GDPR Art. 30 完整可证。

---

## 18. 给客户的一段话

> Experian 在我们的流程里**不是单点工具,是贯穿全旅程的关键支柱**:
>
> - **阶段 ⑥** Experian Combined API 给 Persona Agent 提供画像基础(Mosaic / age_bucket / income / segment)
> - **阶段 ⑧** Experian Suppression Files 是 Audience Export **合规硬门槛**(未签 = 不能上线 CRM 营销)
> - **阶段 ⑪** Experian 的 Identity Graph 与 LiveRamp / TU 一起做跨厂商 ID 桥接
> - **阶段 ⑬** Experian 的 hygiene/标准化数据是 Attribution 跨源对齐的基础
> - **阶段 ⑮** DSAR 触发时 · 必须同步调 Experian 的 delete API 才合规
>
> **没有 Experian = 不只是缺一个数据源,而是 Persona / Audience / Attribution / 合规 4 个模块同时降级**。
>
> TransUnion 是**互补**(主打 CTV / 跨设备);Nielsen 是 TV/CTV 收视基准;Placer IQ 是实体客流;LiveRamp 是 ID 中介。**这 5 家都不可以靠"内部建"替代**,必须签合同接入。
>
> 完整生命周期 · 从 CRM 数据进来 · 到广告投放出去 · 到 Client Portal 报表回流 · 每条记录都有 `record_id` + `pii_token` 跨 Lake 关联 · 每个动作都有 `audit_logs` 留痕 · DSAR 一键反查全栈删除。**这是符合 GDPR + CCPA + HIPAA + SOC 2 标准的端到端数据生命周期**。

---

## 19. 关联文档

- [`docs/EXPERIAN-DATA-ROLE.md`](./EXPERIAN-DATA-ROLE.md) — Experian 在项目里的角色详解
- [`docs/EXPERIAN-APIS-TO-CONFIRM.md`](./EXPERIAN-APIS-TO-CONFIRM.md) — Experian 接口范围客户确认
- [`docs/TRANSUNION-INTEGRATION.md`](./TRANSUNION-INTEGRATION.md) · [`docs/HUBSPOT-INTEGRATION.md`](./HUBSPOT-INTEGRATION.md) · [`docs/STACKADAPT-INTEGRATION.md`](./STACKADAPT-INTEGRATION.md) · [`docs/INTEGRATION-GUIDE-GA4-DV360.md`](./INTEGRATION-GUIDE-GA4-DV360.md) — 各家 adapter 详情
- [`docs/ELT-8-STEP-DESIGN.md`](./ELT-8-STEP-DESIGN.md) — 八步管道设计(对应阶段 ①-⑥)
- [`docs/MULTI-TENANT-DB.md`](./MULTI-TENANT-DB.md) — 多租户物理库(每 Agency 自己的 Lake)
- [`docs/PII-DESIGN-SOLUTION.md`](./PII-DESIGN-SOLUTION.md) — PII Access Service 详解(阶段 ⑥ / ⑧ 核心)
- [`docs/psd/technical-solution.md`](./psd/technical-solution.md) — PSD 原文(本文档落地)
