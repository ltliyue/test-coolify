from __future__ import annotations
"""AudienceExportService — orchestrate persona → platform audience export。"""
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audience_export import AudienceExport
from app.models.persona import Persona
from app.models.credential import Credential
from app.core.encryption import decrypt_credentials
from app.services.audience_export.translator import PersonaToTargetingTranslator
from app.services.audience_export.meta_client import MetaAudienceClient
from app.services.audience_export.dv360_client import DV360AudienceClient

log = logging.getLogger(__name__)

translator = PersonaToTargetingTranslator()


async def get_platform_credentials(db: AsyncSession, agency_id, platform: str) -> Optional[dict]:
    """from Credential Vault getplatformcredential（compliance rule 9：fetch and decrypt）。"""
    stmt = select(Credential).where(
        Credential.agency_id == agency_id,
        Credential.platform == platform,
        Credential.status == "valid",
    )
    result = await db.execute(stmt)
    cred = result.scalar_one_or_none()
    if not cred:
        return None
    try:
        return decrypt_credentials(cred.encrypted_data)
    except Exception as e:
        log.error("Failed to decrypt credential for %s: %s", platform, type(e).__name__)
        return None


async def execute_export(db: AsyncSession, export_id, agency_id) -> AudienceExport:
    """executesingleaudience export。"""
    # query export record
    result = await db.execute(
        select(AudienceExport).where(
            AudienceExport.id == export_id,
            AudienceExport.agency_id == agency_id,
        )
    )
    export = result.scalar_one_or_none()
    if not export:
        raise ValueError(f"AudienceExport {export_id} not found")

    # query persona
    p_result = await db.execute(
        select(Persona).where(
            Persona.id == export.persona_id,
            Persona.agency_id == agency_id,
            Persona.is_active == True,  # noqa: E712
        )
    )
    persona = p_result.scalar_one_or_none()
    if not persona:
        export.status = "failed"
        export.error_message = "Persona not found or deleted"
        await db.commit()
        return export

    export.status = "processing"
    await db.commit()

    try:
        # get credential
        creds = await get_platform_credentials(db, agency_id, export.platform)

        # callplatform API
        if export.platform == "meta_ads":
            token = creds.get("access_token", "") if creds else ""
            account = creds.get("account_id", "") if creds else ""
            client = MetaAudienceClient(token, account)
            result_data = await client.create_custom_audience(export.targeting_spec)
        elif export.platform == "dv360":
            api_key = creds.get("api_key", "") if creds else ""
            adv_id = creds.get("advertiser_id", "mock") if creds else "mock"
            client = DV360AudienceClient(api_key, adv_id)
            result_data = await client.create_audience_segment(export.targeting_spec)
        else:
            raise ValueError(f"Unsupported platform: {export.platform}")

        export.external_audience_id = result_data.get("id", "")
        export.status = "success"
        export.completed_at = datetime.now(timezone.utc)
        log.info("Audience export success: %s → %s = %s",
                 export.persona_id, export.platform, export.external_audience_id)

    except Exception as e:
        log.error("Audience export failed: %s", e)
        export.retry_count += 1
        if export.retry_count <= 1:
            export.status = "pending"  # Retry
            export.error_message = f"Retry after: {type(e).__name__}"
        else:
            export.status = "failed"
            # V-08 compliancefix：de-identify errorinfo，only keep exception type（cancancontain token）
            export.error_message = f"{type(e).__name__}: export failed"
            export.completed_at = datetime.now(timezone.utc)

    await db.commit()
    return export
