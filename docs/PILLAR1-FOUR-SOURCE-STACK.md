# Pillar 1 四源合成栈架构 · TransUnion + Claritas PRIZM + GWI + LiveRamp

_Last updated: **2026-05-26**_

> **文档类型**:数据架构 / 集成总览
> **目标读者**:后端工程 / 数据团队 / 产品 / 客户技术对接 / 投资人沟通
> **目的**:说明 Persona Engine(Pillar 1)的四个数据源**各自贡献什么、如何在 ReceptivIQ 自有 schema 下合成、数据如何流转**。这是把四份单独的 vendor 集成文档(TransUnion / Claritas / GWI / LiveRamp)串成"一个引擎"的架构视图。
> **决策依据**:见 [`PILLAR1-DATA-FOUNDATION-DECISION.md`](./PILLAR1-DATA-FOUNDATION-DECISION.md)(为什么是这四家、Experian 为何降级)。

---

## 0. 核心理念:Synthesis is the moat(合成才是护城河)

> **没有任何一家数据源是"承重"的。ReceptivIQ 的专有价值在于把四源合成为 persona / 渠道倾向 / 文案匹配 —— 这是竞品买不到、Agency 自己拼不出来的。**

- 单一数据源(如纯 Experian)→ 输出像数据源本身,平台沦为"数据商的 UI",议价权被锁死。
- 四源合成 → 合成层成为产品本身,且不被任一供应商的定价/合同绑架。

---

## 1. 一句话分工

| 数据源                     | 角色              | 回答的问题             | 一句话                             |
| -------------------------- | ----------------- | ---------------------- | ---------------------------------- |
| **TransUnion TruAudience** | 🔧 锚(anchor)     | **是谁 + 在哪 + 人口** | 身份解析 + 人口画像 + 渠道倾向     |
| **Claritas PRIZM Premier** | 心理分群 taxonomy | **属于哪一类人**       | 68 段 Mosaic 等价分群,可携带到 DSP |
| **GWI**                    | 态度 / 信息层     | **为什么买 + 怎么说**  | 调研型态度/媒体/语气信号           |
| **LiveRamp**               | 身份 + 激活       | **怎么投出去**         | 跨源身份解析 + 100+ DSP 激活       |

> **记忆法**:TransUnion 是谁 → Claritas 哪类人 → GWI 为什么/怎么说 → LiveRamp 投出去。

---

## 2. 架构总览图

```
╔════════════════════════════════════════════════════════════════════╗
║                  Pillar 1 · Persona Engine 四源合成                  ║
╠════════════════════════════════════════════════════════════════════╣

  第一方数据                  ┌──────────────────────────────────┐
  (HubSpot/GA4/CSV)  ───────► │  ReceptivIQ 自有 Schema(合成层)  │
                              │  processed.contacts_canonical    │
                              └──────────────────────────────────┘
                                     ▲   ▲   ▲   ▲
              ┌──────────────────────┘   │   │   └──────────────────────┐
              │                          │   │                          │
     ┌────────┴────────┐   ┌─────────────┴┐ ┌┴─────────────┐   ┌────────┴────────┐
     │  TransUnion     │   │  Claritas    │ │   GWI        │   │   LiveRamp      │
     │  TruAudience    │   │  PRIZM       │ │              │   │                 │
     │  ─────────────  │   │  ─────────── │ │  ──────────  │   │  ─────────────  │
     │ 身份解析(TUID)  │   │ 68 段心理分群 │ │ 态度/价值观   │   │ RampID 跨源身份 │
     │ 人口属性        │   │ Social/Life  │ │ 媒体习惯      │   │ 180+ 数据市场   │
     │ 渠道倾向        │   │ stage Group  │ │ 信息接受度    │   │ 100+ DSP 激活   │
     │ 98% 美国成人    │   │ ≈ Mosaic     │ │ 1.4M+ 调研    │   │ (含 Experian段) │
     └─────────────────┘   └──────────────┘ └──────────────┘   └─────────────────┘
        确定性 · 个体级        建模 · 分群级      调研 · 人群级         身份 · 激活

                                     │
                                     ▼  合成
              ┌───────────────────────────────────────────────┐
              │  Persona = 身份骨架(TU) + 分群标签(Claritas)   │
              │           + 动机/语气(GWI) + 可激活ID(LiveRamp) │
              └───────────────────────────────────────────────┘
                                     │
            ┌────────────────┬───────┴────────┬──────────────────┐
            ▼                ▼                ▼                  ▼
      ⑦ Persona        ⑧ Audience      ⑩ Creative         ⑫ Activation
        Agent            Build            Agent              (LiveRamp)
```

---

## 3. 每一源贡献什么(详表)

### 3.1 TransUnion TruAudience — 锚

- **覆盖**:98% 美国成人、1.27 亿家庭、8000 万 connected homes
- **贡献**:身份解析(TUID/HHID)+ 数百人口属性 + 渠道倾向 + 跨设备(后 Neustar 整合)
- **为什么是锚**:最接近 Experian 单源替代的一家;**项目已有商业关系**
- **集成**:mTLS + 批量文件交付为主 → 详见 [`TRANSUNION-INTEGRATION.md`](./TRANSUNION-INTEGRATION.md)

### 3.2 Claritas PRIZM Premier — 心理分群

- **覆盖**:全美每户 → 68 段 / 11 Lifestage / 14 Social Group
- **贡献**:Mosaic 等价的人群命名 taxonomy
- **关键价值**:**与 Mosaic 在 publisher/DSP 层可互换** → persona 无损携带到 StackAdapt/Trade Desk/Meta
- **集成**:批量文件(地理映射,零 PII)优先 → 详见 [`CLARITAS-PRIZM-INTEGRATION.md`](./CLARITAS-PRIZM-INTEGRATION.md)

### 3.3 GWI — 态度 / 信息层

- **覆盖**:1.4M+ 年度调研 / 52+ 市场 / 250K+ profiling points
- **贡献**:态度、价值观、媒体习惯、信息接受度 —— "为什么买 + 怎么说"
- **关键价值**:**让 Pillar 3 文案 Agent 在 Phase 1 可演示**;提供公开 API + MCP(可直连 Claude)
- **集成**:Platform API / MCP,在 **persona/segment 层** overlay(非个体)→ 详见 [`GWI-INTEGRATION.md`](./GWI-INTEGRATION.md)

### 3.4 LiveRamp — 身份 + 激活

- **覆盖**:RampID 跨源身份 + 180+ 数据提供商市场(含 Experian/TransUnion 段)
- **贡献**:把合成后的受众**投到 100+ DSP**;并保留"按段买 Experian/TU"的 optionality
- **关键价值**:**项目已集成**;激活通道复用成本最低
- **集成**:见 `docs.liveramp.com`

---

## 4. 数据如何合成(技术流程)

```
STEP 1 · 第一方落地
  HubSpot/GA4/CSV → landing → raw_pii(加密) + processed.contacts_canonical(pii_token)

STEP 2 · TransUnion 增强(个体级 · 锚)
  对每条 contact 用 hashed PII 解析 → 回写 TUID + 人口属性 + 渠道倾向
  → canonical.{tuid, age_band, income_band, channel_propensity}

STEP 3 · Claritas PRIZM append(分群级)
  地址 → ZIP+6 → JOIN prizm_zip_segment → 回写 segment
  → canonical.{prizm_segment, social_group, lifestage_group}

STEP 4 · GWI overlay(人群级 · 在 persona 层)
  Persona Agent 按 segment/人口特征查询 GWI → 叠加态度层
  → personas.{psychographics, channel_preferences, messaging_propensity}

STEP 5 · 合成 persona
  Persona Agent 把以上四层喂给 LLM → 生成可读、可解释、可激活的 ICP

STEP 6 · LiveRamp 激活
  受众 hashed_email → RampID → 推送 100+ DSP
```

> **粒度分层是关键设计**:TransUnion 个体级、Claritas 分群级、GWI 人群级 —— 三种粒度在合成层按 `pii_token`/`segment`/`persona_id` 逐级关联,GWI 不下沉到个体(规避 PII + 节省配额)。

---

## 5. 合成层数据模型(processed.contacts_canonical 增列)

| 列                                                         | 来源       | 粒度 | 级别  |
| ---------------------------------------------------------- | ---------- | ---- | ----- |
| `pii_token`                                                | 第一方哈希 | 个体 | L1    |
| `tuid` / `age_band` / `income_band` / `channel_propensity` | TransUnion | 个体 | L1/L2 |
| `prizm_segment` / `social_group` / `lifestage_group`       | Claritas   | 分群 | L1    |
| `ramp_id`                                                  | LiveRamp   | 个体 | L1    |
| (persona 层)`psychographics` / `messaging_propensity`      | GWI        | 人群 | L0/L1 |

> 所有个体级 PII 仍只存在 Raw PII Lake(加密);canonical 表只存 token + 聚合/分群标签。

---

## 6. 合规要点(四源统一)

> 完整闸门见 [`EXPERIAN-ALTERNATIVES.md` §0](./EXPERIAN-ALTERNATIVES.md)。

| 源         | 合规初判        | PII 暴露             | 关键约束                                               |
| ---------- | --------------- | -------------------- | ------------------------------------------------------ |
| TransUnion | 🟢 强(可签 BAA) | 个体级               | mTLS;入仓前哈希;审计 `enrichment.transunion.completed` |
| Claritas   | 🟢 较强         | 分群(地理映射零 PII) | 优先地理映射方案;append 须哈希                         |
| GWI        | 🟢 较强         | 人群级(最低)         | persona 层 overlay;MCP 严禁传 PII                      |
| LiveRamp   | 🟢 强           | 个体级(激活)         | RampID;purpose-bound 令牌;零落盘                       |

**四源共同硬约束**:

1. **合规抑制(G6)不在四源覆盖内** → 必须由 **LexisNexis/AccuData** 兜底(Deceased/DNC)。
2. **入仓前 `hash_identifier()`**,禁止明文 PII 落仓。
3. **每次调用写 `enrichment.<source>.completed` 审计**,失败 5xx 不静默。
4. **DSAR 级联**:四源 append 结果随第一方记录删除;地理/人群级聚合无 PII 无需删。
5. **凭据 Fernet 加密**,DSN/token 禁止明文出现在日志/Sentry。

---

## 7. 实施顺序建议

| 阶段             | 接入                                                  | 理由                           |
| ---------------- | ----------------------------------------------------- | ------------------------------ |
| **Phase 1a**     | TransUnion(锚)+ LiveRamp(已集成)                      | 先有身份骨架 + 激活通道        |
| **Phase 1b**     | Claritas PRIZM(地理映射)                              | 叠加分群,persona 可读化        |
| **Phase 1c**     | GWI(persona 层 overlay)                               | 叠加态度,驱动 Creative Agent   |
| **Phase 1 兜底** | LexisNexis 抑制                                       | 投放前合规闸门,不可省          |
| **Phase 2**      | Experian enrichment(经 LiveRamp 市场或 Consumer View) | 在 Experian 深度领先的垂直补强 |

---

## 8. 与 9 月投资人 demo 的关系

四源栈让 demo **更难被否定**(详见 [决策记录 §7](./PILLAR1-DATA-FOUNDATION-DECISION.md)):

- 投资人最难问题"这和直接 license Experian 有何区别?"→ **可答:合成是专有的**
- persona 输出是 PRIZM 命名(直观)+ TransUnion 渠道倾向 + GWI 态度驱动的文案 + LiveRamp 激活 —— **synthesis 可见**

---

## 9. 关联文档

- 决策记录(为什么):[`PILLAR1-DATA-FOUNDATION-DECISION.md`](./PILLAR1-DATA-FOUNDATION-DECISION.md)
- 替代方案对比:[`EXPERIAN-ALTERNATIVES.md`](./EXPERIAN-ALTERNATIVES.md)
- TransUnion 集成:[`TRANSUNION-INTEGRATION.md`](./TRANSUNION-INTEGRATION.md)
- Claritas PRIZM 集成:[`CLARITAS-PRIZM-INTEGRATION.md`](./CLARITAS-PRIZM-INTEGRATION.md)
- GWI 集成:[`GWI-INTEGRATION.md`](./GWI-INTEGRATION.md)
- 端到端数据流:[`END-TO-END-DATA-FLOW.md`](./END-TO-END-DATA-FLOW.md)
