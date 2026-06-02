from __future__ import annotations
"""
Warehouse Client — DuckDB (dev) / Snowflake (prod) dual mode.
Selectable via the WAREHOUSE_BACKEND=duckdb|snowflake env var.
"""
import os
import logging
from typing import Optional, Any

log = logging.getLogger(__name__)


class WarehouseClient:
    """Unified warehouse interface; supports DuckDB and Snowflake."""

    def __init__(self, backend: Optional[str] = None):
        self.backend = backend or os.getenv("WAREHOUSE_BACKEND", "duckdb")
        self._conn = None
        self._db_path = os.getenv("DUCKDB_PATH", "/tmp/receptiviq_dev.duckdb")

    def connect(self):
        if self.backend == "duckdb":
            import duckdb
            self._conn = duckdb.connect(self._db_path)
            self._init_duckdb_schema()
        elif self.backend == "snowflake":
            self._connect_snowflake()
        else:
            raise ValueError(f"Unknown backend: {self.backend}")
        return self

    def _init_duckdb_schema(self):
        """Initialize the DuckDB raw schema (kept compatible with Snowflake raw_* tables)."""
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS raw_ga4_events (
                agency_id VARCHAR NOT NULL,
                client_id VARCHAR,
                date DATE NOT NULL,
                property_id VARCHAR NOT NULL,
                session_id VARCHAR,
                event_name VARCHAR,
                user_pseudo_id VARCHAR,
                sessions INTEGER,
                users INTEGER,
                new_users INTEGER,
                page_views INTEGER,
                bounce_rate FLOAT,
                avg_session_duration FLOAT,
                goal_completions INTEGER,
                ingested_at TIMESTAMP DEFAULT now()
            )
        """)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS raw_meta_ads (
                agency_id VARCHAR NOT NULL,
                client_id VARCHAR,
                date DATE NOT NULL,
                account_id VARCHAR NOT NULL,
                campaign_id VARCHAR,
                campaign_name VARCHAR,
                ad_set_id VARCHAR,
                ad_set_name VARCHAR,
                ad_id VARCHAR,
                impressions INTEGER,
                clicks INTEGER,
                spend FLOAT,
                reach INTEGER,
                conversions INTEGER,
                conversion_value FLOAT,
                ingested_at TIMESTAMP DEFAULT now()
            )
        """)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS raw_hubspot_contacts (
                agency_id VARCHAR NOT NULL,
                client_id VARCHAR,
                contact_id VARCHAR NOT NULL,
                email_hash VARCHAR,
                first_name_hash VARCHAR,
                last_name_hash VARCHAR,
                lifecycle_stage VARCHAR,
                lead_source VARCHAR,
                create_date DATE,
                ingested_at TIMESTAMP DEFAULT now()
            )
        """)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS raw_quorum (
                agency_id VARCHAR NOT NULL,
                client_id VARCHAR,
                date DATE NOT NULL,
                audience_id VARCHAR,
                audience_name VARCHAR,
                category VARCHAR,
                reach INTEGER,
                engagement_score FLOAT,
                ingested_at TIMESTAMP DEFAULT now()
            )
        """)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS raw_leadrx (
                agency_id VARCHAR NOT NULL,
                client_id VARCHAR,
                date DATE NOT NULL,
                conversion_id VARCHAR,
                touchpoint_channel VARCHAR,
                touchpoint_source VARCHAR,
                attribution_model VARCHAR,
                attribution_weight FLOAT,
                conversion_value FLOAT,
                ingested_at TIMESTAMP DEFAULT now()
            )
        """)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS raw_liveramp (
                agency_id VARCHAR NOT NULL,
                client_id VARCHAR,
                date DATE NOT NULL,
                segment_id VARCHAR,
                segment_name VARCHAR,
                match_type VARCHAR,
                matched_count INTEGER,
                total_count INTEGER,
                match_rate FLOAT,
                ingested_at TIMESTAMP DEFAULT now()
            )
        """)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS raw_dv360 (
                agency_id VARCHAR NOT NULL,
                client_id VARCHAR,
                date DATE NOT NULL,
                advertiser_id VARCHAR,
                campaign_id VARCHAR,
                campaign_name VARCHAR,
                line_item_id VARCHAR,
                impressions INTEGER,
                clicks INTEGER,
                spend FLOAT,
                conversions INTEGER,
                conversion_value FLOAT,
                ingested_at TIMESTAMP DEFAULT now()
            )
        """)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS raw_stackadapt (
                agency_id VARCHAR NOT NULL,
                client_id VARCHAR,
                date DATE NOT NULL,
                campaign_id VARCHAR,
                campaign_name VARCHAR,
                creative_id VARCHAR,
                impressions INTEGER,
                clicks INTEGER,
                spend FLOAT,
                conversions INTEGER,
                conversion_value FLOAT,
                ingested_at TIMESTAMP DEFAULT now()
            )
        """)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS etl_sync_state (
                agency_id VARCHAR NOT NULL,
                integration_id VARCHAR NOT NULL,
                platform VARCHAR NOT NULL,
                last_sync_at TIMESTAMP,
                last_cursor VARCHAR,
                records_written INTEGER DEFAULT 0,
                PRIMARY KEY (agency_id, integration_id)
            )
        """)

    def _connect_snowflake(self):
        from app.core.config import settings
        import snowflake.connector
        self._conn = snowflake.connector.connect(
            account=settings.SNOWFLAKE_ACCOUNT,
            user=settings.SNOWFLAKE_USER,
            password=settings.SNOWFLAKE_PASSWORD,
            database=settings.SNOWFLAKE_DATABASE,
            schema=settings.SNOWFLAKE_SCHEMA,
            warehouse=settings.SNOWFLAKE_WAREHOUSE,
            role=settings.SNOWFLAKE_ROLE or None,
        )

    # H-02/H-03: SQL statement allow-list — only permit specific safe operations
    _ALLOWED_SQL_PREFIXES = (
        "SELECT ", "INSERT INTO ", "UPDATE ETL_SYNC_STATE ",
        "CREATE TABLE IF NOT EXISTS ",
        "SHOW TABLES",  # DuckDB metadata query
    )

    def execute(self, sql: str, params=None):
        if self._conn is None:
            self.connect()
        # H-02: validate SQL statement prefix (defense against arbitrary SQL injection)
        sql_upper = sql.strip().upper()
        if not any(sql_upper.startswith(prefix) for prefix in self._ALLOWED_SQL_PREFIXES):
            raise ValueError(f"SQL statement not allowed: {sql[:60]}...")
        if self.backend == "duckdb":
            return self._conn.execute(sql, params or [])
        else:
            cursor = self._conn.cursor()
            cursor.execute(sql, params or [])
            return cursor

    # C-1 compliance fix: table/column allow-lists to block SQL injection
    _ALLOWED_TABLES = {
        "raw_meta_ads", "raw_ga4_events", "raw_hubspot_contacts",
        "raw_quorum", "raw_leadrx", "raw_liveramp",
        "raw_dv360", "raw_stackadapt",
        "mart_campaign_unified",
        "etl_sync_state",
    }
    _COL_PATTERN = __import__("re").compile(r"^[a-z_][a-z0-9_]*$")

    def insert_many(self, table: str, rows: list[dict]) -> int:
        """Bulk-insert records. `rows` is a list of dicts whose keys are column names."""
        if not rows:
            return 0
        if self._conn is None:
            self.connect()
        # Table-name allow-list check
        if table not in self._ALLOWED_TABLES:
            raise ValueError(f"Table '{table}' is not in the allowed list: {self._ALLOWED_TABLES}")
        # Column-name regex check
        cols = list(rows[0].keys())
        for col in cols:
            if not self._COL_PATTERN.match(col):
                raise ValueError(f"Invalid column name: '{col}'")
        placeholders = ", ".join("?" * len(cols))
        col_str = ", ".join(cols)
        values = [[r.get(c) for c in cols] for r in rows]
        sql = f"INSERT INTO {table} ({col_str}) VALUES ({placeholders})"
        if self.backend == "duckdb":
            self._conn.executemany(sql, values)
        else:
            cursor = self._conn.cursor()
            cursor.executemany(sql, values)
        return len(rows)

    def query(self, sql: str, params=None) -> list[dict]:
        """Run a query and return a list of dicts."""
        result = self.execute(sql, params)
        if self.backend == "duckdb":
            cols = [desc[0] for desc in result.description]
            return [dict(zip(cols, row)) for row in result.fetchall()]
        else:
            cols = [d[0] for d in result.description]
            return [dict(zip(cols, row)) for row in result.fetchall()]

    def get_sync_state(self, agency_id: str, integration_id: str) -> Optional[dict]:
        rows = self.query(
            "SELECT * FROM etl_sync_state WHERE agency_id=? AND integration_id=?",
            [agency_id, integration_id],
        )
        return rows[0] if rows else None

    def update_sync_state(
        self,
        agency_id: str,
        integration_id: str,
        platform: str,
        last_cursor: Optional[str],
        records_written: int,
    ):
        existing = self.get_sync_state(agency_id, integration_id)
        if existing:
            self.execute(
                "UPDATE etl_sync_state SET last_sync_at=now(), last_cursor=?, records_written=? WHERE agency_id=? AND integration_id=?",
                [last_cursor, records_written, agency_id, integration_id],
            )
        else:
            self.execute(
                "INSERT INTO etl_sync_state VALUES (?, ?, ?, now(), ?, ?)",
                [agency_id, integration_id, platform, last_cursor, records_written],
            )

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None


# Global singleton (replaceable in tests)
_warehouse: Optional[WarehouseClient] = None


def get_warehouse() -> WarehouseClient:
    global _warehouse
    if _warehouse is None:
        _warehouse = WarehouseClient()
        _warehouse.connect()
    return _warehouse


def reset_warehouse(client: Optional[WarehouseClient] = None):
    """Test helper: reset the global client."""
    global _warehouse
    if _warehouse:
        _warehouse.close()
    _warehouse = client
