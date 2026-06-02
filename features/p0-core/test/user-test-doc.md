# p0-core 用户测试文档

聚合多个测试文件：`test_auth.py`（6）+ `test_tenants.py`（5）+ `test_integrations.py`（6）+ `test_compliance.py`（10） = 27 用例

## TC-01: 登录与 JWT

| 步骤                      | 预期                   |
| ------------------------- | ---------------------- |
| POST /auth/login 正确凭证 | 200, 返回 access_token |
| POST /auth/login 错误密码 | 401                    |
| GET /auth/me 带 token     | 200, 返回解密 email    |
| GET /auth/me 无 token     | 401                    |

## TC-02: Agency/Client CRUD

| 步骤                        | 预期             |
| --------------------------- | ---------------- |
| GET /agencies               | 200, 仅本 agency |
| POST /agencies/{id}/clients | 201              |
| GET /agencies/{id}/clients  | 200              |

## TC-03: 凭证加密存储

| 步骤                        | 预期           |
| --------------------------- | -------------- |
| POST /credentials           | 201, 返回脱敏  |
| DB 中 encrypted_data 非明文 | ✅ Fernet 加密 |

## TC-04: 平台集成

| 步骤                        | 预期         |
| --------------------------- | ------------ |
| GET /integrations/platforms | 200, 12 平台 |
| POST /integrations connect  | 201          |
| DELETE /integrations/{id}   | 204          |

## TC-05: 审计日志

| 测试                         | 预期               |
| ---------------------------- | ------------------ |
| 任意 API 操作后查 audit_logs | 含对应 action 记录 |
| UPDATE audit_logs            | 触发器阻止         |
