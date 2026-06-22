import uuid
from datetime import datetime, timedelta, timezone

from app.modules.validation.model import LocalValidationLog
from app.modules.validation.repository import ValidationLogRepository


async def _make_log(synced: bool = False) -> LocalValidationLog:
    return LocalValidationLog(
        id=uuid.uuid4(),
        bus_id="bus-01",
        status="AUTHORIZED",
        is_offline=False,
        captured_at=datetime.now(timezone.utc),
        synced_at=datetime.now(timezone.utc) if synced else None,
    )


async def test_get_pending_sync_excludes_already_synced(db_session) -> None:
    pending = await _make_log(synced=False)
    already_synced = await _make_log(synced=True)
    db_session.add_all([pending, already_synced])
    await db_session.flush()

    repository = ValidationLogRepository(db_session)
    result = await repository.get_pending_sync()

    ids = {log.id for log in result}
    assert pending.id in ids
    assert already_synced.id not in ids


async def test_get_pending_sync_orders_oldest_first(db_session) -> None:
    now = datetime.now(timezone.utc)
    older = LocalValidationLog(
        id=uuid.uuid4(), bus_id="bus-01", status="AUTHORIZED", is_offline=False,
        captured_at=now - timedelta(minutes=5),
    )
    newer = LocalValidationLog(
        id=uuid.uuid4(), bus_id="bus-01", status="AUTHORIZED", is_offline=False,
        captured_at=now,
    )
    db_session.add_all([newer, older])
    await db_session.flush()

    repository = ValidationLogRepository(db_session)
    result = await repository.get_pending_sync()

    assert [log.id for log in result] == [older.id, newer.id]


async def test_mark_synced_sets_timestamp_only_for_given_ids(db_session) -> None:
    first = await _make_log(synced=False)
    second = await _make_log(synced=False)
    db_session.add_all([first, second])
    await db_session.flush()

    repository = ValidationLogRepository(db_session)
    await repository.mark_synced([first.id])

    pending_after = await repository.get_pending_sync()
    pending_ids = {log.id for log in pending_after}

    assert first.id not in pending_ids
    assert second.id in pending_ids


async def test_mark_synced_with_empty_list_is_a_no_op(db_session) -> None:
    log = await _make_log(synced=False)
    db_session.add(log)
    await db_session.flush()

    repository = ValidationLogRepository(db_session)
    await repository.mark_synced([])

    pending = await repository.get_pending_sync()
    assert log.id in {row.id for row in pending}
