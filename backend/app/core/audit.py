"""Unified audit event entry point.

PR 1 of the multi-tenant hardening plan rewrites the audit module:
the legacy simplified helper is gone; every state-changing endpoint
must call ``audit_event(...)`` and ``await`` it. Failure to write the
audit row raises :class:`AuditWriteError` so the calling endpoint
surfaces a 5xx to the client (we never silently lose an audit row).

The current ``public.audit_logs`` schema does not have dedicated
``event / resource / before / after / outcome / occurred_at`` columns,
so we map them onto the existing columns:

    event       -> action
    resource    -> resource_type / resource_id
    before/after-> packed into extra_data JSON
    outcome     -> success boolean + extra_data["outcome"]
    occurred_at -> created_at

Audit writes always go through the platform engine — audit_logs lives in
the platform DB so cross-tenant SRE queries remain possible.
"""
from __future__ import annotations

import json
import logging
import random
import uuid
from datetime import datetime, timezone
from typing import Any, Mapping, Optional

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session as _platform_sessionmaker

# A future PR introduces ``app.core.database.platform_engine`` /
# ``PlatformSessionLocal``; fall back to the unified session maker for now.
try:  # pragma: no cover - defensive import for future split
    from app.core.database import PlatformSessionLocal as _platform_sessionmaker  # type: ignore  # noqa: F401
except Exception:  # noqa: BLE001
    pass

logger = logging.getLogger(__name__)


class AuditWriteError(Exception):
    """Raised when persisting an audit row fails.

    Callers MUST let this propagate so FastAPI returns 5xx. Swallowing
    this exception is a compliance violation (GDPR Art.30 / SOC 2 CC7).
    """


def _coerce_uuid(value: Any) -> Optional[uuid.UUID]:
    if value is None:
        return None
    if isinstance(value, uuid.UUID):
        return value
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError):
        return None


def _extract_request_meta(request: Optional[Request]) -> dict[str, Any]:
    if request is None:
        return {"ip": None, "user_agent": None, "request_id": None,
                "path": None, "method": None}
    ip: Optional[str] = None
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        ip = forwarded.split(",")[0].strip()
    elif request.client:
        ip = request.client.host
    request_id = (
        request.headers.get("x-request-id")
        or getattr(request.state, "request_id", None)
    )
    return {
        "ip": ip,
        "user_agent": request.headers.get("user-agent"),
        "request_id": str(request_id) if request_id else None,
        "path": request.url.path,
        "method": request.method,
    }


def _split_event(event: str) -> tuple[str, str]:
    """Split a dotted event name into (resource_type, resource_action).

    ``personas.create`` -> ("persona", "create"). The last segment is the
    action; everything before becomes the resource_type. Falls back to
    the full string if no dot is present.
    """
    if "." not in event:
        return event, event
    resource, _, _action = event.rpartition(".")
    return resource, event


def should_sample(event: str, rate: float) -> bool:
    """Return True with probability ``rate`` (0..1).

    Used for high-volume events like ``auth.session.guc_set`` that we
    only want to capture probabilistically.
    """
    if rate >= 1.0:
        return True
    if rate <= 0.0:
        return False
    return random.random() < rate  # noqa: S311 - non-cryptographic sampling is fine


async def audit_event(
    *,
    db: AsyncSession,
    event: str,
    actor: Any = None,
    agency_id: Any = None,
    client_id: Any = None,
    resource: Optional[str] = None,
    before: Optional[Mapping[str, Any]] = None,
    after: Optional[Mapping[str, Any]] = None,
    request: Optional[Request] = None,
    outcome: str = "ok",
) -> None:
    """Insert one row into ``public.audit_logs`` and emit a structured log.

    Args:
        db: AsyncSession bound to the request transaction. The row is
            actually written through an independent platform session so
            audit always lands even if the caller rolls back.
        event: Dotted event name like ``personas.create`` or
            ``platform.agency.suspend``.
        actor: The current user (object with ``.id`` + ``.role`` /
            ``.agency_id``) or a raw UUID. Optional for unauthenticated
            paths.
        agency_id / client_id: Tenant scoping. If ``actor`` is provided
            and these are omitted, we read them from the actor.
        resource: Resource identifier (e.g. the affected row's id).
        before / after: Field-level snapshots for PATCH/DELETE. MUST NOT
            include PII (e.g. ``email_encrypted``). Stored as JSON in
            ``extra_data``.
        request: FastAPI Request, used to capture ip / user_agent /
            request_id.
        outcome: "ok" / "denied" / "error" / "403" / ...

    Raises:
        AuditWriteError: when the underlying INSERT fails. Callers must
            propagate this so the endpoint returns 5xx.
    """
    actor_id: Optional[uuid.UUID]
    actor_role: Optional[str] = None
    if actor is None:
        actor_id = None
    elif isinstance(actor, uuid.UUID):
        actor_id = actor
    else:
        actor_id = _coerce_uuid(getattr(actor, "id", None))
        role = getattr(actor, "role", None)
        if role is not None:
            actor_role = role.value if hasattr(role, "value") else str(role)
        if agency_id is None:
            agency_id = getattr(actor, "agency_id", None)
        if client_id is None:
            client_id = getattr(actor, "client_id", None)

    agency_uuid = _coerce_uuid(agency_id)
    client_uuid = _coerce_uuid(client_id)
    resource_type, _ = _split_event(event)

    meta = _extract_request_meta(request)

    extra: dict[str, Any] = {"outcome": outcome}
    if actor_role:
        extra["actor_role"] = actor_role
    if before is not None:
        extra["before"] = dict(before)
    if after is not None:
        extra["after"] = dict(after)
    if meta["request_id"]:
        extra["request_id"] = meta["request_id"]

    occurred_at = datetime.now(timezone.utc)
    success = outcome in {"ok", "shadow"}

    log_payload = {
        "event": event,
        "actor_id": str(actor_id) if actor_id else None,
        "actor_role": actor_role,
        "agency_id": str(agency_uuid) if agency_uuid else None,
        "client_id": str(client_uuid) if client_uuid else None,
        "resource_type": resource_type,
        "resource_id": resource or "",
        "outcome": outcome,
        "ip": meta["ip"],
        "user_agent": meta["user_agent"],
        "request_id": meta["request_id"],
        "path": meta["path"],
        "method": meta["method"],
        "occurred_at": occurred_at.isoformat(),
    }

    # Always emit structured stdout log first (CloudTrail-style ingestion);
    # even if the DB write fails operators have a record.
    logger.info("audit", extra={"audit_event": log_payload})

    # Use an independent platform session so audit lands even if the
    # business transaction rolls back. We commit it immediately.
    try:
        async with _platform_sessionmaker() as session:
            await session.execute(
                _AUDIT_INSERT_SQL,
                {
                    "agency_id": agency_uuid,
                    "client_id": client_uuid,
                    "user_id": actor_id,
                    "action": event,
                    "resource_type": resource_type,
                    "resource_id": resource or "",
                    "ip_address": meta["ip"],
                    "user_agent": meta["user_agent"],
                    "request_path": meta["path"],
                    "request_method": meta["method"],
                    "success": success,
                    "error_message": None if success else outcome,
                    "contains_phi": False,
                    "data_level": "internal",
                    "extra_data": json.dumps(extra),
                    "created_at": occurred_at,
                },
            )
            await session.commit()
    except Exception as exc:  # noqa: BLE001
        # Surface a clean error type. Callers MUST NOT swallow this —
        # endpoints should return 5xx so the client sees the failure.
        logger.error("audit write failed for event=%s: %s", event, exc)
        raise AuditWriteError(f"audit write failed: {exc}") from exc


# Defer the text() construction until module import time so SQLAlchemy
# parses the bindparams once.
from sqlalchemy import text  # noqa: E402

_AUDIT_INSERT_SQL = text(
    """
    INSERT INTO public.audit_logs (
        agency_id, client_id, user_id, action, resource_type, resource_id,
        ip_address, user_agent, request_path, request_method,
        success, error_message, contains_phi, data_level, extra_data, created_at
    )
    VALUES (
        :agency_id, :client_id, :user_id, :action, :resource_type, :resource_id,
        :ip_address, :user_agent, :request_path, :request_method,
        :success, :error_message, :contains_phi, :data_level,
        CAST(:extra_data AS jsonb), :created_at
    )
    """
)


__all__ = ["AuditWriteError", "audit_event", "should_sample"]
