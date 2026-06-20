"""Lider coinlər təqvimi — hər major üçün öz planlı hadisəsi.

- BTC: növbəti halving (mempool.space block height-dən hesablanır).
- XRP: aylıq escrow buraxılışı (mexanizm: ayın 1-i).
- BNB: rüblük auto-burn (təxmini — Yan/Apr/İyul/Okt).
- SOL/ASTER + s.: DefiLlama token unlock-ları (major sektordan).

Hər element: {sym, date(ISO), type, note}. type frontend-də lokallaşdırılır.
Nəticə 6 saat keşlənir.
"""
from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

import httpx

from app.analytics.crypto_calendar import get_crypto_calendar

_HALVING_INTERVAL = 210_000
_TTL = 21600.0
_cache: list | None = None
_cache_at = 0.0


async def _btc_halving() -> dict | None:
    """Növbəti BTC halving tarixini block height-dən təxmin edir."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as c:
            r = await c.get("https://mempool.space/api/blocks/tip/height")
            r.raise_for_status()
            height = int(r.text)
    except Exception:  # noqa: BLE001
        return None
    next_block = ((height // _HALVING_INTERVAL) + 1) * _HALVING_INTERVAL
    remaining = next_block - height
    eta = datetime.now(timezone.utc) + timedelta(minutes=remaining * 10)
    return {
        "sym": "BTC",
        "date": eta.date().isoformat(),
        "type": "halving",
        "note": f"~Block {next_block:,}",
    }


def _xrp_escrow() -> dict:
    """Növbəti ayın 1-i — Ripple escrow buraxılışı."""
    now = datetime.now(timezone.utc)
    nxt = (now.replace(day=1) + timedelta(days=32)).replace(day=1)
    return {
        "sym": "XRP",
        "date": nxt.date().isoformat(),
        "type": "escrow",
        "note": "≈1B XRP",
    }


def _bnb_burn() -> dict:
    """Növbəti rüblük BNB auto-burn (təxmini ~20 Yan/Apr/İyul/Okt)."""
    now = datetime.now(timezone.utc)
    for month in (1, 4, 7, 10, 13):
        y, m = (now.year, month) if month <= 12 else (now.year + 1, 1)
        cand = datetime(y, m, 20, tzinfo=timezone.utc)
        if cand > now:
            return {
                "sym": "BNB",
                "date": cand.date().isoformat(),
                "type": "burn",
                "note": "≈Rüblük",
            }
    return {"sym": "BNB", "date": now.date().isoformat(), "type": "burn", "note": "≈Rüblük"}


async def get_majors_calendar() -> list[dict]:
    """Lider coinlərin planlı hadisələri, tarixə görə sıralı."""
    global _cache, _cache_at
    now = time.monotonic()
    if _cache is not None and now - _cache_at < _TTL:
        return _cache

    items: list[dict] = [_xrp_escrow(), _bnb_burn()]
    halving = await _btc_halving()
    if halving:
        items.append(halving)

    # major sektorun DefiLlama unlock-ları (SOL/ASTER və s.)
    for u in await get_crypto_calendar():
        if u.get("sector") == "major":
            items.append(
                {
                    "sym": u["sym"],
                    "date": u["date"],
                    "type": "unlock",
                    "note": f"{u['tokens']}",
                }
            )

    items.sort(key=lambda x: x["date"])
    if items:
        _cache, _cache_at = items, now
    return items
