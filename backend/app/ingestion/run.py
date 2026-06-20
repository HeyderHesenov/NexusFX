"""Xəbər ingestion-u işə salır: çək → dedup → bazaya yaz.

İstifadə (backend/ qovluğundan):
    python -m app.ingestion.run
"""
from __future__ import annotations

import asyncio

from app.db.session import AsyncSessionLocal, engine
from app.ingestion.rss_collector import collect_all
from app.services.news_service import store_news


async def ingest_once() -> dict[str, int]:
    """Bir ingestion dövrü. Sayğacları qaytarır."""
    items = await collect_all()
    async with AsyncSessionLocal() as session:
        return await store_news(session, items)


async def main() -> None:
    stats = await ingest_once()
    print(
        f"✅ Ingestion bitdi — çəkilən: {stats['fetched']}, "
        f"yeni: {stats['added']}, dublikat: {stats['skipped']}"
    )
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
