"""Transport layer for link CRUD. Thin: validate, delegate, shape response."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models import Link
from app.rate_limit import RateLimiter
from app.schemas import LinkCreate, LinkOut
from app.services import shortener

settings = get_settings()

_create_limit = RateLimiter(
    limit=settings.rate_limit_create_per_minute, window_seconds=60, scope="create"
)

router = APIRouter(prefix="/api/links", tags=["links"])


def _to_out(link: Link) -> LinkOut:
    return LinkOut(
        id=link.id,
        code=link.code,
        long_url=link.long_url,
        short_url=shortener.short_url_for(link.code),
        created_at=link.created_at,
    )


@router.post(
    "",
    response_model=LinkOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(_create_limit)],
)
async def create_link(payload: LinkCreate, db: AsyncSession = Depends(get_db)) -> LinkOut:
    try:
        link = await shortener.create_link(db, str(payload.long_url), payload.custom_code)
    except ValueError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    return _to_out(link)


@router.get("", response_model=list[LinkOut])
async def list_links(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[LinkOut]:
    """List links newest-first. Paginated so the endpoint stays bounded as data grows."""
    rows = (
        await db.execute(
            select(Link).order_by(Link.created_at.desc()).limit(limit).offset(offset)
        )
    ).scalars().all()
    return [_to_out(link) for link in rows]
