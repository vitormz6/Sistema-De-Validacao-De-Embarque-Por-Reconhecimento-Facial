from dataclasses import asdict

from fastapi import APIRouter, Depends, File, UploadFile

from app.core.config import settings
from app.pipeline.face_engine import FaceEngine, get_face_engine
from app.pipeline.service import EmbeddingResult, VisionService
from app.schemas.embedding import EmbeddingGenerateResponse, HealthResponse, ModelsHealthResponse

router = APIRouter(tags=["vision"])


def get_vision_service(
    face_engine: FaceEngine = Depends(get_face_engine),
) -> VisionService:
    return VisionService(face_engine)


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="vision-service",
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
    )


@router.get("/health/models", response_model=ModelsHealthResponse)
async def models_health_check(
    face_engine: FaceEngine = Depends(get_face_engine),
) -> ModelsHealthResponse:
    return ModelsHealthResponse(
        status="ok",
        model_pack=settings.MODEL_PACK_NAME,
        loaded=face_engine.is_loaded(),
    )


@router.post("/embeddings/generate", response_model=EmbeddingGenerateResponse)
async def generate_embedding(
    file: UploadFile = File(...),
    service: VisionService = Depends(get_vision_service),
) -> EmbeddingGenerateResponse:
    image_bytes = await file.read()
    result: EmbeddingResult = service.generate_embedding(image_bytes)
    return EmbeddingGenerateResponse(**asdict(result))
