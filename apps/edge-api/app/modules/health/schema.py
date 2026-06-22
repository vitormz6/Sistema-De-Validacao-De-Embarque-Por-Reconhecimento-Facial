from datetime import datetime

from pydantic import BaseModel


class DeviceStatusResponse(BaseModel):
    status: str
    api: str
    database: str
    vision_service: str
    is_offline: bool
    pending_validations: int


class SyncStatusResponse(BaseModel):
    is_offline: bool
    last_connectivity_check_at: datetime | None
    pending_validations: int
    last_validation_captured_at: datetime | None
