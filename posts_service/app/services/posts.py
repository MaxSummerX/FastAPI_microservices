import os

import httpx
from fastapi import HTTPException, status

from app.repositories.posts import PostRepository
from app.schemas.post import Post as PostSchema
from app.schemas.post import PostBase


CATEGORIES_SERVICE_URL = os.getenv("CATEGORIES_SERVICE_URL", "http://127.0.0.1:8002")


class PostService:
    def __init__(self, post_repo: PostRepository):
        self.post_repo = post_repo

    async def get_all_posts(self, skip: int = 0, limit: int = 100) -> list[PostSchema]:
        db_posts = await self.post_repo.get_all(skip=skip, limit=limit)
        return [PostSchema.model_validate(post) for post in db_posts]

    async def get_post_by_id(self, post_id: int) -> PostSchema | None:
        db_post = await self.post_repo.get_by_id(post_id)
        if db_post is None:
            return None
        return PostSchema.model_validate(db_post)

    async def get_posts_by_category(self, category_id: int, skip: int = 0, limit: int = 100) -> list[PostSchema]:
        async with httpx.AsyncClient() as client:
            try:
                category_response = await client.get(f"{CATEGORIES_SERVICE_URL}/categories/{category_id}")
                category_response.raise_for_status()

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise HTTPException(status_code=400, detail="Invalid category_id: Category not found") from e
                raise HTTPException(
                    status_code=e.response.status_code, detail=f"Error from Categories Service: {e.response.text}"
                ) from e
            except httpx.RequestError as e:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Categories service unavailable: {e}"
                ) from e

        db_posts = await self.post_repo.get_by_category_id(category_id, skip=skip, limit=limit)
        return [PostSchema.model_validate(post) for post in db_posts]

    async def create_post(self, post: PostBase) -> PostSchema | None:
        async with httpx.AsyncClient() as client:
            try:
                category_response = await client.get(f"{CATEGORIES_SERVICE_URL}/categories/{post.category_id}")
                category_response.raise_for_status()

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise HTTPException(status_code=400, detail="Invalid category_id: Category not found") from e
                raise HTTPException(
                    status_code=e.response.status_code, detail=f"Error from Categories Service: {e.response.text}"
                ) from e
            except httpx.RequestError as e:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Categories service unavailable: {e}"
                ) from e

        db_post = await self.post_repo.create(
            title=post.title,
            content=post.content,
            category_id=post.category_id,
        )
        return PostSchema.model_validate(db_post)
