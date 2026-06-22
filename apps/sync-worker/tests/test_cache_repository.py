import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.cache.model import LocalFaceEmbedding
from app.modules.cache.repository import (
    EmbeddingCacheRepository,
    PassengerCacheRepository,
    TicketCacheRepository,
)


async def test_passenger_upsert_inserts_new_row(db_session) -> None:
    repository = PassengerCacheRepository(db_session)
    passenger_id = uuid.uuid4()

    row = await repository.upsert(
        id=passenger_id,
        full_name="Maria Silva",
        document_number="12345678900",
        status="ACTIVE",
    )

    assert row.id == passenger_id
    assert row.full_name == "Maria Silva"


async def test_passenger_upsert_updates_existing_row(db_session) -> None:
    repository = PassengerCacheRepository(db_session)
    passenger_id = uuid.uuid4()

    await repository.upsert(
        id=passenger_id, full_name="Maria Silva", document_number="111", status="ACTIVE"
    )
    updated = await repository.upsert(
        id=passenger_id, full_name="Maria S. Souza", document_number="111", status="BLOCKED"
    )

    assert updated.full_name == "Maria S. Souza"
    assert updated.status == "BLOCKED"


async def test_ticket_upsert_inserts_then_updates(db_session) -> None:
    passenger_repository = PassengerCacheRepository(db_session)
    ticket_repository = TicketCacheRepository(db_session)
    passenger_id = uuid.uuid4()
    ticket_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    await passenger_repository.upsert(
        id=passenger_id, full_name="João", document_number="222", status="ACTIVE"
    )

    inserted = await ticket_repository.upsert(
        id=ticket_id,
        passenger_id=passenger_id,
        ticket_type="MONTHLY",
        status="ACTIVE",
        valid_from=now,
        valid_until=now + timedelta(days=30),
    )
    assert inserted.status == "ACTIVE"

    updated = await ticket_repository.upsert(
        id=ticket_id,
        passenger_id=passenger_id,
        ticket_type="MONTHLY",
        status="CANCELLED",
        valid_from=now,
        valid_until=now + timedelta(days=30),
    )
    assert updated.status == "CANCELLED"


# `local_face_embeddings` (ARRAY(Float)) has no SQLite equivalent — see
# tests/conftest.py — so EmbeddingCacheRepository is exercised against a
# mocked AsyncSession instead of the real in-memory DB.


@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock()
    session.flush = AsyncMock()
    session.add = MagicMock()
    return session


async def test_embedding_upsert_inserts_when_missing(mock_session: AsyncMock) -> None:
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
    assert added.id == embedding_id
    assert added.embedding == [0.1, 0.2, 0.3]
    assert added.active is True
    mock_session.flush.assert_awaited_once()


async def test_embedding_upsert_updates_when_present(mock_session: AsyncMock) -> None:
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
        embedding=[0.5, 0.6],
        model_name="arcface",
        model_version="buffalo_l_v1",
        active=False,
    )

    mock_session.add.assert_not_called()
    assert updated.embedding == [0.5, 0.6]
    assert updated.model_version == "buffalo_l_v1"


async def test_embedding_upsert_revokes_existing_row(mock_session: AsyncMock) -> None:
    """
    Regression test for the biometric-revocation propagation bug: re-running
    upsert with `active=False` on a row that was previously active must
    flip it to inactive, not leave the old True value in place.
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
