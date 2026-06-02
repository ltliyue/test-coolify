# f14-historical-import 用户测试文档

测试文件：`backend/tests/test_imports.py`（9 用例）

## TC-01: 三平台 CSV 上传

| 平台         | 预期                                    |
| ------------ | --------------------------------------- |
| Meta Ads CSV | 200, records_imported > 0               |
| GA4 CSV      | 200, records_imported > 0               |
| HubSpot CSV  | 200, records_imported > 0（PII 已哈希） |

## TC-02: 自动平台检测

| 输入                              | 预期                |
| --------------------------------- | ------------------- |
| Meta 表头 CSV（无 platform 参数） | 自动识别为 meta_ads |
| GA4 表头 CSV                      | 自动识别为 ga4      |

## TC-03: 不支持平台

| 输入                      | 预期 |
| ------------------------- | ---- |
| POST platform=unsupported | 400  |

## TC-04: 空文件

| 输入   | 预期 |
| ------ | ---- |
| 空 CSV | 400  |

## TC-05: 无法识别格式

| 输入                     | 预期 |
| ------------------------ | ---- |
| 随机表头 CSV 无 platform | 422  |

## TC-06: 认证

| 步骤     | 预期 |
| -------- | ---- |
| 无 token | 401  |

## TC-07: PII 匿名化验证

| 测试                     | 预期                  |
| ------------------------ | --------------------- |
| HubSpot CSV 含真实 email | 仓库中存 hash，非明文 |
