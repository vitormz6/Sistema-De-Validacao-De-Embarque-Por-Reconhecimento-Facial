import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.shared.enums import ValidationStatus


class BoardingValidationResponse(BaseModel):
    """
    Shape consumed by the operator UI (README2 section 11): enough to
    render AUTORIZADO / NEGADO / baixa confiança screens with a reason.
    """

    id: uuid.UUID
    status: ValidationStatus
    passenger_id: uuid.UUID | None
    passenger_name: str | None
    ticket_id: uuid.UUID | None
    confidence_score: float | None
    similarity_distance: float | None
    reason_code: str | None
    is_offline: bool
    captured_at: datetime

    model_config = ConfigDict(from_attributes=True)
