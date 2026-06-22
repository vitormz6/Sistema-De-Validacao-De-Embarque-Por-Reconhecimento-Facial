from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.sync_state.model import LocalSyncState


class SyncStateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_last_pull_cursor(self, device_id: str) -> datetime | None:
        statement = select(LocalSyncState).where(LocalSyncState.device_id == device_id)
        result = await self.session.execute(statement)
        row = result.scalar_one_or_none()
        return row.last_pull_cursor if row else None

    async def set_last_pull_cursor(self, device_id: str, cursor: datetime) -> None:
        statement = select(LocalSyncState).where(LocalSyncState.device_id == device_id)
        result = await self.session.execute(statement)
        row = result.scalar_one_or_none()

        if row is None:
            row = LocalSyncState(device_id=device_id, last_pull_cursor=cursor)
            self.session.add(row)
        else:
            row.last_pull_cursor = cursor
            row.updated_at = datetime.now(timezone.utc)

        await self.session.flush()
