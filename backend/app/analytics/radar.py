"""Radar — gələcəkdə dəyərlənə biləcək aktivləri deterministik "fürsət balı" ilə sıralayır.

Hibrid model:
  - Deterministik bal (PULSUZ) sıralayır — momentum + sentiment + impact + anomaliya.
  - AI izahı yalnız istəklə (on-demand, `explain`) — bax `app.agents.radar_ai`.

Bal komponentləri (hər biri 0..100):
  momentum  — 24s dəyişim + ~7g sparkline trendi (müsbət hərəkət üstün).
  sentiment — aktivə aid son xəbərlərin orta sentimenti (DB, leksikon əsaslı).
  impact    — aid xəbərlərin maksimum impact_score-u (DB).
  anomaly   — robust z-score siqnalı varsa (qiymət/həcm sıçrayışı).

Mövcud infrastruktur reuse olunur — yeni qiymət-çəkmə YOXDUR:
  assets.get_overview() (qiymət+sparkline), anomaly.scan_all() (z-score),
  scoring (DB-də onsuz hesablanmış sentiment/impact), swr (keş).
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.analytics import anomaly, assets, swr
from app.db.session import AsyncSessionLocal
from app.models import News

# Tab → (reyestr tipləri, xəbər kateqoriyası)
TAB_CONFIG: dict[str, dict] = {
    "crypto": {"types": {"crypto"}, "news": "crypto"},
    "stock": {"types": {"stock", "index"}, "news": "us"},
    "commodity": {"types": {"commodity", "metal", "industrial"}, "news": "commodities"},
    "forex": {"types": {"forex"}, "news": "forex"},
}

# Aktiv → xəbər başlığında axtarılan əlavə adlar (label onsuz da daxildir).
_ALIASES: dict[str, list[str]] = {
    # Crypto
    "btc": ["bitcoin"], "eth": ["ethereum", "ether"], "sol": ["solana"],
    "xrp": ["ripple"],
    # İndekslər / səhmlər
    "spx": ["s&p 500", "s&p500", "sp500"], "ndx": ["nasdaq"],
    "dji": ["dow jones", "dow"], "rut": ["russell"], "vix": ["volatility index"],
    "nvda": ["nvidia"], "msft": ["microsoft"], "googl": ["google", "alphabet"],
    "amzn": ["amazon"], "meta": ["facebook"], "amd": ["amd"],
    "avgo": ["broadcom"], "tsm": ["tsmc", "taiwan semiconductor"],
    "pltr": ["palantir"], "arm": ["arm holdings"], "mu": ["micron"],
    "smci": ["supermicro", "super micro"], "orcl": ["oracle"],
    "crm": ["salesforce"], "now": ["servicenow"], "aic3": ["c3.ai"],
    # Forex
    "eurusd": ["eur/usd", "euro"], "gbpusd": ["gbp/usd", "pound", "sterling"],
    "usdjpy": ["usd/jpy", "yen"], "dxy": ["dollar index"],
    "audusd": ["aussie"], "usdcad": ["loonie"], "usdtry": ["lira"],
    # Əmtəə / metal
    "oil": ["wti", "crude"], "brent": ["brent"], "natgas": ["natural gas"],
    "gold": ["gold", "xau"], "silver": ["silver"], "platinum": ["platinum"],
    "palladium": ["palladium"], "copper": ["copper"], "uranium": ["uranium"],
    "lithium": ["lithium"], "aluminum": ["aluminium", "aluminum"],
}

_TOP_N = 24
_NEWS_DAYS = 14
_NEWS_LIMIT = 400
_TTL = 300.0  # 5 dəqiqə

# Tab başına SWR keş anbarı.
_caches: dict[str, dict] = {t: {"ts": 0.0, "data": []} for t in TAB_CONFIG}


def _clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, x))


def _matcher(key: str, label: str) -> re.Pattern:
    """Aktiv üçün başlıq matcher-i. Qısa alnum ticker-lər söz sərhədi ilə."""
    terms = list({label, *(_ALIASES.get(key, []))})
    parts: list[str] = []
    for t in terms:
        t = t.strip()
        if not t:
            continue
        esc = re.escape(t)
        if t.isalnum() and len(t) <= 4:
            parts.append(rf"\b{esc}\b")  # BTC, AMD, MU — yalnız tam söz
        else:
            parts.append(esc)  # "eur/usd", "s&p 500", çoxsözlü adlar
    if not parts:
        parts = [re.escape(label)]
    return re.compile("|".join(parts), re.IGNORECASE)


async def _recent_news(news_cat: str) -> list[dict]:
    """Kateqoriyanın son xəbərləri — başlıqda aktiv axtarmaq üçün (DB, yüngül)."""
    since = datetime.now(timezone.utc) - timedelta(days=_NEWS_DAYS)
    stmt = (
        select(News)
        .options(selectinload(News.source))
        .where(News.category == news_cat, News.published_at >= since)
        .order_by(News.published_at.desc().nullslast())
        .limit(_NEWS_LIMIT)
    )
    async with AsyncSessionLocal() as db:
        rows = (await db.scalars(stmt)).all()
    out: list[dict] = []
    for n in rows:
        tr = (n.translations or {}).get("az") or {}
        out.append({
            "id": str(n.id),
            "title": n.title,
            "titleAz": tr.get("title") or n.title_az,
            "url": n.url,
            "image": n.image_url,
            "impactScore": n.impact_score,
            "sentiment": n.sentiment,
            "publishedAt": n.published_at.isoformat() if n.published_at else None,
        })
    return out


def _score(chg_pct: float, spark: list[float], sent: float | None,
           impact: float | None, price_z: float | None,
           has_news: bool) -> tuple[float, dict]:
    """Komponentləri 0..100-ə normallaşdır, çəkili cəm → (bal, breakdown).

    Konviksiya: xəbərlə təsdiqlənməyən hərəkət aşağı etibarlıdır — saf momentum
    sıçrayan mikrokoinlər zirvəni tutmasın deyə bal yumşaldılır.
    """
    # Momentum — müsbət 24s hərəkət + ~7g sparkline trendi (yumşaq miqyas).
    mom = 50.0 + chg_pct * 2.5
    if spark and len(spark) >= 2 and spark[0]:
        mom += (spark[-1] - spark[0]) / spark[0] * 100.0 * 0.6
    mom = _clamp(mom)
    # Sentiment — xəbər yoxdursa neytral (50).
    sen = _clamp((sent + 1.0) / 2.0 * 100.0) if sent is not None else 50.0
    # Impact — aid xəbər intensivliyi (yoxdursa 0).
    imp = _clamp(impact) if impact is not None else 0.0
    # Anomaliya — z-score siqnalı (yoxdursa 0).
    ano = _clamp(abs(price_z) * 18.0) if price_z is not None else 0.0

    conviction = 1.0 if has_news else 0.82
    score = round(
        (0.30 * mom + 0.25 * sen + 0.30 * imp + 0.15 * ano) * conviction, 1
    )
    breakdown = {
        "momentum": round(mom, 1),
        "sentiment": round(sen, 1),
        "impact": round(imp, 1),
        "anomaly": round(ano, 1),
    }
    return score, breakdown


async def _compute(category: str) -> list[dict]:
    cfg = TAB_CONFIG[category]
    overview = await assets.get_overview()
    pool = [a for a in overview if a.get("type") in cfg["types"]]
    if not pool:
        return []

    anomalies = {a["key"]: a for a in await anomaly.scan_all()}
    news = await _recent_news(cfg["news"])

    items: list[dict] = []
    for a in pool:
        key, label = a["key"], a["label"]
        pat = _matcher(key, label)
        matched = [n for n in news if pat.search(n["title"] or "")]
        matched.sort(key=lambda n: (n["impactScore"] or 0), reverse=True)

        sents = [n["sentiment"] for n in matched if n["sentiment"] is not None]
        avg_sent = sum(sents) / len(sents) if sents else None
        max_impact = max(
            (n["impactScore"] for n in matched if n["impactScore"] is not None),
            default=None,
        )
        an = anomalies.get(key)
        score, breakdown = _score(
            a.get("chgPct", 0.0) or 0.0, a.get("spark") or [],
            avg_sent, max_impact, an["price_z"] if an else None,
            bool(matched),
        )
        items.append({
            "key": key, "label": label, "type": a["type"],
            "val": a.get("val"), "price": a.get("price"),
            "chg": a.get("chg"), "chgPct": a.get("chgPct"), "up": a.get("up"),
            "spark": a.get("spark") or [],
            "score": score, "breakdown": breakdown,
            "anomaly": an["severity"] if an else None,
            "news": matched[:2],
        })

    items.sort(key=lambda x: x["score"], reverse=True)
    return items[:_TOP_N]


async def get_radar(category: str, force: bool = False) -> list[dict]:
    """Kateqoriya üzrə fürsət sıralaması (SWR — köhnə dərhal, arxa planda yenilə)."""
    if category not in TAB_CONFIG:
        return []
    store = _caches[category]
    return await swr.get(store, _TTL, lambda: _compute(category), force=force) or []
