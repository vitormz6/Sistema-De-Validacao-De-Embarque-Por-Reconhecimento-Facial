"""
Duplicated from central-api/edge-api's `shared/enums.py` — same reasoning
as edge-api's copy: no shared package between services in this monorepo
yet, and these values are a stable wire contract (central-api's
`/sync/pull` response and `/sync/push` request), not an implementation
detail worth coupling three codebases over.
"""

from enum import StrEnum


class PassengerStatus(StrEnum):
    ACTIVE = "ACTIVE"
    BLOCKED = "BLOCKED"
    INACTIVE = "INACTIVE"


class TicketType(StrEnum):
    SINGLE = "SINGLE"
    MONTHLY = "MONTHLY"
    STUDENT = "STUDENT"
    EMPLOYEE = "EMPLOYEE"
    VALE_TRANSPORTE = "VALE_TRANSPORTE"
    SPECIAL = "SPECIAL"


class TicketStatus(StrEnum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    BLOCKED = "BLOCKED"
    CANCELLED = "CANCELLED"
