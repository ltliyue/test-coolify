from __future__ import annotations
"""AI Agent base class。"""
from abc import ABC, abstractmethod
from typing import Any, Optional
from dataclasses import dataclass, field

from app.services.ai.context import SharedContext


@dataclass
class AgentResponse:
    agent_type: str
    result: Any
    model: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None


class BaseAgent(ABC):
    agent_type: str = ""

    @abstractmethod
    async def run(self, prompt: str, context: SharedContext, **kwargs: Any) -> AgentResponse:
        """execute agent logic，return AgentResponse。"""
