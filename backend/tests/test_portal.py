"""
F-16：client portaltest。
Covers: dashboard、brand config、personas/creatives/reports lightweight view、authenticationcheck。
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient


# ── TC-PTL-01：dashboardsummary ────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_portal_dashboard(client: AsyncClient, auth_headers: dict):
    """GET /portal/dashboard should return brand info and per-module counts."""
    resp = await client.get("/api/v1/portal/dashboard", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "brand" in data
    assert "persona_count" in data
    assert "creative_count" in data
    assert "report_count" in data
    assert data["persona_count"] >= 0
    assert data["creative_count"] >= 0
    assert data["report_count"] >= 0


# ── TC-PTL-02：brand config ──────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_portal_brand(client: AsyncClient, auth_headers: dict):
    """GET /portal/brand should returnbrand config field。"""
    resp = await client.get("/api/v1/portal/brand", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    # All optional fields
    for key in ("name", "logo_url", "primary_color", "secondary_color", "industry", "tagline"):
        assert key in data


# ── TC-PTL-03: brand config reflects PUT updates ────────────────────────────────
@pytest.mark.asyncio
async def test_portal_brand_reflects_update(client: AsyncClient, auth_headers: dict):
    """After PUT brands/config, GET portal/brand should reflect the update."""
    await client.put(
        "/api/v1/brands/config",
        json={"name": "Portal Brand", "primary_color": "#FF0000"},
        headers=auth_headers,
    )
    resp = await client.get("/api/v1/portal/brand", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Portal Brand"
    assert resp.json()["primary_color"] == "#FF0000"


# ── TC-PTL-04：persona lightweight view ──────────────────────────────────────────────
@pytest.mark.asyncio
async def test_portal_personas(client: AsyncClient, auth_headers: dict):
    """After creating a persona, GET /portal/personas should return a lightweight view (no model_used/source)."""
    await client.post(
        "/api/v1/personas",
        json={"name": "Portal Persona", "description": "Test persona"},
        headers=auth_headers,
    )
    resp = await client.get("/api/v1/portal/personas", headers=auth_headers)
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) >= 1
    first = items[0]
    assert "name" in first
    assert "description" in first
    # Should not expose internal fields
    assert "model_used" not in first
    assert "source" not in first


# ── TC-PTL-05：creative lightweight view ─────────────────────────────────────────────
@pytest.mark.asyncio
async def test_portal_creatives(client: AsyncClient, auth_headers: dict):
    """After generating a creative, GET /portal/creatives should return a lightweight view."""
    await client.post(
        "/api/v1/creatives/generate",
        json={"prompt": "Portal test", "platforms": ["INSTAGRAM"]},
        headers=auth_headers,
    )
    resp = await client.get("/api/v1/portal/creatives", headers=auth_headers)
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) >= 1
    first = items[0]
    assert "prompt" in first
    assert "status" in first
    assert "platforms" in first


# ── TC-PTL-06：reports lightweight view ──────────────────────────────────────────────
@pytest.mark.asyncio
async def test_portal_reports(client: AsyncClient, auth_headers: dict):
    """After generating an attribution report, GET /portal/reports should return a lightweight view."""
    await client.post(
        "/api/v1/attribution/report",
        json={"title": "Portal Report"},
        headers=auth_headers,
    )
    resp = await client.get("/api/v1/portal/reports", headers=auth_headers)
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) >= 1
    first = items[0]
    assert "title" in first
    assert "report_type" in first
    # Should not expose internal fields
    assert "model_used" not in first
    assert "results" not in first


# ── TC-PTL-07: dashboard counts update reactively ───────────────────────────────
@pytest.mark.asyncio
async def test_portal_dashboard_counts(client: AsyncClient, auth_headers: dict):
    """After creating a persona/creative/report, dashboard counts should increase."""
    # First fetch the initial counts
    resp0 = await client.get("/api/v1/portal/dashboard", headers=auth_headers)
    initial = resp0.json()

    # Create various resource types
    await client.post("/api/v1/personas", json={"name": "Count Test"}, headers=auth_headers)
    await client.post("/api/v1/creatives/generate", json={"prompt": "Count Test"}, headers=auth_headers)
    await client.post("/api/v1/attribution/report", json={"title": "Count Test"}, headers=auth_headers)

    resp1 = await client.get("/api/v1/portal/dashboard", headers=auth_headers)
    updated = resp1.json()

    assert updated["persona_count"] > initial["persona_count"]
    assert updated["creative_count"] > initial["creative_count"]
    assert updated["report_count"] > initial["report_count"]


# ── TC-PTL-08：authenticationcheck ──────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_portal_requires_auth(client: AsyncClient):
    """/portal/dashboard without JWT should return 401。"""
    resp = await client.get("/api/v1/portal/dashboard")
    assert resp.status_code == 401
