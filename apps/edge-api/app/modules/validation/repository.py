import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.validation.model import LocalValidationLog


class ValidationLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, log: LocalValidationLog) -> LocalValidationLog:
        self.session.add(log)
        await self.session.flush()
        await self.session.refresh(log)
        return log

    async def get_by_id(self, log_id: uuid.UUID) -> LocalValidationLog | None:
        statement = select(LocalValidationLog).where(LocalValidationLog.id == log_id)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def count_pending_sync(self) -> int:
        """
        `synced_at IS NULL` is this table's outbox queue — see
        `LocalValidationLog`'s docstring for why there's no separate
        `local_sync_outbox` table.
        """
        statement = select(func.count()).select_from(LocalValidationLog).where(
            LocalValidationLog.synced_at.is_(None)
        )
        result = await self.session.execute(statement)
        return int(result.scalar_one())

    async def get_last_captured_at(self):
        statement = select(func.max(LocalValidationLog.captured_at))
        result = await self.session.execute(statement)
        return result.scalar_one()
