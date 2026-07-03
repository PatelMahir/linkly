"""Analytics endpoint powering the dashboard charts."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Link
from app.schemas import LinkAnalytics
from app.services import analytics

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/{code}", response_model=LinkAnalytics)
async def link_analytics(code: str, db: AsyncSession = Depends(get_db)) -> LinkAnalytics:
    link = (await db.execute(select(Link).where(Link.code == code))).scalar_one_or_none()
    if link is None:
        raise HTTPException(404, f"No link with code '{code}'")
    return await analytics.get_analytics(db, link)
