from fastapi import Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.dependencies.users import get_users_service
from backend.repositories.tickets_repository import TicketsRepository
from backend.services.tickets_service import TicketsService
from backend.services.users_service import UsersService


def get_tickets_service(
    db: Session = Depends(get_db),  # noqa: B008
    users_service: UsersService = Depends(get_users_service),  # noqa: B008
) -> TicketsService:
    return TicketsService(
        tickets_repository=TicketsRepository(db=db), users_service=users_service
    )
