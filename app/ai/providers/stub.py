from typing import Any

from app.ai.providers.base import LLMProvider
from app.schemas.ai import NO_SOURCE_ANSWER


class StubProvider(LLMProvider):
    """Safe fallback when LLM is disabled or unreachable. Does not invent corporate rules."""

    name = "stub"

    async def complete_json(self, *, system: str, user: str, temperature: float) -> dict[str, Any]:
        return {
            "answer": NO_SOURCE_ANSWER,
            "explanation": "AI-провайдер отключён. Доступны обучение по материалам и ручная проверка.",
            "citations": [],
            "confidence": 0.0,
            "knowledge_gaps": [],
            "next_action": "escalate",
            "requires_human": True,
        }
