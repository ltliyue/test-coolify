"""Minimal async wrapper around the Neon Console API.

Used by ``tenant_provisioner.provision_tenant_database`` when
``TENANT_PROVISION_MODE == "neon_api"``. Keep this file dependency-free
beyond ``httpx`` so it can be unit-tested in isolation.
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_BASE_URL = "https://console.neon.tech/api/v2"


class NeonAPIError(RuntimeError):
    """Raised when a Neon Console API call fails."""


def _require_api_key() -> str:
    api_key = getattr(settings, "NEON_API_KEY", "") or ""
    if not api_key:
        raise NeonAPIError(
            "NEON_API_KEY is not configured; cannot provision via Neon"
        )
    return api_key


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_require_api_key()}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


async def create_project(name: str) -> dict[str, Any]:
    """Create a new Neon project and return the API response payload."""
    payload = {"project": {"name": name}}
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{_BASE_URL}/projects", headers=_headers(), json=payload
        )
        if resp.status_code >= 400:
            raise NeonAPIError(
                f"Neon create_project failed: {resp.status_code} {resp.text}"
            )
        return resp.json()


async def get_connection_uri(
    project_id: str,
    role_name: str = "receptiviq",
    database_name: str = "neondb",
    endpoint_type: str = "read_write",
) -> str:
    """Fetch a connection URI for the given project/role/database."""
    params = {
        "role_name": role_name,
        "database_name": database_name,
        "endpoint_type": endpoint_type,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{_BASE_URL}/projects/{project_id}/connection_uri",
            headers=_headers(),
            params=params,
        )
        if resp.status_code >= 400:
            raise NeonAPIError(
                f"Neon get_connection_uri failed: {resp.status_code} {resp.text}"
            )
        body = resp.json()
        uri = body.get("uri") or body.get("connection_uri")
        if not uri:
            raise NeonAPIError(f"Neon get_connection_uri missing uri field: {body}")
        return uri


async def delete_project(project_id: str) -> None:
    """Best-effort rollback on provisioning failure."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.delete(
            f"{_BASE_URL}/projects/{project_id}", headers=_headers()
        )
        if resp.status_code >= 400:
            logger.warning(
                "Neon delete_project(%s) failed: %s %s",
                project_id,
                resp.status_code,
                resp.text,
            )


__all__ = ["create_project", "get_connection_uri", "delete_project", "NeonAPIError"]
