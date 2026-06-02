from __future__ import annotations
"""CampaignQueryService — from data warehousequerycross-platform campaign aggregate data。"""
import logging
from typing import Optional

from app.core.warehouse_client import WarehouseClient

log = logging.getLogger(__name__)

VALID_PLATFORMS = {"meta_ads", "dv360", "stackadapt"}


class CampaignQueryService:
    def __init__(self, warehouse: WarehouseClient):
        self.wh = warehouse

    def list_campaigns(
        self,
        agency_id: str,
        platform: Optional[str] = None,
        client_id: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:
        sql = "SELECT * FROM mart_campaign_unified WHERE agency_id=?"
        params: list = [agency_id]

        if platform:
            sql += " AND platform=?"
            params.append(platform)
        if client_id:
            sql += " AND client_id=?"
            params.append(client_id)
        if date_from:
            sql += " AND date>=?"
            params.append(date_from)
        if date_to:
            sql += " AND date<=?"
            params.append(date_to)

        sql += " ORDER BY date DESC, spend DESC"
        # Note: DuckDB supports LIMIT/OFFSET via string; Snowflake also supports it
        sql += f" LIMIT {int(limit)} OFFSET {int(offset)}"
        return self.wh.query(sql, params)

    def get_summary(
        self,
        agency_id: str,
        client_id: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> dict:
        sql = "SELECT platform, SUM(spend) AS total_spend, SUM(conversions) AS total_conversions, SUM(impressions) AS total_impressions, SUM(clicks) AS total_clicks, MIN(date) AS min_date, MAX(date) AS max_date FROM mart_campaign_unified WHERE agency_id=?"
        params: list = [agency_id]
        if client_id:
            sql += " AND client_id=?"
            params.append(client_id)
        if date_from:
            sql += " AND date>=?"
            params.append(date_from)
        if date_to:
            sql += " AND date<=?"
            params.append(date_to)
        sql += " GROUP BY platform"

        rows = self.wh.query(sql, params)

        total_spend = sum(r.get("total_spend", 0) or 0 for r in rows)
        total_conversions = sum(r.get("total_conversions", 0) or 0 for r in rows)
        total_impressions = sum(r.get("total_impressions", 0) or 0 for r in rows)
        total_clicks = sum(r.get("total_clicks", 0) or 0 for r in rows)
        platform_breakdown = {r["platform"]: float(r.get("total_spend", 0) or 0) for r in rows}

        min_date = min((str(r.get("min_date", "")) for r in rows if r.get("min_date")), default="")
        max_date = max((str(r.get("max_date", "")) for r in rows if r.get("max_date")), default="")

        return {
            "total_spend": float(total_spend),
            "total_conversions": int(total_conversions),
            "total_impressions": int(total_impressions),
            "total_clicks": int(total_clicks),
            "platform_breakdown": platform_breakdown,
            "date_range": {"from": min_date, "to": max_date},
        }

    def get_campaign_metrics(
        self,
        agency_id: str,
        platform: str,
        external_campaign_id: str,
        limit: int = 90,
        offset: int = 0,
    ) -> list[dict]:
        sql = "SELECT * FROM mart_campaign_unified WHERE agency_id=? AND platform=? AND campaign_id=? ORDER BY date DESC"
        sql += f" LIMIT {int(limit)} OFFSET {int(offset)}"
        return self.wh.query(sql, [agency_id, platform, external_campaign_id])

    def get_campaign_spend_today(
        self, agency_id: str, platform: str, external_campaign_id: str
    ) -> float:
        sql = "SELECT SUM(spend) AS today_spend FROM mart_campaign_unified WHERE agency_id=? AND platform=? AND campaign_id=? AND date=CURRENT_DATE"
        rows = self.wh.query(sql, [agency_id, platform, external_campaign_id])
        if rows and rows[0].get("today_spend"):
            return float(rows[0]["today_spend"])
        return 0.0
