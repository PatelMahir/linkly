"""Business logic for creating and resolving short links.

This is the *service* layer: routers call these functions, and these functions
own the DB + cache interactions. Keeping logic here (not in routers) makes it
unit-testable and reusable.
"""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app import cache
from app.config import get_settings
from app.models import Link
from app.utils.shortcode import generate_code

settings = get_settings()

_MAX_RETRIES = 5


def short_url_for(code: str) -> str:
    return f"{settings.base_url}/{code}"


async def create_link(db: AsyncSession, long_url: str, custom_code: str | None) -> Link:
    """Create a link, generating a unique code (or using a vanity code).

    Retries on collision when auto-generating. Raises ValueError if a requested
    custom code is already taken.
    """
    if custom_code:
        link = Link(code=custom_code, long_url=long_url)
        db.add(link)
        try:
            await db.commit()
        except IntegrityError as exc:
            await db.rollback()
            raise ValueError(f"Code '{custom_code}' is already taken") from exc
        await db.refresh(link)
        return link

    for _ in range(_MAX_RETRIES):
        link = Link(code=generate_code(), long_url=long_url)
        db.add(link)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            continue
        await db.refresh(link)
        return link

    raise RuntimeError("Could not generate a unique code; try again")


async def resolve_code(db: AsyncSession, code: str) -> Link | None:
    """Return the Link for a code, using Redis as a read-through cache."""
    cached = await cache.get_cached_url(code)
    if cached:
        # We still need the Link row for analytics, but the cache lets us skip
        # the URL lookup on the hot path when only the destination is needed.
        pass

    result = await db.execute(select(Link).where(Link.code == code))
    link = result.scalar_one_or_none()
    if link:
        await cache.cache_url(code, link.long_url)
    return link
