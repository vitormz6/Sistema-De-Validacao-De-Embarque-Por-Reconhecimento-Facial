import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.cache.model import LocalFaceEmbedding, LocalPassenger, LocalTicket


class PassengerCacheRepository:
    """Write side of the cache edge-api reads from. Upsert-only — this
    worker never deletes a passenger row locally, even if central stops
    sending it (RFC scope: revocation is expressed via `status`, not by
    central omitting the row from a pull)."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert(
        self,
        *,
        id: uuid.UUID,
        full_name: str,
        document_number: str,
        status: str,
    ) -> LocalPassenger:
        statement = select(LocalPassenger).where(LocalPassenger.id == id)
        result = await self.session.execute(statement)
        row = result.scalar_one_or_none()

        if row is None:
            row = LocalPassenger(
                id=id,
                full_name=full_name,
                document_number=document_number,
                status=status,
            )
            self.session.add(row)
        else:
            row.full_name = full_name
            row.document_number = document_number
            row.status = status
            row.synced_at = datetime.now(timezone.utc)

        await self.session.flush()
        return row


class EmbeddingCacheRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

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
        """
        `active` now arrives from central-api's `EmbeddingSyncItem` instead
        of being implicitly assumed True. Incremental pulls can legitimately
        hand us a revoked (active=False) row — that's exactly how a
        biometric revocation propagates to the edge cache. This worker just
        persists the flag; it's edge-api's own
        `EmbeddingCacheRepository.list_active` (a separate, duplicated
        repository over the same table — see module docstring) that filters
        on it so a revoked embedding stops being offered as a match
        candidate during boarding validation.
        """
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
            row.passenger_id = passenger_id
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
