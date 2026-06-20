"""Xəbər API route-ları — siyahı, axtarış, tək xəbər."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.attributes import flag_modified

from app.agents.forecast_ai import forecast_impact
from app.agents.llm import has_openai
from app.core.constants import Category
from app.db.session import get_db
from app.models import News
from app.schemas.news import NewsOut

_LANGS = {"az", "en", "ru", "tr"}

router = APIRouter()

# selectinload — source adını lazy-load xətası olmadan gətirir.
_BASE = select(News).options(selectinload(News.source))


@router.get("", response_model=list[NewsOut])
async def list_news(
    category: Category | None = Query(None, description="Tab filtri"),
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> list[NewsOut]:
    """Xəbər siyahısı — ən yenidən köhnəyə. category verilsə filtrlənir."""
    stmt = _BASE
    if category is not None:
        stmt = stmt.where(News.category == category.value)
    stmt = stmt.order_by(News.published_at.desc().nullslast()).limit(limit).offset(offset)
    rows = (await db.scalars(stmt)).all()
    return [NewsOut.from_model(n) for n in rows]


@router.get("/search", response_model=list[NewsOut])
async def search_news(
    q: str = Query(..., min_length=1, description="Axtarış sözü"),
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
) -> list[NewsOut]:
    """Başlıq/xülasə üzrə axtarış (orijinal + AZ)."""
    pattern = f"%{q.strip()}%"
    stmt = (
        _BASE.where(
            or_(
                News.title.ilike(pattern),
                News.summary.ilike(pattern),
                News.title_az.ilike(pattern),
                News.summary_az.ilike(pattern),
            )
        )
        .order_by(News.published_at.desc().nullslast())
        .limit(limit)
    )
    rows = (await db.scalars(stmt)).all()
    return [NewsOut.from_model(n) for n in rows]


@router.get("/{news_id}", response_model=NewsOut)
async def get_news(
    news_id: int, db: AsyncSession = Depends(get_db)
) -> NewsOut:
    """Tək xəbər (tam səhifə üçün)."""
    news = (await db.scalars(_BASE.where(News.id == news_id))).first()
    if news is None:
        raise HTTPException(status_code=404, detail="Xəbər tapılmadı")
    return NewsOut.from_model(news, with_content=True)


@router.get("/{news_id}/forecast")
async def get_forecast(
    news_id: int,
    lang: str = Query("az"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """AI bazar proqnozu — dil üzrə keşlənir, yoxdursa GPT ilə yaradılır."""
    lang = lang if lang in _LANGS else "az"
    news = await db.get(News, news_id)
    if news is None:
        raise HTTPException(status_code=404, detail="Xəbər tapılmadı")

    cached = (news.forecast or {}).get(lang)
    if cached:
        return {"ready": True, **cached}

    if not has_openai():
        return {"ready": False}

    fc = await forecast_impact(news.title, news.summary, news.category, lang)
    if not fc:
        return {"ready": False}

    store = dict(news.forecast or {})
    store[lang] = fc
    news.forecast = store
    flag_modified(news, "forecast")
    await db.commit()
    return {"ready": True, **fc}
