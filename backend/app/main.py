"""FastAPI application entrypoint.

Wires middleware and routers. The redirect router is registered LAST so its
catch-all `/{code}` route doesn't shadow the `/api/*` and docs routes.
"""

import time
from collections.abc import Awaitable, Callable
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app import cache, database
from app.config import get_settings
from app.routers import analytics, links, redirect

settings = get_settings()

app = FastAPI(
    title="Linkly API",
    version="0.1.0",
    description="URL shortener with click analytics.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def observability(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Attach a request id and server-timing header for tracing/observability.

    Honors an inbound X-Request-ID so a trace can be correlated across services.
    """
    request_id = request.headers.get("x-request-id") or uuid4().hex
    start = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-Ms"] = f"{(time.perf_counter() - start) * 1000:.1f}"
    return response


@app.get("/health", tags=["ops"])
async def health() -> dict[str, str]:
    """Liveness probe: process is up. Cheap and dependency-free."""
    return {"status": "ok"}


@app.get("/ready", tags=["ops"])
async def ready() -> Response:
    """Readiness probe: verify we can reach Postgres and Redis.

    Load balancers / k8s use this to decide whether to route traffic — key for
    rolling, blue/green, and canary deploys where a pod may be up but not ready.
    """
    checks: dict[str, str] = {}
    healthy = True

    try:
        async with database.engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:  # noqa: BLE001 - report, don't crash the probe
        checks["database"] = "error"
        healthy = False

    try:
        await cache.redis.ping()
        checks["redis"] = "ok"
    except Exception:  # noqa: BLE001
        checks["redis"] = "error"
        healthy = False

    status_code = 200 if healthy else 503
    return JSONResponse(
        status_code=status_code,
        content={"status": "ok" if healthy else "degraded", "checks": checks},
    )


app.include_router(links.router)
app.include_router(analytics.router)
app.include_router(redirect.router)  # keep last: catch-all /{code}
