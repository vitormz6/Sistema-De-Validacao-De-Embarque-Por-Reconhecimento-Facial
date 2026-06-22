"""
Intentionally duplicated from central-api's `app/shared/enums.py`: edge-api
and central-api are separate deployable services with no shared package in
this monorepo, and these values must stay identical since validation
events flow from here into central-api's `boarding_validations` table
as-is during sync. If a third service needs them, promoting this to a
shared library becomes worth the extra build complexity — not yet.
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


class ValidationStatus(StrEnum):
    AUTHORIZED = "AUTHORIZED"
    DENIED_NO_ACTIVE_TICKET = "DENIED_NO_ACTIVE_TICKET"
    DENIED_LOW_CONFIDENCE = "DENIED_LOW_CONFIDENCE"
    DENIED_FACE_NOT_FOUND = "DENIED_FACE_NOT_FOUND"
    DENIED_SPOOF_SUSPECTED = "DENIED_SPOOF_SUSPECTED"
    DENIED_PASSENGER_BLOCKED = "DENIED_PASSENGER_BLOCKED"
