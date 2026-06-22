import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.model import User
from app.modules.passengers.schema import (
    PassengerCreate,
    PassengerListResponse,
    PassengerResponse,
    PassengerUpdate,
)
from app.modules.passengers.service import PassengerService
from app.shared.enums import PassengerStatus

router = APIRouter(
    prefix="/passengers",
    tags=["passengers"],
)


def get_passenger_service(
    session: AsyncSession = Depends(get_db_session),
) -> PassengerService:
    return PassengerService(session)


@router.post(
    "",
    response_model=PassengerResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_passenger(
    payload: PassengerCreate,
    service: PassengerService = Depends(get_passenger_service),
    _current_user: User = Depends(get_current_user),
) -> PassengerResponse:
    passenger = await service.create_passenger(payload)
    return PassengerResponse.model_validate(passenger)


@router.get(
    "",
    response_model=PassengerListResponse,
)
async def list_passengers(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: PassengerStatus | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None, min_length=1),
    service: PassengerService = Depends(get_passenger_service),
    _current_user: User = Depends(get_current_user),
) -> PassengerListResponse:
    passengers, total = await service.list_passengers(
        page=page,
        page_size=page_size,
        status=status_filter,
        search=search,
    )

    return PassengerListResponse(
        items=[PassengerResponse.model_validate(passenger) for passenger in passengers],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{passenger_id}",
    response_model=PassengerResponse,
)
async def get_passenger(
    passenger_id: uuid.UUID,
    service: PassengerService = Depends(get_passenger_service),
    _current_user: User = Depends(get_current_user),
) -> PassengerResponse:
    passenger = await service.get_passenger(passenger_id)
    return PassengerResponse.model_validate(passenger)


@router.put(
    "/{passenger_id}",
    response_model=PassengerResponse,
)
async def update_passenger(
    passenger_id: uuid.UUID,
    payload: PassengerUpdate,
    service: PassengerService = Depends(get_passenger_service),
    _current_user: User = Depends(get_current_user),
) -> PassengerResponse:
    passenger = await service.update_passenger(passenger_id, payload)
    return PassengerResponse.model_validate(passenger)


@router.post(
    "/{passenger_id}/block",
    response_model=PassengerResponse,
)
async def block_passenger(
    passenger_id: uuid.UUID,
    service: PassengerService = Depends(get_passenger_service),
    _current_user: User = Depends(get_current_user),
) -> PassengerResponse:
    passenger = await service.block_passenger(passenger_id)
    return PassengerResponse.model_validate(passenger)


@router.post(
    "/{passenger_id}/activate",
    response_model=PassengerResponse,
)
async def activate_passenger(
    passenger_id: uuid.UUID,
    service: PassengerService = Depends(get_passenger_service),
    _current_user: User = Depends(get_current_user),
) -> PassengerResponse:
    passenger = await service.activate_passenger(passenger_id)
    return PassengerResponse.model_validate(passenger)