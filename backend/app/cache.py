"""Thin async Redis wrapper for the hot redirect path + rate limiting.

The redirect endpoint is the hottest read in the system, so we cache the
minimal payload needed to serve a redirect AND record a click — the link's
`id` and `long_url` — under `link:{code}`. On a cache hit we skip Postgres
entirely.
"""

import json

from redis.asyncio import Redis

from app.config import get_settings

settings = get_settings()

# Module-level client. Referenced as `cache.redis` elsewhere so tests can swap
# in a fake by monkeypatching this attribute.
redis: Redis = Redis.from_url(settings.redis_url, decode_responses=True)


def _key(code: str) -> str:
    return f"link:{code}"


async def get_cached_link(code: str) -> tuple[int, str] | None:
    """Return (link_id, long_url) from cache, or None on a miss."""
    raw = await redis.get(_key(code))
    if raw is None:
        return None
    data = json.loads(raw)
    return data["id"], data["url"]


async def cache_link(code: str, link_id: int, long_url: str) -> None:
    await redis.set(
        _key(code),
        json.dumps({"id": link_id, "url": long_url}),
        ex=settings.cache_ttl_seconds,
    )


async def invalidate(code: str) -> None:
    await redis.delete(_key(code))
