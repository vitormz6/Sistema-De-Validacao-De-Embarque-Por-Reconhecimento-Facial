"""
Read-mostly local cache of what the central API synced down (RF06). Rows
here are upserted by the (not yet implemented) `sync-worker`; edge-api
itself only reads from these tables when deciding on a boarding attempt.

IDs are NOT locally generated — they're the same UUIDs central-api uses,
so a synced row can be safely re-upserted (matched by `id`) without
creating duplicates.
"""

import uuid
from datetime import datetime

from sqlalchemy import ARRAY, Boolean, DateTime, Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.shared.enums import PassengerStatus, TicketStatus, TicketType


class LocalPassenger(Base):
    __tablename__ = "local_passengers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)

    full_name: Mapped[str] = mapped_column(String(160), nullable=False)
    document_number: Mapped[str] = mapped_column(String(32), nullable=False)

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=PassengerStatus.ACTIVE.value,
        index=True,
    )

    synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class LocalFaceEmbedding(Base):
    """
    No pgvector here on purpose — `postgres-edge` is a plain Postgres
    instance (see docker-compose.yml) and a single bus's active passenger
    list is small enough that a linear NumPy cosine-distance scan
    (app/modules/cache/matching.py) is plenty fast without an ANN index.
    """

    __tablename__ = "local_face_embeddings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)

    passenger_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("local_passengers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    embedding: Mapped[list[float]] = mapped_column(ARRAY(Float), nullable=False)

    model_name: Mapped[str] = mapped_column(String(60), nullable=False)
    model_version: Mapped[str] = mapped_column(String(60), nullable=False)

    # Mirrors central-api's `FaceEmbedding.active`. Sync-worker writes this
    # from the `EmbeddingSyncItem.active` field on every pull — including
    # incremental pulls for embeddings that were just revoked. Without this
    # column, a revoked embedding had no way to ever stop being offered as
    # a local match candidate once cached — see `EmbeddingCacheRepository.
    # list_active` below, and central-api.md / edge-api.md for the full
    # writeup of the bug this fixes.
    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class LocalTicket(Base):
    __tablename__ = "local_tickets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)

    passenger_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("local_passengers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    ticket_type: Mapped[str] = mapped_column(
        String(30), nullable=False, default=TicketType.SINGLE.value
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=TicketStatus.ACTIVE.value,
        index=True,
    )

    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
