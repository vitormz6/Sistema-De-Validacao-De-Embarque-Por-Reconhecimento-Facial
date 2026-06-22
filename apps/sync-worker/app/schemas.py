"""
Minimal mirror of central-api's `app/modules/sync/schema.py` — only the
fields this worker actually reads or sends, kept as plain pydantic models
so a malformed/unexpected response from central-api fails loudly (via
`SyncUpstreamError`) instead of corrupting the local cache silently.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel


class PassengerPullItem(BaseModel):
    id: uuid.UUID
    full_name: str
    document_number: str
    status: str


class EmbeddingPullItem(BaseModel):
    id: uuid.UUID
    passenger_id: uuid.UUID
    embedding: list[float]
    model_name: str
    model_version: str
    active: bool


class TicketPullItem(BaseModel):
    id: uuid.UUID
    passenger_id: uuid.UUID
    ticket_type: str
    status: str
    valid_from: datetime
    valid_until: datetime


class PullResult(BaseModel):
    cursor: datetime
    passengers: list[PassengerPullItem]
    embeddings: list[EmbeddingPullItem]
    tickets: list[TicketPullItem]


class PushResult(BaseModel):
    accepted: list[str]
    duplicated: list[str]
    rejected: list[dict[str, str]]
