from dataclasses import dataclass
from uuid import UUID

from backend.exceptions.tickets import (
    DuplicateIdempotencyKeyError,
    IdempotencyConflictError,
    TicketApprovalConflictError,
    TicketApprovalPermissionError,
    TicketCreationError,
    TicketRetrievalError,
)
from backend.jobs import save_ticket_approval
from backend.models.tickets import Tickets, TicketStatus
from backend.models.users import UserRole, Users
from backend.repositories.tickets_repository import TicketsRepository
from backend.schemas.tickets import ApproveTicketRequest, CreateTicketRequest
from backend.scripts.resume_ticket_workflow import resume_ticket_workflow
from backend.services.orders_service import OrdersService
from backend.services.users_service import UsersService


@dataclass(frozen=True)
class TicketCreationResult:
    ticket: Tickets
    created: bool


class TicketsService:
    def __init__(
        self,
        tickets_repository: TicketsRepository,
        users_service: UsersService,
        orders_service: OrdersService,
    ) -> None:
        self.tickets_repo = tickets_repository
        self.users_service = users_service
        self.orders_service = orders_service

    def approve_ticket(
        self, ticket_id: UUID, approve_ticket_request: ApproveTicketRequest
    ):
        user = self.users_service.get_user(user_id=approve_ticket_request.user_id)
        if user.user_role == UserRole.CUSTOMER:
            raise TicketApprovalPermissionError(
                "You do not have permission to approve or reject this ticket."
            )

        ticket = self.get_ticket(ticket_id=ticket_id)
        if ticket.approved is not None:
            if ticket.approved != approve_ticket_request.approved:
                raise TicketApprovalConflictError(
                    "A different approval decision has already been recorded."
                )
            return ticket

        if ticket.status != TicketStatus.WAITING_FOR_APPROVAL:
            raise TicketApprovalConflictError("This ticket is not awaiting approval.")

        if ticket.reply_draft is None:
            raise TicketApprovalConflictError(
                "This ticket has no reply draft to review."
            )

        result = resume_ticket_workflow(
            ticket_id=ticket_id,
            approved=approve_ticket_request.approved,
        )

        return save_ticket_approval(
            ticket_id=ticket_id,
            approved=result["approved"],
        )

    def get_ticket(self, ticket_id) -> Tickets:
        ticket = self.tickets_repo.get_ticket(ticket_id=ticket_id)
        if ticket is None:
            raise TicketRetrievalError(f"Ticket {ticket_id} not found")
        return ticket

    def _get_existing_ticket(
        self,
        user_id: UUID,
        idempotency_key: UUID,
        request: CreateTicketRequest,
    ) -> Tickets | None:
        ticket = self.tickets_repo.get_by_idempotency_key(
            user_id=user_id,
            idempotency_key=idempotency_key,
        )

        if ticket is None:
            return None

        if ticket.text != request.text or ticket.order_number != (
            request.order_number or None
        ):
            raise IdempotencyConflictError(
                "Idempotency key already used with a different request"
            )

        return ticket

    def create_ticket(
        self,
        create_ticket_request: CreateTicketRequest,
        idempotency_key: UUID,
        current_user: Users,
    ) -> Tickets:
        existing_ticket = self._get_existing_ticket(
            user_id=current_user.id,
            idempotency_key=idempotency_key,
            request=create_ticket_request,
        )

        if existing_ticket is not None:
            return existing_ticket

        if create_ticket_request.order_number:
            self.orders_service.get_order_for_user(
                user_id=current_user.id, order_number=create_ticket_request.order_number
            )

        return self.tickets_repo.add(
            Tickets(
                user_id=current_user.id,
                text=create_ticket_request.text,
                idempotency_key=idempotency_key,
                order_number=create_ticket_request.order_number or None,
            )
        )
