from __future__ import annotations
"""LiveRamp ETL adapter — identity resolution / cross-device matching。"""
import logging
from typing import Optional

from app.services.etl.base import BaseAdapter
from app.core.compliance.anonymizer import hash_identifier

log = logging.getLogger(__name__)


class LiveRampAdapter(BaseAdapter):
    platform = "liveramp"
    BASE_URL = "https://api.liveramp.com/v1"

    def get_raw_table(self) -> str:
        return "raw_liveramp"

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
                "limit": 500,
            }
            if cursor:
                params["cursor"] = cursor

            response = httpx.get(
                f"{self.BASE_URL}/segments/match-rates",
                params=params,
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            records = [
                {
                    "date": item.get("date", start_date),
                    "segment_id": item.get("segment_id", ""),
                    "segment_name": item.get("segment_name", ""),
                    "match_type": item.get("match_type", "cookie"),
                    "matched_count": int(item.get("matched", 0)),
                    "total_count": int(item.get("total", 0)),
                    "match_rate": float(item.get("match_rate", 0)),
                }
                for item in data.get("segments", [])
            ]
            next_cursor = data.get("next_cursor")
            return records, next_cursor
        except Exception as e:
            log.error("LiveRamp API error: %s", e)
            raise

    def transform(self, record: dict) -> dict:
        """hashidentityidentifier field（C-3 compliancefix）。"""
        if record.get("segment_id"):
            record["segment_id"] = hash_identifier(record["segment_id"], self.agency_id)
        return record

    def _mock_data(self, start_date: str, end_date: str) -> list[dict]:
        return [
            {
                "date": start_date,
                "segment_id": "seg_001",
                "segment_name": "High Value Shoppers",
                "match_type": "email",
                "matched_count": 45000,
                "total_count": 60000,
                "match_rate": 0.75,
            },
            {
                "date": start_date,
                "segment_id": "seg_002",
                "segment_name": "Cross-Device Mobile",
                "match_type": "device",
                "matched_count": 32000,
                "total_count": 50000,
                "match_rate": 0.64,
            },
        ]
