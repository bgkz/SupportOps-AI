from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status

from backend.dependencies.tickets import get_tickets_service
from backend.exceptions.orders import OrderRetrievalError
from backend.exceptions.tickets import (
    IdempotencyConflictError,
    TicketCreationError,
    TicketRetrievalError,
)
from backend.exceptions.users import UserNotFoundError, UserRetrievalError
from backend.jobs import process_ticket
from backend.redis_queue import job
from backend.schemas.tickets import CreateTicketRequest, TicketResponse
from backend.security.api_key import verify_api_key
from backend.services.tickets_service import TicketsService

router = APIRouter(
    prefix="/tickets",
    dependencies=[Depends(verify_api_key)],
)


@router.get(
    "/{ticket_id}", status_code=status.HTTP_200_OK, response_model=TicketResponse
)
def get_ticket(
    user_id: UUID,
    ticket_id: UUID,
    tickets_service: TicketsService = Depends(get_tickets_service),  # noqa: B008
):

    try:
        return tickets_service.get_ticket(ticket_id=ticket_id, user_id=user_id)
    except UserNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
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
