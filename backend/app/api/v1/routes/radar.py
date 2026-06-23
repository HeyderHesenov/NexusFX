"""Radar route-ları — fürsət sıralaması + on-demand AI izahı (hibrid)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.agents import radar_ai
from app.analytics import radar

router = APIRouter()

_LANGS = {"az", "en", "ru", "tr"}


@router.get("")
async def radar_list(
    category: str = Query("crypto"),
    refresh: bool = Query(False),
) -> list[dict]:
    """Kateqoriya üzrə fürsət balı ilə sıralanmış aktivlər (5 dəq keş)."""
    if category not in radar.TAB_CONFIG:
        raise HTTPException(status_code=404, detail="Naməlum kateqoriya")
    return await radar.get_radar(category, force=refresh)


@router.get("/{key}/explain")
async def radar_explain(key: str, lang: str = Query("az")) -> dict:
    """Aktivin niyə radarda olduğunu AI ilə izah edir (yalnız istəklə)."""
    lang = lang if lang in _LANGS else "az"
    # Aktivi sıralamadan tap — onsuz da keşdə.
    for cat in radar.TAB_CONFIG:
        items = await radar.get_radar(cat)
        item = next((i for i in items if i["key"] == key), None)
        if item:
            text = await radar_ai.explain(item, lang)
            return {"ready": text is not None, "text": text or ""}
    raise HTTPException(status_code=404, detail="Aktiv radarda tapılmadı")
