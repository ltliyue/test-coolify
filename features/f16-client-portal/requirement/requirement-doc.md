# f16-client-portal 需求文档

> 来源：Dev Brief v2 §Client & Agency Portal
> 状态：MVP P2

## 功能概述

白标客户门户。Rose 原话："Agencies showing up with PowerPoint are getting beaten by me showing up with real-time dashboards"。门户是 Pillars 1-4 的前端输出层。

## 功能需求

### FR-1: 多租户账户结构

- Agency 账户包含多个 Client 账户
- Staff 用户看所有 client，Client 用户只看自己
- 权限模型：Admin / Manager / Client（read-only, scoped）

### FR-2: 品牌化 Dashboard

- 白标：每个 client 使用自己的 brand_config
- 可配置 widget 选择
- 由 attribution 数据管道驱动（实时，非静态）

### FR-3: 双视图结构

- Staff View：全详情，所有客户，管道健康度，AI 建议
- Client View：简化标签，CMO 友好语言，品牌匹配展示

### FR-4: AI 洞察摘要

- 一段 AI 生成的当前活动摘要
- Plain English，非技术受众友好
- 使用 Core AI Brain + attribution 数据 + brand_config

### FR-5: 5 个只读端点

- `/portal/dashboard` — 汇总数据
- `/portal/brand` — 当前品牌配置
- `/portal/personas` — persona 列表
- `/portal/creatives` — 创意列表
- `/portal/reports` — 归因报告

## 非功能需求

- Dashboard 加载 < 3 秒
- 5 个端点均为 GET（只读）

## 合规要求

- 所有端点带 audit_simple()
- get_portal_user 依赖：client_viewer 只见自己 client 数据
- 租户 + 客户双层隔离
