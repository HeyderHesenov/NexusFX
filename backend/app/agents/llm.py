"""LLM klient fabrikləri — GPT (xəbər emalı) və Claude (advisor debate)."""
from __future__ import annotations

from functools import lru_cache

from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

from app.core.config import settings


@lru_cache
def openai_client() -> AsyncOpenAI:
    """Tək AsyncOpenAI instansı (xəbər tərcümə/yenidən yazma)."""
    return AsyncOpenAI(api_key=settings.openai_api_key)


@lru_cache
def anthropic_client() -> AsyncAnthropic:
    """Tək AsyncAnthropic instansı (advisor debate)."""
    return AsyncAnthropic(api_key=settings.anthropic_api_key)


def has_openai() -> bool:
    return bool(settings.openai_api_key)


def has_anthropic() -> bool:
    return bool(settings.anthropic_api_key)
