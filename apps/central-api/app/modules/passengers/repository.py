import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.passengers.model import Passenger
from app.shared.enums import PassengerStatus


class PassengerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, passenger: Passenger) -> Passenger:
        self.session.add(passenger)
        await self.session.flush()
        await self.session.refresh(passenger)
        return passenger

    async def get_by_id(self, passenger_id: uuid.UUID) -> Passenger | None:
        statement = select(Passenger).where(Passenger.id == passenger_id)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_document_number(self, document_number: str) -> Passenger | None:
        statement = select(Passenger).where(Passenger.document_number == document_number)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        page: int,
        page_size: int,
        status: PassengerStatus | None = None,
        search: str | None = None,
    ) -> tuple[list[Passenger], int]:
        filters = []

        if status is not None:
            filters.append(Passenger.status == status.value)

        if search:
            search_value = f"%{search.strip()}%"
            filters.append(Passenger.full_name.ilike(search_value))

        query = select(Passenger)

        if filters:
            query = query.where(*filters)

        count_query = select(func.count()).select_from(Passenger)

        if filters:
            count_query = count_query.where(*filters)

        total_result = await self.session.execute(count_query)
        total = int(total_result.scalar_one())

        query = (
            query.order_by(Passenger.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await self.session.execute(query)
        passengers = list(result.scalars().all())

        return passengers, total

    async def update(self, passenger: Passenger) -> Passenger:
        await self.session.flush()
        await self.session.refresh(passenger)
        return passenger

    async def exists_by_document_number(
        self,
        document_number: str,
        ignore_passenger_id: uuid.UUID | None = None,
    ) -> bool:
        statement = select(Passenger.id).where(Passenger.document_number == document_number)

        if ignore_passenger_id is not None:
            statement = statement.where(Passenger.id != ignore_passenger_id)

        result = await self.session.execute(statement)
        return result.scalar_one_or_none() is not None