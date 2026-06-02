"""
F-15: field-mapping tests.
Covers: CRUD, versioning, rollback, preview, canonical schema, platform templates.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient


# ── TC-FM-01: empty list ────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_list_field_mappings_empty(client: AsyncClient, auth_headers: dict):
    """A fresh Agency should return an empty field-mapping list."""
    resp = await client.get("/api/v1/field-mappings", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


# ── TC-FM-02: create field mapping ───────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_create_field_mapping(client: AsyncClient, auth_headers: dict):
    """POST creates a ga4 mapping; returns 201 with id/platform/current_version=1."""
    payload = {"platform": "ga4", "name": "GA4 Default", "use_default_template": True}
    resp = await client.post(
        "/api/v1/field-mappings", json=payload, headers=auth_headers
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["platform"] == "ga4"
    assert data["name"] == "GA4 Default"
    assert data["current_version"] == 1
    assert "id" in data
    assert data["is_active"] is True


# ── TC-FM-03: get single mapping ───────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_get_field_mapping_by_id(client: AsyncClient, auth_headers: dict):
    """GET /{id} should return the just-created mapping."""
    create_resp = await client.post(
        "/api/v1/field-mappings",
        json={"platform": "meta_ads", "name": "Meta Ads Mapping"},
        headers=auth_headers,
    )
    mapping_id = create_resp.json()["id"]

    resp = await client.get(
        f"/api/v1/field-mappings/{mapping_id}", headers=auth_headers
    )
    assert resp.status_code == 200
    assert resp.json()["id"] == mapping_id


# ── TC-FM-04: update creates a new version ─────────────────────────────────────────
@pytest.mark.asyncio
async def test_update_field_mapping_bumps_version(
    client: AsyncClient, auth_headers: dict
):
    """PUT update bumps current_version from 1 to 2."""
    create_resp = await client.post(
        "/api/v1/field-mappings",
        json={"platform": "ga4", "name": "GA4 v1"},
        headers=auth_headers,
    )
    mapping_id = create_resp.json()["id"]
    assert create_resp.json()["current_version"] == 1

    # update mapping (MappingEntry requires target_field)
    update_payload = {
        "mappings": [
            {
                "source_field": "sessions",
                "target_field": "sessions",
            }
        ],
        "change_summary": "Add sessions mapping",
    }
    resp = await client.put(
        f"/api/v1/field-mappings/{mapping_id}",
        json=update_payload,
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["current_version"] == 2


# ── TC-FM-05: soft delete ─────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_delete_field_mapping_soft(client: AsyncClient, auth_headers: dict):
    """After DELETE, GET should return 404 (soft delete; no longer in list)."""
    create_resp = await client.post(
        "/api/v1/field-mappings",
        json={"platform": "hubspot", "name": "HubSpot Mapping"},
        headers=auth_headers,
    )
    mapping_id = create_resp.json()["id"]

    del_resp = await client.delete(
        f"/api/v1/field-mappings/{mapping_id}", headers=auth_headers
    )
    assert del_resp.status_code == 204

    # should no longer appear in list
    list_resp = await client.get("/api/v1/field-mappings", headers=auth_headers)
    ids = [m["id"] for m in list_resp.json()]
    assert mapping_id not in ids

    # direct GET should also return 404
    get_resp = await client.get(
        f"/api/v1/field-mappings/{mapping_id}", headers=auth_headers
    )
    assert get_resp.status_code == 404


# ── TC-FM-06: version history list ────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_list_versions(client: AsyncClient, auth_headers: dict):
    """After create + update, /versions should return 2 version snapshots."""
    create_resp = await client.post(
        "/api/v1/field-mappings",
        json={"platform": "ga4", "name": "GA4 Versioned"},
        headers=auth_headers,
    )
    mapping_id = create_resp.json()["id"]

    # perform one update
    await client.put(
        f"/api/v1/field-mappings/{mapping_id}",
        json={"mappings": [], "change_summary": "Empty update"},
        headers=auth_headers,
    )

    resp = await client.get(
        f"/api/v1/field-mappings/{mapping_id}/versions", headers=auth_headers
    )
    assert resp.status_code == 200
    versions = resp.json()
    assert len(versions) == 2
    # version numbers should be [2, 1] (descending)
    version_nums = [v["version"] for v in versions]
    assert version_nums == sorted(version_nums, reverse=True)


# ── TC-FM-07: version rollback ────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_rollback_to_version(client: AsyncClient, auth_headers: dict):
    """Rolling back to v1 should create v3 with the same mapping_config as v1."""
    # create (v1)
    create_resp = await client.post(
        "/api/v1/field-mappings",
        json={"platform": "meta_ads", "name": "Meta Rollback"},
        headers=auth_headers,
    )
    mapping_id = create_resp.json()["id"]
    v1_config = create_resp.json()["mapping_config"]

    # update (v2)
    await client.put(
        f"/api/v1/field-mappings/{mapping_id}",
        json={
            "mappings": [{"source_field": "clicks", "target_field": "clicks"}],
            "change_summary": "Add clicks",
        },
        headers=auth_headers,
    )

    # fetch v1 version id
    versions_resp = await client.get(
        f"/api/v1/field-mappings/{mapping_id}/versions", headers=auth_headers
    )
    versions = versions_resp.json()
    v1_entry = next(v for v in versions if v["version"] == 1)
    v1_id = v1_entry["id"]

    # roll back to v1
    rollback_resp = await client.post(
        f"/api/v1/field-mappings/{mapping_id}/versions/{v1_id}/rollback",
        headers=auth_headers,
    )
    assert rollback_resp.status_code == 200
    data = rollback_resp.json()
    assert data["current_version"] == 3
    assert data["mapping_config"] == v1_config


# ── TC-FM-08: preview transform ────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_preview_transform(client: AsyncClient, auth_headers: dict):
    """POST /preview should return transformed rows without touching DB data."""
    create_resp = await client.post(
        "/api/v1/field-mappings",
        json={"platform": "ga4", "name": "GA4 Preview"},
        headers=auth_headers,
    )
    mapping_id = create_resp.json()["id"]

    preview_payload = {
        "mappings": [
            {
                "source_field": "sessions",
                "target_field": "sessions",
            }
        ],
        "sample_data": [{"sessions": "1200", "totalUsers": "900"}],
    }
    resp = await client.post(
        f"/api/v1/field-mappings/{mapping_id}/preview",
        json=preview_payload,
        headers=auth_headers,
    )
    assert resp.status_code == 200
    results = resp.json()
    assert isinstance(results, list)
    assert len(results) == 1
    row = results[0]
    assert "source" in row
    assert "transformed" in row
    assert "warnings" in row


# ── TC-FM-09: canonical field schema ─────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_get_canonical_schema(client: AsyncClient, auth_headers: dict):
    """GET /canonical-schema should return a non-empty list with name/type/category/description per entry."""
    resp = await client.get(
        "/api/v1/field-mappings/canonical-schema", headers=auth_headers
    )
    assert resp.status_code == 200
    fields = resp.json()
    assert len(fields) > 0
    first = fields[0]
    for key in ("name", "type", "category", "description"):
        assert key in first


# ── TC-FM-10: platform raw fields list ───────────────────────────────────────────────
@pytest.mark.asyncio
async def test_get_platform_raw_fields(client: AsyncClient, auth_headers: dict):
    """GET /platforms/ga4/raw-fields should return GA4 raw fields."""
    resp = await client.get(
        "/api/v1/field-mappings/platforms/ga4/raw-fields", headers=auth_headers
    )
    assert resp.status_code == 200
    fields = resp.json()
    assert len(fields) > 0
    # each field should include a name
    assert all("name" in f for f in fields)


# ── TC-FM-11: platform default template ───────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_get_default_template(client: AsyncClient, auth_headers: dict):
    """GET /platforms/meta_ads/default-template should return platform and mappings."""
    resp = await client.get(
        "/api/v1/field-mappings/platforms/meta_ads/default-template",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["platform"] == "meta_ads"
    assert "mappings" in data
    assert isinstance(data["mappings"], list)


# ── TC-FM-12: invalid platform returns 404 ────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_invalid_platform_returns_404(client: AsyncClient, auth_headers: dict):
    """Requesting raw fields for a non-existent platform should return 404."""
    resp = await client.get(
        "/api/v1/field-mappings/platforms/nonexistent/raw-fields",
        headers=auth_headers,
    )
    assert resp.status_code == 404


# ── TC-FM-13: authentication check ────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_field_mapping_requires_auth(client: AsyncClient):
    """/field-mappings without JWT should return 401."""
    resp = await client.get("/api/v1/field-mappings")
    assert resp.status_code == 401


# ── TC-FM-14: list filtered by platform ─────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_list_field_mappings_filter_by_platform(
    client: AsyncClient, auth_headers: dict
):
    """?platform=ga4 filter should return only GA4 mappings, not meta_ads."""
    # create ga4 mapping
    await client.post(
        "/api/v1/field-mappings",
        json={"platform": "ga4", "name": "GA4 Filtered"},
        headers=auth_headers,
    )
    # create meta_ads mapping
    await client.post(
        "/api/v1/field-mappings",
        json={"platform": "meta_ads", "name": "Meta Filtered"},
        headers=auth_headers,
    )

    resp = await client.get(
        "/api/v1/field-mappings?platform=ga4", headers=auth_headers
    )
    assert resp.status_code == 200
    items = resp.json()
    assert all(item["platform"] == "ga4" for item in items)
    assert len(items) == 1
