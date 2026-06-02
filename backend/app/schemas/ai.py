from __future__ import annotations
from typing import Optional, Any, Dict
from pydantic import BaseModel, ConfigDict


class AIRequest(BaseModel):
    agent_type: str  # "persona" | "creative" | "attribution" | "general"
    prompt: str
    client_id: Optional[str] = None
    context_override: Optional[Dict[str, Any]] = None  # May override the default context


class AIResponse(BaseModel):
    agent_type: str
    result: Any
    model: str = ""
    tokens_used: int = 0
    budget_remaining: int = 0
    error: Optional[str] = None


class TokenUsageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    model: str
    agent_type: Optional[str] = None
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: Optional[float] = None


class MonthlyUsageSummary(BaseModel):
    agency_id: str
    month: str
    total_tokens: int
    total_cost_usd: float
    budget: int
    budget_remaining: int
    by_model: Dict[str, Any]
    by_agent: Dict[str, Any]
