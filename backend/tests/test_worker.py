"""Tests for the RabbitMQ click pipeline: enqueue (producer) + worker (consumer).

No real broker is used — we assert the producer publishes the right payload and
that the worker's message handler persists a ClickEvent.
"""

import json
from contextlib import asynccontextmanager

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app import queue, worker
from app.models import ClickEvent, Link
from app.services import analytics


@pytest.mark.asyncio
async def test_enqueue_click_publishes_expected_payload(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    captured: dict = {}

    async def _capture(payload: dict) -> None:
        captured.update(payload)

    monkeypatch.setattr(queue, "publish_click", _capture)

    await analytics.enqueue_click(
        link_id=7, referrer="https://x.com", country="US", user_agent="ua"
    )

    assert captured == {
        "link_id": 7,
        "referrer": "https://x.com",
        "country": "US",
        "user_agent": "ua",
    }


class _FakeMessage:
    """Minimal stand-in for aio_pika's IncomingMessage."""

    def __init__(self, payload: dict) -> None:
        self.body = json.dumps(payload).encode()

    def process(self, requeue: bool = False):  # type: ignore[no-untyped-def]
        @asynccontextmanager
        async def _cm():  # type: ignore[no-untyped-def]
            yield

        return _cm()


@pytest.mark.asyncio
async def test_worker_persists_click(db_session: AsyncSession) -> None:
    link = Link(code="wrk1", long_url="https://example.com")
    db_session.add(link)
    await db_session.commit()
    await db_session.refresh(link)

    await worker.handle_message(_FakeMessage({"link_id": link.id, "referrer": "https://ref"}))

    count = await db_session.scalar(
        select(func.count(ClickEvent.id)).where(ClickEvent.link_id == link.id)
    )
    assert count == 1
