# F-18 监控与可观测性 — 开发设计文档

- **功能**：F-18 Observability（Sentry + Langfuse + 增强健康检查）
- **优先级**：P2
- **阶段**：Phase 0 补完
- **日期**：2026-03-31
- **依赖**：F-09（AI Brain），F-02（Auth），F-00（合规）

---

## 架构概览

```
HTTP Request
    │
    ▼
RequestLoggingMiddleware        ← 注入 X-Request-Id，记录耗时/状态码
    │
    ▼
FastAPI Routes
    │
    ├─── POST /api/v1/ai/chat ──→ LangfuseTracer.trace()
    │                                  │
    │                                  ▼
    │                             OpenRouter API
    │                                  │
    │                                  ▼
    │                          LangfuseTracer.finalize()
    │
    └─── GET /health ──→ HealthChecker
                              │
                              ├── check_db()        PostgreSQL
                              ├── check_redis()     Redis (optional)
                              └── check_warehouse() DuckDB/Snowflake

Error anywhere ──→ Sentry.capture_exception()
```

---

## 文件清单

### 新建文件

| 文件                                  | 说明                                            |
| ------------------------------------- | ----------------------------------------------- |
| `backend/app/core/monitoring.py`      | Sentry init、Langfuse tracer、结构化日志        |
| `backend/app/core/health.py`          | HealthChecker 类，DB/Redis/Warehouse 连通性检查 |
| `backend/app/api/v1/health.py`        | GET /health 增强端点                            |
| `backend/tests/test_observability.py` | F-18 测试套件                                   |

### 修改文件

| 文件                           | 改动                                                                                        |
| ------------------------------ | ------------------------------------------------------------------------------------------- |
| `backend/app/main.py`          | 移除内联 Sentry init，改用 monitoring.py；注册 RequestLoggingMiddleware；注册 health router |
| `backend/app/api/v1/ai.py`     | POST /ai/chat 中注入 Langfuse trace                                                         |
| `backend/app/api/v1/router.py` | 无需改动（health 直接挂在 app 根路径）                                                      |

---

## 核心模块设计

### 1. `monitoring.py` — 统一可观测性入口

```python
def init_sentry(dsn: str, environment: str) -> None:
    """初始化 Sentry SDK；dsn 为空时跳过（开发环境）。"""

def get_langfuse() -> Optional[Langfuse]:
    """
    返回全局 Langfuse 客户端单例。
    LANGFUSE_PUBLIC_KEY 未配置时返回 None（降级静默）。
    """

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    每个请求注入 X-Request-Id；
    响应后以 structlog 记录：method/path/status/duration_ms/request_id。
    """
```

### 2. `health.py` — 深度健康检查

```python
@dataclass
class ComponentHealth:
    name: str
    status: Literal["ok", "degraded", "down"]
    latency_ms: Optional[float] = None
    detail: Optional[str] = None

async def check_db(engine) -> ComponentHealth: ...
async def check_redis(url: str) -> ComponentHealth: ...
def check_warehouse() -> ComponentHealth: ...
async def full_health_check() -> dict: ...
```

**响应格式：**

```json
{
  "status": "ok", // "ok" | "degraded" | "down"
  "version": "1.0.0",
  "components": {
    "database": { "status": "ok", "latency_ms": 3.2 },
    "redis": { "status": "degraded", "detail": "connection refused" },
    "warehouse": { "status": "ok", "latency_ms": 1.1 }
  }
}
```

- 全部 ok → HTTP 200
- 任意 degraded → HTTP 200（非致命）
- 任意 down → HTTP 503

### 3. Langfuse AI Tracing

在 `POST /ai/chat` 中：

```python
lf = get_langfuse()
trace = lf.trace(name="ai_chat", user_id=str(current_user.id)) if lf else None
generation = trace.generation(
    name="openrouter_call",
    model=model,
    input=messages,
) if trace else None

# ... 调用 OpenRouter ...

if generation:
    generation.end(output=response_text, usage={
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
    })
if trace:
    trace.update(metadata={"agency_id": str(agency_id)})
```

---

## API 设计

### GET /health（增强）

**现状**：`{"status": "ok", "version": "1.0.0"}`

**升级后**：

```
GET /health
Response 200:
{
  "status": "ok" | "degraded" | "down",
  "version": "1.0.0",
  "components": {
    "database":  ComponentHealth,
    "redis":     ComponentHealth,
    "warehouse": ComponentHealth
  }
}
```

---

## 安全考量

- `GET /health` 无需认证（供 Docker/K8s liveness probe 使用）
- 健康响应不暴露内部错误细节（`detail` 字段仅描述连接状态，不含 traceback）
- Sentry DSN 通过环境变量注入，不硬编码
- Langfuse key 同上，未配置时静默降级（不影响主功能）

---

## 错误处理

| 场景               | 处理策略                                          |
| ------------------ | ------------------------------------------------- |
| Sentry import 失败 | try/except，日志警告，继续启动                    |
| Langfuse init 失败 | 返回 None，AI 调用正常进行，只是不记录 trace      |
| DB 连通失败        | health 返回 down + 503，Sentry 捕获               |
| Redis 连通失败     | health 返回 degraded + 200（非致命）              |
| Warehouse 连通失败 | health 返回 degraded + 200（DuckDB 开发环境可用） |
