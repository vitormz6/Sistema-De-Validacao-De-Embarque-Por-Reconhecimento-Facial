from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.sync.model import SyncDeviceState


class SyncDeviceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, device_id: str) -> SyncDeviceState | None:
        statement = select(SyncDeviceState).where(SyncDeviceState.device_id == device_id)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_or_create(self, device_id: str) -> SyncDeviceState:
        device_state = await self.get(device_id)

        if device_state is not None:
            return device_state

        device_state = SyncDeviceState(device_id=device_id)
        self.session.add(device_state)
        await self.session.flush()
        await self.session.refresh(device_state)
        return device_state

    async def register_pull(self, device_id: str, pulled_at: datetime) -> SyncDeviceState:
        device_state = await self.get_or_create(device_id)
        device_state.last_pull_at = pulled_at
        await self.session.flush()
        return device_state

    async def register_push(self, device_id: str, pushed_at: datetime) -> SyncDeviceState:
        device_state = await self.get_or_create(device_id)
        device_state.last_push_at = pushed_at
        await self.session.flush()
        return device_state

    async def register_ack(self, device_id: str, cursor: datetime) -> SyncDeviceState:
        device_state = await self.get_or_create(device_id)
        device_state.last_pull_cursor = cursor
        await self.session.flush()
        return device_state

    async def list_all(self) -> list[SyncDeviceState]:
        """Backs the Admin Web dashboard's device sync table (RF13)."""
        statement = select(SyncDeviceState).order_by(SyncDeviceState.device_id.asc())
        result = await self.session.execute(statement)
        return list(result.scalars().all())
