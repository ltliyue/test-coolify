from __future__ import annotations
"""Historical data CSV import service.
Supported formats: meta_ads / ga4 / hubspot
Parses CSV, normalizes field names, and writes to the DuckDB raw table via WarehouseClient.
"""
import csv
import io
import logging
from typing import Optional

log = logging.getLogger(__name__)

# Mapping of each platform's CSV column names to raw-table field names
_COLUMN_MAPS = {
    "meta_ads": {
        "campaign_id": "campaign_id",
        "campaign_name": "campaign_name",
        "ad_set_id": "ad_set_id", "adset_id": "ad_set_id",
        "ad_set_name": "ad_set_name", "adset_name": "ad_set_name",
        "ad_id": "ad_id",
        "impressions": "impressions",
        "clicks": "clicks", "link_clicks": "clicks",
        "spend": "spend",
        "reach": "reach",
        "conversions": "conversions", "actions_offsite_conversion": "conversions",
        "conversion_value": "conversion_value", "action_values": "conversion_value",
        "date": "date", "date_start": "date",
    },
    "ga4": {
        "date": "date",
        "property_id": "property_id",
        "sessions": "sessions",
        "totalUsers": "users", "users": "users", "activeUsers": "users",
        "newUsers": "new_users", "new_users": "new_users",
        "screenPageViews": "page_views", "page_views": "page_views",
        "bounceRate": "bounce_rate", "bounce_rate": "bounce_rate",
        "averageSessionDuration": "avg_session_duration", "avg_session_duration": "avg_session_duration",
        "conversions": "goal_completions", "goal_completions": "goal_completions",
    },
    "hubspot": {
        "contact_id": "contact_id", "id": "contact_id",
        "email": "email",
        "firstname": "first_name", "first_name": "first_name",
        "lastname": "last_name", "last_name": "last_name",
        "lifecyclestage": "lifecycle_stage", "lifecycle_stage": "lifecycle_stage",
        "hs_lead_status": "lead_source", "lead_source": "lead_source",
        "creation date": "create_date", "create_date": "create_date",
    },
}

_RAW_TABLE = {
    "meta_ads": "raw_meta_ads",
    "ga4": "raw_ga4_events",
    "hubspot": "raw_hubspot_contacts",
}

_INT_FIELDS = {"impressions", "clicks", "reach", "conversions", "sessions", "users", "new_users", "page_views", "goal_completions"}
_FLOAT_FIELDS = {"spend", "bounce_rate", "avg_session_duration", "conversion_value"}


def _coerce(value: str, field_name: str) -> object:
    """Coerce a CSV string value into the appropriate Python type."""
    if not value or value.strip() == "":
        return None
    v = value.strip()
    if field_name in _INT_FIELDS:
        try:
            return int(float(v))
        except ValueError:
            return None
    if field_name in _FLOAT_FIELDS:
        try:
            return float(v)
        except ValueError:
            return None
    return v


def detect_format(headers: list) -> Optional[str]:
    """based on CSV column nameauto-detectplatformformat。"""
    h = {c.lower().strip() for c in headers}
    if any(x in h for x in ("campaign_id", "adset_id", "ad_set_id", "link_clicks")):
        return "meta_ads"
    if any(x in h for x in ("totalusers", "screenpageviews", "avg_session_duration", "sessions")):
        return "ga4"
    if any(x in h for x in ("contact_id", "lifecyclestage", "hs_lead_status", "firstname")):
        return "hubspot"
    return None


def parse_csv(
    content: bytes,
    platform: str,
    agency_id: str,
    client_id: Optional[str] = None,
) -> list:
    """
    parse CSV file，returnnormalize  dict list（can be directlywrite to DuckDB raw table）。
    Raises ValueError if the format is not supported.
    """
    col_map = _COLUMN_MAPS.get(platform)
    if col_map is None:
        raise ValueError(f"Unsupported platform: {platform}. Supported: {list(_COLUMN_MAPS)}")

    text = content.decode("utf-8-sig")  # process BOM
    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for raw_row in reader:
        record = {"agency_id": agency_id, "client_id": client_id}
        for src_col, raw_val in raw_row.items():
            target = col_map.get(src_col) or col_map.get(src_col.strip().lower())
            if target:
                record[target] = _coerce(raw_val, target)
        # Fill required fields (if absent from CSV)
        if platform == "meta_ads" and "account_id" not in record:
            record["account_id"] = "imported"
        if platform == "ga4":
            record.setdefault("property_id", "imported")
        rows.append(record)
    return rows


def run_historical_import(
    content: bytes,
    platform: str,
    agency_id: str,
    client_id: Optional[str] = None,
) -> dict:
    """
    completeimportflow：parse CSV -> PHI detection/anonymize -> WarehouseClient.insert_many -> return summary。
    return {"platform": ..., "rows_imported": ..., "rows_skipped": ...}
    """
    from app.core.warehouse_client import get_warehouse
    from app.core.compliance.anonymizer import anonymize_record_for_warehouse

    rows = parse_csv(content, platform, agency_id, client_id)
    if not rows:
        return {"platform": platform, "rows_imported": 0, "rows_skipped": 0}

    # H-5 compliance fix: CSV imports must also go through PHI anonymization
    clean_rows = [anonymize_record_for_warehouse(row, agency_id) for row in rows]

    raw_table = _RAW_TABLE[platform]
    wh = get_warehouse()
    written = wh.insert_many(raw_table, clean_rows)

    log.info("Historical import: platform=%s written=%d", platform, written)
    return {
        "platform": platform,
        "rows_imported": written,
        "rows_skipped": len(rows) - written,
    }
