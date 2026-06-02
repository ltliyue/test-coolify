# 合规基础层（GDPR · CCPA · HIPAA）完成报告

- **完成时间**：2026-04-01（历经 4 轮合规审计）
- **功能分支**：main（合规嵌入所有模块，非独立分支）
- **测试报告**：[test-execution-report](test/test-execution-report.md)

## 功能摘要

实现三法规（GDPR/CCPA/HIPAA）全栈合规架构，覆盖 5 层合规体系：Compliance API → Application Middleware → Service Layer → Data Layer → Infrastructure。核心实现包括 Consent 同意管理、DSAR 数据主体权利请求、PHI 检测与匿名化、HIPAA 会话超时、PII 加密存储、审计日志、OAuth CSRF 防护、登录限流等 36 项合规控制点。

## 合规审计历史

| 轮次    | 日期       | 修复项 | 重点领域                                       |
| ------- | ---------- | ------ | ---------------------------------------------- |
| 第 1 轮 | 2026-03-31 | 12 项  | 核心表结构 + API 端点基础合规                  |
| 第 2 轮 | 2026-03-31 | 24 项  | PII 加密（M-02/M-03）+ 审计日志 + OAuth CSRF   |
| 第 3 轮 | 2026-04-01 | 4 项   | 深层架构级问题梳理                             |
| 第 4 轮 | 2026-04-01 | 8 项   | 限流 + 内存 fallback + SQL 注入防护 + 输入校验 |

## 已实现合规控制点

### 数据加密与隐私

- M-02/M-03: 用户 email/full_name Fernet 加密存储 + email_hash SHA-256 查找
- C-03: consent_records 去除明文 email，DSAR 使用 subject_email_hash
- M-04: IP 地址截断为 /24 网段（HIPAA Safe Harbor）
- M-08: HubSpot 适配器日志脱敏

### 认证与访问控制

- M-10: IP 级登录限流（5 次/5 分钟 → 锁定 15 分钟）
- C-04: JWT jti + Redis 黑名单撤销（内存 fallback）
- C-01: OAuth state HMAC 签名 + 10 分钟过期
- C-05: 生产启动 SECRET_KEY 强度校验
- M-01: CORS 环境变量控制 + 方法/头部白名单
- M-11: HSTS / X-Frame-Options / nosniff / Referrer-Policy

### HIPAA 专项

- PHI 检测: Safe Harbor 18 类标识符扫描
- M-05: 会话超时（Redis + 内存 LRU 双层 fallback）
- ETL 匿名化: anonymize_record_for_warehouse + CSV 导入 PHI 扫描

### 数据安全

- H-02/H-03: warehouse_client SQL 前缀白名单 + 表名/列名正则
- L-01: Persona.agency_id NOT NULL 强制租户隔离
- L-02: 字段映射 transform config 4KB + 200 条/次限制
- L-03: AuditLog extra_data 字段名修复
- H-06: Airflow 凭证无默认值
- H-10: dbt 子进程错误信息脱敏

## 文件清单

### 新建文件

- `backend/app/core/pii_crypto.py` — 用户 PII Fernet 加密/解密 + email 哈希
- `backend/app/core/compliance/anonymizer.py` — PII 匿名化工具集
- `backend/app/core/compliance/phi_detector.py` — HIPAA PHI 检测器
- `backend/app/core/compliance/session_guard.py` — HIPAA 会话超时中间件
- `backend/app/api/v1/compliance.py` — Consent + DSAR API
- `backend/app/api/v1/oauth_callback.py` — OAuth 回调（HMAC CSRF 防护）
- `infra/migrations/011_compliance.sql` — 7 张合规表
- `infra/migrations/014_remove_pii_columns.sql` — 去除 consent/DSAR 明文 PII
- `infra/migrations/015_encrypt_user_pii.sql` — 用户 email_hash 列
- `features/compliance/architecture.md` — 10 节合规架构设计文档

### 修改文件

- `backend/app/main.py` — C-05 启动校验 + M-01 CORS + M-11 安全头 + SessionGuard
- `backend/app/core/security.py` — C-04 JWT jti 黑名单
- `backend/app/core/config.py` — H-06 Airflow 凭证无默认值
- `backend/app/core/audit.py` — L-03 extra_data 字段名修复
- `backend/app/core/warehouse_client.py` — H-02/H-03 SQL 白名单
- `backend/app/api/v1/auth.py` — M-10 登录限流 + M-02 email_hash 查找
- `backend/app/models/user.py` — M-02/M-03 PII 加密字段
- `backend/app/models/persona.py` — L-01 agency_id NOT NULL
- `backend/app/models/consent.py` — C-03 去除 subject_email
- `backend/app/models/dsar.py` — C-03 subject_email → subject_email_hash
- `backend/app/schemas/auth.py` — UserResponse.from_user() 解密 PII
- `backend/app/schemas/field_mapping.py` — L-02 输入大小限制
- `backend/app/tasks/etl_tasks.py` — H-10 错误信息脱敏
- `backend/app/services/etl/adapters/hubspot.py` — M-08 日志脱敏

## 已知限制 & 后续工作

- [ ] 数据保留定时任务（Celery Beat 按 retention_policies 自动清理/匿名化）
- [ ] BAA 管理 UI（追踪第三方 BAA 状态和到期提醒）
- [ ] 违规事件自动告警（GDPR 72h / HIPAA 60天通知流程）
- [ ] 跨境数据传输控制（EU 数据路由到对应 Snowflake 区域）
- [ ] 每 Agency 独立加密密钥（当前使用全局 ENCRYPTION_KEY）
- [ ] 密钥轮换机制（90 天自动轮换）
