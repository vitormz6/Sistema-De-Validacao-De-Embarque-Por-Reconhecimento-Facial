from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.tickets.model import Ticket
from app.shared.enums import TicketStatus


class TicketRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, ticket: Ticket) -> Ticket:
        self.session.add(ticket)
        await self.session.flush()
        await self.session.refresh(ticket)
        return ticket

    async def get_by_id(self, ticket_id: uuid.UUID) -> Ticket | None:
        statement = select(Ticket).where(Ticket.id == ticket_id)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        page: int,
        page_size: int,
        passenger_id: uuid.UUID | None = None,
        status: TicketStatus | None = None,
    ) -> tuple[list[Ticket], int]:
        filters = []

        if passenger_id is not None:
            filters.append(Ticket.passenger_id == passenger_id)

        if status is not None:
            filters.append(Ticket.status == status.value)

        query = select(Ticket)
        count_query = select(func.count()).select_from(Ticket)

        if filters:
            query = query.where(*filters)
            count_query = count_query.where(*filters)

        total_result = await self.session.execute(count_query)
        total = int(total_result.scalar_one())

        query = (
            query.order_by(Ticket.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await self.session.execute(query)
        tickets = list(result.scalars().all())

        return tickets, total

    async def list_active_for_passenger(self, passenger_id: uuid.UUID) -> list[Ticket]:
        statement = select(Ticket).where(
            Ticket.passenger_id == passenger_id,
            Ticket.status == TicketStatus.ACTIVE.value,
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def list_active(self, since: datetime | None = None) -> list[Ticket]:
        """
        Used by the sync module (RF06). Same rule as
        `PassengerRepository.list_active`: the initial snapshot
        (`since=None`) only sends currently-active tickets, but incremental
        pulls must ignore status entirely and rely on `updated_at > since`
        — otherwise a ticket that gets cancelled/expired drops out of every
        future delta and the edge cache keeps treating it as valid forever.
        """
        statement = select(Ticket)

        if since is None:
            statement = statement.where(Ticket.status == TicketStatus.ACTIVE.value)
        else:
            statement = statement.where(Ticket.updated_at > since)

        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def update(self, ticket: Ticket) -> Ticket:
        await self.session.flush()
        await self.session.refresh(ticket)
        return ticket
