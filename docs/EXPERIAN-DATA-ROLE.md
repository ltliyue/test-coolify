# Experian 数据在 ReceptivIQ 平台中的作用

> 适用读者：产品 · 业务 · 投资人 · 非技术 stakeholder
> 关联：[ELT-8-STEP-DESIGN](./ELT-8-STEP-DESIGN.md) · [Technical Solution §3.5 + §7](./psd/technical-solution.md) · [PII-DESIGN-SOLUTION](./PII-DESIGN-SOLUTION.md)
> 一句话总结：**Experian Combined API 给平台提供"受众身份证 + 画像档案 + 地址户口"——是连接我们 14 个数据源的"红线"，也是让 AI 真懂消费者的"知识库"。**

---

## 1. Experian 是什么？

Experian 是全球最大的消费者数据公司之一（与 Equifax、TransUnion 并列美国三大）。它有两条主营业务：

| 业务线                                       | 我们**会用**吗                        |
| -------------------------------------------- | ------------------------------------- |
| 🏦 **信用业务**（FICO 信用分 / 信用报告）    | ❌ 不用 —— 受 FCRA 严管，不能用于营销 |
| 🎯 **营销数据业务**（消费者画像 / 受众定向） | ✅ **正是我们要的**                   |

我们用的是它的 **Combined API**（也叫 "Combined Service" / "UE-OV API"）——这是 Experian 营销数据线的核心接口。

---

## 2. 用一个比喻理解

想象 Experian 像一个**消费者档案馆**：

- 收集了美国 3 亿 + 消费者的画像（**合法**、**聚合**、**经过同意**）
- 每个人有个稳定的"图书馆编号"（individual ID）
- 每条记录上贴满标签：年龄段 · 收入档 · 兴趣偏好 · 生活阶段 · 70+ 种 "Mosaic 生活方式段"

**Combined API 就像一个"查档接口"**：

> 你给我一个人的姓名/邮箱/电话/地址，我给你三件东西：
>
> 1. **干净的地址**（把脏的格式洗成标准）
> 2. **三个稳定编号**（这个人 / 这个家庭 / 这个地址在我档案里的编号）
> 3. **你点名要的画像标签**（哪些消费段、哪些行为偏好）

---

## 3. 这个接口返回什么数据？

每次调用返回 **4 类信息**：

### 3.1 ① Hygiene · 干净地址（地址清洗）

把脏的地址洗成 USPS 标准格式。

**举例**：

- 输入："123 s main st apt22, costa mesa CA"
- 输出：
  - 标准化：`123 S Main St, Apt 22, Costa Mesa, CA 92626-2626`
  - 街名 / 街号 / 单元号 拆字段
  - ZIP+4 补全
  - Carrier Route（邮政投递路由）

**为什么需要**：客户上传的 CRM、Tresorit 文件里地址都是手填的（千奇百怪的写法）。不洗就入仓 = 同一个地址被当成 5 条不同记录。

### 3.2 ② Pinning · 身份编号（OmniView 身份解析）

给输入对象打**三个稳定编号**：

| 编号            | 含义                                              | 实际用途                                          |
| --------------- | ------------------------------------------------- | ------------------------------------------------- |
| `individual_id` | **这个人是谁**（在 Experian 数据宇宙里的唯一 ID） | 跨设备 / 跨平台 / 跨源 把同一个人识别出来         |
| `household_id`  | **这个家庭是哪个**                                | 同一户 mobile click + desktop conversion 算同一人 |
| `address_id`    | **这个地址是哪个**                                | 同一地址不同家庭成员可关联                        |

**为什么这是最有价值的一类**——见下面 §4 "Identity Resolution" 章节。

### 3.3 ③ Universal Enrichment · 画像标签（按需点选）

我们告诉 Experian "请给我这个人的：年龄段、收入档、Mosaic 段、TrueTouch 偏好"，它就返回这些字段的具体取值。

**举例**：

- 输入："Dana Smith, 92626"
- 输出：
  - 年龄段：`35-44`
  - 收入档：`$100k-150k`
  - Mosaic 段：`A03 高净值千禧家庭`
  - 生活阶段：`已婚 + 学龄儿童`
  - TrueTouch 偏好：`Email 高响应 · SMS 中响应 · Direct Mail 低响应`
  - 兴趣标签：`户外运动 · 旅行 · 健康`

### 3.4 ④ Data Lookup · segment 命中检查

给一个 segment 编号列表（比如 "高价值用户 · 教育消费决策者 · 健康关注群体"），快速返回"这个人**命中了哪些**"。

**举例**：

- 输入：检查这个人是否命中 segment `12345` 和 `45789`
- 输出：`{"12345": "Y", "45789": {}}` ← 12345 命中，45789 未命中

**为什么需要**：投放前快速筛选受众；不需要展开所有属性。

---

## 4. 在平台里它流向哪里？

```
                            ┌─────────────────────────────┐
                            │   Experian Combined API     │
                            │   /ue-ov（4 类数据）         │
                            └──────────────┬──────────────┘
                                           │
                          经 PII Access Service 受控调用
                                           │
                                           ▼
                            ┌─────────────────────────────┐
                            │   Agency Processed Lake     │
                            │   (4 张 experian_* 表)       │
                            └──────────────┬──────────────┘
                                           │
            ┌──────┬──────┬──────┬─────────┴─────────┬──────┬──────┬──────┐
            ▼      ▼      ▼      ▼                   ▼      ▼      ▼      ▼
         Persona Creative Attrib. Media          Audience Identity DSAR  Reports
         Agent  Agent   Agent  Buying           Export   解析     合规   分析
                                                                  审计
```

**关键点**：Experian 数据**不是**给某一个模块用的，而是**整个平台的横切型基础数据**——8-10 个模块都会消费它。

---

## 5. 4 个 AI Agent 怎么用

### 5.1 Persona Agent · 受众画像

| 没有 Experian       | 有 Experian                                                                            |
| ------------------- | -------------------------------------------------------------------------------------- |
| "30 岁女性，住加州" | "32 岁，年收入 $120k，suburb 房主，Mosaic A03 段，2 个学龄儿童，偏好 Email + 户外品牌" |
| 画像粗糙            | 画像精准——可直接喂给 Creative Agent 生成定向创意                                       |

### 5.2 Creative Agent · 创意生成

读了 persona 的 TrueTouch 偏好后：

- 知道这个 segment **偏好 Email > SMS**（沟通渠道）
- 知道偏好 **情感诉求 > 价格诉求**（创意风格）
- 知道偏好 **早晨 8-10 点** 投放（时段）

→ 生成的创意 brief 直接带这些参数，**A/B 命中率显著提升**。

### 5.3 Attribution Agent · 归因分析

**跨设备归因的痛点**：用户在手机上看到 Meta 广告 → 周末在家用电脑下单。这两个 event 在 Meta / GA4 里**看起来是两个人**，归因丢失。

**Experian household_id 解决**：两个 event 都映射到同一 `household_id` → Attribution Agent 知道是同一家庭 → 归因正确。

**分群 ROAS**：按 Mosaic segment 拆开看，"高净值千禧" 段 ROAS 是 4.2x，"价格敏感" 段是 1.1x → 调整预算分配。

### 5.4 Media Agent · 媒介采买

- 把 Persona Agent 输出的 Experian segment 直接映射到 Meta CA / DV360 / TikTok 的定向参数
- 出价时按 segment 价值差异化（高价值 segment 出更高 CPM）

---

## 6. 它给项目带来的 5 大核心价值

### 价值 1 · 让 AI 真的"懂"消费者

平台 1st-party 数据（Meta 互动 / GA4 行为 / HubSpot 字段）信息量有限——加上 Experian 1000+ 维度第三方画像，AI Agent 的输出质量上一个台阶。

**类比**：没 Experian 就像让 AI "看着身份证写传记"；有 Experian 就像给了它"百度百科 + 朋友圈 + 履历"。

### 价值 2 · 跨源身份解析的"红线"

平台有 14 个数据源（Meta / GA4 / HubSpot / DV360 / TikTok / ...），每个源的用户 ID **互不相通**。Experian 的 `individual_id` 是把它们**串起来的红线**：

```
Meta cookie ABC123  ──┐
GA4 client_id XYZ789 ─┼─→ Experian individual_id = I7891 ←━━ 同一个人
HubSpot contact #42  ─┘
```

**没有 individual_id**：跨源数据无法聚合 → "客户旅程视图" 是空中楼阁
**有 individual_id**：每个客户的完整旅程一目了然

### 价值 3 · 地址 / 数据质量基础设施

14 个数据源里的地址、姓名、电话写法千奇百怪 → Experian Hygiene 标准化后**所有源说同一种语言** → 跨源去重 / 实体解析才能成立。

### 价值 4 · 合规执行的"放大镜"

| 合规场景                                    | Experian 起的作用                                          |
| ------------------------------------------- | ---------------------------------------------------------- |
| **DSAR 删除请求**（用户说"删除我所有数据"） | 用 individual_id 跨所有 14 个源**一次性锁定**该主体 record |
| **HIPAA 客户的纯哈希工作流**                | Experian 支持 SHA-256 哈希输入 → 明文 PII 不出域           |
| **CCPA Opt-Out 追踪**                       | individual_id 维护 do_not_sell 标志 → 跨源一致             |
| **SOC 2 审计**                              | 每次调用有 transaction_id → 完整审计追溯                   |

### 价值 5 · 给 Agency 的差异化卖点

**Experian license 直采贵**（年费 8 万-20 万美金），单家小 Agency 用不起。平台代采 + 按调用计费分账 → **小 Agency 也用得起 Experian 数据**——这是平台对 Agency 的核心吸引力之一。

---

## 7. 对项目开发的关键依赖（简化版）

**最重要的依赖关系**：Experian Combined API 集成必须**先于** Persona / Audience Export / Attribution 模块。

**理由**：这三个模块都依赖 `individual_id` 做跨源关联。如果先做这三个模块再回头集成 Experian，需要**大规模回填 individual_id**——返工成本高。

**开发顺序建议**：

```
Phase 1（基础）        Phase 2（集成）              Phase 3+（业务模块）
───────────           ────────────                ──────────────────
Landing Lake     →    PII Access Service     →    Persona Agent
record_id              + experian_enrich_list      Audience Export
pii_token              operation                   Attribution Agent
audit_events                                       Creative Agent
                                                   Media Agent
```

**关键 P0 任务**：

1. ✅ **Experian sandbox 账号 + insertpartyid + OAuth 凭证**（合同 / 商务负责）
2. ✅ **erich code 字典**（Experian 提供的属性代码表，1000+ 条）
3. ✅ **PII Access Service 的 `experian_enrich_list` operation**（工程负责）
4. ✅ **Processed Lake 里 4 张 experian\_\* 表 schema**（工程负责）
5. ✅ **dbt canonical `dim_person` 模型**（用 individual_id 作主键）

---

## 8. 安全 & 合规

**问：把客户邮箱送给 Experian 安全吗？**

**答**：**安全 + 合规**——3 层保护：

1. **不走业务后端**——明文邮箱**只在 PII Access Service 内存中**短暂存在（≤ 15 分钟 token 过期）
2. **可选纯哈希路径**——HIPAA 客户走 SHA-256 哈希调用，明文从不出域
3. **TLS 1.3 + Audit 全程**——每次调用记 transaction_id，可逐次回放

**问：Experian 会拿我们的数据做什么吗？**

**答**：合同明确——**仅用于本次 enrichment 请求**，不会被 Experian 用于训练模型、转售或其他用途。这是 Experian 营销 API 的标准合同条款（MLA + DPA）。

**问：欧盟 GDPR 客户能用吗？**

**答**：当前接口是 **US 数据**（`sandbox-us-api.experian.com`）—— 主要用于美国市场客户。欧盟客户需走 Experian UK / EMEA endpoint（合同另谈），不是同一个 API。

**问：信用数据会出现吗？**

**答**：**不会**——这是 Experian **Marketing Services** API，**不含**信用分、信用报告、信用历史等 FCRA 监管数据。MLA 中明确限定产品范围。

---

## 9. 成本概览

| 项                                   | 量级                                     |
| ------------------------------------ | ---------------------------------------- |
| 平台年度 master license              | $80k - $200k（按产品组合 + 客户数 tier） |
| 单次 API 调用成本                    | ~$0.01 - $0.05 / 匹配（量大有折扣）      |
| Bulk 文件月度更新（Mosaic taxonomy） | 含在 license 内                          |

**成本控制机制**：

- 每个 Agency 月度 quota（超额需 Admin 审批）
- per-Agency 实时计费仪表盘
- 自动告警阈值（>80% quota 邮件预警）

---

## 10. 常见问题 FAQ

**Q1**：我们可以选择不用 Experian 吗？

A：技术上可以——平台仍可运行，但 Persona/Creative/Attribution Agent 质量明显下降，跨源身份解析靠 hashed email match 命中率仅 ~50%。**强烈建议作为 MVP 标配**。

**Q2**：Experian 和 LiveRamp 重叠吗？

A：有部分重叠（都做身份解析），但定位不同：

- **Experian**：受众**画像数据** + identity（核心是画像）
- **LiveRamp**：身份解析 + cross-device（核心是身份）

平台**同时用两者**——LiveRamp 做高精度跨设备/跨平台 identity，Experian 做丰富画像。

**Q3**：什么时候开始集成？

A：建议 Phase 2（Extract + Classify + Load 阶段，第 4-6 周）就启动——作为 Persona/Audience 模块的前置依赖。合同谈判需提前 30-60 天与 Experian 销售沟通。

**Q4**：Sandbox 和 Production 一样吗？

A：接口签名一样，但 Sandbox 数据是模拟/测试数据（数量少 / 不真实）。开发期用 Sandbox 跑通流程，上线前切换 host 到 Production 即可。

**Q5**：如果 Experian 接口挂了，平台会怎样？

A：实施**降级策略**：

- Persona Agent 退回基于 1st-party 数据生成 persona（画像粗糙但可用）
- Audience Export 用 hashed email match（命中率降低但可用）
- Attribution Agent 退回单设备归因
- 接口恢复后**自动回填** experian 字段

---

## 11. 一图回顾

```
                        ┌──────────────────────┐
                        │    我们的客户          │
                        │  （Agency / Brand）   │
                        └──────────┬───────────┘
                                   │ 上传客户名单
                                   ▼
              ┌───────────────────────────────────────┐
              │   ReceptivIQ Platform                 │
              │                                       │
              │   ┌──────────────────────────────┐    │
              │   │  Raw PII Lake（客户名单）     │    │
              │   └──────────┬───────────────────┘    │
              │              │ PII Access Service     │
              │              │  experian_enrich_list  │
              │              ▼                        │
              │   ┌──────────────────────────────┐    │
              │   │  Experian Combined API       │ ◄──┼─── 第三方
              │   │  Hygiene + Pinning + Enrich  │    │
              │   └──────────┬───────────────────┘    │
              │              │ 返回 4 类数据           │
              │              ▼                        │
              │   ┌──────────────────────────────┐    │
              │   │  Processed Lake               │    │
              │   │  experian_identity            │    │
              │   │  experian_hygiene             │    │
              │   │  experian_segments            │    │
              │   │  experian_attributes          │    │
              │   └──────────┬───────────────────┘    │
              │              │                        │
              │   ┌──────────▼───────────────────┐    │
              │   │  4 AI Agents 消费             │    │
              │   │  Persona / Creative /         │    │
              │   │  Attribution / Media          │    │
              │   └──────────┬───────────────────┘    │
              │              │                        │
              │              ▼                        │
              │   ┌──────────────────────────────┐    │
              │   │  Audience Export             │    │
              │   │  (Meta / DV360 / TikTok ...)  │    │
              │   └──────────────────────────────┘    │
              └───────────────────────────────────────┘
                                   │
                                   ▼
                          投放到广告平台
                          实现 AI 驱动的精准营销
```

---

## 12. 如何实际获取与配置画像标签（操作指南）

§3 提到 Experian 返回 "你点名要的画像标签 + 行为偏好"——这一节回答**怎么点名、code 从哪来、平台怎么配**。

### 12.1 两种"点选"机制（同一个接口里其实是 2 套）

| 你想要的                                                     | 通过哪个参数          | 在响应里              | 用途                                         |
| ------------------------------------------------------------ | --------------------- | --------------------- | -------------------------------------------- |
| **属性值**（年龄段、收入、Mosaic 段名……）                    | `erich`（请求参数）   | `ue_results`          | 取这个人**具体取值**——填进 persona 档案      |
| **segment 命中**（是不是"高价值用户"段、是不是"健康关注"段） | （Experian 后台预配） | `data_lookup_results` | 快速判断"这个人**属于不属于**某个预定义群体" |

**两套机制都来自同一个 `POST /ue-ov` 接口**，只是用法不同：

- `erich=3508,16963` → "请把 3508 和 16963 这两个字段的**取值**返给我"
- segment 命中 → 你的 Experian 账户在后台**关联了哪些 segment list**，每次调用自动返这些 segment 的命中情况

### 12.2 这些"code"是什么？

每个 code 是一个**整数编号**，对应一条 Experian 数据字段。

**举例**（实际编号以合同附带字典为准）：

| code    | 含义                            | 取值示例                  |
| ------- | ------------------------------- | ------------------------- |
| `3508`  | 收入分层（HH Income Range）     | `D`（= $100k-$150k）      |
| `16963` | Mosaic Group（19 大类生活方式） | `A`（= Power Elite）      |
| `16964` | Mosaic Type（71 个细分段）      | `A03`（= 高净值千禧家庭） |
| `25038` | TrueTouch Email Responsiveness  | `H`（= 高响应）           |
| `27195` | 年龄段（10 年区间）             | `35-44`                   |
| `27196` | 性别                            | `F`                       |
| `27197` | 婚姻状态                        | `M`（= 已婚）             |
| `45123` | 兴趣-户外运动                   | `Y` / `N`                 |

**调用示例**：

```json
POST /ue-ov
{
  "insertpartyid": "1234",
  "erich": "3508,16963,16964,25038,27195,27196,27197",
  "email": "dana@example.com",
  "zip": "92626"
}

→ 响应：
{
  "ue_results": {
    "3508":  "D",       // 收入 $100k-150k
    "16963": "A",       // Mosaic Group: Power Elite
    "16964": "A03",     // Mosaic Type: 高净值千禧家庭
    "25038": "H",       // Email 高响应
    "27195": "35-44",   // 35-44 岁
    "27196": "F",       // 女性
    "27197": "M"        // 已婚
  },
  ...
}
```

### 12.3 怎么拿到这本"code 字典"？

**字典不在 API 里，需要从 Experian 拿合同附件。** 流程：

#### 步骤 1 · 商务 / 合同环节

签 MLA（Master License Agreement）时，与 Experian Customer Success 团队索要 **4 份字典文件**：

| 文件名（参考）                         | 格式        | 内容                                                                           |
| -------------------------------------- | ----------- | ------------------------------------------------------------------------------ |
| **Combined API Field Code Dictionary** | Excel / CSV | 1000+ enrichment field code · 每条含：code · 字段名 · 取值域 · 描述 · 数据来源 |
| **Mosaic USA Definitions**             | PDF + CSV   | 71 个 Mosaic Type + 19 个 Group 的完整定义 + 每个段的描述/人口统计/行为特征    |
| **TrueTouch Code Reference**           | Excel       | 各渠道偏好 code（Email / SMS / Direct Mail / Display / 时段 / 创意风格）       |
| **Audience Engine Segment Catalog**    | Excel       | 预构建 1000+ segment 的 ID · 名称 · 估算人数 · 适用场景                        |

通常 Experian 销售在合同签字后 **3-5 个工作日**内交付。

#### 步骤 2 · 平台落库（dbt shared models）

把字典导入 Shared Reference Lake（与其他共享 reference 数据一起管理）：

```text
Shared Reference Lake（平台级 Neon project）
└── shared_experian
    ├── dim_field_codes              ← Combined API Field Code 字典
    │     (code, name, value_domain, description, data_source)
    ├── dim_mosaic_segments          ← 71 Mosaic Type 定义
    │     (mosaic_code, group_code, name, description, demographics_json)
    ├── dim_truetouch_codes          ← 渠道/风格偏好 code
    └── dim_audience_engine_segments ← 1000+ 预构建 segment
          (segment_id, name, est_population, description, category)
```

通过 license-gated FDW 暴露给每个 Agency 的 Processed Lake——所有 Agency 共享同一份字典（B 类共享数据）。

#### 步骤 3 · UI 让 Agency 用户"点选"

在 Audience Builder / Persona Builder 界面提供 **3 种点选方式**：

| 方式                                | UI 形态                                                                                                  | 适用场景               |
| ----------------------------------- | -------------------------------------------------------------------------------------------------------- | ---------------------- |
| **A · 预设套餐**（推荐 · 90% 场景） | 点 "标准画像包"（≈12 codes）/ "深度画像包"（≈40 codes）/ "TrueTouch 渠道包"（≈18 codes）                 | Agency Operator 一键选 |
| **B · 主题点选**                    | 勾选主题区："基础人口" + "Mosaic 段" + "渠道偏好" + "兴趣"——后端 join `dim_field_codes` 取对应 code 集合 | Agency 自定义主题      |
| **C · 字段级精选**                  | Power user 在 1000+ code 列表里全量勾选                                                                  | 数据分析师场景         |

UI 选完 → 后端拼出 `erich` 字符串 → 调 API。

#### 步骤 4 · 平台代码（PII Access Service）

```python
# services/pii-access/operations/experian_enrich_list.py

def experian_enrich_list(audience_id, profile_pack="standard"):
    # 1. 从 dim_field_codes 取 profile pack 对应的 code 列表
    codes = lookup_profile_pack(profile_pack)
    # 例如 standard pack → ["3508", "16963", "16964", "25038", "27195", "27196", "27197"]

    # 2. 从 raw_secure.users 取 audience 名单（仅在内存）
    contacts = load_audience_contacts(audience_id)

    # 3. 批量调 Experian Combined API
    for contact in contacts:
        response = experian_client.ue_ov(
            insertpartyid=AGENCY_CODE,
            erich=",".join(codes),
            email=contact.email,        # 或 sha256email 走哈希路径（HIPAA 客户）
            phone=contact.phone,
            zip=contact.zip
        )
        # 4. 解析 ue_results → 写 processed.experian_attributes
        for code, value in response["ue_results"].items():
            insert_attribute(audience_id, contact.pii_token, code, value)

        # 5. 解析 data_lookup_results → 写 processed.experian_segments
        for segment_id, hit in response["data_lookup_results"].items():
            if hit == "Y":
                insert_segment_hit(audience_id, contact.pii_token, segment_id)

    # 6. 写 audit log（transaction_id, rows_matched, cost_estimate）
```

### 12.4 怎么决定"该选哪些 code"？

不是所有 code 都得选——按业务场景挑：

| 业务场景                                  | 推荐 code pack                                                                     |
| ----------------------------------------- | ---------------------------------------------------------------------------------- |
| **基础 Persona 画像**（Persona Agent 用） | 年龄 + 性别 + 婚姻 + 收入 + Mosaic Group/Type + 家庭构成 + 房产状态（≈12 个 code） |
| **创意定向**（Creative Agent 用）         | 上述 + TrueTouch 渠道偏好 + 创意风格偏好 + 兴趣标签（≈25 个 code）                 |
| **媒介采买**（Media Agent 用）            | 上述 + 购买力分层 + 品类购买倾向 + 在线行为段（≈35 个 code）                       |
| **市场容量分析**                          | 仅取 Mosaic Group + 收入分层 + 地域（≈5 个 code）                                  |
| **HIPAA 合规客户**（PHI 场景）            | **绝不取** healthcare 相关 code（避免 PHI 收集）                                   |

**成本意识**：每个 `erich` code 都是计费维度——一次调用取 30 个 code 比取 5 个贵 ~6 倍。**预设套餐机制 = 控成本核心手段**。

### 12.5 `data_lookup_results`（segment 命中）怎么配？

不同于 `erich`（取属性值），segment lookup 是**在 Experian 后台预配的 segment list**：

**配置方式（Experian Console）**：

1. Experian 销售协助在你的 `insertpartyid` 账户下创建一个 **segment list**
2. 从 Audience Engine Catalog 中**勾选**你关心的 100-500 个 segment（例："Cooking Enthusiasts"、"Eco-Conscious Shoppers"、"Home Improvement DIY"）
3. 每次 `/ue-ov` 调用时，**所有勾选的 segment** 会自动检查并返回命中情况

```json
"data_lookup_results": {
  "12345": "Y",        // 命中"Cooking Enthusiasts"
  "45789": {},         // 未命中"Eco-Conscious Shoppers"
  "67890": "Y"         // 命中"Home Improvement DIY"
}
```

**平台落表**：`processed.experian_segments(pii_token, segment_id, hit_at)`

**业务用途**：投放前快速过滤——"找出 audience 中命中 `高消费` 段的子集" → 这部分人重点投放。

### 12.6 配套的开发任务（按优先级）

| 任务                                                                                  | 谁负责      | 时机                           |
| ------------------------------------------------------------------------------------- | ----------- | ------------------------------ |
| **签 MLA + 拿 4 份字典文件**                                                          | 商务 / 法务 | Phase 0（项目启动前 30-60 天） |
| **导入字典到 Shared Reference Lake**（`dim_field_codes` 等表）                        | 工程 / DBA  | Phase 2 开始时                 |
| **预设 3-5 个 profile pack**（standard / deep / truetouch / media / market_research） | 产品 + 工程 | Phase 2                        |
| **PII Access Service 的 `experian_enrich_list` operation**                            | 工程        | Phase 2                        |
| **UI Audience Builder 集成 profile pack 选择**                                        | 前端 + 产品 | Phase 3                        |
| **成本仪表盘**（按 Agency × pack × 调用量计费 / 告警）                                | 工程        | Phase 5                        |
| **HIPAA-aware code filter**（PHI code 自动 disable）                                  | 合规 + 工程 | Phase 5                        |

### 12.7 端到端示意图

```
[1] 合同/字典阶段（Phase 0）
    ├─ MLA 签字
    └─ Experian Customer Success 交付 4 份字典文件
           ↓
[2] 字典落库（Phase 2 开始）
    └─ Shared Reference Lake.shared_experian.dim_field_codes / dim_mosaic_segments / ...
           ↓
[3] 平台配置 profile packs
    ├─ "standard"   → 12 codes
    ├─ "deep"       → 40 codes
    └─ "truetouch"  → 18 codes
           ↓
[4] Agency Operator 在 UI 选择
    └─ "为 Audience X 跑 standard pack" → 后端构造 erich="3508,16963,..."
           ↓
[5] PII Access Service 调 Experian /ue-ov
    └─ 每条 contact 调一次，明文 PII 在 service 内存（≤ 15 min）
           ↓
[6] 响应落 Processed Lake
    ├─ processed.experian_attributes(audience_id, pii_token, code, value)
    └─ processed.experian_segments(audience_id, pii_token, segment_id)
           ↓
[7] dbt canonical
    └─ dim_person JOIN attributes JOIN segments → 完整 persona
           ↓
[8] AI Agent 消费
    └─ Persona / Creative / Attribution / Media 拿到丰富画像
```

### 12.8 关键 take-away

- ✅ **画像标签和 segment 命中都来自同一个 `/ue-ov` 接口**——只是用法不同（`erich` 取值 vs 后台预配命中）
- ✅ **code 字典需要从 Experian 合同附件拿**（4 份文件 · 3-5 个工作日交付）
- ✅ **字典是 B 类共享数据**——一份字典所有 Agency 共享
- ✅ **预设 profile pack 是控成本的核心**——避免 Agency 全选 1000+ code
- ✅ **HIPAA 客户的 code filter** 必须在平台层做（合规自动过滤 PHI code）

---

## 13. 接口参数详解（Request + Response）

> 本节基于 Experian Combined API 官方 Swagger 规范（`POST /marketing-services/targeting/v1/ue-ov`）逐字段详解，供工程对照实现。

### 13.1 接口基本信息

| 项                    | 值                                                    |
| --------------------- | ----------------------------------------------------- |
| **方法 + 路径**       | `POST /marketing-services/targeting/v1/ue-ov`         |
| **Sandbox Host**      | `sandbox-us-api.experian.com`                         |
| **Production Host**   | `api.experian.com`（由 Experian 在合同确认后提供）    |
| **认证**              | OAuth 2.0 (password flow) · scope `admin`             |
| **Token URL**         | `https://sandbox-us-api.experian.com/oauth2/v1/token` |
| **请求 Content-Type** | `application/json`                                    |
| **响应 Content-Type** | `application/json`                                    |

**OAuth 调用前置步骤**：

```bash
# 1. 拿 access_token
curl -X POST https://sandbox-us-api.experian.com/oauth2/v1/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "username=<your_user>" \
  -d "password=<your_pwd>" \
  -d "scope=admin"

# 响应：{"access_token": "eyJhbG...", "token_type": "Bearer", "expires_in": 3600}

# 2. 用 token 调 /ue-ov
curl -X POST https://sandbox-us-api.experian.com/marketing-services/targeting/v1/ue-ov \
  -H "Authorization: Bearer eyJhbG..." \
  -H "Content-Type: application/json" \
  -d @request.json
```

---

### 13.2 请求参数（UEOVRequest）总览

请求体是一个 JSON 对象，共 **24 个字段**，分 5 类。仅 2 个字段必填，其余按需提供——**送的字段越多、匹配率越高**。

| 类别                            | 字段数 | 字段名                                                                                                     |
| ------------------------------- | ------ | ---------------------------------------------------------------------------------------------------------- |
| **必填**                        | 2      | `insertpartyid` · `erich`                                                                                  |
| **身份识别**                    | 7      | `fname` · `mname` · `lname` · `lname2` · `suffix` · `fullname` · `gender` · `dob`                          |
| **地址**                        | 8      | `addr1` · `addr2` · `addr3` · `city` · `state` · `zip` · `zip4` · `country`                                |
| **联系方式（明文 + 3 种哈希）** | 8      | `email` · `md5email` · `sha1email` · `sha256email` · `phone` · `md1phone` ⚠️ · `sha1phone` · `sha256phone` |
| **地址哈希 + IP**               | 4      | `md5postal` · `sha1postal` · `sha256postal` · `ip`                                                         |

⚠️ **注意**：Swagger 中 phone 的 MD5 字段写作 `md1phone`（疑似 spec 笔误，正常应为 `md5phone`）。**实施时与 Experian 团队确认**——本节按 spec 原文写。

---

### 13.3 必填字段（2 个）

| 字段                | 类型   | 示例                       | 详解                                                                                                                                                                                                                    |
| ------------------- | ------ | -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`insertpartyid`** | string | `"1234"`                   | 你的 **Experian 账户编码**（计费 + 授权用）。Experian 在合同签字后分配；不同 Agency 走平台统一 `insertpartyid` 还是各自的——见 §6 价值 5 商业模式。**每次调用必带**。                                                    |
| **`erich`**         | string | `"3508,16963,16964,25038"` | **核心参数** —— enrichment field code 列表，逗号分隔。决定响应里 `ue_results` 返回哪些属性。code 来自 Experian 合同附带的 **Field Code Dictionary**（见 §12.3）。**送的 code 越多，调用成本越高**（按 code 数量计费）。 |

**`erich` 取值策略**：

- 一次调用建议 5-30 个 code（平衡信息量 vs 成本）
- 平台预设 3-5 个 profile pack（standard / deep / truetouch / media / market_research）
- HIPAA 客户禁用 healthcare 相关 code（合规过滤）

---

### 13.4 身份识别字段（8 个 · 可选）

| 字段       | 类型   | 示例                       | 详解                                     |
| ---------- | ------ | -------------------------- | ---------------------------------------- |
| `fname`    | string | `"Dana"`                   | 名（First Name）                         |
| `mname`    | string | `"Jo"`                     | 中间名（Middle Name）                    |
| `lname`    | string | `"Smith"`                  | 姓（Last Name）                          |
| `lname2`   | string | `"Jones"`                  | 第二姓氏（西班牙裔常见双姓）             |
| `suffix`   | string | `"MD"` / `"Jr"` / `"III"`  | 后缀（学位 / 排行）                      |
| `fullname` | string | `"Dana Jo Smith Jones MD"` | 完整姓名（可代替前述拆分字段）           |
| `gender`   | string | `"M"` / `"F"` / `"U"`      | 性别                                     |
| `dob`      | string | `"19770911"`               | 出生日期 · **格式 YYYYMMDD**（无分隔符） |

**实践建议**：

- 优先送拆分字段（`fname` + `lname`）→ Experian 匹配引擎对结构化输入命中率更高
- `fullname` 作 fallback——只有拆分字段不全时用
- `dob` 是高价值匹配字段（与 zip 组合命中率显著提升）

---

### 13.5 地址字段（8 个 · 可选）

| 字段      | 类型   | 示例              | 详解                           |
| --------- | ------ | ----------------- | ------------------------------ |
| `addr1`   | string | `"123 S Main St"` | 地址行 1（街号 + 街名 + 街类） |
| `addr2`   | string | `"Apt 22"`        | 地址行 2（单元 / 套房）        |
| `addr3`   | string | `""`              | 额外地址行（一般为空）         |
| `city`    | string | `"Costa Mesa"`    | 城市                           |
| `state`   | string | `"CA"`            | 州（2 字母缩写 USPS 标准）     |
| `zip`     | string | `"92626"`         | ZIP（5 位）                    |
| `zip4`    | string | `"2626"`          | ZIP+4 扩展（4 位）             |
| `country` | string | `"USA"`           | 国家（当前 sandbox 仅支持 US） |

**实践建议**：

- 地址脏没关系——Hygiene 模块会清洗（响应 `hygiene_results` 返回标准化版本）
- **最少送 `addr1` + `city` + `state` + `zip`** 即可获得 pinning 命中
- `zip4` 不必送（Hygiene 会补全）

---

### 13.6 联系方式字段（明文 + 哈希 · 8 个 · 可选）

**关键合规字段**——明文与哈希**任选其一或多个并送**，Experian 匹配引擎会自动尝试所有路径。

| 字段          | 类型   | 示例                  | 详解                                        |
| ------------- | ------ | --------------------- | ------------------------------------------- |
| `email`       | string | `"example@gmail.com"` | 邮箱**明文**                                |
| `md5email`    | string | `"<32-char hex>"`     | MD5 哈希                                    |
| `sha1email`   | string | `"<40-char hex>"`     | SHA-1 哈希                                  |
| `sha256email` | string | `"<64-char hex>"`     | **SHA-256 哈希**（推荐 · 合规友好）         |
| `phone`       | string | `"9495673800"`        | 电话**明文**（10 位 US 数字，不含分隔符）   |
| `md1phone` ⚠️ | string | `"<hex>"`             | MD5 哈希（**spec 笔误**，与 Experian 确认） |
| `sha1phone`   | string | `"<hex>"`             | SHA-1 哈希                                  |
| `sha256phone` | string | `"<hex>"`             | SHA-256 哈希（推荐）                        |

**HIPAA 客户路径**（明文 PII 不出域）：

```json
{
  "insertpartyid": "1234",
  "erich": "3508,16963",
  "sha256email": "<sha256(lower(trim(email)))>",
  "sha256phone": "<sha256(strip_punct(phone))>",
  "sha256postal": "<sha256(zip)>"
}
```

**哈希算法约定**（Experian 标准）：

- Email：`SHA256(lowercase(trim(email)))`
- Phone：`SHA256(strip_punctuation(phone))` —— 例如 `"(949) 567-3800"` → `"9495673800"` → SHA-256
- Postal：`SHA256(zip)` —— 仅 5 位 ZIP，不含 ZIP+4

---

### 13.7 地址哈希 + IP（4 个 · 可选）

| 字段           | 类型   | 示例             | 详解                      |
| -------------- | ------ | ---------------- | ------------------------- |
| `md5postal`    | string | `"<hex>"`        | 邮编 MD5 哈希             |
| `sha1postal`   | string | `"<hex>"`        | 邮编 SHA-1 哈希           |
| `sha256postal` | string | `"<hex>"`        | 邮编 SHA-256 哈希（推荐） |
| `ip`           | string | `"10.10.256.66"` | IP 地址（IPv4）           |

**`ip` 用途**：当用户身份不明（只有 IP）时用来做粗匹配——GA4 / Meta web pixel 触发的匿名访问场景有用。

---

### 13.8 响应参数（UEOVResponse）总览

响应体是一个 JSON 对象，共 **6 个顶级字段**：

| 字段                      | 类型    | 含义                                                      | 子字段数                          |
| ------------------------- | ------- | --------------------------------------------------------- | --------------------------------- |
| `FlowControl_Return_Code` | string  | 整体调用状态码                                            | —                                 |
| `data_lookup_results`     | object  | segment 命中结果（key = segment_id, value = "Y" or {}）   | 动态（视后台预配的 segment list） |
| `hygiene_results`         | object  | 地址清洗结果（CASS 标准化输出）                           | 20                                |
| `pinning_results`         | object  | 身份解析（individual / household / address ID）           | 5                                 |
| `transaction_id`          | integer | 交易 ID（数字）                                           | —                                 |
| `txn_id`                  | string  | 交易 ID（字符串，更长）                                   | —                                 |
| `ue_results`              | object  | enrichment 属性取值（key = `erich` code, value = 属性值） | 动态（= `erich` 中传的 code 数）  |

---

### 13.9 `FlowControl_Return_Code` 详解

| 取值（示例）            | 含义                                                        |
| ----------------------- | ----------------------------------------------------------- |
| `FC001`                 | 成功（标准成功码）                                          |
| `FC002` / `FC003` / ... | Experian 内部状态码——详见合同附带 **Return Code Reference** |

**实施建议**：把所有 `FC*` 状态写入 `audit_events` 表的 `experian_flow_code` 字段；非 `FC001` 触发告警。

---

### 13.10 `hygiene_results` 字段详解（20 个子字段）

CASS（Coding Accuracy Support System）地址标准化输出——USPS 邮政标准。

| 字段                  | 类型   | 示例              | 含义                                         |
| --------------------- | ------ | ----------------- | -------------------------------------------- |
| `hy_addr1`            | string | `"123 S Main St"` | 标准化地址行 1                               |
| `hy_addr2`            | string | `"Apt 22"`        | 标准化地址行 2                               |
| `hy_addr3`            | string | `""`              | 额外地址行                                   |
| `hy_street_number`    | string | `"100"`           | 街号（仅数字部分）                           |
| `hy_pre_directional`  | string | `"S"` / `""`      | 街名前方向（North/South 等）                 |
| `hy_street_name`      | string | `"Main"`          | 街名（纯名称）                               |
| `hy_street_suffix`    | string | `"St"`            | 街类（Street/Avenue/Boulevard 缩写）         |
| `hy_post_directional` | string | `""`              | 街名后方向                                   |
| `hy_unit`             | string | `"Apt 101"`       | 单元描述                                     |
| `hy_unit_number`      | string | `"101"`           | 单元号（仅数字）                             |
| `hy_city`             | string | `"Costa Mesa"`    | 标准化城市                                   |
| `hy_state`            | string | `"CA"`            | 标准化州                                     |
| `hy_zip`              | string | `"92626"`         | ZIP 5 位                                     |
| `hy_zip4`             | string | `"2626"`          | ZIP+4 扩展                                   |
| `hy_zip11`            | string | `"90001567890"`   | **ZIP11**（USPS 投递点 11 位编码）           |
| `hy_dpc`              | string | `"01"`            | **DPC**（Delivery Point Code · 投递点 2 位） |
| `hy_check_digit`      | string | `"5"`             | 校验位（用于条码 / IMb 生成）                |
| `hy_crrt`             | string | `"C101"`          | **Carrier Route**（投递路由代码）            |
| `hy_z4fn`             | string | `"2"`             | ZIP4 function number                         |
| `hy_urb`              | string | `""`              | Urban 标识（波多黎各专用，US 大陆通常空）    |
| `hy_MatchLevel`       | string | `"2"`             | **匹配等级**（见下表）                       |
| `hy_errcode`          | string | `""`              | 错误码（**空表示成功**，非空表示问题）       |

**`hy_MatchLevel` 取值**：

| 值  | 含义                          | 数据可用性     |
| --- | ----------------------------- | -------------- |
| `1` | 完全匹配（含 ZIP+4 + 投递点） | ✅ 高 · 可直邮 |
| `2` | 街号 + 街名 + ZIP 匹配        | ✅ 中 · 可直邮 |
| `3` | 街名 + ZIP 匹配（街号不准）   | ⚠️ 仅一般用途  |
| `4` | 仅 ZIP 匹配                   | ⚠️ 仅地理定位  |
| `5` | 未匹配                        | ❌ 不可信      |

**`hy_errcode` 常见值**（实际以 Experian 文档为准）：

- `""` → 成功
- `E01` / `E02` → 地址不可识别 / ZIP 无效

**平台落表**：`processed.experian_hygiene(record_id, pii_token, hy_addr1, hy_city, hy_state, hy_zip, hy_zip4, hy_match_level, hy_errcode, ingested_at)`

---

### 13.11 `pinning_results` 字段详解（5 个子字段）

**OmniView 身份解析输出**——核心字段，跨源 identity 的"红线"。

| 字段                      | 类型   | 示例                                 | 含义                                                |
| ------------------------- | ------ | ------------------------------------ | --------------------------------------------------- |
| `pinning_Return_Code`     | string | `"VE001"`                            | pinning 返回码（成功标识）                          |
| `pinning_individual_id`   | string | `"321987"`                           | **个体 ID** —— 这个人在 Experian 数据宇宙的唯一标识 |
| `pinning_household_id`    | string | `"654321"`                           | **家庭 ID** —— 该个体所属家庭单元                   |
| `pinning_address_id`      | string | `"987654"`                           | **地址 ID** —— 该地址的唯一标识                     |
| `pinning_matchReturnType` | string | `"OTHER"` / `"EXACT"` / `"PROBABLE"` | 匹配类型（命中精度）                                |

**`pinning_Return_Code` 取值**（实际以 Experian 文档为准）：

| 值      | 含义     |
| ------- | -------- |
| `VE001` | 成功匹配 |
| `VE002` | 部分匹配 |
| `VE003` | 未匹配   |

**`pinning_matchReturnType` 取值**：

| 值         | 含义                            | 置信度  |
| ---------- | ------------------------------- | ------- |
| `EXACT`    | 精确匹配（多字段全中）          | 🟢 最高 |
| `PROBABLE` | 概率匹配                        | 🟡 中等 |
| `OTHER`    | 其他类型（部分匹配 / 引擎选择） | 🟡 一般 |
| 空 / 缺失  | 未匹配                          | ❌      |

**平台落表**：`processed.experian_identity(record_id, pii_token, individual_id, household_id, address_id, match_type, return_code, ingested_at)`

**关键使用**：

- `individual_id` 作为 `dim_person` 表的主键来源（fallback 到 platform UUID）
- 跨 14 个 P1 source 通过 `individual_id` 关联同一人
- DSAR 主体定位的核心键

---

### 13.12 `ue_results` 字段详解（动态）

`ue_results` 是一个**动态对象**——key 是 `erich` 参数中送的 code，value 是该 code 对应字段的取值。

**结构**：

```json
"ue_results": {
  "<erich_code>": "<value>",
  ...
}
```

**Swagger 示例**：

```json
"ue_results": {
  "27197": "D",              // 婚姻状态 = D（视字典定义）
  "27195": "VE001",          // 年龄段 = VE001（特殊值，可能表示 fallback）
  "Records Processed": "valid",
  "27196": "Q",
  "25038": "VE001PC"
}
```

**特殊 key**：除了 numeric code，可能含 `"Records Processed"` 等管理 key——平台解析时跳过。

**值的形式**：

- 字符串（多数）：`"D"` / `"35-44"` / `"A03"`
- 数字字符串：`"3"` / `"100000"`（收入估算）
- 编码字符串：`"VE001PC"`（业务码 · 需查字典翻译）

**值翻译**：需要查询字典——同一 code 的值含义不同（如 `3508` 的 `"D"` = $100k-150k，`27196` 的 `"M"` = 已婚）。**平台 dim_field_codes 表存 code + value_domain（取值域）**，dbt model JOIN 翻译为可读值。

**平台落表**：

```sql
processed.experian_attributes (
  record_id    uuid,
  pii_token    bytea,
  field_code   text,         -- "3508" / "16963" / ...
  raw_value    text,         -- "D" / "A" / ...
  decoded_value text,        -- "$100k-150k" / "Power Elite"（JOIN dim_field_codes 翻译）
  ingested_at  timestamptz
)
```

---

### 13.13 `data_lookup_results` 字段详解（动态）

**结构**：

```json
"data_lookup_results": {
  "<segment_id>": "Y",   // 命中
  "<segment_id>": {},    // 未命中（空对象，注意：不是 "N"）
  ...
}
```

**关键点**：

- 命中：value 是字符串 `"Y"`
- **未命中**：value 是**空对象 `{}`**（**非** `"N"` 或 `null`）—— 解析时注意 type check
- segment list 在 Experian 后台预配（见 §12.5）

**Swagger 示例**：

```json
"data_lookup_results": {
  "12345": "Y",
  "45789": {}
}
```

**平台解析逻辑**（Python）：

```python
for segment_id, value in response["data_lookup_results"].items():
    if value == "Y":      # 命中
        record_segment_hit(audience_id, pii_token, segment_id)
    # else: 未命中（{}），不入库
```

**平台落表**：

```sql
processed.experian_segments (
  record_id  uuid,
  pii_token  bytea,
  segment_id text,
  hit_at     timestamptz
)
```

仅插入命中的 segment（未命中不入库，节省存储）。

---

### 13.14 `transaction_id` + `txn_id` 详解

| 字段             | 类型    | 示例                           | 用途                                |
| ---------------- | ------- | ------------------------------ | ----------------------------------- |
| `transaction_id` | integer | `98765`                        | 短数字 ID（计费 / 日志关联）        |
| `txn_id`         | string  | `"30000000000000000010203040"` | 长字符串 ID（全局唯一，跨系统追溯） |

**两个 ID 的关系**：通常 `transaction_id` 是 `txn_id` 的短哈希或后几位；两者都用于**审计追溯** + **错误支持**（联系 Experian 客服时报 `txn_id` 可直接定位调用记录）。

**平台必存**：每次调用响应写 `raw_secure.pii_access_log` 表：

```sql
raw_secure.pii_access_log (
  call_id            uuid PRIMARY KEY,
  agency_id          uuid,
  actor              text,             -- 谁触发
  purpose            text,             -- "experian_enrich_list"
  experian_txn_id    text NOT NULL,    -- ← 这里
  experian_transaction_id bigint,      -- ← 这里
  rows_matched       int,
  cost_estimate_usd  numeric(10,4),
  flow_code          text,             -- FlowControl_Return_Code
  called_at          timestamptz,
  -- INSERT-only · 6 年保留
)
```

---

### 13.15 错误响应

| HTTP 状态码                   | Schema             | 触发条件                                    |
| ----------------------------- | ------------------ | ------------------------------------------- |
| **400 Bad Request**           | `ErrorResponse400` | Payload 格式错误 / Authorization token 缺失 |
| **401 Unauthorized**          | `ErrorResponse401` | access_token 无效 / 过期                    |
| **500 Internal Server Error** | `ErrorResponse500` | Experian 服务端错误（建议自动重试 + 告警）  |

**ErrorResponse400 / 401 结构**：

```json
{
  "errors": [
    {
      "errorCode": "400",
      "errorType": "Bad Request",
      "message": "Authorization token missing"
    }
  ]
}
```

**ErrorResponse500 结构**：

```json
{
  "error": {
    "errorCode": "500",
    "message": "Internal server error"
  }
}
```

**平台错误处理策略**：

| HTTP     | 重试             | 告警      | 处理                                 |
| -------- | ---------------- | --------- | ------------------------------------ |
| 400      | ❌ 不重试        | ⚠️ Sentry | 记录 + 跳过该 record + 进 quarantine |
| 401      | ❌ 不重试        | 🔴 P0     | 触发 token 刷新流程 + 通知 SRE       |
| 500      | ✅ 指数退避 3 次 | ⚠️ Sentry | 重试失败后入 quarantine + alert      |
| 网络超时 | ✅ 指数退避 3 次 | ⚠️ Sentry | 同上                                 |

---

### 13.16 完整调用示例（Request + Response）

**请求**（明文 PII 路径，非 HIPAA 客户）：

```json
POST /marketing-services/targeting/v1/ue-ov
Authorization: Bearer eyJhbG...
Content-Type: application/json

{
  "insertpartyid": "1234",
  "erich":         "3508,16963,16964,25038,27195,27196,27197",
  "fname":         "Dana",
  "lname":         "Smith",
  "dob":           "19770911",
  "addr1":         "123 S Main St",
  "addr2":         "Apt 22",
  "city":          "Costa Mesa",
  "state":         "CA",
  "zip":           "92626",
  "email":         "dana@example.com",
  "phone":         "9495673800"
}
```

**响应**（200 OK）：

```json
{
  "FlowControl_Return_Code": "FC001",

  "hygiene_results": {
    "hy_addr1": "123 S Main St",
    "hy_addr2": "Apt 22",
    "hy_street_number": "123",
    "hy_pre_directional": "S",
    "hy_street_name": "Main",
    "hy_street_suffix": "St",
    "hy_unit": "Apt 22",
    "hy_unit_number": "22",
    "hy_city": "Costa Mesa",
    "hy_state": "CA",
    "hy_zip": "92626",
    "hy_zip4": "2626",
    "hy_zip11": "92626262201",
    "hy_dpc": "01",
    "hy_crrt": "C101",
    "hy_check_digit": "5",
    "hy_z4fn": "2",
    "hy_MatchLevel": "1",
    "hy_errcode": ""
  },

  "pinning_results": {
    "pinning_Return_Code": "VE001",
    "pinning_individual_id": "I7891234",
    "pinning_household_id": "H6543210",
    "pinning_address_id": "A9876541",
    "pinning_matchReturnType": "EXACT"
  },

  "ue_results": {
    "3508": "D", // 收入 $100k-150k
    "16963": "A", // Mosaic Group: Power Elite
    "16964": "A03", // Mosaic Type: 高净值千禧家庭
    "25038": "H", // Email 高响应
    "27195": "35-44", // 35-44 岁
    "27196": "F", // 女性
    "27197": "M" // 已婚
  },

  "data_lookup_results": {
    "12345": "Y", // 命中"Cooking Enthusiasts"
    "45789": {}, // 未命中"Eco-Conscious Shoppers"
    "67890": "Y" // 命中"Home Improvement DIY"
  },

  "transaction_id": 98765,
  "txn_id": "30000000000000000010203040"
}
```

**平台处理后落表（4 张表）**：

```sql
-- 1. experian_hygiene
INSERT INTO processed.experian_hygiene VALUES
  (record_id, pii_token, '123 S Main St', 'Costa Mesa', 'CA', '92626', '2626', '1', '', now());

-- 2. experian_identity
INSERT INTO processed.experian_identity VALUES
  (record_id, pii_token, 'I7891234', 'H6543210', 'A9876541', 'EXACT', 'VE001', now());

-- 3. experian_attributes (7 rows，每 erich code 一行)
INSERT INTO processed.experian_attributes VALUES
  (record_id, pii_token, '3508',  'D',     '$100k-150k',         now()),
  (record_id, pii_token, '16963', 'A',     'Power Elite',         now()),
  (record_id, pii_token, '16964', 'A03',   '高净值千禧家庭',       now()),
  (record_id, pii_token, '25038', 'H',     'Email 高响应',        now()),
  (record_id, pii_token, '27195', '35-44', '35-44 岁',            now()),
  (record_id, pii_token, '27196', 'F',     '女性',                now()),
  (record_id, pii_token, '27197', 'M',     '已婚',                now());

-- 4. experian_segments (仅命中的 2 行)
INSERT INTO processed.experian_segments VALUES
  (record_id, pii_token, '12345', now()),
  (record_id, pii_token, '67890', now());

-- 5. pii_access_log (1 行)
INSERT INTO raw_secure.pii_access_log VALUES
  (call_id, agency_id, 'persona_agent', 'experian_enrich_list',
   '30000000000000000010203040', 98765, 1, 0.025, 'FC001', now());
```

---

### 13.17 字段速查卡

**请求字段 24 个**：

```
必填 (2):    insertpartyid · erich
身份 (8):    fname · mname · lname · lname2 · suffix · fullname · gender · dob
地址 (8):    addr1 · addr2 · addr3 · city · state · zip · zip4 · country
联系 (8):    email · md5email · sha1email · sha256email · phone · md1phone · sha1phone · sha256phone
其他 (4):    md5postal · sha1postal · sha256postal · ip
```

**响应顶级字段 7 个**：

```
FlowControl_Return_Code   (string)
hygiene_results           (object · 20 子字段)
pinning_results           (object · 5 子字段)
ue_results                (object · 动态，= erich code 数)
data_lookup_results       (object · 动态，= 后台预配 segment 数)
transaction_id            (integer)
txn_id                    (string)
```

**5 张平台落表**：

- `processed.experian_hygiene` ← hygiene_results
- `processed.experian_identity` ← pinning_results
- `processed.experian_attributes` ← ue_results
- `processed.experian_segments` ← data_lookup_results（仅命中）
- `raw_secure.pii_access_log` ← transaction_id / txn_id / 调用元数据

---

## 14. 总结

> Experian Combined API 给平台提供"消费者档案馆"接口——一个客户名单进去，回来三件宝：标准地址 + 跨源身份 ID + 详细画像。这让我们的 AI Agent **真懂消费者**、让 14 个数据源**讲同一种语言**、让 DSAR 等合规请求**一键执行**、并让小 Agency 也**用得起世界一流的消费者数据**。它不是某一个模块的依赖，而是整个平台的**横切型基础设施**——必须在 Persona/Audience/Attribution 模块开发前完成集成。
