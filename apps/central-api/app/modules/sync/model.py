from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class SyncDeviceState(Base):
    """
    Tracks the sync cursor for each edge device (bus). One row per device,
    upserted on every pull/push/ack cycle (see README2 section 13).
    """

    __tablename__ = "sync_device_state"

    device_id: Mapped[str] = mapped_column(String(64), primary_key=True)

    last_pull_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_pull_cursor: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_push_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

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
