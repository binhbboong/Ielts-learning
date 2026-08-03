from functools import lru_cache

from app.ai.claude_provider import ClaudeProvider
from app.ai.local_provider import LocalAIProvider
from app.ai.openai_provider import OpenAIProvider
from app.ai.provider import AIProvider
from app.core.config import settings


@lru_cache
def get_ai_provider() -> AIProvider:
    if settings.AI_PROVIDER == "claude":
        return ClaudeProvider()
    if settings.AI_PROVIDER == "local":
        return LocalAIProvider()
    if settings.AI_PROVIDER == "openai":
        return OpenAIProvider()
    raise ValueError(f"Unsupported AI provider: {settings.AI_PROVIDER}")
