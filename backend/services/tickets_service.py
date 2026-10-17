from fastapi import Depends
from sqlalchemy.orm import Session

from backend.repositories.tickets_repository import TicketsRepository


class TicketsService:
    def __init__(self, tickets_repository: TicketsRepository):
        self.tickets_repo = tickets_repository
