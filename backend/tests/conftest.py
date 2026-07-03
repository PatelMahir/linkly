"""Test fixtures: an in-memory SQLite DB and an in-process fake Redis.

The DB uses a StaticPool so a single shared in-memory database is reused across
sessions — this matters because background tasks (click recording) open their
*own* session and must see the same data the request wrote.

Redis is replaced with fakeredis so cache + rate-limiting logic runs for real
without a Redis server.
"""

from collections.abc import AsyncGenerator

import fakeredis.aioredis
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app import cache, database
from app.database import Base, get_db
from app.main import app


@pytest_asyncio.fixture
async def client(monkeypatch) -> AsyncGenerator[AsyncClient, None]:  # type: ignore[no-untyped-def]
    # Shared in-memory DB (StaticPool) so request + background sessions align.
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    test_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    # Point the app's engine + session factory at the test DB. Background tasks
    # use database.SessionLocal; the readiness probe uses database.engine.
    monkeypatch.setattr(database, "engine", engine)
    monkeypatch.setattr(database, "SessionLocal", test_session)

    # Swap Redis for an in-process fake shared by cache + rate limiter.
    fake_redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(cache, "redis", fake_redis)

    async def _get_db() -> AsyncGenerator[AsyncSession, None]:
        async with test_session() as session:
            yield session

    app.dependency_overrides[get_db] = _get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
    await engine.dispose()
