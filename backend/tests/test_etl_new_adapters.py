"""
f20-etl-adapters: Quorum / LeadRX / LiveRamp / DV360 / StackAdapt test。
Uses DuckDB in-memory mode + mock adapters.
"""
from __future__ import annotations

import pytest

from app.services.etl.adapters.quorum import QuorumAdapter
from app.services.etl.adapters.leadrx import LeadRXAdapter
from app.services.etl.adapters.liveramp import LiveRampAdapter
from app.services.etl.adapters.dv360 import DV360Adapter
from app.services.etl.adapters.stackadapt import StackAdaptAdapter
from app.services.etl.runner import ETLRunner


@pytest.fixture
def warehouse():
    from app.core.warehouse_client import WarehouseClient
    wh = WarehouseClient(backend="duckdb")
    wh._db_path = ":memory:"
    wh.connect()
    yield wh
    wh.close()


# ── TC-01: Quorum Adapter ────────────────────────────────────────────────────

def test_quorum_adapter_mock():
    adapter = QuorumAdapter(credentials={"mock": True}, agency_id="agency-001")
    records, cursor = adapter.fetch("2026-03-01", "2026-03-31")
    assert len(records) == 2
    assert records[0]["audience_id"] == "aud_001"
    assert records[0]["category"] == "advocacy"
    assert cursor is None


def test_quorum_adapter_raw_table():
    adapter = QuorumAdapter(credentials={}, agency_id="agency-001")
    assert adapter.get_raw_table() == "raw_quorum"


def test_quorum_etl_end_to_end(warehouse):
    adapter = QuorumAdapter(credentials={"mock": True}, agency_id="agency-q")
    runner = ETLRunner(warehouse)
    result = runner.run(adapter, "2026-03-01", "2026-03-31", "integ-q")
    assert result.success is True
    assert result.records_written == 2
    rows = warehouse.query("SELECT * FROM raw_quorum")
    assert len(rows) == 2
    assert rows[0]["agency_id"] == "agency-q"


# ── TC-02: LeadRX Adapter ────────────────────────────────────────────────────

def test_leadrx_adapter_mock():
    adapter = LeadRXAdapter(credentials={"mock": True}, agency_id="agency-001")
    records, cursor = adapter.fetch("2026-03-01", "2026-03-31")
    assert len(records) == 2
    assert records[0]["touchpoint_channel"] == "paid_search"
    assert records[0]["attribution_weight"] == 0.4
    assert cursor is None


def test_leadrx_adapter_raw_table():
    adapter = LeadRXAdapter(credentials={}, agency_id="agency-001")
    assert adapter.get_raw_table() == "raw_leadrx"


def test_leadrx_etl_end_to_end(warehouse):
    adapter = LeadRXAdapter(credentials={"mock": True}, agency_id="agency-l")
    runner = ETLRunner(warehouse)
    result = runner.run(adapter, "2026-03-01", "2026-03-31", "integ-l")
    assert result.success is True
    assert result.records_written == 2


# ── TC-03: LiveRamp Adapter ──────────────────────────────────────────────────

def test_liveramp_adapter_mock():
    adapter = LiveRampAdapter(credentials={"mock": True}, agency_id="agency-001")
    records, cursor = adapter.fetch("2026-03-01", "2026-03-31")
    assert len(records) == 2
    assert records[0]["segment_name"] == "High Value Shoppers"
    assert records[0]["match_type"] == "email"
    assert cursor is None


def test_liveramp_adapter_raw_table():
    adapter = LiveRampAdapter(credentials={}, agency_id="agency-001")
    assert adapter.get_raw_table() == "raw_liveramp"


def test_liveramp_etl_end_to_end(warehouse):
    adapter = LiveRampAdapter(credentials={"mock": True}, agency_id="agency-lr")
    runner = ETLRunner(warehouse)
    result = runner.run(adapter, "2026-03-01", "2026-03-31", "integ-lr")
    assert result.success is True
    assert result.records_written == 2


# ── TC-04: DV360 Adapter ─────────────────────────────────────────────────────

def test_dv360_adapter_mock():
    adapter = DV360Adapter(credentials={"mock": True}, agency_id="agency-001")
    records, cursor = adapter.fetch("2026-03-01", "2026-03-31")
    assert len(records) == 1
    assert records[0]["campaign_name"] == "Programmatic Q1 2026"
    assert records[0]["spend"] == 1250.00
    assert cursor is None


def test_dv360_adapter_raw_table():
    adapter = DV360Adapter(credentials={}, agency_id="agency-001")
    assert adapter.get_raw_table() == "raw_dv360"


def test_dv360_etl_end_to_end(warehouse):
    adapter = DV360Adapter(credentials={"mock": True}, agency_id="agency-dv")
    runner = ETLRunner(warehouse)
    result = runner.run(adapter, "2026-03-01", "2026-03-31", "integ-dv")
    assert result.success is True
    assert result.records_written == 1
    rows = warehouse.query("SELECT * FROM raw_dv360")
    assert rows[0]["campaign_name"] == "Programmatic Q1 2026"


# ── TC-05: StackAdapt Adapter ────────────────────────────────────────────────

def test_stackadapt_adapter_mock():
    adapter = StackAdaptAdapter(credentials={"mock": True}, agency_id="agency-001")
    records, cursor = adapter.fetch("2026-03-01", "2026-03-31")
    assert len(records) == 1
    assert records[0]["campaign_name"] == "Native Display Q1"
    assert records[0]["spend"] == 920.00
    assert cursor is None


def test_stackadapt_adapter_raw_table():
    adapter = StackAdaptAdapter(credentials={}, agency_id="agency-001")
    assert adapter.get_raw_table() == "raw_stackadapt"


def test_stackadapt_etl_end_to_end(warehouse):
    adapter = StackAdaptAdapter(credentials={"mock": True}, agency_id="agency-sa")
    runner = ETLRunner(warehouse)
    result = runner.run(adapter, "2026-03-01", "2026-03-31", "integ-sa")
    assert result.success is True
    assert result.records_written == 1


# ── TC-06: allow-listverify ────────────────────────────────────────────────────────

def test_warehouse_whitelist_accepts_new_tables(warehouse):
    """All new raw tables should be in the allow-list."""
    for table in ["raw_quorum", "raw_leadrx", "raw_liveramp", "raw_dv360", "raw_stackadapt"]:
        rows = [{"agency_id": "test", "date": "2026-01-01"}]
        # should not raise ValueError
        warehouse.insert_many(table, rows)


def test_warehouse_whitelist_rejects_unknown(warehouse):
    """Unknown table names should be rejected."""
    with pytest.raises(ValueError, match="not in the allowed list"):
        warehouse.insert_many("raw_unknown", [{"agency_id": "test"}])


# ── TC-07: multi-platformdo not interfere with each other ────────────────────────────────────────────────────

def test_all_new_adapters_isolated(warehouse):
    """5  new adapter eachwritetheir owntable，do not interfere with each other。"""
    adapters = [
        QuorumAdapter(credentials={"mock": True}, agency_id="agency-all"),
        LeadRXAdapter(credentials={"mock": True}, agency_id="agency-all"),
        LiveRampAdapter(credentials={"mock": True}, agency_id="agency-all"),
        DV360Adapter(credentials={"mock": True}, agency_id="agency-all"),
        StackAdaptAdapter(credentials={"mock": True}, agency_id="agency-all"),
    ]
    runner = ETLRunner(warehouse)
    for i, adapter in enumerate(adapters):
        result = runner.run(adapter, "2026-03-01", "2026-03-31", f"integ-{i}")
        assert result.success is True

    assert len(warehouse.query("SELECT * FROM raw_quorum")) == 2
    assert len(warehouse.query("SELECT * FROM raw_leadrx")) == 2
    assert len(warehouse.query("SELECT * FROM raw_liveramp")) == 2
    assert len(warehouse.query("SELECT * FROM raw_dv360")) == 1
    assert len(warehouse.query("SELECT * FROM raw_stackadapt")) == 1
