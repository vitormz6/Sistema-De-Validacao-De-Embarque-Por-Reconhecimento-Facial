from collections.abc import AsyncGenerator

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database.base import Base, import_all_models

import_all_models()

# `local_face_embeddings.embedding` is a Postgres ARRAY(Float) column with
# no SQLite equivalent — excluded here the same way pgvector's Vector type
# was excluded in central-api's tests. Anything touching embeddings is
# tested with a mocked `EmbeddingCacheRepository` instead (see
# test_validation_service.py).
_SQLITE_COMPATIBLE_TABLES = [
    table for name, table in Base.metadata.tables.items() if name != "local_face_embeddings"
]


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async with engine.begin() as conn:
        await conn.run_sync(
            lambda sync_conn: Base.metadata.create_all(sync_conn, tables=_SQLITE_COMPATIBLE_TABLES)
        )

    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with session_factory() as session:
        yield session

    await engine.dispose()
