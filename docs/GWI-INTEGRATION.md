# GWI(GlobalWebIndex)集成说明

_Last updated: **2026-05-26**_

> **文档类型**:第三方数据供应商集成指南
> **目标读者**:后端工程 / 产品 / 客户技术对接 / 数据合规
> **目的**:说明 GWI 是什么、在 ReceptivIQ 中扮演什么角色、能拿到哪些数据、怎么集成、有哪些坑与合规约束。
> **定位**:GWI 是 [Pillar 1 四源合成栈](./PILLAR1-DATA-FOUNDATION-DECISION.md) 中的**态度 / 信息倾向(attitudinal & messaging)信号层**,与 TransUnion(身份/人口)、Claritas PRIZM(心理分群)、LiveRamp(身份/激活)互补。
> **所有官网链接均在 2026-05 经联网检索核实可访问。**

---

## 目录

1. GWI 是什么
2. 在 ReceptivIQ 中的作用
3. 关键概念:调研型数据 vs 确定性数据
4. 能拿到哪些数据
5. 关键网址
6. 怎么集成(开发视角)
7. 怎么操作(用户视角)
8. API 配额与限制
9. 合规约束
10. Adapter 实施计划
11. 常见踩坑

---

## 1. GWI 是什么

### 一句话定义

**GWI 是一家全球消费者调研(survey-based)数据公司** —— 通过持续的大规模问卷,刻画消费者的**态度、价值观、兴趣、媒体习惯、品牌好感**,回答的是"消费者**为什么**这样做",而非"这个人是谁"。

### 它属于哪一类

GWI **不是身份解析,也不是确定性的人口/交易数据库**,而是**"态度信号源"**:

- 不告诉你"张三住哪、收入多少"(那是 TransUnion 的活)
- 而告诉你"像张三这类人,对环保信息接受度高、偏好短视频、信任 KOL 推荐"

> 类比:TransUnion/Claritas 告诉你"客户是谁、属于哪类人",GWI 告诉你"该用什么话术、在哪个渠道、打什么情感点才打得动他"。

### 规模

- **约 1.4M-2M 年度调研受访者**,跨 **52+ 市场**
- **250K+ profiling points / 40 亿+ 唯一数据点**
- 覆盖兴趣、行为、人口、媒体习惯

---

## 2. 在 ReceptivIQ 中的作用

### 数据流定位

```
TransUnion 人口 + Claritas PRIZM segment(确定性"是谁/哪类人")
        │
        ▼  ⑥ Enrich · 用 segment/人口特征匹配 GWI 态度画像
   GWI attitudinal overlay
   "这类人:环保驱动 · 信任评测 · 偏好 Instagram/TikTok · 对价格敏感度中"
        │
        ├──► ⑦ Persona Agent:补全 persona 的"动机/价值观"维度
        │
        ├──► ⑩ Creative Agent:态度信号直接驱动文案语气与情感点
        │     (这是让 Pillar 3 文案 Agent 在 Phase 1 就能演示的关键)
        │
        └──► ⑪ Media Agent:媒体习惯信号指导渠道预算分配
```

### 三处消费 —— GWI 是"为什么 + 怎么说"的层

| 阶段                         | GWI 的作用                                                                                                |
| ---------------------------- | --------------------------------------------------------------------------------------------------------- |
| **Persona Agent(Pillar 1)**  | 补全"动机 / 价值观 / 态度",让 persona 从"人口骨架"变成"有血有肉的人"                                      |
| **Creative Agent(Pillar 3)** | 信息接受度 / 语气偏好直接驱动文案 —— **GWI 是让 Adaptive Voice Writer 在 Phase 1 可演示而非画饼的那一层** |
| **Media Agent**              | 媒体习惯(用哪些平台、何时活跃)指导渠道选择与预算                                                          |

> **四源互补**:TransUnion = 是谁 + 人口;Claritas = 哪类人(分群);**GWI = 为什么买 + 怎么说**;LiveRamp = 投出去。

---

## 3. 关键概念:调研型数据 vs 确定性数据

| 维度           | GWI(调研型)                                      | TransUnion/Claritas(确定性/建模) |
| -------------- | ------------------------------------------------ | -------------------------------- |
| **来源**       | 大规模问卷自报                                   | 信贷/交易/公开记录/地理建模      |
| **回答的问题** | 为什么 / 态度 / 偏好                             | 是谁 / 在哪 / 买过什么           |
| **粒度**       | **人群级 / 画像级**(非个体级)                    | 个体级 / 家庭级 / 地理级         |
| **用法**       | 给 persona/segment **叠加态度层**;指导文案与渠道 | 锁定具体人群、做名单             |
| **不能做**     | 不能定位"具体某个人"                             | 不擅长"为什么"的深层动机         |

> ⚠️ **核心认知**:GWI 是**人群级态度画像**,不是个体级数据库。它的价值是"给已锁定的人群配上正确的沟通策略",而不是"找到具体的人"。这也决定了它的 PII 风险天然较低。

---

## 4. 能拿到哪些数据

| 数据                          | 说明                           | 数据级别(本项目分级) |
| ----------------------------- | ------------------------------ | -------------------- |
| **态度 / 价值观**             | 环保意识、品牌忠诚、风险偏好等 | L0/L1(人群级聚合)    |
| **兴趣 / 行为**               | 爱好、活动、生活方式           | L0/L1                |
| **媒体习惯**                  | 平台使用、消费时段、设备       | L0/L1                |
| **品牌好感 / share-of-voice** | 对品牌/品类的认知与偏好        | L0/L1                |
| **信息接受度**                | 对不同信息类型/语气的响应倾向  | L0/L1                |
| **Synthetic Audiences**       | 基于真实调研的合成受众         | L1                   |

> **关键**:GWI 输出是**人群级聚合洞察(L0/L1)**,不含个体 PII —— 合规风险显著低于确定性个体数据源。

---

## 5. 关键网址(均已实测可打开)

### 5.1 商业 / 产品入口

| 用途                    | 链接                             |
| ----------------------- | -------------------------------- |
| GWI 主站                | https://www.gwi.com/             |
| 平台总览                | https://www.gwi.com/platform     |
| 数据总览                | https://www.gwi.com/data         |
| Integrations / API 入口 | https://www.gwi.com/integrations |
| GWI Core(报告/趋势)     | https://www.gwi.com/core         |

### 5.2 开发者 / 技术资源(GWI 有公开 API + MCP)⭐

| 用途                                     | 链接                                                                               |
| ---------------------------------------- | ---------------------------------------------------------------------------------- |
| API 产品页                               | https://www.gwi.com/api                                                            |
| Platform API 入门                        | https://api.globalwebindex.com/docs/platform-api/getting-started/introduction      |
| Spark MCP 集成指南                       | https://api.globalwebindex.com/docs/spark-mcp/integration-guide/overview           |
| Integration products / APIs(Help Center) | https://help.globalwebindex.com/en/articles/10725820-integration-products-and-apis |
| Respondent Level Data                    | https://www.gwi.com/respondent-level-data                                          |

> ✅ 与多数全栈数据厂商不同,**GWI 提供公开文档化的 Platform API + MCP 连接器**(可直连 Claude / ChatGPT / Copilot),工程友好度高。

---

## 6. 怎么集成(开发视角)

### 6.1 两条技术路径

| 路径                         | 说明                                                                            | 适用                                             |
| ---------------------------- | ------------------------------------------------------------------------------- | ------------------------------------------------ |
| **Platform API**(结构化查询) | 参数化访问 markets / waves / demographics,全面支持 Core + add-on + 自定义数据集 | 程序化拉取态度画像,入仓                          |
| **Spark MCP / Agent Spark**  | MCP 连接器,让 AI Agent(Claude 等)实时查询 GWI 洞察                              | **直接给 Persona/Creative Agent 做实时洞察增强** |

> 💡 **MCP 路径对本项目尤其有价值**:我们的 AI Agent 架构(brain.py)本就基于 LLM,GWI 的 MCP 连接器可让 Agent **在生成 persona/文案时实时拉 GWI 态度数据**,而非预先 ETL 落仓。

### 6.2 认证方式

- **Platform API** —— Spark API token(签约后获取)
- **MCP 连接器** —— OAuth 2.0(GWI 账号凭证)或 Spark API token

> 凭证经 Fernet 加密存 `credentials.encrypted_data`,禁止明文出现在日志/Sentry。

### 6.3 集成模式(推荐:画像级 overlay,非个体增强)

```
GWI 不是"对每条 contact 增强",而是"对 persona/segment 叠加态度层"

  Persona Agent 生成 ICP 骨架(TransUnion + Claritas)
        │
        ▼  按 segment/人口特征查询 GWI(Platform API 或 MCP)
  GWI 返回该人群的态度/媒体/信息倾向画像
        │
        ▼  写入 personas.psychographics / channel_preferences
        ▼  Creative Agent 读取 → 驱动文案语气
```

> **关键设计**:GWI 是**人群级**数据,所以集成点是 **persona/segment 层**,不是逐条 contact 层。这避免了对每个用户调用 API,也天然规避个体 PII。

### 6.4 BaseAdapter 落地

遵循项目 ETL Adapter Pattern(见 `CLAUDE.md`):

- 新增 `backend/app/services/etl/adapters/gwi.py`
- `platform = "gwi"`
- `fetch()` → 按 persona 的 segment/人口特征查询 GWI Platform API
- `transform()` → 输出 `{persona_id, attitudes, media_habits, messaging_propensity}`,**人群级聚合,无 PII**
- raw 表 `raw_gwi_insights`(人群级洞察)入 `_ALLOWED_TABLES`
- **可选**:配置 GWI MCP 连接器给 `brain.py`,让 Agent 实时查询

---

## 7. 怎么操作(用户视角)

| 角色              | 操作                                                                                        |
| ----------------- | ------------------------------------------------------------------------------------------- |
| **Agency 管理员** | 在 Integrations 页连接 GWI(填入 Spark API token / OAuth,Fernet 加密存储)                    |
| **策略师**        | 在 Persona Engine 中无需感知 GWI —— 系统自动为 persona 叠加态度层;Creative 文案自动带情感点 |
| **数据团队**      | 配置 GWI MCP 连接器,使 AI Agent 可实时查询(可选高级用法)                                    |

---

## 8. API 配额与限制

| 维度           | 说明                                                              |
| -------------- | ----------------------------------------------------------------- |
| **认证**       | Spark API token / OAuth 2.0                                       |
| **数据级别**   | 人群级 / 画像级(非个体)                                           |
| **配额**       | 按合同分级(Pro / 企业);具体以签约为准                             |
| **数据新鲜度** | always-on 调研,持续更新;按 wave 发布                              |
| **MCP**        | Agent Spark MCP 对符合条件的 Pro 用户开放(ChatGPT/Claude/Copilot) |

---

## 9. 合规约束

> 遵循 [`EXPERIAN-ALTERNATIVES.md` §0 七道合规闸门](./EXPERIAN-ALTERNATIVES.md) + 本项目入仓规则。

1. **合规初判 🟢 较强** —— GWI 是**人群级调研聚合数据**,不含个体 PII,暴露面在四源中最低。
2. **集成在 persona/segment 层** —— 不对个体 contact 调用,天然规避个体数据外传。
3. **G6 抑制不覆盖** —— GWI **不做** Deceased/DNC 抑制,必须由 LexisNexis/AccuData 兜底。
4. **审计** —— 查询写 `enrichment.gwi.completed`(persona_id、wave 版本),失败 5xx 不静默。
5. **凭据加密** —— Spark token / OAuth 凭证 Fernet 加密;禁止明文落日志/Sentry。
6. **MCP 数据出口管控** —— 若启用 MCP 让 Agent 实时查询,确保不把客户 PII 传入 GWI prompt;只传 segment/人口特征。
7. **数据来源存证** —— GWI DPA / 合规证明存档,关联 `data_source_attestation`。
8. **用途限定** —— 合同写明仅营销用途。

---

## 10. Adapter 实施计划

| 状态         | 说明                                                             |
| ------------ | ---------------------------------------------------------------- |
| **当前**     | ❌ 未实现(P1 · Pillar 1 四源栈成员)                              |
| **前置**     | 商业合同 + Spark API token / OAuth 凭证                          |
| **MVP 范围** | Platform API 拉取人群态度画像 → 写入 persona;Creative Agent 接入 |
| **后续**     | GWI MCP 连接器接入 `brain.py`,Agent 实时洞察查询                 |

### 待新增

- `backend/app/services/etl/adapters/gwi.py`
- raw 表 `raw_gwi_insights`(加入 `_ALLOWED_TABLES` + `_init_duckdb_schema()`)
- `personas.psychographics / channel_preferences` 接入 GWI 输出
- dbt staging:`stg_gwi.sql` + sources.yml 条目
- (可选)`brain.py` 配置 GWI MCP 连接器

---

## 11. 常见踩坑

1. **以为 GWI 是个体数据源** —— 它是**人群级调研**,不能定位具体某个人;集成点在 persona/segment 层,不是 contact 层。
2. **逐条 contact 调 GWI** —— 错误用法,会浪费配额且无意义;应按人群特征查询一次,overlay 到整个 segment。
3. **把调研数据当确定性事实** —— GWI 是自报态度信号,需与 TransUnion/Claritas 的确定性数据**互补**,不能单独锁定人群。
4. **MCP 误传 PII** —— 启用 MCP 让 Agent 查询时,只传 segment/人口特征,**严禁把客户 PII 放进 prompt**。
5. **忘了抑制兜底** —— GWI 不含 Deceased/DNC,投放前仍须过 LexisNexis 抑制。
6. **wave 版本漂移** —— GWI 按 wave 更新,记录数据版本以便复现 persona。

---

## 12. 关联文档

- Pillar 1 数据地基决策:[`PILLAR1-DATA-FOUNDATION-DECISION.md`](./PILLAR1-DATA-FOUNDATION-DECISION.md)
- 四源合成栈架构:[`PILLAR1-FOUR-SOURCE-STACK.md`](./PILLAR1-FOUR-SOURCE-STACK.md)
- 替代方案对比:[`EXPERIAN-ALTERNATIVES.md`](./EXPERIAN-ALTERNATIVES.md)
- Claritas PRIZM 集成:[`CLARITAS-PRIZM-INTEGRATION.md`](./CLARITAS-PRIZM-INTEGRATION.md)
- TransUnion 集成:[`TRANSUNION-INTEGRATION.md`](./TRANSUNION-INTEGRATION.md)
- 端到端数据流:[`END-TO-END-DATA-FLOW.md`](./END-TO-END-DATA-FLOW.md)

---

## 来源(已核实链接)

- [GWI 主站](https://www.gwi.com/)
- [GWI Platform](https://www.gwi.com/platform)
- [GWI Data](https://www.gwi.com/data)
- [GWI API](https://www.gwi.com/api)
- [GWI Integrations](https://www.gwi.com/integrations)
- [GWI Platform API 入门](https://api.globalwebindex.com/docs/platform-api/getting-started/introduction)
- [GWI Spark MCP 集成指南](https://api.globalwebindex.com/docs/spark-mcp/integration-guide/overview)
- [GWI Help Center — Integration products and APIs](https://help.globalwebindex.com/en/articles/10725820-integration-products-and-apis)
