from __future__ import annotations
"""platform OAuth authorizeflow — authorize URL generate + callback process。"""
import hashlib
import hmac
import time
import uuid
import logging
from typing import Optional
from urllib.parse import urlencode
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.tenant_db import get_tenant_db
from app.core.deps import get_current_user
from app.core.encryption import encrypt_credentials
from app.models.user import User
from app.models.credential import Credential
from app.models.integration import Integration
from app.models.enums import (
    AuthType, CredentialType, CredentialStatus,
    IntegrationPlatform, IntegrationStatus,
)

# C-01: HMAC-signed state parameter to prevent CSRF and cross-tenant attacks
_STATE_TTL = 600  # 10-minute expiration


def _sign_state(agency_id: str, user_id: str) -> str:
    """Generate an HMAC-signed state: payload|timestamp|signature"""
    ts = str(int(time.time()))
    payload = f"{agency_id}:{user_id}:{ts}"
    sig = hmac.new(settings.SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()[:32]
    return f"{payload}:{sig}"


def _verify_state(state: str) -> tuple:
    """Verify and parse state, returning (agency_id, user_id). Raises on invalid or expired state."""
    parts = state.split(":")
    if len(parts) != 4:
        raise ValueError("Malformed state")
    agency_str, user_str, ts_str, sig = parts
    # verify signature
    payload = f"{agency_str}:{user_str}:{ts_str}"
    expected = hmac.new(settings.SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()[:32]
    if not hmac.compare_digest(sig, expected):
        raise ValueError("Invalid signature")
    # verifyexpire
    if int(time.time()) - int(ts_str) > _STATE_TTL:
        raise ValueError("State expired")
    return uuid.UUID(agency_str), uuid.UUID(user_str)

log = logging.getLogger(__name__)
router = APIRouter(prefix="/integrations/oauth", tags=["oauth"])

# each platform OAuth config
_OAUTH_CONFIG = {
    "ga4": {
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "scopes": "https://www.googleapis.com/auth/analytics.readonly",
        "client_id_env": "GA4_CLIENT_ID",
        "client_secret_env": "GA4_CLIENT_SECRET",
        "redirect_uri_env": "GA4_REDIRECT_URI",
        "platform_enum": IntegrationPlatform.GA4,
    },
    "meta_ads": {
        "auth_url": "https://www.facebook.com/v19.0/dialog/oauth",
        "token_url": "https://graph.facebook.com/v19.0/oauth/access_token",
        "scopes": "ads_read,ads_management,read_insights",
        "client_id_env": "META_APP_ID",
        "client_secret_env": "META_APP_SECRET",
        "redirect_uri_env": "META_REDIRECT_URI",
        "platform_enum": IntegrationPlatform.META_ADS,
    },
    "hubspot": {
        "auth_url": "https://app.hubspot.com/oauth/authorize",
        "token_url": "https://api.hubapi.com/oauth/v1/token",
        "scopes": "crm.objects.contacts.read",
        "client_id_env": "HUBSPOT_CLIENT_ID",
        "client_secret_env": "HUBSPOT_CLIENT_SECRET",
        "redirect_uri_env": "HUBSPOT_REDIRECT_URI",
        "platform_enum": IntegrationPlatform.HUBSPOT,
    },
}

_PLATFORM_REDIRECT_URI_MAP = {
    "GA4_REDIRECT_URI": "http://localhost:8000/api/v1/integrations/oauth/callback/ga4",
    "META_REDIRECT_URI": "http://localhost:8000/api/v1/integrations/oauth/callback/meta_ads",
    "HUBSPOT_REDIRECT_URI": "http://localhost:8000/api/v1/integrations/oauth/callback/hubspot",
}


def _get_env(key: str) -> str:
    val = getattr(settings, key, "") or _PLATFORM_REDIRECT_URI_MAP.get(key, "")
    return val


@router.get("/authorize/{platform}")
async def get_authorize_url(
    platform: str,
    user: User = Depends(get_current_user),
):
    """Generate a platform OAuth authorize URL; the frontend redirects to it for user authorization."""
    config = _OAUTH_CONFIG.get(platform)
    if not config:
        raise HTTPException(status_code=400, detail=f"Unsupported OAuth platform: {platform}")

    client_id = _get_env(config["client_id_env"])
    redirect_uri = _get_env(config["redirect_uri_env"])

    if not client_id:
        raise HTTPException(status_code=400, detail=f"{platform} OAuth not configured")

    # C-01: HMAC-signed state to prevent CSRF + cross-tenant attacks
    state_str = _sign_state(str(user.agency_id), str(user.id))

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": config["scopes"],
        "state": state_str,
        "access_type": "offline",
        "prompt": "consent",
    }
    authorize_url = f"{config['auth_url']}?{urlencode(params)}"
    return {"authorize_url": authorize_url, "platform": platform}


@router.get("/callback/{platform}")
async def handle_oauth_callback(
    platform: str,
    code: str = Query(...),
    state: str = Query(""),
    db: AsyncSession = Depends(get_tenant_db),
):
    """process OAuth callback：exchange code for access_token，encrypt and storecredential，createintegration record。"""
    config = _OAUTH_CONFIG.get(platform)
    if not config:
        raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}")

    client_id = _get_env(config["client_id_env"])
    client_secret = _get_env(config["client_secret_env"])
    redirect_uri = _get_env(config["redirect_uri_env"])

    if not client_id or not client_secret:
        raise HTTPException(status_code=500, detail=f"{platform} OAuth not configured on server")

    # C-01 + C-02: verify HMAC-signed state (replaces the authentication dependency)
    try:
        agency_id, user_id = _verify_state(state)
    except (ValueError, Exception):
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")

    # authorization_code → access_token
    token_data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(config["token_url"], data=token_data)
            if resp.status_code != 200:
                log.error("OAuth token exchange failed for %s: status=%d", platform, resp.status_code)
                raise HTTPException(status_code=400, detail="Token exchange failed")
            tokens = resp.json()
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="Failed to reach OAuth provider")

    access_token = tokens.get("access_token", "")
    refresh_token = tokens.get("refresh_token", "")

    # encrypt and storecredential
    encrypted = encrypt_credentials({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": tokens.get("token_type", "Bearer"),
    })
    credential = Credential(
        agency_id=agency_id,
        platform=platform,
        credential_type=CredentialType.OAUTH,
        encrypted_data=encrypted,
        status=CredentialStatus.VALID,
        created_by=user_id,
    )
    db.add(credential)
    await db.flush()

    # create Integration record
    integration = Integration(
        agency_id=agency_id,
        platform=config["platform_enum"],
        auth_type=AuthType.OAUTH,
        status=IntegrationStatus.CONNECTED,
        credential_id=credential.id,
        config={"connected_by": str(user_id)},
        connected_at=datetime.now(timezone.utc),
        created_by=user_id,
    )
    db.add(integration)

    # audit log
    from app.core.audit import audit_event
    await audit_event(
        db=db,
        event="oauth.connect",
        actor=user_id,
        agency_id=agency_id,
        resource=platform,
    )

    await db.commit()

    return {
        "status": "connected",
        "platform": platform,
        "integration_id": str(integration.id),
    }
