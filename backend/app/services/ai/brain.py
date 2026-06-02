"""
Core AI Brain — central LLM router
receive AgentRequest → dispatch to a specialized Agent → record Token usage + audit log

ported from ReceptivIQ/includes/agent-service/src/brain/router.ts
"""
from __future__ import annotations

import uuid
import time
import logging
from typing import Any, Dict, Literal, Optional

from sqlalchemy.orm import Session

from app.core.sync_database import SyncSession
from app.services.ai.context import build_shared_context, SharedContext
from app.services.ai.agents import persona, creative, attribution

log = logging.getLogger("core-ai-brain")

AgentName = Literal["persona", "creative", "attribution_reporting"]


class AgentRequest:
    def __init__(
        self,
        agent: AgentName,
        agency_id: uuid.UUID,
        user_id: uuid.UUID,
        prompt: str,
        client_id: Optional[uuid.UUID] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.request_id = str(uuid.uuid4())
        self.agent = agent
        self.agency_id = agency_id
        self.client_id = client_id
        self.user_id = user_id
        self.prompt = prompt
        self.context = context or {}


class AgentResponse:
    def __init__(
        self,
        request_id: str,
        agent: AgentName,
        output: dict[str, Any],
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        estimated_cost_usd: float,
        duration_ms: int,
    ) -> None:
        self.request_id = request_id
        self.agent = agent
        self.output = output
        self.model = model
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = prompt_tokens + completion_tokens
        self.estimated_cost_usd = estimated_cost_usd
        self.duration_ms = duration_ms


def check_budget(ctx: SharedContext) -> bool:
    """Check whether the token budget is sufficient. Returns True if budget remains, False if exhausted."""
    return ctx.budget_remaining > 0


def record_usage_orm(req: AgentRequest, resp: AgentResponse) -> None:
    """Write a token-usage record via SQLAlchemy ORM (sync, for use from Celery/sync contexts)."""
    try:
        from app.models.token_usage import TokenUsage
        with SyncSession() as session:
            usage = TokenUsage(
                agency_id=req.agency_id,
                client_id=req.client_id,
                user_id=req.user_id,
                request_id=resp.request_id,
                agent_name=req.agent,
                model=resp.model,
                agent_type=req.agent,
                prompt_tokens=resp.prompt_tokens,
                completion_tokens=resp.completion_tokens,
                total_tokens=resp.total_tokens,
                estimated_cost_usd=resp.estimated_cost_usd,
                cost_usd=resp.estimated_cost_usd,
            )
            session.add(usage)
            session.commit()
    except Exception as e:
        log.warning("Failed to record token usage via ORM: %s", e)


async def route_request(request: AgentRequest) -> AgentResponse:
    """Central router: receive request → assemble context → dispatch Agent → record usage."""
    start_ms = int(time.time() * 1000)
    log.info(
        "Agent request received",
        extra={"request_id": request.request_id, "agent": request.agent, "agency_id": str(request.agency_id)},
    )

    # 1. Assemble Shared Context (brand config + historical campaigns + Persona object)
    ctx = await build_shared_context(
        agency_id=request.agency_id,
        client_id=request.client_id,
        user_id=request.user_id,
        extra=request.context,
    )

    # 1b. Check token budget
    if not check_budget(ctx):
        raise ValueError(
            f"Monthly token budget of {ctx.monthly_token_budget:,} has been exhausted "
            f"(used: {ctx.tokens_used_this_month:,})."
        )

    # 2. Dispatch to the appropriate Agent
    match request.agent:
        case "persona":
            response_data = await persona.run(request, ctx)
        case "creative":
            response_data = await creative.run(request, ctx)
        case "attribution_reporting":
            response_data = await attribution.run(request, ctx)
        case _:
            raise ValueError(f"Unknown agent: {request.agent}")

    duration_ms = int(time.time() * 1000) - start_ms
    response = AgentResponse(
        request_id=request.request_id,
        agent=request.agent,
        duration_ms=duration_ms,
        **response_data,
    )

    # 3. persist：Token usage + Persona structured output + audit log
    record_usage_orm(request, response)
    _persist_structured_output(request, response)
    _record_audit_log(request, response)

    log.info(
        "Agent request completed",
        extra={
            "request_id": request.request_id,
            "agent": request.agent,
            "duration_ms": duration_ms,
            "total_tokens": response.total_tokens,
        },
    )
    return response


# ── Internal persistence helpers ──────────────────────────────────────────────────────────

def _persist_structured_output(req: AgentRequest, resp: AgentResponse) -> None:
    """Write structured output to the corresponding business table (currently supports persona)."""
    try:
        if resp.agent == "persona" and resp.output.get("type") == "persona":
            with SyncSession() as session:
                import json
                session.execute(
                    """
                    INSERT INTO persona_results
                      (agency_id, client_id, persona_data, audience_blueprint,
                       model, prompt_tokens, completion_tokens, cost_usd, created_by)
                    VALUES (:aid, :cid, :pd, :ab, :model, :pt, :ct, :cost, :uid)
                    """,
                    {
                        "aid": req.agency_id, "cid": req.client_id,
                        "pd": json.dumps(resp.output.get("personas", [])),
                        "ab": json.dumps(resp.output.get("audience_blueprint", {})),
                        "model": resp.model,
                        "pt": resp.prompt_tokens, "ct": resp.completion_tokens,
                        "cost": resp.estimated_cost_usd, "uid": req.user_id,
                    },
                )
                session.commit()
    except Exception as e:
        log.warning("Failed to persist structured output: %s", e)


def _record_audit_log(req: AgentRequest, resp: AgentResponse) -> None:
    try:
        with SyncSession() as session:
            session.execute(
                """
                INSERT INTO audit_logs
                  (agency_id, client_id, user_id, action, resource_type,
                   request_id, status, duration_ms)
                VALUES (:aid, :cid, :uid, :action, 'agent', :rid, 'success', :dur)
                """,
                {
                    "aid": req.agency_id, "cid": req.client_id, "uid": req.user_id,
                    "action": f"agent.{req.agent}", "rid": resp.request_id,
                    "dur": resp.duration_ms,
                },
            )
            session.commit()
    except Exception as e:
        log.warning("Failed to record audit log: %s", e)
