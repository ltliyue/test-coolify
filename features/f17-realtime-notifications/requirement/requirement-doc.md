# f17-realtime-notifications 需求文档

> 来源：Frontend 实时反馈需求 + AI agent 进度提示
> 状态：MVP P2

## 功能概述

实时通知系统。支持 WebSocket 推送 + REST API 管理通知状态。用于 AI 生成完成、预算告警、报告就绪等场景。

## 功能需求

### FR-1: 通知 CRUD（REST）

- GET `/notifications` — 列表（分页）
- GET `/notifications/unread-count` — 未读计数
- PATCH `/notifications/{id}/read` — 标记已读
- PATCH `/notifications/read-all` — 全部已读

### FR-2: WebSocket 实时推送

- WS `/ws` — JWT 认证 + 心跳
- ConnectionManager 内存级全局单例
- 按 user_id 分组
- 自动断线重连

### FR-3: 通知分发

- dispatcher.create_notification() 同时写 DB + WS 推送
- 支持分类：generation_complete / budget_alert / report_ready / system
- 支持严重度：info / warning / error

### FR-4: 过滤查询

- 按 category / severity / unread_only 过滤

## 非功能需求

- WS 心跳间隔 30 秒
- 消息投递延迟 < 500ms

## 合规要求

- WS 连接需 JWT 认证
- 通知按 agency_id 隔离
- 不在 message 中包含 PII（只含业务元数据）
