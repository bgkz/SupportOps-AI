from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.exceptions.tickets import TicketRetrievalError
from backend.models.tickets import Tickets
from backend.models.users import UserRole, Users
from backend.repositories.tickets_repository import TicketsRepository


def test_get_by_idempotency_key_returns_none_when_ticket_not_found(
    db: Session,
) -> None:
    assert db.scalar(select(func.count()).select_from(Tickets)) == 0

    assert (
        TicketsRepository(db=db).get_by_idempotency_key(
            user_id=uuid4(), idempotency_key=uuid4()
        )
        is None
    )


def test_get_by_idempotency_key_filters_by_user_and_key(db: Session) -> None:
    user = Users(
        email=f"tickets-{uuid4()}@example.com",
        hashed_password="test-hash",
        user_role=UserRole.CUSTOMER,
    )

    other_user = Users(
        email=f"tickets-{uuid4()}@example.com",
        hashed_password="test-hash",
        user_role=UserRole.CUSTOMER,
    )

    expected_idempotency_key = uuid4()

    db.add_all([user, other_user])
    db.flush()

    expected_ticket = Tickets(
        user_id=user.id,
        text="Meine Bestellung AB-0043 ist beschädigt angekommen.",
        order_number="AB-0043",
        idempotency_key=expected_idempotency_key,
    )
    ticket_with_other_key = Tickets(
        user_id=user.id,
        text="Wo bleibt meine Bestellung CD-0044?",
        order_number="CD-0044",
        idempotency_key=uuid4(),
    )
    other_users_ticket = Tickets(
        user_id=other_user.id,
        text="Meine Bestellung EF-0045 wurde doppelt abgebucht.",
        order_number="EF-0045",
        idempotency_key=expected_idempotency_key,
    )
    db.add_all([expected_ticket, ticket_with_other_key, other_users_ticket])
    db.flush()

    tickets_repo = TicketsRepository(db=db)

    result = tickets_repo.get_by_idempotency_key(
        user_id=user.id, idempotency_key=expected_idempotency_key
    )

    assert result is expected_ticket
