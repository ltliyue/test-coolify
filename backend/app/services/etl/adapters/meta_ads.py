from __future__ import annotations
"""Meta Ads（Facebook/Instagram）ETL adapter."""
import logging
from typing import Optional

from app.services.etl.base import BaseAdapter

log = logging.getLogger(__name__)


class MetaAdsAdapter(BaseAdapter):
    platform = "meta_ads"
    BASE_URL = "https://graph.facebook.com/v19.0"

    def get_raw_table(self) -> str:
        return "raw_meta_ads"

    def fetch(
        self, start_date: str, end_date: str, cursor: Optional[str] = None
    ) -> tuple[list[dict], Optional[str]]:
        if self.credentials.get("mock"):
            return self._mock_data(start_date, end_date), None

        access_token = self.credentials.get("access_token", "")
        account_id = self.credentials.get("account_id", "")

        try:
            import httpx

            params = {
                "access_token": access_token,
                "time_range": f'{{"since":"{start_date}","until":"{end_date}"}}',
                "fields": "campaign_id,campaign_name,adset_id,adset_name,ad_id,ad_name,impressions,clicks,spend,reach,actions,action_values",
                "level": "ad",
                "limit": 500,
            }
            if cursor:
                params["after"] = cursor

            response = httpx.get(
                f"{self.BASE_URL}/act_{account_id}/insights",
                params=params,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            records = self._parse_meta_response(data, account_id)
            next_cursor = data.get("paging", {}).get("cursors", {}).get("after")
            return records, next_cursor
        except Exception as e:
            log.error("Meta Ads API error: %s", e)
            raise

    def _parse_meta_response(self, data: dict, account_id: str) -> list[dict]:
        records = []
        for row in data.get("data", []):
            conversions = sum(
                int(a.get("value", 0))
                for a in row.get("actions", [])
                if a.get("action_type") in ("purchase", "lead", "complete_registration")
            )
            conversion_value = sum(
                float(a.get("value", 0))
                for a in row.get("action_values", [])
                if a.get("action_type") == "purchase"
            )
            records.append({
                "date": row.get("date_start"),
                "account_id": account_id,
                "campaign_id": row.get("campaign_id", ""),
                "campaign_name": row.get("campaign_name", ""),
                "ad_set_id": row.get("adset_id", ""),
                "ad_set_name": row.get("adset_name", ""),
                "ad_id": row.get("ad_id", ""),
                "impressions": int(row.get("impressions", 0)),
                "clicks": int(row.get("clicks", 0)),
                "spend": float(row.get("spend", 0)),
                "reach": int(row.get("reach", 0)),
                "conversions": conversions,
                "conversion_value": conversion_value,
            })
        return records

    def _mock_data(self, start_date: str, end_date: str) -> list[dict]:
        return [
            {
                "date": start_date,
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
            }
        ]
