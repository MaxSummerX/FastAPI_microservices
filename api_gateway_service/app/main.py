import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request, Response


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.http_client = httpx.AsyncClient()
    try:
        yield
    finally:
        await app.state.http_client.aclose()


app = FastAPI(lifespan=lifespan)

POSTS_SERVICE_URL = os.environ.get("POSTS_SERVICE_URL")
CATEGORIES_SERVICE_URL = os.environ.get("CATEGORIES_SERVICE_URL")


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
async def proxy_request(request: Request, path: str) -> Response:
    target_url = None
    if path.startswith("posts"):
        target_url = f"{POSTS_SERVICE_URL}/{path}"
    elif path.startswith("categories"):
        target_url = f"{CATEGORIES_SERVICE_URL}/{path}"

    if not target_url:
        return Response(content="Not found", status_code=404)

    body = await request.body()

    proxied_request = app.state.http_client.build_request(
        method=request.method,
        url=target_url,
        headers=request.headers,
        params=request.query_params,
        content=body,
    )
    response = await app.state.http_client.send(proxied_request)

    return Response(content=response.content, status_code=response.status_code, headers=dict(response.headers))
