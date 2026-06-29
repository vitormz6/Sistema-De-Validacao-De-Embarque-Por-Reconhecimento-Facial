import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.validations.model import BoardingValidation
from app.modules.validations.repository import ValidationRepository
from app.modules.validations.schema import (
    IngestResult,
    ValidationEventIngest,
    ValidationStatsResponse,
)
from app.shared.enums import ValidationStatus


class ValidationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = ValidationRepository(session)

    async def register_events(self, events: list[ValidationEventIngest]) -> IngestResult:
        """
        Recebe um batch de eventos de embarque vindos do edge.
        Usa external_id para evitar duplicata se o sync tentar de novo.
        """
        result = IngestResult()

        for event in events:
            try:
                existing = await self.repository.get_by_external_id(event.external_id)

                if existing is not None:
                    result.duplicated.append(event.external_id)
                    continue

                validation = BoardingValidation(
                    external_id=event.external_id,
                    bus_id=event.bus_id,
                    route_id=event.route_id,
                    passenger_id=event.passenger_id,
                    ticket_id=event.ticket_id,
                    status=event.status.value,
                    confidence_score=event.confidence_score,
                    similarity_distance=event.similarity_distance,
                    reason_code=event.reason_code,
                    is_offline=event.is_offline,
                    captured_at=event.captured_at,
                    synced_at=datetime.now(timezone.utc),
                )

                await self.repository.create(validation)
                result.accepted.append(event.external_id)
            except Exception as exc:  # noqa: BLE001 - keep the batch resilient
                result.rejected.append({"external_id": event.external_id, "reason": str(exc)})

        await self.session.commit()

        return result

    async def get_validation(self, validation_id: uuid.UUID) -> BoardingValidation:
        validation = await self.repository.get_by_id(validation_id)

        if validation is None:
            raise NotFoundError("Validation not found.")

        return validation

    async def list_validations(
        self,
        *,
        page: int,
        page_size: int,
        status: ValidationStatus | None,
        passenger_id: uuid.UUID | None,
        bus_id: str | None,
        captured_from: datetime | None,
        captured_to: datetime | None,
    ) -> tuple[list[BoardingValidation], int]:
        return await self.repository.list(
            page=page,
            page_size=page_size,
            status=status,
            passenger_id=passenger_id,
            bus_id=bus_id,
            captured_from=captured_from,
            captured_to=captured_to,
        )

    async def get_stats(self) -> ValidationStatsResponse:
        by_status = await self.repository.count_by_status()
        return ValidationStatsResponse(by_status=by_status, total=sum(by_status.values()))
