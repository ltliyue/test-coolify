"""
F-14: historical CSV import tests.
Covers: meta_ads / ga4 / hubspot import、autoformatdetection、edge cases、authenticationcheck。
"""
from __future__ import annotations

import io
import pytest
from httpx import AsyncClient


# ── CSV samples ───────────────────────────────────────────────────────────────
_META_ADS_CSV = (
    "campaign_id,campaign_name,adset_id,impressions,clicks,spend,date\n"
    "c001,Summer Sale,a001,10000,500,25.50,2024-01-01\n"
    "c001,Summer Sale,a002,8000,320,18.00,2024-01-01\n"
).encode("utf-8")

_GA4_CSV = (
    "date,property_id,sessions,totalUsers,newUsers,screenPageViews,bounceRate\n"
    "2024-01-01,12345,1200,900,300,4500,0.35\n"
    "2024-01-02,12345,1350,1000,250,5000,0.30\n"
).encode("utf-8")

_HUBSPOT_CSV = (
    "contact_id,email,firstname,lastname,lifecyclestage,creation date\n"
    "1,alice@test.com,Alice,Smith,lead,2024-01-01\n"
    "2,bob@test.com,Bob,Jones,customer,2024-01-02\n"
).encode("utf-8")


def _make_form(content: bytes, filename: str, platform: str = None, client_id: str = None):
    """Build multipart form data."""
    files = {"file": (filename, io.BytesIO(content), "text/csv")}
    data = {}
    if platform:
        data["platform"] = platform
    if client_id:
        data["client_id"] = client_id
    return files, data


# ── TC-IMP-01：meta_ads CSV import ──────────────────────────────────────────────
@pytest.mark.asyncio
async def test_upload_meta_ads_csv(client: AsyncClient, auth_headers: dict):
    """upload meta_ads CSV，should return 200，rows_imported=2。"""
    files, data = _make_form(_META_ADS_CSV, "meta.csv", platform="meta_ads")
    resp = await client.post(
        "/api/v1/import/upload", files=files, data=data, headers=auth_headers
    )
    assert resp.status_code == 200
    result = resp.json()
    assert result["platform"] == "meta_ads"
    assert result["rows_imported"] == 2
    assert result["rows_skipped"] == 0
    assert "Successfully imported" in result["message"]


# ── TC-IMP-02：ga4 CSV import ───────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_upload_ga4_csv(client: AsyncClient, auth_headers: dict):
    """upload ga4 CSV，should return rows_imported=2。"""
    files, data = _make_form(_GA4_CSV, "ga4.csv", platform="ga4")
    resp = await client.post(
        "/api/v1/import/upload", files=files, data=data, headers=auth_headers
    )
    assert resp.status_code == 200
    result = resp.json()
    assert result["platform"] == "ga4"
    assert result["rows_imported"] == 2


# ── TC-IMP-03：hubspot CSV import ───────────────────────────────────────────────
@pytest.mark.asyncio
async def test_upload_hubspot_csv(client: AsyncClient, auth_headers: dict):
    """upload hubspot CSV，should return rows_imported=2。"""
    files, data = _make_form(_HUBSPOT_CSV, "hubspot.csv", platform="hubspot")
    resp = await client.post(
        "/api/v1/import/upload", files=files, data=data, headers=auth_headers
    )
    assert resp.status_code == 200
    result = resp.json()
    assert result["platform"] == "hubspot"
    assert result["rows_imported"] == 2


# ── TC-IMP-04：auto-detect meta_ads format ─────────────────────────────────────────
@pytest.mark.asyncio
async def test_auto_detect_meta_ads_format(client: AsyncClient, auth_headers: dict):
    """without platform parameter when ，should auto-detectto  meta_ads。"""
    files, data = _make_form(_META_ADS_CSV, "unknown.csv")  # without platform
    resp = await client.post(
        "/api/v1/import/upload", files=files, data=data, headers=auth_headers
    )
    assert resp.status_code == 200
    result = resp.json()
    assert result["platform"] == "meta_ads"


# ── TC-IMP-05：auto-detect ga4 format ─────────────────────────────────────────────
@pytest.mark.asyncio
async def test_auto_detect_ga4_format(client: AsyncClient, auth_headers: dict):
    """GA4 CSV without platform parameter when auto-detect。"""
    files, data = _make_form(_GA4_CSV, "unknown.csv")
    resp = await client.post(
        "/api/v1/import/upload", files=files, data=data, headers=auth_headers
    )
    assert resp.status_code == 200
    assert resp.json()["platform"] == "ga4"


# ── TC-IMP-06: unsupported platform is rejected ─────────────────────────────────
@pytest.mark.asyncio
async def test_unsupported_platform_rejected(client: AsyncClient, auth_headers: dict):
    """passing unsupported  platform should return 400。"""
    files, data = _make_form(_META_ADS_CSV, "data.csv", platform="tiktok")
    resp = await client.post(
        "/api/v1/import/upload", files=files, data=data, headers=auth_headers
    )
    assert resp.status_code == 400
    assert "Unsupported platform" in resp.json()["detail"]


# ── TC-IMP-07：empty file be reject ──────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_empty_file_rejected(client: AsyncClient, auth_headers: dict):
    """uploadempty fileshould return 400。"""
    files = {"file": ("empty.csv", io.BytesIO(b""), "text/csv")}
    resp = await client.post(
        "/api/v1/import/upload",
        files=files,
        data={"platform": "meta_ads"},
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert "Empty file" in resp.json()["detail"]


# ── TC-IMP-08: returns 422 when format cannot be auto-detected ──────────────────
@pytest.mark.asyncio
async def test_undetectable_format_returns_422(client: AsyncClient, auth_headers: dict):
    """When CSV column names are unrecognizable (no platform specified), should return 422."""
    unknown_csv = b"foo,bar,baz\n1,2,3\n"
    files, data = _make_form(unknown_csv, "mystery.csv")  # without platform
    resp = await client.post(
        "/api/v1/import/upload", files=files, data=data, headers=auth_headers
    )
    assert resp.status_code == 422


# ── TC-IMP-09：unauthenticated be reject ──────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_import_requires_auth(client: AsyncClient):
    """/import/upload without JWT should return 401。"""
    files, data = _make_form(_META_ADS_CSV, "meta.csv", platform="meta_ads")
    resp = await client.post("/api/v1/import/upload", files=files, data=data)
    assert resp.status_code == 401
