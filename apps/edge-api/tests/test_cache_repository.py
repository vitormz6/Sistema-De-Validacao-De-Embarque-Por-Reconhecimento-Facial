import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.cache.model import LocalFaceEmbedding
from app.modules.cache.repository import EmbeddingCacheRepository

# `local_face_embeddings.embedding` (ARRAY(Float)) has no SQLite equivalent
# (see tests/conftest.py), so EmbeddingCacheRepository is exercised against
# a mocked AsyncSession instead of the real in-memory DB — same pattern
# used in sync-worker's tests/test_cache_repository.py.


@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock()
    session.flush = AsyncMock()
    session.add = MagicMock()
    return session


async def test_embedding_upsert_inserts_with_active_flag(mock_session: AsyncMock) -> None:
    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = execute_result

    repository = EmbeddingCacheRepository(mock_session)
    embedding_id = uuid.uuid4()
    passenger_id = uuid.uuid4()

    await repository.upsert(
        id=embedding_id,
        passenger_id=passenger_id,
        embedding=[0.1, 0.2, 0.3],
        model_name="arcface",
        model_version="buffalo_l",
        active=True,
    )

    mock_session.add.assert_called_once()
    added = mock_session.add.call_args[0][0]
    assert isinstance(added, LocalFaceEmbedding)
    assert added.active is True


async def test_embedding_upsert_revokes_existing_row(mock_session: AsyncMock) -> None:
    """
    Regression test for the biometric-revocation propagation bug: when
    sync-worker re-upserts an embedding with `active=False` (because
    central-api revoked it), the local row must flip to inactive — not
    keep its previously-cached `active=True` value.
    """
    existing = LocalFaceEmbedding(
        id=uuid.uuid4(),
        passenger_id=uuid.uuid4(),
        embedding=[0.0, 0.0],
        model_name="arcface",
        model_version="buffalo_l_v0",
        active=True,
    )
    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = existing
    mock_session.execute.return_value = execute_result

    repository = EmbeddingCacheRepository(mock_session)

    updated = await repository.upsert(
        id=existing.id,
        passenger_id=existing.passenger_id,
        embedding=existing.embedding,
        model_name=existing.model_name,
        model_version=existing.model_version,
        active=False,
    )

    assert updated.active is False


async def test_list_active_filters_by_active_flag(mock_session: AsyncMock) -> None:
    """
    `list_active` used to return the whole table unconditionally. Now it
    must filter on the `active` column — asserted here by inspecting the
    compiled SQL passed to `session.execute`, since the SQLite test DB
    can't host this table directly (see module docstring above).
    """
    execute_result = MagicMock()
    execute_result.scalars.return_value.all.return_value = []
    mock_session.execute.return_value = execute_result

    repository = EmbeddingCacheRepository(mock_session)
    await repository.list_active()

    mock_session.execute.assert_awaited_once()
    statement = mock_session.execute.call_args[0][0]
    compiled_sql = str(statement.compile(compile_kwargs={"literal_binds": True})).lower()

    assert "local_face_embeddings" in compiled_sql
    assert "active" in compiled_sql
    assert "true" in compiled_sql
