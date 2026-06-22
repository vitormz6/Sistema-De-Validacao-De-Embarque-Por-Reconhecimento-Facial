from datetime import datetime, timezone

from app.modules.sync_state.repository import SyncStateRepository


async def test_returns_none_before_first_pull(db_session) -> None:
    repository = SyncStateRepository(db_session)

    assert await repository.get_last_pull_cursor("bus-01") is None


def _as_utc(value: datetime) -> datetime:
    """
    SQLite (unlike Postgres) drops tzinfo on round-trip through a
    `DateTime(timezone=True)` column — this only normalizes the *test*
    DB's read-back value, production Postgres preserves the offset.
    """
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


async def test_set_then_get_round_trips(db_session) -> None:
    repository = SyncStateRepository(db_session)
    cursor = datetime(2026, 6, 21, 12, 0, tzinfo=timezone.utc)

    await repository.set_last_pull_cursor("bus-01", cursor)
    stored = await repository.get_last_pull_cursor("bus-01")

    assert _as_utc(stored) == cursor


async def test_set_twice_updates_in_place(db_session) -> None:
    repository = SyncStateRepository(db_session)
    first = datetime(2026, 6, 21, 12, 0, tzinfo=timezone.utc)
    second = datetime(2026, 6, 21, 13, 0, tzinfo=timezone.utc)

    await repository.set_last_pull_cursor("bus-01", first)
    await repository.set_last_pull_cursor("bus-01", second)

    stored = await repository.get_last_pull_cursor("bus-01")
    assert _as_utc(stored) == second
