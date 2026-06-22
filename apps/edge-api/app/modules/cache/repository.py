import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.cache.model import LocalFaceEmbedding, LocalPassenger, LocalTicket
from app.shared.enums import TicketStatus


class PassengerCacheRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, passenger_id: uuid.UUID) -> LocalPassenger | None:
        statement = select(LocalPassenger).where(LocalPassenger.id == passenger_id)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def upsert(
        self,
        *,
        id: uuid.UUID,
        full_name: str,
        document_number: str,
        status: str,
    ) -> LocalPassenger:
        """Used by the future sync-worker (and by tests/seed scripts here)."""
        passenger = await self.get_by_id(id)

        if passenger is None:
            passenger = LocalPassenger(
                id=id,
                full_name=full_name,
                document_number=document_number,
                status=status,
            )
            self.session.add(passenger)
        else:
            passenger.full_name = full_name
            passenger.document_number = document_number
            passenger.status = status
            passenger.synced_at = datetime.now(timezone.utc)

        await self.session.flush()
        return passenger


class EmbeddingCacheRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_active(self) -> list[LocalFaceEmbedding]:
        """
        Returns only embeddings whose `active` flag is True. This used to
        return the entire table unconditionally on the assumption that
        central-api only ever syncs down embeddings belonging to passengers
        with active biometrics — that assumption was false for incremental
        pulls: a revoked embedding stays in the local cache forever unless
        something marks it inactive. Sync-worker now persists central's
        `active` flag verbatim (see `EmbeddingPullItem`/`upsert` below), so
        filtering on it here is what actually stops a revoked embedding
        from being offered as a match candidate during boarding validation.
        """
        statement = select(LocalFaceEmbedding).where(LocalFaceEmbedding.active.is_(True))
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def upsert(
        self,
        *,
        id: uuid.UUID,
        passenger_id: uuid.UUID,
        embedding: list[float],
        model_name: str,
        model_version: str,
        active: bool,
    ) -> LocalFaceEmbedding:
        statement = select(LocalFaceEmbedding).where(LocalFaceEmbedding.id == id)
        result = await self.session.execute(statement)
        row = result.scalar_one_or_none()

        if row is None:
            row = LocalFaceEmbedding(
                id=id,
                passenger_id=passenger_id,
                embedding=embedding,
                model_name=model_name,
                model_version=model_version,
                active=active,
            )
            self.session.add(row)
        else:
            row.embedding = embedding
            row.model_name = model_name
            row.model_version = model_version
            row.active = active
            row.synced_at = datetime.now(timezone.utc)

        await self.session.flush()
        return row


class TicketCacheRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_active_for_passenger(
        self, passenger_id: uuid.UUID, *, now: datetime | None = None
    ) -> LocalTicket | None:
        reference_time = now or datetime.now(timezone.utc)

        statement = select(LocalTicket).where(
            LocalTicket.passenger_id == passenger_id,
            LocalTicket.status == TicketStatus.ACTIVE.value,
            LocalTicket.valid_from <= reference_time,
            LocalTicket.valid_until >= reference_time,
        )
        result = await self.session.execute(statement)
        return result.scalars().first()

    async def upsert(
        self,
        *,
        id: uuid.UUID,
        passenger_id: uuid.UUID,
        ticket_type: str,
        status: str,
        valid_from: datetime,
        valid_until: datetime,
    ) -> LocalTicket:
        statement = select(LocalTicket).where(LocalTicket.id == id)
        result = await self.session.execute(statement)
        row = result.scalar_one_or_none()

        if row is None:
            row = LocalTicket(
                id=id,
                passenger_id=passenger_id,
                ticket_type=ticket_type,
                status=status,
                valid_from=valid_from,
                valid_until=valid_until,
            )
            self.session.add(row)
        else:
            row.ticket_type = ticket_type
            row.status = status
            row.valid_from = valid_from
            row.valid_until = valid_until
            row.synced_at = datetime.now(timezone.utc)

        await self.session.flush()
        return row
