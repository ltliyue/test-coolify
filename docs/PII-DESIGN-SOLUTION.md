# PII 设计解决方案（Plaintext PII Storage & Access）

> 状态：针对客户两个反馈问题的正式回应 · 与 [PSD-TECHNICAL-SOLUTION §3.3 / §3.4 / §3.5](./psd/technical-solution.md) 对应
> 适用范围：Raw PII-Segregated Lake 的隔离强度认定 + 明文 PII 的存放位置与访问路径
> 决策状态：✅ 推荐方案（已并入 TSD v3）

---

## 1. 客户问题回顾

### Q1 · Raw PII-Segregated Lake 是 soft isolation 还是 hard isolation？

> Does "Raw PII-segregated Lake" mean that PII and non-PII data reside in the same lake, separated only through soft isolation mechanisms such as partitioning or schema separation? Can this soft isolation pass the four compliance audits (GDPR / CCPA / HIPAA / SOC 2)?

### Q2 · 下游 Pillar 需要明文 PII，明文 PII 放在哪？

> We understand "Processed Lake" as containing all raw data in a unified format, with PII data de-identified. However, several downstream Pillars (lookalike modeling, Meta Custom Audience upload, GDPR data subject location, etc.) require plaintext PII as input. Where is this plaintext PII expected to reside?

---

## 2. 答复摘要（TL;DR）

| 问题                        | 答复                                                                                                                                                                                                            |
| --------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Q1 隔离强度**             | **Hard Isolation**（物理硬隔离），**不是** partition / schema 软隔离。两 Lake 部署在**不同 Neon project**（独立 endpoint + 独立存储 + 独立 KMS + 独立 VPC subnet）。                                            |
| **Q1 合规通过性**           | 满足 GDPR Art.32/25、HIPAA §164.312/308、CCPA/CPRA §1798.81.5、SOC 2 Type II CC6——具体条款对应见 §4 的合规属性矩阵。                                                                                            |
| **Q2 明文 PII 位置**        | **明文 PII 永远只驻留在 Raw PII-Segregated Lake**（per-Agency Neon project，字段级 AES-256 加密 + per-Agency KMS）。**不复制、不迁移、不缓存**到 Processed Lake / AI Brain / Pillar 服务。                      |
| **Q2 下游 Pillar 怎么用？** | 下游通过 **PII Access Service** 这一**唯一受控出口**访问；明文在 service 内存中即时变换为业务允许的产物（平台特定哈希 / DSAR 响应包 / SMTP 邮件），变换结果直接出站到外部，**永不落地**到平台内任何持久化存储。 |

---

## 3. Q1 解决方案 · Hard Isolation 设计

### 3.1 不接受的方案（明确拒绝）

❌ 同一 Neon project / database 内通过 schema 切分（`pii.*` vs `analytics.*`）
❌ 同一存储集群、不同 table prefix（`raw_pii_*` vs `processed_*`）
❌ 同一存储、不同 row-level policy

> **审计原理**：以上方案下两个 "Lake" 共享 **trust boundary**（同一数据库实例、同一进程内存空间、同一服务账号有权访问）。审计师会认定其为**逻辑隔离**而非**物理隔离**，无法独立证明 SOC 2 CC6.6 "physical and logical access controls"，也不满足 HIPAA §164.310 "Physical safeguards" 的可证明性。

### 3.2 推荐方案 · 6 层硬隔离

| #             | 层                                                                                                                                            | 强制实施                                                                                                    | 失败时的检测 |
| ------------- | --------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- | ------------ |
| **1. 存储层** | 两 Lake 部署在**不同的 Neon project**（不同 endpoint、不同存储集群、独立计费）；不允许跨 project 共享 compute                                 | Neon control plane API 巡检：每 Agency 必须有 2 个 project（`{agency}-raw-pii` + `{agency}-processed`）     |
| **2. 加密层** | 两 Lake 各自拥有独立的 KMS 主密钥；Processed Lake 的服务账号**永远不持有** Raw Lake 解密密钥；字段级 Fernet 加密 + per-Agency salt            | KMS audit log 监控：Processed service account 任何对 raw-pii KMS key 的调用 = P0 告警                       |
| **3. 网络层** | Raw PII Lake 处于独立 VPC subnet（私有，不可路由 Internet）；仅 PII Access Service 与 ELT Worker 两类服务可经 mTLS 进入                       | VPC flow logs：任何非白名单源 IP 的 inbound 连接 = 即时阻断 + P0 告警                                       |
| **4. 身份层** | 服务账号最小权限（read-decrypt scoped to one column-set）；跨 Lake 调用必须持 **purpose-bound short-lived token（≤ 15 min）**；不存在长期凭证 | IAM audit：长期 credential 存在 OR token TTL > 15 min = 违规事件                                            |
| **5. 数据层** | 写入 Processed Lake 前必经 `anonymize_record_for_warehouse()`；包含原始 PII 字段的 record 在 schema constraint + 写入 hook 两道拦截下被拒     | DLP 持续扫描 Processed Lake：发现原始 PII 模式（email regex / phone regex / SSN regex）= P0 告警 + 自动隔离 |
| **6. 审计层** | 全部跨 Lake 流量（含 PII Access Service 的每次调用）写 INSERT-only audit_events 表；6 年保留；含 actor / purpose / target_rows / output_hash  | 月度审计师 attestation 报告自动生成；任何 audit 表 UPDATE/DELETE 操作 = 立即上报                            |

### 3.3 跨 Lake 关联（不破坏隔离的前提下）

下游 Processed Lake 的分析查询经常需要"知道这条 transaction 属于哪个 user，但不需要知道 user 是谁"。

**机制**：tokenized join key（不可逆哈希）

```text
Raw PII Lake                          Processed Lake
─────────────                          ───────────────
users                                  events_anonymized
  id                                     id
  email_plaintext (encrypted) ──────┐    user_token  ← 同一 SHA-256(email + agency_salt)
  full_name_plaintext (encrypted)   │    event_type
  pii_token = SHA-256(email + salt) ┘    timestamp
                                         …

JOIN 在 Processed Lake 内：events.user_token = … (可)
JOIN 跨 Lake：明令禁止；用 PII Access Service 取代
```

**关键属性**：

- Processed Lake 持 `user_token`（hash），可在自己内部做 user-level analysis
- 但 `user_token → email` 不可逆——除非走 PII Access Service 的 `dsar_locate_subject` 操作
- 每 Agency salt 独立——A Agency 的 token 在 B Agency 数据中无意义

---

## 4. Q1 合规属性矩阵（4 大法规如何满足）

| 法规 / 条款                                                 | 关键要求                                  | 本方案如何满足                                                   | 证据                                                |
| ----------------------------------------------------------- | ----------------------------------------- | ---------------------------------------------------------------- | --------------------------------------------------- |
| **GDPR Art. 32**（Security of processing）                  | 加密、最小权限、访问控制、定期测试        | 字段级 AES-256 + per-Agency KMS + 6 层隔离 + 季度 pentest        | Neon project list · KMS rotation log · pentest 报告 |
| **GDPR Art. 25**（Privacy by Design）                       | 默认最小数据原则                          | PII 默认不进入分析与 AI 路径；Processed Lake 仅持 token          | DLP 扫描报告 + Schema constraints DDL               |
| **GDPR Art. 17**（Right to erasure）                        | 30 天内响应删除请求                       | DSAR locate via PII Access Service + 删除 hook 联动 audit_events | DSAR audit log + retention 引擎报告                 |
| **HIPAA §164.312(a)**（Access control）                     | 唯一用户标识 + 紧急访问 + 自动登出 + 加密 | 独立服务账号 + 15 分钟 session 超时 + 字段级加密                 | IAM audit + session timeout config                  |
| **HIPAA §164.312(e)**（Transmission security）              | 网络传输加密                              | mTLS 跨段 + TLS 1.3 出站 + 拒绝明文传输                          | VPC flow logs + TLS cert inventory                  |
| **HIPAA §164.308**（Administrative safeguards）             | Workforce clearance + 6 年审计            | 合规审计员独占 Raw Lake 读权；INSERT-only 6 年审计               | audit_events 表 + RBAC matrix                       |
| **HIPAA §164.310**（Physical safeguards）                   | 物理访问控制（包括 cloud 等价）           | 独立 Neon project + 独立 VPC = 等价物理边界                      | Neon project list + VPC topology                    |
| **CCPA / CPRA §1798.81.5**（Reasonable security）           | 加密 + 访问控制 + 销毁规程                | 同 GDPR Art. 32 + retention 引擎                                 | 同上                                                |
| **CCPA §1798.105**（Right to delete）                       | 45 天内响应                               | 同 GDPR Art. 17 路径                                             | DSAR audit log                                      |
| **SOC 2 Type II CC6.1**（Logical access）                   | 身份认证 + 授权 + 监控                    | JWT + scoped purpose-bound token + audit_events                  | 控制矩阵证据                                        |
| **SOC 2 Type II CC6.6**（Logical/physical access controls） | 边界保护 + 网络分段                       | VPC subnet + mTLS + 拒绝跨 trust boundary                        | VPC flow logs + 网络拓扑                            |
| **SOC 2 Type II CC6.7**（Restricted transmission of data）  | 传输加密 + 数据分级                       | TLS 1.3 + 数据分级（L0/L1/L2/L3）+ 出口控制                      | 数据分级文档 + TLS inventory                        |

> **审计师视角**：6 层中任意 3 层是"等价物理控制"（Neon project 分离、KMS 隔离、VPC 隔离），任意 3 层是"程序控制"（purpose-bound token、anonymization hook、INSERT-only audit）；这种"物理 + 程序"双层组合是 SOC 2 Type II 期望的标准模式。

---

## 5. Q2 解决方案 · 明文 PII 的存放与访问

### 5.1 明文 PII 唯一驻留位置

```text
┌──────────────────────────────────────────────────────────────────┐
│        Raw PII-Segregated Lake (per-Agency Neon project)         │
│  ──────────────────────────────────────────────────────────────   │
│  Table: users                                                     │
│    id                  uuid PRIMARY KEY                            │
│    agency_id           uuid NOT NULL                               │
│    email_encrypted     bytea  ← Fernet (AES-256-GCM)              │
│    email_hash          bytea  ← SHA-256(lowercase(email)+salt)    │
│    phone_encrypted     bytea  ← Fernet                            │
│    phone_hash          bytea                                       │
│    full_name_encrypted bytea  ← Fernet                            │
│    ssn_encrypted       bytea  ← Fernet (Regulated tier only)      │
│    address_encrypted   bytea  ← Fernet                            │
│    pii_token           bytea  ← SHA-256(email_hash + agency_salt) │
│                                  ↑ 跨 Lake 关联用的不可逆 token     │
│  ──────────────────────────────────────────────────────────────   │
│  · 表所在 schema: raw_secure                                       │
│  · 字段加密密钥: per-Agency KMS master key (key alias =            │
│    `agency-{id}-pii`)                                              │
│  · 字段级加密粒度: 每一行每一字段独立 nonce + 独立 IV               │
│  · 主键解密权限: 仅 PII Access Service                              │
│  · email_hash / phone_hash 字段可被 PII Access Service 读用于查找  │
│    (例如 WHERE email_hash = SHA-256('john@example.com'+salt))      │
│                                                                    │
└──────────────────────────────────────────────────────────────────┘
                                  │
                  ◄ ─ ─ ─ ─ ─ ─ ─ ┴ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ▶
                  ✗ 复制到 Processed Lake = 拒绝
                  ✗ 缓存在 Pillar 内存 = 拒绝
                  ✗ 经 LLM context = 拒绝
                  ✗ 落盘到日志 = 拒绝
                  ✓ 仅 PII Access Service 可临时持有（内存中）
```

**3 个数据形态共存**（同一条用户记录）：

| 字段              | 形态                              | 用途                                  | 谁能读                                 |
| ----------------- | --------------------------------- | ------------------------------------- | -------------------------------------- |
| `email_encrypted` | 密文（Fernet）                    | 明文还原所需                          | 仅 PII Access Service                  |
| `email_hash`      | SHA-256(lower(email)+salt)        | 跨记录查找同一主体（DSAR / lookup）   | PII Access Service + 合规审计员        |
| `pii_token`       | SHA-256(email_hash + agency_salt) | Processed Lake 跨表 JOIN 不可逆 token | 任何 Agency 内服务（出现在 Processed） |

### 5.2 PII Access Service · 唯一受控出口

```text
                ┌─────────────────── Caller ──────────────────┐
                │ Pillar 服务 / Campaign Manager UI / DSAR 端点 │
                └────────────────┬────────────────────────────┘
                                 │
                                 │ POST /pii-access/operation
                                 │ Headers:
                                 │   Authorization: Bearer <purpose-bound JWT>
                                 │   X-Agency-Id: <uuid>
                                 │   X-Purpose: audience.upload.meta
                                 │   X-Token-Ttl: 900 (= 15 min hard cap)
                                 │
                                 ▼
        ┌───────────────────────────────────────────────────────┐
        │              PII Access Service                       │
        │  ─────────────────────────────────────────────────    │
        │  1) Token verify                                       │
        │     · agency_id 匹配？                                  │
        │     · purpose 在 operation allow-list？                 │
        │     · TTL ≤ 15 min？                                   │
        │     · 请求者 RBAC 角色拥有此 purpose？                  │
        │  2) Load operation impl from allow-list                │
        │     · build_audience_hash_list(input_ids)              │
        │     · dsar_locate_subject(email)                       │
        │     · dsar_export_subject(subject_id)                  │
        │     · liveramp_resolve(seed_list)                      │
        │     · send_notification(subject_id, template)          │
        │     · legal_export(subject_id, case_id)                │
        │  3) Open KMS context (per-Agency master key)            │
        │  4) Stream decrypt → in-memory transform → output       │
        │     · 明文绝不落盘                                       │
        │     · 输出仅含变换后的产物                                │
        │  5) Direct egress (NOT via app stack):                  │
        │     · Meta CA API / DV360 API / SMTP / DSAR JSON file   │
        │  6) Write audit_events row（actor / purpose / target    │
        │     rows / output fingerprint / external_response_id）  │
        └───────────────────────────────────────────────────────┘
                                 │
                                 ▼
                ┌────────────── Outputs ──────────────┐
                │ ✓ SHA-256 哈希列表（Meta CA）          │
                │ ✓ LiveRamp RampID 集合                  │
                │ ✓ DSAR 响应 JSON （直接送到客户邮箱）   │
                │ ✓ 加密的 legal export 包               │
                │ ✗ 明文 PII（永不离开 service 内存）     │
                └─────────────────────────────────────┘
```

**6 个关键安全属性：**

| #   | 属性                     | 强制机制                                                                                                                                  |
| --- | ------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | **明文绝不落盘**         | service 是 stateless container；本地 disk 挂载为 `tmpfs noexec`；日志中 PII 字段自动 redact（`logger filter`）                            |
| 2   | **purpose-bound JWT**    | 每次操作必须携带 `purpose` claim（如 `audience.upload.meta`），与 `operation` 入参一一映射；mismatch = 拒绝                               |
| 3   | **operation allow-list** | service **不暴露通用 SQL**；仅注册的 6 个操作可调用；新增 operation 走 PR review + 安全评审                                               |
| 4   | **行级审计**             | 每条 audit_events 包含：`actor / purpose / agency_id / rows_decrypted / output_fingerprint / external_response_id / latency_ms`；6 年保留 |
| 5   | **Token TTL ≤ 15 min**   | JWT exp 由签发端控制；service 端再校验；任何 TTL > 15 min 的 token 拒绝                                                                   |
| 6   | **Agency 间隔离**        | 每个调用必须有 `X-Agency-Id` 与 token claim 匹配；KMS context per-Agency；service 内部不缓存跨 Agency 状态                                |

### 5.3 下游 Pillar 用例映射

| Pillar / 用例                                 | 需要明文吗                       | 调用的 Operation                                          | 输出                                                  | 明文是否离开 service                           |
| --------------------------------------------- | -------------------------------- | --------------------------------------------------------- | ----------------------------------------------------- | ---------------------------------------------- |
| **Meta Custom Audience 上传**                 | 是（要计算 Meta 特定的 SHA-256） | `build_audience_hash_list(audience_id, platform="meta")`  | Meta CA API 接受的 hash list（经 Meta API 直接上传）  | 否                                             |
| **DV360 Customer Match**                      | 是                               | `build_audience_hash_list(audience_id, platform="dv360")` | DV360 接受的 hash list                                | 否                                             |
| **TikTok / Trade Desk / StackAdapt 受众上传** | 是                               | `build_audience_hash_list(audience_id, platform=<name>)`  | 平台特定 hash                                         | 否                                             |
| **LiveRamp 身份解析**                         | 是（要发明文给 LiveRamp）        | `liveramp_resolve(seed_list_id)`                          | LiveRamp RampID 集合，落 Agency 自己的 Processed Lake | 否（直接 LiveRamp API）                        |
| **Lookalike 建模 (seed list 生成)**           | 间接                             | `build_audience_hash_list` 与上同；模型本身只看 hash      | 平台特定 hash                                         | 否                                             |
| **GDPR / CCPA DSAR 主体定位**                 | 是                               | `dsar_locate_subject(email_or_phone)`                     | 该主体所有 record_id（不含明文）                      | 否                                             |
| **GDPR DSAR 数据导出**                        | 是                               | `dsar_export_subject(subject_id, format="json")`          | DSAR JSON 直接送到 SMTP / SFTP                        | 是（送到主体自己邮箱）— 这是法律要求的合法出站 |
| **CCPA Opt-Out**                              | 是（更新 do_not_sell 标志）      | `dsar_apply_optout(subject_id)`                           | 状态码                                                | 否                                             |
| **法律 / 监管请求**                           | 是                               | `legal_export(subject_id, case_id)`                       | 加密包送到法律团队 secure mailbox                     | 是（合法出站）                                 |
| **Email / SMS 通知**                          | 是                               | `send_notification(subject_id, template_id)`              | SMTP/SMS API 响应 ID                                  | 否（直接走外部 API）                           |
| **Agency 内分析、报表、AI Brain**             | **否**                           | n/a — 使用 `pii_token`                                    | n/a                                                   | n/a                                            |

### 5.4 业务用户视角（UX）

业务团队（Campaign Manager 等）触发"上传受众到 Meta"时，**不会看到明文 PII**：

```text
[ Campaign Manager UI ]
  ↓ 点击 "Upload audience to Meta"
  ↓ 选择 audience segment (audience_id = …)
  ↓ 选择平台 = Meta
  ↓ 提交
                    ↓ frontend → backend
                    ↓ backend signs purpose-bound JWT
                    ↓ purpose = "audience.upload.meta"
                    ↓ POST PII Access Service
                                ↓
                                ↓ (service in-memory transform)
                                ↓ Meta API 响应：success, 1234 hashes uploaded
                                ↓
                    ↑ backend
                    ↑
[ UI 显示 ]
  ✓ "Successfully uploaded 1,234 hashed identities to Meta"
  (用户从未看到任何 email / phone)
```

### 5.5 与 §3.5 共享参考数据策略的关系

§3.5 引入的 **Shared Reference Lake**（Experian / Nielsen / Placer IQ / Quorum 等 B 类数据）按合同**无 individual-level PII**，因此：

- Shared Reference Lake **不参与 PII 边界**——它在第三个 Neon project，独立于 Raw PII Lake 与 Processed Lake
- PII Access Service **不读 Shared Reference Lake**（没必要）
- 共享数据的 license 边界由 §3.5.2 的 license_grants RLS 控制，与 PII 边界正交

---

## 6. 数据流总览图

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ EXTERNAL SOURCES (14 P1)                                                     │
└──────────┬──────────────────────────────────────────────────────────────────┘
           │ TLS 1.3 + OAuth (per-Agency for A 类 / platform for B 类)
           ▼
┌──────────────────────── ELT (Classification Gate) ──────────────────────────┐
│  PHI Detector + PII Classifier                                               │
│   ├─ 含 individual PII 字段 ────►  routed to Raw PII Lake (encrypted)         │
│   ├─ 仅含 hash/token 字段   ────►  routed to Processed Lake                  │
│   └─ B 类共享参考          ────►  routed to Shared Reference Lake             │
└──────────┬──────────┬──────────┬───────────────────────────────────────────┘
           │          │          │
           ▼          ▼          ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ Raw PII Lake     │ │ Processed Lake   │ │ Shared Reference │
│ (per-Agency      │ │ (per-Agency      │ │ Lake             │
│  Neon project)   │ │  Neon project)   │ │ (platform-wide   │
│                  │ │                  │ │  Neon project)   │
│ Fernet + KMS     │ │ pii_token 关联    │ │ no individual PII │
│ encrypted PII    │ │ canonical / marts│ │ license-gated     │
└────┬─────────────┘ └────▲─────────────┘ └────▲─────────────┘
     │ (read-decrypt)      │ (read)             │ (read via FDW)
     │                     │                    │
     ▼                     │                    │
┌─────────────────┐        │                    │
│ PII Access      │        │                    │
│ Service         │────────┘                    │
│                 │                             │
│ in-memory only  │                             │
│ purpose-bound   │                             │
│ allow-list ops  │                             │
└────┬────────────┘                             │
     │ direct egress (NOT via app stack)        │
     │                                          │
     ▼                                          │
┌────────────────────────────┐                  │
│ External                   │                  │
│ · Meta CA API (hashes)     │                  │
│ · DV360 / TikTok / TTD     │                  │
│ · LiveRamp (plaintext OK   │                  │
│   under DPA + IDS contract)│                  │
│ · DSAR subject (SMTP/SFTP) │                  │
│ · Legal team mailbox       │                  │
└────────────────────────────┘                  │
                                                │
                                                │
              Agency Processed Lake ────► JOIN ◄┘
                                          (FDW read-only,
                                           license-gated RLS)
                                                │
                                                ▼
                                        AI Brain / Pillars / Portal
                                        （只看 pii_token + Processed + Shared）
```

---

## 7. 实施清单（PR-by-PR）

| #   | 项                                                                                 | 文件 / 模块                          | 优先级 |
| --- | ---------------------------------------------------------------------------------- | ------------------------------------ | ------ |
| 1   | 拆分 Raw / Processed 为独立 Neon project（per-Agency 两个）                        | `infra/terraform/neon.tf`            | P0     |
| 2   | 字段级 Fernet 加密 helper + per-Agency KMS context                                 | `backend/app/core/pii_crypto.py`     | P0     |
| 3   | `users` 等含 PII 表的 schema 改造（email_encrypted / email_hash / pii_token 三列） | `infra/migrations/0XX_pii_split.sql` | P0     |
| 4   | PII Access Service container（独立部署，stateless，tmpfs 文件系统）                | `services/pii-access/`               | P0     |
| 5   | 6 个 operation 的 allow-list 实现                                                  | `services/pii-access/operations/`    | P0     |
| 6   | purpose-bound JWT 签发 + 校验（≤ 15 min TTL）                                      | `backend/app/core/pii_token.py`      | P0     |
| 7   | `audit_events` 写入 hook（per-row 粒度）                                           | `services/pii-access/audit.py`       | P0     |
| 8   | DLP 持续扫描 Processed Lake（cron + 告警）                                         | `services/dlp-scanner/`              | P0     |
| 9   | Schema constraint + 写入 hook 阻止原始 PII 进 Processed                            | `dbt/macros/forbid_pii_columns.sql`  | P0     |
| 10  | VPC 网络分段配置（Raw PII subnet private）                                         | `infra/terraform/vpc.tf`             | P0     |
| 11  | Pillar UI 改造：所有"上传到 Meta"等操作走 PII Access Service                       | `frontend/src/audiences/`            | P0     |
| 12  | DSAR 端点改造：`/dsar/locate` 与 `/dsar/export` 走 PII Access Service              | `backend/app/api/v1/dsar.py`         | P0     |
| 13  | 合规审计师 RBAC 角色（独占 Raw Lake 读权 via PII Access Service）                  | `backend/app/rbac/`                  | P1     |
| 14  | 季度 pentest 计划（PII Access Service 为重点目标）                                 | 合规计划文档                         | P1     |
| 15  | 监管报告自动生成（GDPR/HIPAA breach SLA 触发器）                                   | `services/compliance-report/`        | P1     |

---

## 8. 与现有 TSD 的关联

本方案是对 PSD-TECHNICAL-SOLUTION §3.3 + §3.4 + §3.5 的**详细化与可落地化**：

| TSD 章节                                        | 本方案对应章节                                          |
| ----------------------------------------------- | ------------------------------------------------------- |
| §3.3 PII Segregation Boundary（Hard Isolation） | §3 + §4（6 层硬隔离 + 4 法规属性矩阵）                  |
| §3.4 PII Access Service                         | §5（明文 PII 存放位置 + 唯一受控出口 + 6 个 operation） |
| §3.5 Shared Reference Strategy                  | §5.5（说明与 PII 边界正交）                             |

**变更建议**：将本文档 §3、§5 的详细图表反向并入 TSD 对应章节（已部分完成），并把本文档作为客户回应附件随 PSD 一并提交。

---

## 9. 客户问题的最终答复（一句话）

> **Q1**：**Hard Isolation**（不是 partition/schema 软隔离）—— 通过独立 Neon project + 独立 KMS + 独立 VPC + purpose-bound token + INSERT-only audit + DLP 扫描的 6 层防护，满足 GDPR / CCPA / HIPAA / SOC 2 Type II 全部条款。
>
> **Q2**：**明文 PII 仅存于 Raw PII-Segregated Lake（字段级 AES-256 加密，per-Agency KMS）**；下游 Pillar（Meta CA / DV360 / LiveRamp / DSAR / 法律请求 / 通知）通过 **PII Access Service** 这一唯一受控出口访问，service 内存中即时变换为合法产物（hash / DSAR 包 / SMTP），明文 PII 永不复制、永不缓存、永不进入 Processed Lake / AI Brain / 业务日志。

---

## 10. 相关文档

- [PSD Technical Solution §3.3](./psd/technical-solution.md#33-pii-segregation-boundaryhard-isolation) — PII 边界正式定义
- [PSD Technical Solution §3.4](./psd/technical-solution.md#34-pii-access-service明文-pii-的受控出口) — PII Access Service 正式定义
- [PSD Technical Solution §3.5](./psd/technical-solution.md#35-数据分类与共享参考数据策略tenant-scoping--shared-reference) — Shared Reference Lake 设计
- [ADR-002 Neon Tenancy](./ADR-002-NEON-TENANCY-OPTIMAL.md) — 仓库选型与隔离决策
- [Network Diagram](./psd/network-diagram.svg) — L3 双 Lake + PII Boundary 中柱可视化
