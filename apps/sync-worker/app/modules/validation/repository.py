import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.validation.model import LocalValidationLog

DEFAULT_PUSH_BATCH_SIZE = 100


class ValidationLogRepository:
    """
    Read side of edge-api's `local_validation_logs` outbox
    (`synced_at IS NULL`, see edge-api.md). This worker never inserts new
    rows here — only edge-api does, at boarding time.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_pending_sync(
        self, limit: int = DEFAULT_PUSH_BATCH_SIZE
    ) -> list[LocalValidationLog]:
        statement = (
            select(LocalValidationLog)
            .where(LocalValidationLog.synced_at.is_(None))
            .order_by(LocalValidationLog.captured_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def mark_synced(self, log_ids: list[uuid.UUID]) -> None:
        """
        Called only for `accepted` + `duplicated` ids in the push
        response — `rejected` ones stay with `synced_at = NULL` and get
        retried on the next cycle (RF10's "retentativa em caso de falha").
        """
        if not log_ids:
            return

        statement = select(LocalValidationLog).where(LocalValidationLog.id.in_(log_ids))
        result = await self.session.execute(statement)
        synced_at = datetime.now(timezone.utc)

        for row in result.scalars().all():
            row.synced_at = synced_at

        await self.session.flush()
