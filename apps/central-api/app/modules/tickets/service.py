import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationFailedError
from app.modules.passengers.repository import PassengerRepository
from app.modules.tickets.model import Ticket
from app.modules.tickets.repository import TicketRepository
from app.modules.tickets.schema import TicketCreate, TicketUpdate
from app.shared.enums import TicketStatus


class TicketService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = TicketRepository(session)
        self.passenger_repository = PassengerRepository(session)

    async def create_ticket(self, data: TicketCreate) -> Ticket:
        passenger = await self.passenger_repository.get_by_id(data.passenger_id)

        if passenger is None:
            raise NotFoundError("Passenger not found.")

        ticket = Ticket(
            passenger_id=data.passenger_id,
            ticket_type=data.ticket_type.value,
            valid_from=data.valid_from,
            valid_until=data.valid_until,
            status=TicketStatus.ACTIVE.value,
        )

        created_ticket = await self.repository.create(ticket)
        await self.session.commit()

        return created_ticket

    async def get_ticket(self, ticket_id: uuid.UUID) -> Ticket:
        ticket = await self.repository.get_by_id(ticket_id)

        if ticket is None:
            raise NotFoundError("Ticket not found.")

        return ticket

    async def list_tickets(
        self,
        *,
        page: int,
        page_size: int,
        passenger_id: uuid.UUID | None,
        status: TicketStatus | None,
    ) -> tuple[list[Ticket], int]:
        return await self.repository.list(
            page=page,
            page_size=page_size,
            passenger_id=passenger_id,
            status=status,
        )

    async def update_ticket(self, ticket_id: uuid.UUID, data: TicketUpdate) -> Ticket:
        ticket = await self.get_ticket(ticket_id)

        valid_from = data.valid_from if data.valid_from is not None else ticket.valid_from
        valid_until = data.valid_until if data.valid_until is not None else ticket.valid_until

        if valid_until <= valid_from:
            raise ValidationFailedError("valid_until must be after valid_from.")

        if data.ticket_type is not None:
            ticket.ticket_type = data.ticket_type.value

        ticket.valid_from = valid_from
        ticket.valid_until = valid_until

        if data.status is not None:
            ticket.status = data.status.value

        updated_ticket = await self.repository.update(ticket)
        await self.session.commit()

        return updated_ticket

    async def block_ticket(self, ticket_id: uuid.UUID) -> Ticket:
        ticket = await self.get_ticket(ticket_id)
        ticket.status = TicketStatus.BLOCKED.value

        updated_ticket = await self.repository.update(ticket)
        await self.session.commit()

        return updated_ticket

    async def activate_ticket(self, ticket_id: uuid.UUID) -> Ticket:
        ticket = await self.get_ticket(ticket_id)
        ticket.status = TicketStatus.ACTIVE.value

        updated_ticket = await self.repository.update(ticket)
        await self.session.commit()

        return updated_ticket
