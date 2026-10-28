from uuid import uuid4

import pytest
from pytest import MonkeyPatch
from sqlalchemy.orm import Session, sessionmaker

from backend.exceptions.tickets import TicketRetrievalError
from backend.jobs import get_ticket
from backend.models.tickets import Tickets
from backend.models.users import UserRole, Users


@pytest.fixture
def test_session_factory(db: Session) -> sessionmaker:
    return sessionmaker(
        bind=db.get_bind(),
        join_transaction_mode="create_savepoint",
        expire_on_commit=False,
    )


def test_get_ticket_raises_retrieval_error_when_ticket_not_found(
    test_session_factory: sessionmaker, monkeypatch: MonkeyPatch
) -> None:

    monkeypatch.setattr(
        "backend.jobs.SessionLocal",
        test_session_factory,
    )

    with pytest.raises(TicketRetrievalError, match="wurde nicht gefunden"):
        get_ticket(ticket_id=uuid4())


def test_get_ticket_returns_existing_ticket(
    monkeypatch: MonkeyPatch,
    db: Session,
    test_session_factory: sessionmaker,
) -> None:

    monkeypatch.setattr(
        "backend.jobs.SessionLocal",
        test_session_factory,
    )

    user = Users(
        user_role=UserRole.CUSTOMER,
        email="ticket-test@example.com",
        hashed_password="test-password-hash",
    )
    db.add(user)
    db.flush()

    ticket = Tickets(
        user_id=user.id,
        text="Beispiel Ticket-Text",
    )
    db.add(ticket)
    db.flush()
    ticket_id = ticket.id

    result = get_ticket(ticket_id)

    assert isinstance(result, Tickets)
    assert result.id == ticket_id
    assert result.user_id == user.id
    assert result.text == "Beispiel Ticket-Text"


def test_get_embedding_model_loads_expected_model() -> None:
    from sentence_transformers import SentenceTransformer

    from backend.jobs import get_embedding_model

    model = get_embedding_model()

    assert isinstance(model, SentenceTransformer)
    assert model.tokenizer.name_or_path == (
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )
