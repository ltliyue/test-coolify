# p0-core 设计文档

## 架构概览

```
Request → CORS → SecurityHeaders → SessionGuard → RequestLogging
       → Router → get_current_user (JWT + agency_id)
       → Handler → Agency-scoped query
       → audit_simple() → Response
```

## 核心模块

| 模块       | 文件                                                       | 要点                                               |
| ---------- | ---------------------------------------------------------- | -------------------------------------------------- |
| 多租户     | `models/agency.py` + `models/client.py`                    | UUID PK, agency_id FK，slug 唯一约束               |
| 认证       | `core/security.py` + `api/v1/auth.py`                      | JWT + jti Redis 黑名单，bcrypt 密码                |
| 依赖注入   | `core/deps.py`                                             | get_current_user / get_portal_user / get_agency_id |
| 凭证保险库 | `core/encryption.py` + `models/credential.py`              | Fernet 对称加密，scopes 数组                       |
| 审计日志   | `core/audit.py` + `models/audit_log.py`                    | INSERT-only 触发器防修改                           |
| 平台集成   | `services/platform_registry.py` + `api/v1/integrations.py` | 12 平台注册表                                      |

## 关键决策

- **JWT**：access 30min + refresh 7d + jti 黑名单（logout 立即撤销）
- **RBAC**：三角色 enum（agency_admin / agency_ops / client_viewer）
- **OAuth CSRF**：HMAC 签名 state + 10 分钟过期（C-01）
- **登录限流**：IP 级 5次/5min → 15min 锁定（M-10）
- **PII 加密**：User.email/full_name Fernet + email_hash 索引查找（M-02/M-03）

## 中间件顺序

外层 → 内层：

1. SecurityHeadersMiddleware
2. HIPAASessionGuard
3. RequestLoggingMiddleware（注入 request_id）
4. CORSMiddleware
