"""
Same table as edge-api/app/modules/validation/model.py. edge-api is the
only writer of new rows (one per boarding attempt); this worker is the
only writer of `synced_at` on existing rows once central-api has
accepted them.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class LocalValidationLog(Base):
    __tablename__ = "local_validation_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    bus_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    route_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    passenger_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("local_passengers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    ticket_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("local_tickets.id", ondelete="SET NULL"),
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
        server_default=func.now(),
    )

    synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
