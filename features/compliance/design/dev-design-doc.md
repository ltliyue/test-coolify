# compliance 设计文档

> 权威来源：`features/compliance/architecture.md`（10 节完整设计）

## 架构概览

```
Layer 5: API           — /compliance/dsar + /consent + /audit
Layer 4: Middleware    — SessionGuard + PHIDetector + audit_simple
Layer 3: Service       — Anonymizer + RetentionEngine + DSARService
Layer 2: Data          — consent_records + dsar_requests + audit_logs + retention_policies
Layer 1: Infrastructure — TLS 1.3 + AES-256 + per-tenant key
```

## 核心文件

| 文件                               | 职责                                                                        |
| ---------------------------------- | --------------------------------------------------------------------------- |
| `core/compliance/anonymizer.py`    | hash_identifier / truncate_ip / mask_email / anonymize_record_for_warehouse |
| `core/compliance/phi_detector.py`  | HIPAA Safe Harbor 18 类扫描 + deidentify_safe_harbor                        |
| `core/compliance/session_guard.py` | 15 分钟超时中间件（Redis + LRU fallback）                                   |
| `core/pii_crypto.py`               | Fernet 加密 email/name + SHA-256 email_hash                                 |
| `core/audit.py`                    | record_audit_event / audit_simple（INSERT-only）                            |
| `api/v1/compliance.py`             | DSAR + Consent API（5 端点）                                                |

## 数据表

- `consent_records` — subject_hash + purpose + granted + ip_truncated
- `dsar_requests` — subject_email_hash + request_type + regulation + due_date
- `audit_logs` — BigSerial PK + INSERT-only + contains_phi + extra_data JSONB
- `retention_policies` / `breach_incidents` / `business_associate_agreements`

## 关键决策

- 审计日志使用 BigSerial（非 UUID），性能优先
- DSAR subject 存 email_hash 而非明文（C-03）
- IP 地址自动 /24 截断（anonymizer 识别字段名包含 "ip"）
- HIPAA session 超时降级策略：Redis 不可用时切到内存 LRU

## 合规审计历史

4 轮审计共 56 项发现已全部修复，见 DEV-FRAMEWORK.md §F-00。
