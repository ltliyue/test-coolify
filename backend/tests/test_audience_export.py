"""
f21-persona-audience-export: Persona → ad-platform audience export tests.
"""
from __future__ import annotations

import uuid
import pytest
import pytest_asyncio


# ── TC-01: Translator PII filter ──────────────────────────────────────────────

def test_translator_strips_pii_fields():
    """targeting_spec should notcontain email/phone/name etc. PII。"""
    from app.services.audience_export.translator import PersonaToTargetingTranslator

    t = PersonaToTargetingTranslator()
    spec, warnings = t.translate(
        persona_name="Test Persona",
        psychographics={
            "interests": ["fitness", "tech"],
            "email": "secret@example.com",
            "phone": "555-1234",
            "demographics": {"age_min": 25, "age_max": 45, "name": "John"},
        },
        channel_preferences={"preferred": "social"},
        platform="meta_ads",
    )
    # PII should  be remove
    targeting = spec.get("targeting", {})
    assert "email" not in str(spec).lower() or "secret" not in str(spec)
    assert "phone" not in str(spec).lower() or "555" not in str(spec)
    assert targeting.get("age_min") == 25


def test_translator_empty_psychographics_warns():
    """no psychographics  when should return warning。"""
    from app.services.audience_export.translator import PersonaToTargetingTranslator

    t = PersonaToTargetingTranslator()
    spec, warnings = t.translate("Empty", None, None, "meta_ads")
    assert len(warnings) > 0
    assert "no psychographics" in warnings[0].lower()


def test_translator_meta_format():
    from app.services.audience_export.translator import PersonaToTargetingTranslator

    t = PersonaToTargetingTranslator()
    spec, _ = t.translate(
        "Fitness Fan",
        {"interests": ["yoga"], "demographics": {"countries": ["US", "CA"]}},
        {},
        "meta_ads",
        "My Custom Audience",
    )
    assert spec["name"] == "My Custom Audience"
    assert spec["targeting"]["geo_locations"]["countries"] == ["US", "CA"]


def test_translator_dv360_format():
    from app.services.audience_export.translator import PersonaToTargetingTranslator

    t = PersonaToTargetingTranslator()
    spec, _ = t.translate("Shoppers", {"interests": []}, {}, "dv360")
    assert spec["audienceType"] == "FIRST_PARTY"
    assert spec["membershipDurationDays"] == 30


def test_translator_invalid_platform():
    from app.services.audience_export.translator import PersonaToTargetingTranslator

    t = PersonaToTargetingTranslator()
    with pytest.raises(ValueError, match="Unsupported platform"):
        t.translate("Test", {}, {}, "tiktok")


# ── TC-02: Meta Client Mock ─────────────────────────────────────────────────

def test_meta_client_mock():
    from app.services.audience_export.meta_client import MetaAudienceClient

    client = MetaAudienceClient("", "")
    result = client.mock_create({"name": "Test Audience"})
    assert result["id"].startswith("mock_meta_")
    assert result["name"] == "Test Audience"


# ── TC-03: DV360 Client Mock ────────────────────────────────────────────────

def test_dv360_client_mock():
    from app.services.audience_export.dv360_client import DV360AudienceClient

    client = DV360AudienceClient("", "mock_adv")
    result = client.mock_create({"displayName": "Test Segment"})
    assert result["id"].startswith("mock_dv360_")


def test_dv360_client_invalid_advertiser():
    from app.services.audience_export.dv360_client import DV360AudienceClient

    with pytest.raises(ValueError, match="Invalid advertiser_id"):
        DV360AudienceClient("key", "../malicious")


# ── TC-04: API — export preview ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_export_preview(client, auth_headers, test_agency, test_user):
    """Preview should return targeting_spec and warnings."""
    from app.models.persona import Persona
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
    from sqlalchemy.pool import NullPool

    # first create persona
    resp = await client.post(
        "/api/v1/personas",
        json={
            "name": "Preview Test",
            "psychographics": {"interests": ["gaming"], "demographics": {"age_min": 18, "age_max": 35}},
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    persona_id = resp.json()["id"]

    # Preview
    resp = await client.get(
        f"/api/v1/personas/{persona_id}/export-audience/preview?platform=meta_ads",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["platform"] == "meta_ads"
    assert "targeting" in data["targeting_spec"]


@pytest.mark.asyncio
async def test_export_preview_invalid_platform(client, auth_headers, test_agency, test_user):
    resp = await client.post(
        "/api/v1/personas",
        json={"name": "P1"},
        headers=auth_headers,
    )
    persona_id = resp.json()["id"]

    resp = await client.get(
        f"/api/v1/personas/{persona_id}/export-audience/preview?platform=invalid",
        headers=auth_headers,
    )
    assert resp.status_code == 400


# ── TC-05: API — initiateexport ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_export(client, auth_headers, test_agency, test_user):
    """initiateexportshould create pending record。"""
    resp = await client.post(
        "/api/v1/personas",
        json={"name": "Export Test", "psychographics": {"interests": ["travel"]}},
        headers=auth_headers,
    )
    persona_id = resp.json()["id"]

    resp = await client.post(
        f"/api/v1/personas/{persona_id}/export-audience",
        json={"platform": "meta_ads"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "pending"
    assert data["platform"] == "meta_ads"
    assert data["persona_id"] == persona_id
    assert data["targeting_spec"] is not None


@pytest.mark.asyncio
async def test_create_export_nonexistent_persona(client, auth_headers, test_agency, test_user):
    fake_id = str(uuid.uuid4())
    resp = await client.post(
        f"/api/v1/personas/{fake_id}/export-audience",
        json={"platform": "dv360"},
        headers=auth_headers,
    )
    assert resp.status_code == 404


# ── TC-06: API — export history ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_persona_exports(client, auth_headers, test_agency, test_user):
    """After exporting, the record should be findable."""
    resp = await client.post(
        "/api/v1/personas",
        json={"name": "History Test"},
        headers=auth_headers,
    )
    persona_id = resp.json()["id"]

    # create twiceexport
    for platform in ["meta_ads", "dv360"]:
        await client.post(
            f"/api/v1/personas/{persona_id}/export-audience",
            json={"platform": platform},
            headers=auth_headers,
        )

    resp = await client.get(
        f"/api/v1/personas/{persona_id}/export-audience",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 2
