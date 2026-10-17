from fastapi import APIRouter, Depends, HTTPException, status

from backend.schemas.tickets import CreateTicketRequest
from backend.security.api_key import verify_api_key

router = APIRouter(
    prefix="/tickets",
    dependencies=[Depends(verify_api_key)],
)


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_ticket(create_ticket_request: CreateTicketRequest):
    pass
