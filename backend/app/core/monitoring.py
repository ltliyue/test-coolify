from __future__ import annotations
"""
Unified observability module: Sentry initialization, Langfuse client, structured request-log middleware.

Usage:
  from app.core.monitoring import init_sentry, get_langfuse, RequestLoggingMiddleware
"""
import logging
import time
import uuid
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

log = logging.getLogger(__name__)

# ── Sentry ─────────────────────────────────────────────────────────────────────

def init_sentry(dsn: str, environment: str = "development") -> None:
    """
    Initialize the Sentry SDK.
    Skip silently when dsn is empty or None (dev/test).
    """
    if not dsn:
        log.debug("Sentry DSN not configured, skipping initialization")
        return
    try:
        import sentry_sdk
        sentry_sdk.init(
            dsn=dsn,
            traces_sample_rate=0.1,
            environment=environment,
            # Compliance: never send the request body (may contain PHI)
            send_default_pii=False,
        )
        log.info("Sentry initialized (environment=%s)", environment)
    except ImportError:
        log.warning("sentry-sdk not installed; monitoring disabled")
    except Exception as exc:
        log.warning("Sentry init failed: %s", exc)


# ── Langfuse ──────────────────────────────────────────────────────────────────

_langfuse_client: Optional[object] = None
_langfuse_initialized: bool = False


def get_langfuse() -> Optional[object]:
    """
    Return the global Langfuse client singleton.
    Returns None when LANGFUSE_PUBLIC_KEY is unset (silent degradation; core flow unaffected).
    """
    global _langfuse_client, _langfuse_initialized
    if _langfuse_initialized:
        return _langfuse_client

    _langfuse_initialized = True
    try:
        from app.core.config import settings
        if not settings.LANGFUSE_PUBLIC_KEY or not settings.LANGFUSE_SECRET_KEY:
            log.debug("Langfuse keys not configured, tracing disabled")
            return None

        from langfuse import Langfuse
        _langfuse_client = Langfuse(
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            secret_key=settings.LANGFUSE_SECRET_KEY,
            host=settings.LANGFUSE_HOST,
        )
        log.info("Langfuse initialized (host=%s)", settings.LANGFUSE_HOST)
    except ImportError:
        log.warning("langfuse package not installed; LLM tracing disabled")
    except Exception as exc:
        log.warning("Langfuse init failed: %s", exc)

    return _langfuse_client


def reset_langfuse() -> None:
    """Test helper: reset the global Langfuse singleton."""
    global _langfuse_client, _langfuse_initialized
    _langfuse_client = None
    _langfuse_initialized = False


# ── Request Logging Middleware ─────────────────────────────────────────────────

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Inject a unique X-Request-Id per request and emit a structured access log on response:
      method | path | status | duration_ms | request_id
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        start = time.perf_counter()

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        response.headers["X-Request-Id"] = request_id

        log.info(
            "request completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "request_id": request_id,
            },
        )
        return response
