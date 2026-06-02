# ReceptivIQ — 合规架构设计文档

> **适用法规**：GDPR（欧盟）· CCPA（加州）· HIPAA（美国医疗）
> **版本**：v1.0 | 日期：2026-03-31
> **原则**：Privacy by Design — 合规嵌入架构，而非事后补丁

---

## 一、三大法规核心要求对照

| 要求              | GDPR                        | CCPA            | HIPAA                               |
| ----------------- | --------------------------- | --------------- | ----------------------------------- |
| 数据主体访问权    | ✅ DSAR（30天内响应）       | ✅ 45天内响应   | ✅ PHI访问请求                      |
| 删除权            | ✅ 被遗忘权                 | ✅ 删除权       | ✅ PHI销毁标准                      |
| 数据可携权        | ✅ 机器可读格式导出         | ✅              | —                                   |
| 拒绝数据出售权    | —                           | ✅ Do Not Sell  | —                                   |
| 加密传输          | ✅ 建议TLS1.3               | ✅              | ✅ 强制要求                         |
| 加密静态存储      | ✅ 建议AES-256              | ✅              | ✅ 强制AES-256                      |
| 审计日志          | ✅ 所有数据访问             | ✅              | ✅ 所有PHI访问                      |
| 违规通知          | ✅ 72小时（监管机构）       | ✅ 通知受害者   | ✅ 60天（HHS）                      |
| 数据最小化        | ✅ 只收集必要数据           | ✅              | ✅ 最小必要原则                     |
| 同意管理          | ✅ 明确同意+目的            | ✅ 选择退出机制 | —                                   |
| 第三方协议        | ✅ DPA（数据处理协议）      | ✅ 服务商合同   | ✅ BAA（业务伙伴协议）              |
| 数据本地化        | ✅ 欧盟数据不出境（需合规） | —               | —                                   |
| 自动退出          | —                           | —               | ✅ 15分钟会话超时                   |
| De-identification | ✅ 匿名化/假名化            | ✅              | ✅ Safe Harbor/Expert Determination |

---

## 二、数据分级策略（Data Classification）

所有数据字段必须在系统中打标签，决定加密、访问控制、保留策略。

```
Level 0 — Public（公开）
  示例：平台名称、活动名称、汇总指标
  策略：无特殊限制

Level 1 — Internal（内部）
  示例：租户配置、系统日志、非个人化报告
  策略：内部访问控制

Level 2 — Confidential · PII（个人可识别信息）
  示例：用户邮件、姓名、IP地址、Cookie ID、设备指纹
  适用法规：GDPR + CCPA
  策略：
    - 数据库字段加密（pgcrypto / Fernet）
    - 进入数据仓库前必须哈希/假名化
    - 访问需审计日志
    - 受数据保留策略约束

Level 3 — Restricted · PHI（受保护健康信息）
  示例：健康状况、医疗记录、诊断相关营销数据（医疗客户场景）
  适用法规：HIPAA + GDPR + CCPA
  策略：
    - AES-256 应用层加密（专用密钥）
    - 需签署 BAA 才可处理
    - 15分钟会话超时
    - 严格访问控制（need-to-know）
    - 最高级别审计日志（包含访问原因）
    - 6年数据保留（HIPAA要求）
    - 只有 HIPAA-enabled 客户可启用
```

---

## 三、架构级合规层设计

### 3.1 Privacy by Design — 七大原则落地

```
原则 1：主动预防 → 合规检查嵌入 CI/CD，数据分级在 schema 迁移时强制声明
原则 2：默认隐私 → 新字段默认 Level 1，需显式降级为 Level 0
原则 3：嵌入设计 → 合规不是附加模块，是每个 Service 的内置职责
原则 4：完整功能 → 合规不降低功能，隐私保护与业务价值并行
原则 5：全生命周期 → 数据从采集到销毁都有合规策略
原则 6：可见透明 → 审计日志对客户可查，数据流程对监管可解释
原则 7：尊重用户 → DSAR API 在 SLA 内响应，同意可随时撤回
```

### 3.2 分层合规架构

```
┌────────────────────────────────────────────────────────┐
│  Layer 5: Compliance API                               │
│  /api/v1/compliance/                                   │
│  DSAR（访问/删除/导出）· 同意管理 · 违规通知          │
├────────────────────────────────────────────────────────┤
│  Layer 4: Application Middleware                       │
│  ComplianceMiddleware（请求级合规检查）                │
│  PHIDetector · ConsentVerifier · SessionGuard          │
├────────────────────────────────────────────────────────┤
│  Layer 3: Service Layer                               │
│  DataClassifier · RetentionEngine · DSARService        │
│  BreachDetector · AnonymizationService                 │
├────────────────────────────────────────────────────────┤
│  Layer 2: Data Layer                                  │
│  PostgreSQL RLS · 字段加密 · 审计触发器                │
│  retention_policies 表 · consent_records 表            │
├────────────────────────────────────────────────────────┤
│  Layer 1: Infrastructure                              │
│  TLS 1.3 · AES-256 at rest · 密钥管理（per-tenant）   │
│  网络隔离 · 备份加密 · 漏洞扫描                        │
└────────────────────────────────────────────────────────┘
```

---

## 四、数据库级合规设计

### 4.1 合规相关核心表

```sql
-- 同意记录（GDPR 核心）
consent_records:
  user_id, agency_id, client_id,
  purpose,          -- 'analytics' | 'marketing' | 'cross_device' | 'data_sharing'
  granted,          -- true/false
  consent_text,     -- 同意时展示的文本（快照）
  ip_address,       -- 同意时的 IP（GDPR 举证）
  granted_at, withdrawn_at

-- 数据主体请求（DSAR）
dsar_requests:
  id, agency_id, subject_email,
  request_type,     -- 'access' | 'delete' | 'export' | 'rectify' | 'restrict'
  status,           -- 'pending' | 'in_progress' | 'completed' | 'rejected'
  regulation,       -- 'gdpr' | 'ccpa' | 'hipaa'
  due_date,         -- GDPR: 30d, CCPA: 45d, HIPAA: 30d
  completed_at, response_path

-- 数据保留策略
retention_policies:
  data_type, jurisdiction,
  retention_days,   -- 保留天数（0 = 永久）
  purge_strategy    -- 'delete' | 'anonymize' | 'archive'

-- 违规事件记录
breach_incidents:
  id, agency_id, detected_at,
  severity,         -- 'low' | 'medium' | 'high' | 'critical'
  affected_records, affected_users,
  data_types[],     -- 受影响数据类型
  gdpr_notified_at, ccpa_notified_at, hipaa_notified_at,
  hhs_notified_at,  -- HIPAA 要求通知 HHS
  status, resolution_notes

-- BAA 追踪（HIPAA 要求）
business_associate_agreements:
  id, agency_id, vendor_name, vendor_type,
  signed_at, expires_at,
  covers_phi,       -- 是否涉及 PHI
  document_path, status
```

### 4.2 数据保留策略默认值

| 数据类型            | GDPR        | CCPA | HIPAA | 系统默认          |
| ------------------- | ----------- | ---- | ----- | ----------------- |
| 会话/行为日志       | 90天        | 90天 | —     | 90天              |
| 个人识别信息（PII） | 合同期+30天 | —    | —     | 合同期+30天       |
| 营销活动数据        | 3年         | 3年  | —     | 3年               |
| 审计日志            | 3年         | 3年  | 6年   | **6年**（取最长） |
| PHI（健康信息）     | —           | —    | 6年   | 6年               |
| 财务/计费记录       | 7年         | —    | —     | 7年               |
| 系统日志            | 1年         | —    | 1年   | 1年               |

### 4.3 PII 字段加密策略

```
原则：PII 在数据库中永远不以明文存储

实现方式：
  PostgreSQL 层：pgcrypto 对称加密（AES-256-CBC）
  应用层：Fernet 加密（用于凭证等高敏感字段）
  密钥管理：
    - 每个 Agency 独立加密密钥
    - 密钥存储在独立的 Key Management Service（或 HashiCorp Vault）
    - 密钥轮换：每 90 天自动轮换
    - 密钥与数据物理分离

数据仓库（Snowflake）：
  - 所有进入仓库的用户标识符必须哈希（SHA-256 + 盐值）
  - 原始 PII 永远不进入 Snowflake
  - Canonical Events 表的 user_id 字段：存储哈希值，原始值仅在 PostgreSQL
```

---

## 五、ETL 管道合规要求

### 5.1 数据进入仓库前的合规处理流程

```
原始数据采集（平台 API）
        ↓
[1] PHI 扫描器（PHI Detector）
    - 检测 18 类 HIPAA PHI 标识符
    - 发现 PHI → 标记 + 通知 + 拒绝进入仓库（除非客户启用 HIPAA 模式）
        ↓
[2] 同意过滤器（Consent Filter）
    - 仅处理已获授权的用户数据
    - GDPR：需有合法处理依据（同意/合同/合法利益）
    - CCPA：需检查 Do Not Sell 选择退出列表
        ↓
[3] 假名化 / 匿名化（Pseudonymization）
    - 用户标识符（email、user_id）→ SHA-256 哈希（+ 每租户盐值）
    - IP地址 → 截断后3字节（192.168.1.x → 192.168.1.0）
    - 设备指纹 → 单向哈希
        ↓
[4] 数据最小化（Data Minimization）
    - 移除非必要字段（冗余个人信息）
    - 只保留活动分析所需的最小字段集
        ↓
[5] 写入 Snowflake Raw 层
    - 打上数据分级标签（level, jurisdiction, retention_days）
    - 记录数据来源和处理时间
```

### 5.2 HIPAA 特殊处理

```python
# 18 类 PHI 标识符检测
PHI_IDENTIFIERS = [
    "name", "geographic_data", "dates",           # 日期（出生日、入院日等）
    "phone", "fax", "email", "ssn",
    "medical_record_number", "health_plan_number",
    "account_number", "certificate_number",
    "vehicle_identifiers", "device_identifiers",
    "web_urls", "ip_address",                      # 注意：IP 也是 PHI
    "biometric_identifiers", "full_face_photos",
    "unique_identifying_numbers",
]

# 医疗行业客户的额外 ETL 处理：
# 1. 应用 HIPAA Safe Harbor de-identification（移除所有 18 类标识符）
# 2. 或 Expert Determination（统计学方法证明无法重新识别）
# 3. 所有 PHI 访问必须记录完整审计日志（包含访问原因）
```

---

## 六、API 合规端点设计

### 6.1 DSAR API（数据主体权利）

```
POST /api/v1/compliance/dsar
  body: { request_type, subject_email, regulation, verification_token }
  → 创建 DSAR 请求，触发身份核验流程
  SLA: GDPR=30天, CCPA=45天, HIPAA=30天

GET  /api/v1/compliance/dsar/{id}
  → 查询请求状态（pending/in_progress/completed）

DSAR 执行流程（自动化）：
  access  → 查询所有表，生成 JSON 报告，发送加密邮件
  delete  → 删除或匿名化所有记录，保留审计痕迹（GDPR 要求留删除记录本身）
  export  → 生成可移植数据包（JSON/CSV），24小时有效下载链接
  rectify → 标记记录待人工核实和修正
```

### 6.2 同意管理 API

```
POST /api/v1/compliance/consent
  body: { user_id, purpose, granted, consent_text }
  → 记录同意（含 IP、时间戳、同意文本快照）

DELETE /api/v1/compliance/consent/{id}
  → 撤回同意（记录撤回时间，触发相关数据处理暂停）

GET /api/v1/compliance/consent/status?user_id=&purpose=
  → 查询用户当前同意状态
```

### 6.3 违规通知 API（内部）

```
POST /api/v1/compliance/breach
  body: { severity, affected_tables, affected_count, description }
  → 创建违规事件，触发通知流程：
    - 内部：Sentry 告警 + Slack 通知
    - GDPR：生成监管机构通知草稿（72小时内提交）
    - CCPA：生成受影响用户通知列表
    - HIPAA：生成 HHS 通知 + 媒体通知（>500人时）
```

---

## 七、传输与存储加密

### 7.1 传输安全

```
所有 HTTP 请求：TLS 1.3（强制，拒绝 1.2 及以下）
  - HSTS: max-age=31536000; includeSubDomains; preload
  - Certificate Pinning（移动客户端）

内部服务间通信：mTLS（mutual TLS）
  - backend ↔ Airflow
  - backend ↔ Snowflake（Snowflake 原生 TLS）

WebSocket：WSS（TLS 加密）
```

### 7.2 静态存储加密

```
PostgreSQL：
  - 数据库磁盘：AES-256（托管服务商级别）
  - PII 字段：pgcrypto 应用层加密（数据库内可查 = 加密状态）
  - 密钥：每个 Agency 独立密钥，存储在 KMS

Snowflake：
  - 内置 AES-256 + 自动密钥轮换（Tri-Secret Secure 可选）
  - Customer Managed Keys（企业版）

MinIO（文件存储）：
  - SSE-S3（服务端加密）
  - 客户端加密用于 PHI 文件

Redis（缓存）：
  - 不存储 PII/PHI（仅 session token + 非敏感缓存）
  - 加密连接（requirepass + TLS）
```

---

## 八、HIPAA 技术保护措施完整清单

| 保护措施     | 要求                                | 实现方式                    |
| ------------ | ----------------------------------- | --------------------------- |
| 唯一用户标识 | 每用户唯一 ID                       | user_id UUID，禁止共享账户  |
| 紧急访问程序 | Break-glass 流程                    | 独立紧急访问角色 + 自动审计 |
| 自动注销     | PHI 访问后 15 分钟                  | SessionGuard 中间件         |
| 加密/解密    | PHI 字段级加密                      | AES-256 Fernet              |
| 审计控制     | 所有 PHI 访问记录                   | 审计日志表（不可篡改）      |
| 完整性控制   | PHI 不被非法修改                    | 数据库触发器 + 哈希校验     |
| 传输安全     | TLS 加密传输                        | TLS 1.3 强制                |
| 设备管控     | 工作站安全策略                      | 文档化安全策略（非技术）    |
| PHI 去标识化 | Safe Harbor 或 Expert Determination | De-identification Service   |
| BAA 管理     | 所有接触 PHI 的供应商               | BAA 追踪表 + 到期提醒       |

---

## 九、跨境数据传输（GDPR 专项）

```
欧盟客户数据必须满足以下之一才能传输到 EU 以外：

1. 充分性决定（Adequacy Decision）
   - 美国：目前依赖 EU-US Data Privacy Framework（DPF）
   - 检查：https://www.privacyshield.gov/

2. 标准合同条款（SCC）
   - 与美国供应商（Snowflake、OpenRouter、MinIO S3）签署 SCC
   - 保存在 BAA 管理表中

3. 数据本地化选项（企业版）
   - 欧盟客户可选择 EU-hosted Snowflake region
   - 配置：SNOWFLAKE_REGION=eu-west-1

架构要求：
  - 记录每个客户的数据居民地（data_residency 字段）
  - ETL 管道根据 data_residency 路由到对应 Snowflake 区域
  - 跨境传输需记录传输机制（SCC/DPF/adequacy）
```

---

## 十、合规开发检查清单（CI/CD 集成）

每次 PR 合并前自动检查：

```yaml
compliance-checks:
  - name: PII field classification
    check: 所有新增数据库字段必须声明 data_level（0/1/2/3）
    fail: 未声明分级的字段阻断合并

  - name: Encryption check
    check: Level 2/3 字段必须有加密注解
    fail: 未加密的 PII/PHI 字段阻断合并

  - name: Audit log coverage
    check: 访问 PII/PHI 的 API 端点必须触发审计日志
    fail: 缺少审计调用的端点阻断合并

  - name: Retention policy
    check: 新增数据类型必须在 retention_policies 中声明策略
    fail: 无保留策略的数据类型发出警告

  - name: HIPAA session timeout
    check: 涉及 PHI 的视图必须有 15 分钟超时配置
    fail: 违反配置阻断合并

  - name: No PII in logs
    check: 扫描代码确保 PII 字段不被 log.info/print 输出
    fail: 发现 PII 日志输出阻断合并

  - name: No PII in URL params
    check: HIPAA 要求 PHI 不出现在 URL 中
    fail: URL 参数包含可疑 PII 字段阻断合并
```

---

## 十一、合规相关文件清单

### 已实现 ✅

```
features/compliance/
├── architecture.md             ← 本文件
├── COMPLETION.md               ← 合规模块完成报告（4 轮审计）
└── test/
    └── test-execution-report.md ← 测试执行报告

infra/migrations/
├── 011_compliance.sql          ← 合规核心表（consent_records, dsar_requests 等 7 张）
├── 014_remove_pii_columns.sql  ← C-03：去除 consent/DSAR 明文 PII 列
└── 015_encrypt_user_pii.sql    ← M-02/M-03：用户 email_hash 列

backend/app/core/compliance/
├── phi_detector.py             ← PHI 识别（HIPAA Safe Harbor 18 类标识符）
├── anonymizer.py               ← 假名化/匿名化（hash_identifier / truncate_ip / scrub_pii_from_logs）
└── session_guard.py            ← HIPAA 会话超时（Redis + 内存 LRU 双层 fallback）

backend/app/core/
├── pii_crypto.py               ← M-02/M-03：用户 PII Fernet 加密 + email 哈希
├── security.py                 ← C-04：JWT jti + Redis 黑名单撤销
├── audit.py                    ← 审计日志记录（INSERT-only，extra_data JSONB）
└── encryption.py               ← Fernet 对称加密（凭证保险库 + PII）

backend/app/api/v1/
├── compliance.py               ← Consent + DSAR API（M-06 租户隔离，M-04 IP 截断）
├── auth.py                     ← M-10 登录限流 + M-02 email_hash 查找
└── oauth_callback.py           ← C-01 HMAC 签名 state（CSRF 防护）
```

### 待实现 📋（Phase 2/3）

```
features/compliance/
├── dsar-playbook.md            ← DSAR 响应操作手册
├── breach-response-playbook.md ← 违规响应操作手册
├── vendor-baa-register.md      ← BAA 供应商登记表
└── data-flow-map.md            ← 数据流图（GDPR DPIA 输入）

infra/migrations/
└── xxx_rls_policies.sql        ← PostgreSQL Row-Level Security 策略

backend/app/core/compliance/
├── classifier.py               ← 数据分级（当前通过注释和文档标注）
└── consent.py                  ← 同意管理工具类（当前逻辑在 API 层）

backend/app/services/compliance/
├── dsar_service.py             ← DSAR 自动化处理（access/delete/export）
├── retention_engine.py         ← 数据保留 + Celery Beat 自动清理
├── breach_detector.py          ← 违规检测 + 多法规通知
└── transfer_guard.py           ← GDPR 跨境数据传输控制
```
