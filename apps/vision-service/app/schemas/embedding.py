from pydantic import BaseModel


class EmbeddingGenerateResponse(BaseModel):
    """
    Contract consumed by central-api's `app/modules/biometrics/vision_client.py`
    (`FaceEmbeddingResult`) — keep both in sync if this shape changes.
    """

    face_found: bool
    embedding: list[float] | None = None
    quality_score: float | None = None
    liveness_score: float | None = None
    spoof_suspected: bool | None = None
    model_name: str | None = None
    model_version: str | None = None
    detector_name: str | None = None
    detector_version: str | None = None
    reason: str | None = None


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    environment: str


class ModelsHealthResponse(BaseModel):
    status: str
    model_pack: str
    loaded: bool
