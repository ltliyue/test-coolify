"""
f19-campaigns: unified Campaign view + Budget Config CRUD test。
Campaign dataquery uses DuckDB mock，Budget Config use PG（via conftest fixtures）。
"""
from __future__ import annotations

import pytest
import pytest_asyncio

from app.services.campaign_query import CampaignQueryService


@pytest.fixture
def warehouse():
    """Standalone in-memory DuckDB warehouse instance with the mart_campaign_unified view."""
    from app.core.warehouse_client import WarehouseClient
    wh = WarehouseClient(backend="duckdb")
    wh._db_path = ":memory:"
    wh.connect()
    # Create mart_campaign_unified as a regular table (for tests)
    wh._conn.execute("""
        CREATE TABLE IF NOT EXISTS mart_campaign_unified (
            agency_id VARCHAR NOT NULL,
            client_id VARCHAR,
            date DATE NOT NULL,
            platform VARCHAR NOT NULL,
            campaign_id VARCHAR,
            campaign_name VARCHAR,
            impressions INTEGER DEFAULT 0,
            clicks INTEGER DEFAULT 0,
            spend FLOAT DEFAULT 0,
            reach INTEGER DEFAULT 0,
            conversions INTEGER DEFAULT 0,
            conversion_value FLOAT DEFAULT 0
        )
    """)
    yield wh
    wh.close()


@pytest.fixture
def seeded_warehouse(warehouse):
    """inserttest campaign data。"""
    rows = [
        ("ag1", None, "2026-03-15", "meta_ads", "c1", "Summer Campaign", 50000, 1200, 850.50, 42000, 85, 4250.0),
        ("ag1", None, "2026-03-16", "meta_ads", "c1", "Summer Campaign", 48000, 1100, 800.00, 40000, 78, 3900.0),
        ("ag1", None, "2026-03-15", "dv360", "d1", "Programmatic Q1", 200000, 3500, 1250.00, 0, 120, 6000.0),
        ("ag1", None, "2026-03-15", "stackadapt", "s1", "Native Display", 150000, 2800, 920.00, 0, 95, 4750.0),
        ("ag2", None, "2026-03-15", "meta_ads", "c2", "Other Agency", 10000, 200, 100.00, 8000, 10, 500.0),
    ]
    warehouse._conn.executemany(
        "INSERT INTO mart_campaign_unified VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        rows,
    )
    return warehouse


# ── TC-01: CampaignQueryService.list_campaigns ───────────────────────────────

def test_list_campaigns_returns_all_for_agency(seeded_warehouse):
    svc = CampaignQueryService(seeded_warehouse)
    results = svc.list_campaigns("ag1")
    assert len(results) == 4  # 2 meta + 1 dv360 + 1 stackadapt


def test_list_campaigns_filters_by_platform(seeded_warehouse):
    svc = CampaignQueryService(seeded_warehouse)
    results = svc.list_campaigns("ag1", platform="dv360")
    assert len(results) == 1
    assert results[0]["platform"] == "dv360"


def test_list_campaigns_filters_by_date(seeded_warehouse):
    svc = CampaignQueryService(seeded_warehouse)
    results = svc.list_campaigns("ag1", date_from="2026-03-16", date_to="2026-03-16")
    assert len(results) == 1
    assert results[0]["campaign_name"] == "Summer Campaign"


def test_list_campaigns_pagination(seeded_warehouse):
    svc = CampaignQueryService(seeded_warehouse)
    page1 = svc.list_campaigns("ag1", limit=2, offset=0)
    page2 = svc.list_campaigns("ag1", limit=2, offset=2)
    assert len(page1) == 2
    assert len(page2) == 2


def test_list_campaigns_tenant_isolation(seeded_warehouse):
    svc = CampaignQueryService(seeded_warehouse)
    ag1 = svc.list_campaigns("ag1")
    ag2 = svc.list_campaigns("ag2")
    assert len(ag1) == 4
    assert len(ag2) == 1


# ── TC-02: CampaignQueryService.get_summary ──────────────────────────────────

def test_get_summary(seeded_warehouse):
    svc = CampaignQueryService(seeded_warehouse)
    summary = svc.get_summary("ag1")
    assert summary["total_spend"] == pytest.approx(3820.50, 0.01)
    assert summary["total_conversions"] == 378
    assert "meta_ads" in summary["platform_breakdown"]
    assert "dv360" in summary["platform_breakdown"]
    assert "stackadapt" in summary["platform_breakdown"]


def test_get_summary_tenant_isolation(seeded_warehouse):
    svc = CampaignQueryService(seeded_warehouse)
    summary = svc.get_summary("ag2")
    assert summary["total_spend"] == pytest.approx(100.00, 0.01)


# ── TC-03: CampaignQueryService.get_campaign_metrics ─────────────────────────

def test_get_campaign_metrics(seeded_warehouse):
    svc = CampaignQueryService(seeded_warehouse)
    metrics = svc.get_campaign_metrics("ag1", "meta_ads", "c1")
    assert len(metrics) == 2  # 2 days of data


def test_get_campaign_metrics_empty(seeded_warehouse):
    svc = CampaignQueryService(seeded_warehouse)
    metrics = svc.get_campaign_metrics("ag1", "meta_ads", "nonexistent")
    assert len(metrics) == 0


# ── TC-04: Budget Config CRUD（via API） ────────────────────────────────────

@pytest.mark.asyncio
async def test_budget_config_crud(client, auth_headers, test_agency):
    # CREATE
    resp = await client.post(
        "/api/v1/campaigns/budget-configs",
        json={
            "platform": "meta_ads",
            "external_campaign_id": "camp_123",
            "campaign_name": "Test Campaign",
            "daily_budget": 100.00,
            "pacing_alert_threshold": 0.15,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    config_id = data["id"]
    assert data["platform"] == "meta_ads"
    assert data["daily_budget"] == 100.00

    # LIST
    resp = await client.get("/api/v1/campaigns/budget-configs", headers=auth_headers)
    assert resp.status_code == 200
    configs = resp.json()
    assert len(configs) >= 1

    # UPDATE
    resp = await client.put(
        f"/api/v1/campaigns/budget-configs/{config_id}",
        json={"daily_budget": 200.00},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["daily_budget"] == 200.00

    # DELETE
    resp = await client.delete(
        f"/api/v1/campaigns/budget-configs/{config_id}",
        headers=auth_headers,
    )
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_budget_config_unique_constraint(client, auth_headers, test_agency):
    """Duplicate (platform, external_campaign_id) should return 409."""
    body = {
        "platform": "dv360",
        "external_campaign_id": "dup_001",
        "daily_budget": 50.00,
    }
    resp1 = await client.post("/api/v1/campaigns/budget-configs", json=body, headers=auth_headers)
    assert resp1.status_code == 201

    resp2 = await client.post("/api/v1/campaigns/budget-configs", json=body, headers=auth_headers)
    assert resp2.status_code == 409


@pytest.mark.asyncio
async def test_budget_config_not_found(client, auth_headers, test_agency):
    """accessnon-existent config should return 404。"""
    import uuid
    fake_id = str(uuid.uuid4())
    resp = await client.put(
        f"/api/v1/campaigns/budget-configs/{fake_id}",
        json={"daily_budget": 999},
        headers=auth_headers,
    )
    assert resp.status_code == 404
