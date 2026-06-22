from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class LocalSyncState(Base):
    """
    One row per device (in practice, one row total — a bus only ever
    syncs as itself). Tracks the cursor central-api handed back on the
    last successful pull, so the next pull only asks for what changed
    since then (`SyncPullRequest.since`).
    """

    __tablename__ = "local_sync_state"

    device_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    last_pull_cursor: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
