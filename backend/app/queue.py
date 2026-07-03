"""RabbitMQ publisher for the click-analytics pipeline.

Why a queue: on a busy shortener, redirects vastly outnumber every other
operation. Writing each click to Postgres inline couples the redirect latency to
DB write throughput. Instead the redirect publishes a lightweight message and a
separate worker (`app/worker.py`) consumes and persists them — so the two scale
independently and a burst of clicks buffers in the broker instead of hammering
the DB.

Publishing is best-effort: if the broker is unreachable we log and move on
rather than break the redirect. `_channel` is module-level so tests can inject a
fake by monkeypatching `publish_click`.
"""

import json
import logging

import aio_pika

from app.config import get_settings

logger = logging.getLogger("linkly.queue")
settings = get_settings()

QUEUE_NAME = "click_events"

_connection: aio_pika.abc.AbstractRobustConnection | None = None
_channel: aio_pika.abc.AbstractChannel | None = None


async def _get_channel() -> aio_pika.abc.AbstractChannel:
    """Lazily open a robust connection + channel and declare the queue."""
    global _connection, _channel
    if _channel is None or _channel.is_closed:
        _connection = await aio_pika.connect_robust(settings.rabbitmq_url)
        _channel = await _connection.channel()
        # Durable queue so buffered clicks survive a broker restart.
        await _channel.declare_queue(QUEUE_NAME, durable=True)
    return _channel


async def publish_click(payload: dict) -> None:
    """Publish a click event. Never raises — analytics must not break redirects."""
    try:
        channel = await _get_channel()
        await channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(payload).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                content_type="application/json",
            ),
            routing_key=QUEUE_NAME,
        )
    except Exception:  # noqa: BLE001 - best-effort, degrade gracefully
        logger.warning("Failed to publish click event; dropping", exc_info=True)


async def close() -> None:
    """Close the connection on shutdown."""
    global _connection, _channel
    if _connection is not None and not _connection.is_closed:
        await _connection.close()
    _connection = None
    _channel = None
