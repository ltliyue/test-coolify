# f16-client-portal 设计文档

## 架构概览

```
Client User Login → get_portal_user 依赖
  ├── role=client_viewer   → 仅看自己 client 的数据
  └── role=agency_admin/ops → 看所有 client（Staff View）

5 个只读端点：
GET /portal/dashboard  — 汇总指标（campaigns + budgets）
GET /portal/brand      — 当前 client 的 brand_config
GET /portal/personas   — persona 列表（简化字段）
GET /portal/creatives  — 创意列表
GET /portal/reports    — 归因报告
```

## 核心文件

| 文件                            | 职责                          |
| ------------------------------- | ----------------------------- |
| `api/v1/portal.py`              | 5 端点，简化响应字段          |
| `core/deps.py::get_portal_user` | 按 role 限定 client_id 作用域 |

## 关键决策

- **只读视图**：MVP 所有 5 个端点都是 GET
- **字段简化**：response 字段比 Staff View 少，CMO 友好（如不暴露 model_used / retry_count）
- **白标主题**：brand_config 直接从 client 级获取，前端注入 CSS 变量
- **AI Insight**：MVP 不实现，预留字段位置（dashboard.ai_insight，Phase 2 填充）

## Staff View vs Client View 差异

| 端点      | Staff                 | Client                       |
| --------- | --------------------- | ---------------------------- |
| dashboard | 全 agency 汇总        | 单 client 汇总               |
| personas  | 完整字段 + model_used | 仅 name + description + tone |
| reports   | 完整 results JSON     | 仅 channels 汇总 + insights  |

## Phase 2 扩展

- 可配置 widget 选择（per-client dashboard 定制）
- AI Insight 自动摘要叠加
- 实时 WebSocket 推送（已有 f17 基础）
