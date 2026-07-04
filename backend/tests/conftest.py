"""Test fixtures: in-memory SQLite, fake Redis, and an inline "worker".

The DB uses a StaticPool so a single shared in-memory database is reused across
sessions — the request session, the readiness probe, and the worker all see the
same data.

Redis is replaced with fakeredis. RabbitMQ is replaced by wiring `publish_click`
straight to the persist path, so end-to-end redirect -> analytics assertions
hold without running a broker.
"""

from collections.abc import AsyncGenerator

import fakeredis.aioredis
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app import cache, database, queue
from app.database import Base, get_db
from app.main import app
from app.services.analytics import record_click


def _make_engine():  # type: ignore[no-untyped-def]
    return create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


async def _setup(monkeypatch):  # type: ignore[no-untyped-def]
    engine = _make_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    test_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    # Point the app's engine + session factory at the test DB.
    monkeypatch.setattr(database, "engine", engine)
    monkeypatch.setattr(database, "SessionLocal", test_session)

    # In-process Redis for cache + rate limiting.
    monkeypatch.setattr(cache, "redis", fakeredis.aioredis.FakeRedis(decode_responses=True))

    # Simulate the worker inline: publishing a click persists it immediately.
    async def _fake_publish(payload: dict) -> None:
        async with test_session() as db:
            await record_click(
                db,
                payload["link_id"],
                payload.get("referrer"),
                payload.get("country"),
                payload.get("user_agent"),
            )

    monkeypatch.setattr(queue, "publish_click", _fake_publish)
    return engine, test_session


@pytest_asyncio.fixture
async def db_session(monkeypatch) -> AsyncGenerator[AsyncSession, None]:  # type: ignore[no-untyped-def]
    engine, test_session = await _setup(monkeypatch)
    async with test_session() as session:
        yield session
    await engine.dispose()


@pytest_asyncio.fixture
async def client(monkeypatch) -> AsyncGenerator[AsyncClient, None]:  # type: ignore[no-untyped-def]
    engine, test_session = await _setup(monkeypatch)

    async def _get_db() -> AsyncGenerator[AsyncSession, None]:
        async with test_session() as session:
            yield session

    app.dependency_overrides[get_db] = _get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
    await engine.dispose()
