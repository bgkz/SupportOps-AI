from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status

from backend.dependencies.tickets import get_tickets_service
from backend.dependencies.users import get_users_service
from backend.exceptions.tickets import IdempotencyConflictError
from backend.exceptions.users import UserNotFoundError
from backend.schemas.tickets import CreateTicketRequest, TicketResponse
from backend.security.api_key import verify_api_key
from backend.services.tickets_service import TicketsService
from backend.services.users_service import UsersService

router = APIRouter(
    prefix="/tickets",
    dependencies=[Depends(verify_api_key)],
)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=TicketResponse)
def create_ticket(
    create_ticket_request: CreateTicketRequest,
    idempotency_key: Annotated[UUID, Header(alias="Idempotency-Key")],
    users_service: UsersService = Depends(get_users_service),  # noqa: B008
    tickets_service: TicketsService = Depends(get_tickets_service),  # noqa: B008
):
    try:
        users_service.get_user(user_id=create_ticket_request.user_id)
        return tickets_service.create_ticket(
            request=create_ticket_request,
            idempotency_key=idempotency_key,
        )
    except UserNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except IdempotencyConflictError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error))
