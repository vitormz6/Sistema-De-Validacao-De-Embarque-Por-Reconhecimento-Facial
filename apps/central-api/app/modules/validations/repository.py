import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.validations.model import BoardingValidation
from app.shared.enums import ValidationStatus


class ValidationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, validation: BoardingValidation) -> BoardingValidation:
        self.session.add(validation)
        await self.session.flush()
        await self.session.refresh(validation)
        return validation

    async def get_by_id(self, validation_id: uuid.UUID) -> BoardingValidation | None:
        statement = select(BoardingValidation).where(BoardingValidation.id == validation_id)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_external_id(self, external_id: str) -> BoardingValidation | None:
        statement = select(BoardingValidation).where(
            BoardingValidation.external_id == external_id
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        page: int,
        page_size: int,
        status: ValidationStatus | None = None,
        passenger_id: uuid.UUID | None = None,
        bus_id: str | None = None,
        captured_from: datetime | None = None,
        captured_to: datetime | None = None,
    ) -> tuple[list[BoardingValidation], int]:
        filters = []

        if status is not None:
            filters.append(BoardingValidation.status == status.value)

        if passenger_id is not None:
            filters.append(BoardingValidation.passenger_id == passenger_id)

        if bus_id is not None:
            filters.append(BoardingValidation.bus_id == bus_id)

        if captured_from is not None:
            filters.append(BoardingValidation.captured_at >= captured_from)

        if captured_to is not None:
            filters.append(BoardingValidation.captured_at <= captured_to)

        query = select(BoardingValidation)
        count_query = select(func.count()).select_from(BoardingValidation)

        if filters:
            query = query.where(*filters)
            count_query = count_query.where(*filters)

        total_result = await self.session.execute(count_query)
        total = int(total_result.scalar_one())

        query = (
            query.order_by(BoardingValidation.captured_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await self.session.execute(query)
        validations = list(result.scalars().all())

        return validations, total

    async def count_by_status(self) -> dict[str, int]:
        statement = select(BoardingValidation.status, func.count()).group_by(
            BoardingValidation.status
        )
        result = await self.session.execute(statement)
        return {status: count for status, count in result.all()}
