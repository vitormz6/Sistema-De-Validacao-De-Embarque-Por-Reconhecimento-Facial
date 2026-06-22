import uuid

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.model import User
from app.modules.biometrics.schema import BiometricCompareResult, BiometricEnrollmentResponse
from app.modules.biometrics.service import BiometricService

router = APIRouter(tags=["biometrics"])


def get_biometric_service(session: AsyncSession = Depends(get_db_session)) -> BiometricService:
    return BiometricService(session)


@router.post(
    "/passengers/{passenger_id}/biometrics/enroll",
    response_model=BiometricEnrollmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def enroll_biometrics(
    passenger_id: uuid.UUID,
    file: UploadFile = File(...),
    service: BiometricService = Depends(get_biometric_service),
    _current_user: User = Depends(get_current_user),
) -> BiometricEnrollmentResponse:
    image_bytes = await file.read()
    embedding = await service.enroll(
        passenger_id,
        image_bytes,
        file.content_type or "application/octet-stream",
    )
    return BiometricEnrollmentResponse.model_validate(embedding)


@router.get(
    "/passengers/{passenger_id}/biometrics",
    response_model=list[BiometricEnrollmentResponse],
)
async def list_biometrics(
    passenger_id: uuid.UUID,
    service: BiometricService = Depends(get_biometric_service),
    _current_user: User = Depends(get_current_user),
) -> list[BiometricEnrollmentResponse]:
    history = await service.list_history(passenger_id)
    return [BiometricEnrollmentResponse.model_validate(item) for item in history]


@router.post(
    "/passengers/{passenger_id}/biometrics/revoke",
    response_model=BiometricEnrollmentResponse,
)
async def revoke_biometrics(
    passenger_id: uuid.UUID,
    service: BiometricService = Depends(get_biometric_service),
    _current_user: User = Depends(get_current_user),
) -> BiometricEnrollmentResponse:
    embedding = await service.revoke(passenger_id)
    return BiometricEnrollmentResponse.model_validate(embedding)


@router.post(
    "/biometrics/compare",
    response_model=BiometricCompareResult,
)
async def compare_biometrics(
    file: UploadFile = File(...),
    passenger_id: uuid.UUID | None = Form(default=None),
    service: BiometricService = Depends(get_biometric_service),
    _current_user: User = Depends(get_current_user),
) -> BiometricCompareResult:
    image_bytes = await file.read()
    return await service.compare(
        image_bytes,
        file.content_type or "application/octet-stream",
        passenger_id=passenger_id,
    )
