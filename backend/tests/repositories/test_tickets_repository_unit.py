from unittest.mock import Mock
from uuid import uuid4

import pytest
from psycopg.errors import ForeignKeyViolation, NotNullViolation, UniqueViolation
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from backend.exceptions.tickets import (
    DuplicateIdempotencyKeyError, TicketCreationError, TicketRetrievalError,
)
from backend.exceptions.users import UserNotFoundError
from backend.models.tickets import Tickets
from backend.repositories.tickets_repository import TicketsRepository


@pytest.mark.parametrize("operation", ["flush", "commit"])
@pytest.mark.parametrize(
    ("orig_type", "constraint", "expected"),
    [
        (UniqueViolation, "uq_tickets_user_id_idempotency_key", DuplicateIdempotencyKeyError),
        (UniqueViolation, "tickets_pkey", TicketCreationError),
        (UniqueViolation, None, TicketCreationError),
        (ForeignKeyViolation, "tickets_user_id_fkey", UserNotFoundError),
        (ForeignKeyViolation, "other_fkey", TicketCreationError),
        (NotNullViolation, None, TicketCreationError),
    ],
)
def test_add_maps_only_known_constraints(operation, orig_type, constraint, expected):
    db = Mock(spec=Session)
    info = {ord("n"): constraint.encode()} if constraint else None
    orig = orig_type("Insert failed", info=info)
    error = IntegrityError(None, None, orig)
    getattr(db, operation).side_effect = error
    with pytest.raises(expected) as caught:
        TicketsRepository(db).add(Tickets())
    assert caught.value.__cause__ is error
    db.rollback.assert_called_once_with()


def test_lookup_wraps_database_failure():
    db = Mock(spec=Session)
    error = SQLAlchemyError("Database unavailable")
    db.execute.side_effect = error
    with pytest.raises(TicketRetrievalError) as caught:
        TicketsRepository(db).get_by_idempotency_key(uuid4(), uuid4())
    assert caught.value.__cause__ is error
    db.rollback.assert_called_once_with()


def test_add_wraps_database_failure():
    db = Mock(spec=Session)
    db.flush.side_effect = SQLAlchemyError("Database unavailable")
    with pytest.raises(TicketCreationError):
        TicketsRepository(db).add(Tickets())
    db.rollback.assert_called_once_with()
