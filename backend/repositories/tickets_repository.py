from uuid import UUID

from psycopg.errors import ForeignKeyViolation, NotNullViolation, UniqueViolation
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from backend.exceptions.tickets import (
    DuplicateIdempotencyKeyError,
    TicketCreationError,
    TicketRetrievalError,
)
from backend.exceptions.users import UserNotFoundError
from backend.models.tickets import Tickets


class TicketsRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_ticket(self, ticket_id: UUID) -> Tickets | None:
        try:
            return self.db.get(Tickets, ticket_id)
        except SQLAlchemyError as error:
            self.db.rollback()
            raise TicketRetrievalError("Ticket could not be retrieved") from error

    def get_by_idempotency_key(
        self, user_id: UUID, idempotency_key: UUID
    ) -> Tickets | None:
        statement = select(Tickets).where(
            Tickets.user_id == user_id,
            Tickets.idempotency_key == idempotency_key,
        )

        try:
            return self.db.execute(statement).scalar_one_or_none()
        except SQLAlchemyError as error:
            self.db.rollback()
            raise TicketRetrievalError("Ticket could not be retrieved") from error

    def add(self, ticket: Tickets) -> Tickets:
        try:
            self.db.add(ticket)
            self.db.flush()
            self.db.refresh(ticket)
            self.db.commit()
            return ticket
        except IntegrityError as error:
            self.db.rollback()
            if (
                isinstance(error.orig, UniqueViolation)
                and error.orig.diag.constraint_name
                == "uq_tickets_user_id_idempotency_key"
            ):
                raise DuplicateIdempotencyKeyError(
                    "Idempotency key already exists for this user"
                ) from error
            if (
                isinstance(error.orig, ForeignKeyViolation)
                and error.orig.diag.constraint_name == "tickets_user_id_fkey"
            ):
                raise UserNotFoundError("User not found") from error
            if isinstance(error.orig, NotNullViolation):
                raise TicketCreationError(
                    "Required ticket fields are missing"
                ) from error
            raise TicketCreationError("Ticket could not be created") from error
        except SQLAlchemyError as error:
            self.db.rollback()
            raise TicketCreationError("Ticket could not be created") from error
