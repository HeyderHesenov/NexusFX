"""ForecastAgent — xəbərin bazar instrumentlərinə təsirini GPT ilə proqnozlaşdırır.

Bir GPT çağırışı → tək dildə {summary, pairs:[{sym, impact, reason}]}.
Forex xəbəri → forex cütləri; kripto → BTC/ETH və s.; ABŞ → indekslər + USD.
On-demand çağırılır, News.forecast[lang] altında keşlənir.
"""
from __future__ import annotations

import json

from openai import AsyncOpenAI

from app.core.config import settings

_LANG_NAMES = {
    "az": "Azerbaijani",
    "en": "English",
    "ru": "Russian",
    "tr": "Turkish",
}
_IMPACTS = {"up", "down", "mixed", "neutral"}

_FOCUS = {
    "forex": "major forex pairs (EUR/USD, GBP/USD, USD/JPY, DXY, etc.)",
    "us": "US indices and USD pairs (S&P 500, NASDAQ, DXY, EUR/USD)",
    "crypto": "major crypto assets (BTC, ETH) and DXY",
}

_SYSTEM = (
    "You are a markets analyst for the NexusIQ terminal. Given a news item, "
    "you assess how it could plausibly affect tradable instruments. "
    "Be specific and educational, stay neutral, give NO financial advice. "
    "Never invent facts not implied by the news. Output ONLY valid JSON."
)


def _prompt(title: str, summary: str | None, category: str, lang: str) -> str:
    focus = _FOCUS.get(category, _FOCUS["forex"])
    lname = _LANG_NAMES.get(lang, "English")
    return (
        f"Write entirely in {lname}.\n"
        f"Assess how this news could affect {focus}.\n"
        "Pick the 3-5 MOST relevant instruments. For each give a likely "
        "directional bias and a one-sentence reason grounded in the news.\n\n"
        "Return JSON exactly like:\n"
        '{"summary":"one short sentence overview",'
        '"pairs":[{"sym":"EUR/USD","impact":"up","reason":"..."}]}\n'
        "impact must be one of: up, down, mixed, neutral.\n\n"
        f"NEWS TITLE: {title}\n"
        f"NEWS SUMMARY: {summary or '(no summary)'}"
    )


async def forecast_impact(
    title: str,
    summary: str | None,
    category: str,
    lang: str,
    client: AsyncOpenAI | None = None,
) -> dict | None:
    """{summary, pairs:[{sym, impact, reason}]} qaytarır. Xəta → None."""
    from app.agents.llm import openai_client

    cli = client or openai_client()
    try:
        resp = await cli.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": _prompt(title, summary, category, lang)},
            ],
            response_format={"type": "json_object"},
            temperature=0.5,
            max_tokens=600,
        )
        data = json.loads(resp.choices[0].message.content or "{}")
    except Exception:  # noqa: BLE001
        return None

    pairs = []
    for p in data.get("pairs") or []:
        sym, impact, reason = p.get("sym"), p.get("impact"), p.get("reason")
        if not (isinstance(sym, str) and isinstance(reason, str)):
            continue
        impact = impact if impact in _IMPACTS else "neutral"
        pairs.append(
            {"sym": sym.strip()[:16], "impact": impact, "reason": reason.strip()}
        )
    if not pairs:
        return None
    summ = data.get("summary")
    return {
        "summary": summ.strip() if isinstance(summ, str) else "",
        "pairs": pairs[:5],
    }
