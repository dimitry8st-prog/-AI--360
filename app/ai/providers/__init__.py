from app.ai.providers.base import LLMProvider
from app.ai.providers.stub import StubProvider
from app.core.config import Settings


def get_llm_provider(settings: Settings) -> LLMProvider:
    if not settings.llm_is_live:
        return StubProvider()
    from app.ai.providers.openai_compat import OpenAICompatProvider

    return OpenAICompatProvider(settings)
