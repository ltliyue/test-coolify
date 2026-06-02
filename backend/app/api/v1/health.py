from __future__ import annotations
"""GET /health — deep health check endpoint (no authentication required)."""
from fastapi import APIRouter, Response

from app.core.health import full_health_check

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(response: Response):
    """
    Check DB / Redis / Warehouse connectivity.

    - all parts ok → 200
    - any degraded (Redis/Warehouse unavailable) → 200 (non-fatal)
    - database down → 503
    """
    result, status_code = await full_health_check()
    response.status_code = status_code
    return result
