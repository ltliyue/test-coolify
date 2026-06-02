# F-15 字段映射系统 完成报告

- **完成时间**：2026-03-31
- **功能分支**：feat/f15-field-mapping
- **测试报告**：[test-execution-report](test/test-execution-report.md)

## 功能摘要

实现完整的字段映射系统，支持将平台原始字段映射到 24 个标准字段（Canonical Schema），具备版本管理（自动快照）、精确回滚、变换预览和 6 个平台默认模板。从 IQ 项目迁移，适配 Agency 多租户架构（agency_id 替代 tenant_id）。

## 文件清单

### 新建文件

- `backend/app/models/field_mapping.py` — FieldMapping + FieldMappingVersion ORM 模型
- `backend/app/services/field_mapping/canonical_schema.py` — 24 个标准字段（6 类别）
- `backend/app/services/field_mapping/transform.py` — TransformEngine（4 种变换：direct/value_mapping/unit_conversion/formula）
- `backend/app/services/field_mapping/template_loader.py` — 模板加载器
- `backend/app/services/field_mapping/templates/ga4.json` — GA4 默认模板
- `backend/app/services/field_mapping/templates/meta_ads.json` — Meta Ads 默认模板
- `backend/app/services/field_mapping/templates/hubspot.json` — HubSpot 默认模板
- `backend/app/services/field_mapping/templates/tiktok_ads.json` — TikTok Ads 默认模板
- `backend/app/services/field_mapping/templates/dv360.json` — DV360 默认模板
- `backend/app/services/field_mapping/templates/stackadapt.json` — StackAdapt 默认模板
- `backend/app/schemas/field_mapping.py` — 完整 Pydantic 模型套件（9 个 schema）
- `backend/app/api/v1/field_mappings.py` — 10 个 REST 端点
- `backend/tests/test_field_mappings.py` — 14 个测试用例，覆盖 CRUD/版本/回滚/预览/模板
- `infra/migrations/008_field_mapping_agency.sql` — 添加 agency_id FK + platform 列，保留 tenant_id 兼容

### 修改文件

- `backend/app/api/v1/router.py` — 注册 field_mappings router
- `backend/tests/conftest.py` — 添加 field_mapping_versions / field_mappings 到 TRUNCATE 列表

## 已知限制 & 后续工作

- [ ] formula 变换的安全沙箱强化（当前使用 AST 白名单）
- [ ] 跨 Agency 模板共享（公共模板库）
- [ ] 字段映射与 ETL runner 的深度集成（自动应用映射）
