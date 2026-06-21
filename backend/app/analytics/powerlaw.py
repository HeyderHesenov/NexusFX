"""Bitcoin Power Law (Güc Qanunu) modeli — uzunmüddətli ədalətli dəyər.

Santostasi power-law: log10(qiymət) = a + b·log10(genesis-dən günlər).
BTC-nin 15+ illik tarixi log-log qrafikdə düz xəttə oturur (b ≈ 5.8, R² ≈ 0.95).

Sabit əmsal HARDCODE EDİLMİR — model BTC-nin tam tarixindən real reqressiya ilə
fit edilir, beləcə R² və proqnozlar həqiqi datadan çıxır.
"""
from __future__ import annotations

import asyncio
import time
from datetime import date, datetime, timedelta, timezone

import numpy as np
import yfinance as yf

GENESIS = date(2009, 1, 3)  # Bitcoin genesis bloku
_cache: dict = {"ts": 0.0, "data": None}
_TTL = 6 * 3600.0  # 6 saat


def _fit_sync() -> dict | None:
    df = yf.download(
        "BTC-USD", period="max", interval="1d",
        auto_adjust=True, progress=False, threads=True,
    )["Close"]
    series = df.dropna()
    if hasattr(series, "ndim") and series.ndim > 1:
        series = series.iloc[:, 0]
    if len(series) < 500:
        return None

    dates = [d.date() if hasattr(d, "date") else d for d in series.index]
    days = np.array([(d - GENESIS).days for d in dates], dtype=float)
    prices = series.to_numpy(dtype=float)
    mask = (days > 0) & (prices > 0)
    days, prices, dates = days[mask], prices[mask], [d for d, m in zip(dates, mask) if m]

    x = np.log10(days)
    y = np.log10(prices)
    b, a = np.polyfit(x, y, 1)  # y = b*x + a

    yhat = a + b * x
    ss_res = float(np.sum((y - yhat) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r2 = 1 - ss_res / ss_tot if ss_tot else 0.0

    resid = y - yhat
    off_low = float(np.percentile(resid, 2))   # dəstək (alt zolaq)
    off_high = float(np.percentile(resid, 98))  # müqavimət (üst zolaq)

    def model_for(d: int) -> float:
        return float(10 ** (a + b * np.log10(d)))

    last_date = dates[-1]
    last_days = (last_date - GENESIS).days
    last_price = float(prices[-1])
    model_now = model_for(last_days)

    # Aylıq seyrəltmə (chart yükünü kiçik saxla).
    series_out = []
    step = max(1, len(dates) // 200)
    for i in range(0, len(dates), step):
        d = dates[i]
        dd = (d - GENESIS).days
        m = model_for(dd)
        series_out.append({
            "date": d.strftime("%Y-%m-%d"),
            "actual": round(float(prices[i]), 2),
            "model": round(m, 2),
            "low": round(m * 10 ** off_low, 2),
            "high": round(m * 10 ** off_high, 2),
        })

    # Gələcək proqnozlar.
    projections = []
    for years in (1, 2, 4):
        fd = last_date + timedelta(days=365 * years)
        dd = (fd - GENESIS).days
        m = model_for(dd)
        projections.append({
            "years": years,
            "date": fd.strftime("%Y-%m-%d"),
            "model": round(m, 2),
            "support": round(m * 10 ** off_low, 2),
            "resistance": round(m * 10 ** off_high, 2),
        })

    return {
        "a": round(a, 4),
        "b": round(b, 4),
        "r2": round(r2, 4),
        "genesis": GENESIS.strftime("%Y-%m-%d"),
        "lastDate": last_date.strftime("%Y-%m-%d"),
        "price": round(last_price, 2),
        "model": round(model_now, 2),
        "support": round(model_now * 10 ** off_low, 2),
        "resistance": round(model_now * 10 ** off_high, 2),
        "deviationPct": round((last_price / model_now - 1) * 100, 1),
        "projections": projections,
        "series": series_out,
    }


async def get_power_law() -> dict | None:
    """BTC power-law modeli (6 saat keş)."""
    now = time.time()
    if _cache["data"] and now - _cache["ts"] < _TTL:
        return _cache["data"]
    data = await asyncio.to_thread(_fit_sync)
    if data:
        _cache["data"] = data
        _cache["ts"] = now
    return _cache["data"]
