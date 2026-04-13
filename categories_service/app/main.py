import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routers import categories
from app.core.database import create_db_and_tables
from app.core.rabbitmq_worker import run_consumer


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    print("Приложение категорий запускается. Создаем базу данных и запускаем RabbitMQ consumer...")
    consumer_task = asyncio.create_task(run_consumer())
    await create_db_and_tables()
    print("Инициализация завершена.")
    yield
    print("Приложение категорий завершает работу. Останавливаем consumer...")
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        print("Consumer RabbitMQ успешно остановлен.")


app = FastAPI(title="Сервис категорий", lifespan=lifespan)

app.include_router(categories.router)


@app.get("/")
async def root() -> dict[str, str]:
    """Корневой эндпоинт."""
    return {"message": "Welcome to categories service."}
