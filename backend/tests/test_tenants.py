"""
Tests for F-01: Tenant management endpoints
- POST /api/v1/tenants/agencies
- GET  /api/v1/tenants/agencies
- POST /api/v1/tenants/agencies/{id}/clients
- GET  /api/v1/tenants/agencies/{id}/clients
"""
import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


async def test_list_agencies(client: AsyncClient, auth_headers, test_agency):
    resp = await client.get("/api/v1/tenants/agencies", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(a["name"] == "Test Agency" for a in data)


async def test_get_agency_detail(client: AsyncClient, auth_headers, test_agency):
    resp = await client.get(f"/api/v1/tenants/agencies/{test_agency.id}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Test Agency"


async def test_create_client(client: AsyncClient, auth_headers, test_agency):
    resp = await client.post(
        f"/api/v1/tenants/agencies/{test_agency.id}/clients",
        headers=auth_headers,
        json={
            "name": "ACME Corp",
            "agency_id": str(test_agency.id),
            "verticals": ["healthcare", "retail"],
        },
    )
    assert resp.status_code in (200, 201)
    data = resp.json()
    assert data["name"] == "ACME Corp"
    assert "slug" in data


async def test_list_clients(client: AsyncClient, auth_headers, test_agency):
    resp = await client.get(
        f"/api/v1/tenants/agencies/{test_agency.id}/clients",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_agencies_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/tenants/agencies")
    assert resp.status_code in (401, 403)
