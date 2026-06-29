from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.router import router
from app.core.config import settings
from app.core.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    configure_logging()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Face detection, quality, basic liveness and embedding generation.",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    app.include_router(router)

    Instrumentator().instrument(app).expose(app, endpoint="/metrics")

    return app


app = create_app()
