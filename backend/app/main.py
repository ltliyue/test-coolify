from __future__ import annotations
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.compliance.session_guard import HIPAASessionGuard
from app.core.monitoring import init_sentry, RequestLoggingMiddleware

# ── Environment detection + C-05 SECRET_KEY startup check ────────────────────────
import os as _os
_env = _os.environ.get("ENVIRONMENT", "development" if settings.SECRET_KEY.startswith("change") else "production")
if _env == "production" and (
    settings.SECRET_KEY.startswith("change") or len(settings.SECRET_KEY) < 32
):
    raise RuntimeError("FATAL: SECRET_KEY is weak or default in production. Set a 32+ char random key.")
init_sentry(settings.SENTRY_DSN, environment=_env)

# ── App ────────────────────────────────────────────────────────────────────────
# M-4: disable API docs exposure in production
_docs_url = "/docs" if _env == "development" else None
_redoc_url = "/redoc" if _env == "development" else None

app = FastAPI(
    title="ReceptivIQ Platform API",
    description="AI-native Agency OS — GDPR · CCPA · HIPAA compliant",
    version="1.0.0",
    docs_url=_docs_url,
    redoc_url=_redoc_url,
)

# ── Middleware (registered outermost-first = executed last; Starlette onion model) ──
# M-01: CORS — env-driven, restricted methods and headers
_cors_origins = _os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors_origins],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-Id"],
)

# HIPAA session timeout (compliance) — try Redis, fall back gracefully if unavailable
_redis_client = None
try:
    import redis.asyncio as aioredis  # type: ignore
    _redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
except Exception:
    pass  # Fall back to no session timeout if Redis is unavailable
app.add_middleware(HIPAASessionGuard, redis_client=_redis_client)

# Request-ID injection + structured access logging
app.add_middleware(RequestLoggingMiddleware)


# M-11: security response-headers middleware
from starlette.middleware.base import BaseHTTPMiddleware as _BaseHttp  # noqa: E402
from starlette.requests import Request as _Req  # noqa: E402


class _SecurityHeadersMiddleware(_BaseHttp):
    async def dispatch(self, request: _Req, call_next):  # type: ignore
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if _env == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        return response


app.add_middleware(_SecurityHeadersMiddleware)

# ── Routes ─────────────────────────────────────────────────────────────────────
from app.api.v1.router import api_router   # noqa: E402
from app.api.v1.health import router as health_router  # noqa: E402

app.include_router(api_router)
app.include_router(health_router)  # GET /health (deep health check)

# WebSocket (root-level route, not under /api/v1 prefix)
from app.api.v1.ws import router as ws_router  # noqa: E402
app.include_router(ws_router)


# PR 2: dispose per-tenant engines cleanly on shutdown.
@app.on_event("shutdown")
async def _dispose_tenant_engines() -> None:  # pragma: no cover - lifecycle hook
    from app.core.tenant_router import TenantSessionRouter

    await TenantSessionRouter.instance().dispose_all()
