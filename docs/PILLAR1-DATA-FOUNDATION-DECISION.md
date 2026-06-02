# Pillar 1 数据地基决策记录(ADR)· Experian → 四源合成栈

_Last updated: **2026-05-26**_

> **文档类型**:架构决策记录(ADR)
> **来源**:Whale Song × ReceptivIQ Discovery — Sprint 0 简报(Jason Amunwa / Shiguang Lu)
> **决策对象**:ReceptivIQ Persona Engine(Pillar 1)的底层数据源
> **状态**:🟢 已建议,待 Rose Fulton 在 Sprint 0 结束前确认
> **目标读者**:创始人 / 技术总监 / 后端工程 / 投资人沟通

---

## 1. 决策摘要(TL;DR)

> **把 Pillar 1 的数据地基从"Experian 单源"改为"TransUnion + Claritas + GWI + LiveRamp"四源合成栈;Experian 降级到 Phase 2/3 的 enrichment 层。**

**一句话理由**:Experian 的 API 是"增强已有名单",不是"按条件发现人群"——而 Persona Engine 的本职恰恰是后者。继续用 Experian 做地基,要么让 ReceptivIQ 沦为"Experian 的 UI"(无护城河),要么自建查询引擎(成本/工期爆炸)。

---

## 2. 背景与起因

原平台提案把 **Experian 列为 Pillar 1 的主数据源**,前提假设是:可以对接一个 **query 式 API** —— 提交受众条件,返回匹配的消费者记录。

Sprint 0 期间,Whale Song 与 Experian 工程联系人(Sunaina)做集成尽调,**该假设被推翻**。

---

## 3. 关键发现:Experian 集成模型的真相

| 维度                                   | 真实情况                                                                                                                                    |
| -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| **Combined API 实际是什么**            | **Enrichment(增强)API**。输入你已持有的 PII(姓名+地址 / 邮箱 / 电话),返回这些**特定记录**的附加属性。**不能**按心理/行为/垂直条件返回人群。 |
| **Persona Engine 真正需要的**          | 从策略师的 prompt **发现人群**(discover audiences),而非增强一份已知名单 —— 形状完全不匹配。                                                 |
| **Experian 为此用例实际 license 什么** | **Consumer View** —— 营销数据库的平面文件 feed,季度刷新交付到 S3/SFTP。约 2.5 亿美国消费者、每户约 2,300 属性。                             |
| **代价**                               | 要变成可用的 Persona Engine,ReceptivIQ 必须**自建**查询引擎、分群构建器、lookalike 建模、激活管道。                                         |

### 两条死路

| Path A · 薄包 Experian                                                                     | Path B · 在 Consumer View 上自建引擎                   |
| ------------------------------------------------------------------------------------------ | ------------------------------------------------------ |
| ReceptivIQ 沦为 Experian Audience Engine UI 的薄壳                                         | License 平面文件,自建查询/分群/建模/激活               |
| **风险:无专有护城河** —— 输出就是 Experian 的(Mosaic 可识别);Experian 改价直接冲击单位经济 | **风险:成本/工期数量级上升** —— 赶不出 9 月投资人 demo |

> 两条路都不是当初卖给客户的方案,也都产不出 9 月目标:**一个明显专有、不像临时拼凑的引导式 demo**。

---

## 4. 为什么这是"平台防御性"问题,而非"数据质量"问题 ⭐

**核心论点:Synthesis is the moat(合成才是护城河)。**

- Agency 不会为"数据访问"付 $15K-25K/月 —— 那他们能直接找 Experian/Acxiom 买。
- ReceptivIQ 卖的是 **合成**:心理分群 → 创意 brief;渠道倾向 → 媒介采买;信息匹配 → 文案;归因 → 闭环。这是 10 个 Pillar 做的活,也是没人在单一平台上做的活。

### 单一数据源地基会侵蚀平台价值

1. **输出像数据源本身** —— Mosaic profile 可识别,投资人/竞品一眼看出是 Experian 的。
2. **议价权翻转** —— 供应商知道你换不掉;企业级数据合同 $25K-500K/年,按供应商条款重新定价。
3. **Phase 2 Pillar 继承依赖** —— 创意/文案/媒介/归因/CRM 全都消费 Pillar 1 的 persona,锁死一个供应商的 taxonomy = 锁死全部 10 个 Pillar。

---

## 5. 决策:四源合成栈

| 数据源                     | 角色              | 贡献                                                                                                                                   | 替代的 Experian 能力                               |
| -------------------------- | ----------------- | -------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------- |
| **TransUnion TruAudience** | 🔧 锚(anchor)     | 人口基础 + 渠道倾向 + 身份解析;覆盖 98% 美国成人、1.27 亿家庭、8000 万 connected homes;后 Neustar 整合的身份图含数百属性 + 200+ 数据源 | 身份解析 + 人口画像 + 渠道倾向(替代 TrueTouch)     |
| **Claritas PRIZM Premier** | 心理分群 taxonomy | 68 household segment / 11 Lifestage / 14 Social Group;数据底座含 Epsilon/Valassis/Data Axle/TomTom                                     | Mosaic 心理分群(publisher/DSP 层可互换)            |
| **GWI**                    | 态度/文案信号     | 1.4M+ 年度调研 / 52+ 市场 / 250K+ profiling points;"为什么买"的 attitudinal 信号                                                       | (Experian 无对等)增量能力,驱动 Pillar 3 文案 Agent |
| **LiveRamp**               | 身份解析 + 激活   | RampID 跨源匹配 + 180+ 提供商市场(含 Experian/TransUnion 段);**项目已集成**                                                            | 身份解析 + 激活;并通过市场按段买 Experian          |

> **护城河逻辑**:四家中**没有一家是"承重"的**。合成层成为产品本身,且不被任一供应商的定价/合同绑架。

### Mosaic ↔ PRIZM 可互换性(关键依据)

Rose 在 Session 2 已确认:"即便 Claritas 的 PRIZM 也会拉 Mosaic profile……做 publisher 和 inventory 时,大家都回到 Mosaic 生态。" —— 正因如此,publisher / DSP / 激活伙伴把 PRIZM 与 Mosaic 视为功能等价,**persona 可无损携带**进 StackAdapt / Trade Desk / Basis / Viant / Meta。

---

## 6. Experian 的去向(不抛弃)

Experian 不消失,降级为 enrichment 层,两种 sequencing 都保留:

1. **Phase 2 enrichment 层** —— 地基上线后,在 Experian 深度显著领先的垂直(汽车在库、家庭收入深度、特定金融属性)摄入 Consumer View。**是给可用平台做增强,而非押注单一供应商**。
2. **经 LiveRamp 市场** —— Experian 段可经 LiveRamp 按段、按次付费访问,低承诺地用于特定客户项目,同时评估是否值得 full Consumer View license。

---

## 7. 9 月投资人 demo 对比

**Demo 场景(两案相同)**:策略师打开 Persona Engine,prompt:

> "I'm seeking Nissan Pathfinder buyers in Oregon — 目标:增加三家经销商试驾、捕捉置换意向、再激活未购买的历史访客。"

|                                                     | Experian 单源                     | 四源栈                                               |
| --------------------------------------------------- | --------------------------------- | ---------------------------------------------------- |
| Persona 输出                                        | Mosaic profile,明显 Experian 风味 | PRIZM 同样直观命名的 cluster                         |
| 渠道倾向                                            | Experian TrueTouch                | TransUnion + GWI 媒介习惯叠加(两独立信号互校,更丰富) |
| 信息倾向                                            | 限于 TrueTouch                    | GWI attitudinal 直接驱动(让 Pillar 3 可演示)         |
| 激活                                                | Experian destination network      | LiveRamp 市场,内建跨源身份解析                       |
| 投资人最难问题"这和直接 license Experian 有何区别?" | **最难答**                        | **可答:合成是专有的**                                |

> 四源栈不会产出更薄的 demo,而是**更难被投资人否定**的 demo —— 因为合成可见。

---

## 8. 需要的决策(Sprint 0 解锁项)

| #   | 决策                                         | 需要                                             | 期限            |
| --- | -------------------------------------------- | ------------------------------------------------ | --------------- |
| 1   | 采纳四源栈为 Pillar 1 地基                   | Yes / No / 讨论                                  | Sprint 0 结束前 |
| 2   | 打开 TransUnion 对话                         | 用现有关系要 TruAudience 样本+报价(暂不订阅)     | 2 周内          |
| 3   | 授权 Claritas / GWI / LiveRamp 样本请求      | 仅销售咨询,供应商通常免费给样本                  | 2 周内          |
| 4   | 确认 StackAdapt 合同是否含 LiveRamp 身份解析 | 影响 Pillar 6 归因范围                           | Sprint 0 结束前 |
| 5   | Experian 降到 Phase 2/3                      | 确认不再是 Phase 1 阻塞项;保持 Sunaina 关系      | Sprint 0 结束前 |
| 6   | 确认预算 envelope                            | 各供应商 indicative 报价随 Sprint 0 销售对话汇总 | Sprint 1 review |

> **最怕:停顿(pause)**。每拖一周压缩 9 月 demo 的开发窗口。

---

## 9. 属性覆盖图(四源栈)

| 属性类别                         | TransUnion | Claritas  | GWI       | LiveRamp  |
| -------------------------------- | ---------- | --------- | --------- | --------- |
| 身份 / hashed email / 家庭 ID    | Primary    | —         | —         | Primary   |
| 人口(年龄/性别/收入/家庭构成)    | Primary    | Secondary | —         | —         |
| 地理 + polygon 叠加              | Secondary  | Primary   | —         | —         |
| 金融 / 信用 / 忠诚度             | Primary    | Secondary | —         | —         |
| 心理 / cluster 命名(Mosaic 等价) | —          | Primary   | Secondary | —         |
| 汽车垂直信号                     | Primary    | Secondary | —         | —         |
| 零售 / 购物行为                  | Primary    | —         | —         | Secondary |
| 渠道倾向(Meta/TV/音频/直邮)      | Primary    | —         | Secondary | —         |
| 信息倾向 / 语气接受度            | Secondary  | —         | Primary   | —         |
| 内容互动 / 生活方式触发          | Secondary  | Primary   | —         | —         |
| 垂直 taxonomy(汽车/旅行/金融)    | Primary    | Secondary | —         | —         |
| 竞争 share-of-voice 输入         | Secondary  | —         | Primary   | Secondary |
| 激活目的地矩阵                   | Primary    | —         | —         | Primary   |

> **最薄的两块**:汽车垂直深度、零售购物行为。两者都可在 Phase 2 经 LiveRamp 市场(汽车用 S&P Global Mobility,零售用 NCSolutions / Numerator)或 Experian enrichment 补齐,不影响 Phase 1 地基。

---

## 10. 合规约束(本项目第一前置)

无论用哪几家,接入时都必须(见 [`EXPERIAN-ALTERNATIVES.md`](./EXPERIAN-ALTERNATIVES.md) §0):

1. **七道合规闸门** —— 每家供应商签约前过 G1-G7(来源举证 / DPA / BAA / 用途限定 / DSAR / 抑制兜底 / SOC2)。
2. **入仓前哈希** —— 任何源数据进仓库前 `hash_identifier()`,禁止明文 PII 落仓。
3. **合规抑制必须兜底** —— 四源栈均**不含** Deceased/DNC 抑制,必须配 LexisNexis/AccuData。
4. **审计每次调用** —— 写 `enrichment.<provider>.completed`,失败 5xx 不静默。
5. **DSAR 级联** —— 每个新源接入 `dsar.py` 删除/导出级联清单。

---

## 11. 关联文档

- 替代方案对比:[`EXPERIAN-ALTERNATIVES.md`](./EXPERIAN-ALTERNATIVES.md)
- 端到端数据流:[`END-TO-END-DATA-FLOW.md`](./END-TO-END-DATA-FLOW.md)
- Experian 接口清单:[`EXPERIAN-APIS-TO-CONFIRM.md`](./EXPERIAN-APIS-TO-CONFIRM.md)
- TransUnion 集成:[`TRANSUNION-INTEGRATION.md`](./TRANSUNION-INTEGRATION.md)
- 竞品全景:[`COMPETITIVE-LANDSCAPE.md`](./COMPETITIVE-LANDSCAPE.md)

---

## 来源(已核实链接)

- [Claritas PRIZM Premier](https://claritas.com/prizm-premier/)
- [Claritas MyBestSegments](https://claritas360.claritas.com/mybestsegments/)
- [GWI 官网](https://www.gwi.com/)
- [GWI API](https://www.gwi.com/api)
- [GWI Platform API 文档](https://api.globalwebindex.com/docs/platform-api/getting-started/introduction)
- [TransUnion TruAudience](https://www.transunion.com/solution/truaudience)
- [LiveRamp 文档](https://docs.liveramp.com)
