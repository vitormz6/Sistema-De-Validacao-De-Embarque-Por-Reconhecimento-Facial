import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.validations.schema import IngestResult, ValidationEventIngest
from app.shared.enums import PassengerStatus, TicketStatus, TicketType


class PassengerSyncItem(BaseModel):
    id: uuid.UUID
    full_name: str
    document_number: str
    status: PassengerStatus


class EmbeddingSyncItem(BaseModel):
    id: uuid.UUID
    passenger_id: uuid.UUID
    embedding: list[float]
    model_name: str
    model_version: str
    active: bool = Field(
        description=(
            "Whether this embedding is the passenger's current active "
            "biometric. Incremental pulls can include revoked (active="
            "False) embeddings too, so the edge can drop them from its "
            "local match candidates instead of keeping a stale one around."
        ),
    )


class TicketSyncItem(BaseModel):
    id: uuid.UUID
    passenger_id: uuid.UUID
    ticket_type: TicketType
    status: TicketStatus
    valid_from: datetime
    valid_until: datetime


class SyncPullRequest(BaseModel):
    device_id: str = Field(min_length=1, max_length=64)
    since: datetime | None = None


class SyncPullResponse(BaseModel):
    device_id: str
    generated_at: datetime
    cursor: datetime
    passengers: list[PassengerSyncItem]
    embeddings: list[EmbeddingSyncItem]
    tickets: list[TicketSyncItem]


class SyncPushRequest(BaseModel):
    device_id: str = Field(min_length=1, max_length=64)
    events: list[ValidationEventIngest]


class SyncPushResponse(IngestResult):
    device_id: str


class SyncAckRequest(BaseModel):
    device_id: str = Field(min_length=1, max_length=64)
    cursor: datetime


class SyncAckResponse(BaseModel):
    device_id: str
    cursor: datetime
    acknowledged_at: datetime


class SyncStatusResponse(BaseModel):
    device_id: str
    registered: bool
    last_pull_at: datetime | None
    last_pull_cursor: datetime | None
    last_push_at: datetime | None


class SyncDeviceListResponse(BaseModel):
    """Backs the Admin Web dashboard's device sync table (RF13)."""

    devices: list[SyncStatusResponse]
