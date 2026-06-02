"""
F-10：Persona Agent test。
Covers: CRUD、AI generate、soft-delete、filter、authenticationcheck。
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient


# ── TC-PER-01：listto empty ──────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_list_personas_empty(client: AsyncClient, auth_headers: dict):
    """A new Agency's persona list should be empty."""
    resp = await client.get("/api/v1/personas", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


# ── TC-PER-02：manually create Persona ──────────────────────────────────────────────
@pytest.mark.asyncio
async def test_create_persona_manual(client: AsyncClient, auth_headers: dict):
    """POST manually create persona，return 201，source=manual。"""
    payload = {
        "name": "Budget-Conscious Buyer",
        "description": "A value-driven shopper who compares prices across platforms.",
        "psychographics": {
            "values": ["affordability", "practicality"],
            "interests": ["deal hunting", "comparison shopping"],
        },
        "recommended_tone": "Friendly and helpful",
    }
    resp = await client.post(
        "/api/v1/personas", json=payload, headers=auth_headers
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Budget-Conscious Buyer"
    assert data["source"] == "manual"
    assert data["is_active"] is True
    assert data["psychographics"]["values"] == ["affordability", "practicality"]


# ── TC-PER-03：AI generate Persona ──────────────────────────────────────────────
@pytest.mark.asyncio
async def test_generate_personas_ai(client: AsyncClient, auth_headers: dict):
    """POST /generate should call persona agent（mock mode），return AI generate  persona list。"""
    resp = await client.post(
        "/api/v1/personas/generate",
        json={"prompt": "Generate personas for an e-commerce brand", "count": 3},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    # AI generate  source should to  "ai"
    assert data[0]["source"] == "ai"
    assert data[0]["name"]  # non-null


# ── TC-PER-04：get single Persona ──────────────────────────────────────────────
@pytest.mark.asyncio
async def test_get_persona_by_id(client: AsyncClient, auth_headers: dict):
    """GET /{id} should return the just-created persona."""
    create_resp = await client.post(
        "/api/v1/personas",
        json={"name": "Tech Savvy Tim"},
        headers=auth_headers,
    )
    persona_id = create_resp.json()["id"]

    resp = await client.get(
        f"/api/v1/personas/{persona_id}", headers=auth_headers
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Tech Savvy Tim"


# ── TC-PER-05：update Persona ──────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_update_persona(client: AsyncClient, auth_headers: dict):
    """PUT update name  and  recommended_tone。"""
    create_resp = await client.post(
        "/api/v1/personas",
        json={"name": "Original Name", "recommended_tone": "Formal"},
        headers=auth_headers,
    )
    persona_id = create_resp.json()["id"]

    resp = await client.put(
        f"/api/v1/personas/{persona_id}",
        json={"name": "Updated Name", "recommended_tone": "Casual"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Name"
    assert resp.json()["recommended_tone"] == "Casual"


# ── TC-PER-06：soft-delete Persona ────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_delete_persona_soft(client: AsyncClient, auth_headers: dict):
    """After DELETE, GET should return 404 and the item should no longer appear in the list."""
    create_resp = await client.post(
        "/api/v1/personas",
        json={"name": "To Be Deleted"},
        headers=auth_headers,
    )
    persona_id = create_resp.json()["id"]

    del_resp = await client.delete(
        f"/api/v1/personas/{persona_id}", headers=auth_headers
    )
    assert del_resp.status_code == 204

    get_resp = await client.get(
        f"/api/v1/personas/{persona_id}", headers=auth_headers
    )
    assert get_resp.status_code == 404


# ── TC-PER-07: filter by source ─────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_list_personas_filter_by_source(client: AsyncClient, auth_headers: dict):
    """?source=manual should return only manually-created personas."""
    # manually create one 
    await client.post(
        "/api/v1/personas",
        json={"name": "Manual Persona"},
        headers=auth_headers,
    )
    # AI generatesome
    await client.post(
        "/api/v1/personas/generate",
        json={"prompt": "Generate personas", "count": 1},
        headers=auth_headers,
    )

    # filtermanual
    resp = await client.get(
        "/api/v1/personas?source=manual", headers=auth_headers
    )
    assert resp.status_code == 200
    items = resp.json()
    assert all(p["source"] == "manual" for p in items)


# ── TC-PER-08：authenticationcheck ──────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_persona_requires_auth(client: AsyncClient):
    """/personas without JWT should return 401。"""
    resp = await client.get("/api/v1/personas")
    assert resp.status_code == 401


# ── TC-PER-09：non-existent ID return 404 ──────────────────────────────────────────
@pytest.mark.asyncio
async def test_get_nonexistent_persona_404(client: AsyncClient, auth_headers: dict):
    """request non-existent  persona ID should return 404。"""
    import uuid
    fake_id = str(uuid.uuid4())
    resp = await client.get(
        f"/api/v1/personas/{fake_id}", headers=auth_headers
    )
    assert resp.status_code == 404
