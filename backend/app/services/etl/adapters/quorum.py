from __future__ import annotations
"""Quorum ETL adapter — row-level audiencedata。"""
import logging
from typing import Optional

from app.services.etl.base import BaseAdapter

log = logging.getLogger(__name__)


class QuorumAdapter(BaseAdapter):
    platform = "quorum"
    BASE_URL = "https://api.quorum.us/v1"

    def get_raw_table(self) -> str:
        return "raw_quorum"

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
                params["offset"] = cursor

            response = httpx.get(
                f"{self.BASE_URL}/audiences",
                params=params,
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            records = [
                {
                    "date": item.get("date", start_date),
                    "audience_id": item.get("id", ""),
                    "audience_name": item.get("name", ""),
                    "category": item.get("category", ""),
                    "reach": int(item.get("reach", 0)),
                    "engagement_score": float(item.get("engagement_score", 0)),
                    }
                for item in data.get("results", [])
            ]
            next_cursor = str(data["next_offset"]) if data.get("next_offset") else None
            return records, next_cursor
        except Exception as e:
            log.error("Quorum API error: %s", e)
            raise

    def _mock_data(self, start_date: str, end_date: str) -> list[dict]:
        return [
            {
                "date": start_date,
                "audience_id": "aud_001",
                "audience_name": "Political Engaged 25-44",
                "category": "advocacy",
                "reach": 120000,
                "engagement_score": 0.78,
            },
            {
                "date": start_date,
                "audience_id": "aud_002",
                "audience_name": "Healthcare Awareness",
                "category": "health",
                "reach": 85000,
                "engagement_score": 0.65,
            },
        ]
