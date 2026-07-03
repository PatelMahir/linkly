"""Unit tests for the Redis-backed rate limiter.

Exercises the RateLimiter dependency directly with a fake Redis and a stub
Request, so we assert the counter/threshold logic without spinning up HTTP.
"""

from types import SimpleNamespace

import fakeredis.aioredis
import pytest
from fastapi import HTTPException

from app import cache
from app.rate_limit import RateLimiter


def _request(ip: str = "1.2.3.4"):  # type: ignore[no-untyped-def]
    return SimpleNamespace(client=SimpleNamespace(host=ip))


@pytest.mark.asyncio
async def test_allows_up_to_limit_then_blocks(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cache, "redis", fakeredis.aioredis.FakeRedis(decode_responses=True))
    limiter = RateLimiter(limit=2, window_seconds=60, scope="unit")

    # First two calls pass.
    await limiter(_request())
    await limiter(_request())

    # Third call over the window is rejected with 429 + Retry-After.
    with pytest.raises(HTTPException) as exc:
        await limiter(_request())
    assert exc.value.status_code == 429
    assert "Retry-After" in exc.value.headers


@pytest.mark.asyncio
async def test_limit_is_per_client_ip(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cache, "redis", fakeredis.aioredis.FakeRedis(decode_responses=True))
    limiter = RateLimiter(limit=1, window_seconds=60, scope="unit")

    await limiter(_request("10.0.0.1"))
    # A different IP has its own budget.
    await limiter(_request("10.0.0.2"))

    with pytest.raises(HTTPException):
        await limiter(_request("10.0.0.1"))
