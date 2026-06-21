"""Aktiv reyestri + canlı qiymət/tarixçə — watchlist, asset səhifəsi, müqayisə.

Tək mənbə: yfinance. Qiymət fast_info (canlı), tarixçə isə gündəlik bağlanış.
Nəticələr keşlənir.
"""
from __future__ import annotations

import asyncio
import time

import httpx
import yfinance as yf

from app.analytics.market import _live_last_prev

# (key, label, Yahoo simvolu, tip, dəqiqlik)
ASSETS: list[tuple[str, str, str, str, int]] = [
    ("btc", "BTC", "BTC-USD", "crypto", 0),
    ("eth", "ETH", "ETH-USD", "crypto", 0),
    ("sol", "SOL", "SOL-USD", "crypto", 2),
    ("xrp", "XRP", "XRP-USD", "crypto", 3),
    ("spx", "S&P 500", "^GSPC", "index", 0),
    ("ndx", "NASDAQ", "^NDX", "index", 0),
    ("dji", "Dow Jones", "^DJI", "index", 0),
    ("eurusd", "EUR/USD", "EURUSD=X", "forex", 4),
    ("gbpusd", "GBP/USD", "GBPUSD=X", "forex", 4),
    ("usdjpy", "USD/JPY", "USDJPY=X", "forex", 2),
    ("dxy", "DXY", "DX-Y.NYB", "forex", 2),
    ("oil", "WTI Oil", "CL=F", "commodity", 2),
    ("brent", "Brent", "BZ=F", "commodity", 2),
    ("natgas", "Nat Gas", "NG=F", "commodity", 3),
    ("gold", "Gold", "GC=F", "metal", 1),
    ("silver", "Silver", "SI=F", "metal", 2),
]

_BY_KEY = {k: (k, lbl, sym, typ, dec) for k, lbl, sym, typ, dec in ASSETS}

_RANGE_MAP = {
    "1mo": ("1mo", "1d"),
    "3mo": ("3mo", "1d"),
    "6mo": ("6mo", "1d"),
    "1y": ("1y", "1d"),
}

_quote_cache: dict[str, tuple[float, dict]] = {}
_hist_cache: dict[str, tuple[float, dict]] = {}
_QUOTE_TTL = 60.0
_HIST_TTL = 1800.0

# ---- Binance top coinlər (dinamik) ----
# Reyestrdə onsuz da olan baza coinlər (dublikat olmasın).
_REGISTRY_BASES = {"BTC", "ETH", "SOL", "XRP"}
# Stablecoin / leveraged token — atlanır.
_SKIP_BASES = {"USDT", "USDC", "FDUSD", "TUSD", "BUSD", "DAI", "USDP", "EUR", "USDE"}
_TOP_COINS = 50
_COINS_TTL = 300.0  # 5 dəqiqə
# key → {label, symbol, price, chgPct}
_coins: dict[str, dict] = {}
_coins_ts = 0.0


def _is_leveraged(base: str) -> bool:
    return any(base.endswith(x) for x in ("UP", "DOWN", "BULL", "BEAR"))


async def _ensure_coins() -> None:
    """Binance-dən həcmə görə top coinləri çəkir (5 dəq keş)."""
    global _coins, _coins_ts
    now = time.time()
    if _coins and now - _coins_ts < _COINS_TTL:
        return
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            r = await client.get("https://api.binance.com/api/v3/ticker/24hr")
            r.raise_for_status()
            rows = r.json()
    except (httpx.HTTPError, ValueError):
        return  # köhnə keş qalır

    usdt = [
        row for row in rows
        if row.get("symbol", "").endswith("USDT")
    ]
    usdt.sort(key=lambda x: float(x.get("quoteVolume", 0) or 0), reverse=True)

    coins: dict[str, dict] = {}
    for row in usdt:
        sym = row["symbol"]
        base = sym[:-4]  # "USDT" çıxar
        if (
            base in _REGISTRY_BASES
            or base in _SKIP_BASES
            or "USD" in base  # stablecoin variantları (USD1, USDE, ...)
            or _is_leveraged(base)
        ):
            continue
        key = f"c_{base.lower()}"
        coins[key] = {
            "label": base,
            "symbol": sym,
            "price": float(row.get("lastPrice", 0) or 0),
            "chgPct": float(row.get("priceChangePercent", 0) or 0),
        }
        if len(coins) >= _TOP_COINS:
            break

    if coins:
        _coins = coins
        _coins_ts = now


async def list_assets() -> list[dict]:
    """Reyestr metadatası (UI seçicilər üçün) + Binance top coinlər."""
    await _ensure_coins()
    base = [
        {"key": k, "label": lbl, "sym": sym, "type": typ}
        for k, lbl, sym, typ, _ in ASSETS
    ]
    coins = [
        {"key": k, "label": v["label"], "sym": v["symbol"], "type": "crypto"}
        for k, v in _coins.items()
    ]
    return base + coins


def _coin_dec(price: float) -> int:
    if price >= 1000:
        return 0
    if price >= 1:
        return 2
    if price >= 0.01:
        return 4
    return 6


def _fmt(value: float, dec: int) -> str:
    return f"{value:,.0f}" if dec == 0 else f"{value:,.{dec}f}"


def _quote_sync(key: str) -> dict | None:
    meta = _BY_KEY.get(key)
    if not meta:
        return None
    _, label, sym, typ, dec = meta
    lp = _live_last_prev(sym)
    if lp is None:
        return None
    last, prev = lp
    chg = (last - prev) / prev * 100 if prev else 0.0
    return {
        "key": key,
        "label": label,
        "type": typ,
        "val": _fmt(last, dec),
        "price": round(last, max(dec, 2)),
        "chg": f"{chg:+.2f}%",
        "chgPct": round(chg, 2),
        "up": chg >= 0,
    }


async def get_quote(key: str) -> dict | None:
    """Tək aktivin canlı qiyməti (60s keş)."""
    if key.startswith("c_"):
        await _ensure_coins()
        c = _coins.get(key)
        if not c:
            return None
        last, chg = c["price"], c["chgPct"]
        dec = _coin_dec(last)
        return {
            "key": key,
            "label": c["label"],
            "type": "crypto",
            "val": _fmt(last, dec),
            "price": last,
            "chg": f"{chg:+.2f}%",
            "chgPct": round(chg, 2),
            "up": chg >= 0,
        }

    now = time.time()
    cached = _quote_cache.get(key)
    if cached and now - cached[0] < _QUOTE_TTL:
        return cached[1]
    data = await asyncio.to_thread(_quote_sync, key)
    if data:
        _quote_cache[key] = (now, data)
    return data


_KLINE_LIMITS = {"1mo": 30, "3mo": 90, "6mo": 180, "1y": 365}


async def _coin_history(key: str, rng: str) -> dict | None:
    c = _coins.get(key)
    if not c:
        return None
    limit = _KLINE_LIMITS.get(rng, 90)
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            r = await client.get(
                "https://api.binance.com/api/v3/klines",
                params={"symbol": c["symbol"], "interval": "1d", "limit": limit},
            )
            r.raise_for_status()
            rows = r.json()
    except (httpx.HTTPError, ValueError):
        return None
    dec = _coin_dec(c["price"])
    points = []
    for k in rows:
        ts = int(k[0]) // 1000
        from datetime import datetime, timezone

        d = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
        points.append({"date": d, "close": round(float(k[4]), max(dec, 2))})
    if len(points) < 2:
        return None
    first, last = points[0]["close"], points[-1]["close"]
    chg = (last - first) / first * 100 if first else 0.0
    return {
        "key": key,
        "label": c["label"],
        "type": "crypto",
        "range": rng,
        "points": points,
        "changePct": round(chg, 2),
    }


def _history_sync(key: str, rng: str) -> dict | None:
    meta = _BY_KEY.get(key)
    if not meta:
        return None
    _, label, sym, typ, dec = meta
    period, interval = _RANGE_MAP.get(rng, _RANGE_MAP["3mo"])
    try:
        df = yf.download(
            sym, period=period, interval=interval,
            auto_adjust=True, progress=False, threads=True,
        )["Close"]
    except Exception:  # noqa: BLE001
        return None
    series = df.dropna()
    if hasattr(series, "iloc") and getattr(series, "ndim", 1) > 1:
        series = series.iloc[:, 0]
    points = [
        {"date": d.strftime("%Y-%m-%d"), "close": round(float(v), max(dec, 2))}
        for d, v in series.items()
    ]
    if len(points) < 2:
        return None
    first = points[0]["close"]
    last = points[-1]["close"]
    chg = (last - first) / first * 100 if first else 0.0
    return {
        "key": key,
        "label": label,
        "type": typ,
        "range": rng,
        "points": points,
        "changePct": round(chg, 2),
    }


async def get_history(key: str, rng: str = "3mo") -> dict | None:
    """Aktivin tarixi qiymət seriyası (30 dəq keş)."""
    rng = rng if rng in _RANGE_MAP else "3mo"
    ck = f"{key}:{rng}"
    now = time.time()
    cached = _hist_cache.get(ck)
    if cached and now - cached[0] < _HIST_TTL:
        return cached[1]

    if key.startswith("c_"):
        await _ensure_coins()
        data = await _coin_history(key, rng)
    else:
        data = await asyncio.to_thread(_history_sync, key, rng)

    if data:
        _hist_cache[ck] = (now, data)
    return data
