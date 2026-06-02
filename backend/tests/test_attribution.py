"""
F-12：Attribution Agent test。
Covers: generate attribution report, list, get details, authentication checks.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient


# ── TC-ATT-01: generate attribution report ──────────────────────────────────────
@pytest.mark.asyncio
async def test_generate_attribution_report(client: AsyncClient, auth_headers: dict):
    """POST /attribution/report should return 201，status=completed。"""
    payload = {
        "title": "Q1 2024 Attribution",
        "prompt": "Analyze attribution for all channels in Q1",
        "report_type": "multi_touch",
    }
    resp = await client.post(
        "/api/v1/attribution/report", json=payload, headers=auth_headers
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Q1 2024 Attribution"
    assert data["report_type"] == "multi_touch"
    assert data["status"] == "completed"
    assert data["results"] is not None
    assert "id" in data


# ── TC-ATT-02: report contains attribution analysis result ──────────────────────
@pytest.mark.asyncio
async def test_attribution_report_has_results(client: AsyncClient, auth_headers: dict):
    """The report's results field should contain channels and attribution data."""
    resp = await client.post(
        "/api/v1/attribution/report",
        json={"title": "Test Report", "prompt": "Attribution analysis"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    results = resp.json()["results"]
    assert isinstance(results, dict)
    # mock datashould contain channels
    assert "channels" in results or "attribution_model" in results


# ── TC-ATT-03: list attribution reports ─────────────────────────────────────────
@pytest.mark.asyncio
async def test_list_attribution_reports(client: AsyncClient, auth_headers: dict):
    """After generation, GET /reports should return a non-empty list."""
    await client.post(
        "/api/v1/attribution/report",
        json={"title": "List Test"},
        headers=auth_headers,
    )

    resp = await client.get("/api/v1/attribution/reports", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["title"] == "List Test"


# ── TC-ATT-04：get singlereport ──────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_get_attribution_report_by_id(client: AsyncClient, auth_headers: dict):
    """GET /reports/{id} should return the corresponding report."""
    create_resp = await client.post(
        "/api/v1/attribution/report",
        json={"title": "Get By Id"},
        headers=auth_headers,
    )
    report_id = create_resp.json()["id"]

    resp = await client.get(
        f"/api/v1/attribution/reports/{report_id}", headers=auth_headers
    )
    assert resp.status_code == 200
    assert resp.json()["id"] == report_id
    assert resp.json()["title"] == "Get By Id"


# ── TC-ATT-05：non-existentreportreturn 404 ──────────────────────────────────────────
@pytest.mark.asyncio
async def test_get_nonexistent_report_404(client: AsyncClient, auth_headers: dict):
    """request non-existent  report ID should return 404。"""
    import uuid
    resp = await client.get(
        f"/api/v1/attribution/reports/{uuid.uuid4()}", headers=auth_headers
    )
    assert resp.status_code == 404


# ── TC-ATT-06：report containing daterange ────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_attribution_with_date_range(client: AsyncClient, auth_headers: dict):
    """Passing date_range_start/end should be stored correctly."""
    resp = await client.post(
        "/api/v1/attribution/report",
        json={
            "title": "Date Range Test",
            "date_range_start": "2024-01-01",
            "date_range_end": "2024-03-31",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["date_range_start"] == "2024-01-01"
    assert data["date_range_end"] == "2024-03-31"


# ── TC-ATT-07：reportcontaining insights field ──────────────────────────────────────────
@pytest.mark.asyncio
async def test_attribution_report_has_insights(client: AsyncClient, auth_headers: dict):
    """The attribution report should contain insights (a recommendation summary from the LLM)."""
    resp = await client.post(
        "/api/v1/attribution/report",
        json={"title": "Insights Test"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    # insights from recommendations merge
    assert data["insights"] is not None or data["insights"] == ""


# ── TC-ATT-08：authenticationcheck ──────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_attribution_requires_auth(client: AsyncClient):
    """/attribution/reports without JWT should return 401。"""
    resp = await client.get("/api/v1/attribution/reports")
    assert resp.status_code == 401


# ── TC-ATT-09：agency_id bind ────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_attribution_bound_to_agency(
    client: AsyncClient, auth_headers: dict, test_agency
):
    """The report's agency_id should match the current user's agency."""
    resp = await client.post(
        "/api/v1/attribution/report",
        json={"title": "Agency Binding"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["agency_id"] == str(test_agency.id)
