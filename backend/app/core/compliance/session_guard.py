"""
Session Guard — HIPAA session-timeout middleware
HIPAA §164.312(a)(2)(iii): automatic logoff to prevent unauthorized workstation access.

Rules:
- PHI-related endpoints: 15-minute inactivity auto-logoff
- Other endpoints: 60-minute inactivity
- Alerting: the next request after timeout returns 401 with an explicit message

M-05 compliance fix: when Redis is unavailable, fall back to an in-memory LRU cache;
ensures the session-timeout mechanism is always active (no multi-instance sharing in degraded mode).
"""
from __future__ import annotations

import time
import logging
from collections import OrderedDict
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

log = logging.getLogger("session-guard")

# HIPAA requires 15-minute auto-logoff after PHI access (seconds)
HIPAA_SESSION_TIMEOUT = 15 * 60   # 15 minutes
DEFAULT_SESSION_TIMEOUT = 60 * 60  # 60 minutes

# URL prefixes that touch PHI (extended dynamically by tenant type)
PHI_ENDPOINTS = frozenset({
    "/api/v1/hipaa/",
    "/api/v1/health/",
    "/api/v1/compliance/dsar",
})

# M-05: in-memory LRU cache (fallback when Redis is unavailable)
_MAX_MEMORY_SESSIONS = 10_000


class _MemorySessionStore:
    """Simple in-process LRU cache (single-instance only). Used when Redis is unavailable."""

    def __init__(self, max_size: int = _MAX_MEMORY_SESSIONS) -> None:
        self._store: OrderedDict[str, float] = OrderedDict()
        self._max = max_size

    def get(self, key: str) -> float | None:
        val = self._store.get(key)
        if val is not None:
            self._store.move_to_end(key)
        return val

    def set(self, key: str, value: float) -> None:
        self._store[key] = value
        self._store.move_to_end(key)
        while len(self._store) > self._max:
            self._store.popitem(last=False)


class HIPAASessionGuard(BaseHTTPMiddleware):
    """
    Check last_activity_at and reject the request when expired.
    Writes to Redis when available; falls back to the in-memory LRU cache otherwise.
    """

    def __init__(self, app, redis_client=None) -> None:
        super().__init__(app)
        self.redis = redis_client
        self._mem_store = _MemorySessionStore()

    async def dispatch(self, request: Request, call_next):
        # Skip public endpoints
        if self._is_public(request.url.path):
            return await call_next(request)

        # Read auth info from request.state (injected upstream by JWT middleware)
        user = getattr(request.state, "user", None)
        if not user:
            return await call_next(request)

        # Decide whether this request touches PHI
        is_phi_request = any(request.url.path.startswith(p) for p in PHI_ENDPOINTS)
        timeout = HIPAA_SESSION_TIMEOUT if is_phi_request else DEFAULT_SESSION_TIMEOUT
        session_key = f"session:last_active:{user['user_id']}"

        # Try Redis → fall back to memory
        last_active = await self._get_last_active(session_key)
        if last_active is not None:
            elapsed = time.time() - last_active
            if elapsed > timeout:
                timeout_type = "HIPAA PHI" if is_phi_request else "standard"
                log.warning(
                    "Session timeout: user=%s path=%s elapsed=%.0fs type=%s",
                    user["user_id"], request.url.path, elapsed, timeout_type,
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "code": "SESSION_TIMEOUT",
                        "message": (
                            "Your session has expired due to inactivity. "
                            "Please log in again."
                            + (" (HIPAA 15-minute timeout policy)" if is_phi_request else "")
                        ),
                        "regulation": "HIPAA §164.312(a)(2)(iii)" if is_phi_request else None,
                    },
                )

        # Update last-activity timestamp
        await self._set_last_active(session_key, time.time(), timeout + 60)

        return await call_next(request)

    async def _get_last_active(self, key: str) -> float | None:
        """Read from Redis; fall back to in-memory cache on failure."""
        if self.redis:
            try:
                val = await self.redis.get(key)
                if val is not None:
                    return float(val)
                return None
            except Exception:
                pass  # Redis failure — degrade
        return self._mem_store.get(key)

    async def _set_last_active(self, key: str, value: float, ttl: int) -> None:
        """Dual-write to Redis + memory so the in-memory cache covers Redis failures."""
        self._mem_store.set(key, value)
        if self.redis:
            try:
                await self.redis.setex(key, ttl, str(value))
            except Exception:
                pass  # Redis failed; memory copy is already written

    @staticmethod
    def _is_public(path: str) -> bool:
        public_prefixes = ("/api/v1/auth/", "/health", "/docs", "/openapi")
        return any(path.startswith(p) for p in public_prefixes)
