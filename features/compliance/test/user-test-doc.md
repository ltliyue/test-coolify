# compliance 用户测试文档

测试文件：`backend/tests/test_compliance.py`（10 用例）

## TC-01: Consent 记录创建与撤回

| 步骤                                  | 预期               |
| ------------------------------------- | ------------------ |
| POST /compliance/consent granted=true | 201                |
| POST /compliance/consent/withdraw     | 200, granted=false |

## TC-02: DSAR 提交（GDPR / CCPA）

| 步骤                                  | 预期               |
| ------------------------------------- | ------------------ |
| POST /compliance/dsar regulation=gdpr | 201, due_date +30d |
| POST regulation=ccpa                  | 201, due_date +45d |

## TC-03: DSAR 列表

| 步骤                 | 预期                      |
| -------------------- | ------------------------- |
| GET /compliance/dsar | 200, 含当前 agency 的请求 |

## TC-04: Anonymizer 哈希一致性

| 测试                       | 预期     |
| -------------------------- | -------- |
| 相同 email + salt 哈希两次 | 结果相同 |
| 不同租户 salt              | 结果不同 |

## TC-05: PHI 检测

| 测试                | 预期          |
| ------------------- | ------------- |
| 含 email 字段的记录 | has_phi=true  |
| 纯聚合指标记录      | has_phi=false |

## TC-06: 未认证访问

| 步骤                              | 预期 |
| --------------------------------- | ---- |
| 无 token 请求所有 compliance 端点 | 401  |
