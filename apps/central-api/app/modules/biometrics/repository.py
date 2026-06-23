import uuid
from datetime import datetime, timezone

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.biometrics.model import FaceEmbedding
from app.modules.passengers.model import Passenger
from app.shared.enums import PassengerStatus


class FaceEmbeddingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, embedding: FaceEmbedding) -> FaceEmbedding:
        self.session.add(embedding)
        await self.session.flush()
        await self.session.refresh(embedding)
        return embedding

    async def get_active_by_passenger(self, passenger_id: uuid.UUID) -> FaceEmbedding | None:
        statement = select(FaceEmbedding).where(
            FaceEmbedding.passenger_id == passenger_id,
            FaceEmbedding.active.is_(True),
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_by_passenger(self, passenger_id: uuid.UUID) -> list[FaceEmbedding]:
        statement = (
            select(FaceEmbedding)
            .where(FaceEmbedding.passenger_id == passenger_id)
            .order_by(FaceEmbedding.created_at.desc())
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def list_active(self, since: datetime | None = None) -> list[FaceEmbedding]:
        """
        Used by the sync module (RF06). Same incremental-vs-snapshot rule
        as passengers/tickets, but `FaceEmbedding` has no `updated_at`
        column — only `created_at` (set once) and `revoked_at` (set once,
        when revoked). So an incremental pull must match rows that either
        were CREATED after the cursor (a new enrollment) OR were REVOKED
        after the cursor (re-enrollment, or a block), regardless of their
        current `active` value. Without the `revoked_at` half of this, a
        revoked embedding would never reach the edge again after the pull
        that revoked it, and the old (now-revoked) embedding would keep
        authorizing offline boarding for that passenger indefinitely — the
        most security-sensitive instance of this bug.
        """
        statement = select(FaceEmbedding)

        if since is None:
            # Snapshot: only active embeddings whose passenger is also active.
            # Without the passenger join, an active embedding belonging to a
            # BLOCKED passenger would be included while the passenger itself
            # is excluded from the snapshot — causing a FK violation when the
            # sync-worker tries to upsert the embedding before its passenger.
            statement = (
                statement.join(Passenger, FaceEmbedding.passenger_id == Passenger.id)
                .where(FaceEmbedding.active.is_(True))
                .where(Passenger.status == PassengerStatus.ACTIVE.value)
            )
        else:
            statement = statement.where(
                or_(
                    FaceEmbedding.created_at > since,
                    FaceEmbedding.revoked_at > since,
                )
            )

        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def revoke_active(self, passenger_id: uuid.UUID) -> None:
        active_embedding = await self.get_active_by_passenger(passenger_id)

        if active_embedding is None:
            return

        active_embedding.active = False
        active_embedding.revoked_at = datetime.now(timezone.utc)
        await self.session.flush()

    async def find_nearest(
        self,
        embedding: list[float],
        *,
        passenger_id: uuid.UUID | None = None,
        limit: int = 1,
    ) -> list[tuple[FaceEmbedding, float]]:
        """
        Returns the `limit` closest active embeddings to the given vector,
        paired with their cosine distance (0 = identical, 2 = opposite).
        """
        distance = FaceEmbedding.embedding.cosine_distance(embedding)

        statement = select(FaceEmbedding, distance).where(FaceEmbedding.active.is_(True))

        if passenger_id is not None:
            statement = statement.where(FaceEmbedding.passenger_id == passenger_id)

        statement = statement.order_by(distance.asc()).limit(limit)

        result = await self.session.execute(statement)
        return [(row[0], float(row[1])) for row in result.all()]
