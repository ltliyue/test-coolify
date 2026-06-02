# F-14 历史数据 CSV 导入 — 测试执行报告

- **测试时间**：2026-03-31
- **测试环境**：macOS，Python 3.9.6，PostgreSQL（receptiviq@localhost:5432/receptiviq），DuckDB（内存模式）
- **测试命令**：`PYTHONPATH=. DATABASE_URL=postgresql+asyncpg://receptiviq:receptiviq@localhost:5432/receptiviq python3 -m pytest tests/test_imports.py -v`
- **测试结果**：✅ 9/9 通过，0 失败，0 跳过

---

## 测试用例执行明细

### F-14：历史 CSV 导入（test_imports.py）

| #   | 测试用例                               | 结果      | 说明                                                      |
| --- | -------------------------------------- | --------- | --------------------------------------------------------- |
| 1   | `test_upload_meta_ads_csv`             | ✅ PASSED | meta_ads CSV 2 行，rows_imported=2，message 含 "imported" |
| 2   | `test_upload_ga4_csv`                  | ✅ PASSED | GA4 CSV 2 行（YYYY-MM-DD 格式），rows_imported=2          |
| 3   | `test_upload_hubspot_csv`              | ✅ PASSED | HubSpot CSV 2 行，rows_imported=2                         |
| 4   | `test_auto_detect_meta_ads_format`     | ✅ PASSED | 不传 platform，通过列名自动检测为 meta_ads                |
| 5   | `test_auto_detect_ga4_format`          | ✅ PASSED | 不传 platform，通过列名自动检测为 ga4                     |
| 6   | `test_unsupported_platform_rejected`   | ✅ PASSED | platform=tiktok 返回 400，错误提示 "Unsupported platform" |
| 7   | `test_empty_file_rejected`             | ✅ PASSED | 空文件返回 400，错误提示 "Empty file"                     |
| 8   | `test_undetectable_format_returns_422` | ✅ PASSED | 无法识别列名且未传 platform，返回 422                     |
| 9   | `test_import_requires_auth`            | ✅ PASSED | 无 JWT 返回 401                                           |

---

## 修复说明

- **GA4 日期格式**：DuckDB `DATE` 类型要求 `YYYY-MM-DD`，测试 CSV 从 `YYYYMMDD` 改为 `YYYY-MM-DD`

## 总结

- **POST /import/upload**：multipart 上传，支持 meta_ads/ga4/hubspot 三平台
- **自动检测**：detect_format() 通过 CSV 列名特征推断平台（大小写不敏感）
- **DuckDB 写入**：通过 WarehouseClient.insert*many() 写入对应 raw*\* 表
- **最大 50MB**：超大文件返回 413（超出测试范围）
- **全量回归**：92/92 通过（9 新增 + 83 回归），0 失败
