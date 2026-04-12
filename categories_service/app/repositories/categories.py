from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category


class CategoryRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, category_id: int) -> Category | None:
        result = await self.db.scalar(select(Category).where(Category.id == category_id))
        return result

    async def get_by_name(self, name: str) -> Category | None:
        result = await self.db.scalar(select(Category).where(Category.name == name))
        return result

    async def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[Category]:
        result = await self.db.scalars(select(Category).offset(skip).limit(limit))
        return result.all()

    async def create(self, name: str) -> Category:
        db_category = Category(name=name)
        self.db.add(db_category)
        await self.db.commit()
        await self.db.refresh(db_category)
        return db_category
