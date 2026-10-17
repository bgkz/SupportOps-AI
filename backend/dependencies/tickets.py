from fastapi import Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.repositories.tickets_repository import TicketsRepository
from backend.services.tickets_service import TicketsService


def get_tickets_service(
    db: Session = Depends(get_db),  # noqa: B008
) -> TicketsService:
    return TicketsService(tickets_repository=TicketsRepository(db=db))
