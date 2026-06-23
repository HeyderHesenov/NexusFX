"""RadarAI — bir aktivin niyə radarda olduğunu GPT ilə qısaca izah edir.

On-demand (yalnız istifadəçi "AI izah" düyməsinə basanda) — API qənaəti.
Tək GPT çağırışı → seçilmiş dildə qısa, neytral, təhsil xarakterli izah.
Nəticə (key, lang) üzrə yaddaşda keşlənir (1 saat) — təkrar xərc yox.
"""
from __future__ import annotations

import time

from app.core.config import settings

_LANG_NAMES = {"az": "Azerbaijani", "en": "English", "ru": "Russian", "tr": "Turkish"}

_SYSTEM = (
    "You are a markets analyst for the NexusIQ terminal. Given an asset and its "
    "opportunity-score breakdown, explain in 2-3 short sentences why it currently "
    "stands out. Stay neutral, educational, give NO financial advice and invent no facts."
)

_TTL = 3600.0  # 1 saat
_cache: dict[tuple[str, str], tuple[float, str]] = {}


def _prompt(label: str, category: str, score: float,
            breakdown: dict, news_titles: list[str], lang: str) -> str:
    lname = _LANG_NAMES.get(lang, "English")
    b = breakdown or {}
    heads = "\n".join(f"- {t}" for t in news_titles[:3]) or "(no recent headlines)"
    return (
        f"Write entirely in {lname}. 2-3 short sentences, no preamble.\n"
        f"ASSET: {label} ({category})\n"
        f"OPPORTUNITY SCORE: {score}/100\n"
        f"COMPONENTS (0-100): momentum={b.get('momentum')}, "
        f"sentiment={b.get('sentiment')}, impact={b.get('impact')}, "
        f"anomaly={b.get('anomaly')}\n"
        f"RECENT HEADLINES:\n{heads}\n\n"
        "Explain what is driving the score (e.g. strong momentum, positive news "
        "sentiment, a volatility spike) in plain terms."
    )


async def explain(key: str, label: str, category: str, score: float,
                  breakdown: dict, news_titles: list[str], lang: str) -> str | None:
    """Aktiv üçün qısa AI izahı (keşli). Xəta/açar yoxdursa None."""
    from app.agents.llm import has_openai, openai_client

    lang = lang if lang in _LANG_NAMES else "az"
    ck = (key, lang)
    hit = _cache.get(ck)
    if hit and time.time() - hit[0] < _TTL:
        return hit[1]
    if not has_openai():
        return None
    try:
        resp = await openai_client().chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": _prompt(
                    label, category, score, breakdown, news_titles, lang)},
            ],
            temperature=0.5,
            max_tokens=220,
        )
        text = (resp.choices[0].message.content or "").strip()
    except Exception:  # noqa: BLE001
        return None
    if text:
        _cache[ck] = (time.time(), text)
    return text or None
