# Google GA4 与 DV360 接入文档

> **文档类型**:知识文档 / 接入参考
> **日期**:2026-05-12
> **目标读者**:工程师 / 接入工程师 / 产品 / 运营对接人
> **目的**:理解 GA4 和 DV360 是什么、能做什么、怎么接入、本项目里怎么用

---

## 目录

- [Part 1:Google Analytics 4(GA4)](#part-1google-analytics-4ga4)
  - [1.1 是什么](#11-是什么)
  - [1.2 作用 / 用途](#12-作用--用途)
  - [1.3 关键网址](#13-关键网址)
  - [1.4 核心概念(必懂)](#14-核心概念必懂)
  - [1.5 能拿到哪些数据](#15-能拿到哪些数据)
  - [1.6 怎么集成(开发视角)](#16-怎么集成开发视角)
  - [1.7 怎么操作(用户视角)](#17-怎么操作用户视角)
  - [1.8 API 配额与限制](#18-api-配额与限制)
  - [1.9 常见踩坑](#19-常见踩坑)
- [Part 2:Display & Video 360(DV360)](#part-2display--video-360dv360)
  - [2.1 是什么](#21-是什么)
  - [2.2 作用 / 用途](#22-作用--用途)
  - [2.3 关键网址](#23-关键网址)
  - [2.4 核心概念(组织层级必懂)](#24-核心概念组织层级必懂)
  - [2.5 能拿到哪些数据](#25-能拿到哪些数据)
  - [2.6 怎么集成(开发视角)](#26-怎么集成开发视角)
  - [2.7 怎么操作(用户视角)](#27-怎么操作用户视角)
  - [2.8 API 配额与限制](#28-api-配额与限制)
  - [2.9 常见踩坑](#29-常见踩坑)
- [Part 3:在 ReceptivIQ 项目中的实现](#part-3在-receptiviq-项目中的实现)
- [附录:速查表与进阶资料](#附录速查表与进阶资料)

---

# Part 1:Google Analytics 4(GA4)

## 1.1 是什么

**Google Analytics 4** 是 Google 的**网站和移动应用流量分析平台**,2020 年 10 月推出,2023 年 7 月**完全取代**了上一代 Universal Analytics(UA)。

### 一句话定义

> GA4 = "**事件驱动**(event-based)的用户行为分析平台,既追踪网页也追踪 App,内置机器学习预测和跨设备识别"

### 与上一代 UA 的关键区别

| 维度          | Universal Analytics(老) | **GA4(新)**                       |
| ------------- | ----------------------- | --------------------------------- |
| 数据模型      | 基于 **session**(会话)  | 基于 **event**(事件)              |
| 网页 / App    | 两个独立产品            | 统一一个 property                 |
| 跨设备识别    | 弱                      | 强(基于 Google Signals + User-ID) |
| 报表          | 预定义为主              | 灵活探索 + AI 洞察                |
| 数据保留      | 最长 50 个月            | 最长 14 个月(默认 2 个月)         |
| BigQuery 导出 | 仅 360 付费版           | **免费版也支持**                  |

> **核心变化**:从"页面浏览量为中心" → "用户行为事件流为中心"。每次点击、滚动、视频播放都是一个 event。

---

## 1.2 作用 / 用途

### 营销代理场景下的核心价值

1. **了解用户来源**:哪些渠道(SEM / 社交 / 邮件 / 直接访问)带来了流量
2. **追踪转化漏斗**:从访问 → 加购 → 下单的每一步转化率
3. **A/B 测试与归因**:配合 Google Ads,衡量广告投入的 ROI
4. **用户画像分群**:按行为 / 兴趣 / 地理 / 设备类型自动分群
5. **预测未来**:GA4 内置 ML 模型预测"7 天内购买概率"、"流失概率"

### 在本项目中的位置

```
GA4 是 Persona Agent 和 Attribution Agent 最重要的数据源之一:
  GA4 → 用户行为事件 → 仓库 → Persona Agent(画像)/ Attribution Agent(归因)
```

---

## 1.3 关键网址

### 用户后台

| 用途                               | URL                                                          |
| ---------------------------------- | ------------------------------------------------------------ |
| GA4 主控制台                       | https://analytics.google.com                                 |
| GA4 报表 / 探索                    | https://analytics.google.com(选择 property 后默认进 Reports) |
| Admin 后台(创建 property / 配置流) | https://analytics.google.com → 左下角齿轮                    |
| GA4 Demo Account(免账号探索)       | https://support.google.com/analytics/answer/6367342          |

### 开发者文档

| 用途                                      | URL                                                                                             |
| ----------------------------------------- | ----------------------------------------------------------------------------------------------- |
| GA4 Data API 文档(主要)                   | https://developers.google.com/analytics/devguides/reporting/data/v1                             |
| Data API Quickstart                       | https://developers.google.com/analytics/devguides/reporting/data/v1/quickstart-client-libraries |
| Dimension & Metric API Schema(查所有字段) | https://developers.google.com/analytics/devguides/reporting/data/v1/api-schema                  |
| Admin API(管理 property)                  | https://developers.google.com/analytics/devguides/config/admin/v1                               |
| Measurement Protocol(服务端事件上报)      | https://developers.google.com/analytics/devguides/collection/protocol/ga4                       |

### Google Cloud Console

| 用途                                    | URL                                                                           |
| --------------------------------------- | ----------------------------------------------------------------------------- |
| GCP Console(创 OAuth client + 启用 API) | https://console.cloud.google.com                                              |
| 启用 GA4 Data API                       | https://console.cloud.google.com/apis/library/analyticsdata.googleapis.com    |
| 启用 GA4 Admin API                      | https://console.cloud.google.com/apis/library/analyticsadmin.googleapis.com   |
| OAuth 同意页配置                        | https://console.cloud.google.com/apis/credentials/consent                     |
| API Quota 查看 / 申请提升               | https://console.cloud.google.com/apis/api/analyticsdata.googleapis.com/quotas |

### API endpoint

```
https://analyticsdata.googleapis.com/v1beta/properties/{PROPERTY_ID}:runReport
https://analyticsadmin.googleapis.com/v1beta/accounts
```

---

## 1.4 核心概念(必懂)

### 1.4.1 层级结构

```
Google Account
  └── GA4 Account                    (e.g. "Whalesong Product")
        └── Property(GA4 资产)        (e.g. "Brand-A Website" — 这是 API 调用的目标)
              └── Data Stream         (e.g. Web Stream / iOS Stream / Android Stream)
                    └── Events        (每次用户交互产生一条)
```

**关键 ID**:

- **Property ID**:数字格式(如 `123456789`),API 调用必填,在 Admin → Property Settings 里看
- **Measurement ID**(`G-XXXXXXXXXX`):前端 SDK 用,服务端 API **不用**

### 1.4.2 Event(事件)

GA4 的最小单位。每个 event 有:

- `event_name`:`page_view` / `scroll` / `click` / `purchase` / 自定义
- `event_parameters`:键值对,例如 `{page_path: "/home", page_referrer: "google.com"}`
- `user_properties`:用户级属性,例如 `{user_tier: "premium"}`
- `timestamp_micros`:微秒时间戳

GA4 **自动追踪**的事件:

- `page_view` · `session_start` · `first_visit` · `scroll`(90% 深度)· `click`(外链)
- `file_download` · `video_start / progress / complete` · `form_start / submit`

**自定义事件**:开发者在前端用 `gtag('event', 'add_to_cart', {item_id: 'sku123'})` 上报。

### 1.4.3 Dimension(维度) vs Metric(指标)

| 类型                | 例子                                                                      | 数据特征              |
| ------------------- | ------------------------------------------------------------------------- | --------------------- |
| **Dimension**(维度) | `country`, `deviceCategory`, `pagePath`, `source / medium`, `date`        | **分类型**,用来"分组" |
| **Metric**(指标)    | `sessions`, `activeUsers`, `screenPageViews`, `bounceRate`, `conversions` | **数值型**,用来"聚合" |

API 查询时:`dimensions=country&metrics=activeUsers` → 输出"按国家分组的活跃用户数"。

---

## 1.5 能拿到哪些数据

### 1.5.1 用户类指标

| 指标                     | 含义                         |
| ------------------------ | ---------------------------- |
| `totalUsers`             | 总用户数(去重)               |
| `activeUsers`            | 活跃用户数(过去 28 天有互动) |
| `newUsers`               | 新用户数                     |
| `userEngagementDuration` | 用户互动时长(秒)             |

### 1.5.2 流量类指标

| 指标                     | 含义                                |
| ------------------------ | ----------------------------------- |
| `sessions`               | 会话数                              |
| `screenPageViews`        | 页面浏览数                          |
| `engagedSessions`        | 互动会话数(停留 > 10s 或多页或转化) |
| `bounceRate`             | 跳出率                              |
| `averageSessionDuration` | 平均会话时长                        |

### 1.5.3 转化类指标

| 指标              | 含义                         |
| ----------------- | ---------------------------- |
| `conversions`     | 转化次数(按 event_name 标记) |
| `eventCount`      | 事件总次数                   |
| `eventValue`      | 事件价值(美元等)             |
| `totalRevenue`    | 总收入(电商场景)             |
| `purchaseRevenue` | 购买收入                     |

### 1.5.4 维度

| 维度                             | 含义                            |
| -------------------------------- | ------------------------------- |
| `date`                           | 日期(`YYYYMMDD`)                |
| `country` / `city` / `region`    | 地理                            |
| `deviceCategory`                 | `desktop` / `mobile` / `tablet` |
| `browser` / `operatingSystem`    | 浏览器 / 系统                   |
| `source` / `medium` / `campaign` | UTM 参数(广告归因关键)          |
| `pagePath` / `pageTitle`         | 页面                            |
| `landingPage`                    | 落地页                          |
| `userAgeBracket` / `userGender`  | 人口统计(开启 Google Signals)   |

完整字段表:[GA4 API Schema](https://developers.google.com/analytics/devguides/reporting/data/v1/api-schema)

### 1.5.5 BigQuery 原始数据导出(高级用法)

启用后,GA4 每天把**所有 raw event** 推到 BigQuery 表:

- 数据集名:`analytics_{property_id}`
- 表:`events_YYYYMMDD`(每天一张)+ `events_intraday_YYYYMMDD`(实时,延迟约 10 分钟)
- 一行一个 event,字段比 API 多 10 倍(完整设备指纹、user_pseudo_id 等)

**为什么重要**:绕过 API 配额和聚合限制,直接拿原始事件做自定义归因。

---

## 1.6 怎么集成(开发视角)

### 1.6.1 前置条件

1. Agency 在 [GCP Console](https://console.cloud.google.com) 创建项目(如 `receptiviq-prod`)
2. 启用 **Google Analytics Data API** + **Google Analytics Admin API**
3. 配置 **OAuth 2.0 Consent Screen**(填应用名、support email、scopes)
4. 创建 **OAuth 2.0 Client ID**(Web Application 类型),拿到 `client_id` + `client_secret`
5. Brand Client(品牌方)在我方平台点"连接 GA4" → 跳转 Google 授权 → 回调拿 `refresh_token`

### 1.6.2 OAuth 2.0 授权流程(标准 SaaS 模式)

```
User 点 "Connect GA4"
   ↓
我方后端生成 state(HMAC 签名) → 重定向到:
   https://accounts.google.com/o/oauth2/v2/auth?
     client_id=<our_client_id>&
     redirect_uri=<our_callback>&
     scope=https://www.googleapis.com/auth/analytics.readonly&
     response_type=code&
     access_type=offline&        ← 关键!不加这个拿不到 refresh_token
     prompt=consent&             ← 强制每次都返回 refresh_token
     state=<signed_state>
   ↓
User 在 Google 页面同意
   ↓
Google 重定向回我方 callback:
   https://app.agency-xyz.com/oauth/callback?code=<auth_code>&state=<signed_state>
   ↓
我方后端 POST 到 https://oauth2.googleapis.com/token:
   {client_id, client_secret, code, redirect_uri, grant_type: "authorization_code"}
   ↓
Google 返回 {access_token, refresh_token, expires_in, ...}
   ↓
我方:
  1. 用 access_token 调 GA4 Admin API 列出该用户能访问的 Property
  2. 让 User 选择要接入的 Property → 存 Property ID
  3. refresh_token 用 Fernet 加密存到 credentials 表
```

### 1.6.3 调用 Data API(伪代码)

```python
# 请求一份 "过去 30 天按国家分组的活跃用户数"
POST https://analyticsdata.googleapis.com/v1beta/properties/{property_id}:runReport
Headers:
  Authorization: Bearer <access_token>
  Content-Type: application/json
Body:
{
  "dateRanges": [{"startDate": "30daysAgo", "endDate": "today"}],
  "dimensions": [{"name": "country"}],
  "metrics": [{"name": "activeUsers"}, {"name": "sessions"}]
}
```

返回:

```json
{
  "rows": [
    {"dimensionValues": [{"value": "United States"}],
     "metricValues": [{"value": "12453"}, {"value": "8901"}]},
    ...
  ]
}
```

### 1.6.4 推荐的 Python SDK

```
google-analytics-data         # Data API(查报表)
google-analytics-admin        # Admin API(列 property)
google-auth-oauthlib          # OAuth flow
```

### 1.6.5 Service Account(可选 — B2B 场景)

如果 Agency 直接管理客户的 GA4(已被授权),可以用 **Service Account**:

1. GCP Console 创建 Service Account
2. 下载 JSON Key
3. 在 GA4 后台 → Admin → Property Access Management → 把 Service Account 邮箱加为 Viewer
4. Python:`google.auth.default()` 自动加载 Key,不需 OAuth flow

**缺点**:适合"我方代客户管理"模型,不适合"客户授权我方读取自己 GA4"模型。

---

## 1.7 怎么操作(用户视角)

### 1.7.1 创建 GA4 Property

1. 登录 [analytics.google.com](https://analytics.google.com)
2. 左下角齿轮 → Admin
3. **Account** 列 → 创建或选已有
4. **Property** 列 → 「+ Create Property」→ 填名字、时区、货币
5. 选 "Web" → 输入网站 URL → 拿到 Measurement ID(`G-XXX`)
6. 前端嵌 `gtag.js`(或用 Google Tag Manager)
7. 几分钟后 Real-time 报表能看到第一个用户

### 1.7.2 关键配置

| 配置                     | 位置                                                  | 重要性                                                       |
| ------------------------ | ----------------------------------------------------- | ------------------------------------------------------------ |
| **Enhanced Measurement** | Property → Data Streams → Web stream                  | 自动追踪 scroll / outbound click / video 等,默认开           |
| **Conversions**          | Configure → Events → 把某个 event 标记为 "Conversion" | 营销归因关键                                                 |
| **Custom Dimensions**    | Configure → Custom definitions                        | 把自定义 event parameter 提升为可查询维度                    |
| **Audiences**            | Configure → Audiences                                 | 定义"30 天内购买过的用户" 等分群,可推送到 Google Ads / DV360 |
| **Data Retention**       | Admin → Data Settings → Data Retention                | 默认 2 个月,建议改 14 个月(最长)                             |
| **Google Signals**       | Admin → Data Settings → Data Collection               | 启用后可拿到跨设备和人口统计                                 |
| **BigQuery Linking**     | Admin → BigQuery Linking                              | 启用 raw event 每日导出                                      |

---

## 1.8 API 配额与限制

| 限制                                  | 数值                        | 备注                        |
| ------------------------------------- | --------------------------- | --------------------------- |
| 每天总请求数                          | **50,000 / project**        | 项目级,跨所有 property 共享 |
| 每 100 秒请求数                       | 2,000 / project             | 突发限速                    |
| 单 property 并发                      | 10 个 concurrent            | 防滥用                      |
| 单 report 行数                        | 250,000 max                 | 超过需分页                  |
| Property 用户数级别配额(Token bucket) | 每属性每小时 50,000 tokens  | 复杂查询消耗多              |
| 申请提升配额                          | 通过 GCP Console quota 页面 | 通常 1-3 天审批             |

> **重要**:大客户的 property 配额可能不够,要提前向 Google 申请提升。

---

## 1.9 常见踩坑

| 踩坑                                   | 原因                                                           | 解决                                                                   |
| -------------------------------------- | -------------------------------------------------------------- | ---------------------------------------------------------------------- |
| 拿不到 `refresh_token`                 | OAuth URL 没加 `access_type=offline`                           | 加上,并加 `prompt=consent` 强制重新授权                                |
| 数据延迟 24-48 小时                    | GA4 标准数据有处理窗口                                         | Real-time 报表用 Realtime API;批量数据接受 1-2 天延迟                  |
| `(not set)` 大量出现在 source / medium | 直接访问或 UTM 缺失                                            | 教育客户必须打 UTM 参数                                                |
| Property ID 与 Measurement ID 混淆     | 两个不同概念                                                   | Property ID 给 API,Measurement ID 给前端 SDK                           |
| 数据回溯改不了                         | GA4 不允许补传历史数据                                         | 通过 Measurement Protocol 上报实时事件,不要尝试改过去                  |
| BigQuery 导出表延迟一天                | `events_YYYYMMDD` 在 T+1 才完整,实时数据在 `events_intraday_*` | 分析报表用 `events_YYYYMMDD`,实时面板用 `events_intraday_*`            |
| Cross-domain tracking 失效             | 多域名场景未配置                                               | Admin → Data Streams → Configure tag settings → Configure your domains |
| 跳出率(bounceRate)总是 100%            | GA4 定义变了:engagement < 10s 或无互动事件                     | 检查 Enhanced Measurement 是否开启                                     |

---

# Part 2:Display & Video 360(DV360)

## 2.1 是什么

**Display & Video 360** 是 Google 的**企业级程序化广告平台**(Demand-Side Platform,DSP),属于 **Google Marketing Platform(GMP)** 套件之一。

### 一句话定义

> DV360 = "**面向品牌方和大型代理商**的程序化广告投放系统,可在 Google 自有库存 + 第三方交易市场上购买展示 / 视频 / 音频 / CTV 广告"

### 与 Google Ads 的区别(经常被混淆)

| 维度     | Google Ads                                       | **DV360**                                                       |
| -------- | ------------------------------------------------ | --------------------------------------------------------------- |
| 主要库存 | Google Search + YouTube + Google Display Network | **多个 ad exchange**(自有 + 第三方,如 OpenX、Magnite、PubMatic) |
| 适合人群 | 中小广告主 / 个人                                | **品牌方 / 大型代理商**                                         |
| 学习曲线 | 较低                                             | **高**(企业级工具)                                              |
| 报表深度 | 简化                                             | **细到 inventory source / bid stream**                          |
| API      | Google Ads API                                   | **DV360 API**(完全不同的 endpoint)                              |
| 起步预算 | 几美元/天起                                      | 通常月支出 $10K+                                                |

---

## 2.2 作用 / 用途

### 营销代理场景下的核心价值

1. **多渠道一站式投放**:Display + Video + CTV(联网电视)+ Audio + DOOH(数字户外)
2. **跨 Exchange 库存覆盖**:Google AdX + OpenX + Magnite + Index Exchange 等几十家
3. **精细化定向**:Google 第一方数据 + 第三方 DMP + 客户上传的 Audience
4. **Programmatic Direct**:私有市场(PMP)/ Preferred Deals 与发布商直接谈价
5. **品牌安全 / 视频viewability**:与 IAS / DoubleVerify / MOAT 等集成

### 在本项目中的位置

```
DV360 在 ReceptivIQ 中既是:
  - Adapter 数据源:拉 campaign performance 数据 → 仓库
  - F-21 受众导出目标:把 AI 生成的 persona 推送回 DV360 作为 First-Party Audience
```

---

## 2.3 关键网址

### 用户后台

| 用途                        | URL                                                    |
| --------------------------- | ------------------------------------------------------ |
| DV360 主控制台              | https://displayvideo.google.com                        |
| Help Center                 | https://support.google.com/displayvideo                |
| Display Specs(创意尺寸规范) | https://support.google.com/displayvideo/answer/2706700 |

### 开发者文档

| 用途                       | URL                                                                                           |
| -------------------------- | --------------------------------------------------------------------------------------------- |
| **DV360 API v3 总览**      | https://developers.google.com/display-video/api/reference/rest                                |
| API Quickstart             | https://developers.google.com/display-video/api/quickstart                                    |
| Reporting API(Bid Manager) | https://developers.google.com/bid-manager/reference/rest                                      |
| API Client Libraries       | https://developers.google.com/display-video/api/libraries                                     |
| **Audience API**(F-21 用)  | https://developers.google.com/display-video/api/reference/rest/v3/firstAndThirdPartyAudiences |

### Google Cloud Console

| 用途                         | URL                                                                                |
| ---------------------------- | ---------------------------------------------------------------------------------- |
| 启用 Display & Video 360 API | https://console.cloud.google.com/apis/library/displayvideo.googleapis.com          |
| 启用 DBM API(Reporting)      | https://console.cloud.google.com/apis/library/doubleclickbidmanager.googleapis.com |

### API endpoint

```
https://displayvideo.googleapis.com/v3/advertisers/{ADVERTISER_ID}/...
https://doubleclickbidmanager.googleapis.com/v2/queries
```

---

## 2.4 核心概念(组织层级必懂)

DV360 的组织层级**非常重要**,API 调用必须沿此层级:

```
Partner                              (代理商整体账号)
  └── Advertiser                     (一个品牌客户 — API 调用入口,需 Advertiser ID)
        └── Campaign                 (营销目标,如 "2026 Q3 brand awareness")
              └── Insertion Order(IO)(预算和投放周期单位)
                    └── Line Item(LI)(单次投放单元,定向 + 创意 + 出价)
                          └── Creative          (实际广告素材)

  Audience Lists                     (一级资源:可重用的受众)
  Inventory Sources                  (广告库存,如 AdX、PMP 交易)
  Floodlight Activities              (转化追踪点)
```

| 层级                    | 含义                                 | 典型操作                                |
| ----------------------- | ------------------------------------ | --------------------------------------- |
| **Partner**             | 代理商整体账号,管理多个品牌          | 创建 Advertiser、设默认设置             |
| **Advertiser**          | 一个品牌 — **API 调用以此为根**      | 大多数 API 路径 `/advertisers/{id}/...` |
| **Campaign**            | 营销战役(类似营销活动)               | 设总体目标、frequency cap、品牌安全     |
| **Insertion Order(IO)** | 预算包,管理一段时间和一笔预算        | 设预算、起止时间、KPI                   |
| **Line Item(LI)**       | 投放单元 — **每天调优的核心对象**    | 定向 / 出价 / 频次 / 创意组合           |
| **Creative**            | 实际广告素材(banner / video / audio) | 上传、审核、关联到 LI                   |

---

## 2.5 能拿到哪些数据

### 2.5.1 实体管理 API(DV360 v3)

可以读 / 写以下资源:

- **Advertisers**:广告主基本信息
- **Campaigns / Insertion Orders / Line Items / Creatives**:四级广告对象
- **Inventory Sources**:库存
- **First/Third-Party Audiences**:受众列表(F-21 推送目标)
- **Combined Audiences**:组合受众
- **Custom Lists**:自定义列表(种子用户、否定列表)
- **Floodlight Activities**:转化点
- **Targeting Options**:几十种定向维度

### 2.5.2 报表 API(Bid Manager API v2)

通过创建 **Query**(查询模板)+ **Report**(实际报表)拿数据:

#### 主要指标(metrics)

| 指标                          | 含义                 |
| ----------------------------- | -------------------- |
| `IMPRESSIONS`                 | 曝光数               |
| `CLICKS`                      | 点击数               |
| `REVENUE_USD`                 | 广告主花费           |
| `CTR`                         | 点击率               |
| `VIDEO_COMPLETIONS`           | 视频完整播放数       |
| `VIEWABLE_IMPRESSIONS`        | 可视曝光数(MRC 标准) |
| `TOTAL_CONVERSIONS`           | 总转化数(Floodlight) |
| `POST_CLICK_CONVERSIONS`      | 点击后转化           |
| `POST_VIEW_CONVERSIONS`       | 看到后转化           |
| `RICH_MEDIA_VIDEO_TRUE_VIEWS` | 真实观看(TrueView)   |

#### 主要维度(filters / groupings)

| 维度                                                        | 含义                         |
| ----------------------------------------------------------- | ---------------------------- |
| `DATE`                                                      | 日期                         |
| `ADVERTISER` / `CAMPAIGN` / `INSERTION_ORDER` / `LINE_ITEM` | 实体维度                     |
| `CREATIVE`                                                  | 创意                         |
| `INVENTORY_SOURCE`                                          | 库存来源                     |
| `COUNTRY` / `REGION` / `CITY`                               | 地理                         |
| `DEVICE_TYPE` / `OS` / `BROWSER`                            | 设备                         |
| `LINE_ITEM_TYPE`                                            | 投放类型(标准 / TrueView 等) |
| `AUDIENCE_LIST`                                             | 命中的受众                   |

### 2.5.3 报表类型

- **STANDARD**:标准 campaign performance
- **AUDIENCE_PERFORMANCE**:按 audience 维度
- **REACH**:覆盖与频次
- **CROSS_PARTNER_REACH**:跨 partner 去重 reach
- **YOUTUBE**:YouTube 单独维度

---

## 2.6 怎么集成(开发视角)

### 2.6.1 前置条件

1. Agency / 客户已有 DV360 账号(Google sales 开通)
2. 在 GCP Console **同一项目**(可与 GA4 共用)启用 `Display & Video 360 API` + `DoubleClick Bid Manager API`
3. 获取 **Advertiser ID**(在 DV360 后台 URL 里能看到,如 `displayvideo.google.com/#ng_nav/p/1234567/a/9876543`,`9876543` 即 advertiser_id)
4. **服务账号或 OAuth 用户**必须被加到该 Advertiser 的访问列表(Setup → User access)

### 2.6.2 认证方式(两选一)

#### 方式 A:OAuth 2.0(SaaS 客户授权模式)

- 与 GA4 OAuth flow 几乎一致
- scope:`https://www.googleapis.com/auth/display-video` + `https://www.googleapis.com/auth/doubleclickbidmanager`
- Client / Brand Client 自己授权我方代他们调用

#### 方式 B:Service Account(我方代管模式)

- 创建 Service Account
- 在 DV360 User access 里把 SA 邮箱加为 Reporter(只读)/ Standard User(读写)
- Python `google.auth.default()` 加载 JSON Key

### 2.6.3 调用示例(伪代码)

#### 拉所有 Advertiser

```
GET https://displayvideo.googleapis.com/v3/advertisers?partnerId={partner_id}
Authorization: Bearer <token>
```

#### 拉某 Advertiser 下所有 Line Item

```
GET https://displayvideo.googleapis.com/v3/advertisers/{advertiser_id}/lineItems
```

#### 创建 First-Party Audience(F-21 推送场景)

```
POST https://displayvideo.googleapis.com/v3/advertisers/{advertiser_id}/firstAndThirdPartyAudiences
Body:
{
  "displayName": "ReceptivIQ-generated audience",
  "audienceType": "CUSTOMER_MATCH_USER_ID",
  "membershipDurationDays": 30,
  "description": "Persona from Agent v1.2"
}
```

#### 创建 Reporting Query

```
POST https://doubleclickbidmanager.googleapis.com/v2/queries
Body:
{
  "metadata": {
    "title": "Daily campaign perf",
    "dataRange": {"range": "LAST_30_DAYS"},
    "format": "CSV"
  },
  "params": {
    "type": "STANDARD",
    "groupBys": ["FILTER_DATE", "FILTER_ADVERTISER", "FILTER_LINE_ITEM"],
    "metrics": ["METRIC_IMPRESSIONS", "METRIC_CLICKS", "METRIC_REVENUE_USD"]
  },
  "schedule": {"frequency": "DAILY"}
}
```

返回 `queryId`,后续 `POST /queries/{queryId}:run` 触发执行,产物是 GCS 上的 CSV 链接。

### 2.6.4 推荐的 Python SDK

```
google-ads                       # 不要装 — 这是给 Google Ads 的,DV360 用下面这个
googleapiclient                  # google-api-python-client,通用
google-auth                      # 认证

# 调用方式
from googleapiclient.discovery import build
service = build('displayvideo', 'v3', credentials=creds)
advertisers = service.advertisers().list(partnerId='123').execute()
```

---

## 2.7 怎么操作(用户视角)

### 2.7.1 创建一个 Campaign 的完整流程

1. **Partner level**:登录 [displayvideo.google.com](https://displayvideo.google.com),选择 Partner
2. **进入 Advertiser**:左侧导航选目标 Advertiser
3. **创建 Campaign**:Campaigns → 「+ NEW CAMPAIGN」→ 选目标(品牌认知 / 转化等)
4. **创建 Insertion Order**:Campaign 内 「+ NEW IO」→ 设预算、起止日期、KPI(如 CPM ≤ $5)
5. **创建 Line Item**:IO 内 「+ NEW LI」→ 选 LI 类型(Display / Video / Audio)→ 配定向 + 创意
6. **上传 Creative**:Creatives → 上传素材或 import from Google Web Designer
7. **关联 Creative 到 LI**:在 LI 编辑页选择已上传创意
8. **激活**:Status: Active → 进入 review → 通过后开始投放
9. **看效果**:Reports → 选模板或 Custom report

### 2.7.2 关键设置

| 设置                       | 位置                             | 注意                                       |
| -------------------------- | -------------------------------- | ------------------------------------------ |
| **Brand Safety**(品牌安全) | Campaign → Brand Safety Controls | 排除暴力 / 不当内容类别                    |
| **Frequency Cap**          | IO / LI 层级                     | 限制单用户曝光次数                         |
| **Bid Strategy**           | LI → Bidding                     | Auto(由 Google 优化)or Manual CPM          |
| **Audiences**              | LI → Audience Targeting          | Google 第一方 + 上传的自定义受众           |
| **Inventory**              | LI → Inventory Sources           | 选 AdX-only / 全 Exchange / 自定义白名单   |
| **Viewability**            | LI → Viewability                 | 选 MRC 标准还是 GroupM 标准                |
| **Floodlight**(转化追踪)   | Advertiser → Floodlight          | 必须先在 Floodlight 里建 activity 才能追踪 |

### 2.7.3 报表怎么看

1. **Insights**(快速看):Campaign / IO / LI 页面顶部内置图表
2. **Reports** → **Standard Reports**:预设模板(performance, audience, reach)
3. **Reports** → **Custom Reports**:自由选维度 / 指标 / 时间窗口
4. **Reports** → **Scheduled Reports**:定时邮件发送 / 推送到 Cloud Storage

---

## 2.8 API 配额与限制

| 限制                 | 数值                        | 备注                       |
| -------------------- | --------------------------- | -------------------------- |
| 默认 QPS(写)         | **4 QPS / project**         | 极低,大量写入需要批量接口  |
| 读 QPS               | 10-20 QPS / project         | 比写宽松                   |
| Bid Manager API 报表 | 同时 max **5 runs / query** | 一个 query 不能并发跑太多  |
| Report 最长运行时长  | **60 分钟**                 | 超时自动失败,要拆查询      |
| 单 Report 最大行数   | 10 万行                     | 超过需用 BigQuery transfer |
| 申请配额提升         | GCP Console → Quotas        | 通常 3-7 天审批,要说明用途 |

> **重要**:DV360 的写 API 配额是出了名的低(4 QPS),做批量更新一定要用 Batch API + 实现指数退避重试。

---

## 2.9 常见踩坑

| 踩坑                               | 原因                                      | 解决                                                                      |
| ---------------------------------- | ----------------------------------------- | ------------------------------------------------------------------------- |
| `403 PERMISSION_DENIED`            | Service Account 没在 DV360 User access 里 | Admin → User access 加邮箱 + 选权限级别                                   |
| 写 API 频繁 429 限速               | DV360 写 QPS 只有 4                       | 用 batch endpoint;实现 exponential backoff                                |
| Report 数据延迟 24h+               | Bid Manager API 报表是 batch,不是实时     | 实时需求用 DV360 UI 的 In-Page reports                                    |
| Audience 上传后 24h 才能用         | Audience 同步要时间                       | 计划提前 1-2 天上传                                                       |
| LI 创建后 status 是 `DRAFT`        | API 创建出来不自动激活                    | 显式 PATCH 改为 `ACTIVE`                                                  |
| Floodlight tag 不工作              | 没在网站埋 tag                            | 用 Google Tag Manager 部署 Floodlight 像素                                |
| Audience size 显示 "Too small"     | 自定义受众 < 1000 用户                    | DV360 要求最低人数,继续累积或合并                                         |
| `partnerId` vs `advertiserId` 弄混 | 层级搞错                                  | partner_id 是代理商,advertiser_id 是品牌,API 路径绝大多数用 advertiser_id |
| 报表 CSV 中文乱码                  | 默认 UTF-8 但 Excel 不识别 BOM            | 用 Python pandas 直接读,或者 Excel 导入时选 UTF-8                         |

---

# Part 3:在 ReceptivIQ 项目中的实现

## 3.1 GA4 集成现状

### 代码位置

- **Adapter**:[backend/app/services/etl/adapters/ga4.py](../backend/app/services/etl/adapters/ga4.py) — `GA4Adapter`
- **OAuth callback**:[backend/app/api/v1/oauth_callback.py](../backend/app/api/v1/oauth_callback.py)
- **dbt staging**:[dbt/models/staging/stg_ga4.sql](../dbt/models/staging/stg_ga4.sql)
- **Platform registry**:[backend/app/services/platform_registry.py](../backend/app/services/platform_registry.py) — `"ga4"` 条目

### 配置 ENV

```env
GA4_CLIENT_ID=<google-oauth-client-id>
GA4_CLIENT_SECRET=<google-oauth-client-secret>
```

### 数据流

```
GA4 (User OAuth)
   ↓ adapter.fetch(start_date, end_date)
runReport API 返回行数据
   ↓ adapter.transform()
   ↓ Compliance Gate(IP 截断 + segment_id 哈希)
raw_ga4_events  (Snowflake / DuckDB)
   ↓ dbt
stg_ga4 → canonical_events → mart_attribution / mart_persona_signals
```

### 当前拉取字段(可扩展)

```
date · property_id · session_id · event_name · user_pseudo_id
sessions · users · new_users · page_views · bounce_rate
avg_session_duration · goal_completions
```

## 3.2 DV360 集成现状

### 代码位置

- **Adapter**:[backend/app/services/etl/adapters/dv360.py](../backend/app/services/etl/adapters/dv360.py) — `DV360Adapter`
- **Audience export client**:[backend/app/services/audience_export/dv360_client.py](../backend/app/services/audience_export/dv360_client.py) — F-21 推送 audience 回 DV360
- **dbt staging**:[dbt/models/staging/stg_dv360.sql](../dbt/models/staging/stg_dv360.sql)
- **Platform registry**:[backend/app/services/platform_registry.py](../backend/app/services/platform_registry.py) — `"dv360"` 条目

### 配置 ENV

```env
DV360_API_KEY=<api-key-or-service-account-json>
DV360_ADVERTISER_ID=<advertiser-id-from-DV360-URL>
```

### 数据流(双向)

```
入站:
  DV360 Reporting API → adapter.fetch → raw_dv360 → stg_dv360 → mart_campaign_unified

出站(F-21):
  PostgreSQL personas → AudienceExportService → DV360AudienceClient
   → POST /firstAndThirdPartyAudiences → DV360 First-Party Audience(供投放用)
```

### Adapter 当前实现要点

- 使用 `service_account.Credentials.from_service_account_info()` 加载 JSON Key
- 调用 `displayvideo.googleapis.com/v3/advertisers/{id}/lineItems` 拉 LI 数据
- 报表数据走 Bid Manager API `v2/queries`
- 输入校验:`advertiser_id` 必须匹配正则 `^[a-zA-Z0-9_-]+$`(防 SSRF)

---

# 附录:速查表与进阶资料

## A.1 GA4 vs DV360 一图速懂

| 维度            | GA4                                     | DV360                                     |
| --------------- | --------------------------------------- | ----------------------------------------- |
| **产品定位**    | 用户行为分析                            | 程序化广告投放                            |
| **谁的客户**    | 任何有网站的公司                        | 大品牌 / 大代理商                         |
| **核心动作**    | 看用户在你网站做什么                    | 决定钱花在哪个广告位                      |
| **数据方向**    | 入(收集网站数据)                        | 入(看报表) + 出(投广告)                   |
| **API 协议**    | REST + gRPC                             | REST                                      |
| **API host**    | `analyticsdata.googleapis.com`          | `displayvideo.googleapis.com`             |
| **关键 ID**     | Property ID(数字)                       | Advertiser ID(数字)                       |
| **OAuth scope** | `analytics.readonly`                    | `display-video` + `doubleclickbidmanager` |
| **QPS 默认**    | 50K/day,2K/100s                         | 4 QPS(写)/ 20 QPS(读)                     |
| **数据延迟**    | 24-48h(批)/ 实时(Realtime API)          | 24h(Reporting API)/ 实时(UI in-page)      |
| **是否免费**    | GA4 免费;GA4 360 付费                   | DV360 按 spend 抽佣                       |
| **本项目用途**  | Persona 行为信号 · Attribution 转化追踪 | Campaign 数据采集 · Audience 推送         |

## A.2 OAuth Redirect URI 速查(本项目)

```
开发: http://localhost:8000/api/v1/oauth/callback
生产: https://app.agency-xyz.com/api/v1/oauth/callback
```

在 GCP Console → Credentials → OAuth 2.0 Client → Authorized redirect URIs 里**两个都要填**。

## A.3 必装 Python 包

```
# GA4
pip install google-analytics-data google-analytics-admin

# DV360
pip install google-api-python-client

# 通用
pip install google-auth google-auth-oauthlib google-auth-httplib2
```

## A.4 核心结论速记

3 条最重要的常识(看这一份文档至少应该记住):

1. **GA4 是事件流,不是会话计数** — 每次滚动、点击、停留都是一行数据
2. **DV360 和 Google Ads 是两套完全独立的系统** — API endpoint / 认证 / 概念都不同,别搞错
3. **DV360 写 QPS 只有 4** — 大批量改 Line Item 必须用 batch endpoint + 指数退避重试

## A.5 推荐阅读 / 进阶资料

| 资源                                                                                                    | 类型         |
| ------------------------------------------------------------------------------------------------------- | ------------ |
| [GA4 API Schema 字段表](https://developers.google.com/analytics/devguides/reporting/data/v1/api-schema) | 字典查询     |
| [GA4 Demo Account](https://support.google.com/analytics/answer/6367342)                                 | 实操练习     |
| [DV360 API Codelab](https://developers.google.com/display-video/api/quickstart)                         | Hands-on     |
| [Bid Manager API Reference](https://developers.google.com/bid-manager/reference/rest)                   | 报表 API     |
| [Google Tag Manager 入门](https://support.google.com/tagmanager)                                        | 客户埋点必备 |
| [Floodlight 工作原理](https://support.google.com/displayvideo/answer/2829712)                           | 转化追踪     |

---

> 文档版本历史
> v1.0 · 2026-05-12 · 初版,分享会用
