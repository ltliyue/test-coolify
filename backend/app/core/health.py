from __future__ import annotations
"""
Deep health-check module.
Checks PostgreSQL, Redis (optional), and warehouse (DuckDB/Snowflake) connectivity.

Return shape:
{
  "status": "ok" | "degraded" | "down",
  "version": "1.0.0",
  "components": {
    "database":  ComponentHealth,
    "redis":     ComponentHealth,
    "warehouse": ComponentHealth,
  }
}

HTTP status:
  all ok          → 200
  any degraded    → 200
  any down        → 503
"""
import time
import logging
from dataclasses import dataclass, field
from typing import Literal, Optional, Dict, Any

log = logging.getLogger(__name__)

_VERSION = "1.0.0"


@dataclass
class ComponentHealth:
    name: str
    status: Literal["ok", "degraded", "down"] = "ok"
    latency_ms: Optional[float] = None
    detail: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"status": self.status}
        if self.latency_ms is not None:
            d["latency_ms"] = self.latency_ms
        if self.detail is not None:
            d["detail"] = self.detail
        return d


async def check_db() -> ComponentHealth:
    """PostgreSQL connectivity check: runs SELECT 1."""
    from app.core.database import engine
    from sqlalchemy import text

    t0 = time.perf_counter()
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        latency = round((time.perf_counter() - t0) * 1000, 2)
        return ComponentHealth(name="database", status="ok", latency_ms=latency)
    except Exception as exc:
        log.warning("DB health check failed: %s", exc)
        return ComponentHealth(name="database", status="down", detail="connection failed")


async def check_redis() -> ComponentHealth:
    """Redis connectivity check: PING. Degrades gracefully when unavailable (non-fatal)."""
    from app.core.config import settings

    t0 = time.perf_counter()
    try:
        import redis.asyncio as aioredis  # type: ignore
        r = aioredis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        await r.ping()
        await r.aclose()
        latency = round((time.perf_counter() - t0) * 1000, 2)
        return ComponentHealth(name="redis", status="ok", latency_ms=latency)
    except ImportError:
        return ComponentHealth(name="redis", status="degraded", detail="redis package not installed")
    except Exception as exc:
        log.warning("Redis health check failed: %s", exc)
        return ComponentHealth(name="redis", status="degraded", detail="connection failed")


def check_warehouse() -> ComponentHealth:
    """Warehouse (DuckDB/Snowflake) connectivity check."""
    from app.core.config import settings

    t0 = time.perf_counter()
    backend = getattr(settings, "WAREHOUSE_BACKEND", None) or "duckdb"

    try:
        if backend == "duckdb":
            import duckdb  # type: ignore
            conn = duckdb.connect(":memory:")
            conn.execute("SELECT 1")
            conn.close()
        else:
            # Snowflake: lazy check — only verify the connector is importable, no pool
            import snowflake.connector  # type: ignore

        latency = round((time.perf_counter() - t0) * 1000, 2)
        return ComponentHealth(name="warehouse", status="ok", latency_ms=latency, detail=backend)
    except ImportError as exc:
        return ComponentHealth(name="warehouse", status="degraded", detail=f"missing package: {exc}")
    except Exception as exc:
        log.warning("Warehouse health check failed: %s", exc)
        return ComponentHealth(name="warehouse", status="degraded", detail="connection failed")


async def full_health_check() -> tuple[Dict[str, Any], int]:
    """
    Run the full health check and return (response_dict, http_status_code).
    """
    db_health = await check_db()
    redis_health = await check_redis()
    wh_health = check_warehouse()

    components = {
        "database": db_health.to_dict(),
        "redis": redis_health.to_dict(),
        "warehouse": wh_health.to_dict(),
    }

    # Aggregate status precedence: down > degraded > ok
    statuses = {c.status for c in (db_health, redis_health, wh_health)}
    if "down" in statuses:
        overall = "down"
        http_code = 503
    elif "degraded" in statuses:
        overall = "degraded"
        http_code = 200
    else:
        overall = "ok"
        http_code = 200

    return {
        "status": overall,
        "version": _VERSION,
        "components": components,
    }, http_code
