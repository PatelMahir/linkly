"""Business logic for creating and resolving short links.

This is the *service* layer: routers call these functions, and these functions
own the DB + cache interactions. Keeping logic here (not in routers) makes it
unit-testable and reusable.
"""

from typing import NamedTuple

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app import cache
from app.config import get_settings
from app.models import Link
from app.utils.shortcode import generate_code

settings = get_settings()

_MAX_RETRIES = 5


class ResolvedLink(NamedTuple):
    """Minimal link data needed to serve a redirect + record a click.

    Returned from either the cache (no DB round-trip) or Postgres.
    """

    id: int
    long_url: str


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


async def resolve_code(db: AsyncSession, code: str) -> ResolvedLink | None:
    """Resolve a code to (id, long_url) using Redis as a read-through cache.

    On a cache hit we return immediately without touching Postgres — this is the
    optimization that lets the redirect path scale. On a miss we read the DB once
    and populate the cache for next time.
    """
    cached = await cache.get_cached_link(code)
    if cached is not None:
        return ResolvedLink(id=cached[0], long_url=cached[1])

    result = await db.execute(select(Link.id, Link.long_url).where(Link.code == code))
    row = result.first()
    if row is None:
        return None

    await cache.cache_link(code, row.id, row.long_url)
    return ResolvedLink(id=row.id, long_url=row.long_url)
