from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_edge_device_key
from app.database.session import get_db_session
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.model import User
from app.modules.sync.schema import (
    SyncAckRequest,
    SyncAckResponse,
    SyncDeviceListResponse,
    SyncPullRequest,
    SyncPullResponse,
    SyncPushRequest,
    SyncPushResponse,
    SyncStatusResponse,
)
from app.modules.sync.service import SyncService

router = APIRouter(
    prefix="/sync",
    tags=["sync"],
    dependencies=[Depends(verify_edge_device_key)],
)

# Separate router (same `/sync` prefix, different auth): the routes above
# authenticate edge *devices* via the shared X-Device-Key secret, but
# Admin Web's dashboard (RF13) is a human admin/operator acting through a
# JWT, not a device. A route can't selectively opt out of a dependency
# declared on its router, hence the second APIRouter instead of bolting
# this onto `router` above.
admin_router = APIRouter(prefix="/sync", tags=["sync"])


def get_sync_service(session: AsyncSession = Depends(get_db_session)) -> SyncService:
    return SyncService(session)


@router.post("/pull", response_model=SyncPullResponse)
async def pull(
    payload: SyncPullRequest,
    service: SyncService = Depends(get_sync_service),
) -> SyncPullResponse:
    return await service.pull(payload.device_id, payload.since)


@router.post("/push", response_model=SyncPushResponse)
async def push(
    payload: SyncPushRequest,
    service: SyncService = Depends(get_sync_service),
) -> SyncPushResponse:
    return await service.push(payload.device_id, payload.events)


@router.post("/ack", response_model=SyncAckResponse)
async def ack(
    payload: SyncAckRequest,
    service: SyncService = Depends(get_sync_service),
) -> SyncAckResponse:
    return await service.ack(payload.device_id, payload.cursor)


@router.get("/status", response_model=SyncStatusResponse)
async def status(
    device_id: str = Query(min_length=1, max_length=64),
    service: SyncService = Depends(get_sync_service),
) -> SyncStatusResponse:
    return await service.status(device_id)


@admin_router.get("/devices", response_model=SyncDeviceListResponse)
async def list_devices(
    service: SyncService = Depends(get_sync_service),
    _current_user: User = Depends(get_current_user),
) -> SyncDeviceListResponse:
    return await service.list_devices()
