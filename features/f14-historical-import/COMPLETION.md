# F-14 历史数据手动导入 完成报告

- **完成时间**：2026-03-31
- **功能分支**：feat/f14-historical-import
- **测试报告**：[test-execution-report](test/test-execution-report.md)

## 功能摘要

实现历史数据 CSV 批量导入功能，支持 meta_ads / ga4 / hubspot 三平台。上传时自动检测平台格式（通过列名特征），规范化字段名后写入 DuckDB raw 表，最大支持 50MB 文件。

## 文件清单

### 新建文件

- `backend/app/services/etl/historical_importer.py` — CSV 解析、平台检测、字段规范化、DuckDB 写入
- `backend/app/schemas/import_schema.py` — ImportResponse Pydantic 模型
- `backend/app/api/v1/imports.py` — POST `/import/upload` 端点（multipart）
- `backend/tests/test_imports.py` — 9 个测试用例，覆盖三平台/自动检测/边界情况/认证

### 修改文件

- `backend/app/api/v1/router.py` — 注册 imports router

## 已知限制 & 后续工作

- [ ] 进度通知（大文件异步导入 + WebSocket 进度推送）
- [ ] 重复数据检测（基于 date + campaign_id 去重）
- [ ] 支持更多平台（tiktok_ads / dv360）
