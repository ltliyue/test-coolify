"""
Tests for F-00: Compliance API
- POST /api/v1/compliance/consent
- POST /api/v1/compliance/consent/withdraw
- POST /api/v1/compliance/dsar
- GET  /api/v1/compliance/dsar
- PATCH /api/v1/compliance/dsar/{id}
"""
import pytest
from httpx import AsyncClient

from app.core.compliance.anonymizer import hash_identifier


pytestmark = pytest.mark.asyncio


async def test_record_consent(client: AsyncClient, auth_headers, test_agency):
    resp = await client.post(
        "/api/v1/compliance/consent",
        headers=auth_headers,
        json={
            "agency_id": str(test_agency.id),
            "client_id": None,
            "subject_email": "user@example.com",
            "purpose": "analytics",
            "granted": True,
            "do_not_sell": False,
            "consent_text": "I agree to analytics tracking",
            "consent_version": "v1.0",
            "source": "web_form",
        },
    )
    assert resp.status_code in (200, 201)
    data = resp.json()
    assert data["purpose"] == "analytics"
    assert data["granted"] is True
    # subject_hash should be anonymized
    expected_hash = hash_identifier("user@example.com", str(test_agency.id))
    assert data["subject_hash"] == expected_hash


async def test_withdraw_consent(client: AsyncClient, auth_headers, test_agency):
    # First record
    await client.post(
        "/api/v1/compliance/consent",
        headers=auth_headers,
        json={
            "agency_id": str(test_agency.id),
            "client_id": None,
            "subject_email": "withdraw@example.com",
            "purpose": "marketing",
            "granted": True,
            "do_not_sell": False,
            "consent_text": "I agree",
            "consent_version": "v1.0",
        },
    )
    # Then withdraw
    resp = await client.post(
        "/api/v1/compliance/consent/withdraw",
        headers=auth_headers,
        json={
            "subject_email": "withdraw@example.com",
            "purpose": "marketing",
            "agency_id": str(test_agency.id),
        },
    )
    assert resp.status_code == 200


async def test_submit_dsar_gdpr(client: AsyncClient, auth_headers, test_agency):
    resp = await client.post(
        "/api/v1/compliance/dsar",
        headers=auth_headers,
        json={
            "agency_id": str(test_agency.id),
            "request_type": "delete",
            "regulation": "gdpr",
            "subject_email": "delete-me@example.com",
        },
    )
    assert resp.status_code in (200, 201)
    data = resp.json()
    assert data["request_type"] == "delete"
    assert data["regulation"] == "gdpr"
    assert data["status"] == "pending"
    assert "due_date" in data
    # GDPR due_date should be ~30 days from now
    from datetime import datetime, timezone, timedelta
    due = datetime.fromisoformat(data["due_date"].replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    assert 28 <= (due - now).days <= 31


async def test_submit_dsar_ccpa_due_date(client: AsyncClient, auth_headers, test_agency):
    resp = await client.post(
        "/api/v1/compliance/dsar",
        headers=auth_headers,
        json={
            "agency_id": str(test_agency.id),
            "request_type": "access",
            "regulation": "ccpa",
            "subject_email": "ccpa@example.com",
        },
    )
    assert resp.status_code in (200, 201)
    data = resp.json()
    from datetime import datetime, timezone
    due = datetime.fromisoformat(data["due_date"].replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    # CCPA = 45 days
    assert 43 <= (due - now).days <= 46


async def test_list_dsar(client: AsyncClient, auth_headers, test_agency):
    resp = await client.get("/api/v1/compliance/dsar", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_anonymizer_hash_consistency():
    """Unit test: same inputs always produce same hash."""
    h1 = hash_identifier("user@example.com", "tenant-123")
    h2 = hash_identifier("user@example.com", "tenant-123")
    assert h1 == h2
    assert len(h1) == 64  # SHA-256 hex


async def test_anonymizer_different_tenants():
    """Unit test: same email, different tenants → different hashes."""
    h1 = hash_identifier("user@example.com", "tenant-A")
    h2 = hash_identifier("user@example.com", "tenant-B")
    assert h1 != h2


async def test_phi_detector_finds_email():
    """Unit test: PHI detector identifies email addresses."""
    from app.core.compliance.phi_detector import scan_record
    result = scan_record({"message": "Contact john@example.com for details"})
    assert result.has_phi
    phi_types = [f["type"] for f in result.findings]
    assert "email" in phi_types


async def test_phi_detector_clean_record():
    """Unit test: PHI detector passes clean records."""
    from app.core.compliance.phi_detector import scan_record
    result = scan_record({"campaign_id": "abc123", "impressions": 5000, "platform": "ga4"})
    assert not result.has_phi


async def test_compliance_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/compliance/dsar")
    assert resp.status_code in (401, 403)
