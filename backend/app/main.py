"""NexusIQ FastAPI giriş nöqtəsi."""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.scheduler import shutdown_scheduler, start_scheduler, startup_catchup

logger = logging.getLogger("nexusiq.startup")

_IS_DEV = settings.environment == "development"
_MAX_BODY = 256 * 1024  # 256 KB — sorğu gövdəsi limiti (DoS/yaddaş qoruması)


class _BodySizeLimit(BaseHTTPMiddleware):
    """Content-Length həddi aşan POST/PUT sorğularını 413 ilə rədd edir."""

    async def dispatch(self, request: Request, call_next):
        if request.method in ("POST", "PUT", "PATCH"):
            cl = request.headers.get("content-length")
            if cl and cl.isdigit() and int(cl) > _MAX_BODY:
                return JSONResponse(
                    {"detail": "Sorğu gövdəsi çox böyükdür."}, status_code=413
                )
        return await call_next(request)


async def _prewarm() -> None:
    """Ağır analitik keşləri arxa planda isidir — ilk istifadəçi gözləməsin."""
    from app.analytics import anomaly, assets, correlation, market, radar

    tasks = {
        "market": market.get_quotes(),
        "metals": market.get_metals(),
        "commodities": market.get_commodities(),
        "overview": assets.get_overview(),
        "correlation": correlation.get_matrix(90),
        "anomaly": anomaly.scan_all(),
        "radar_crypto": radar.get_radar("crypto"),
        "radar_stock": radar.get_radar("stock"),
        "radar_commodity": radar.get_radar("commodity"),
    }
    results = await asyncio.gather(*tasks.values(), return_exceptions=True)
    warmed = [n for n, r in zip(tasks, results) if not isinstance(r, Exception)]
    logger.info("Prewarm tamamlandı: %s", ", ".join(warmed) or "yox")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Başlanğıc / bağlanış hadisələri — planlayıcı + keş istiləşməsi."""
    # startup
    start_scheduler()
    asyncio.create_task(_prewarm())  # blok etmədən keşləri isidir
    asyncio.create_task(startup_catchup())  # tərcüməsiz backlog-u dərhal tut
    yield
    # shutdown
    shutdown_scheduler()


def create_app() -> FastAPI:
    # Swagger/OpenAPI yalnız development-də açıq (prod-da API səthi gizli).
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Financial Intelligence Platform — AI Analyst Terminal",
        lifespan=lifespan,
        docs_url="/docs" if _IS_DEV else None,
        redoc_url=None,
        openapi_url="/openapi.json" if _IS_DEV else None,
    )

    app.add_middleware(_BodySizeLimit)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=False,  # frontend cookie/credential göndərmir
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type"],
    )

    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.get("/")
    async def root() -> dict:
        info = {"app": settings.app_name, "api": settings.api_v1_prefix}
        if _IS_DEV:
            info["docs"] = "/docs"
        return info

    return app


app = create_app()
