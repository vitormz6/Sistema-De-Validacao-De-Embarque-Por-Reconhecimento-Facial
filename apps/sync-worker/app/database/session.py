from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


@asynccontextmanager
async def session_scope() -> AsyncGenerator[AsyncSession, None]:
    """
    No FastAPI request scope here to hang a `Depends` off, so each sync
    cycle opens its own session explicitly via this context manager.
    """
    async with AsyncSessionLocal() as session:
        yield session
