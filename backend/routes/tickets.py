from fastapi import APIRouter, Depends, HTTPException, status

from backend.dependencies.tickets import get_tickets_service
from backend.dependencies.users import get_users_service
from backend.exceptions.users import UserNotFoundError
from backend.schemas.tickets import CreateTicketRequest
from backend.security.api_key import verify_api_key
from backend.services.tickets_service import TicketsService
from backend.services.users_service import UsersService

router = APIRouter(
    prefix="/tickets",
    dependencies=[Depends(verify_api_key)],
)


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_ticket(
    create_ticket_request: CreateTicketRequest,
    users_service: UsersService = Depends(get_users_service),  # noqa: B008
    tickets_service: TicketsService = Depends(get_tickets_service),  # noqa: B008
):
    try:
        user = users_service.get_user(user_id=create_ticket_request.user_id)

    except UserNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))
