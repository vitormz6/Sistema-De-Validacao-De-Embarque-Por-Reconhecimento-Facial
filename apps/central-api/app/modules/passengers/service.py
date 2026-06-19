import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.modules.passengers.model import Passenger
from app.modules.passengers.repository import PassengerRepository
from app.modules.passengers.schema import PassengerCreate, PassengerUpdate
from app.shared.enums import PassengerStatus


class PassengerService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = PassengerRepository(session)

    async def create_passenger(self, data: PassengerCreate) -> Passenger:
        existing_passenger = await self.repository.get_by_document_number(data.document_number)

        if existing_passenger is not None:
            raise ConflictError("A passenger with this document number already exists.")

        passenger = Passenger(
            full_name=data.full_name.strip(),
            document_number=data.document_number.strip(),
            birth_date=data.birth_date,
            status=PassengerStatus.ACTIVE.value,
        )

        created_passenger = await self.repository.create(passenger)
        await self.session.commit()

        return created_passenger

    async def get_passenger(self, passenger_id: uuid.UUID) -> Passenger:
        passenger = await self.repository.get_by_id(passenger_id)

        if passenger is None:
            raise NotFoundError("Passenger not found.")

        return passenger

    async def list_passengers(
        self,
        *,
        page: int,
        page_size: int,
        status: PassengerStatus | None,
        search: str | None,
    ) -> tuple[list[Passenger], int]:
        return await self.repository.list(
            page=page,
            page_size=page_size,
            status=status,
            search=search,
        )

    async def update_passenger(
        self,
        passenger_id: uuid.UUID,
        data: PassengerUpdate,
    ) -> Passenger:
        passenger = await self.get_passenger(passenger_id)

        if data.document_number is not None:
            document_number = data.document_number.strip()

            document_exists = await self.repository.exists_by_document_number(
                document_number=document_number,
                ignore_passenger_id=passenger_id,
            )

            if document_exists:
                raise ConflictError("A passenger with this document number already exists.")

            passenger.document_number = document_number

        if data.full_name is not None:
            passenger.full_name = data.full_name.strip()

        if data.birth_date is not None:
            passenger.birth_date = data.birth_date

        if data.status is not None:
            passenger.status = data.status.value

        updated_passenger = await self.repository.update(passenger)
        await self.session.commit()

        return updated_passenger

    async def block_passenger(self, passenger_id: uuid.UUID) -> Passenger:
        passenger = await self.get_passenger(passenger_id)
        passenger.status = PassengerStatus.BLOCKED.value

        updated_passenger = await self.repository.update(passenger)
        await self.session.commit()

        return updated_passenger

    async def activate_passenger(self, passenger_id: uuid.UUID) -> Passenger:
        passenger = await self.get_passenger(passenger_id)
        passenger.status = PassengerStatus.ACTIVE.value

        updated_passenger = await self.repository.update(passenger)
        await self.session.commit()

        return updated_passenger