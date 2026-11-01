from dataclasses import dataclass
from uuid import UUID

from backend.exceptions.tickets import (
    DuplicateIdempotencyKeyError,
    IdempotencyConflictError,
    TicketCreationError,
)
from backend.models.tickets import Tickets
from backend.repositories.tickets_repository import TicketsRepository
from backend.schemas.tickets import CreateTicketRequest
from backend.services.users_service import UsersService


@dataclass(frozen=True)
class TicketCreationResult:
    ticket: Tickets
    created: bool


class TicketsService:
    def __init__(
        self, tickets_repository: TicketsRepository, users_service: UsersService
    ):
        self.tickets_repo = tickets_repository
        self.users_service = users_service

    def create_ticket(
        self, request: CreateTicketRequest, idempotency_key: UUID
    ) -> TicketCreationResult:
        self.users_service.get_user(user_id=request.user_id)
        existing_ticket = self.tickets_repo.get_by_idempotency_key(
            user_id=request.user_id,
            idempotency_key=idempotency_key,
        )

        if existing_ticket is not None:
            return TicketCreationResult(self._validate_replay(existing_ticket, request), False)

        try:
            ticket = self.tickets_repo.add(
                Tickets(
                    user_id=request.user_id,
                    text=request.text,
                    idempotency_key=idempotency_key,
                )
            )
            return TicketCreationResult(ticket, True)
        except DuplicateIdempotencyKeyError as error:
            existing_ticket = self.tickets_repo.get_by_idempotency_key(
                user_id=request.user_id, idempotency_key=idempotency_key
            )
            if existing_ticket is None:
                raise TicketCreationError("Ticket could not be created") from error
            return TicketCreationResult(self._validate_replay(existing_ticket, request), False)

    @staticmethod
    def _validate_replay(ticket: Tickets, request: CreateTicketRequest) -> Tickets:
        if ticket.text != request.text:
            raise IdempotencyConflictError(
                "Idempotency key already used with a different request"
            )
        return ticket
