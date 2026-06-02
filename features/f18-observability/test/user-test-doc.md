# F-18 监控与可观测性 — 测试文档

## 测试范围

| 模块                      | 测试点                                     |
| ------------------------- | ------------------------------------------ |
| Sentry 初始化             | DSN 有值时初始化；无值时跳过，不报错       |
| Langfuse 客户端           | key 有值时返回实例；无值时返回 None        |
| RequestLoggingMiddleware  | 每个请求注入 X-Request-Id；记录耗时        |
| GET /health（基础）       | 返回 200，含 version 字段                  |
| GET /health（DB 检查）    | PostgreSQL 可连通时 database.status=ok     |
| GET /health（Redis 降级） | Redis 不可用时 status=degraded，仍返回 200 |
| GET /health（整体 down）  | DB 不可达时返回 503                        |
| Langfuse AI tracing       | 无 key 时 AI chat 正常执行，不报错         |

## 测试用例

### TC-OBS-01：GET /health 基础结构

- **前置**：无（无需 auth）
- **操作**：`GET /health`
- **期望**：HTTP 200，响应含 `status`、`version`、`components` 字段

### TC-OBS-02：健康检查 DB ok

- **前置**：PostgreSQL 可用（测试环境默认）
- **操作**：`GET /health`
- **期望**：`components.database.status == "ok"`，`latency_ms` 为正数

### TC-OBS-03：健康检查 Redis 降级

- **前置**：Redis URL 设为无效地址
- **操作**：`GET /health`
- **期望**：HTTP 200，`components.redis.status == "degraded"`，整体 `status == "degraded"`

### TC-OBS-04：健康检查 Warehouse ok

- **前置**：DuckDB 内存模式（默认）
- **操作**：`GET /health`
- **期望**：`components.warehouse.status == "ok"`

### TC-OBS-05：健康检查无需认证

- **前置**：无 Authorization header
- **操作**：`GET /health`
- **期望**：HTTP 200（不需要 JWT）

### TC-OBS-06：Sentry 无 DSN 时不崩溃

- **前置**：SENTRY_DSN="" （默认）
- **操作**：应用启动
- **期望**：正常启动，无 Sentry 相关异常

### TC-OBS-07：Langfuse 无 key 时 AI 调用正常

- **前置**：LANGFUSE_PUBLIC_KEY="" （默认）
- **操作**：`POST /api/v1/ai/chat`（带 auth）
- **期望**：HTTP 200，响应正常，无 Langfuse 相关错误

### TC-OBS-08：X-Request-Id 注入

- **前置**：任意请求
- **操作**：`GET /health`
- **期望**：响应 header 含 `X-Request-Id`（UUID 格式）
