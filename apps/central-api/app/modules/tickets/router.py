import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.model import User
from app.modules.tickets.schema import (
    TicketCreate,
    TicketListResponse,
    TicketResponse,
    TicketUpdate,
)
from app.modules.tickets.service import TicketService
from app.shared.enums import TicketStatus

router = APIRouter(prefix="/tickets", tags=["tickets"])


def get_ticket_service(session: AsyncSession = Depends(get_db_session)) -> TicketService:
    return TicketService(session)


@router.post(
    "",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_ticket(
    payload: TicketCreate,
    service: TicketService = Depends(get_ticket_service),
    _current_user: User = Depends(get_current_user),
) -> TicketResponse:
    ticket = await service.create_ticket(payload)
    return TicketResponse.model_validate(ticket)


@router.get("", response_model=TicketListResponse)
async def list_tickets(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    passenger_id: uuid.UUID | None = Query(default=None),
    status_filter: TicketStatus | None = Query(default=None, alias="status"),
    service: TicketService = Depends(get_ticket_service),
    _current_user: User = Depends(get_current_user),
) -> TicketListResponse:
    tickets, total = await service.list_tickets(
        page=page,
        page_size=page_size,
        passenger_id=passenger_id,
        status=status_filter,
    )

    return TicketListResponse(
        items=[TicketResponse.model_validate(ticket) for ticket in tickets],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: uuid.UUID,
    service: TicketService = Depends(get_ticket_service),
    _current_user: User = Depends(get_current_user),
) -> TicketResponse:
    ticket = await service.get_ticket(ticket_id)
    return TicketResponse.model_validate(ticket)


@router.put("/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: uuid.UUID,
    payload: TicketUpdate,
    service: TicketService = Depends(get_ticket_service),
    _current_user: User = Depends(get_current_user),
) -> TicketResponse:
    ticket = await service.update_ticket(ticket_id, payload)
    return TicketResponse.model_validate(ticket)


@router.post("/{ticket_id}/block", response_model=TicketResponse)
async def block_ticket(
    ticket_id: uuid.UUID,
    service: TicketService = Depends(get_ticket_service),
    _current_user: User = Depends(get_current_user),
) -> TicketResponse:
    ticket = await service.block_ticket(ticket_id)
    return TicketResponse.model_validate(ticket)


@router.post("/{ticket_id}/activate", response_model=TicketResponse)
async def activate_ticket(
    ticket_id: uuid.UUID,
    service: TicketService = Depends(get_ticket_service),
    _current_user: User = Depends(get_current_user),
) -> TicketResponse:
    ticket = await service.activate_ticket(ticket_id)
    return TicketResponse.model_validate(ticket)
