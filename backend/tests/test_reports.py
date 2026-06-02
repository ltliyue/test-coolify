"""
f22-pdf-reports: PDF reportgenerate + schedule + emailtest。
"""
from __future__ import annotations
import uuid
import pytest


# ── TC-01: HTML template rendering ─────────────────────────────────

def test_render_report_html():
    """HTML template renderingshould return valid HTML。"""
    from app.services.reports.generator import render_report_html

    html = render_report_html(
        agency_name="Test Agency",
        brand_color="#FF5733",
        campaigns=[
            {"platform": "meta_ads", "campaign_name": "Summer", "spend": 850.5, "impressions": 50000, "clicks": 1200, "conversions": 85},
        ],
        summary={"total_spend": 850.5, "total_impressions": 50000, "total_clicks": 1200, "total_conversions": 85},
        date_from="2026-03-01",
        date_to="2026-03-31",
    )
    assert "Test Agency" in html
    assert "Campaign Performance Report" in html
    assert "$850.50" in html
    assert "No personally identifiable information" in html


def test_render_report_empty_campaigns():
    """No campaign data should render normally (no crash)."""
    from app.services.reports.generator import render_report_html

    html = render_report_html("Empty", None, [], {"total_spend": 0, "total_impressions": 0, "total_clicks": 0, "total_conversions": 0}, "N/A", "N/A")
    assert "Empty" in html


# ── TC-02: PDF generate fallback ─────────────────────────────

def test_html_to_pdf_fallback():
    """weasyprint unavailable when should return HTML bytes as fallback。"""
    from app.services.reports.generator import html_to_pdf

    result = html_to_pdf("<html><body>Test</body></html>")
    assert isinstance(result, bytes)
    assert len(result) > 0


# ── TC-03: Schedule CRUD API ─────────────────────────────

@pytest.mark.asyncio
async def test_schedule_crud(client, auth_headers, test_agency):
    # CREATE
    resp = await client.post(
        "/api/v1/reports/schedules",
        json={
            "schedule_name": "Weekly Report",
            "frequency": "weekly",
            "recipients": ["client@example.com"],
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    schedule_id = data["id"]
    assert data["frequency"] == "weekly"
    assert data["is_active"] is True
    assert data["next_run_at"] is not None
    assert data["recipients_count"] == 1  # 1 recipient, encrypted in DB

    # LIST
    resp = await client.get("/api/v1/reports/schedules", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    # UPDATE
    resp = await client.put(
        f"/api/v1/reports/schedules/{schedule_id}",
        json={"frequency": "daily", "schedule_name": "Daily Report"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["frequency"] == "daily"

    # DELETE
    resp = await client.delete(f"/api/v1/reports/schedules/{schedule_id}", headers=auth_headers)
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_schedule_invalid_frequency(client, auth_headers, test_agency):
    resp = await client.post(
        "/api/v1/reports/schedules",
        json={"schedule_name": "Bad", "frequency": "hourly", "recipients": ["a@b.com"]},
        headers=auth_headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_schedule_empty_recipients(client, auth_headers, test_agency):
    resp = await client.post(
        "/api/v1/reports/schedules",
        json={"schedule_name": "No Recip", "frequency": "daily", "recipients": []},
        headers=auth_headers,
    )
    assert resp.status_code == 422


# ── TC-04: Manual Report Generation ──────────────────────

@pytest.mark.asyncio
async def test_generate_report(client, auth_headers, test_agency):
    resp = await client.post(
        "/api/v1/reports/generate",
        json={"report_type": "campaign_performance"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "pending"
    assert data["report_type"] == "campaign_performance"


# ── TC-05: Report History ────────────────────────────────

@pytest.mark.asyncio
async def test_report_history(client, auth_headers, test_agency):
    # first generateone
    await client.post(
        "/api/v1/reports/generate",
        json={},
        headers=auth_headers,
    )

    resp = await client.get("/api/v1/reports/history", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


# ── TC-06: Tenant Isolation ──────────────────────────────

@pytest.mark.asyncio
async def test_schedule_not_found_other_agency(client, auth_headers, test_agency):
    fake_id = str(uuid.uuid4())
    resp = await client.put(
        f"/api/v1/reports/schedules/{fake_id}",
        json={"schedule_name": "Hack"},
        headers=auth_headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_download_not_found(client, auth_headers, test_agency):
    fake_id = str(uuid.uuid4())
    resp = await client.get(f"/api/v1/reports/history/{fake_id}/download", headers=auth_headers)
    assert resp.status_code == 404


# ── TC-07: Email Sender Mock Mode ────────────────────────

@pytest.mark.asyncio
async def test_email_sender_mock():
    """SMTP not configuredshould to  mock mode，return True。"""
    from app.services.reports.email_sender import send_report_email

    result = await send_report_email(
        recipients=["test@example.com"],
        subject="Test Report",
        download_url="https://example.com/report.pdf",
        agency_name="Test Agency",
    )
    assert result is True
