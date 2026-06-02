from __future__ import annotations
"""GA4（Google Analytics 4）ETL adapter.
production environment uses Google Analytics Data API v1。
Return mock data for tests/dev (when credentials contain mock=True).
"""
import logging
from typing import Optional

from app.services.etl.base import BaseAdapter

log = logging.getLogger(__name__)

# Mapping of GA4 report dimensions and metrics to raw_ga4_events table fields
GA4_METRICS_MAP = {
    "sessions": "sessions",
    "totalUsers": "users",
    "newUsers": "new_users",
    "screenPageViews": "page_views",
    "bounceRate": "bounce_rate",
    "averageSessionDuration": "avg_session_duration",
    "goalCompletions": "goal_completions",
}


class GA4Adapter(BaseAdapter):
    platform = "ga4"

    def get_raw_table(self) -> str:
        return "raw_ga4_events"

    def fetch(
        self, start_date: str, end_date: str, cursor: Optional[str] = None
    ) -> tuple[list[dict], Optional[str]]:
        if self.credentials.get("mock"):
            return self._mock_data(start_date, end_date), None

        # production environment：call Google Analytics Data API
        property_id = self.credentials.get("property_id", "")
        access_token = self.credentials.get("access_token", "")

        try:
            import httpx

            headers = {"Authorization": f"Bearer {access_token}"}
            payload = {
                "dateRanges": [{"startDate": start_date, "endDate": end_date}],
                "dimensions": [{"name": "date"}, {"name": "sessionSource"}],
                "metrics": [{"name": m} for m in GA4_METRICS_MAP],
            }
            response = httpx.post(
                f"https://analyticsdata.googleapis.com/v1beta/properties/{property_id}:runReport",
                json=payload,
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            records = self._parse_ga4_response(data, property_id, start_date)
            return records, None
        except Exception as e:
            log.error("GA4 API error: %s", e)
            raise

    def _parse_ga4_response(self, data: dict, property_id: str, start_date: str) -> list[dict]:
        records = []
        dim_headers = [d["name"] for d in data.get("dimensionHeaders", [])]
        met_headers = [m["name"] for m in data.get("metricHeaders", [])]

        for row in data.get("rows", []):
            dims = {
                dim_headers[i]: row["dimensionValues"][i]["value"]
                for i in range(len(dim_headers))
            }
            mets = {
                met_headers[i]: row["metricValues"][i]["value"]
                for i in range(len(met_headers))
            }

            record = {
                "date": dims.get("date", start_date),
                "property_id": property_id,
                "sessions": int(mets.get("sessions", 0)),
                "users": int(mets.get("totalUsers", 0)),
                "new_users": int(mets.get("newUsers", 0)),
                "page_views": int(mets.get("screenPageViews", 0)),
                "bounce_rate": float(mets.get("bounceRate", 0)),
                "avg_session_duration": float(mets.get("averageSessionDuration", 0)),
                "goal_completions": int(mets.get("goalCompletions", 0)),
            }
            records.append(record)
        return records

    def _mock_data(self, start_date: str, end_date: str) -> list[dict]:
        """Return mock data for tests."""
        return [
            {
                "date": start_date,
                "property_id": "123456789",
                "sessions": 1000,
                "users": 800,
                "new_users": 300,
                "page_views": 4500,
                "bounce_rate": 0.42,
                "avg_session_duration": 185.3,
                "goal_completions": 45,
            }
        ]
