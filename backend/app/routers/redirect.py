"""The public redirect endpoint: GET /{code} -> 307 to the original URL.

Records a click event as a side effect. Note this router has no /api prefix
because short links live at the root path.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import analytics, shortener

router = APIRouter(tags=["redirect"])


@router.get("/{code}")
async def redirect(
    code: str, request: Request, db: AsyncSession = Depends(get_db)
) -> RedirectResponse:
    link = await shortener.resolve_code(db, code)
    if link is None:
        raise HTTPException(404, "Short link not found")

    # Best-effort analytics; a logging failure must not break the redirect.
    try:
        await analytics.record_click(
            db,
            link_id=link.id,
            referrer=request.headers.get("referer"),
            country=request.headers.get("cf-ipcountry"),  # e.g. behind Cloudflare
            user_agent=request.headers.get("user-agent", "")[:512],
        )
    except Exception:  # noqa: BLE001 - deliberately non-fatal
        pass

    return RedirectResponse(url=link.long_url, status_code=307)
