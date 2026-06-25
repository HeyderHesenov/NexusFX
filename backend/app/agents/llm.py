"""LLM klient fabrikləri — provayder-agnostik (birincili / ikincili model).

Bütün xarici LLM SDK-ları YALNIZ bu faylda izolyasiya olunur; tətbiqin qalan
hissəsi yalnız `primary_client` / `secondary_client` və `PrimaryClient` /
`SecondaryClient` tiplərini görür.
"""
from __future__ import annotations

from functools import lru_cache

from anthropic import AsyncAnthropic as _SecondarySDK
from openai import AsyncOpenAI as _PrimarySDK

from app.core.config import settings

# Provayder-agnostik tip adları (tətbiqin qalan hissəsi bunları işlədir).
PrimaryClient = _PrimarySDK
SecondaryClient = _SecondarySDK


@lru_cache
def primary_client() -> PrimaryClient:
    """Birincili model klienti (xəbər emalı, RAG, brief)."""
    return _PrimarySDK(api_key=settings.llm_primary_key)


@lru_cache
def secondary_client() -> SecondaryClient:
    """İkincili model klienti (advisor debate)."""
    return _SecondarySDK(api_key=settings.llm_secondary_key)


def has_primary() -> bool:
    return bool(settings.llm_primary_key)


def has_secondary() -> bool:
    return bool(settings.llm_secondary_key)
