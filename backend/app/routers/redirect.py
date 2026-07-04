"""The public redirect endpoint: GET /{code} -> 307 to the original URL.

Scaling notes:
  * On a cache hit the destination is served without touching Postgres.
  * The click is published to RabbitMQ (via a BackgroundTask) and persisted by a
    separate worker, so the redirect is never blocked by a DB write.
  * The endpoint is rate-limited per client IP.

This router has no /api prefix because short links live at the root path.
"""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.rate_limit import RateLimiter
from app.services import analytics, shortener

settings = get_settings()

_redirect_limit = RateLimiter(
    limit=settings.rate_limit_redirect_per_minute, window_seconds=60, scope="redirect"
)

router = APIRouter(tags=["redirect"])


@router.get("/{code}", dependencies=[Depends(_redirect_limit)])
async def redirect(
    code: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    link = await shortener.resolve_code(db, code)
    if link is None:
        raise HTTPException(404, "Short link not found")

    # Publish analytics off the hot path; the redirect returns without waiting.
    background_tasks.add_task(
        analytics.enqueue_click,
        link_id=link.id,
        referrer=request.headers.get("referer"),
        country=request.headers.get("cf-ipcountry"),  # e.g. behind Cloudflare
        user_agent=request.headers.get("user-agent", "")[:512],
    )

    return RedirectResponse(url=link.long_url, status_code=307)
