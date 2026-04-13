import asyncio
import os
import uuid

import aio_pika
from aio_pika.abc import (
    AbstractChannel,
    AbstractIncomingMessage,
    AbstractQueue,
    AbstractRobustConnection,
)


RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")


class RpcClient:
    """Асинхронный RPC клиент для RabbitMQ."""

    def __init__(self, amqp_url: str = RABBITMQ_URL) -> None:
        self.amqp_url = amqp_url
        self.connection: AbstractRobustConnection | None = None
        self.channel: AbstractChannel | None = None
        self.callback_queue: AbstractQueue | None = None
        self.futures: dict[str, asyncio.Future[bytes]] = {}
        self.loop = asyncio.get_running_loop()

    async def on_response(self, message: AbstractIncomingMessage) -> None:
        correlation_id = message.correlation_id
        future = self.futures.pop(correlation_id, None) if correlation_id else None
        if future:
            future.set_result(message.body)

    async def connect(self) -> None:
        self.connection = await aio_pika.connect_robust(self.amqp_url, loop=self.loop)
        self.channel = await self.connection.channel()
        self.callback_queue = await self.channel.declare_queue(exclusive=True)
        await self.callback_queue.consume(self.on_response, no_ack=True)

    async def close(self) -> None:
        if self.connection and not self.connection.is_closed:
            await self.connection.close()

    async def call(self, category_id: int) -> bytes | None:
        if not self.connection or self.connection.is_closed:
            raise ConnectionError("RPC client is not connected")

        correlation_id = str(uuid.uuid4())
        future = self.loop.create_future()
        self.futures[correlation_id] = future

        if self.channel is None:
            raise ConnectionError("RPC client is not connected")
        if self.callback_queue is None:
            raise ConnectionError("RPC client is not connected")

        await self.channel.default_exchange.publish(
            aio_pika.Message(
                body=str(category_id).encode(),
                correlation_id=correlation_id,
                reply_to=self.callback_queue.name,
            ),
            routing_key="category_check_queue",
        )

        try:
            return await asyncio.wait_for(future, timeout=5.0)
        except TimeoutError:
            self.futures.pop(correlation_id, None)
            return None


class RabbitMQCategoryValidator:
    """Валидатор категорий чере  RabbitMQ RPC"""

    def __init__(self) -> None:
        self.rpc_client = RpcClient()

    async def connect(self) -> None:
        await self.rpc_client.connect()

    async def close(self) -> None:
        await self.rpc_client.close()

    async def check_exists(self, category_id: int) -> bool:
        response = await self.rpc_client.call(category_id)
        if response is None:
            return False
        return response == b"true"


category_validator_instance = RabbitMQCategoryValidator()
