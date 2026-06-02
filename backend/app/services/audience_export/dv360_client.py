from __future__ import annotations
"""DV360 API client — Audience Segment create。"""
import re
import logging
import uuid

log = logging.getLogger(__name__)


class DV360AudienceClient:
    BASE_URL = "https://displayvideo.googleapis.com/v3"

    def __init__(self, api_key: str, advertiser_id: str):
        self.api_key = api_key
        self.advertiser_id = advertiser_id
        # H-4 compliance: validate advertiser_id input (prevents SSRF)
        if advertiser_id and not re.match(r"^[a-zA-Z0-9_-]+$", advertiser_id):
            raise ValueError(f"Invalid advertiser_id format: {advertiser_id[:20]}")

    async def create_audience_segment(self, targeting_spec: dict) -> dict:
        """create DV360 Audience Segment，return {id, name}。"""
        if not self.api_key:
            return self.mock_create(targeting_spec)

        import httpx

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self.BASE_URL}/advertisers/{self.advertiser_id}/firstAndThirdPartyAudiences",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "displayName": targeting_spec.get("displayName", "ReceptivIQ Audience"),
                    "audienceType": targeting_spec.get("audienceType", "FIRST_PARTY"),
                    "membershipDurationDays": targeting_spec.get("membershipDurationDays", 30),
                    "description": targeting_spec.get("description", ""),
                },
            )
            response.raise_for_status()
            data = response.json()
            return {
                "id": data.get("firstAndThirdPartyAudienceId", ""),
                "name": targeting_spec.get("displayName", ""),
            }

    def mock_create(self, targeting_spec: dict) -> dict:
        """Mock mode：returnsimulated segment ID。"""
        mock_id = f"mock_dv360_{uuid.uuid4().hex[:8]}"
        log.info("Mock DV360 audience created: %s", mock_id)
        return {"id": mock_id, "name": targeting_spec.get("displayName", "")}
