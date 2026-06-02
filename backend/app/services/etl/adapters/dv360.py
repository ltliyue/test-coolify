from __future__ import annotations
"""DV360 ETL adapter — programmatic campaign data。"""
import logging
from typing import Optional

from app.services.etl.base import BaseAdapter

log = logging.getLogger(__name__)


class DV360Adapter(BaseAdapter):
    platform = "dv360"
    BASE_URL = "https://displayvideo.googleapis.com/v3"

    def get_raw_table(self) -> str:
        return "raw_dv360"

    def fetch(
        self, start_date: str, end_date: str, cursor: Optional[str] = None
    ) -> tuple[list[dict], Optional[str]]:
        if self.credentials.get("mock"):
            return self._mock_data(start_date, end_date), None

        import re
        api_key = self.credentials.get("api_key", "")
        advertiser_id = self.credentials.get("advertiser_id", "")
        if not re.match(r"^[a-zA-Z0-9_-]+$", advertiser_id):
            raise ValueError(f"Invalid advertiser_id format: {advertiser_id[:20]}")
        try:
            import httpx

            params = {
                "filter.dateRange.startDate.year": start_date[:4],
                "filter.dateRange.startDate.month": start_date[5:7],
                "filter.dateRange.startDate.day": start_date[8:10],
                "filter.dateRange.endDate.year": end_date[:4],
                "filter.dateRange.endDate.month": end_date[5:7],
                "filter.dateRange.endDate.day": end_date[8:10],
                "pageSize": 500,
            }
            if cursor:
                params["pageToken"] = cursor

            response = httpx.get(
                f"{self.BASE_URL}/advertisers/{advertiser_id}/campaigns",
                params=params,
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            records = [
                {
                    "date": start_date,
                    "advertiser_id": advertiser_id,
                    "campaign_id": item.get("campaignId", ""),
                    "campaign_name": item.get("displayName", ""),
                    "line_item_id": "",
                    "impressions": int(item.get("impressions", 0)),
                    "clicks": int(item.get("clicks", 0)),
                    "spend": float(item.get("totalMediaCostAdvertiser", 0)),
                    "conversions": int(item.get("totalConversions", 0)),
                    "conversion_value": float(item.get("totalConversionValue", 0)),
                }
                for item in data.get("campaigns", [])
            ]
            next_cursor = data.get("nextPageToken")
            return records, next_cursor
        except Exception as e:
            log.error("DV360 API error: %s", e)
            raise

    def _mock_data(self, start_date: str, end_date: str) -> list[dict]:
        return [
            {
                "date": start_date,
                "advertiser_id": "adv_001",
                "campaign_id": "dv_camp_001",
                "campaign_name": "Programmatic Q1 2026",
                "line_item_id": "li_001",
                "impressions": 200000,
                "clicks": 3500,
                "spend": 1250.00,
                "conversions": 120,
                "conversion_value": 6000.00,
            },
        ]
