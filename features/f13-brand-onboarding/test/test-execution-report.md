# F-13 品牌入驻 — 测试执行报告

- **测试时间**：2026-03-31
- **测试环境**：macOS，Python 3.9.6，PostgreSQL（receptiviq@localhost:5432/receptiviq）
- **测试命令**：`PYTHONPATH=. DATABASE_URL=postgresql+asyncpg://receptiviq:receptiviq@localhost:5432/receptiviq python3 -m pytest tests/test_brands.py -v`
- **测试结果**：✅ 7/7 通过，0 失败，0 跳过

---

## 测试用例执行明细

### F-13：品牌入驻（test_brands.py）

| #   | 测试用例                               | 结果      | 说明                                                       |
| --- | -------------------------------------- | --------- | ---------------------------------------------------------- |
| 1   | `test_get_brand_config_empty`          | ✅ PASSED | 新 Agency 配置为空，所有字段返回 None                      |
| 2   | `test_update_brand_config`             | ✅ PASSED | PUT 设置 name/industry/brand_voice/primary_color，均持久化 |
| 3   | `test_patch_preserves_existing_fields` | ✅ PASSED | 二次 PUT 只传 tagline，原有 name/industry 不被清空         |
| 4   | `test_reset_brand_config`              | ✅ PASSED | DELETE 后 GET 返回空配置，website_url/name 均为 None       |
| 5   | `test_brand_config_requires_auth`      | ✅ PASSED | 无 JWT 返回 401                                            |
| 6   | `test_brand_config_contains_agency_id` | ✅ PASSED | 响应 agency_id 与当前用户 agency 匹配                      |
| 7   | `test_update_multiple_fields_at_once`  | ✅ PASSED | 一次 PUT 同时更新 8 个字段，全部持久化                     |

---

## 总结

- **GET /brands/config**：读取 Agency.brand_config JSONB 字段，新建 Agency 返回空配置
- **PUT /brands/config**：PATCH 语义合并更新，未传字段不覆盖已有值
- **DELETE /brands/config**：重置为空 `{}`，幂等操作
- **认证**：所有端点均需 JWT，无 token 返回 401
- **全量回归**：92/92 通过（7 新增 + 85 回归），0 失败
