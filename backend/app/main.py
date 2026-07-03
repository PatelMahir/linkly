"""FastAPI application entrypoint.

Wires middleware and routers. The redirect router is registered LAST so its
catch-all `/{code}` route doesn't shadow the `/api/*` and docs routes.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


@app.get("/health", tags=["ops"])
async def health() -> dict[str, str]:
    """Liveness probe for load balancers / k8s."""
    return {"status": "ok"}


app.include_router(links.router)
app.include_router(analytics.router)
app.include_router(redirect.router)  # keep last: catch-all /{code}
