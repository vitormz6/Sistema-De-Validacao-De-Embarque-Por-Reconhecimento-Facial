import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.shared.enums import PassengerStatus


class PassengerCreate(BaseModel):
    full_name: str = Field(min_length=3, max_length=160)
    document_number: str = Field(min_length=3, max_length=32)
    birth_date: date | None = None


class PassengerUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=3, max_length=160)
    document_number: str | None = Field(default=None, min_length=3, max_length=32)
    birth_date: date | None = None
    status: PassengerStatus | None = None


class PassengerResponse(BaseModel):
    id: uuid.UUID
    full_name: str
    document_number: str
    birth_date: date | None
    status: PassengerStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PassengerListResponse(BaseModel):
    items: list[PassengerResponse]
    total: int
    page: int
    page_size: int