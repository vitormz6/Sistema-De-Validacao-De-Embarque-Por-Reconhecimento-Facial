import asyncio
from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.modules.passengers.schema import PassengerCreate, PassengerUpdate
from app.modules.passengers.service import PassengerService
from app.shared.enums import PassengerStatus

pytestmark = pytest.mark.asyncio


async def test_create_passenger(db_session: AsyncSession) -> None:
    service = PassengerService(db_session)

    passenger = await service.create_passenger(
        PassengerCreate(full_name="Joao Silva", document_number="12345678900")
    )

    assert passenger.id is not None
    assert passenger.status == PassengerStatus.ACTIVE.value


async def test_create_passenger_rejects_duplicate_document(db_session: AsyncSession) -> None:
    service = PassengerService(db_session)

    await service.create_passenger(
        PassengerCreate(full_name="Joao Silva", document_number="12345678900")
    )

    with pytest.raises(ConflictError):
        await service.create_passenger(
            PassengerCreate(full_name="Outro Nome", document_number="12345678900")
        )


async def test_get_passenger_not_found_raises(db_session: AsyncSession) -> None:
    service = PassengerService(db_session)

    with pytest.raises(NotFoundError):
        await service.get_passenger(__import__("uuid").uuid4())


async def test_block_and_activate_passenger(db_session: AsyncSession) -> None:
    service = PassengerService(db_session)

    passenger = await service.create_passenger(
        PassengerCreate(full_name="Maria Souza", document_number="98765432100")
    )

    blocked = await service.block_passenger(passenger.id)
    assert blocked.status == PassengerStatus.BLOCKED.value

    activated = await service.activate_passenger(passenger.id)
    assert activated.status == PassengerStatus.ACTIVE.value


async def test_list_active_used_by_sync(db_session: AsyncSession) -> None:
    service = PassengerService(db_session)

    await service.create_passenger(
        PassengerCreate(full_name="Ana Lima", document_number="11122233344")
    )
    p2 = await service.create_passenger(
        PassengerCreate(full_name="Bruno Costa", document_number="55566677788")
    )
    await service.block_passenger(p2.id)

    active_passengers = await service.repository.list_active()

    assert len(active_passengers) == 1
    assert active_passengers[0].document_number == "11122233344"


async def test_list_active_incremental_includes_recently_blocked_passenger(
    db_session: AsyncSession,
) -> None:
    """
    Regression test for the sync-propagation bug: a passenger blocked
    AFTER the sync cursor must still appear in the incremental delta, even
    though they're no longer ACTIVE — otherwise the edge cache never learns
    the passenger was blocked and keeps authorizing their boarding offline
    forever. Only the initial snapshot (`since=None`) should filter by
    status; incremental pulls must rely solely on `updated_at > since`.
    """
    service = PassengerService(db_session)

    untouched = await service.create_passenger(
        PassengerCreate(full_name="Intocado", document_number="33344455566")
    )
    to_block = await service.create_passenger(
        PassengerCreate(full_name="Sera Bloqueado", document_number="77788899900")
    )

    cursor = datetime.now(timezone.utc)
    # SQLite's func.now() (used only in this test DB) has 1s resolution,
    # so we sleep past the second boundary to guarantee the block's
    # updated_at lands strictly after `cursor`. Postgres doesn't need this.
    await asyncio.sleep(1.1)

    blocked = await service.block_passenger(to_block.id)
    assert blocked.status == PassengerStatus.BLOCKED.value

    delta = await service.repository.list_active(since=cursor)
    delta_ids = {p.id for p in delta}

    assert to_block.id in delta_ids
    assert untouched.id not in delta_ids


async def test_update_passenger(db_session: AsyncSession) -> None:
    service = PassengerService(db_session)

    passenger = await service.create_passenger(
        PassengerCreate(full_name="Carlos Dias", document_number="22233344455")
    )

    updated = await service.update_passenger(
        passenger.id, PassengerUpdate(full_name="Carlos Dias Jr.")
    )

    assert updated.full_name == "Carlos Dias Jr."
