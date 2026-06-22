import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.model import User
from app.modules.validations.schema import (
    ValidationListResponse,
    ValidationResponse,
    ValidationStatsResponse,
)
from app.modules.validations.service import ValidationService
from app.shared.enums import ValidationStatus

router = APIRouter(prefix="/validations", tags=["validations"])


def get_validation_service(session: AsyncSession = Depends(get_db_session)) -> ValidationService:
    return ValidationService(session)


@router.get("", response_model=ValidationListResponse)
async def list_validations(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: ValidationStatus | None = Query(default=None, alias="status"),
    passenger_id: uuid.UUID | None = Query(default=None),
    bus_id: str | None = Query(default=None),
    captured_from: datetime | None = Query(default=None),
    captured_to: datetime | None = Query(default=None),
    service: ValidationService = Depends(get_validation_service),
    _current_user: User = Depends(get_current_user),
) -> ValidationListResponse:
    validations, total = await service.list_validations(
        page=page,
        page_size=page_size,
        status=status_filter,
        passenger_id=passenger_id,
        bus_id=bus_id,
        captured_from=captured_from,
        captured_to=captured_to,
    )

    return ValidationListResponse(
        items=[ValidationResponse.model_validate(item) for item in validations],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/stats", response_model=ValidationStatsResponse)
async def get_validation_stats(
    service: ValidationService = Depends(get_validation_service),
    _current_user: User = Depends(get_current_user),
) -> ValidationStatsResponse:
    """
    Backs the Admin Web dashboard (RF13). Registered before
    `/{validation_id}` — otherwise FastAPI would try to parse "stats" as a
    UUID path param and 422 before this handler is ever reached.
    """
    return await service.get_stats()


@router.get("/{validation_id}", response_model=ValidationResponse)
async def get_validation(
    validation_id: uuid.UUID,
    service: ValidationService = Depends(get_validation_service),
    _current_user: User = Depends(get_current_user),
) -> ValidationResponse:
    validation = await service.get_validation(validation_id)
    return ValidationResponse.model_validate(validation)
