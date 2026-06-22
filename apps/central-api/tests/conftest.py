from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database.base import Base, import_all_models

import_all_models()

# NOTE: tests run against in-memory SQLite for speed and zero external
# dependencies. The `face_embeddings` table uses a pgvector column type
# that has no SQLite equivalent, so it is intentionally excluded here —
# biometrics tests instead mock the repository/vision client (see
# test_biometrics.py) rather than hitting a real table.
_SQLITE_COMPATIBLE_TABLES = [
    table
    for name, table in Base.metadata.tables.items()
    if name != "face_embeddings"
]


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(
            sync_conn, tables=_SQLITE_COMPATIBLE_TABLES
        ))

    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"
