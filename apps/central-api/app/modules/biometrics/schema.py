import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BiometricEnrollmentResponse(BaseModel):
    id: uuid.UUID
    passenger_id: uuid.UUID
    model_name: str
    model_version: str
    detector_name: str
    detector_version: str
    quality_score: float
    active: bool
    created_at: datetime
    revoked_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class BiometricCompareResult(BaseModel):
    decision: str
    matched_passenger_id: uuid.UUID | None
    distance: float | None
    similarity: float | None
    threshold: float = Field(description="Maximum cosine distance accepted as a match.")
