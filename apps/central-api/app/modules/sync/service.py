from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.biometrics.repository import FaceEmbeddingRepository
from app.modules.passengers.repository import PassengerRepository
from app.modules.sync.model import SyncDeviceState
from app.modules.sync.repository import SyncDeviceRepository
from app.modules.sync.schema import (
    EmbeddingSyncItem,
    PassengerSyncItem,
    SyncAckResponse,
    SyncDeviceListResponse,
    SyncPullResponse,
    SyncPushResponse,
    SyncStatusResponse,
    TicketSyncItem,
)
from app.modules.tickets.repository import TicketRepository
from app.modules.validations.schema import ValidationEventIngest
from app.modules.validations.service import ValidationService


class SyncService:
    """Orquestra os endpoints de sincronização central↔edge (pull/push/ack)."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.device_repository = SyncDeviceRepository(session)
        self.passenger_repository = PassengerRepository(session)
        self.embedding_repository = FaceEmbeddingRepository(session)
        self.ticket_repository = TicketRepository(session)
        self.validation_service = ValidationService(session)

    async def pull(self, device_id: str, since: datetime | None) -> SyncPullResponse:
        passengers = await self.passenger_repository.list_active(since=since)
        embeddings = await self.embedding_repository.list_active(since=since)
        tickets = await self.ticket_repository.list_active(since=since)

        generated_at = datetime.now(timezone.utc)
        await self.device_repository.register_pull(device_id, generated_at)
        await self.session.commit()

        return SyncPullResponse(
            device_id=device_id,
            generated_at=generated_at,
            cursor=generated_at,
            passengers=[
                PassengerSyncItem(
                    id=p.id,
                    full_name=p.full_name,
                    document_number=p.document_number,
                    status=p.status,
                )
                for p in passengers
            ],
            embeddings=[
                EmbeddingSyncItem(
                    id=e.id,
                    passenger_id=e.passenger_id,
                    embedding=list(e.embedding),
                    model_name=e.model_name,
                    model_version=e.model_version,
                    active=e.active,
                )
                for e in embeddings
            ],
            tickets=[
                TicketSyncItem(
                    id=t.id,
                    passenger_id=t.passenger_id,
                    ticket_type=t.ticket_type,
                    status=t.status,
                    valid_from=t.valid_from,
                    valid_until=t.valid_until,
                )
                for t in tickets
            ],
        )

    async def push(
        self, device_id: str, events: list[ValidationEventIngest]
    ) -> SyncPushResponse:
        ingest_result = await self.validation_service.register_events(events)

        await self.device_repository.register_push(device_id, datetime.now(timezone.utc))
        await self.session.commit()

        return SyncPushResponse(device_id=device_id, **ingest_result.model_dump())

    async def ack(self, device_id: str, cursor: datetime) -> SyncAckResponse:
        await self.device_repository.register_ack(device_id, cursor)
        await self.session.commit()

        return SyncAckResponse(
            device_id=device_id,
            cursor=cursor,
            acknowledged_at=datetime.now(timezone.utc),
        )

    async def status(self, device_id: str) -> SyncStatusResponse:
        device_state = await self.device_repository.get(device_id)

        if device_state is None:
            return SyncStatusResponse(
                device_id=device_id,
                registered=False,
                last_pull_at=None,
                last_pull_cursor=None,
                last_push_at=None,
            )

        return _to_status_response(device_state)

    async def list_devices(self) -> SyncDeviceListResponse:
        """Lista todos os devices registrados para o dashboard do admin."""
        device_states = await self.device_repository.list_all()
        return SyncDeviceListResponse(
            devices=[_to_status_response(device_state) for device_state in device_states]
        )


def _to_status_response(device_state: SyncDeviceState) -> SyncStatusResponse:
    return SyncStatusResponse(
        device_id=device_state.device_id,
        registered=True,
        last_pull_at=device_state.last_pull_at,
        last_pull_cursor=device_state.last_pull_cursor,
        last_push_at=device_state.last_push_at,
    )
