"""TranslationAgent + SummarizationAgent — GPT ilə xəbəri 4 dildə yenidən yazır.

Bir GPT çağırışı → 4 dil (az/en/ru/tr) üçün {title, body}.
body = AI-nın öz sözləri ilə qısa xülasə (məntiqi saxlayır, mənbə cümlələrini
dəyişə bilər). Birbaşa kopya YOX — müəllif hüququ + kontekst üçün.
"""
from __future__ import annotations

import json

from openai import AsyncOpenAI

from app.core.config import settings

LANGS = ("az", "en", "ru", "tr")
_LANG_NAMES = {
    "az": "Azerbaijani",
    "en": "English",
    "ru": "Russian",
    "tr": "Turkish",
}

_SYSTEM = (
    "You are a financial news editor for the NexusIQ terminal. "
    "You rewrite market news in your OWN words — never copy the source "
    "sentences verbatim. Keep every fact and the logical meaning intact, "
    "stay neutral and professional, no hype, no financial advice. "
    "Output ONLY valid JSON."
)


def _user_prompt(title: str, summary: str | None) -> str:
    langs = ", ".join(f"{c} ({_LANG_NAMES[c]})" for c in LANGS)
    return (
        "Rewrite the following market news item into a concise summary in your "
        f"own words, for EACH of these languages: {langs}.\n\n"
        "Rules:\n"
        "- body: 2-4 sentences, reworded (not copied), facts preserved.\n"
        "- title: a clear localized headline (not a copy).\n"
        "- Return JSON exactly like: "
        '{"az":{"title":"...","body":"..."},"en":{...},"ru":{...},"tr":{...}}\n\n'
        f"SOURCE TITLE: {title}\n"
        f"SOURCE SUMMARY: {summary or '(no summary provided)'}"
    )


async def translate_and_rewrite(
    title: str, summary: str | None, client: AsyncOpenAI | None = None
) -> dict[str, dict[str, str]] | None:
    """GPT-dən 4 dilli {lang: {title, body}} qaytarır. Xəta olarsa None."""
    from app.agents.llm import openai_client

    cli = client or openai_client()
    try:
        resp = await cli.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": _user_prompt(title, summary)},
            ],
            response_format={"type": "json_object"},
            temperature=0.4,
            max_tokens=900,
        )
        data = json.loads(resp.choices[0].message.content or "{}")
    except Exception:  # noqa: BLE001 — şəbəkə/parse xətası → emaldan keç
        return None

    # Validasiya: hər dil üçün title+body olmalıdır.
    out: dict[str, dict[str, str]] = {}
    for code in LANGS:
        node = data.get(code) or {}
        t, b = node.get("title"), node.get("body")
        if isinstance(t, str) and isinstance(b, str) and t.strip() and b.strip():
            out[code] = {"title": t.strip()[:500], "body": b.strip()}
    return out or None
