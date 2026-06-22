"""
Same tables as edge-api/app/modules/cache/model.py — duplicated model
definitions pointed at the same postgres-edge schema edge-api migrates.
This worker is the only writer for these three tables; edge-api only
reads them when validating a boarding attempt.
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
