from __future__ import annotations
"""StackAdapt ETL adapter — native/programmatic ad data。"""
import logging
from typing import Optional

from app.services.etl.base import BaseAdapter

log = logging.getLogger(__name__)


class StackAdaptAdapter(BaseAdapter):
    platform = "stackadapt"
    BASE_URL = "https://api.stackadapt.com/v3"

    def get_raw_table(self) -> str:
        return "raw_stackadapt"

    def fetch(
        self, start_date: str, end_date: str, cursor: Optional[str] = None
    ) -> tuple[list[dict], Optional[str]]:
        if self.credentials.get("mock"):
            return self._mock_data(start_date, end_date), None

        api_key = self.credentials.get("api_key", "")
        try:
            import httpx

            params = {
                "start_date": start_date,
                "end_date": end_date,
                "page_size": 500,
            }
            if cursor:
                params["page"] = cursor

            response = httpx.get(
                f"{self.BASE_URL}/campaigns/stats",
                params=params,
                headers={"X-Authorization": api_key},
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            records = [
                {
                    "date": item.get("date", start_date),
                    "campaign_id": str(item.get("campaign_id", "")),
                    "campaign_name": item.get("campaign_name", ""),
                    "creative_id": str(item.get("creative_id", "")),
                    "impressions": int(item.get("impressions", 0)),
                    "clicks": int(item.get("clicks", 0)),
                    "spend": float(item.get("spend", 0)),
                    "conversions": int(item.get("conversions", 0)),
                    "conversion_value": float(item.get("conversion_value", 0)),
                }
                for item in data.get("data", [])
            ]
            next_page = data.get("next_page")
            next_cursor = str(next_page) if next_page else None
            return records, next_cursor
        except Exception as e:
            log.error("StackAdapt API error: %s", e)
            raise

    def _mock_data(self, start_date: str, end_date: str) -> list[dict]:
        return [
            {
                "date": start_date,
                "campaign_id": "sa_camp_001",
                "campaign_name": "Native Display Q1",
                "creative_id": "sa_cr_001",
                "impressions": 150000,
                "clicks": 2800,
                "spend": 920.00,
                "conversions": 95,
                "conversion_value": 4750.00,
            },
        ]
