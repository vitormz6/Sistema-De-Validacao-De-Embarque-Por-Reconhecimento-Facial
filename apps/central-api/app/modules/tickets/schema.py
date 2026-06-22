import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.shared.enums import TicketStatus, TicketType


class TicketCreate(BaseModel):
    passenger_id: uuid.UUID
    ticket_type: TicketType = TicketType.SINGLE
    valid_from: datetime
    valid_until: datetime

    @model_validator(mode="after")
    def validate_validity_window(self) -> "TicketCreate":
        if self.valid_until <= self.valid_from:
            raise ValueError("valid_until must be after valid_from.")
        return self


class TicketUpdate(BaseModel):
    ticket_type: TicketType | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    status: TicketStatus | None = None


class TicketResponse(BaseModel):
    id: uuid.UUID
    passenger_id: uuid.UUID
    ticket_type: TicketType
    status: TicketStatus
    valid_from: datetime
    valid_until: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TicketListResponse(BaseModel):
    items: list[TicketResponse]
    total: int
    page: int
    page_size: int = Field(le=100)
