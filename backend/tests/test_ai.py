"""
F-09：AI Brain API test。
test POST /api/v1/ai/chat  and  GET /api/v1/ai/usage/monthly。
not depend on real OpenRouter API（OPENROUTER_API_KEY to empty when use placeholder reply）。
"""
from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import AsyncClient


# ── TC-AI-01：no token access /ai/chat return 401 ─────────────────────────────────
@pytest.mark.asyncio
async def test_ai_chat_requires_auth(client: AsyncClient):
    resp = await client.post("/api/v1/ai/chat", json={
        "agent_type": "general",
        "prompt": "Hello",
    })
    assert resp.status_code in (401, 403)


# ── TC-AI-02：no token access /ai/usage/monthly return 401 ────────────────────────
@pytest.mark.asyncio
async def test_ai_usage_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/ai/usage/monthly")
    assert resp.status_code in (401, 403)


# ── TC-AI-03：normalrequest /ai/chat returnresponse ─────────────────────────────────────
@pytest.mark.asyncio
async def test_ai_chat_success(client: AsyncClient, auth_headers: dict):
    """
    Without OPENROUTER_API_KEY a placeholder text is returned, but HTTP status should be 200.
    Verify response structure: agent_type, result, model, tokens_used, budget_remaining are all present.
    """
    resp = await client.post(
        "/api/v1/ai/chat",
        json={"agent_type": "general", "prompt": "What is marketing?"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "agent_type" in data
    assert data["agent_type"] == "general"
    assert "result" in data
    assert "model" in data
    assert "tokens_used" in data
    assert "budget_remaining" in data
    assert data["budget_remaining"] >= 0


# ── TC-AI-04: budget_remaining is computed correctly ────────────────────────────
@pytest.mark.asyncio
async def test_ai_chat_budget_remaining_reflects_usage(
    client: AsyncClient, auth_headers: dict, test_agency
):
    """
    budget_remaining = monthly_token_budget - tokens_used_this_month
    no API key  when  tokens_used=0，budget_remaining should etc.in agency.monthly_token_budget。
    """
    resp = await client.post(
        "/api/v1/ai/chat",
        json={"agent_type": "persona", "prompt": "Describe the target audience."},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    # Without a real LLM call tokens_used=0, so budget_remaining should equal the default budget
    assert data["budget_remaining"] == test_agency.monthly_token_budget


# ── TC-AI-05：over budget when return 429 ────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_ai_chat_budget_exceeded(
    client: AsyncClient, auth_headers: dict, test_agency, test_user
):
    """
    manualwrite many token_usage over budget，/ai/chat should return 429 BUDGET_EXCEEDED。
    """
    from sqlalchemy import text
    import uuid
    from tests.conftest import TestSession

    # write exceeding budget  token_usage record
    async with TestSession() as session:
        await session.execute(text("""
            INSERT INTO token_usage (agency_id, user_id, model, total_tokens)
            VALUES (:agency_id, :user_id, 'test-model', :tokens)
        """), {
            "agency_id": str(test_agency.id),
            "user_id": str(test_user.id),
            "tokens": test_agency.monthly_token_budget + 1,
        })
        await session.commit()

    resp = await client.post(
        "/api/v1/ai/chat",
        json={"agent_type": "general", "prompt": "Hello"},
        headers=auth_headers,
    )
    assert resp.status_code == 429
    detail = resp.json().get("detail", {})
    assert detail.get("code") == "BUDGET_EXCEEDED"


# ── TC-AI-06：/ai/usage/monthly returncorrectstructure ──────────────────────────────────
@pytest.mark.asyncio
async def test_ai_usage_monthly_structure(
    client: AsyncClient, auth_headers: dict, test_agency
):
    """The monthly usage summary should contain the correct fields, and total_tokens=0 when usage is empty."""
    resp = await client.get("/api/v1/ai/usage/monthly", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "agency_id" in data
    assert data["agency_id"] == str(test_agency.id)
    assert "month" in data
    assert "total_tokens" in data
    assert data["total_tokens"] == 0  # has noanyuserecord
    assert "budget" in data
    assert data["budget"] == test_agency.monthly_token_budget
    assert "budget_remaining" in data
    assert data["budget_remaining"] == test_agency.monthly_token_budget
    assert "by_model" in data
    assert "by_agent" in data
    assert isinstance(data["by_model"], dict)
    assert isinstance(data["by_agent"], dict)


# ── TC-AI-07：/ai/usage/monthly  containing usage when aggregatecorrect ──────────────────────────────
@pytest.mark.asyncio
async def test_ai_usage_monthly_with_records(
    client: AsyncClient, auth_headers: dict, test_agency, test_user
):
    """After inserting 2 token_usage records, the monthly summary should aggregate correctly."""
    from sqlalchemy import text
    from tests.conftest import TestSession

    async with TestSession() as session:
        await session.execute(text("""
            INSERT INTO token_usage (agency_id, user_id, model, agent_type, prompt_tokens, completion_tokens, total_tokens)
            VALUES
              (:agency_id, :user_id, 'claude-sonnet', 'persona', 100, 50, 150),
              (:agency_id, :user_id, 'claude-sonnet', 'creative', 200, 80, 280)
        """), {
            "agency_id": str(test_agency.id),
            "user_id": str(test_user.id),
        })
        await session.commit()

    resp = await client.get("/api/v1/ai/usage/monthly", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_tokens"] == 430
    assert data["by_model"].get("claude-sonnet") == 430
    assert data["by_agent"].get("persona") == 150
    assert data["by_agent"].get("creative") == 280
    assert data["budget_remaining"] == test_agency.monthly_token_budget - 430
