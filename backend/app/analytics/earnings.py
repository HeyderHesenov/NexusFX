"""US səhm gəlir (earnings) təqvimi — yfinance ilə yaxın hesabat tarixləri.

Hər iri şirkət üçün ən yaxın GƏLƏCƏK earnings tarixi. 6 saat keşlənir
(tarixlər tez-tez dəyişmir). yfinance sinxron → thread-də paralel çağırılır.
"""
from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone

import yfinance as yf

# (ticker, şirkət adı, AI-səhmidirmi) — iri kapitallı US şirkətləri.
# ai=True → "AI Səhmləri" kateqoriyasında da görünür.
_TICKERS = [
    ("AAPL", "Apple", False),
    ("MSFT", "Microsoft", True),
    ("NVDA", "NVIDIA", True),
    ("AMZN", "Amazon", False),
    ("GOOGL", "Alphabet", True),
    ("META", "Meta", True),
    ("TSLA", "Tesla", False),
    ("JPM", "JPMorgan", False),
    ("V", "Visa", False),
    ("WMT", "Walmart", False),
    ("XOM", "Exxon Mobil", False),
    ("NFLX", "Netflix", False),
    ("AMD", "AMD", True),
    ("KO", "Coca-Cola", False),
    ("DIS", "Disney", False),
    # AI-yönümlü əlavələr
    ("AVGO", "Broadcom", True),
    ("MU", "Micron", True),
    ("SMCI", "Super Micro", True),
    ("ARM", "Arm Holdings", True),
    ("TSM", "TSMC", True),
    ("PLTR", "Palantir", True),
]

_TTL = 21600.0  # 6 saat
_cache: list | None = None
_cache_at = 0.0


def _next_earning(sym: str, name: str, ai: bool) -> dict | None:
    """Bu ticker üçün ən yaxın gələcək earnings tarixi (yoxdursa None)."""
    try:
        df = yf.Ticker(sym).get_earnings_dates(limit=8)
        if df is None or df.empty:
            return None
        now = datetime.now(timezone.utc)
        future = [ts for ts in df.index.to_pydatetime() if ts.astimezone(timezone.utc) >= now]
        if not future:
            return None
        ts = min(future)
        return {
            "sym": sym,
            "name": name,
            "date": ts.date().isoformat(),
            "time": ts.strftime("%H:%M"),
            "ai": ai,
        }
    except Exception:  # noqa: BLE001
        return None


async def get_earnings() -> list[dict]:
    """Yaxın earnings hesabatları, tarixə görə sıralı. Xəta → son keş / boş."""
    global _cache, _cache_at
    now = time.monotonic()
    if _cache is not None and now - _cache_at < _TTL:
        return _cache
    try:
        results = await asyncio.gather(
            *(asyncio.to_thread(_next_earning, s, n, ai) for s, n, ai in _TICKERS)
        )
    except Exception:  # noqa: BLE001
        return _cache or []
    items = sorted((r for r in results if r), key=lambda x: x["date"])
    if items:
        _cache, _cache_at = items, now
    return items
