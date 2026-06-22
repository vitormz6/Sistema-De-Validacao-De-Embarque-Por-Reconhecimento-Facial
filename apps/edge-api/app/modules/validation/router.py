from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.modules.validation.schema import BoardingValidationResponse
from app.modules.validation.service import BoardingValidationService

router = APIRouter(prefix="/local", tags=["validation"])


def get_validation_service(
    session: AsyncSession = Depends(get_db_session),
) -> BoardingValidationService:
    return BoardingValidationService(session)


@router.post("/validate-boarding", response_model=BoardingValidationResponse)
async def validate_boarding(
    file: UploadFile = File(...),
    service: BoardingValidationService = Depends(get_validation_service),
) -> BoardingValidationResponse:
    image_bytes = await file.read()
    return await service.validate(image_bytes, file.content_type or "application/octet-stream")
