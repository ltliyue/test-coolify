from __future__ import annotations
from datetime import datetime, timezone

import httpx
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encryption import decrypt_credentials, encrypt_credentials
from app.models.credential import Credential
from app.models.enums import CredentialStatus


async def refresh_oauth_token(credential: Credential, db: AsyncSession) -> Credential:
    try:
        cred_data = decrypt_credentials(credential.encrypted_data)
        platform = credential.platform

        if platform in ("ga4",):
            updated_data, expires_at = await _refresh_google(cred_data)
        elif platform == "meta_ads":
            updated_data, expires_at = await _refresh_meta(cred_data)
        elif platform == "hubspot":
            updated_data, expires_at = await _refresh_hubspot(cred_data)
        elif platform == "tiktok_ads":
            updated_data, expires_at = await _refresh_tiktok(cred_data)
        else:
            raise NotImplementedError(f"OAuth token refresh not implemented for platform: {platform}")

        new_encrypted = encrypt_credentials(updated_data)
        now = datetime.now(timezone.utc)

        await db.execute(
            update(Credential)
            .where(Credential.id == credential.id)
            .values(
                encrypted_data=new_encrypted,
                expires_at=expires_at,
                last_refreshed_at=now,
                status=CredentialStatus.VALID,
                error_message=None,
                updated_at=now,
            )
        )
        await db.commit()
        await db.refresh(credential)
        return credential

    except NotImplementedError:
        raise
    except Exception as exc:
        now = datetime.now(timezone.utc)
        await db.execute(
            update(Credential)
            .where(Credential.id == credential.id)
            .values(
                status=CredentialStatus.ERROR,
                error_message=f"Token refresh failed: {type(exc).__name__}",  # H-04: do not leak token/secret
                updated_at=now,
            )
        )
        await db.commit()
        await db.refresh(credential)
        return credential


async def _refresh_google(cred_data: dict) -> tuple[dict, datetime | None]:
    refresh_token = cred_data.get("refresh_token")
    if not refresh_token:
        raise ValueError("No refresh_token found in credential data")

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": cred_data.get("client_id", ""),
                "client_secret": cred_data.get("client_secret", ""),
            },
        )
        resp.raise_for_status()
        token_data = resp.json()

    updated = {**cred_data, "access_token": token_data["access_token"]}
    expires_in = token_data.get("expires_in")
    expires_at = None
    if expires_in:
        from datetime import timedelta
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

    return updated, expires_at


async def _refresh_meta(cred_data: dict) -> tuple[dict, datetime | None]:
    access_token = cred_data.get("access_token")
    if not access_token:
        raise ValueError("No access_token found in credential data")

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://graph.facebook.com/oauth/access_token",
            params={
                "grant_type": "fb_exchange_token",
                "client_id": cred_data.get("client_id", ""),
                "client_secret": cred_data.get("client_secret", ""),
                "fb_exchange_token": access_token,
            },
        )
        resp.raise_for_status()
        token_data = resp.json()

    updated = {**cred_data, "access_token": token_data["access_token"]}
    expires_in = token_data.get("expires_in")
    expires_at = None
    if expires_in:
        from datetime import timedelta
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))

    return updated, expires_at


async def _refresh_hubspot(cred_data: dict) -> tuple[dict, datetime | None]:
    refresh_token = cred_data.get("refresh_token")
    if not refresh_token:
        raise ValueError("No refresh_token found in credential data")

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.hubapi.com/oauth/v1/token",
            data={
                "grant_type": "refresh_token",
                "client_id": cred_data.get("client_id", ""),
                "client_secret": cred_data.get("client_secret", ""),
                "refresh_token": refresh_token,
            },
        )
        resp.raise_for_status()
        token_data = resp.json()

    updated = {
        **cred_data,
        "access_token": token_data["access_token"],
        "refresh_token": token_data.get("refresh_token", refresh_token),
    }
    expires_in = token_data.get("expires_in")
    expires_at = None
    if expires_in:
        from datetime import timedelta
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

    return updated, expires_at


async def _refresh_tiktok(cred_data: dict) -> tuple[dict, datetime | None]:
    refresh_token = cred_data.get("refresh_token")
    if not refresh_token:
        raise ValueError("No refresh_token found in credential data")

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://business-api.tiktok.com/open_api/v1.3/oauth2/refresh_token/",
            json={
                "app_id": cred_data.get("app_id", ""),
                "secret": cred_data.get("app_secret", ""),
                "refresh_token": refresh_token,
            },
        )
        resp.raise_for_status()
        body = resp.json()

    data = body.get("data", {})
    access_token = data.get("access_token")
    if not access_token:
        raise ValueError(f"TikTok refresh failed: {body.get('message', 'unknown error')}")

    updated = {
        **cred_data,
        "access_token": access_token,
        "refresh_token": data.get("refresh_token", refresh_token),
    }
    expires_in = data.get("access_token_expire_in")
    expires_at = None
    if expires_in:
        from datetime import timedelta
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

    return updated, expires_at
