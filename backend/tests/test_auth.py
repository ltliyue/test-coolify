"""
Tests for F-02: Authentication endpoints
- POST /api/v1/auth/login
- GET  /api/v1/auth/me
"""
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_login_success(client: AsyncClient, test_user, test_agency):
    resp = await client.post("/api/v1/auth/login", json={
        "email": test_user._raw_email,  # M-02: useplaintext email login
        "password": "TestPass123!",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


async def test_login_wrong_password(client: AsyncClient, test_user):
    resp = await client.post("/api/v1/auth/login", json={
        "email": test_user._raw_email,
        "password": "WrongPassword",
    })
    assert resp.status_code == 401


async def test_login_unknown_email(client: AsyncClient):
    resp = await client.post("/api/v1/auth/login", json={
        "email": "nobody@test.com",
        "password": "TestPass123!",
    })
    assert resp.status_code == 401


async def test_get_me(client: AsyncClient, test_user, auth_headers):
    resp = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == test_user._raw_email  # M-02: /me returns decrypted plaintext
    assert data["role"] == "agency_admin"


async def test_get_me_no_token(client: AsyncClient):
    resp = await client.get("/api/v1/auth/me")
    # HTTPBearer returns 403 or 401 when no credentials; either is acceptable
    assert resp.status_code in (401, 403)


async def test_get_me_invalid_token(client: AsyncClient):
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid"})
    assert resp.status_code == 401
