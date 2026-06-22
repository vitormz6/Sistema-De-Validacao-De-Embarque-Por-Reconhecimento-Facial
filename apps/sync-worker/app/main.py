import asyncio

from app.core.config import settings
from app.core.exceptions import SyncUpstreamError
from app.core.logging import configure_logging, get_logger
from app.database.session import session_scope
from app.runner import SyncRunner

logger = get_logger(__name__)


async def run_cycle() -> None:
    async with session_scope() as session:
        runner = SyncRunner(session)

        pulled = await runner.run_pull_cycle()
        pushed = await runner.run_push_cycle()

        logger.info("sync_cycle_completed", pulled=pulled, pushed=pushed)


async def main() -> None:
    configure_logging()
    logger.info("sync_worker_started", bus_id=settings.BUS_ID, interval=settings.SYNC_INTERVAL_SECONDS)

    while True:
        try:
            await run_cycle()
        except SyncUpstreamError as exc:
            # central-api unreachable or rejected the request outright —
            # expected during network outages (the whole reason this is a
            # retry-next-tick loop and not a one-shot script). Nothing is
            # lost: the local outbox (`synced_at IS NULL`) and the pull
            # cursor are untouched until a cycle fully succeeds.
            logger.warning("sync_cycle_failed", error=str(exc))
        except Exception as exc:  # noqa: BLE001 - a single bad cycle must never kill the worker
            logger.error("sync_cycle_unexpected_error", error=str(exc))

        await asyncio.sleep(settings.SYNC_INTERVAL_SECONDS)


if __name__ == "__main__":
    asyncio.run(main())
