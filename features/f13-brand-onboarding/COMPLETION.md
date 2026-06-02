# F-13 品牌入驻系统 完成报告

- **完成时间**：2026-03-31
- **功能分支**：feat/f13-brand-onboarding
- **测试报告**：[test-execution-report](test/test-execution-report.md)

## 功能摘要

实现品牌入驻系统，允许 Agency 通过 REST API 读取和更新品牌配置（名称、Logo、颜色、调性、行业等）。配置以 JSONB 格式存储于 `agencies.brand_config` 字段，使用 PATCH 语义合并更新，不覆盖未传字段。

## 文件清单

### 新建文件

- `backend/app/schemas/brand.py` — BrandConfigUpdate / BrandConfigResponse Pydantic 模型
- `backend/app/api/v1/brands.py` — GET/PUT/DELETE `/brands/config` 三个端点
- `backend/tests/test_brands.py` — 7 个测试用例，覆盖读写/PATCH 语义/重置/认证

### 修改文件

- `backend/app/api/v1/router.py` — 注册 brands router

## 已知限制 & 后续工作

- [ ] Logo 图片上传（目前只存 URL，不处理文件上传）
- [ ] 品牌配置变更审计日志
