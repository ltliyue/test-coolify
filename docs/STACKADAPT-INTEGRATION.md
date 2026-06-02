# StackAdapt 接入文档

> **文档类型**:知识文档 / 接入参考
> _Last updated: **2026-05-21**_
> **目标读者**:工程师 / 接入工程师 / 产品 / 运营对接人 / 客户 IT
> **目的**:理解 StackAdapt 是什么、能做什么、怎么接入、本项目里怎么用

---

## 目录

- [Part 1:StackAdapt 平台](#part-1stackadapt-平台)
  - [1.1 是什么](#11-是什么)
  - [1.2 作用 / 用途](#12-作用--用途)
  - [1.3 关键网址](#13-关键网址)
  - [1.4 核心概念(必懂)](#14-核心概念必懂)
  - [1.5 能拿到哪些数据](#15-能拿到哪些数据)
  - [1.6 怎么集成(开发视角)](#16-怎么集成开发视角)
  - [1.7 怎么操作(用户视角)](#17-怎么操作用户视角)
  - [1.8 API 配额与限制](#18-api-配额与限制)
  - [1.9 常见踩坑](#19-常见踩坑)
- [Part 2:在 ReceptivIQ 项目中的实现](#part-2在-receptiviq-项目中的实现)
  - [2.1 当前 Adapter 现状](#21-当前-adapter-现状)
  - [2.2 客户端接入流程(自助 UI)](#22-客户端接入流程自助-ui)
  - [2.3 数据落仓 · 字段映射](#23-数据落仓--字段映射)
  - [2.4 合规与数据分级](#24-合规与数据分级)
  - [2.5 错误处理 & 监控](#25-错误处理--监控)
  - [2.6 验收测试清单](#26-验收测试清单)
  - [2.7 Phase 2 升级路线(REST → GraphQL)](#27-phase-2-升级路线rest--graphql)
- [附录:速查表与进阶资料](#附录速查表与进阶资料)

---

# Part 1:StackAdapt 平台

## 1.1 是什么

**StackAdapt** = 加拿大多伦多的程序化广告 DSP(Demand-Side Platform),成立于 2014 年,2024 年估值约 $25 亿美元,主打**全渠道自助式程序化**。

### 一句话定义

> StackAdapt = "一个由 AI 驱动的程序化广告 DSP,覆盖 **Native + Display + Video + CTV + Audio + Digital Out-of-Home + In-Game** 7 大渠道,Agency / 品牌侧客户可在一个后台跨渠道投放、优化、报表"。

### 与同类 DSP 的差异

| 维度          | StackAdapt                           | Trade Desk              | DV360                   |
| ------------- | ------------------------------------ | ----------------------- | ----------------------- |
| 渠道覆盖      | 7 大渠道(原生强)                     | 7 大渠道(显示 / CTV 强) | 6 大渠道(Google 生态强) |
| 客户群        | **Agency 友好** · 中型品牌           | 大型 Agency · 企业      | Google 客户为主         |
| 起步预算      | 低($500/月即可)                      | 高($25 K+/月)           | 中                      |
| AI / 自动优化 | 强(原生广告产品矩阵)                 | 强(Koa AI)              | 强(Performance Max)     |
| API 类型      | **GraphQL(主推)** + REST(deprecated) | REST + Reporting API    | REST + Reporting API    |

---

## 1.2 作用 / 用途

平台侧消费 StackAdapt 数据的典型场景:

| 场景                                  | 用途                                                                                                       |
| ------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| **Campaign 报表统一**                 | StackAdapt 投放数据进 ReceptivIQ 仓库 → 与 Meta / GA4 / DV360 数据跨源对齐 → Agency 客户看到统一 dashboard |
| **Attribution Agent 多触点归因**      | StackAdapt 的曝光 / 点击 / 转化路径与其他渠道合并,做跨渠道 MTA / MMM                                       |
| **Creative Agent 创意回流学习**       | 每个 creative 的 CTR / CVR 表现回流给 Creative Agent,优化下次 prompt                                       |
| **Audience 双向同步**(Phase 2)        | ReceptivIQ Persona Agent 生成的种子受众 → 推送到 StackAdapt 为投放目标                                     |
| **Media Agent 自动投放优化**(Phase 2) | AI 根据归因结果回写 StackAdapt(暂停低效 campaign · 调预算)                                                 |

---

## 1.3 关键网址(均已实测可打开)

| 类别                     | 网址                                                        |
| ------------------------ | ----------------------------------------------------------- |
| **官方 API 参考文档**    | https://docs.stackadapt.com/                                |
| 企业 API 商业页          | https://www.stackadapt.com/enterprise-api-solution          |
| 主站                     | https://www.stackadapt.com/                                 |
| **TypeScript SDK**(官方) | https://www.npmjs.com/package/@stackadapt/pa-typescript-sdk |
| TypeScript SDK GitHub    | https://github.com/stackadapt/pa-typescript-sdk             |
| 客户后台(登录入口)       | https://app.stackadapt.com/                                 |
| 帮助中心                 | https://help.stackadapt.com/                                |

### 三方接入说明(有真实截图 / 操作步骤,便于客户 IT 参考)

| 三方                           | 网址                                                                                                  | 价值                                             |
| ------------------------------ | ----------------------------------------------------------------------------------------------------- | ------------------------------------------------ |
| Supermetrics(2025-05 迁移公告) | https://docs.supermetrics.com/docs/stackadapt-new-api-key-required-may-13-2025                        | **必读** — 解释 GraphQL Key 替换 REST Key 的迁移 |
| Fivetran 接入指南              | https://fivetran.com/docs/connectors/applications/stackadapt/setup-guide                              | 标准 ELT 接入流程                                |
| AgencyAnalytics 接入步骤       | https://help.agencyanalytics.com/en/articles/6202979-connect-stackadapt                               | 截图最详细                                       |
| Whatagraph 接入步骤            | https://help.whatagraph.com/en/articles/11092414-how-to-connect-your-stackadapt-account-to-whatagraph | 备用参考                                         |
| Improvado GraphQL 文档         | https://improvado.io/docs/stackadapt-graphql                                                          | GraphQL Schema 速览                              |

> ⚠️ **重要历史变更**:**2025 年 5 月 13 日**起,StackAdapt 正式淘汰旧 REST API Key,**所有新接入必须使用 GraphQL Key**。旧的 REST Key 仍在过渡期可用但已被弃用,**预计 2026 年内停服**。

---

## 1.4 核心概念(必懂)

### 1.4.1 账户层级

```
StackAdapt Organization (顶层)
└─ Account (账户 · 通常 = 一个 Agency / 一个品牌)
   └─ Advertiser (广告主 · 一个账户下可有多个,常对应客户)
      └─ Campaign Group (campaign 集合,如季度活动)
         └─ Campaign (一个具体投放任务)
            └─ Ad Group (定向 + 出价配置)
               └─ Ad / Creative (具体素材)
```

**ReceptivIQ 关注的粒度**:`Advertiser` → `Campaign` → `Creative`。Ad Group 一般不单独抓,聚合在 Campaign 层。

### 1.4.2 报表维度(Dimension)与指标(Metric)

| 类别                 | 示例                                                                                                                             |
| -------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| **Dimensions(切片)** | `date` · `advertiser_id` · `campaign_id` · `creative_id` · `device_type` · `country` · `placement`                               |
| **Metrics(度量)**    | `impressions` · `clicks` · `spend` · `conversions` · `conversion_value` · `viewability` · `ctr` · `cpm` · `cpc` · `cpa` · `roas` |
| **特殊维度**         | `domain`(站点)· `geo`(地域)· `age_bucket` / `gender`(人口学,部分可用)                                                            |

### 1.4.3 GraphQL vs REST

| 维度     | GraphQL(主推)                             | REST(deprecated)                |
| -------- | ----------------------------------------- | ------------------------------- |
| 状态     | 当前推荐                                  | 已弃用,过渡期可用               |
| Key      | **GQL Key**(独立)                         | 旧 REST Key(2026 内停服)        |
| Endpoint | 单一端点,query 自定义字段                 | 多端点 `/v3/campaigns/stats` 等 |
| 写操作   | ✅ 支持(create / update / pause campaign) | 部分支持                        |
| 读操作   | ✅ 完整(含 reporting)                     | ✅ 完整                         |

---

## 1.5 能拿到哪些数据

### 1.5.1 投放执行(可读 + 可写)

- Campaign / Campaign Group / Advertiser 的**创建 · 修改 · 暂停 · 启用**
- Ad / Creative 的上传 · 启用 · 暂停
- 预算 · 出价 · 定向条件的查询和修改

### 1.5.2 报表数据(读)

| 类别           | 示例字段                                                                              |
| -------------- | ------------------------------------------------------------------------------------- |
| 基础指标(日级) | impressions · clicks · spend · conversions · conversion_value · ctr · cpm · cpc · cpa |
| 视频指标       | video_starts · video_25/50/75/100_complete · video_completion_rate                    |
| Viewability    | viewable_impressions · viewability_rate · time_in_view                                |
| 转化路径       | first_touch_campaign · last_touch_campaign · assist_count                             |
| 受众洞察       | domain_top_N(域名分布)· geo_top_N(地理分布)· demographics(年龄 · 性别)                |
| 实时           | real-time conversion · footfall(到店流量,LBS 类)                                      |

### 1.5.3 受众(Audience)

- Custom Audience 的创建与上传(matched audience)
- Lookalike segment 的状态查询
- Retargeting Pixel 触发数据

---

## 1.6 怎么集成(开发视角)

### 1.6.1 前置条件

1. 客户在 StackAdapt 已有付费账户(StackAdapt Account)
2. 客户向 StackAdapt 客户经理 / 客户成功经理申请 **GQL API Key**
3. 客户能找到自己的 Advertiser ID(在后台 URL 中可见)

### 1.6.2 GraphQL 认证(标准做法)

```http
POST https://api.stackadapt.com/graphql
X-Authorization: <gql_api_key>
Content-Type: application/json

{
  "query": "query { campaigns(advertiserId: \"<adv_id>\") { id name status } }"
}
```

> ⚠️ **不要用 `Bearer` 前缀**;**用 `X-Authorization` 或 `Authorization` header 直接放 Key**(不带 schema 前缀)。这是 StackAdapt 的特例。

### 1.6.3 关键 GraphQL Query 示例(报表)

```graphql
query CampaignStats($advertiserId: ID!, $startDate: Date!, $endDate: Date!) {
  reporting(
    advertiserId: $advertiserId
    dateRange: { start: $startDate, end: $endDate }
    dimensions: [DATE, CAMPAIGN, CREATIVE]
    metrics: [IMPRESSIONS, CLICKS, SPEND, CONVERSIONS, CONVERSION_VALUE]
  ) {
    rows {
      date
      campaignId
      campaignName
      creativeId
      impressions
      clicks
      spend
      conversions
      conversionValue
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

> 上面的字段名是常见命名,具体以 https://docs.stackadapt.com/ 的 Schema 为准。**集成前用 GraphQL Playground introspection 一次,自动生成最新 Schema**。

### 1.6.4 推荐 SDK(避免手写)

**Node / TypeScript**(官方维护):

```bash
npm i @stackadapt/pa-typescript-sdk
```

```ts
import { StackAdaptClient } from "@stackadapt/pa-typescript-sdk";
const client = new StackAdaptClient({ apiKey: process.env.STACKADAPT_KEY! });
const stats = await client.reporting.queryCampaignStats({
  advertiserId,
  startDate,
  endDate,
});
```

**Python**:无官方 SDK,可用 `gql` + `requests` 库手写;或继承我们 `BaseAdapter` 用 `httpx`(见 Part 2)。

### 1.6.5 Pagination(分页)

GraphQL 用 **cursor-based** 分页:`pageInfo.hasNextPage` + `pageInfo.endCursor` → 下次请求传 `after: endCursor`。

---

## 1.7 怎么操作(用户视角)

### 1.7.1 获取 GQL API Key(客户操作)

**StackAdapt 后台暂不提供自助生成 GQL Key**(2025 年 5 月起统一改为需要客户经理代为开通):

1. 登录 https://app.stackadapt.com/
2. 联系自己的 **Customer Success Manager(CSM)**(签约时分配的对接人)
3. 申请"GQL Public API access" + 说明用途("ReceptivIQ 平台数据接入")
4. CSM 通过工单系统开通 → 24-72 小时内邮件下发 Key
5. 把 Key 提供给 Agency 管理员录入 ReceptivIQ

> 🟡 如果客户没有 CSM(小客户),可走 https://help.stackadapt.com/ 提工单。

### 1.7.2 找到 Advertiser ID

后台 URL 里:`https://app.stackadapt.com/advertisers/<ADV_ID>/dashboard`,中间的 `<ADV_ID>` 就是。**一个 Account 下若有多个 Advertiser,每个都有独立 ID**。

### 1.7.3 撤销 Key

在 ReceptivIQ 平台直接点 **Integrations → StackAdapt → Disconnect**;**或**让客户 CSM 在 StackAdapt 侧吊销该 Key。两条路径任一即可生效。

---

## 1.8 API 配额与限制

| 限制            | 数值                                                         | 备注                                                          |
| --------------- | ------------------------------------------------------------ | ------------------------------------------------------------- |
| 默认配额        | **60 requests / minute**(标准 tier)                          | 跨整个 GQL 端点,所有 query 共享                               |
| 单 query 复杂度 | StackAdapt 内部有 cost 算法                                  | 单次 query 选 50+ 字段时可能被拒(GraphQL "Query too complex") |
| 分页大小        | 通常 `first: 1000` 是上限                                    | 超过会被强制截断                                              |
| 历史回溯        | **最长 24 个月**                                             | 早于 24 个月的数据需联系 CSM 申请导出                         |
| 报表延迟        | 当日数据 **延迟 2-4 小时**;转化数据延迟 24-72 小时(归因窗口) | 建议每次同步窗口含**回溯 7 天**容错延迟                       |
| Enterprise tier | 可申请 180+ req/min                                          | 找 CSM                                                        |

---

## 1.9 常见踩坑

| 踩坑                                         | 解决                                                                                      |
| -------------------------------------------- | ----------------------------------------------------------------------------------------- |
| **用 REST Key 调 GraphQL** → 401             | 必须使用 GQL Key(2025-05 后申请的新 Key)                                                  |
| **`Authorization: Bearer <key>` 前缀** → 401 | 去掉 `Bearer`,Key 直接放 header                                                           |
| **当日数据为 0**                             | 等 2-4 小时;StackAdapt 报表延迟                                                           |
| **conversion_value 与后台总数对不齐**        | StackAdapt 默认按归因窗口(通常 30 天)回算 → 历史回灌一定要拉 30 天前的窗口                |
| **多 advertiser 数据混在一起**               | 每个 query 都要带 `advertiserId` 参数;否则可能拿到账户下全部 advertiser                   |
| **币种问题**                                 | StackAdapt 按 advertiser 设置的币种返回(USD / CAD / EUR / …);务必同时保留 `currency` 字段 |
| **GraphQL Query 太大被拒**                   | 拆成两个 query;或用 dimensions / metrics 子集                                             |
| **REST 模式被弃用提醒**                      | StackAdapt 邮件提醒过渡;Phase 2 升级 GraphQL 是必做项                                     |

---

# Part 2:在 ReceptivIQ 项目中的实现

## 2.1 当前 Adapter 现状

| 项           | 状态                                                                                     |
| ------------ | ---------------------------------------------------------------------------------------- |
| 文件位置     | `backend/app/services/etl/adapters/stackadapt.py`                                        |
| 模式         | **legacy REST v3**(`X-Authorization` header)                                             |
| Mock 模式    | ✅ 已实现(`credentials = {"mock": True}` 跳过真实 API)                                   |
| 抓取粒度     | Campaign + Creative 日级聚合                                                             |
| 续抓策略     | page 数字 cursor + `sync_logs.last_cursor` 持久化                                        |
| 是否生产就绪 | 🟡 **过渡期可用,但需 Phase 2 升级到 GraphQL** — REST v3 将在 2026 年内被 StackAdapt 停服 |

### 2.1.1 当前实现关键代码(节选)

```python
class StackAdaptAdapter(BaseAdapter):
    platform = "stackadapt"
    BASE_URL = "https://api.stackadapt.com/v3"  # legacy · Phase 2 改 /graphql

    def get_raw_table(self) -> str:
        return "raw_stackadapt"

    def fetch(self, start_date, end_date, cursor=None):
        if self.credentials.get("mock"):
            return self._mock_data(start_date, end_date), None
        api_key = self.credentials.get("api_key", "")
        # httpx GET /v3/campaigns/stats with X-Authorization header
        ...
```

## 2.2 客户端接入流程(自助 UI)

```
客户 / Agency Admin                  平台
       │                              │
       │  1. 找 StackAdapt CSM 申请 GQL Key
       │  (24-72h)                    │
       │                              │
       │  2. 收到 Key + Advertiser ID │
       ├─────────────────────────────►│
       │                              │
       │  3. UI: Operations → Integrations → StackAdapt → Connect
       │     录入 Key + (可选)Advertiser ID + 抓取范围
       │                              │
       │                              │  4. 后端单次连通性测试
       │                              │     · 失败 → 凭证不入库,UI 报错
       │                              │     · 成功 → Fernet 加密入 credentials 表
       │                              │             写 sync_logs(status=pending)
       │                              │
       │                              │  5. Celery 任务异步触发首次同步
       │                              │     · 默认窗口:今天 - 90 天
       │                              │     · 写入 raw_stackadapt(per-Agency 物理库)
       │                              │
       │  6. WebSocket 推送            │
       │  ◄───────"sync_complete"─────│
       │                              │
       │  7. UI 显示状态变 Connected   │
       │                              │
       │  8. 后续每小时增量同步        │
       │     (默认 cron · 客户可调到日级)
```

## 2.3 数据落仓 · 字段映射

ReceptivIQ 把 StackAdapt 原始字段写入 **`raw_stackadapt`** 表(每 Agency 各自的物理库内,per-Agency 物理隔离)。

| StackAdapt 字段         | `raw_stackadapt` 列 | 类型            | 备注                                      |
| ----------------------- | ------------------- | --------------- | ----------------------------------------- |
| `date`                  | `date`              | `DATE`          | 报表日(StackAdapt 默认 UTC)               |
| `campaign_id`           | `campaign_id`       | `TEXT`          | 复合主键的一部分                          |
| `campaign_name`         | `campaign_name`     | `TEXT`          | 用于显示                                  |
| `creative_id`           | `creative_id`       | `TEXT`          | Creative Agent 关联键                     |
| `impressions`           | `impressions`       | `BIGINT`        |                                           |
| `clicks`                | `clicks`            | `BIGINT`        |                                           |
| `spend`                 | `spend`             | `NUMERIC(14,4)` | StackAdapt 默认 USD,可选其他              |
| `currency`              | `currency`          | `TEXT(3)`       | ISO 4217 · 当前 schema 暂未存(Phase 2 补) |
| `conversions`           | `conversions`       | `BIGINT`        |                                           |
| `conversion_value`      | `conversion_value`  | `NUMERIC(14,4)` |                                           |
| `ctr` / `cpm` / `cpc`   | (不存)              | —               | dbt staging 模型现算,避免冗余             |
| `agency_id`(平台注入)   | `agency_id`         | `UUID`          | 多租户硬隔离键                            |
| `synced_at`(平台注入)   | `synced_at`         | `TIMESTAMPTZ`   | 入库时间戳                                |
| `record_hash`(平台计算) | `record_hash`       | `TEXT`          | `SHA-256(date+campaign+creative)` · 防重  |

**下游 dbt 模型**:

- `stg_stackadapt.sql`(STEP 4 Normalize):字段名规范化 + CTR/CPM/CPC 计算 + 时区统一 UTC
- `canonical.events` 经 `mart_campaign_unified.sql` 与 Meta / GA4 / DV360 等跨源对齐

## 2.4 合规与数据分级

| 数据                                 | 平台分级          | 处理                                                               |
| ------------------------------------ | ----------------- | ------------------------------------------------------------------ |
| Campaign / Creative 聚合指标         | **L0 Public**     | 进 `processed.raw.stackadapt_records` · 平台层可跨源建模           |
| Advertiser ID / Campaign Name        | **L1 Internal**   | 不跨 Agency 边界(per-Agency 物理库自动隔离)                        |
| StackAdapt GQL Key                   | **L2 PII-级凭据** | Fernet 加密 · `audit_logs` 行级审计 · 日志只出现 `dsn_fingerprint` |
| 转化事件(若含 cookie / hashed email) | **L2 PII**        | 走 Raw PII Lake · 默认 **不抓**,客户明确启用才打开                 |

### 2.4.1 GDPR / CCPA 约束

- StackAdapt 是 **Data Processor**;客户(品牌方)是 **Data Controller**;ReceptivIQ 平台是 **Sub-processor**
- 客户的 DPA 必须明列 ReceptivIQ 为 sub-processor — 走我们 sub-processor 通知机制
- 平台默认仅消费**聚合广告报表**(已经是 L0),不直接对接最终消费者 PII

### 2.4.2 撤销 / 删除流程

| 触发                         | 平台响应                                                                                              |
| ---------------------------- | ----------------------------------------------------------------------------------------------------- |
| 客户在 UI 点 **Disconnect**  | `credentials.status = revoked` · cron 停止 · 历史已入仓数据保留(便于审计 / 回归)                      |
| 客户在 StackAdapt 侧吊销 Key | 下一次同步触发 401 · 平台自动 fallback 到 `disconnected` 状态 + 通知 Agency Admin                     |
| DSAR 删除请求                | 走 `/api/v1/compliance/dsar/*` 流程 · 把该客户在 `raw_stackadapt` 的对应行标记为 deleted 或物理 purge |

## 2.5 错误处理 & 监控

| 错误                      | 平台响应                                 | 客户可见                          |
| ------------------------- | ---------------------------------------- | --------------------------------- |
| 401 Unauthorized          | 凭证状态 → `expired` · 通知 Agency Admin | "StackAdapt key invalid · 请重连" |
| 403 Forbidden             | 同上(可能权限不足)                       | "Key missing read scope"          |
| 429 Rate Limited          | 指数退避 1s → 2s → 4s → 8s,最多 3 次     | 监控告警 · 用户无感               |
| 5xx                       | 退避 + 重试 + Sentry alert               | "StackAdapt unstable, retrying"   |
| GraphQL `errors` 字段非空 | 当作错误 · 写 `sync_logs.error_message`  | 显示首条错误                      |
| 数据为空(0 行)            | 正常完成同步 · 仅日志                    | 无                                |

所有错误都会:

- 写入 `sync_logs`(每次同步 1 行 · 含状态码 / error_message / rows_synced)
- 关键错误(401/403 / 连续 5 次失败)→ WebSocket 实时通知 Agency Admin
- 经 `audit_event(...)` 写入 `audit_logs`(action 模式:`integration.stackadapt.sync_*`)

## 2.6 验收测试清单

### 2.6.1 Mock 模式(无凭证开发 / CI)

```python
adapter = StackAdaptAdapter(credentials={"mock": True})
records, cursor = adapter.fetch("2026-05-01", "2026-05-21")
assert len(records) == 1
assert records[0]["campaign_id"] == "sa_camp_001"
```

CI 单测全部基于 Mock,不依赖真实 API。

### 2.6.2 客户接入烟测

```bash
curl -X POST http://platform.example.com/api/v1/integrations/stackadapt/test \
  -H "Authorization: Bearer <user_jwt>" \
  -H "Content-Type: application/json" \
  -d '{"sample_days": 7}'

# 期望返回:
# {"status": "ok", "rows_fetched": 124, "next_cursor": "2"}
```

### 2.6.3 数据对账(客户首次接入必做)

| 校验        | 方法                                                                                             | 允许误差    |
| ----------- | ------------------------------------------------------------------------------------------------ | ----------- |
| 总花费      | StackAdapt 后台 Top-level 报表 vs `SELECT SUM(spend) FROM stg_stackadapt WHERE date BETWEEN ...` | ±1%         |
| Campaign 数 | 后台 Campaign 列表 vs `SELECT COUNT(DISTINCT campaign_id) FROM stg_stackadapt`                   | 0(必须一致) |
| 时区        | 抽样 1 天的 impressions 数对齐                                                                   | ±0.5%       |
| 转化数      | 注意 30 天归因窗口 · 抓取窗口至少包含归因窗口                                                    | ±2%         |

### 2.6.4 持续监控指标

- `stackadapt_sync_success_rate` · `stackadapt_rows_per_sync` · `stackadapt_p99_latency`
- 7 天连续 0 行同步 → 自动告警(可能凭证失效或 advertiser 已暂停)

## 2.7 Phase 2 升级路线(REST → GraphQL)

| Phase   | 工作                               | 触发条件 / 时机                                           |
| ------- | ---------------------------------- | --------------------------------------------------------- |
| **2.1** | **REST v3 → GraphQL 升级**(必做)   | StackAdapt 即将停服 v3;**目标 2026 Q3 前完成**            |
| 2.2     | `currency` 字段补入 schema         | 与 2.1 同步,GraphQL 返回原币 + 货币代码                   |
| 2.3     | Conversion-level 抓取(per-event)   | 客户启用归因深度分析,**需要 PII Access Service**          |
| 2.4     | 写回:暂停 / 调预算 / 创建 campaign | Media Agent 落地,**需要客户重新生成 write-scope GQL Key** |
| 2.5     | Audience 双向同步                  | Audience Export 接入 StackAdapt 作为 destination          |

### 2.7.1 升级 to GraphQL 的工程清单

- [ ] 客户重新申请 GQL Key(StackAdapt CSM 工单,24-72h)
- [ ] 把 `BASE_URL` 改为 `https://api.stackadapt.com/graphql`
- [ ] 使用 `@stackadapt/pa-typescript-sdk`(Node 后端方案)**或**手写 Python `gql` + `httpx`
- [ ] 切换 cursor 分页 — 从数字 `page=N` 改 GraphQL 的 `endCursor`
- [ ] Schema introspection 自动生成 type bindings,持续兼容 StackAdapt 字段演变
- [ ] CI 加 mock GraphQL server(可用 `pytest-httpx` mock GraphQL endpoint)

---

# 附录:速查表与进阶资料

## A.1 接入前客户准备清单

```
[ ] 1. 客户已签约 StackAdapt 付费账户
[ ] 2. 客户已联系 CSM 申请 GQL API Key(过渡期可用 REST Key)
[ ] 3. 客户提供 Advertiser ID 清单(每个 advertiser 一行)
[ ] 4. 客户确认 advertiser 的币种(USD/CAD/EUR/…)
[ ] 5. 客户确认 DPA 已列出 ReceptivIQ 为 sub-processor
[ ] 6. 客户确认初始回灌窗口(默认 90 天,可申请 12-18 个月)
[ ] 7. 客户确认抓取频率(默认每小时,可调至每日)
```

## A.2 常见 GraphQL Query 速查

```graphql
# 列出 advertisers
query {
  advertisers {
    id
    name
    currency
  }
}

# 列出 campaigns
query ($advId: ID!) {
  campaigns(advertiserId: $advId) {
    id
    name
    status
    startDate
    endDate
    budget
  }
}

# 日级报表
query ($advId: ID!, $start: Date!, $end: Date!) {
  reporting(
    advertiserId: $advId
    dateRange: { start: $start, end: $end }
    dimensions: [DATE, CAMPAIGN]
    metrics: [IMPRESSIONS, CLICKS, SPEND, CONVERSIONS]
  ) {
    rows {
      date
      campaignId
      impressions
      clicks
      spend
      conversions
    }
  }
}

# 暂停 campaign(Phase 2 写操作)
mutation {
  updateCampaign(id: "123", status: PAUSED) {
    id
    status
  }
}
```

**字段名以 https://docs.stackadapt.com/ 实际 Schema 为准** — 上面是常见命名示意。

## A.3 关联文档

- [INTEGRATION-GUIDE-GA4-DV360](./INTEGRATION-GUIDE-GA4-DV360.md) — 同款知识文档模板
- [ELT-8-STEP-DESIGN](./ELT-8-STEP-DESIGN.md) — 八步 ELT 框架(StackAdapt 走第 1/2/3/5 步)
- [PII-DESIGN-SOLUTION](./PII-DESIGN-SOLUTION.md) — 凭证加密 + PII 边界(GQL Key 走 L2)
- [MULTI-TENANT-DB](./MULTI-TENANT-DB.md) — `raw_stackadapt` 在每 Agency 物理库内
- [ARCHITECTURE-AUDIT-2026Q2](./ARCHITECTURE-AUDIT-2026Q2.md) — adapter 当前在 14 个 P1 中位列已实现,Phase 2 GraphQL 升级在路线图

## A.4 风险提示

- **StackAdapt REST API 将在 2026 年内停服**(自 2025-05-13 起官方 deprecation)
- 当前 adapter 仍为 REST · **必须在 2026 Q3 前完成 GraphQL 升级**,否则同步会全线断流
- GQL Key 申请需经 CSM,**新客户接入要预留 1-3 个工作日**
- 转化数据有 30 天归因窗口延迟,**回灌策略须考虑回溯期**
