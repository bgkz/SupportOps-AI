from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status

from backend.dependencies.tickets import get_tickets_service
from backend.exceptions.orders import OrderRetrievalError
from backend.exceptions.tickets import (
    IdempotencyConflictError,
    TicketApprovalConflictError,
    TicketApprovalPermissionError,
    TicketCreationError,
    TicketRetrievalError,
)
from backend.exceptions.users import UserNotFoundError, UserRetrievalError
from backend.jobs import process_ticket
from backend.redis_queue import job
from backend.schemas.tickets import (
    ApproveTicketRequest,
    CreateTicketRequest,
    TicketResponse,
)
from backend.security.api_key import verify_api_key
from backend.services.tickets_service import TicketsService

router = APIRouter(
    prefix="/tickets",
    dependencies=[Depends(verify_api_key)],
)


@router.post(
    "/{ticket_id}/approval",
    status_code=status.HTTP_200_OK,
    response_model=TicketResponse,
)
def approve_ticket(
    ticket_id: UUID,
    approve_ticket_request: ApproveTicketRequest,
    tickets_service: TicketsService = Depends(get_tickets_service),  # noqa: B008
):
    try:
        return tickets_service.approve_ticket(
            ticket_id=ticket_id, approve_ticket_request=approve_ticket_request
        )
    except UserNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except TicketApprovalPermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error),
        ) from error
    except TicketRetrievalError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error
    except TicketApprovalConflictError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error


@router.get(
    "/{ticket_id}", status_code=status.HTTP_200_OK, response_model=TicketResponse
)
def get_ticket(
    ticket_id: UUID,
    tickets_service: TicketsService = Depends(get_tickets_service),  # noqa: B008
):

    try:
        return tickets_service.get_ticket(ticket_id=ticket_id)

    except TicketRetrievalError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=TicketResponse)
def create_ticket(
    create_ticket_request: CreateTicketRequest,
    idempotency_key: Annotated[UUID, Header(alias="Idempotency-Key")],
    tickets_service: TicketsService = Depends(get_tickets_service),  # noqa: B008
):
    try:
        result = tickets_service.create_ticket(
            request=create_ticket_request,
            idempotency_key=idempotency_key,
        )
        if result.created:
            job.enqueue(process_ticket, result.ticket.id)

        return result.ticket

    except TicketCreationError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error
    except (TicketRetrievalError, UserRetrievalError, OrderRetrievalError) as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error

    except UserNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except IdempotencyConflictError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(error)
        ) from error
