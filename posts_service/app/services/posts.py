from fastapi import HTTPException, status

from app.core.rabbitmq import RabbitMQCategoryValidator
from app.repositories.posts import PostRepository
from app.schemas.post import Post as PostSchema
from app.schemas.post import PostBase


class PostService:
    def __init__(self, post_repo: PostRepository, category_validator: RabbitMQCategoryValidator):
        self.post_repo = post_repo
        self.category_validator = category_validator

    async def get_all_posts(self, skip: int = 0, limit: int = 100) -> list[PostSchema]:
        db_posts = await self.post_repo.get_all(skip=skip, limit=limit)
        return [PostSchema.model_validate(post) for post in db_posts]

    async def get_post_by_id(self, post_id: int) -> PostSchema | None:
        db_post = await self.post_repo.get_by_id(post_id)
        if db_post is None:
            return None
        return PostSchema.model_validate(db_post)

    async def get_posts_by_category(self, category_id: int, skip: int = 0, limit: int = 100) -> list[PostSchema]:
        if category_id and not await self.category_validator.check_exists(category_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid category_id: Category not found")

        db_posts = await self.post_repo.get_by_category_id(category_id, skip=skip, limit=limit)
        return [PostSchema.model_validate(post) for post in db_posts]

    async def create_post(self, post: PostBase) -> PostSchema | None:
        if not await self.category_validator.check_exists(post.category_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid category_id: Category not found")

        db_post = await self.post_repo.create(
            title=post.title,
            content=post.content,
            category_id=post.category_id,
        )
        return PostSchema.model_validate(db_post)
