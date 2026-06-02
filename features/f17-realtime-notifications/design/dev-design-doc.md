# f17-realtime-notifications 设计文档

## 架构概览

```
业务事件（generation done / budget alert / report ready）
  ↓
dispatcher.create_notification(user_id, type, title, message, metadata)
  ├── 写入 notifications 表
  └── ConnectionManager.send_to_user(user_id, payload)
       ↓ WebSocket
       Client

REST API:
GET /notifications             — 列表
GET /notifications/unread-count
PATCH /notifications/{id}/read
PATCH /notifications/read-all
```

## 核心文件

| 文件                                   | 职责                                                  |
| -------------------------------------- | ----------------------------------------------------- |
| `models/notification.py`               | Notification ORM（type/title/message/metadata JSONB） |
| `services/notifications/manager.py`    | WebSocket ConnectionManager（内存单例）               |
| `services/notifications/dispatcher.py` | create_notification（双写）                           |
| `api/v1/notifications.py`              | 4 REST 端点                                           |
| `api/v1/ws.py`                         | WebSocket /ws 端点（JWT 认证）                        |

## 数据模型

```
Notification:
  id UUID PK
  agency_id UUID NOT NULL
  user_id UUID nullable（null = agency-wide broadcast）
  type VARCHAR  — generation_complete / budget_alert / report_ready / system
  title / message
  metadata JSONB  — 业务上下文（无 PII）
  is_read BOOL
  created_at
```

## 关键决策

- **内存单例 ConnectionManager**：简单有效，单实例部署足够；多实例需 Redis pub/sub（Phase 2）
- **按 user_id 分组**：每用户可有多个设备/标签页同时在线
- **双写策略**：先写 DB 再 WS 推送，WS 失败不影响持久化
- **心跳 30 秒**：防止 NAT/proxy 超时
- **JWT 认证**：WS upgrade 时从 query param 读取 token（WS 不支持 Authorization header 标准）

## Phase 2 扩展

- Redis pub/sub 支持多实例部署
- 通知偏好设置（per-user 启用/禁用类型）
- 邮件/SMS 渠道分发
