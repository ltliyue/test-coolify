from __future__ import annotations
"""HubSpot contacts ETL adapter.
Production uses HubSpot Contacts API v3 (access_token based).
Returns mock data for tests/dev (when credentials contain mock=True).
"""
import logging
from typing import Optional

from app.services.etl.base import BaseAdapter

log = logging.getLogger(__name__)

HUBSPOT_API_BASE = "https://api.hubapi.com"


class HubSpotAdapter(BaseAdapter):
    platform = "hubspot"

    def get_raw_table(self) -> str:
        return "raw_hubspot_contacts"

    def fetch(
        self, start_date: str, end_date: str, cursor: Optional[str] = None
    ) -> tuple[list[dict], Optional[str]]:
        if self.credentials.get("mock"):
            return self._mock_data(start_date, end_date), None

        access_token = self.credentials.get("access_token", "")

        try:
            import httpx

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }
            params = {
                "limit": 100,
                "properties": "email,firstname,lastname,lifecyclestage,hs_lead_status,creation date",
            }
            if cursor:
                params["after"] = cursor

            response = httpx.get(
                f"{HUBSPOT_API_BASE}/crm/v3/objects/contacts",
                params=params,
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            records = self._parse_hubspot_response(data)
            next_cursor = data.get("paging", {}).get("next", {}).get("after")
            return records, next_cursor
        except Exception as e:
            # M-08: do not expose full API error in logs（cancancontain token/PII）
            log.error("HubSpot API error: %s", type(e).__name__)
            raise

    def _parse_hubspot_response(self, data: dict) -> list[dict]:
        records = []
        for contact in data.get("results", []):
            props = contact.get("properties", {})
            create_date = props.get("creation date", "")
            # creation date is ISO 8601; take only the date portion
            create_date_only = create_date[:10] if create_date else None

            records.append({
                "contact_id": contact.get("id", ""),
                "email_hash": props.get("email", ""),
                "first_name_hash": props.get("firstname", ""),
                "last_name_hash": props.get("lastname", ""),
                "lifecycle_stage": props.get("lifecyclestage", ""),
                "lead_source": props.get("hs_lead_status", ""),
                "create_date": create_date_only,
            })
        return records

    def _mock_data(self, start_date: str, end_date: str) -> list[dict]:
        """Return mock data for tests."""
        return [
            {
                "contact_id": "contact_001",
                "email_hash": "jane.doe@example.com",
                "first_name_hash": "Jane",
                "last_name_hash": "Doe",
                "lifecycle_stage": "lead",
                "lead_source": "NEW",
                "create_date": start_date,
            },
            {
                "contact_id": "contact_002",
                "email_hash": "john.smith@example.com",
                "first_name_hash": "John",
                "last_name_hash": "Smith",
                "lifecycle_stage": "customer",
                "lead_source": "CONNECTED",
                "create_date": start_date,
            },
        ]
