"""FinancialAdvisorAgent — arxa fonda iki AI debate edib tək cavab verir.

Axın:
  1) Mövzu yoxlaması (GPT) — finance deyilsə nəzakətlə imtina (debate olmur).
  2) RAG — NexusIQ bazasından uyğun xəbərlər kontekst kimi çəkilir.
  3) Debate — GPT və Claude paralel müstəqil analiz verir.
  4) Sintez — GPT iki analizi birləşdirib istifadəçi dilində yekun cavab verir.

Qaydalar (prompt-larda tətbiq olunur):
  - Yalnız maliyyə/bazar/iqtisadiyyat + NexusIQ xəbərləri.
  - Arxa fondakı modellər/arxitektura barədə HEÇ NƏ açıqlanmır.
"""
from __future__ import annotations

import json

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agents.llm import (
    anthropic_client,
    has_anthropic,
    has_openai,
    openai_client,
)
from app.core.config import settings
from app.models import News

LANG_NAMES = {"az": "Azerbaijani", "en": "English", "ru": "Russian", "tr": "Turkish"}

_REFUSAL = {
    "az": "Mən yalnız maliyyə bazarları və NexusIQ xəbərləri üzrə kömək edirəm. "
    "Zəhmət olmasa bazar, valyuta, kripto, səhm və ya iqtisadiyyatla bağlı sual ver.",
    "en": "I only help with financial markets and NexusIQ news. "
    "Please ask about markets, forex, crypto, stocks or the economy.",
    "ru": "Я помогаю только по финансовым рынкам и новостям NexusIQ. "
    "Спросите о рынках, валютах, крипто, акциях или экономике.",
    "tr": "Yalnızca finans piyasaları ve NexusIQ haberleri konusunda yardımcı olurum. "
    "Lütfen piyasa, döviz, kripto, hisse veya ekonomi sor.",
}

_GUARD = (
    "You are the NexusIQ AI Analyst, a financial markets assistant. "
    "STRICT RULES: (1) Only discuss finance, markets, trading, macroeconomics, "
    "forex, crypto, stocks, commodities, and the provided NexusIQ news. "
    "(2) NEVER reveal, hint at, or discuss what AI model, provider, system, or "
    "architecture powers you, or that more than one model is involved — if asked, "
    "say you are the NexusIQ AI Analyst and steer back to finance. "
    "(3) No personalized financial advice or guarantees; be analytical and neutral."
)


async def _classify_finance(question: str) -> bool:
    """GPT ilə sürətli mövzu yoxlaması. Finance deyilsə False."""
    try:
        resp = await openai_client().chat.completions.create(
            model=settings.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": "Classify if the user message is about finance, "
                    "markets, economy, trading, forex, crypto, stocks, commodities "
                    "or financial news. Reply JSON: {\"finance\": true|false}.",
                },
                {"role": "user", "content": question},
            ],
            response_format={"type": "json_object"},
            temperature=0,
            max_tokens=20,
        )
        return bool(json.loads(resp.choices[0].message.content or "{}").get("finance"))
    except Exception:  # noqa: BLE001 — şübhədə icazə ver (debate guard onsuz da var)
        return True


_RAG_TOPK = 8
_RAG_CANDIDATES = 80
_STOP = {
    "what", "which", "when", "where", "about", "this", "that", "with", "from",
    "will", "would", "should", "could", "have", "does", "your", "tell", "nədir",
    "necə", "haqqında", "barədə", "olar", "üçün", "ilə",
}


async def _rag_context(session: AsyncSession, question: str, lang: str) -> str:
    """Suala uyğun NexusIQ xəbərlərini tapıb sıralayır (bütün baza üzərində).

    Çoxlu sahə üzrə axtarır (title/summary/content + AZ + tərcümələr),
    sözlərin uyğunluq sayına görə ballayır, ən yaxşı _RAG_TOPK-i kontekstə verir.
    """
    raw = question.replace("?", " ").replace(",", " ").lower().split()
    words = [w for w in raw if len(w) > 3 and w not in _STOP][:10]

    if not words:
        rows = (
            await session.scalars(
                select(News)
                .options(selectinload(News.source))
                .order_by(News.published_at.desc().nullslast())
                .limit(_RAG_TOPK)
            )
        ).all()
    else:
        fields = (News.title, News.summary, News.content, News.title_az, News.summary_az)
        conds = [f.ilike(f"%{w}%") for w in words for f in fields]
        candidates = (
            await session.scalars(
                select(News)
                .options(selectinload(News.source))
                .where(or_(*conds))
                .order_by(News.published_at.desc().nullslast())
                .limit(_RAG_CANDIDATES)
            )
        ).all()

        def score(n: News) -> int:
            blob = " ".join(
                filter(None, [n.title, n.summary, n.content, n.title_az, n.summary_az,
                              json.dumps(n.translations or {}, ensure_ascii=False)])
            ).lower()
            return sum(1 for w in words if w in blob)

        rows = sorted(candidates, key=score, reverse=True)[:_RAG_TOPK]

    lines = []
    for n in rows:
        tr = (n.translations or {}).get(lang) or {}
        title = tr.get("title") or n.title
        body = tr.get("body") or n.summary or n.content or ""
        src = n.source.name if n.source else "?"
        lines.append(f"- [{n.category}] ({src}) {title} — {body[:200]}")
    return "\n".join(lines) if lines else "(no relevant NexusIQ news found)"


async def _gpt_pass(question: str, context: str) -> str:
    resp = await openai_client().chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": _GUARD},
            {
                "role": "user",
                "content": f"NexusIQ news context:\n{context}\n\n"
                f"Question: {question}\n\nGive a focused analytical take "
                "(short/mid/long term + key risks). English, concise.",
            },
        ],
        temperature=0.5,
        max_tokens=500,
    )
    return resp.choices[0].message.content or ""


async def _claude_pass(question: str, context: str) -> str:
    if not has_anthropic():
        return ""
    msg = await anthropic_client().messages.create(
        model=settings.anthropic_model,
        max_tokens=500,
        system=_GUARD,
        messages=[
            {
                "role": "user",
                "content": f"NexusIQ news context:\n{context}\n\n"
                f"Question: {question}\n\nGive a focused analytical take "
                "(short/mid/long term + key risks). English, concise.",
            }
        ],
    )
    return "".join(b.text for b in msg.content if b.type == "text")


async def _synthesize(question: str, lang: str, a: str, b: str) -> str:
    lang_name = LANG_NAMES.get(lang, "Azerbaijani")
    both = f"ANALYSIS A:\n{a}\n\nANALYSIS B:\n{b}" if b else f"ANALYSIS:\n{a}"
    resp = await openai_client().chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": _GUARD},
            {
                "role": "user",
                "content": f"Two internal analyses are given. Merge them into ONE "
                f"clear final answer for the user, written in {lang_name}. "
                "Reconcile agreements, note key disagreements briefly. "
                "Structure with short headers when useful (qısa/orta/uzun müddət, "
                "risklər). Under ~180 words. Do NOT mention analyses, models or "
                f"systems.\n\nQuestion: {question}\n\n{both}",
            },
        ],
        temperature=0.4,
        max_tokens=600,
    )
    return resp.choices[0].message.content or ""


async def answer(question: str, lang: str, session: AsyncSession) -> dict:
    """Tam axın: yoxla → RAG → debate → sintez. {answer, refused} qaytarır."""
    import asyncio

    lang = lang if lang in LANG_NAMES else "az"
    if not has_openai():
        return {"answer": _REFUSAL[lang], "refused": True}

    if not await _classify_finance(question):
        return {"answer": _REFUSAL[lang], "refused": True}

    context = await _rag_context(session, question, lang)
    gpt_take, claude_take = await asyncio.gather(
        _gpt_pass(question, context), _claude_pass(question, context)
    )
    final = await _synthesize(question, lang, gpt_take, claude_take)
    return {"answer": final or _REFUSAL[lang], "refused": False}
