"""
F-08：WarehouseClient DuckDB modetest。
use in-memory DuckDB（:memory:），not depend on anyexternal service。
"""
from __future__ import annotations

import pytest

# Each test uses a standalone in-memory DuckDB instance
@pytest.fixture
def wh():
    from app.core.warehouse_client import WarehouseClient
    client = WarehouseClient(backend="duckdb")
    client._db_path = ":memory:"
    client.connect()
    yield client
    client.close()


# ── TC-WH-01：Schema initialize ────────────────────────────────────────────────────
def test_duckdb_schema_initialized(wh):
    """after connecting 4 raw tablesshould auto-create。"""
    tables = wh.query("SHOW TABLES")
    table_names = {r["name"] for r in tables}
    assert "raw_ga4_events" in table_names
    assert "raw_meta_ads" in table_names
    assert "raw_hubspot_contacts" in table_names
    assert "etl_sync_state" in table_names


# ── TC-WH-02：insert_many ──────────────────────────────────────────────────────
def test_insert_many_ga4(wh):
    """Batch insert into raw_ga4_events and query it back."""
    rows = [
        {
            "agency_id": "agency-001",
            "client_id": None,
            "date": "2026-03-01",
            "property_id": "123456789",
            "sessions": 1000,
            "users": 800,
            "new_users": 300,
            "page_views": 4500,
            "bounce_rate": 0.42,
            "avg_session_duration": 185.3,
            "goal_completions": 45,
        }
    ]
    written = wh.insert_many("raw_ga4_events", rows)
    assert written == 1

    results = wh.query("SELECT * FROM raw_ga4_events")
    assert len(results) == 1
    assert results[0]["sessions"] == 1000
    assert results[0]["agency_id"] == "agency-001"


def test_insert_many_meta_ads(wh):
    """Batch insert 2 records into raw_meta_ads."""
    rows = [
        {
            "agency_id": "agency-001",
            "client_id": None,
            "date": "2026-03-01",
            "account_id": "act_123456",
            "campaign_id": "camp_001",
            "campaign_name": "Summer 2026",
            "ad_set_id": "adset_001",
            "ad_set_name": "Lookalike 1%",
            "ad_id": "ad_001",
            "impressions": 50000,
            "clicks": 1200,
            "spend": 850.50,
            "reach": 42000,
            "conversions": 85,
            "conversion_value": 4250.00,
        },
        {
            "agency_id": "agency-001",
            "client_id": "client-001",
            "date": "2026-03-02",
            "account_id": "act_123456",
            "campaign_id": "camp_002",
            "campaign_name": "Retargeting",
            "ad_set_id": "adset_002",
            "ad_set_name": "Site Visitors",
            "ad_id": "ad_002",
            "impressions": 10000,
            "clicks": 350,
            "spend": 210.00,
            "reach": 9000,
            "conversions": 25,
            "conversion_value": 1250.00,
        },
    ]
    written = wh.insert_many("raw_meta_ads", rows)
    assert written == 2

    results = wh.query("SELECT COUNT(*) AS cnt FROM raw_meta_ads")
    assert results[0]["cnt"] == 2


def test_insert_many_empty(wh):
    """empty listnot write ，return 0。"""
    written = wh.insert_many("raw_ga4_events", [])
    assert written == 0


# ── TC-WH-03：query ────────────────────────────────────────────────────────────
def test_query_returns_dict_list(wh):
    """query() return dict list，key to column name。"""
    wh.insert_many("raw_ga4_events", [{
        "agency_id": "agency-x",
        "client_id": None,
        "date": "2026-03-01",
        "property_id": "prop-1",
        "sessions": 500,
        "users": 400,
        "new_users": 100,
        "page_views": 2000,
        "bounce_rate": 0.3,
        "avg_session_duration": 120.0,
        "goal_completions": 20,
    }])
    rows = wh.query("SELECT sessions, users FROM raw_ga4_events WHERE agency_id=?", ["agency-x"])
    assert len(rows) == 1
    assert "sessions" in rows[0]
    assert rows[0]["sessions"] == 500


# ── TC-WH-04：sync_state ──────────────────────────────────────────────────────
def test_sync_state_create_and_update(wh):
    """first time update_sync_state create record，the second timeupdate。"""
    agency_id = "agency-001"
    integration_id = "integ-001"

    # initial state：does not exist
    assert wh.get_sync_state(agency_id, integration_id) is None

    # first insert
    wh.update_sync_state(agency_id, integration_id, "ga4", "cursor-abc", 100)
    state = wh.get_sync_state(agency_id, integration_id)
    assert state is not None
    assert state["records_written"] == 100
    assert state["last_cursor"] == "cursor-abc"

    # update
    wh.update_sync_state(agency_id, integration_id, "ga4", "cursor-xyz", 250)
    state2 = wh.get_sync_state(agency_id, integration_id)
    assert state2["records_written"] == 250
    assert state2["last_cursor"] == "cursor-xyz"


def test_sync_state_different_agencies(wh):
    """sync states of different agencies do not interfere。"""
    wh.update_sync_state("agency-A", "integ-1", "ga4", None, 50)
    wh.update_sync_state("agency-B", "integ-1", "meta_ads", None, 75)

    a = wh.get_sync_state("agency-A", "integ-1")
    b = wh.get_sync_state("agency-B", "integ-1")
    assert a["records_written"] == 50
    assert b["records_written"] == 75
    assert a["platform"] == "ga4"
    assert b["platform"] == "meta_ads"
