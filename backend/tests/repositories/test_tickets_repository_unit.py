from unittest.mock import Mock, call
from uuid import uuid4

import pytest
from psycopg.errors import (
    CheckViolation,
    ForeignKeyViolation,
    NotNullViolation,
    UniqueViolation,
)
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
from backend.repositories.tickets_repository import TicketsRepository


@pytest.mark.parametrize("operation", ["flush", "refresh", "commit"])
@pytest.mark.parametrize(
    ("original_type", "constraint", "expected_exception", "expected_message"),
    [
        pytest.param(
            UniqueViolation,
            "uq_tickets_user_id_idempotency_key",
            DuplicateIdempotencyKeyError,
            "Idempotency key already exists for this user",
            id="duplicate-idempotency-key",
        ),
        pytest.param(
            ForeignKeyViolation,
            "tickets_user_id_fkey",
            UserNotFoundError,
            "User not found",
            id="missing-user",
        ),
        pytest.param(
            NotNullViolation,
            None,
            TicketCreationError,
            "Required ticket fields are missing",
            id="missing-required-field",
        ),
        pytest.param(
            UniqueViolation,
            "tickets_pkey",
            TicketCreationError,
            "Ticket could not be created",
            id="other-unique-constraint",
        ),
        pytest.param(
            UniqueViolation,
            None,
            TicketCreationError,
            "Ticket could not be created",
            id="unique-without-constraint",
        ),
        pytest.param(
            ForeignKeyViolation,
            "other_fkey",
            TicketCreationError,
            "Ticket could not be created",
            id="other-foreign-key",
        ),
        pytest.param(
            ForeignKeyViolation,
            None,
            TicketCreationError,
            "Ticket could not be created",
            id="foreign-key-without-constraint",
        ),
        pytest.param(
            CheckViolation,
            None,
            TicketCreationError,
            "Ticket could not be created",
            id="check-violation",
        ),
        pytest.param(
            Exception,
            None,
            TicketCreationError,
            "Ticket could not be created",
            id="other-integrity-error",
        ),
    ],
)
def test_add_maps_integrity_errors_to_domain_exceptions(
    operation: str,
    original_type: type[Exception],
    constraint: str | None,
    expected_exception: type[Exception],
    expected_message: str,
) -> None:
    db = Mock(spec=Session)
    if constraint is not None:
        original_error = original_type(
            "Insert failed", info={ord("n"): constraint.encode()}
        )
    else:
        original_error = original_type("Insert failed")
    error = IntegrityError(statement=None, params=None, orig=original_error)
    getattr(db, operation).side_effect = error
    repo = TicketsRepository(db=db)
    ticket = Tickets(user_id=uuid4(), text="Meine Bestellung fehlt.")

    with pytest.raises(expected_exception) as exc_info:
        repo.add(ticket)

    assert str(exc_info.value) == expected_message
    assert exc_info.value.__cause__ is error
    calls = [call.add(ticket), call.flush(), call.refresh(ticket), call.commit()]
    failed_call_index = ["add", "flush", "refresh", "commit"].index(operation)
    assert db.mock_calls == calls[: failed_call_index + 1] + [call.rollback()]


@pytest.mark.parametrize("operation", ["add", "flush", "refresh", "commit"])
def test_add_maps_database_error_to_creation_error(operation: str) -> None:
    db = Mock(spec=Session)
    error = SQLAlchemyError("Database operation failed")
    getattr(db, operation).side_effect = error
    repo = TicketsRepository(db=db)
    ticket = Tickets(user_id=uuid4(), text="Meine Bestellung fehlt.")

    with pytest.raises(TicketCreationError) as exc_info:
        repo.add(ticket)

    assert str(exc_info.value) == "Ticket could not be created"
    assert exc_info.value.__cause__ is error
    calls = [call.add(ticket), call.flush(), call.refresh(ticket), call.commit()]
    failed_call_index = ["add", "flush", "refresh", "commit"].index(operation)
    assert db.mock_calls == calls[: failed_call_index + 1] + [call.rollback()]


def test_add_persists_and_returns_ticket() -> None:
    db = Mock(spec=Session)
    tickets_repo = TicketsRepository(db=db)

    expected_ticket = Tickets(
        user_id=uuid4(),
        text="Meine Bestellung AB-0043 ist beschädigt angekommen.",
        order_number="AB-0043",
        idempotency_key=uuid4(),
    )

    ticket_added = tickets_repo.add(ticket=expected_ticket)

    assert expected_ticket is ticket_added
    assert db.mock_calls == [
        call.add(expected_ticket),
        call.flush(),
        call.refresh(expected_ticket),
        call.commit(),
    ]


def test_get_by_idempotency_key_returns_none() -> None:
    db = Mock(spec=Session)
    db.execute.return_value.scalar_one_or_none.return_value = None

    tickets_repo = TicketsRepository(db=db)

    assert (
        tickets_repo.get_by_idempotency_key(user_id=uuid4(), idempotency_key=uuid4())
        is None
    )

    db.execute.assert_called_once()
    db.rollback.assert_not_called()


def test_get_by_idempotency_key_filters_by_user_and_key_and_returns_ticket() -> None:
    user_id = uuid4()
    idempotency_key = uuid4()
    db = Mock(spec=Session)
    ticket = Tickets(
        user_id=user_id,
        idempotency_key=idempotency_key,
        text="Meine Bestellung fehlt.",
    )
    db.execute.return_value.scalar_one_or_none.return_value = ticket

    tickets_repo = TicketsRepository(db=db)

    result = tickets_repo.get_by_idempotency_key(
        user_id=user_id, idempotency_key=idempotency_key
    )

    assert result is ticket
    db.execute.assert_called_once()
    actual_statement = db.execute.call_args.args[0]
    expected_statement = select(Tickets).where(
        Tickets.user_id == user_id,
        Tickets.idempotency_key == idempotency_key,
    )
    assert actual_statement.compare(expected_statement)
    db.execute.return_value.scalar_one_or_none.assert_called_once_with()
    db.rollback.assert_not_called()


def test_get_by_idempotency_key_maps_database_error_to_retrieval_error() -> None:
    db = Mock(spec=Session)
    db.execute.side_effect = SQLAlchemyError

    tickets_repo = TicketsRepository(db=db)

    with pytest.raises(
        TicketRetrievalError, match="Ticket could not be retrieved"
    ) as exc_info:
        tickets_repo.get_by_idempotency_key(idempotency_key=uuid4(), user_id=uuid4())

    db.rollback.assert_called_once()

    assert isinstance(exc_info.value.__cause__, SQLAlchemyError)
