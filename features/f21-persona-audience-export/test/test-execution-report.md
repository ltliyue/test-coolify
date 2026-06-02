# f21-persona-audience-export 测试执行报告

- **测试时间**：2026-04-02
- **测试环境**：pytest + PostgreSQL + mock SMTP/平台 API
- **测试文件**：`backend/tests/test_audience_export.py`

## 执行结果

| 测试用例                                   | 结果    | 说明                            |
| ------------------------------------------ | ------- | ------------------------------- |
| test_translator_strips_pii_fields          | ✅ 通过 | email/phone/name PII 被移除     |
| test_translator_empty_psychographics_warns | ✅ 通过 | 空数据返回 warning              |
| test_translator_meta_format                | ✅ 通过 | Meta targeting spec 格式正确    |
| test_translator_dv360_format               | ✅ 通过 | DV360 audience spec 格式正确    |
| test_translator_invalid_platform           | ✅ 通过 | 无效平台抛 ValueError           |
| test_meta_client_mock                      | ✅ 通过 | Meta mock 返回 audience ID      |
| test_dv360_client_mock                     | ✅ 通过 | DV360 mock 返回 segment ID      |
| test_dv360_client_invalid_advertiser       | ✅ 通过 | SSRF 防护（advertiser_id 验证） |
| test_export_preview                        | ✅ 通过 | 预览返回 targeting_spec         |
| test_export_preview_invalid_platform       | ✅ 通过 | 400 错误处理                    |
| test_create_export                         | ✅ 通过 | 导出创建 pending 记录           |
| test_create_export_nonexistent_persona     | ✅ 通过 | 404 错误处理                    |
| test_list_persona_exports                  | ✅ 通过 | 导出历史查询                    |

## 测试汇总

- **通过**：13/13
- **失败**：0

## 合规验证

- ✅ Translator 显式过滤 Level 2+ PII 字段（email/phone/name/ip/device_id）
- ✅ targeting_spec 仅含 Level 0 聚合属性
- ✅ 所有端点带 audit_simple() 审计
- ✅ 凭证从 Credential Vault 解密获取
- ✅ error_message 仅保留异常类型名

## 总结

13 个用例全部通过，PII 过滤逻辑经 unit test 重点验证。真实 Meta/DV360 API 调用需有效凭证，生产环境需单独 smoke test。
