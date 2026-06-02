"""
F-06: ETL pipeline framework tests.
Uses DuckDB in-memory mode + mock adapters, with no dependency on any external API or database.
"""
from __future__ import annotations

import pytest

from app.services.etl.adapters.ga4 import GA4Adapter
from app.services.etl.adapters.meta_ads import MetaAdsAdapter
from app.services.etl.adapters.hubspot import HubSpotAdapter
from app.services.etl.runner import ETLRunner


@pytest.fixture
def warehouse():
    """Standalone in-memory DuckDB warehouse instance."""
    from app.core.warehouse_client import WarehouseClient
    wh = WarehouseClient(backend="duckdb")
    wh._db_path = ":memory:"
    wh.connect()
    yield wh
    wh.close()


# ── TC-ETL-01：GA4 mock adapter ────────────────────────────────────────────────
def test_ga4_adapter_mock_returns_data():
    """GA4 mock modeshould return 1   synthetic record。"""
    adapter = GA4Adapter(
        credentials={"mock": True},
        agency_id="agency-001",
    )
    records, cursor = adapter.fetch("2026-03-01", "2026-03-31")
    assert len(records) == 1
    assert records[0]["sessions"] == 1000
    assert records[0]["property_id"] == "123456789"
    assert cursor is None


def test_ga4_adapter_get_raw_table():
    adapter = GA4Adapter(credentials={}, agency_id="agency-001")
    assert adapter.get_raw_table() == "raw_ga4_events"


# ── TC-ETL-02：Meta Ads mock adapter ───────────────────────────────────────────
def test_meta_ads_adapter_mock_returns_data():
    """Meta Ads mock modeshould return 1   synthetic record。"""
    adapter = MetaAdsAdapter(
        credentials={"mock": True},
        agency_id="agency-001",
    )
    records, cursor = adapter.fetch("2026-03-01", "2026-03-31")
    assert len(records) == 1
    assert records[0]["impressions"] == 50000
    assert records[0]["campaign_name"] == "Summer 2026"
    assert cursor is None


def test_meta_ads_adapter_get_raw_table():
    adapter = MetaAdsAdapter(credentials={}, agency_id="agency-001")
    assert adapter.get_raw_table() == "raw_meta_ads"


# ── TC-ETL-03：HubSpot mock adapter ────────────────────────────────────────────
def test_hubspot_adapter_mock_returns_data():
    """HubSpot mock mode should return 2 synthetic contact records."""
    adapter = HubSpotAdapter(
        credentials={"mock": True},
        agency_id="agency-001",
    )
    records, cursor = adapter.fetch("2026-03-01", "2026-03-31")
    assert len(records) == 2
    assert records[0]["email_hash"] == "jane.doe@example.com"
    assert records[1]["lifecycle_stage"] == "customer"
    assert cursor is None


def test_hubspot_adapter_get_raw_table():
    adapter = HubSpotAdapter(credentials={}, agency_id="agency-001")
    assert adapter.get_raw_table() == "raw_hubspot_contacts"


# ── TC-ETL-04：ETLRunner end-to-end（GA4）────────────────────────────────────────
def test_etl_runner_ga4_end_to_end(warehouse):
    """
    ETLRunner should ：
    1. via GA4 mock adapter fetch 1  record
    2. inject agency_id
    3. write to DuckDB raw_ga4_events table
    4. update etl_sync_state
    5. return ETLresult.success=True, records_written=1
    """
    adapter = GA4Adapter(
        credentials={"mock": True},
        agency_id="agency-001",
        client_id="client-001",
    )
    runner = ETLRunner(warehouse)
    result = runner.run(adapter, "2026-03-01", "2026-03-31", "integ-001")

    assert result.success is True
    assert result.records_fetched == 1
    assert result.records_written == 1
    assert result.records_skipped == 0
    assert result.platform == "ga4"

    # verify written towarehouse
    rows = warehouse.query("SELECT * FROM raw_ga4_events")
    assert len(rows) == 1
    assert rows[0]["agency_id"] == "agency-001"
    assert rows[0]["client_id"] == "client-001"
    assert rows[0]["sessions"] == 1000

    # verify sync state update
    state = warehouse.get_sync_state("agency-001", "integ-001")
    assert state is not None
    assert state["records_written"] == 1


# ── TC-ETL-05：ETLRunner end-to-end（Meta Ads）────────────────────────────────────
def test_etl_runner_meta_ads_end_to_end(warehouse):
    """ETLRunner completes a full ETL via the Meta Ads mock adapter."""
    adapter = MetaAdsAdapter(
        credentials={"mock": True},
        agency_id="agency-002",
    )
    runner = ETLRunner(warehouse)
    result = runner.run(adapter, "2026-03-01", "2026-03-31", "integ-002")

    assert result.success is True
    assert result.records_written == 1

    rows = warehouse.query("SELECT * FROM raw_meta_ads")
    assert len(rows) == 1
    assert rows[0]["campaign_name"] == "Summer 2026"
    assert rows[0]["agency_id"] == "agency-002"


# ── TC-ETL-06：ETLRunner end-to-end（HubSpot）─────────────────────────────────────
def test_etl_runner_hubspot_end_to_end(warehouse):
    """ETLRunner completes a full ETL via the HubSpot mock adapter, writing 2 contacts."""
    adapter = HubSpotAdapter(
        credentials={"mock": True},
        agency_id="agency-003",
        client_id="client-003",
    )
    runner = ETLRunner(warehouse)
    result = runner.run(adapter, "2026-03-01", "2026-03-31", "integ-003")

    assert result.success is True
    assert result.records_fetched == 2
    assert result.records_written == 2

    rows = warehouse.query("SELECT * FROM raw_hubspot_contacts")
    assert len(rows) == 2


# ── TC-ETL-07：PHI detection does not block clean record ─────────────────────────────────────
def test_etl_runner_clean_record_passes_phi_check(warehouse):
    """no PHI field recordshould directlyvia，not skipped。"""
    adapter = GA4Adapter(
        credentials={"mock": True},  # mock datano PHI
        agency_id="agency-phi",
    )
    runner = ETLRunner(warehouse)
    result = runner.run(adapter, "2026-03-01", "2026-03-31", "integ-phi")

    assert result.success is True
    assert result.records_skipped == 0


# ── TC-ETL-08：multi-platformdo not interfere with each other ─────────────────────────────────────────────────
def test_etl_runner_multiple_platforms_isolated(warehouse):
    """GA4  and  Meta Ads eachwritetheir owntable，do not interfere with each other。"""
    ga4 = GA4Adapter(credentials={"mock": True}, agency_id="agency-x")
    meta = MetaAdsAdapter(credentials={"mock": True}, agency_id="agency-x")
    runner = ETLRunner(warehouse)

    runner.run(ga4, "2026-03-01", "2026-03-31", "integ-ga4")
    runner.run(meta, "2026-03-01", "2026-03-31", "integ-meta")

    ga4_rows = warehouse.query("SELECT * FROM raw_ga4_events")
    meta_rows = warehouse.query("SELECT * FROM raw_meta_ads")
    assert len(ga4_rows) == 1
    assert len(meta_rows) == 1
