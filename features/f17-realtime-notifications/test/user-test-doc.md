# f17-realtime-notifications 用户测试文档

测试文件：`backend/tests/test_notifications.py`（9 用例）

## TC-01: 空列表

| 步骤               | 预期    |
| ------------------ | ------- |
| GET /notifications | 200, [] |

## TC-02: 创建 + 列表

| 步骤                                   | 预期          |
| -------------------------------------- | ------------- |
| dispatcher.create_notification() 写 DB | ✅            |
| GET /notifications                     | 200, 含新通知 |

## TC-03: 未读计数

| 步骤                            | 预期            |
| ------------------------------- | --------------- |
| GET /notifications/unread-count | 200, {count: N} |
| 标记 1 个已读后                 | count -= 1      |

## TC-04: 标记已读

| 步骤                           | 预期              |
| ------------------------------ | ----------------- |
| PATCH /notifications/{id}/read | 200, is_read=true |

## TC-05: 全部已读

| 步骤                          | 预期 |
| ----------------------------- | ---- |
| PATCH /notifications/read-all | 200  |
| unread-count = 0              | ✅   |

## TC-06: 按 category 过滤

| 步骤                   | 预期              |
| ---------------------- | ----------------- |
| GET ?type=budget_alert | 200, 仅 budget 类 |

## TC-07: unread_only 过滤

| 步骤                  | 预期        |
| --------------------- | ----------- |
| GET ?unread_only=true | 200, 仅未读 |

## TC-08: WebSocket ConnectionManager

| 测试                      | 预期 |
| ------------------------- | ---- |
| 初始状态 connections 为空 | ✅   |

## TC-09: 认证

| 步骤     | 预期 |
| -------- | ---- |
| 无 token | 401  |
