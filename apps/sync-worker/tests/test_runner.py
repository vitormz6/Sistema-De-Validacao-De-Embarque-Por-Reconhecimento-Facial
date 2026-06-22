import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock

from app.modules.validation.model import LocalValidationLog
from app.runner import SyncRunner
from app.schemas import (
    EmbeddingPullItem,
    PassengerPullItem,
    PullResult,
    PushResult,
    TicketPullItem,
)


async def test_run_pull_cycle_upserts_passengers_and_tickets_then_acks(db_session) -> None:
    passenger_id = uuid.uuid4()
    ticket_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    pull_result = PullResult(
        cursor=now,
        passengers=[
            PassengerPullItem(
                id=passenger_id, full_name="Ana", document_number="123", status="ACTIVE"
            )
        ],
        # `local_face_embeddings` isn't creatable on the SQLite test DB
        # (see tests/conftest.py) — EmbeddingCacheRepository is covered
        # separately in test_cache_repository.py with a mocked session.
        embeddings=[],
        tickets=[
            TicketPullItem(
                id=ticket_id,
                passenger_id=passenger_id,
                ticket_type="MONTHLY",
                status="ACTIVE",
                valid_from=now,
                valid_until=now,
            )
        ],
    )

    fake_client = AsyncMock()
    fake_client.pull = AsyncMock(return_value=pull_result)
    fake_client.ack = AsyncMock()

    runner = SyncRunner(db_session, client=fake_client)
    upserted_count = await runner.run_pull_cycle()

    assert upserted_count == 2
    fake_client.ack.assert_awaited_once_with(now)


async def test_run_pull_cycle_forwards_embedding_active_flag(db_session) -> None:
    """
    Regression test for the biometric-revocation propagation bug, at the
    runner level: a revoked embedding (active=False) in the pull response
    must reach `EmbeddingCacheRepository.upsert` with that same flag, not
    silently default to True. `local_face_embeddings` can't be created on
    the SQLite test DB (see tests/conftest.py), so the embedding repository
    itself is swapped for a mock here, mirroring the pattern already used
    in test_cache_repository.py.
    """
    passenger_id = uuid.uuid4()
    embedding_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    pull_result = PullResult(
        cursor=now,
        passengers=[],
        embeddings=[
            EmbeddingPullItem(
                id=embedding_id,
                passenger_id=passenger_id,
                embedding=[0.1, 0.2],
                model_name="arcface",
                model_version="buffalo_l",
                active=False,
            )
        ],
        tickets=[],
    )

    fake_client = AsyncMock()
    fake_client.pull = AsyncMock(return_value=pull_result)
    fake_client.ack = AsyncMock()

    runner = SyncRunner(db_session, client=fake_client)
    runner.embedding_repository.upsert = AsyncMock()

    await runner.run_pull_cycle()

    runner.embedding_repository.upsert.assert_awaited_once_with(
        id=embedding_id,
        passenger_id=passenger_id,
        embedding=[0.1, 0.2],
        model_name="arcface",
        model_version="buffalo_l",
        active=False,
    )


async def test_run_push_cycle_marks_accepted_and_duplicated_as_synced(db_session) -> None:
    accepted_log = LocalValidationLog(
        id=uuid.uuid4(), bus_id="bus-01", status="AUTHORIZED", is_offline=False,
        captured_at=datetime.now(timezone.utc),
    )
    duplicated_log = LocalValidationLog(
        id=uuid.uuid4(), bus_id="bus-01", status="AUTHORIZED", is_offline=False,
        captured_at=datetime.now(timezone.utc),
    )
    rejected_log = LocalValidationLog(
        id=uuid.uuid4(), bus_id="bus-01", status="AUTHORIZED", is_offline=False,
        captured_at=datetime.now(timezone.utc),
    )
    db_session.add_all([accepted_log, duplicated_log, rejected_log])
    await db_session.flush()

    push_result = PushResult(
        accepted=[str(accepted_log.id)],
        duplicated=[str(duplicated_log.id)],
        rejected=[{"external_id": str(rejected_log.id), "reason": "malformed"}],
    )

    fake_client = AsyncMock()
    fake_client.push = AsyncMock(return_value=push_result)

    runner = SyncRunner(db_session, client=fake_client)
    synced_count = await runner.run_push_cycle()

    assert synced_count == 2
    await db_session.refresh(accepted_log)
    await db_session.refresh(duplicated_log)
    await db_session.refresh(rejected_log)
    assert accepted_log.synced_at is not None
    assert duplicated_log.synced_at is not None
    assert rejected_log.synced_at is None


async def test_run_push_cycle_with_nothing_pending_skips_push_call(db_session) -> None:
    fake_client = AsyncMock()
    fake_client.push = AsyncMock()

    runner = SyncRunner(db_session, client=fake_client)
    synced_count = await runner.run_push_cycle()

    assert synced_count == 0
    fake_client.push.assert_not_awaited()
