"""Crypto Fear & Greed indeksi — alternative.me pulsuz API (açarsız).

Dəyər 0-100 + təsnifat. Nəticə 10 dəqiqə keşlənir (indeks gündə bir dəyişir).
"""
from __future__ import annotations

import time

import httpx

_URL = "https://api.alternative.me/fng/?limit=1"
_TTL = 600.0
_cache: dict | None = None
_cache_at = 0.0


async def get_fear_greed() -> dict | None:
    """{value:int, label:str, updatedAt:int} — xəta olsa son keş və ya None."""
    global _cache, _cache_at
    now = time.monotonic()
    if _cache and now - _cache_at < _TTL:
        return _cache
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(_URL)
            r.raise_for_status()
            d = (r.json().get("data") or [])[0]
        out = {
            "value": int(d["value"]),
            "label": str(d["value_classification"]),
            "updatedAt": int(d["timestamp"]),
        }
    except Exception:  # noqa: BLE001
        return _cache
    _cache, _cache_at = out, now
    return out
