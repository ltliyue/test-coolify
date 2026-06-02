"""
F-11：Creative Agent test。
Covers: generate creative content, list, get details, authentication checks.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient


# ── TC-CRE-01: generate creative content ────────────────────────────────────────
@pytest.mark.asyncio
async def test_generate_creative(client: AsyncClient, auth_headers: dict):
    """POST /generate should return 200，status=COMPLETED，containing results list。"""
    payload = {
        "prompt": "Create marketing content for a summer sale campaign",
        "platforms": ["INSTAGRAM", "FACEBOOK"],
    }
    resp = await client.post(
        "/api/v1/creatives/generate", json=payload, headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "COMPLETED"
    assert data["prompt"] == payload["prompt"]
    assert data["agent_type"] == "creative"
    assert isinstance(data["results"], list)
    assert len(data["results"]) > 0


# ── TC-CRE-02：generateresultcontain copy_text ────────────────────────────────────────
@pytest.mark.asyncio
async def test_creative_results_contain_copy(client: AsyncClient, auth_headers: dict):
    """generate  result should contain copy_text  and  platform。"""
    resp = await client.post(
        "/api/v1/creatives/generate",
        json={"prompt": "Write ad copy for a tech product"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    results = resp.json()["results"]
    for result in results:
        assert "platform" in result
        assert result["copy_text"] is not None
        assert result["status"] == "COMPLETED"


# ── TC-CRE-03：list Generations ──────────────────────────────────────────────
@pytest.mark.asyncio
async def test_list_generations(client: AsyncClient, auth_headers: dict):
    """After generation, GET /creatives should return a non-empty list."""
    # first generateone 
    await client.post(
        "/api/v1/creatives/generate",
        json={"prompt": "Test campaign"},
        headers=auth_headers,
    )

    resp = await client.get("/api/v1/creatives", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1


# ── TC-CRE-04：get single Generation ──────────────────────────────────────────
@pytest.mark.asyncio
async def test_get_generation_by_id(client: AsyncClient, auth_headers: dict):
    """GET /{id} should returncontaining results  complete generation。"""
    gen_resp = await client.post(
        "/api/v1/creatives/generate",
        json={"prompt": "Holiday campaign"},
        headers=auth_headers,
    )
    gen_id = gen_resp.json()["id"]

    resp = await client.get(
        f"/api/v1/creatives/{gen_id}", headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == gen_id
    assert data["prompt"] == "Holiday campaign"
    assert isinstance(data["results"], list)


# ── TC-CRE-05：non-existent Generation return 404 ──────────────────────────────────
@pytest.mark.asyncio
async def test_get_nonexistent_generation_404(client: AsyncClient, auth_headers: dict):
    """request non-existent  generation ID should return 404。"""
    import uuid
    resp = await client.get(
        f"/api/v1/creatives/{uuid.uuid4()}", headers=auth_headers
    )
    assert resp.status_code == 404


# ── TC-CRE-06：platformfilter ──────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_generate_specific_platforms(client: AsyncClient, auth_headers: dict):
    """When requesting only the INSTAGRAM platform, results should contain only INSTAGRAM."""
    resp = await client.post(
        "/api/v1/creatives/generate",
        json={"prompt": "Instagram only campaign", "platforms": ["INSTAGRAM"]},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    results = resp.json()["results"]
    for r in results:
        assert r["platform"] == "INSTAGRAM"


# ── TC-CRE-07：authenticationcheck ──────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_creatives_requires_auth(client: AsyncClient):
    """/creatives without JWT should return 401。"""
    resp = await client.get("/api/v1/creatives")
    assert resp.status_code == 401


# ── TC-CRE-08：agency_id bindcorrect ───────────────────────────────────────────
@pytest.mark.asyncio
async def test_creative_bound_to_agency(
    client: AsyncClient, auth_headers: dict, test_agency
):
    """The generated result's agency_id should match the current user's agency."""
    resp = await client.post(
        "/api/v1/creatives/generate",
        json={"prompt": "Agency binding test"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["agency_id"] == str(test_agency.id)
