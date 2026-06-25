"""Yüngül in-memory rate limiter — bahalı endpoint-lər üçün (per-IP sürüşən pəncərə).

Tək-proses demo üçün kifayətdir; xarici asılılıq yoxdur. Çoxlu instans/prod üçün
Redis-əsaslı limiter lazım olar.
"""
from __future__ import annotations

import time
from collections import defaultdict

from fastapi import HTTPException, Request, status

# bucket adı → (ip → [son sorğu vaxtları])
_HITS: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))


def _client_ip(request: Request) -> str:
    """Proksinin arxasındakı real IP (X-Forwarded-For), yoxdursa socket IP."""
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def rate_limit(name: str, limit: int, window: float = 60.0):
    """FastAPI dependency — `name` bucket-i üçün per-IP `limit`/`window`. Aşılırsa 429."""

    async def _dep(request: Request) -> None:
        ip = _client_ip(request)
        now = time.monotonic()
        hits = _HITS[name][ip]
        # pəncərədən kənar köhnə vaxtları at
        cutoff = now - window
        hits[:] = [t for t in hits if t > cutoff]
        if len(hits) >= limit:
            retry = int(window - (now - hits[0])) + 1
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Çox sayda sorğu — bir azdan yenidən cəhd et.",
                headers={"Retry-After": str(max(1, retry))},
            )
        hits.append(now)

    return _dep
