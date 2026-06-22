import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.shared.enums import ValidationStatus


class ValidationEventIngest(BaseModel):
    """Payload shape sent by the edge `sync-worker` when pushing events."""

    external_id: str = Field(min_length=1, max_length=64)
    bus_id: str = Field(min_length=1, max_length=64)
    route_id: str | None = None
    passenger_id: uuid.UUID | None = None
    ticket_id: uuid.UUID | None = None
    status: ValidationStatus
    confidence_score: float | None = Field(default=None, ge=0, le=1)
    similarity_distance: float | None = Field(default=None, ge=0)
    reason_code: str | None = None
    is_offline: bool = False
    captured_at: datetime


class ValidationResponse(BaseModel):
    id: uuid.UUID
    external_id: str
    bus_id: str
    route_id: str | None
    passenger_id: uuid.UUID | None
    ticket_id: uuid.UUID | None
    status: ValidationStatus
    confidence_score: float | None
    similarity_distance: float | None
    reason_code: str | None
    is_offline: bool
    captured_at: datetime
    synced_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ValidationListResponse(BaseModel):
    items: list[ValidationResponse]
    total: int
    page: int
    page_size: int


class IngestResult(BaseModel):
    accepted: list[str] = Field(default_factory=list)
    duplicated: list[str] = Field(default_factory=list)
    rejected: list[dict[str, str]] = Field(default_factory=list)


class ValidationStatsResponse(BaseModel):
    """Powers the Admin Web dashboard (RF13)."""

    by_status: dict[str, int]
    total: int
