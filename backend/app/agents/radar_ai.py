"""RadarAI — kəşf edilmiş aktivin niyə perspektivli olduğunu GPT ilə izah edir.

On-demand (yalnız "AI izah" düyməsi) — API qənaəti. Tək GPT çağırışı → seçilmiş
dildə qısa, neytral izah (MC, gəlir/tema, momentum əsasında).
Nəticə (key, lang) üzrə yaddaşda keşlənir (1 saat).
"""
from __future__ import annotations

import time

from app.core.config import settings

_LANG_NAMES = {"az": "Azerbaijani", "en": "English", "ru": "Russian", "tr": "Turkish"}

_SYSTEM = (
    "You are a markets analyst for the NexusIQ terminal. You explain why a small, "
    "under-the-radar asset (micro-cap crypto or small-cap stock) currently stands "
    "out as a potential opportunity. 2-3 short sentences. Stay neutral and "
    "educational, give NO financial advice, invent no facts beyond the data given."
)

_TTL = 3600.0
_cache: dict[tuple[str, str], tuple[float, str]] = {}


def _prompt(item: dict, lang: str) -> str:
    lname = _LANG_NAMES.get(lang, "English")
    typ = item.get("type")
    lines = [
        f"Write entirely in {lname}. 2-3 short sentences, no preamble.",
        f"ASSET: {item.get('name') or item.get('label')} ({item.get('label')})",
        f"TYPE: {typ}",
        f"MARKET CAP: {item.get('mcapFmt')}",
        f"OPPORTUNITY SCORE: {item.get('score')}/100",
        f"24H CHANGE: {item.get('chg')}",
    ]
    if typ == "crypto":
        lines.append(f"CATEGORY: {item.get('category')}")
        lines.append(f"30-DAY PROTOCOL REVENUE: {item.get('revenueFmt')}")
        lines.append(
            "Explain why a revenue-generating micro-cap protocol at this size "
            "could be an early opportunity (real usage, fees, growth)."
        )
    else:
        lines.append(f"THEME: {item.get('theme')}")
        lines.append(
            "Explain the thesis: how this theme (e.g. AI demand → energy/chips) "
            "could drive this small-cap, and what the price trend suggests."
        )
    return "\n".join(lines)


async def explain(item: dict, lang: str) -> str | None:
    """Kəşf item-i üçün qısa AI izahı (keşli). Xəta/açar yoxdursa None."""
    from app.agents.llm import has_openai, openai_client

    lang = lang if lang in _LANG_NAMES else "az"
    ck = (item.get("key", ""), lang)
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
                {"role": "user", "content": _prompt(item, lang)},
            ],
            temperature=0.5,
            max_tokens=240,
        )
        text = (resp.choices[0].message.content or "").strip()
    except Exception:  # noqa: BLE001
        return None
    if text:
        _cache[ck] = (time.time(), text)
    return text or None
