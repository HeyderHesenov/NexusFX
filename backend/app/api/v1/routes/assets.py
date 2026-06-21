"""Aktiv route-ları — reyestr, canlı qiymət, tarixçə (watchlist/asset/compare)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.analytics import assets

router = APIRouter()


@router.get("")
async def all_assets() -> list[dict]:
    """İzlənə bilən aktivlərin reyestri + Binance top coinlər."""
    return await assets.list_assets()


@router.get("/{key}/quote")
async def asset_quote(key: str) -> dict:
    """Tək aktivin canlı qiyməti."""
    q = await assets.get_quote(key)
    if q is None:
        raise HTTPException(status_code=404, detail="Aktiv tapılmadı")
    return q


@router.get("/{key}")
async def asset_detail(
    key: str, range: str = Query("3mo")
) -> dict:
    """Aktiv: canlı qiymət + tarixi seriya (chart üçün)."""
    quote = await assets.get_quote(key)
    history = await assets.get_history(key, range)
    if quote is None and history is None:
        raise HTTPException(status_code=404, detail="Aktiv tapılmadı")
    return {"quote": quote, "history": history}
