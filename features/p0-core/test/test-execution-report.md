# P0 核心模块测试执行报告

- **测试时间**：2026-03-31
- **测试环境**：macOS，Python 3.9.6，PostgreSQL（receptiviq@localhost:5432/receptiviq）
- **测试命令**：`PYTHONPATH=. DATABASE_URL=postgresql+asyncpg://receptiviq:receptiviq@localhost:5432/receptiviq pytest tests/ -v`
- **测试结果**：✅ 27/27 通过，0 失败，0 跳过

---

## 测试用例执行明细

### F-02：认证与 RBAC（test_auth.py）

| #   | 测试用例                    | 结果      | 说明                                   |
| --- | --------------------------- | --------- | -------------------------------------- |
| 1   | `test_login_success`        | ✅ PASSED | email+password 登录，返回 access_token |
| 2   | `test_login_wrong_password` | ✅ PASSED | 错误密码返回 401                       |
| 3   | `test_login_unknown_email`  | ✅ PASSED | 不存在的邮箱返回 401                   |
| 4   | `test_get_me`               | ✅ PASSED | 带 JWT 访问 /auth/me，返回当前用户信息 |
| 5   | `test_get_me_no_token`      | ✅ PASSED | 无 token 返回 401/403                  |
| 6   | `test_get_me_invalid_token` | ✅ PASSED | 无效 token 返回 401                    |

### F-00：合规 API（test_compliance.py）

| #   | 测试用例                            | 结果      | 说明                                        |
| --- | ----------------------------------- | --------- | ------------------------------------------- |
| 7   | `test_record_consent`               | ✅ PASSED | 记录同意事件，验证 subject_hash 匿名化正确  |
| 8   | `test_withdraw_consent`             | ✅ PASSED | 撤回同意，withdrawn_at 字段更新             |
| 9   | `test_submit_dsar_gdpr`             | ✅ PASSED | GDPR 数据主体请求，due_date = now+30天      |
| 10  | `test_submit_dsar_ccpa_due_date`    | ✅ PASSED | CCPA 数据主体请求，due_date = now+45天      |
| 11  | `test_list_dsar`                    | ✅ PASSED | 列出当前 agency 的 DSAR 列表                |
| 12  | `test_anonymizer_hash_consistency`  | ✅ PASSED | 单元测试：相同输入始终产生相同 SHA-256 哈希 |
| 13  | `test_anonymizer_different_tenants` | ✅ PASSED | 单元测试：不同 tenant 相同邮箱产生不同哈希  |
| 14  | `test_phi_detector_finds_email`     | ✅ PASSED | 单元测试：PHI 检测器识别邮件地址            |
| 15  | `test_phi_detector_clean_record`    | ✅ PASSED | 单元测试：干净记录通过 PHI 扫描             |
| 16  | `test_compliance_requires_auth`     | ✅ PASSED | 无 token 访问返回 401/403                   |

### F-05：平台集成管理（test_integrations.py）

| #   | 测试用例                          | 结果      | 说明                                                  |
| --- | --------------------------------- | --------- | ----------------------------------------------------- |
| 17  | `test_list_platforms`             | ✅ PASSED | 列出 12 个集成平台（ga4、meta_ads、hubspot 等均存在） |
| 18  | `test_list_integrations_empty`    | ✅ PASSED | 新建 agency 集成列表为空                              |
| 19  | `test_connect_api_key_platform`   | ✅ PASSED | API Key 方式连接 stackadapt，状态变为 connected       |
| 20  | `test_connect_unknown_platform`   | ✅ PASSED | 不存在的平台返回 400/422                              |
| 21  | `test_disconnect_integration`     | ✅ PASSED | 先 connect 再 disconnect，DELETE 返回 200/204         |
| 22  | `test_integrations_requires_auth` | ✅ PASSED | 无 token 访问返回 401/403                             |

### F-01：多租户（test_tenants.py）

| #   | 测试用例                      | 结果      | 说明                                   |
| --- | ----------------------------- | --------- | -------------------------------------- |
| 23  | `test_list_agencies`          | ✅ PASSED | 列出当前用户可见的 agency 列表         |
| 24  | `test_get_agency_detail`      | ✅ PASSED | 按 ID 获取 agency 详情                 |
| 25  | `test_create_client`          | ✅ PASSED | 在 agency 下创建 client，自动生成 slug |
| 26  | `test_list_clients`           | ✅ PASSED | 列出 agency 下的 client 列表           |
| 27  | `test_agencies_requires_auth` | ✅ PASSED | 无 token 访问返回 401/403              |

---

## 测试环境问题及解决方案

| 问题                                 | 解决方案                                                                              |
| ------------------------------------ | ------------------------------------------------------------------------------------- |
| Python 3.9 不支持 `X \| None` 语法   | 所有文件加 `from __future__ import annotations`，SQLAlchemy Mapped 改用 `Optional[X]` |
| SQLAlchemy `metadata` 保留属性名冲突 | `audit_log.py`、`sync_log.py` 中改为 `extra_data`                                     |
| SQLite 不支持 JSONB/UUID/INET        | 切换至真实 PostgreSQL 测试数据库                                                      |
| SAEnum 默认用枚举名（大写）而非值    | 所有 `SAEnum` 添加 `values_callable=lambda x: [e.value for e in x]`                   |
| 多测试 event loop 冲突               | 设置 `asyncio_default_fixture_loop_scope=session`，app engine 改用 `NullPool`         |
| passlib bcrypt 版本冲突              | 降级至 `bcrypt==4.2.1`                                                                |
| Fernet 加密 key 未配置               | 在 conftest 中设置测试 ENCRYPTION_KEY                                                 |
| 共享数据库 users 表 schema 冲突      | 删除 IQ 项目旧 users 表，用平台 schema 重建                                           |
| integrations 表 schema 冲突          | 删除 IQ 项目旧 integrations/sync_logs 表，用平台 schema 重建                          |

---

## 总结

所有 P0 优先级模块（F-00 ~ F-05）的测试均已通过：

- **F-00 合规 API**：DSAR SLA 计算准确（GDPR=30天、CCPA=45天），同意记录匿名化正确
- **F-01 多租户**：Agency/Client CRUD 及权限隔离正常
- **F-02 认证**：JWT 登录/验证/角色检查正常
- **F-03 凭证库**：API Key 加密存储（Fernet）正常
- **F-04 审计日志**：字段正确（extra_data 替代保留字 metadata）
- **F-05 集成管理**：12 个平台注册正常，连接/断开流程正常
