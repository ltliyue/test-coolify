"""
F-18：monitoring and observabilitytest。
Covers: deep GET /health check, X-Request-Id injection, silent Langfuse degradation, Sentry no-crash.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient


# ── TC-OBS-01：GET /health basicstructure ────────────────────────────────────────────
@pytest.mark.asyncio
async def test_health_structure(client: AsyncClient):
    """
    /health should return 200 with three top-level fields: status, version, components.
    components must include database, redis, and warehouse.
    """
    resp = await client.get("/health")
    assert resp.status_code in (200, 503)  # DB reachable when  200
    data = resp.json()
    assert "status" in data
    assert "version" in data
    assert "components" in data
    assert "database" in data["components"]
    assert "redis" in data["components"]
    assert "warehouse" in data["components"]


# ── TC-OBS-02：DB reachable when  database.status=ok ────────────────────────────────────
@pytest.mark.asyncio
async def test_health_db_ok(client: AsyncClient):
    """test environment PostgreSQL available，database should to  ok。"""
    resp = await client.get("/health")
    data = resp.json()
    db_health = data["components"]["database"]
    assert db_health["status"] == "ok"
    assert "latency_ms" in db_health
    assert db_health["latency_ms"] >= 0


# ── TC-OBS-03：Redis unreachable when degrade，HTTP still 200 ────────────────────────────────
@pytest.mark.asyncio
async def test_health_redis_degraded(client: AsyncClient):
    """
    test environment Redis cancannot start。
    Expect: redis.status is ok or degraded, but overall HTTP should not be 503.
    """
    resp = await client.get("/health")
    data = resp.json()
    redis_status = data["components"]["redis"]["status"]
    assert redis_status in ("ok", "degraded")
    # Redis unreachableshould not cause 503 (non-fatal)
    if redis_status == "degraded" and data["components"]["database"]["status"] == "ok":
        assert resp.status_code == 200


# ── TC-OBS-04：Warehouse（DuckDB）health ────────────────────────────────────────
@pytest.mark.asyncio
async def test_health_warehouse_ok(client: AsyncClient):
    """In DuckDB dev mode warehouse should be ok or degraded (including degraded when not installed)."""
    resp = await client.get("/health")
    data = resp.json()
    wh_status = data["components"]["warehouse"]["status"]
    assert wh_status in ("ok", "degraded")


# ── TC-OBS-05: /health requires no authentication ───────────────────────────────
@pytest.mark.asyncio
async def test_health_no_auth_required(client: AsyncClient):
    """/health does not require JWT; anyclientmay access it。"""
    # without any headers
    resp = await client.get("/health")
    assert resp.status_code != 401
    assert resp.status_code != 403


# ── TC-OBS-06: overall-status aggregation logic ─────────────────────────────────
@pytest.mark.asyncio
async def test_health_overall_status_logic(client: AsyncClient):
    """
    verify aggregation logic：
    - DB ok + Redis degraded → overall=degraded
    - DB ok + Redis ok → overall=ok (if warehouse is also ok)
    """
    resp = await client.get("/health")
    data = resp.json()
    overall = data["status"]
    components = data["components"]

    statuses = {v["status"] for v in components.values()}

    if "down" in statuses:
        assert overall == "down"
        assert resp.status_code == 503
    elif "degraded" in statuses:
        assert overall == "degraded"
        assert resp.status_code == 200
    else:
        assert overall == "ok"
        assert resp.status_code == 200


# ── TC-OBS-07：X-Request-Id inject ─────────────────────────────────────────────
@pytest.mark.asyncio
async def test_request_id_header_injected(client: AsyncClient):
    """/health response header should contain X-Request-Id（UUID format）。"""
    resp = await client.get("/health")
    assert "x-request-id" in resp.headers
    request_id = resp.headers["x-request-id"]
    # verify isvalid UUID
    import uuid
    parsed = uuid.UUID(request_id)
    assert str(parsed) == request_id


# ── TC-OBS-08：Langfuse no key  when  AI chat normalexecute ───────────────────────────
@pytest.mark.asyncio
async def test_ai_chat_langfuse_graceful_without_key(
    client: AsyncClient, auth_headers: dict
):
    """
    LANGFUSE_PUBLIC_KEY defaultto empty，get_langfuse() should return None。
    The AI chat endpoint should not fail because Langfuse is unconfigured.
    """
    # reset Langfuse singletonensuretestisolation
    from app.core.monitoring import reset_langfuse, get_langfuse
    reset_langfuse()

    lf = get_langfuse()
    assert lf is None  # test environment has no config for Langfuse key

    # AI chat still shouldwork normally
    resp = await client.post(
        "/api/v1/ai/chat",
        json={"agent_type": "general", "prompt": "Hello"},
        headers=auth_headers,
    )
    assert resp.status_code == 200


# ── TC-OBS-09：Sentry no DSN  when startno exception ────────────────────────────────────
def test_sentry_init_no_dsn_no_crash():
    """init_sentry should not raise an exception when given an empty DSN."""
    from app.core.monitoring import init_sentry
    # should not raise any exception
    init_sentry("")
    init_sentry(None)  # type: ignore


# ── TC-OBS-10：RequestLoggingMiddleware propagaterequest ID ───────────────────────────
@pytest.mark.asyncio
async def test_request_id_passthrough(client: AsyncClient):
    """clientpassing X-Request-Id  when ，response shouldreturnsame ID。"""
    custom_id = "test-request-id-12345678"
    resp = await client.get("/health", headers={"X-Request-Id": custom_id})
    assert resp.headers.get("x-request-id") == custom_id
