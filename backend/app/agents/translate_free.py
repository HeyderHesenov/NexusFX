"""Pulsuz maşın tərcüməsi — xəbərləri 4 dilə SADİQ tərcümə edir.

Google-ın açarsız (gtx) tərcümə endpoint-i, httpx ilə. API xərci YOXDUR.
AI-dən fərqli olaraq mətni yenidən YAZMIR — orijinalı olduğu kimi tərcümə edir
(istifadəçi tələbi: "xəbərin texti dəyişilməsin, sadəcə dilə uyğunlaşsın").

İstifadə (backend/ qovluğundan):
    python -m app.agents.translate_free        # 12 xəbər backfill
    python -m app.agents.translate_free 100    # 100 xəbər
"""
from __future__ import annotations

import asyncio
import logging
import sys

import httpx
from sqlalchemy import or_, select

from app.core.config import settings
from app.db.session import AsyncSessionLocal, engine
from app.models import News

logger = logging.getLogger("nexusiq.translate")

LANGS = ("az", "en", "ru", "tr")
_URL = "https://translate.googleapis.com/translate_a/single"
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; NexusIQ/1.0)"}
_MAX_CHARS = 4800  # endpoint limiti
_RETRIES = 3       # gtx rate-limit/timeout üçün cəhd sayı
_BACKOFF = 0.5     # baza gecikmə (saniyə) — eksponensial: 0.5, 1.0, 2.0


class TranslationError(Exception):
    """gtx endpoint-i bütün cəhdlərdən sonra uğursuz oldu.

    KRİTİK: səssiz orijinalı qaytarmaq əvəzinə qaldırılır ki, uğursuzluq
    İngiliscə mətni `title_az`-a daimi kilidləməsin — çağıran retry edə bilsin.
    """


async def _translate_one(client: httpx.AsyncClient, text: str, target: str) -> str:
    """Bir mətni hədəf dilə tərcümə. Bütün cəhdlər uğursuzsa TranslationError."""
    if not text:
        return text
    last_exc: Exception | None = None
    for attempt in range(_RETRIES):
        try:
            r = await client.get(
                _URL,
                params={
                    "client": "gtx",
                    "sl": "auto",
                    "tl": target,
                    "dt": "t",
                    "q": text[:_MAX_CHARS],
                },
            )
            r.raise_for_status()
            data = r.json()
            # Cavab: [[["tərcümə","orijinal",...], ...], ...]
            out = "".join(seg[0] for seg in data[0] if seg and seg[0])
            if out:
                return out
            last_exc = ValueError("boş tərcümə cavabı")
        except (httpx.HTTPError, ValueError, IndexError, KeyError, TypeError) as exc:
            last_exc = exc
        if attempt < _RETRIES - 1:
            await asyncio.sleep(_BACKOFF * (2**attempt))
    raise TranslationError(f"{target}: {last_exc}")


async def translate_news(
    title: str, summary: str | None, source_lang: str = "en"
) -> tuple[dict[str, dict[str, str]], bool]:
    """title + summary → ({lang: {title, body}}, complete).

    Mənbə dil tərcümə olunmur. `complete=True` yalnız BÜTÜN hədəf dillər uğurla
    tərcümə olunduqda — qismən uğurda alınan dillər saxlanır, amma complete=False
    (çağıran `title_az`-ı doldurmur → növbəti dövrdə retry).
    """
    out: dict[str, dict[str, str]] = {}
    complete = True
    async with httpx.AsyncClient(timeout=12.0, headers=_HEADERS) as client:
        for lang in LANGS:
            if lang == source_lang:
                out[lang] = {"title": title, "body": summary or ""}
                continue
            try:
                t = await _translate_one(client, title, lang)
                b = await _translate_one(client, summary or "", lang)
                out[lang] = {"title": t, "body": b}
            except TranslationError as exc:
                complete = False
                logger.warning("Tərcümə uğursuz (%s): %s", lang, exc)
    return out, complete


async def translate_pending(limit: int | None = None) -> dict[str, int]:
    """Tərcüməsiz xəbərləri pulsuz tərcümə edir.

    `title_az IS NULL` həm translations=NULL, həm də boş translations={} olan
    xəbərləri tutur (köhnə ingestion bəzi sətirləri boş dict ilə yaratmışdı).
    """
    limit = limit or settings.free_translate_batch
    async with AsyncSessionLocal() as session:
        rows = (
            await session.scalars(
                select(News)
                .where(News.title_az.is_(None))
                .order_by(News.published_at.desc().nullslast())
                .limit(limit)
            )
        ).all()
        pending = [(n.id, n.title, n.summary, n.language) for n in rows]

    if not pending:
        return {"pending": 0, "translated": 0}

    translated = 0
    ids = [row_id for row_id, _, _, _ in pending]
    async with AsyncSessionLocal() as session:
        by_id = {
            n.id: n
            for n in (
                await session.scalars(select(News).where(News.id.in_(ids)))
            ).all()
        }
        for row_id, title, summary, lang in pending:
            news = by_id.get(row_id)
            if news is None:
                continue
            tr, complete = await translate_news(title, summary, source_lang=lang or "en")
            # Alınan dilləri həmişə saxla (ru/tr itməsin). title_az isə yalnız
            # tam uğurda — uğursuzluqda NULL qalır → növbəti dövrdə avtomatik retry.
            news.translations = tr
            if complete:
                az = tr.get("az") or {}
                news.title_az = az.get("title")
                news.summary_az = az.get("body")
                translated += 1
        await session.commit()

    return {"pending": len(pending), "translated": translated}


async def translate_all_pending(max_loops: int = 50) -> dict[str, int]:
    """Bütün tərcüməsiz xəbərləri drenaj edir (batch-batch, hamısı bitənə qədər).

    `translate_pending` tək batch (free_translate_batch) tutur; bu isə backlog
    tamamilə bitənə qədər təkrarlayır. Beləcə bir ingestion dövründə nə qədər yeni
    xəbər gəlsə də, hamısı dərhal tərcümə olunur — UI heç vaxt tərcüməsiz qalmır.
    `max_loops` patoloji halda sonsuz dövrəni önləyən təhlükəsizlik həddidir.
    """
    if not settings.free_translate_enabled:
        return {"translated": 0}
    total = 0
    for _ in range(max_loops):
        stats = await translate_pending()
        n = stats.get("translated", 0)
        total += n
        if n == 0:
            break
    return {"translated": total}


async def retranslate_stale(limit: int = 100) -> dict[str, int]:
    """Keçmiş səssiz uğursuzluqdan İngiliscə "kilidlənmiş" xəbərləri bərpa edir.

    Köhnə kod gtx xətasında İngiliscəni `title_az`-a yazıb — element artıq NULL
    deyil deyə bir daha retry olunmurdu. Burada `az` başlığı orijinala bərabər
    (mənbə dili az olmayan) sətirləri tapıb `title_az`-ı NULL-a qaytarır ki, normal
    `translate_pending` axını onları yenidən tərcümə etsin. `limit` ilə məhdud —
    nadir həqiqətən-identik başlıqlar üçün sonsuz iş yaratmasın.
    """
    if not settings.free_translate_enabled:
        return {"reset": 0, "translated": 0}
    async with AsyncSessionLocal() as session:
        rows = (
            await session.scalars(
                select(News)
                .where(
                    News.title_az.is_not(None),
                    News.title_az == News.title,
                    or_(News.language.is_(None), News.language != "az"),
                )
                .order_by(News.published_at.desc().nullslast())
                .limit(limit)
            )
        ).all()
        reset = 0
        for n in rows:
            n.title_az = None
            n.summary_az = None
            reset += 1
        await session.commit()

    if reset:
        logger.info("retranslate_stale — %s kilidlənmiş xəbər sıfırlandı", reset)
        translated = (await translate_all_pending()).get("translated", 0)
        return {"reset": reset, "translated": translated}
    return {"reset": 0, "translated": 0}


async def main() -> None:
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else settings.free_translate_batch
    print(f"⏳ {limit} xəbər pulsuz tərcümə olunur (Google free)…")
    stats = await translate_pending(limit)
    print(f"✅ Bitdi — cəhd: {stats['pending']}, tərcümə: {stats['translated']}")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
