# f18-observability 需求文档

> 来源：生产运维 + 合规审计需求
> 状态：MVP P2

## 功能概述

监控与可观测性基础设施。集成 Sentry（错误追踪）、Langfuse（LLM 观测）、深度健康检查、结构化日志。

## 功能需求

### FR-1: 深度健康检查

- GET `/health` — 无需认证
- 聚合检查：DB（asyncpg ping）+ Redis + Warehouse（DuckDB/Snowflake）
- 整体状态：healthy / degraded / unhealthy
- 任一组件降级即整体 degraded

### FR-2: Sentry 集成

- 生产启用（SENTRY_DSN 配置时）
- 自动捕获 FastAPI 异常
- 无配置时静默降级

### FR-3: Langfuse LLM 观测

- 懒加载单例
- 追踪每次 LLM 调用的 prompt/completion/延迟
- 无配置时静默降级（不影响 AI 功能）

### FR-4: Request ID 中间件

- 每个请求生成唯一 ID（UUID）
- 注入 request.state + response header
- 支持客户端 X-Request-ID passthrough

### FR-5: 结构化日志

- JSON 格式日志
- 包含 request_id / user_id / agency_id 上下文
- 不记录敏感信息（token / 密码 / PII）

## 非功能需求

- health 检查 < 500ms
- 监控降级不影响业务

## 合规要求

- Sentry 捕获的异常消息需过滤 PII
- 日志中的 API token / 密码需 scrub
- request_id 可用于审计追溯
