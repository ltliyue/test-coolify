# f14-historical-import 设计文档

## 架构概览

```
POST /import (multipart CSV + platform?)
  ↓
HistoricalImporter.parse_csv()
  ↓ (platform=None 时自动检测)
auto_detect_platform() — 基于表头字段匹配
  ↓
CSV 行 → 字段映射（canonical schema）
  ↓
PHI 扫描 + 匿名化（复用 ETL runner 合规层）
  ↓
warehouse.insert_many(raw_table, rows)
  ↓
返回 ImportResponse (records_imported, platform_detected, errors)
```

## 核心文件

| 文件                                  | 职责                               |
| ------------------------------------- | ---------------------------------- |
| `services/etl/historical_importer.py` | CSV parse + auto-detect + 合规处理 |
| `api/v1/imports.py`                   | POST /import 端点                  |
| `schemas/import_schema.py`            | ImportResponse                     |

## 平台自动检测

基于表头字段特征匹配：

| 平台     | 标志性字段                                          |
| -------- | --------------------------------------------------- |
| GA4      | `sessions`, `pageviews`, `bounceRate`               |
| Meta Ads | `campaign_name`, `spend`, `impressions`, `adset_id` |
| HubSpot  | `email`, `lifecyclestage`, `createdate`             |

无法识别时返回 422（Unprocessable Entity）。

## 关键决策

- **复用 ETL 合规层**：不重复实现匿名化/哈希，调用相同的 anonymizer
- **同步处理**：小文件同步处理（< 50MB），大文件建议分批上传
- **无文件持久化**：解析完成立即释放，不存入 MinIO
- **字段映射复用**：使用 field_mapping/templates/{platform}.json

## 错误处理

| 场景           | 响应             |
| -------------- | ---------------- |
| 空文件         | 400              |
| 不支持平台     | 400              |
| 自动检测失败   | 422              |
| 部分行解析失败 | 200, errors 数组 |
