# 客户账号准备清单(Client Account Provisioning Checklist)

> **用途**:项目 kickoff 时交付给客户的清单,列出客户需要**自行创建 / 提供 / 授权访问**的全部三方账号。
> **版本**:v2 · 2026-05-11
> **变更说明**:v2 简化为单表结构,聚焦"客户实际要做的事",由 Dev Team 自理项移至附录。
> **填表方式**:客户每完成一项,在 ☑️ 列打勾 + 填写交付日期;完整凭证投递到共享密码保险库(1Password Teams / Bitwarden Org)。
>
> ⚠️ **不要通过邮件 / 微信 / Slack 明文发送任何凭证**。

---

## 角色定义

| 角色                     | 说明                          | 谁来负责                    |
| ------------------------ | ----------------------------- | --------------------------- |
| **Agency**(签约方)       | 营销代理公司,本平台的直接客户 | 客户自身                    |
| **Brand Client**(品牌方) | Agency 服务的下级品牌客户     | 由 Agency 邀请加入,自行授权 |
| **Dev Team**             | ReceptivIQ 开发团队           | 我方                        |

---

## 优先级图例

- 🔴 **P0** — 项目开发必须,缺一项就阻塞下一阶段
- 🟡 **P1** — 上线前必须,开发阶段可用 mock / 试用账号
- 🟢 **P2** — 后续阶段(HIPAA / Phase 3)再要

---

## 主清单(19 项)

| ☑️  | 服务                              | 客户操作                                                                                                                                          | 交付物                                                                                                 | 优先级            | 备注                                                                                             |
| --- | --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ | ----------------- | ------------------------------------------------------------------------------------------------ |
| ☐   | **GitHub Organization**           | 创建组织(如 `agency-xyz`)或提供已有组织名                                                                                                         | 邀请 Dev Team(Maintain 或 Admin)                                                                       | 🔴 P0             | —                                                                                                |
| ☐   | **Neon**(PostgreSQL 托管)         | 注册 [neon.tech](https://neon.tech)                                                                                                               | 邀请 Dev Team · Project 创建权限 · 开发 + 测试两套环境的 DB 连接串(`postgresql://...?sslmode=require`) | 🔴 P0             | 业务库,开发与测试环境分离                                                                        |
| ☐   | **Render**                        | 注册 [render.com](https://render.com),开 Team 账户                                                                                                | Owner 邮箱 + 邀请 Dev Team 为 Admin                                                                    | 🟡 P1             | 项目用 `render.yaml` 一键部署                                                                    |
| ☐   | **OpenRouter**                    | 注册 [openrouter.ai](https://openrouter.ai),充值预付 $50 起                                                                                       | API Key(`sk-or-v1-...`)                                                                                | 🔴 P0             | 所有 LLM 流量走它;开发空 Key 自动走 Mock Mode                                                    |
| ☐   | **Anthropic Console**(HIPAA 场景) | 申请 Anthropic Enterprise + BAA 签署                                                                                                              | 直接 Anthropic API Key                                                                                 | 🟢 P2             | 仅当 Agency 服务医疗类 Brand Client 时需要                                                       |
| ☐   | **Sentry**                        | 注册 [sentry.io](https://sentry.io) Team plan                                                                                                     | 邀请 Dev Team 成员                                                                                     | 🟡 P1             | 错误监控;开发空 DSN 自动跳过                                                                     |
| ☐   | **Langfuse**(Cloud 或自托管)      | 注册 [langfuse.com](https://langfuse.com)                                                                                                         | 邀请 Dev Team 成员                                                                                     | 🟡 P1             | LLM 调用 tracing                                                                                 |
| ☐   | **Experian**                      | Experian Audience Engine 后台或销售经理处获取 API 凭证                                                                                            | API Key + Customer ID(**或数据导出文件**)                                                              | 🟡 P1             | ⚠️ **客户暂无账号,需要 Dev Team 提供数据支持方案**(短期:接受 CSV/Parquet 数据导出;长期:开通 API) |
| ☐   | **Google Cloud Console**          | 创建项目 → 启用 Google Analytics Data API → 配 OAuth 同意页 → 创建 OAuth 2.0 Client(Web)                                                          | 邀请 Dev Team 成员(给 Admin 权限)· Client ID + Client Secret                                           | 🔴 P0             | GA4 + Google 用户登录共用此项目                                                                  |
| ☐   | **Meta for Developers**           | 注册 [developers.facebook.com](https://developers.facebook.com),创建 App(类型 `Business`),开启 Marketing API                                      | 邀请 Dev Team 成员(Admin)· App ID + App Secret                                                         | 🔴 P0             | Meta Ads 数据 + 受众导出                                                                         |
| ☐   | **HubSpot Developer**             | 注册 [developers.hubspot.com](https://developers.hubspot.com),创建 App,申请 `crm.objects.contacts.read` / `.deals.read` / `crm.lists.read` Scopes | 邀请 Dev Team 成员(Admin)· Client ID + Client Secret                                                   | 🔴 P0             | HubSpot CRM 数据同步                                                                             |
| ☐   | **TikTok for Business**           | 注册 [business-api.tiktok.com](https://business-api.tiktok.com),申请 Marketing API 接入                                                           | 邀请 Dev Team 成员(Admin)· App ID + Secret                                                             | 🟡 P1             | TikTok 广告数据;Marketing API 邀请制,提前 1-3 周申请                                             |
| ☐   | **DV360**(Display & Video 360)    | Google Ads / DV360 后台生成 Service Account JSON 或 API Key + 提供 Advertiser ID                                                                  | 如有运营团队,邀请 Dev Team(Admin)· API Key / Service Account JSON + Advertiser ID                      | 🟡 P1             | 需 GCP 项目启用 DV360 API                                                                        |
| ☐   | **StackAdapt**                    | 后台 → Settings → API Access → Generate Key                                                                                                       | 如有运营团队,邀请 Dev Team(Admin)· API Key                                                             | 🟡 P1             | —                                                                                                |
| ☐   | **LiveRamp**                      | LiveRamp Console → API Credentials                                                                                                                | 如有运营团队,邀请 Dev Team(Admin)· API Key                                                             | 🟡 P1             | 身份解析 + 分段匹配率(双向使用,详见 `ARCHITECTURE-DIAGRAM.md` LiveRamp 章节)                     |
| ☐   | **Google Ads**                    | Google Ads API Center 申请开发者 token + 在 GCP 同项目配 OAuth                                                                                    | 如有运营团队,邀请 Dev Team(Admin)· Developer Token + Client ID + Client Secret + Customer ID           | 🟡 P1             | 区别于 GA4,处理"日常活动健康检查"                                                                |
| ☐   | **Salesforce**                    | Salesforce Setup → App Manager → 创建 Connected App,启用 OAuth                                                                                    | 如有运营团队,邀请 Dev Team(Admin)· Consumer Key + Consumer Secret + Sandbox / Prod URL                 | 🟡 P1             | "Start with Hubspot, Salesforce, and Oracle's Netsuite"                                          |
| ☐   | **Oracle NetSuite**               | NetSuite SuiteCloud → Integration → Token-Based Auth(TBA)                                                                                         | 如有运营团队,邀请 Dev Team(Admin)· Account ID + Consumer Key/Secret + Token ID/Secret                  | 🟢 P2             | —                                                                                                |
| ☐   | **PlacerIQ**                      | PlacerIQ CSM 处申请 API 访问                                                                                                                      | 如有运营团队,邀请 Dev Team(Admin)· API Key + Org ID                                                    | 🔴 **P0**(已升级) | "Quorum & PlacerIQ" — 位置情报;Persona Agent 关键差异化输入                                      |

---

## ⚠️ 特别说明

### Experian — 数据支持替代方案

客户当前**无 Experian 账号**。短期方案:

1. **由客户从 Experian 销售经理处获取一次性受众数据导出**(CSV / Parquet 格式)
2. Dev Team 编写**离线导入器**(`backend/app/services/etl/historical_importer.py` 扩展),把数据落入 `raw_experian` 表
3. 跳过 OAuth / API Key 集成,后续如客户开通 API 再切到实时同步

需要客户协调销售经理给出**字段清单 + 导出频次**承诺。

### PlacerIQ — 优先级提升至 P0

原因:位置情报数据是 Persona Agent 生成画像的关键差异化输入,缺失将直接影响 MVP demo 效果。

### "如有运营团队,邀请 Dev Team" 的语义

部分广告平台(DV360 / StackAdapt / LiveRamp / Google Ads / Salesforce / NetSuite / PlacerIQ)通常由 Agency 内部运营团队管理。若 Agency 自行运营:

- ✅ 邀请 Dev Team 成员为 Admin,Dev Team 自助生成 Key/Token
- 🔁 若由外包团队代管:Agency 协调外包出具凭证给 Dev Team(走保险库)

---

## 由 Dev Team 自行处理(不需要客户操作)

以下项**不在客户清单**中,由 Dev Team 内部完成,客户**无需操作**:

| 服务                                        | Dev Team 处理方式                                                                         |
| ------------------------------------------- | ----------------------------------------------------------------------------------------- |
| **域名 / SSL**                              | MVP 阶段使用 Render 提供的子域(`<project>.onrender.com`),上线再迁移到客户域名             |
| **Snowflake**                               | 生产环境数据仓库由 Dev Team 在后续阶段评估开通(Phase 2);开发使用 DuckDB 替代,无需客户账号 |
| **AWS Account**                             | S3 用于报告 / 资产存储,可暂用 MinIO(本地)+ 后续接入 Render 自带存储                       |
| **SMTP 服务**                               | Dev Team 用 SendGrid Free / AWS SES Sandbox 起步,生产再迁到 Agency 自有                   |
| **加密密钥**                                | `SECRET_KEY` / `ENCRYPTION_KEY` 由 Dev Team 在 Render Env 生成 + 客户 1Password 双备份    |
| **DPA / BAA 法务文件**                      | 上线前由 Agency 法务团队与各 vendor 签署,Dev Team 提供清单 + 模板                         |
| **LeadRX / Quorum / Adobe Firefly / Canva** | 当前不在客户列表;若后续需要再追加                                                         |

---

## 凭证交付模板(`.env`)

客户全部 P0 项就绪后,把以下凭证一次性投递到共享密码保险库:

```env
# === Source ===
GITHUB_ORG=agency-xyz

# === Hosting & DB ===
RENDER_TEAM=<team-id>
NEON_DEV_URL=postgresql://...?sslmode=require       # dev environment
NEON_TEST_URL=postgresql://...?sslmode=require      # test environment

# === AI ===
OPENROUTER_API_KEY=sk-or-v1-...
ANTHROPIC_API_KEY=<optional, HIPAA tenants only>

# === Monitoring ===
SENTRY_DSN=https://...@...ingest.sentry.io/...
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com

# === Data Sources — OAuth ===
GA4_CLIENT_ID=<google-oauth-client-id>
GA4_CLIENT_SECRET=<google-oauth-client-secret>
GOOGLE_CLIENT_ID=<same as GA4 or separate>
GOOGLE_CLIENT_SECRET=<...>
META_APP_ID=<meta-app-id>
META_APP_SECRET=<meta-app-secret>
HUBSPOT_CLIENT_ID=<hubspot-client-id>
HUBSPOT_CLIENT_SECRET=<hubspot-client-secret>
TIKTOK_APP_ID=<tiktok-app-id>
TIKTOK_APP_SECRET=<tiktok-app-secret>
GOOGLE_ADS_DEVELOPER_TOKEN=<token>
GOOGLE_ADS_CLIENT_ID=<oauth-client-id>
GOOGLE_ADS_CLIENT_SECRET=<oauth-client-secret>
GOOGLE_ADS_CUSTOMER_ID=<customer-id>
SALESFORCE_CONSUMER_KEY=<key>
SALESFORCE_CONSUMER_SECRET=<secret>
SALESFORCE_INSTANCE_URL=https://<your-instance>.my.salesforce.com
NETSUITE_ACCOUNT_ID=<id>
NETSUITE_CONSUMER_KEY=<key>
NETSUITE_CONSUMER_SECRET=<secret>
NETSUITE_TOKEN_ID=<token-id>
NETSUITE_TOKEN_SECRET=<token-secret>

# === Data Sources — API Key ===
DV360_API_KEY=<key>
DV360_ADVERTISER_ID=<id>
STACKADAPT_API_KEY=<key>
LIVERAMP_API_KEY=<key>
PLACERIQ_API_KEY=<key>
PLACERIQ_ORG_ID=<id>

# === Experian (special — data feed or future API) ===
EXPERIAN_DATA_FEED_PATH=<S3 or shared drive path for one-time exports>
# EXPERIAN_API_KEY=<future, when account is provisioned>

# === Generated by Dev Team (don't pre-fill) ===
SECRET_KEY=<generated>
ENCRYPTION_KEY=<generated>
```

---

## 📦 阶段交付时间线

| 阶段                   | 客户应完成                                          | 阻塞 Dev Team 的工作      |
| ---------------------- | --------------------------------------------------- | ------------------------- |
| **Week 0**(签约)       | GitHub Org · Neon(dev+test)· OpenRouter             | 仓库初始化 · 本地开发起步 |
| **Week 1**(开发起步)   | Google Cloud · Meta · HubSpot · PlacerIQ 申请启动   | ETL Adapter 接真实 API    |
| **Week 2**(打通数据流) | TikTok · Salesforce · DV360 · StackAdapt · LiveRamp | 全链路 ETL 联调           |
| **Week 3**(数据增强)   | Google Ads · Experian 数据导出文件 · NetSuite       | 跨源 attribution 验证     |
| **Week 4**(集成测试)   | Sentry · Langfuse · Render                          | 监控与部署验证            |
| **Phase 2 / Phase 3**  | Anthropic BAA · 其他扩展                            | HIPAA 客户支持            |

---

## ⚠️ 常见踩坑提醒

1. **OAuth Redirect URI 不一致** — Developer Console 必须配 **开发 + 生产两套** URL,缺一个就无法登录
2. **HubSpot Scopes 申请不全** — 必须申请 `crm.objects.contacts.read` + `crm.objects.deals.read` + `crm.lists.read`,缺一项 ETL 报 403
3. **Meta App 必须升级为 Business 类型** — Personal App 在 14 天后停止访问 Marketing API
4. **TikTok Marketing API 是邀请制** — 申请 → 审批可能 1-3 周,**Week 0 就要提交**
5. **Neon Free Plan 有 0.5GB 上限 + 自动暂停** — 测试环境可用 Free,**开发环境建议直接 Pro**
6. **Google Cloud OAuth Consent Screen 验证** — App 进入生产模式前需 Google 审核(通常 1-2 周),提前发起
7. **Salesforce Sandbox vs Production URL** — Dev/Test 用 Sandbox(`*.sandbox.my.salesforce.com`),上线切 Production
8. **Experian 数据导出格式** — 务必明确字段清单 + 编码(UTF-8)+ 文件格式(CSV/Parquet)再让对方导出,否则返工

---

## 📋 交付协议

1. 创建共享密码保险库(推荐 **1Password Teams** / Bitwarden Organization)
2. 邀请 Dev Team 邮箱加入(我方提供邮箱列表)
3. 按本清单顺序入库凭证,**每入一项打 ☑️ 并填日期**
4. 凭证全部入库后,Dev Team 拉取并完成环境配置(预计 1 个工作日)
5. **每季度** rotate 一次 P0 凭证(由 Dev Team 主动发起)

---

## 联系人

| 角色                          | 姓名       | 邮箱       |
| ----------------------------- | ---------- | ---------- |
| 客户对接人(Agency Lead)       | ****\_**** | ****\_**** |
| 客户运维(Render / Neon Admin) | ****\_**** | ****\_**** |
| Dev Team Lead                 | ****\_**** | ****\_**** |
| Dev Team 接入工程师           | ****\_**** | ****\_**** |

---

> 文档版本历史
> v1.0 · 2026-05-11 · 初版(多分类版本)
> v2.0 · 2026-05-11 · 简化为单表;PlacerIQ 升 P0;Experian 改走数据支持方案;移除 Dev Team 自理项(域名 / Snowflake / AWS / SMTP / 加密密钥);移除暂不需要的平台(LeadRX / Quorum / Adobe Firefly / Canva)
