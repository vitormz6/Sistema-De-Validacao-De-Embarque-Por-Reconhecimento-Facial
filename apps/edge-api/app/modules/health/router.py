import httpx
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.connectivity import ConnectivityTracker, get_connectivity_tracker
from app.database.session import get_db_session
from app.modules.health.schema import DeviceStatusResponse, SyncStatusResponse
from app.modules.validation.repository import ValidationLogRepository

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "edge-api",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


async def _check_database(session: AsyncSession) -> str:
    try:
        await session.execute(text("SELECT 1"))
        return "ok"
    except Exception:  # noqa: BLE001 - health check must never raise
        return "error"


async def _check_vision_service() -> str:
    try:
        async with httpx.AsyncClient(
            base_url=settings.VISION_SERVICE_URL,
            timeout=settings.VISION_SERVICE_TIMEOUT_SECONDS,
            trust_env=False,
        ) as client:
            response = await client.get("/health")
            response.raise_for_status()
            return "ok"
    except httpx.HTTPError:
        return "unreachable"


@router.get("/local/device/status", response_model=DeviceStatusResponse)
async def device_status(
    session: AsyncSession = Depends(get_db_session),
    tracker: ConnectivityTracker = Depends(get_connectivity_tracker),
) -> DeviceStatusResponse:
    database_status = await _check_database(session)
    vision_status = await _check_vision_service()
    await tracker.check_now()

    pending_validations = await ValidationLogRepository(session).count_pending_sync()

    overall_status = "ok" if database_status == "ok" and vision_status == "ok" else "degraded"

    return DeviceStatusResponse(
        status=overall_status,
        api="ok",
        database=database_status,
        vision_service=vision_status,
        is_offline=tracker.is_offline,
        pending_validations=pending_validations,
    )


@router.get("/local/sync/status", response_model=SyncStatusResponse)
async def sync_status(
    session: AsyncSession = Depends(get_db_session),
    tracker: ConnectivityTracker = Depends(get_connectivity_tracker),
) -> SyncStatusResponse:
    """
    Cheaper than `/local/device/status`: reads the last cached connectivity
    result instead of pinging central-api again, so the operator UI can
    poll this frequently for the online/offline indicator without adding
    load. The actual sync `pull`/`push`/`ack` cycle is the sync-worker's
    job — this only reports the local outbox queue depth (RF14).
    """
    log_repository = ValidationLogRepository(session)

    return SyncStatusResponse(
        is_offline=tracker.is_offline,
        last_connectivity_check_at=tracker.checked_at,
        pending_validations=await log_repository.count_pending_sync(),
        last_validation_captured_at=await log_repository.get_last_captured_at(),
    )
