from __future__ import annotations
"""Meta Marketing API client — Custom Audience create。"""
import logging
import uuid

log = logging.getLogger(__name__)


class MetaAudienceClient:
    BASE_URL = "https://graph.facebook.com/v19.0"

    def __init__(self, access_token: str, account_id: str):
        self.access_token = access_token
        self.account_id = account_id

    async def create_custom_audience(self, targeting_spec: dict) -> dict:
        """create Meta Custom Audience，return {id, name}。"""
        if not self.access_token:
            return self.mock_create(targeting_spec)

        import httpx

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self.BASE_URL}/act_{self.account_id}/customaudiences",
                headers={"Authorization": f"Bearer {self.access_token}"},
                json={
                    "name": targeting_spec.get("name", "ReceptivIQ Audience"),
                    "description": targeting_spec.get("description", ""),
                    "subtype": targeting_spec.get("subtype", "CUSTOM"),
                },
            )
            response.raise_for_status()
            data = response.json()
            return {"id": data.get("id", ""), "name": targeting_spec.get("name", "")}

    def mock_create(self, targeting_spec: dict) -> dict:
        """Mock mode：returnsimulated audience ID。"""
        mock_id = f"mock_meta_{uuid.uuid4().hex[:8]}"
        log.info("Mock Meta audience created: %s", mock_id)
        return {"id": mock_id, "name": targeting_spec.get("name", "")}
