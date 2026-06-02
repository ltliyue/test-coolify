"""
F-13：brand onboardingtest。
Covers: GET /brands/config、PUT（PATCH semantics）、DELETE、authenticationcheck。
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient


# ── TC-BRD-01: all fields are None in the initial state ─────────────────────────
@pytest.mark.asyncio
async def test_get_brand_config_empty(client: AsyncClient, auth_headers: dict):
    """A newly-created Agency's brand config should return 200, with all fields None (unset)."""
    resp = await client.get("/api/v1/brands/config", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "agency_id" in data
    # all optionalfielddefaultto  None
    for field in ("name", "logo_url", "primary_color", "brand_voice", "industry"):
        assert data.get(field) is None


# ── TC-BRD-02：PUT update brand config ───────────────────────────────────────────────
@pytest.mark.asyncio
async def test_update_brand_config(client: AsyncClient, auth_headers: dict):
    """PUT setset name/industry/brand_voice，return containupdated value config。"""
    payload = {
        "name": "Acme Marketing",
        "industry": "e-commerce",
        "brand_voice": "Professional and friendly",
        "primary_color": "#FF6B35",
    }
    resp = await client.put(
        "/api/v1/brands/config", json=payload, headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Acme Marketing"
    assert data["industry"] == "e-commerce"
    assert data["brand_voice"] == "Professional and friendly"
    assert data["primary_color"] == "#FF6B35"


# ── TC-BRD-03: PUT preserves existing fields (PATCH semantics) ───────────────────
@pytest.mark.asyncio
async def test_patch_preserves_existing_fields(client: AsyncClient, auth_headers: dict):
    """
    first set name + industry，
    then onlyupdate tagline，
    originalhas name/industry should not be cleared。
    """
    # first setinitial value
    await client.put(
        "/api/v1/brands/config",
        json={"name": "BrandX", "industry": "finance"},
        headers=auth_headers,
    )

    # Update only tagline
    resp = await client.put(
        "/api/v1/brands/config",
        json={"tagline": "Think Different"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    # Original fields are preserved
    assert data["name"] == "BrandX"
    assert data["industry"] == "finance"
    # New field has been updated
    assert data["tagline"] == "Think Different"


# ── TC-BRD-04：DELETE resetconfig ─────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_reset_brand_config(client: AsyncClient, auth_headers: dict):
    """After DELETE, GET should return empty config (all fields None)."""
    # first write data
    await client.put(
        "/api/v1/brands/config",
        json={"name": "Temporary Brand", "website_url": "https://example.com"},
        headers=auth_headers,
    )

    # reset
    resp_del = await client.delete("/api/v1/brands/config", headers=auth_headers)
    assert resp_del.status_code == 204

    # read and verify cleared
    resp_get = await client.get("/api/v1/brands/config", headers=auth_headers)
    assert resp_get.status_code == 200
    data = resp_get.json()
    assert data.get("name") is None
    assert data.get("website_url") is None


# ── TC-BRD-05：unauthenticatedrequest be reject ──────────────────────────────────────────────
@pytest.mark.asyncio
async def test_brand_config_requires_auth(client: AsyncClient):
    """/brands/config without JWT should return 401。"""
    resp = await client.get("/api/v1/brands/config")
    assert resp.status_code == 401


# ── TC-BRD-06：responsecontain agency_id ─────────────────────────────────────────────
@pytest.mark.asyncio
async def test_brand_config_contains_agency_id(
    client: AsyncClient, auth_headers: dict, test_agency
):
    """The agency_id returned by GET should match the current user's agency."""
    resp = await client.get("/api/v1/brands/config", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["agency_id"] == str(test_agency.id)


# ── TC-BRD-07：multiplefieldsimultaneouslyupdate ─────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_update_multiple_fields_at_once(client: AsyncClient, auth_headers: dict):
    """once PUT cansimultaneouslyupdate multiplefield，allshould  be persist。"""
    payload = {
        "name": "MultiField Brand",
        "logo_url": "https://cdn.example.com/logo.png",
        "primary_color": "#123456",
        "secondary_color": "#ABCDEF",
        "brand_voice": "Bold and concise",
        "target_audience": "Millennial marketers",
        "website_url": "https://multibrand.io",
        "tagline": "All at once",
    }
    resp = await client.put(
        "/api/v1/brands/config", json=payload, headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    for key, value in payload.items():
        assert data[key] == value
