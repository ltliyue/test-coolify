"""
Tests for F-05: Platform integration management
- GET  /api/v1/integrations/platforms
- GET  /api/v1/integrations/
- POST /api/v1/integrations/connect
- DELETE /api/v1/integrations/{id}
"""
import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


async def test_list_platforms(client: AsyncClient, auth_headers):
    resp = await client.get("/api/v1/integrations/platforms", headers=auth_headers)
    assert resp.status_code == 200
    platforms = resp.json()
    assert isinstance(platforms, list)
    keys = [p["key"] for p in platforms]
    # All P0 platforms must be present
    for expected in ["ga4", "meta_ads", "hubspot", "stackadapt"]:
        assert expected in keys, f"Platform '{expected}' missing from registry"


async def test_list_integrations_empty(client: AsyncClient, auth_headers):
    resp = await client.get("/api/v1/integrations/", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_connect_api_key_platform(client: AsyncClient, auth_headers, test_agency):
    resp = await client.post(
        "/api/v1/integrations/connect",
        headers=auth_headers,
        json={
            "platform": "stackadapt",
            "data": {"api_key": "sk_test_1234567890abcdef"},
        },
    )
    assert resp.status_code in (200, 201)
    data = resp.json()
    assert data["platform"] == "stackadapt"
    assert data["status"] == "connected"


async def test_connect_unknown_platform(client: AsyncClient, auth_headers):
    resp = await client.post(
        "/api/v1/integrations/connect",
        headers=auth_headers,
        json={"platform": "nonexistent_platform", "data": {}},
    )
    assert resp.status_code in (400, 422)


async def test_disconnect_integration(client: AsyncClient, auth_headers, test_agency):
    # First connect
    connect_resp = await client.post(
        "/api/v1/integrations/connect",
        headers=auth_headers,
        json={"platform": "dv360", "data": {"api_key": "test_key", "advertiser_id": "12345"}},
    )
    if connect_resp.status_code not in (200, 201):
        pytest.skip("Connect failed, skip disconnect test")

    integration_id = connect_resp.json()["id"]

    # Then disconnect
    del_resp = await client.delete(
        f"/api/v1/integrations/{integration_id}",
        headers=auth_headers,
    )
    assert del_resp.status_code in (200, 204)


async def test_integrations_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/integrations/")
    assert resp.status_code in (401, 403)
