"""Transport layer for link CRUD. Thin: validate, delegate, shape response."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Link
from app.schemas import LinkCreate, LinkOut
from app.services import shortener

router = APIRouter(prefix="/api/links", tags=["links"])


def _to_out(link: Link) -> LinkOut:
    return LinkOut(
        id=link.id,
        code=link.code,
        long_url=link.long_url,
        short_url=shortener.short_url_for(link.code),
        created_at=link.created_at,
    )


@router.post("", response_model=LinkOut, status_code=status.HTTP_201_CREATED)
async def create_link(payload: LinkCreate, db: AsyncSession = Depends(get_db)) -> LinkOut:
    try:
        link = await shortener.create_link(db, str(payload.long_url), payload.custom_code)
    except ValueError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    return _to_out(link)


@router.get("", response_model=list[LinkOut])
async def list_links(db: AsyncSession = Depends(get_db)) -> list[LinkOut]:
    rows = (await db.execute(select(Link).order_by(Link.created_at.desc()))).scalars().all()
    return [_to_out(link) for link in rows]
