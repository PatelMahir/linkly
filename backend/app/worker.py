"""Click-analytics worker: consumes click events from RabbitMQ and persists them.

Run as its own process/container (see docker-compose `worker` service):

    python -m app.worker

Scaling: run N replicas of this worker to increase ingestion throughput — the
broker load-balances messages across them. `prefetch_count` bounds how many
unacked messages each consumer holds so work spreads evenly.
"""

import asyncio
import json
import logging

import aio_pika

from app import database
from app.config import get_settings
from app.queue import QUEUE_NAME
from app.services.analytics import record_click

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("linkly.worker")


async def handle_message(message: aio_pika.abc.AbstractIncomingMessage) -> None:
    """Persist one click event. `message.process()` acks on success, requeues on error."""
    async with message.process(requeue=True):
        data = json.loads(message.body)
        async with database.SessionLocal() as db:
            await record_click(
                db,
                link_id=data["link_id"],
                referrer=data.get("referrer"),
                country=data.get("country"),
                user_agent=data.get("user_agent"),
            )
        logger.info("Recorded click for link_id=%s", data["link_id"])


async def main() -> None:
    settings = get_settings()
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=50)
    queue = await channel.declare_queue(QUEUE_NAME, durable=True)

    logger.info("Worker ready; consuming from '%s'", QUEUE_NAME)
    await queue.consume(handle_message)
    await asyncio.Future()  # run until cancelled


if __name__ == "__main__":
    asyncio.run(main())
