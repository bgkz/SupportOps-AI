from uuid import UUID

from backend.exceptions.tickets import IdempotencyConflictError
from backend.models.tickets import Tickets
from backend.repositories.tickets_repository import TicketsRepository
from backend.schemas.tickets import CreateTicketRequest


class TicketsService:
    def __init__(self, tickets_repository: TicketsRepository):
        self.tickets_repo = tickets_repository

    def create_ticket(
        self, request: CreateTicketRequest, idempotency_key: UUID
    ) -> Tickets:
        existing_ticket = self.tickets_repo.get_by_idempotency_key(
            user_id=request.user_id,
            idempotency_key=idempotency_key,
        )

        if existing_ticket is not None:
            if existing_ticket.text != request.text:
                raise IdempotencyConflictError(
                    "Idempotency key already used with a different request"
                )

            return existing_ticket

        return self.tickets_repo.add(
            Tickets(
                user_id=request.user_id,
                text=request.text,
                idempotency_key=idempotency_key,
            )
        )
