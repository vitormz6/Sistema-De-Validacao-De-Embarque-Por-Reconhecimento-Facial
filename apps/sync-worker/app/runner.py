from sqlalchemy.ext.asyncio import AsyncSession

from app.central_client import CentralApiClient
from app.core.config import settings
from app.core.logging import get_logger
from app.modules.cache.repository import (
    EmbeddingCacheRepository,
    PassengerCacheRepository,
    TicketCacheRepository,
)
from app.modules.sync_state.repository import SyncStateRepository
from app.modules.validation.model import LocalValidationLog
from app.modules.validation.repository import ValidationLogRepository

logger = get_logger(__name__)


class SyncRunner:
    """
    Executa um ciclo de pull (central→edge) e um de push (edge→central).
    Os dois commits são independentes — falha no push não desfaz o pull.
    """

    def __init__(self, session: AsyncSession, client: CentralApiClient | None = None) -> None:
        self.session = session
        self.client = client or CentralApiClient()
        self.sync_state_repository = SyncStateRepository(session)
        self.passenger_repository = PassengerCacheRepository(session)
        self.embedding_repository = EmbeddingCacheRepository(session)
        self.ticket_repository = TicketCacheRepository(session)
        self.log_repository = ValidationLogRepository(session)

    async def run_pull_cycle(self) -> int:
        """Returns how many rows were upserted (for logging/metrics)."""
        since = await self.sync_state_repository.get_last_pull_cursor(settings.BUS_ID)

        result = await self.client.pull(since)

        for passenger in result.passengers:
            await self.passenger_repository.upsert(
                id=passenger.id,
                full_name=passenger.full_name,
                document_number=passenger.document_number,
                status=passenger.status,
            )

        for embedding in result.embeddings:
            await self.embedding_repository.upsert(
                id=embedding.id,
                passenger_id=embedding.passenger_id,
                embedding=embedding.embedding,
                model_name=embedding.model_name,
                model_version=embedding.model_version,
                active=embedding.active,
            )

        for ticket in result.tickets:
            await self.ticket_repository.upsert(
                id=ticket.id,
                passenger_id=ticket.passenger_id,
                ticket_type=ticket.ticket_type,
                status=ticket.status,
                valid_from=ticket.valid_from,
                valid_until=ticket.valid_until,
            )

        await self.sync_state_repository.set_last_pull_cursor(settings.BUS_ID, result.cursor)
        await self.session.commit()

        await self.client.ack(result.cursor)

        return len(result.passengers) + len(result.embeddings) + len(result.tickets)

    async def run_push_cycle(self) -> int:
        """Returns how many logs were marked synced (for logging/metrics)."""
        pending = await self.log_repository.get_pending_sync()

        if not pending:
            return 0

        events = [_to_push_event(log) for log in pending]
        result = await self.client.push(events)

        synced_ids = [log.id for log in pending if str(log.id) in result.accepted + result.duplicated]
        await self.log_repository.mark_synced(synced_ids)
        await self.session.commit()

        if result.rejected:
            logger.warning("sync_push_rejected", rejected=result.rejected)

        return len(synced_ids)


def _to_push_event(log: LocalValidationLog) -> dict:
    return {
        "external_id": str(log.id),
        "bus_id": log.bus_id,
        "route_id": log.route_id,
        "passenger_id": str(log.passenger_id) if log.passenger_id else None,
        "ticket_id": str(log.ticket_id) if log.ticket_id else None,
        "status": log.status,
        "confidence_score": log.confidence_score,
        "similarity_distance": log.similarity_distance,
        "reason_code": log.reason_code,
        "is_offline": log.is_offline,
        "captured_at": log.captured_at.isoformat(),
    }
