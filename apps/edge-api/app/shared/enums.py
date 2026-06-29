# Duplicado do central-api — os dois precisam dos mesmos valores pra o sync funcionar.
# TODO: extrair pra pacote compartilhado se mais serviços precisarem
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
