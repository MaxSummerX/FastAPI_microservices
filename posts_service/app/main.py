from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routers import posts
from app.core.database import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    print("Приложение запускается. Создаем базу данных...")
    await create_db_and_tables()
    print("База данных инициализирована.")
    yield
    print("Приложение завершает работу.")


app = FastAPI(title="Сервис постов", lifespan=lifespan)

app.include_router(posts.router)


@app.get("/")
async def root() -> dict[str, str]:
    """Корневой эндпойнт"""
    return {"message": "Welcome to posts service."}
