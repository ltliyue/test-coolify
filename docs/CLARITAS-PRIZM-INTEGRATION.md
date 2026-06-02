# Claritas PRIZM Premier 集成说明

_Last updated: **2026-05-26**_

> **文档类型**:第三方数据供应商集成指南
> **目标读者**:后端工程 / 产品 / 客户技术对接 / 数据合规
> **目的**:说明 Claritas PRIZM Premier 是什么、在 ReceptivIQ 中扮演什么角色、能拿到哪些数据、怎么集成、有哪些坑与合规约束。
> **定位**:PRIZM 是 [Pillar 1 四源合成栈](./PILLAR1-DATA-FOUNDATION-DECISION.md) 中的**心理分群(psychographic clustering)taxonomy**,与 TransUnion(身份/人口)、GWI(态度)、LiveRamp(身份/激活)互补。
> **所有官网链接均在 2026-05 经联网检索核实可访问。**

---

## 目录

1. PRIZM 是什么
2. 在 ReceptivIQ 中的作用
3. 关键概念:68 段 / 11 Lifestage / 14 Social Group
4. 能拿到哪些数据
5. 关键网址
6. 怎么集成(开发视角)
7. 怎么操作(用户视角)
8. 数据交付与刷新
9. 合规约束
10. Adapter 实施计划
11. 常见踩坑

---

## 1. PRIZM 是什么

### 一句话定义

**Claritas PRIZM Premier 是把全美每一户家庭归类到 68 个消费者细分(segment)之一的地理人口 + 心理(geodemographic + psychographic)分群系统** —— 给每户贴一个像"02 = Networked Neighbors"这样的标签,描述其生活方式、媒体消费与购买偏好。

### 它属于哪一类

它**不是身份解析工具,也不是全量属性增强 API**,而是一套**"人群命名 taxonomy"**:

- 不告诉你"张三的邮箱是什么"(那是 TransUnion/LiveRamp 的活)
- 而告诉你"张三这一户属于 02 段,这群人偏好 X 媒体、买 Y 产品"

> 类比:PRIZM 之于人群,就像星座之于性格 —— 一个**可读、可携带、行业通用**的人群标签。

### 与 Experian Mosaic 的关系(关键)

PRIZM 与 **Experian Mosaic 在 publisher / DSP / 激活层功能可互换**(Rose 在 Session 2 已确认)。这意味着:

- 用 PRIZM 生成的 persona,可**无损携带**进 StackAdapt / Trade Desk / Basis / Viant / Meta 等投放平台
- **正因如此,我们用 PRIZM 替代 Mosaic 不损失下游激活能力** —— 这是 Pillar 1 改用四源栈的核心可行性依据

### Claritas 的四套分群体系

| 分群               | 用途                               |
| ------------------ | ---------------------------------- |
| **PRIZM Premier**  | 通用消费者生活方式分群(本文档主角) |
| **P$YCLE Premier** | 金融/财富行为分群                  |
| **ConneXions**     | 技术/媒体采纳分群                  |
| **CultureCode**    | 多元文化/族裔分群                  |

> 都建立在 10,000+ 人口与行为属性、2,500+ Syndicated Audiences 之上;通过 **AudienceAnywhere** 平台对第一方数据做 append 与 lookalike。

---

## 2. 在 ReceptivIQ 中的作用

### 数据流定位

```
processed.contacts_canonical (pii_token + TransUnion 人口数据)
        │
        ▼  ⑥ Enrich 阶段 · 对每户 append PRIZM segment code
   PRIZM segment = "02 Networked Neighbors"
        │
        ├──► ⑦ Persona Agent:用 segment 命名 + 描述构建 ICP
        │     "Networked Neighbors:高收入郊区家庭,数字化程度高……"
        │
        ├──► ⑧ Audience Build:用 segment code 作 SQL 谓词筛人群
        │     WHERE prizm_segment IN ('01','02','03')  -- Elite Suburbs
        │
        └──► ⑫ Activation:segment 可直接映射到 DSP 的 Mosaic/PRIZM 受众
```

### 三处消费

| 阶段                        | PRIZM 的作用                                                            |
| --------------------------- | ----------------------------------------------------------------------- |
| **Persona Agent(Pillar 1)** | segment 的命名 + narrative 直接成为 persona 的"骨架",让画像可读、可解释 |
| **Audience Build**          | 按 segment code 分组 —— 比逐属性筛选更稳定、更可携带                    |
| **Activation**              | segment 与 Mosaic 互换 → persona 可直接落到主流 DSP 的现成受众          |

> **互补关系**:TransUnion 提供"这户是谁 + 人口数据",PRIZM 提供"这户属于哪类人 + 怎么打",GWI 提供"这类人为什么买",LiveRamp 把结果投出去。

---

## 3. 关键概念:68 段 / 11 Lifestage / 14 Social Group

### 三级结构

```
68 个 Segment(最细 · 如 "02 Networked Neighbors")
   │
   ├── 归入 14 个 Social Group(按城市化程度 + 社会经济等级)
   │     如 S1 = Elite Suburbs(精英郊区)
   │
   └── 归入 11 个 Lifestage Group(按年龄 + 社会经济等级 + 是否有孩子)
         如 F1 = (家庭生命阶段分组)
```

### Segment 编码规则

- **Segment code**:01-68,**按社会经济等级排序**(01 最高:收入/教育/职业/房产价值综合最高)
- **每段同时带两个分组标签**:一个 Social Group(S1-S14 等)+ 一个 Lifestage Group(如 F1)
- **示例**:`02 = Networked Neighbors` → Social Group `S1 Elite Suburbs` + Lifestage Group `F1`

### 两种分组维度的差异

| 分组                | 依据                           | 用途                               |
| ------------------- | ------------------------------ | ---------------------------------- |
| **Social Group**    | 城市化程度 + 社会经济等级      | "住在哪、多富" → 媒介/渠道选择     |
| **Lifestage Group** | 年龄 + 社会经济等级 + 有无孩子 | "处于人生哪个阶段" → 产品/信息选择 |

> 一个 persona 可以同时用两个维度描述:"高收入精英郊区(Social)+ 有孩子的成熟家庭(Lifestage)"。

---

## 4. 能拿到哪些数据

| 数据                         | 说明                                   | 数据级别(本项目分级)    |
| ---------------------------- | -------------------------------------- | ----------------------- |
| **PRIZM Segment Code**       | 01-68 的家庭分群编码                   | L1(聚合标签,非 PII)     |
| **Segment Narrative**        | 每段的文字画像(生活方式/媒体/购买偏好) | L0(公开描述)            |
| **Social / Lifestage Group** | 二级分组标签                           | L1                      |
| **Segment 分布数据**         | 某地理区域内各段占比(ZIP+6 / ZIP9 级)  | L0/L1(地理聚合)         |
| **Syndicated Audiences**     | 2,500+ 预制受众(基于 10,000+ 属性)     | L1                      |
| **Append 结果**              | 对客户第一方名单 append 上述标签       | 取决于名单本身(通常 L2) |

> **关键**:PRIZM 输出本身是**聚合分群标签(L0/L1)**,PII 暴露面小;敏感的是"把标签 append 到含 PII 的第一方名单"这一步 —— 那一步遵循本项目入仓哈希规则。

---

## 5. 关键网址(均已实测可打开)

### 5.1 商业 / 产品入口

| 用途                         | 链接                                             |
| ---------------------------- | ------------------------------------------------ |
| PRIZM Premier 产品页         | https://claritas.com/prizm-premier/              |
| Claritas 数据总览            | https://claritas.com/data/                       |
| Claritas 主站                | https://claritas.com/                            |
| MyBestSegments(段落查询工具) | https://claritas360.claritas.com/mybestsegments/ |

### 5.2 段落定义文档(理解 68 段)

| 用途                                       | 链接                                                                                                                                                                                |
| ------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| PRIZM Premier Segment Narratives(2023 PDF) | https://data.sagepub.com/docs/claritas/PRIZM_Premier_Segment_Narratives_2023.pdf                                                                                                    |
| Social Segment Distribution(2024 PDF)      | https://claritas.com/wp-content/uploads/2024/03/PRIZM%C2%AE-Premier-Social-Segment-Distribution-2024.pdf                                                                            |
| ZIP+6 Distributions Release Notes(2024)    | https://claritas360.claritas.com/knowledgecenter/help/content/claritas%20360/news_and_info/2024/adu/claritas%20prizm%20premier%20zip+6%20distributions%20release%20notes%202024.pdf |

### 5.3 开发者 / 技术资源

| 用途                                               | 链接                                              |
| -------------------------------------------------- | ------------------------------------------------- |
| Claritas 360 Knowledge Center                      | https://claritas360.claritas.com/knowledgecenter/ |
| AudienceAnywhere(第一方数据 append/lookalike 平台) | https://claritas.com/ (经销售开通)                |

> ⚠️ Claritas **无完全公开的开发者 API 门户**;技术对接细节(文件 schema、API/SFTP 凭证)经签约后由 Claritas 客户团队提供。

---

## 6. 怎么集成(开发视角)

### 6.1 三种交付方式

| 方式                      | 说明                                                           | 适用                     |
| ------------------------- | -------------------------------------------------------------- | ------------------------ |
| **批量文件交付**(主流)    | Claritas 把 PRIZM 段映射文件(如 ZIP+6 → segment)交付到 S3/SFTP | 地理级分群、初始全量加载 |
| **Append 服务**           | 上传第一方名单,Claritas 回传每条 append 上 segment             | 对客户 CRM 打标          |
| **AudienceAnywhere 平台** | UI / 程序化构建自定义 + lookalike 受众                         | 受众构建                 |

> 与 TransUnion 类似:**大批量文件交付优于实时 API 调用**,适合做初始数据加载与定期刷新。

### 6.2 集成模式(推荐:地理映射 + append)

```
方案 A · 地理映射(无 PII,合规最轻)
  Claritas ZIP+6 → segment 映射文件  (批量下载)
        │
        ▼  入库 reference 表 prizm_zip_segment(zip6, segment_code)
  对每条 contact 的地址 → 取 zip6 → JOIN 得 segment
        │
        ▼  写入 processed.contacts_canonical.prizm_segment

方案 B · 名单 append(更精确,走 append 服务)
  上传 hashed 第一方名单 → Claritas append → 回传 segment
        │
        ▼  按 record_id 回写 canonical
```

> **MVP 建议走方案 A** —— 不外传 PII,只用地址→ZIP+6→segment 的本地 JOIN,合规风险最低。

### 6.3 BaseAdapter 落地

遵循项目 ETL Adapter Pattern(见 `CLAUDE.md`):

- 新增 `backend/app/services/etl/adapters/claritas.py`
- `platform = "claritas_prizm"`
- `fetch()` → 拉取/读取批量 segment 映射文件
- `transform()` → 输出 `{record_id, prizm_segment, social_group, lifestage_group}`,**不含原始 PII**
- 新增 raw 表 `raw_claritas_prizm`(仅 zip6/segment 等聚合字段)入 `_ALLOWED_TABLES`
- segment narrative 作为**静态 reference 表**(68 行)随 seed 入库,供 Persona Agent 解码

### 6.4 Segment 解码表(随项目内置)

把 68 段的 `code → name → narrative` 做成静态 reference(类似 `field_mappings` 的枚举解码),Persona Agent 直接查表把 `02` 翻译成 "Networked Neighbors + narrative"。

---

## 7. 怎么操作(用户视角)

| 角色              | 操作                                                                                            |
| ----------------- | ----------------------------------------------------------------------------------------------- |
| **Agency 管理员** | 在 Integrations 页连接 Claritas(填入 Claritas 提供的 SFTP/API 凭证,Fernet 加密存 `credentials`) |
| **策略师**        | 在 Persona Engine prompt 中无需感知 PRIZM —— 系统自动用 segment 丰富画像                        |
| **数据团队**      | 定期(季度)触发 segment 映射文件刷新同步                                                         |

---

## 8. 数据交付与刷新

| 维度         | 说明                                                                |
| ------------ | ------------------------------------------------------------------- |
| **刷新频率** | 通常年度大版本 + 期间增量(ZIP+6 分布按年发布)                       |
| **数据级别** | ZIP+6 / ZIP9 / 地理普查级 / 家庭级(append)                          |
| **交付通道** | S3 / SFTP 批量;append 服务                                          |
| **版本管理** | segment taxonomy 跨年可能微调,需记录版本(如 2024 vs 2023 narrative) |

---

## 9. 合规约束

> 遵循 [`EXPERIAN-ALTERNATIVES.md` §0 七道合规闸门](./EXPERIAN-ALTERNATIVES.md) + 本项目入仓规则。

1. **合规初判 🟢 较强** —— PRIZM 输出是聚合分群标签,本身 PII 暴露面小(优于个体级数据源)。
2. **方案 A(地理映射)零 PII 外传** —— 优先采用,只在本地做 ZIP+6→segment 的 JOIN。
3. **方案 B(名单 append)须哈希** —— 上传第一方名单前 `hash_identifier()`,禁止明文外传与落仓。
4. **G6 抑制不覆盖** —— PRIZM **不做** Deceased/DNC 抑制,必须由 LexisNexis/AccuData 兜底。
5. **审计** —— append 调用写 `enrichment.claritas_prizm.completed`(record 数、版本),失败 5xx 不静默。
6. **DSAR 级联** —— append 结果(segment 标签)在 DSAR 删除时随第一方记录一并清除;地理映射表无 PII,无需删除。
7. **数据来源存证** —— Claritas DPA / 合规证明存档,关联 `data_source_attestation`。
8. **用途限定** —— 合同写明仅营销用途(虽 PRIZM 非信贷数据,仍按统一标准约束)。

---

## 10. Adapter 实施计划

| 状态         | 说明                                                       |
| ------------ | ---------------------------------------------------------- |
| **当前**     | ❌ 未实现(P1 · Pillar 1 四源栈成员,随 TransUnion 一起接入) |
| **前置**     | 商业合同 + Claritas 提供 segment 映射文件/凭证 + 样本文件  |
| **MVP 范围** | 方案 A 地理映射 + 68 段解码表 + Persona Agent 接入         |
| **后续**     | 方案 B 名单 append + AudienceAnywhere lookalike            |

### 待新增

- `backend/app/services/etl/adapters/claritas.py`
- raw 表 `raw_claritas_prizm`(加入 `_ALLOWED_TABLES` + `_init_duckdb_schema()`)
- reference 表 `prizm_segment_definitions`(68 行 seed)+ `prizm_zip_segment`(地理映射)
- `processed.contacts_canonical` 增列 `prizm_segment / social_group / lifestage_group`
- dbt staging:`stg_claritas_prizm.sql` + sources.yml 条目

---

## 11. 常见踩坑

1. **以为 PRIZM 是身份解析** —— 它不给个体身份,只给分群标签;身份要靠 TransUnion/LiveRamp。
2. **以为 PRIZM 有实时查询 API** —— 主流是批量文件交付,无完全公开 REST API;实时 append 需走专门服务。
3. **segment 版本漂移** —— 跨年 taxonomy 可能微调,persona 解码表要绑定数据版本,否则 narrative 对不上。
4. **把 segment 当 PII** —— segment 是聚合标签(L0/L1),但 append 到 PII 名单后整体升级为该名单的级别。
5. **忘了抑制兜底** —— PRIZM 不含 Deceased/DNC,投放前仍须过 LexisNexis 抑制。
6. **PII 外传风险** —— 用 append 服务前确认走哈希;能用方案 A 地理映射就不外传明文。

---

## 12. 关联文档

- Pillar 1 数据地基决策:[`PILLAR1-DATA-FOUNDATION-DECISION.md`](./PILLAR1-DATA-FOUNDATION-DECISION.md)
- 替代方案对比:[`EXPERIAN-ALTERNATIVES.md`](./EXPERIAN-ALTERNATIVES.md)
- TransUnion 集成:[`TRANSUNION-INTEGRATION.md`](./TRANSUNION-INTEGRATION.md)
- 端到端数据流:[`END-TO-END-DATA-FLOW.md`](./END-TO-END-DATA-FLOW.md)

---

## 来源(已核实链接)

- [Claritas PRIZM Premier 产品页](https://claritas.com/prizm-premier/)
- [Claritas 数据总览](https://claritas.com/data/)
- [Claritas MyBestSegments](https://claritas360.claritas.com/mybestsegments/)
- [PRIZM Premier Segment Narratives 2023 (PDF)](https://data.sagepub.com/docs/claritas/PRIZM_Premier_Segment_Narratives_2023.pdf)
- [PRIZM Premier Social Segment Distribution 2024 (PDF)](https://claritas.com/wp-content/uploads/2024/03/PRIZM%C2%AE-Premier-Social-Segment-Distribution-2024.pdf)
- [Claritas PRIZM — Wikipedia](https://en.wikipedia.org/wiki/Claritas_Prizm)
- [Claritas PRIZM Premier — PolicyMap](https://www.policymap.com/data/sources/claritas-prizm-premier)
