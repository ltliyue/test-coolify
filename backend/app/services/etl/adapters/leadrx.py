from __future__ import annotations
"""LeadRX ETL adapter — attribution data."""
import logging
from typing import Optional

from app.services.etl.base import BaseAdapter
from app.core.compliance.anonymizer import hash_identifier

log = logging.getLogger(__name__)


class LeadRXAdapter(BaseAdapter):
    platform = "leadrx"
    BASE_URL = "https://api.leadrx.com/v1"

    def get_raw_table(self) -> str:
        return "raw_leadrx"

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
                "limit": 1000,
            }
            if cursor:
                params["cursor"] = cursor

            response = httpx.get(
                f"{self.BASE_URL}/conversions",
                params=params,
                headers={"X-Api-Key": api_key},
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            records = [
                {
                    "date": item.get("conversion_date", start_date),
                    "conversion_id": item.get("id", ""),
                    "touchpoint_channel": item.get("channel", ""),
                    "touchpoint_source": item.get("source", ""),
                    "attribution_model": item.get("model", "last_touch"),
                    "attribution_weight": float(item.get("weight", 1.0)),
                    "conversion_value": float(item.get("value", 0)),
                }
                for item in data.get("conversions", [])
            ]
            next_cursor = data.get("next_cursor")
            return records, next_cursor
        except Exception as e:
            log.error("LeadRX API error: %s", e)
            raise

    def transform(self, record: dict) -> dict:
        """hashconversion ID（C-4 compliancefix）。"""
        if record.get("conversion_id"):
            record["conversion_id"] = hash_identifier(record["conversion_id"], self.agency_id)
        return record

    def _mock_data(self, start_date: str, end_date: str) -> list[dict]:
        return [
            {
                "date": start_date,
                "conversion_id": "conv_001",
                "touchpoint_channel": "paid_search",
                "touchpoint_source": "google",
                "attribution_model": "linear",
                "attribution_weight": 0.4,
                "conversion_value": 125.00,
            },
            {
                "date": start_date,
                "conversion_id": "conv_002",
                "touchpoint_channel": "paid_social",
                "touchpoint_source": "meta",
                "attribution_model": "linear",
                "attribution_weight": 0.6,
                "conversion_value": 125.00,
            },
        ]
