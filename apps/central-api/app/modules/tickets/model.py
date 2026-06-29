import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.shared.enums import TicketStatus, TicketType


class Ticket(Base):
    """Passagem vinculada a um passageiro. Por enquanto sem associação a linha/rota."""

    __tablename__ = "tickets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    passenger_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("passengers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    ticket_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=TicketType.SINGLE.value,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=TicketStatus.ACTIVE.value,
        index=True,
    )

    valid_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    valid_until: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
