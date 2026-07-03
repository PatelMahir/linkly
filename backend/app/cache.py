"""Thin async Redis wrapper for hot redirect lookups.

The redirect path is the hottest read in the system, so we cache
`code -> long_url` with a TTL to avoid hitting Postgres every time.
"""

from redis.asyncio import Redis

from app.config import get_settings

settings = get_settings()

redis: Redis = Redis.from_url(settings.redis_url, decode_responses=True)


def _key(code: str) -> str:
    return f"link:{code}"


async def get_cached_url(code: str) -> str | None:
    return await redis.get(_key(code))


async def cache_url(code: str, long_url: str) -> None:
    await redis.set(_key(code), long_url, ex=settings.cache_ttl_seconds)


async def invalidate(code: str) -> None:
    await redis.delete(_key(code))
