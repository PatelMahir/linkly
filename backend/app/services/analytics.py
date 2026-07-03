"""Analytics: enqueue clicks (write path) and aggregate them (read path).

Write path is decoupled via RabbitMQ — the redirect *enqueues* a click and the
worker (`app/worker.py`) calls `record_click` to persist it. This keeps the
redirect fast and lets ingestion scale independently.
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app import queue
from app.models import ClickEvent, Link
from app.schemas import ClickPoint, LinkAnalytics


async def enqueue_click(
    link_id: int,
    referrer: str | None,
    country: str | None,
    user_agent: str | None,
) -> None:
    """Publish a click event to the broker (called from the redirect path)."""
    await queue.publish_click(
        {
            "link_id": link_id,
            "referrer": referrer,
            "country": country,
            "user_agent": user_agent,
        }
    )


async def record_click(
    db: AsyncSession,
    link_id: int,
    referrer: str | None,
    country: str | None,
    user_agent: str | None,
) -> None:
    """Persist a click event. Called by the worker after consuming a message."""
    db.add(
        ClickEvent(
            link_id=link_id,
            referrer=referrer,
            country=country,
            user_agent=user_agent,
        )
    )
    await db.commit()


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
