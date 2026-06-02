# F-15 字段映射系统 — 测试执行报告

- **测试时间**：2026-03-31
- **测试环境**：macOS，Python 3.9.6，PostgreSQL（receptiviq@localhost:5432/receptiviq）
- **测试命令**：`PYTHONPATH=. DATABASE_URL=postgresql+asyncpg://receptiviq:receptiviq@localhost:5432/receptiviq python3 -m pytest tests/test_field_mappings.py -v`
- **测试结果**：✅ 14/14 通过，0 失败，0 跳过

---

## 测试用例执行明细

### F-15：字段映射系统（test_field_mappings.py）

| #   | 测试用例                                      | 结果      | 说明                                                              |
| --- | --------------------------------------------- | --------- | ----------------------------------------------------------------- |
| 1   | `test_list_field_mappings_empty`              | ✅ PASSED | 新 Agency 映射列表为空数组                                        |
| 2   | `test_create_field_mapping`                   | ✅ PASSED | POST 创建 ga4 映射，返回 201，current_version=1，is_active=true   |
| 3   | `test_get_field_mapping_by_id`                | ✅ PASSED | GET /{id} 返回正确映射                                            |
| 4   | `test_update_field_mapping_bumps_version`     | ✅ PASSED | PUT 更新后 current_version 从 1 升至 2                            |
| 5   | `test_delete_field_mapping_soft`              | ✅ PASSED | DELETE 软删除，列表不再返回，GET /{id} 返回 404                   |
| 6   | `test_list_versions`                          | ✅ PASSED | 创建+更新后 /versions 返回 2 个快照，降序排列                     |
| 7   | `test_rollback_to_version`                    | ✅ PASSED | 回滚到 v1，创建 v3，mapping_config 与 v1 相同                     |
| 8   | `test_preview_transform`                      | ✅ PASSED | POST /preview 返回 source/transformed/warnings 三字段             |
| 9   | `test_get_canonical_schema`                   | ✅ PASSED | /canonical-schema 返回非空列表，含 name/type/category/description |
| 10  | `test_get_platform_raw_fields`                | ✅ PASSED | /platforms/ga4/raw-fields 返回 GA4 原始字段列表                   |
| 11  | `test_get_default_template`                   | ✅ PASSED | /platforms/meta_ads/default-template 返回 platform+mappings       |
| 12  | `test_invalid_platform_returns_404`           | ✅ PASSED | 不存在的平台返回 404                                              |
| 13  | `test_field_mapping_requires_auth`            | ✅ PASSED | 无 JWT 返回 401                                                   |
| 14  | `test_list_field_mappings_filter_by_platform` | ✅ PASSED | ?platform=ga4 只返回 GA4 映射，过滤 meta_ads                      |

---

## 修复说明

- **MappingEntry 字段名**：schema 中使用 `target_field`（非 `canonical_field`），无 `transform_type` 顶层字段，测试已修正

## 总结

- **10 个 API 端点**：list/create/get/update/delete + versions list/rollback + preview + canonical-schema + platform templates
- **版本管理**：每次 PUT 自动创建 FieldMappingVersion 快照，支持精确回滚
- **软删除**：DELETE 设置 is_active=False，不物理删除，支持审计
- **TransformEngine**：支持 direct/value_mapping/unit_conversion/formula 四种变换类型
- **6 个平台模板**：ga4/meta_ads/hubspot/tiktok_ads/dv360/stackadapt
- **全量回归**：92/92 通过（14 新增 + 78 回归），0 失败
