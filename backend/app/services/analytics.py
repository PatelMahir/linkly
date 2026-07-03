"""Analytics queries: aggregate click_events into dashboard-ready shapes."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app import database
from app.models import ClickEvent, Link
from app.schemas import ClickPoint, LinkAnalytics


async def record_click(
    db: AsyncSession,
    link_id: int,
    referrer: str | None,
    country: str | None,
    user_agent: str | None,
) -> None:
    """Append a click event using an existing session."""
    db.add(
        ClickEvent(
            link_id=link_id,
            referrer=referrer,
            country=country,
            user_agent=user_agent,
        )
    )
    await db.commit()


async def record_click_bg(
    link_id: int,
    referrer: str | None,
    country: str | None,
    user_agent: str | None,
) -> None:
    """Record a click from a FastAPI BackgroundTask.

    Runs *after* the redirect response is sent, so the request-scoped session is
    already closed — we open our own short-lived session here. `database.SessionLocal`
    is referenced at call time so tests can point it at the test database.
    """
    async with database.SessionLocal() as db:
        await record_click(db, link_id, referrer, country, user_agent)


async def get_analytics(db: AsyncSession, link: Link) -> LinkAnalytics:
    total = await db.scalar(
        select(func.count(ClickEvent.id)).where(ClickEvent.link_id == link.id)
    )

    referrer_rows = (
        await db.execute(
            select(ClickEvent.referrer, func.count(ClickEvent.id))
            .where(ClickEvent.link_id == link.id)
            .group_by(ClickEvent.referrer)
            .order_by(func.count(ClickEvent.id).desc())
            .limit(5)
        )
    ).all()

    # Clicks per day for the timeseries chart.
    day = func.date(ClickEvent.created_at)
    series_rows = (
        await db.execute(
            select(day, func.count(ClickEvent.id))
            .where(ClickEvent.link_id == link.id)
            .group_by(day)
            .order_by(day)
        )
    ).all()

    return LinkAnalytics(
        code=link.code,
        total_clicks=total or 0,
        top_referrers=[(r or "direct", c) for r, c in referrer_rows],
        timeseries=[ClickPoint(date=str(d), clicks=c) for d, c in series_rows],
    )
