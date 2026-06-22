import asyncio
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationFailedError
from app.modules.passengers.schema import PassengerCreate
from app.modules.passengers.service import PassengerService
from app.modules.tickets.schema import TicketCreate, TicketUpdate
from app.modules.tickets.service import TicketService
from app.shared.enums import TicketStatus, TicketType


async def _create_passenger(session: AsyncSession):
    return await PassengerService(session).create_passenger(
        PassengerCreate(full_name="Passageiro Teste", document_number="00011122233")
    )


async def test_create_ticket_for_unknown_passenger_raises(db_session: AsyncSession) -> None:
    service = TicketService(db_session)
    now = datetime.now(timezone.utc)

    with pytest.raises(NotFoundError):
        await service.create_ticket(
            TicketCreate(
                passenger_id=uuid.uuid4(),
                ticket_type=TicketType.SINGLE,
                valid_from=now,
                valid_until=now + timedelta(days=1),
            )
        )


async def test_create_ticket_happy_path(db_session: AsyncSession) -> None:
    passenger = await _create_passenger(db_session)
    service = TicketService(db_session)
    now = datetime.now(timezone.utc)

    ticket = await service.create_ticket(
        TicketCreate(
            passenger_id=passenger.id,
            ticket_type=TicketType.MONTHLY,
            valid_from=now,
            valid_until=now + timedelta(days=30),
        )
    )

    assert ticket.status == TicketStatus.ACTIVE.value
    assert ticket.passenger_id == passenger.id


async def test_block_and_activate_ticket(db_session: AsyncSession) -> None:
    passenger = await _create_passenger(db_session)
    service = TicketService(db_session)
    now = datetime.now(timezone.utc)

    ticket = await service.create_ticket(
        TicketCreate(
            passenger_id=passenger.id,
            valid_from=now,
            valid_until=now + timedelta(days=1),
        )
    )

    blocked = await service.block_ticket(ticket.id)
    assert blocked.status == TicketStatus.BLOCKED.value

    active_tickets = await service.repository.list_active_for_passenger(passenger.id)
    assert active_tickets == []

    activated = await service.activate_ticket(ticket.id)
    assert activated.status == TicketStatus.ACTIVE.value


async def test_list_active_incremental_includes_recently_blocked_ticket(
    db_session: AsyncSession,
) -> None:
    """
    Same regression as the passenger case: a ticket blocked AFTER the sync
    cursor must still show up in the incremental delta, even though it's no
    longer ACTIVE, so the edge cache learns the ticket stopped being valid.
    """
    passenger = await _create_passenger(db_session)
    service = TicketService(db_session)
    now = datetime.now(timezone.utc)

    untouched = await service.create_ticket(
        TicketCreate(
            passenger_id=passenger.id,
            ticket_type=TicketType.SINGLE,
            valid_from=now,
            valid_until=now + timedelta(days=1),
        )
    )
    to_block = await service.create_ticket(
        TicketCreate(
            passenger_id=passenger.id,
            ticket_type=TicketType.MONTHLY,
            valid_from=now,
            valid_until=now + timedelta(days=30),
        )
    )

    cursor = datetime.now(timezone.utc)
    # See passenger-side test for why this sleep is needed under SQLite.
    await asyncio.sleep(1.1)

    blocked = await service.block_ticket(to_block.id)
    assert blocked.status == TicketStatus.BLOCKED.value

    delta = await service.repository.list_active(since=cursor)
    delta_ids = {t.id for t in delta}

    assert to_block.id in delta_ids
    assert untouched.id not in delta_ids


async def test_update_ticket_rejects_invalid_window(db_session: AsyncSession) -> None:
    passenger = await _create_passenger(db_session)
    service = TicketService(db_session)
    now = datetime.now(timezone.utc)

    ticket = await service.create_ticket(
        TicketCreate(
            passenger_id=passenger.id,
            valid_from=now,
            valid_until=now + timedelta(days=1),
        )
    )

    with pytest.raises(ValidationFailedError):
        await service.update_ticket(
            ticket.id,
            TicketUpdate(valid_from=now, valid_until=now - timedelta(days=1)),
        )
