"""Redis-backed fixed-window rate limiting, exposed as a FastAPI dependency.

Why fixed-window: it's O(1) per request (a single INCR + conditional EXPIRE),
which is exactly what you want on hot paths. For stricter fairness you'd swap in
a sliding-window or token-bucket algorithm, but the dependency interface stays
the same.

Usage:
    limiter = RateLimiter(limit=30, window_seconds=60, scope="create")

    @router.post("", dependencies=[Depends(limiter)])
    async def create(...): ...
"""

from fastapi import HTTPException, Request, status

from app import cache


class RateLimiter:
    def __init__(self, limit: int, window_seconds: int, scope: str) -> None:
        self.limit = limit
        self.window = window_seconds
        self.scope = scope

    async def __call__(self, request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        key = f"rl:{self.scope}:{client_ip}"

        # INCR returns the new counter value; on the first hit we set the TTL so
        # the window expires. `cache.redis` is looked up at call time so tests
        # can inject a fake client.
        count = await cache.redis.incr(key)
        if count == 1:
            await cache.redis.expire(key, self.window)

        if count > self.limit:
            retry_after = await cache.redis.ttl(key)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Retry in {retry_after}s.",
                headers={"Retry-After": str(max(retry_after, 1))},
            )
