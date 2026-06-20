"""Xəbər Pydantic sxemləri — frontend (camelCase) ilə uyğun."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from app.models import News

_EXCERPT_MAX = 1400


def _excerpt(content: str | None) -> str | None:
    """Tam mətndən təmiz bir hissə — cümlə sərhədində kəsilir."""
    if not content:
        return None
    text = content.strip()
    if len(text) <= _EXCERPT_MAX:
        return text
    cut = text[:_EXCERPT_MAX]
    dot = cut.rfind(". ")
    if dot > _EXCERPT_MAX * 0.5:
        cut = cut[: dot + 1]
    return cut.rstrip() + " …"


class NewsOut(BaseModel):
    """Frontend NewsItem ilə eyni forma. AI emalı varsa az variantı seçilir."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: str
    title: str
    summary: str | None = None
    content: str | None = None
    image_url: str | None = None
    category: str
    source: str | None = None
    original_url: str | None = None
    published_at: datetime | None = None
    sentiment: float | None = None
    impact_score: float | None = None
    is_processed: bool = False
    # {"az": {"title","body"}, "en": {...}, "ru": {...}, "tr": {...}}
    translations: dict | None = None

    @classmethod
    def from_model(cls, n: News, with_content: bool = False) -> "NewsOut":
        """ORM modeli → çıxış sxemi. title/summary orijinal; dil seçimi frontend-də.

        with_content=True yalnız tək-xəbər səhifəsində — siyahını şişirtmir.
        """
        return cls(
            id=str(n.id),
            title=n.title,
            summary=n.summary,
            content=_excerpt(n.content) if with_content else None,
            image_url=n.image_url,
            category=n.category,
            source=n.source.name if n.source else None,
            original_url=n.url,
            published_at=n.published_at,
            sentiment=n.sentiment,
            impact_score=n.impact_score,
            is_processed=n.is_processed,
            translations=n.translations,
        )
