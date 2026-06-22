import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class BoardingValidation(Base):
    """
    Consolidated record of a boarding attempt, synced from the edge (see
    README2 section 5.8 / 6.1). Rows here always originate at the edge and
    arrive through `POST /sync/push`; the central-api never creates them
    directly.
    """

    __tablename__ = "boarding_validations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Idempotency key generated on the edge so retried syncs don't duplicate
    # the same boarding attempt (RF11).
    external_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
    )

    bus_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    route_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    passenger_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("passengers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    ticket_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tickets.id", ondelete="SET NULL"),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    similarity_distance: Mapped[float | None] = mapped_column(Float, nullable=True)
    reason_code: Mapped[str | None] = mapped_column(String(60), nullable=True)

    is_offline: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
