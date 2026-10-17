from uuid import UUID

from psycopg.errors import NotNullViolation
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from backend.exceptions.tickets import TicketCreationError
from backend.models.tickets import Tickets


class TicketsRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_idempotency_key(
        self, user_id: UUID, idempotency_key: UUID
    ) -> Tickets | None:
        statement = select(Tickets).where(
            Tickets.user_id == user_id,
            Tickets.idempotency_key == idempotency_key,
        )

        return self.db.execute(statement).scalar_one_or_none()

    def add(self, ticket: Tickets) -> Tickets:
        try:
            self.db.add(ticket)
            self.db.flush()
            self.db.refresh(ticket)
            self.db.commit()
            return ticket
        except IntegrityError as error:
            self.db.rollback()
            if isinstance(error.orig, NotNullViolation):
                raise TicketCreationError(
                    "Required ticket fields are missing"
                ) from error
            raise TicketCreationError("Ticket could not be created")
        except SQLAlchemyError as error:
            self.db.rollback()
            raise TicketCreationError("Ticket could not be created") from error
