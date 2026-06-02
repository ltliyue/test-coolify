# HubSpot 接入文档

> **文档类型**:知识文档 / 接入参考
> _Last updated: **2026-05-21**_
> **目标读者**:工程师 / 接入工程师 / 产品 / 运营对接人 / 客户 IT
> **目的**:理解 HubSpot 是什么、能做什么、怎么接入、本项目里怎么用

---

## 目录

- [Part 1:HubSpot 平台](#part-1hubspot-平台)
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
  - [2.2 客户接入流程(自助 UI)](#22-客户接入流程自助-ui)
  - [2.3 数据落仓 · 字段映射](#23-数据落仓--字段映射)
  - [2.4 合规与数据分级](#24-合规与数据分级)
  - [2.5 错误处理 & 监控](#25-错误处理--监控)
  - [2.6 验收测试清单](#26-验收测试清单)
  - [2.7 Phase 2 升级路线(Private App → OAuth Marketplace App)](#27-phase-2-升级路线private-app--oauth-marketplace-app)
- [附录:速查表与进阶资料](#附录速查表与进阶资料)

---

# Part 1:HubSpot 平台

## 1.1 是什么

**HubSpot** = 美国上市公司(NYSE: HUBS · 市值 $30B+),全球第一梯队的 **CRM + Marketing Automation + Sales + Service** 一体化平台,2025 年活跃客户 24 万+。

### 一句话定义

> HubSpot = "一个 CRM + 营销自动化 + 销售管道 + 客服 + CMS + 数据分析的一站式 SaaS,以 **CRM** 为单一事实源,把 **Marketing → Sales → Service** 全漏斗的数据 / 流程 / 报表打通"。

### 与同类 CRM 的差异

| 维度       | HubSpot                            | Salesforce                        | Marketo     | Mailchimp     |
| ---------- | ---------------------------------- | --------------------------------- | ----------- | ------------- |
| 定位       | CRM + 全栈营销自动化               | CRM(企业级)                       | 营销自动化  | 邮件营销      |
| 客户群     | **SMB + 中型企业**(强项)           | 企业级                            | 中大型 B2B  | SMB           |
| 起步价     | 免费版可用 → Starter $20/mo        | Pro $25/seat/mo 起                | $1250/mo 起 | Free → $13/mo |
| API 类型   | **REST(成熟)+ GraphQL(部分)**      | REST + GraphQL + SOAP             | REST + SOAP | REST          |
| 开发者门槛 | 🟢 低(Private App 30 秒生成 token) | 🟡 中(需要 Connected App + OAuth) | 🔴 高       | 🟢 低         |

---

## 1.2 作用 / 用途

ReceptivIQ 平台消费 HubSpot 数据的典型场景:

| 场景                             | 用途                                                                                 |
| -------------------------------- | ------------------------------------------------------------------------------------ |
| **Persona Agent · 客户画像构建** | 拉取 Contacts / Companies 的属性、互动历史、生命周期阶段,合成 Ideal Customer Profile |
| **Attribution Agent · 营销归因** | 关联 HubSpot Deals(转化结果)与 Meta / GA4 / DV360 触点 → 跨渠道 MTA                  |
| **Audience Export · 受众回流**   | Persona Agent 生成的种子受众 → HubSpot Lists → 用作邮件营销 / Workflows / Ads 触发   |
| **Creative Agent · 客户上下文**  | 拿到 HubSpot 客户当前的 lifecycle stage / lead_source 等,优化邮件 / 落地页文案       |
| **Reports Agent · 漏斗报表**     | Pipeline 阶段转化率 + Deal value · 进 PDF 报表给 Agency 客户                         |

---

## 1.3 关键网址(均已实测可打开)

| 类别                                              | 网址                                                                                         |
| ------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| **官方开发者门户**                                | https://developers.hubspot.com/                                                              |
| **API 总览**                                      | https://developers.hubspot.com/docs/api/overview                                             |
| **Authentication(OAuth + Private App)**           | https://developers.hubspot.com/docs/apps/developer-platform/build-apps/authentication        |
| **Scopes 完整列表**                               | https://developers.hubspot.com/docs/apps/developer-platform/build-apps/authentication/scopes |
| **CRM Objects API(Contacts / Companies / Deals)** | https://developers.hubspot.com/docs/api/crm/contacts                                         |
| **Rate Limit / 用量指南**                         | https://developers.hubspot.com/docs/developer-tooling/platform/usage-guidelines              |
| **Webhook(实时事件)**                             | https://developers.hubspot.com/docs/api/webhooks                                             |
| 客户后台                                          | https://app.hubspot.com/                                                                     |
| **App Marketplace**(发布 OAuth App)               | https://www.hubspot.com/products/marketplace                                                 |
| Developer Account 注册                            | https://developers.hubspot.com/get-started                                                   |
| Status 页(服务状态)                               | https://status.hubspot.com/                                                                  |
| HubSpot Academy(免费课程)                         | https://academy.hubspot.com/                                                                 |

### 三方接入说明(操作截图最全)

| 三方                          | 网址                                                                                       |
| ----------------------------- | ------------------------------------------------------------------------------------------ |
| Knit · HubSpot API 完整指南   | https://www.getknit.dev/blog/hubspot-api-directory-oD0RSt                                  |
| Apideck · HubSpot OAuth 注册  | https://developers.apideck.com/connectors/hubspot/docs/application_owner+oauth_credentials |
| Prismatic · HubSpot Component | https://prismatic.io/docs/components/hubspot/                                              |
| n8n · HubSpot 凭证            | https://docs.n8n.io/integrations/builtin/credentials/hubspot/                              |

---

## 1.4 核心概念(必懂)

### 1.4.1 账户层级

```
HubSpot Portal (账户/portalId · 一个客户 = 一个 portal)
├─ Hubs (产品模块)
│  ├─ Marketing Hub  (营销自动化)
│  ├─ Sales Hub      (CRM + Pipeline)
│  ├─ Service Hub    (客服 ticket)
│  ├─ CMS Hub        (网站建站)
│  └─ Operations Hub (数据同步)
└─ 数据模型(全 Hub 共享)
   ├─ Contacts       (个人,核心对象)
   ├─ Companies      (公司)
   ├─ Deals          (交易/订单)
   ├─ Tickets        (服务工单)
   ├─ Products / Quotes / Line Items
   ├─ Custom Objects (Enterprise 客户可建)
   ├─ Lists          (受众段)
   └─ Workflows      (自动化流程)
```

### 1.4.2 认证方式:Private App vs OAuth App

| 维度       | **Private App**              | **OAuth App**(Marketplace App)             |
| ---------- | ---------------------------- | ------------------------------------------ |
| 适用       | 单一 portal · 自己开发自己用 | 多客户(SaaS · Marketplace 上架)            |
| Key 类型   | 长期 access token(不过期)    | OAuth 标准:access + refresh token          |
| 申请门槛   | 客户后台 30 秒生成           | 需注册 Developer Account · 提交 App Review |
| 适合谁     | 客户单独使用                 | **ReceptivIQ 这类多租户平台** ✅           |
| Scope 管理 | 创建时选,后续可改            | OAuth 授权时弹窗选                         |
| Webhook    | ✅ 支持                      | ✅ 支持                                    |

> 🟡 **现状对照**:ReceptivIQ 当前 adapter 直接接 `Authorization: Bearer <token>`,**两种 token 都能用**(Private App 静态 token 或 OAuth access token)。当前自助接入流程**默认用 Private App**(客户自己生成 token 给我们),Phase 2 升级到 OAuth(平台注册 Marketplace App,客户一键授权)。

### 1.4.3 Scope(权限范围)

HubSpot 把 API 权限切成几十个 scope,**Private App 创建时勾选**,**OAuth 授权时弹窗展示**。ReceptivIQ 默认需要的最小集:

| Scope 代码                   | 用途                |
| ---------------------------- | ------------------- |
| `crm.objects.contacts.read`  | 读 Contacts         |
| `crm.objects.companies.read` | 读 Companies        |
| `crm.objects.deals.read`     | 读 Deals(转化漏斗)  |
| `crm.lists.read`             | 读 Lists            |
| `crm.schemas.contacts.read`  | 读自定义属性 schema |
| `oauth`(OAuth App 必带)      | 标识 OAuth App      |

**写操作(可选)** — 仅在 Audience Export 启用时申请:

| Scope 代码                   | 用途                   |
| ---------------------------- | ---------------------- |
| `crm.lists.write`            | 写 Lists(种子受众回流) |
| `crm.objects.contacts.write` | 创建 / 更新 Contact    |

### 1.4.4 ID 与标识

| 字段                  | 类型   | 备注                                                        |
| --------------------- | ------ | ----------------------------------------------------------- |
| `portalId`(账户)      | int    | 客户后台 URL `app.hubspot.com/contacts/<portalId>/...` 可见 |
| `vid` / `id`(Contact) | int    | Contact 主键                                                |
| `email`               | string | Contact 二级唯一键                                          |
| `companyId`           | int    | Company 主键                                                |
| `dealId`              | int    | Deal 主键                                                   |
| `hs_object_id`        | int    | 所有 object 的统一字段                                      |

---

## 1.5 能拿到哪些数据

### 1.5.1 CRM 核心对象

| 对象                  | 字段示例(常用)                                                                                                                            |
| --------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| **Contacts**(个人)    | email · firstname · lastname · phone · lifecyclestage · hs_lead_status · createdate · lastmodifieddate · hs_analytics_source · 自定义属性 |
| **Companies**(公司)   | name · domain · industry · numberofemployees · annualrevenue · country · createdate · 自定义属性                                          |
| **Deals**(交易)       | dealname · amount · dealstage · closedate · pipeline · createdate · hs_deal_stage_probability · 自定义属性                                |
| **Tickets**           | subject · content · hs_pipeline_stage · createdate · hs_ticket_priority                                                                   |
| **Engagements**(互动) | Email opens · Email clicks · Meeting bookings · Calls · Notes                                                                             |

### 1.5.2 营销自动化

- **Email Marketing**:发送 / 打开 / 点击 / 退订 / 反弹率
- **Workflows**(自动化流程):trigger / step / completion 数据
- **Forms**:提交记录 · UTM 参数
- **Landing Pages / CTAs**:访问数 · 转化率

### 1.5.3 行为分析

- 网站访问历史(每个 contact 的 page-view sequence)
- UTM / 来源 / referrer
- Session metrics

### 1.5.4 列表与受众

- **Lists**:静态列表 + 动态智能列表(基于属性的 segment)
- **Custom Object**(仅 Enterprise):可建自定义对象

### 1.5.5 写回能力

- 创建 / 更新 Contact / Company / Deal
- 向 List 加成员(种子受众回流)
- 触发 Workflow

---

## 1.6 怎么集成(开发视角)

### 1.6.1 前置条件(三选一)

| 方案                                            | 适用                              | 前置                                                     |
| ----------------------------------------------- | --------------------------------- | -------------------------------------------------------- |
| **方案 A · Private App**(单一客户)              | 客户自己生成 token 给我们         | 客户登录后台即可创建,30 秒                               |
| **方案 B · OAuth App · Developer Account 内部** | 我们建一个 Developer Account 测试 | 注册 https://developers.hubspot.com/get-started · 免审核 |
| **方案 C · OAuth App · Marketplace(推荐 GA)**   | **多客户自助接入**(SaaS 标准做法) | 注册 + 提交 App Review(2-4 周)                           |

### 1.6.2 Private App 认证(当前 adapter 路径)

```http
GET https://api.hubapi.com/crm/v3/objects/contacts
Authorization: Bearer <private_app_access_token>
Content-Type: application/json
```

`<private_app_access_token>` 是客户后台生成的长期 token(`pat-xx1-xxxxxxxx-xxxx-...` 格式)。

### 1.6.3 OAuth 2.0 授权流程(Phase 2 推荐路径)

```
平台前端                     用户/客户                HubSpot                    平台后端
    │                            │                       │                          │
    │ "Connect HubSpot" ────────►│                       │                          │
    │                            │                       │                          │
    │  redirect to               │                       │                          │
    │  app.hubspot.com/oauth/authorize?                  │                          │
    │    client_id=...&scope=crm.objects.contacts.read&  │                          │
    │    redirect_uri=...&state=<hmac-signed>            │                          │
    │                            │                       │                          │
    │                            │ 用户在 HubSpot 同意    │                          │
    │                            │                       │                          │
    │                            │                       │  redirect with code      │
    │                            │                       ├────────────────────────►│
    │                            │                       │                          │
    │                            │                       │  POST /oauth/v1/token    │
    │                            │                       │◄─────────────────────────│
    │                            │                       │  返回 access + refresh   │
    │                            │                       ├────────────────────────►│
    │                            │                       │                          │
    │                            │                       │                          │ Fernet 加密落库
    │                            │                       │                          │ 写 audit_logs
    │                            │                       │                          │
    │  redirect back to /integrations · status=connected │                          │
    │◄───────────────────────────┴───────────────────────┴──────────────────────────│
```

### 1.6.4 关键 REST 端点

```http
# 列出 Contacts(分页 cursor 在 paging.next.after)
GET /crm/v3/objects/contacts?limit=100&properties=email,firstname,lifecyclestage
Authorization: Bearer <token>

# 单个 Contact 详情
GET /crm/v3/objects/contacts/{id}?properties=...

# 列出 Deals
GET /crm/v3/objects/deals?limit=100&properties=dealname,amount,dealstage,closedate

# 列出 Companies
GET /crm/v3/objects/companies?limit=100&properties=name,domain,industry

# 创建 Contact(需要 write scope)
POST /crm/v3/objects/contacts
{
  "properties": { "email": "...", "firstname": "..." }
}

# Lists(种子受众回流)
POST /crm/v3/lists
GET  /crm/v3/lists/{listId}/memberships
```

### 1.6.5 推荐 SDK

| 语言    | SDK                                                 |
| ------- | --------------------------------------------------- |
| Python  | https://github.com/HubSpot/hubspot-api-python(官方) |
| Node.js | `@hubspot/api-client` (npm)                         |
| Ruby    | `hubspot-api-client` (RubyGems)                     |
| PHP     | `hubspot/api-client` (Composer)                     |

ReceptivIQ 当前 adapter 用 `httpx` 直调,因为只用到 contacts 端点,**不引入 SDK 依赖**。如果 Phase 2 接更多对象,值得切到官方 Python SDK。

### 1.6.6 Webhook(实时事件,可选)

订阅 HubSpot 事件 → 接收实时推送(无须轮询):

```http
POST https://your-platform.com/webhooks/hubspot
X-HubSpot-Signature: <hmac-sha256>

{
  "subscriptionType": "contact.creation",
  "objectId": 12345,
  "portalId": 67890,
  ...
}
```

ReceptivIQ Phase 2 启用,当前默认走 cron 轮询。

---

## 1.7 怎么操作(用户视角)

### 1.7.1 创建 Private App(自助 30 秒)

1. 登录 https://app.hubspot.com/
2. 右上角齿轮 → **Settings → Integrations → Private Apps**
3. 点 **Create a private app**
4. 填:
   - Name(如 `ReceptivIQ Integration`)
   - Description(可选)
   - **Scopes**:勾选 §1.4.3 列出的 scope
5. 点 **Create app** → 弹窗显示一次性 Access Token(`pat-xx1-...`)
6. **立刻复制保存**(关闭就再看不到完整 Token,只能重新生成)
7. 把 Token 交给 Agency 管理员

> 🟡 **要求**:执行此操作的用户在 HubSpot 必须有 **Super Admin** 权限,否则看不到 Private Apps 入口。

### 1.7.2 找到 Portal ID

后台 URL 中:`https://app.hubspot.com/contacts/<PORTAL_ID>/objects/0-1/views/...`,中间数字就是。或后台 Settings → Account Defaults → Account Information 也能看到。

### 1.7.3 撤销 Private App

在 ReceptivIQ 平台 **Integrations → HubSpot → Disconnect**,**或**在 HubSpot 后台 Settings → Integrations → Private Apps → 该 App → **Delete**。两种方式任一即可。

### 1.7.4 OAuth 一键授权(Phase 2 后)

1. 在 ReceptivIQ **Integrations → HubSpot → Connect** 点击
2. 浏览器跳转到 HubSpot 授权页(显示请求的 scope 清单)
3. 用户在 HubSpot 点 **Allow**
4. 自动跳回 ReceptivIQ,状态变 Connected
   **无须手动复制 token**。

---

## 1.8 API 配额与限制

### 1.8.1 标准配额(2026 最新)

| 计划                          | 每日请求数                        | 每 10 秒突发 |
| ----------------------------- | --------------------------------- | ------------ |
| **Free / Starter**            | 250,000                           | 100          |
| **Professional**              | 650,000                           | 190          |
| **Enterprise**                | 1,000,000                         | 190          |
| **API Limit Increase 加购包** | +1M / 天(最多买 2 个,即 +2M / 天) | —            |

> 配额重置时间 = HubSpot Portal 设置的时区 00:00。

### 1.8.2 端点级限制

| 端点                                                  | 限制                       |
| ----------------------------------------------------- | -------------------------- |
| **Search API** (`POST /crm/v3/objects/<type>/search`) | 5 req/sec/account(更严)    |
| **Files API**                                         | 上传 100 MB 单文件上限     |
| **Webhook 推送**                                      | 单次 batch 最大 100 条事件 |

### 1.8.3 超限响应

- 触发 429 Too Many Requests
- response header 含:`X-HubSpot-RateLimit-Remaining` · `X-HubSpot-RateLimit-Reset`
- ReceptivIQ adapter 指数退避 + 重试 3 次(1s → 2s → 4s)

### 1.8.4 历史数据

- Contacts / Companies / Deals **无历史长度限制**,只要还在 Portal 里就能拉
- 已删除对象走 `archived=true` 参数显式拉取(默认不返回)

---

## 1.9 常见踩坑

| 踩坑                                              | 解决                                                                                 |
| ------------------------------------------------- | ------------------------------------------------------------------------------------ |
| **Private App token 丢了** → 没法 disconnect 重置 | 在 HubSpot 后台直接 delete 该 Private App,新建一个                                   |
| **API Key 已淘汰**(2022 起废弃)                   | 不要找老文档说的"API Key";现在必须用 Private App 或 OAuth                            |
| **Scope 不够 → 403**                              | 后台编辑 Private App → 加 scope → 保存(token 自动更新 scope,无需重发)                |
| **Search API 5 req/sec 限速**                     | 不要用 Search 跑批量;改用 GET list + `properties=` 一次拉 100 条                     |
| **自定义属性拿不到**                              | properties 默认只返回 standard 字段;**必须显式列出** `properties=fname1,fname2,...`  |
| **email 字段大小写**                              | HubSpot 内部把 email 强制小写存;客户端比对 hash 时也要 lowercase + trim              |
| **lifecyclestage 跨 portal 含义不同**             | 客户可自定义 lifecyclestage 名称;**先拉 schema** 再做映射                            |
| **删除 Contact 不报错但没生效**                   | 删除是 archive(软删);硬删要 `?permanent=true` 且需要更高 scope                       |
| **OAuth `state` 参数被攻击**                      | 必须用 HMAC 签名 + `agency_id + nonce + timestamp` · 见我们 `oauth_callback.py` C-01 |

---

# Part 2:在 ReceptivIQ 项目中的实现

## 2.1 当前 Adapter 现状

| 项                          | 状态                                                                                |
| --------------------------- | ----------------------------------------------------------------------------------- |
| 文件位置                    | `backend/app/services/etl/adapters/hubspot.py`                                      |
| 认证模式                    | **Bearer token**(兼容 Private App token 和 OAuth access token)                      |
| API 版本                    | **CRM v3**(`/crm/v3/objects/contacts`)                                              |
| 抓取对象                    | **Contacts**(`raw_hubspot_contacts` 表)— Companies / Deals 待 Phase 2               |
| Mock 模式                   | ✅ `credentials = {"mock": True}` 走合成数据                                        |
| 续抓策略                    | `paging.next.after` cursor + `sync_logs.last_cursor` 持久化                         |
| 抓取字段(`properties` 参数) | `email, firstname, lastname, lifecyclestage, hs_lead_status, createdate`            |
| Token 类型(凭证表内)        | `access_token`(字段名通用,值可以是 Private App pat 或 OAuth token)                  |
| OAuth 流程                  | 🟡 部分实现 — `oauth_callback.py` 通用框架在;HubSpot 专用 client_id/secret 注册待补 |

### 2.1.1 当前实现关键代码(节选)

```python
class HubSpotAdapter(BaseAdapter):
    platform = "hubspot"
    HUBSPOT_API_BASE = "https://api.hubapi.com"

    def get_raw_table(self) -> str:
        return "raw_hubspot_contacts"

    def fetch(self, start_date, end_date, cursor=None):
        if self.credentials.get("mock"):
            return self._mock_data(...)
        access_token = self.credentials.get("access_token", "")
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {
            "limit": 100,
            "properties": "email,firstname,lastname,lifecyclestage,hs_lead_status,createdate",
        }
        if cursor:
            params["after"] = cursor
        response = httpx.get(
            f"{HUBSPOT_API_BASE}/crm/v3/objects/contacts",
            params=params, headers=headers, timeout=30,
        )
        ...
        next_cursor = data.get("paging", {}).get("next", {}).get("after")
        return records, next_cursor
```

### 2.1.2 PII 处理(重要)

HubSpot Contacts 含明文 PII(email · phone · firstname · lastname),平台落仓前做了 **C-3 合规处理**:

```python
records.append({
    "contact_id":      contact["id"],                      # L0 — id 本身不是 PII
    "email_hash":      hash_identifier(props["email"]),    # L2 → SHA-256(email + agency_salt)
    "first_name_hash": hash_identifier(props["firstname"]),
    "last_name_hash":  hash_identifier(props["lastname"]),
    "lifecycle_stage": props["lifecyclestage"],            # L0
    "lead_source":     props["hs_lead_status"],            # L0
    "create_date":     create_date_iso[:10],               # L0
})
```

**默认不存明文 email/name 到 raw 表**。若客户需要走 PII Access Service(如 Audience Export),走独立路径,**不在 raw 层**。

## 2.2 客户接入流程(自助 UI)

### 2.2.1 当前流程(Private App 路径)

```
客户 / Agency Admin                  平台
       │                              │
       │  1. 在 HubSpot 创建 Private App
       │     (Settings → Integrations → Private Apps)
       │     勾选 §1.4.3 scope
       │     一次性复制 pat-xx1-... token
       │                              │
       │  2. UI: Operations → Integrations → HubSpot → Connect
       │     录入 Token + Portal ID(选填)
       ├─────────────────────────────►│
       │                              │
       │                              │  3. 后端单次 GET /crm/v3/objects/contacts?limit=1
       │                              │     · 失败 → 凭证不入库,UI 报错
       │                              │     · 成功 → Fernet 加密入 credentials 表
       │                              │
       │                              │  4. Celery 任务异步触发首次同步
       │                              │     · 默认窗口:不限(HubSpot 全量)
       │                              │     · 写入 raw_hubspot_contacts(per-Agency 物理库)
       │                              │
       │  5. WebSocket 推送            │
       │  ◄───────"sync_complete"─────│
       │                              │
       │  6. UI 显示状态变 Connected   │
       │                              │
       │  7. 后续每小时增量同步        │
       │     使用 paging.next.after cursor 续抓
```

### 2.2.2 Phase 2 OAuth 流程(规划中)

```
[ReceptivIQ 一键 Connect HubSpot]
      ↓
浏览器跳转 → HubSpot 同意页(展示 scope 清单)
      ↓
用户点击 Allow
      ↓
HubSpot redirect 回来 → 平台后端用 code 换 token
      ↓
凭证 Fernet 加密入库 · 状态 Connected
      ↓
首次同步 + cron 增量
```

**待落地工作**:

- [ ] 在 HubSpot Developer Account 注册一个 OAuth App
- [ ] 提交 App Review 审核(2-4 周)
- [ ] 在 `oauth_callback.py` 加 HubSpot 专用分支(client_id / secret / scope list / refresh logic)
- [ ] Marketplace listing(可选,但提交了能拿"verified app"标识)

## 2.3 数据落仓 · 字段映射

ReceptivIQ 把 HubSpot Contacts 写入 **`raw_hubspot_contacts`** 表(每 Agency 各自物理库内)。

| HubSpot 字段                      | `raw_hubspot_contacts` 列 | 类型          | 备注                                                       |
| --------------------------------- | ------------------------- | ------------- | ---------------------------------------------------------- |
| `id`                              | `contact_id`              | `TEXT`        | HubSpot Contact ID                                         |
| `properties.email`                | `email_hash`              | `TEXT(64)`    | **SHA-256(lowercase(email) + agency_salt)** · 不存明文     |
| `properties.firstname`            | `first_name_hash`         | `TEXT(64)`    | 同上                                                       |
| `properties.lastname`             | `last_name_hash`          | `TEXT(64)`    | 同上                                                       |
| `properties.lifecyclestage`       | `lifecycle_stage`         | `TEXT`        | subscriber / lead / mql / sql / opportunity / customer / … |
| `properties.hs_lead_status`       | `lead_source`             | `TEXT`        | 自定义值                                                   |
| `properties.createdate`(ISO 8601) | `create_date`             | `DATE`        | 仅日期部分                                                 |
| `agency_id`(平台注入)             | `agency_id`               | `UUID`        | 多租户硬隔离键                                             |
| `client_id`(平台注入,可空)        | `client_id`               | `UUID`        | 子租户隔离键(RLS)                                          |
| `synced_at`(平台注入)             | `synced_at`               | `TIMESTAMPTZ` | 入库时间戳                                                 |
| `record_hash`(平台计算)           | `record_hash`             | `TEXT(64)`    | `SHA-256(contact_id + lastmodified_ts)` · 防重             |

**下游 dbt 模型**:

- `stg_hubspot.sql`(STEP 4 Normalize):字段类型对齐 · 时区统一 · null 处理
- `mart_persona_signals.sql`:lifecycle / lead_source 聚合给 Persona Agent
- `mart_attribution.sql`:与 Deals 表 JOIN 形成转化漏斗(Phase 2,Deals 抓取后)

## 2.4 合规与数据分级

| 数据                                                             | 平台分级           | 处理                                                               |
| ---------------------------------------------------------------- | ------------------ | ------------------------------------------------------------------ |
| `contact_id` / `lifecycle_stage` / `lead_source` / `create_date` | **L0 Public**      | 直接进 raw / Processed Lake                                        |
| Email / 姓 / 名 → hash                                           | **L2 PII**         | SHA-256 + agency salt,**不可逆**;明文不入库                        |
| `phone` / 自定义 PII 字段                                        | **L2 PII**         | 同上处理(Phase 2 扩展时补)                                         |
| HubSpot Token                                                    | **L2 PII-级凭据**  | Fernet 加密 · `audit_logs` 行级审计 · 日志只出现 `dsn_fingerprint` |
| Custom Object · 业务自定义字段                                   | 视字段内容动态分级 | Phase 2 `field_classifier.py` 实现                                 |

### 2.4.1 GDPR / CCPA 约束

- **HubSpot 是 Data Processor**(对客户而言);客户(品牌方)是 Controller;ReceptivIQ 是 Sub-processor
- 客户的 DPA 必须列 ReceptivIQ — 走我们 sub-processor 通知机制
- HubSpot 内置的 GDPR 工具(Subscription preferences · Cookie policy)与我们 DSAR 流程**互补**:HubSpot 处理"客户与品牌"层面;ReceptivIQ 的 DSAR 处理"客户与平台"层面

### 2.4.2 DSAR / Right to Delete

- 客户(终端用户)向 Agency 请求删除 → Agency 管理员在 ReceptivIQ 发起 DSAR → 平台:
  1. 从 `raw_hubspot_contacts` 删除该 `email_hash` 对应行
  2. **不**主动调 HubSpot API 删除源记录(那是 Agency 与 HubSpot 之间的合同关系)
  3. 审计行保留(留痕证据)

### 2.4.3 撤销 / 删除流程

| 触发                          | 平台响应                                              |
| ----------------------------- | ----------------------------------------------------- |
| UI 点 Disconnect              | credentials.status = revoked · 停 cron · 历史数据保留 |
| 客户在 HubSpot 删 Private App | 下次同步 401 · 自动 fallback disconnect               |
| DSAR purge                    | `/api/v1/compliance/dsar/*` 流程清理                  |

## 2.5 错误处理 & 监控

| 错误                      | 平台响应                                            | 客户可见                                  |
| ------------------------- | --------------------------------------------------- | ----------------------------------------- |
| 401 Unauthorized          | 凭证 → expired · 通知 Agency Admin                  | "HubSpot token invalid · 请重连"          |
| 403 Forbidden(scope 不够) | 同上 + 提示需要哪个 scope                           | "Missing scope: `crm.objects.deals.read`" |
| 429 Rate Limited          | 读 `X-HubSpot-RateLimit-Reset` · 等到指定时间再重试 | 监控告警,用户无感                         |
| 5xx                       | 退避 + 重试 + Sentry alert                          | "HubSpot unstable, retrying"              |
| 单条 contact 解析失败     | 跳过该条 · 记 `sync_logs.error_message` + 行号      | 不阻断其他 contact                        |
| 数据为空                  | 正常完成 · 仅日志                                   | 无                                        |

所有错误都走 `audit_event(...)` 写入 `audit_logs`(action 模式:`integration.hubspot.sync_*`),关键错误推送 WebSocket。

## 2.6 验收测试清单

### 2.6.1 Mock 模式(无凭证开发 / CI)

```python
adapter = HubSpotAdapter(credentials={"mock": True})
records, cursor = adapter.fetch("2026-01-01", "2026-05-21")
assert len(records) >= 1
assert records[0]["email_hash"].startswith("hash:") or len(records[0]["email_hash"]) == 64
```

### 2.6.2 客户接入烟测

```bash
curl -X POST http://platform.example.com/api/v1/integrations/hubspot/test \
  -H "Authorization: Bearer <user_jwt>" \
  -H "Content-Type: application/json" \
  -d '{"sample_size": 5}'

# 期望返回:
# {"status": "ok", "rows_fetched": 5, "next_cursor": "VG9rZW4...", "scopes_ok": true}
```

### 2.6.3 数据对账

| 校验           | 方法                                                                                          | 误差        |
| -------------- | --------------------------------------------------------------------------------------------- | ----------- |
| Contact 总数   | HubSpot 后台 Contacts 总数 vs `SELECT COUNT(*) FROM raw_hubspot_contacts WHERE agency_id=:id` | 0(必须一致) |
| 最近 7 天新增  | 后台 List "Recently created" vs `SELECT COUNT(*) WHERE create_date >= today - 7`              | 0           |
| Lifecycle 分布 | 后台 lifecycle 报表 vs `GROUP BY lifecycle_stage`                                             | ±1%         |

### 2.6.4 持续监控

- `hubspot_sync_success_rate` / `hubspot_rows_per_sync` / `hubspot_p99_latency`
- 7 天 0 行同步 → 自动告警

## 2.7 Phase 2 升级路线(Private App → OAuth Marketplace App)

| Phase   | 工作                                         | 触发条件 / 时机                                             |
| ------- | -------------------------------------------- | ----------------------------------------------------------- |
| **2.1** | **OAuth Marketplace App 注册 + Code Review** | ReceptivIQ 正式开放 self-serve 接入时;**预留 2-4 周审核期** |
| 2.2     | 抓取 Companies + Deals + Engagements         | 客户需要漏斗归因 · Deal level attribution                   |
| 2.3     | Webhook 实时事件接入(代替 cron 轮询)         | 客户要求实时受众触发 / 实时同步                             |
| 2.4     | Audience Export 写回(创建 / 更新 List)       | Persona Agent 种子受众投放到 HubSpot Marketing Hub          |
| 2.5     | Custom Object 支持(仅 Enterprise 客户)       | 客户的业务对象有自定义模型时                                |

### 2.7.1 OAuth Marketplace App 工程清单

- [ ] 在 https://developers.hubspot.com/get-started 注册 Developer Account
- [ ] 在 Developer Account 内 "Create app" → 填 OAuth 配置
- [ ] 配置 Scopes(§1.4.3 最小集)+ Redirect URI(`https://platform.example.com/api/v1/oauth/hubspot/callback`)
- [ ] 在平台 `oauth_callback.py` 加 HubSpot 分支(state HMAC + token exchange + refresh logic)
- [ ] 把 client_id 写入 .env(`HUBSPOT_CLIENT_ID`)· client_secret 走 Secret Manager
- [ ] 提交 **App Review**(自助提交,HubSpot 审核 2-4 周)
- [ ] 通过后 listing 到 https://www.hubspot.com/products/marketplace(可选)
- [ ] UI 从"输入 token"变成"一键 Connect"按钮

---

# 附录:速查表与进阶资料

## A.1 接入前客户准备清单(Private App 路径)

```
[ ] 1. 客户已有 HubSpot 付费或免费账户
[ ] 2. 客户内有 Super Admin 权限的人(否则看不到 Private Apps)
[ ] 3. Super Admin 在 HubSpot 创建 Private App
[ ] 4. 勾选必要 scope(crm.objects.contacts.read 至少)
[ ] 5. 复制 pat-xx1-... access token(关闭就再看不到)
[ ] 6. 客户告知自己的 Portal ID(可选,后台 URL 中可见)
[ ] 7. 客户确认 DPA 已列出 ReceptivIQ 为 sub-processor
```

## A.2 常用 REST 端点速查

```http
# 列出 / 读取
GET /crm/v3/objects/contacts?limit=100&properties=...
GET /crm/v3/objects/contacts/{id}
GET /crm/v3/objects/companies?limit=100&properties=name,domain,industry
GET /crm/v3/objects/deals?limit=100&properties=dealname,amount,dealstage

# 创建 / 更新(需 write scope)
POST  /crm/v3/objects/contacts             {"properties": {...}}
PATCH /crm/v3/objects/contacts/{id}        {"properties": {...}}

# 批量
POST /crm/v3/objects/contacts/batch/read   {"inputs": [{"id": "..."}], "properties": [...]}
POST /crm/v3/objects/contacts/batch/upsert {"inputs": [...]}

# 自定义属性 schema
GET /crm/v3/properties/contacts

# Lists
GET  /crm/v3/lists
POST /crm/v3/lists/{listId}/memberships/add {"vids": [12345, 67890]}

# Token refresh(OAuth)
POST /oauth/v1/token  grant_type=refresh_token & refresh_token=... & client_id=... & client_secret=...
```

## A.3 关联文档

- [INTEGRATION-GUIDE-GA4-DV360](./INTEGRATION-GUIDE-GA4-DV360.md) — 同款知识文档模板
- [STACKADAPT-INTEGRATION](./STACKADAPT-INTEGRATION.md) — StackAdapt 接入指南(相同结构)
- [ELT-8-STEP-DESIGN](./ELT-8-STEP-DESIGN.md) — 八步 ELT 框架(HubSpot 走第 1/2/3/5 步)
- [PII-DESIGN-SOLUTION](./PII-DESIGN-SOLUTION.md) — 凭证加密 + PII 边界(token 走 L2,email/name 走 hash)
- [MULTI-TENANT-DB](./MULTI-TENANT-DB.md) — `raw_hubspot_contacts` 在每 Agency 物理库内
- [ARCHITECTURE-AUDIT-2026Q2](./ARCHITECTURE-AUDIT-2026Q2.md) — adapter 当前在 14 个 P1 中位列已实现

## A.4 风险提示

- **API Key 全面废弃**(2022 起): 不要在新代码 / 老博客里复用"hapikey="参数,必须用 Private App / OAuth
- **Private App token 不过期** = 长期凭据,泄漏后影响大;Fernet 加密 + 限定 scope + 定期 rotate(建议季度)
- **Webhook signature 必须验证**(`X-HubSpot-Signature-v3`)否则可被伪造事件
- **OAuth App Review 2-4 周**,Phase 2 切换需要提前排期
- **客户被风控冻结 Portal** → API 全部 401;沟通走 HubSpot Support(SLA 1 工作日)
