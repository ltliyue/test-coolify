# F-16 客户门户 完成报告

- **完成时间**：2026-03-31
- **功能分支**：feat/f16-client-portal
- **测试报告**：[test-execution-report](test/test-execution-report.md)

## 功能摘要

实现客户门户后端 API，提供 5 个只读端点，为 client_viewer 角色用户提供精简的数据视图。支持白标品牌配置（优先取 client.brand_config，fallback 到 agency），隐藏内部字段（model_used/source/cost），实现仪表板摘要（persona/creative/report 计数联动）。

## 文件清单

### 新建文件

- `backend/app/api/v1/portal.py` — 5 个端点：dashboard/brand/personas/creatives/reports

### 修改文件

- `backend/app/core/deps.py` — 添加 get_current_client_viewer() 和 get_portal_user()
- `backend/app/api/v1/router.py` — 注册 portal router

## 已知限制 & 后续工作

- [ ] 前端 PortalLayout.tsx / ClientDashboard.tsx 组件
- [ ] 白标 CSS 变量动态注入
- [ ] client_viewer 角色的细粒度权限控制
