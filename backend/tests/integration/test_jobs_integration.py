from collections.abc import Iterator
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from pytest import MonkeyPatch
from sqlalchemy.orm import Session, sessionmaker

from backend.exceptions.tickets import TicketApprovalConflictError, TicketRetrievalError
from backend.jobs import (
    get_ticket,
    process_ticket,
    save_ticket_approval,
    save_workflow_result,
)
from backend.models.tickets import TicketCategories, Tickets, TicketStatus
from backend.models.users import UserRole, Users


@pytest.fixture
def test_session_factory(db: Session) -> sessionmaker:
    return sessionmaker(
        bind=db.get_bind(),
        join_transaction_mode="create_savepoint",
        expire_on_commit=False,
    )


@pytest.mark.parametrize(
    (
        "ticket_status",
        "reply_draft",
        "stored_approval",
        "approved",
        "expected_exception",
        "expected_message",
    ),
    [
        pytest.param(
            None,
            "Beispiel draft",
            None,
            True,
            TicketRetrievalError,
            "wurde nicht gefunden",
            id="ticket-not-found",
        ),
        *[
            pytest.param(
                status,
                "Beispiel draft",
                None,
                True,
                TicketApprovalConflictError,
                r"Das Ticket wartet nicht auf Freigabe\.",
                id=f"invalid-status-{status.value}",
            )
            for status in (
                TicketStatus.PENDING,
                TicketStatus.PROCESSING,
                TicketStatus.ESCALATED,
                TicketStatus.RESOLVED,
            )
        ],
        pytest.param(
            TicketStatus.WAITING_FOR_APPROVAL,
            None,
            None,
            True,
            TicketApprovalConflictError,
            r"Es gibt keinen Antwortentwurf zur Freigabe\.",
            id="missing-reply-draft",
        ),
        pytest.param(
            TicketStatus.WAITING_FOR_APPROVAL,
            "Beispiel draft",
            True,
            False,
            TicketApprovalConflictError,
            r"A different approval decision has already been recorded\.",
            id="reject-previously-approved-ticket",
        ),
        pytest.param(
            TicketStatus.WAITING_FOR_APPROVAL,
            "Beispiel draft",
            False,
            True,
            TicketApprovalConflictError,
            r"A different approval decision has already been recorded\.",
            id="approve-previously-rejected-ticket",
        ),
    ],
)
def test_save_ticket_approval_raises_errors_when_ticket_is_invalid(
    test_session_factory: sessionmaker,
    monkeypatch: MonkeyPatch,
    db: Session,
    ticket_status: TicketStatus | None,
    reply_draft: str | None,
    stored_approval: bool | None,
    approved: bool,
    expected_exception: type[Exception],
    expected_message: str,
) -> None:

    monkeypatch.setattr(
        "backend.jobs.SessionLocal",
        test_session_factory,
    )

    ticket_id = uuid4()

    if ticket_status is not None:
        user = Users(
            user_role=UserRole.CUSTOMER,
            email="ticket-test@example.com",
            hashed_password="test-password-hash",
        )
        db.add(user)
        db.flush()

        ticket = Tickets(
            id=ticket_id,
            user_id=user.id,
            text="Meine Bestellung ist noch nicht angekommen.",
            status=ticket_status,
            reply_draft=reply_draft,
            approved=stored_approval,
        )
        db.add(ticket)
        db.flush()

    with pytest.raises(expected_exception, match=expected_message):
        save_ticket_approval(ticket_id=ticket_id, approved=approved)

    db.expunge_all()
    stored = db.get(Tickets, ticket_id)
    if ticket_status is None:
        assert stored is None
    else:
        assert stored is not None
        assert stored.approved is stored_approval


@pytest.mark.parametrize(
    ("stored_approval", "approved"),
    [
        pytest.param(None, True, id="approve-undecided-ticket"),
        pytest.param(None, False, id="reject-undecided-ticket"),
        pytest.param(True, True, id="repeat-approval"),
        pytest.param(False, False, id="repeat-rejection"),
    ],
)
def test_save_ticket_approval_saves_approval(
    test_session_factory: sessionmaker,
    monkeypatch: MonkeyPatch,
    db: Session,
    stored_approval: bool | None,
    approved: bool,
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
    ticket_id = uuid4()
    ticket = Tickets(
        id=ticket_id,
        user_id=user.id,
        text="Meine Bestellung ist noch nicht angekommen.",
        status=TicketStatus.WAITING_FOR_APPROVAL,
        reply_draft="Beispiel draft",
        approved=stored_approval,
    )

    db.add(ticket)
    db.flush()

    result = save_ticket_approval(ticket_id=ticket.id, approved=approved)

    assert result.id == ticket_id
    assert result.approved is approved

    db.expunge_all()
    stored = db.get(Tickets, ticket_id)

    assert stored is not None
    assert stored.approved is approved


@pytest.mark.parametrize(
    "ticket_status",
    [
        TicketStatus.WAITING_FOR_APPROVAL,
        TicketStatus.ESCALATED,
        TicketStatus.PROCESSING,
        TicketStatus.RESOLVED,
    ],
)
def test_save_workflow_result_keeps_non_pending_ticket_unchanged(
    test_session_factory: sessionmaker,
    monkeypatch: MonkeyPatch,
    ticket_status: TicketStatus,
    db: Session,
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
        text="Meine Bestellung ist noch nicht angekommen.",
        status=ticket_status,
    )

    db.add(ticket)
    db.flush()

    ticket_id = ticket.id
    user_id = user.id

    db.expunge_all()
    ticket_updated = Tickets(
        id=ticket_id,
        user_id=user_id,
        category=TicketCategories.SHIPPING_STATUS,
        status=TicketStatus.WAITING_FOR_APPROVAL,
        order_number="ORD-12345",
    )

    result = save_workflow_result(ticket=ticket_updated)

    assert result.id == ticket_id
    assert result.status == ticket_status
    assert result.category is None
    assert result.order_number is None

    stored = db.get(Tickets, ticket_id)
    assert stored is not None
    assert stored.status == ticket_status
    assert stored.category is None
    assert stored.order_number is None


def test_save_workflow_result_raises_error_when_ticket_not_found(
    test_session_factory: sessionmaker, monkeypatch: MonkeyPatch
) -> None:

    monkeypatch.setattr(
        "backend.jobs.SessionLocal",
        test_session_factory,
    )

    with pytest.raises(TicketRetrievalError, match="wurde nicht gefunden."):
        save_workflow_result(ticket=Tickets(id=uuid4(), user_id=uuid4()))


def test_save_workflow_result_persists_workflow_fields(
    test_session_factory: sessionmaker, monkeypatch: MonkeyPatch, db: Session
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
        text="Meine Bestellung ist noch nicht angekommen.",
        status=TicketStatus.PENDING,
    )
    db.add(ticket)
    db.flush()

    ticket_id = ticket.id
    user_id = user.id
    db.expunge_all()

    ticket_updated = Tickets(
        id=ticket_id,
        user_id=user_id,
        text="Meine Bestellung ist noch nicht angekommen. ORD-12345",
        category=TicketCategories.SHIPPING_STATUS,
        status=TicketStatus.WAITING_FOR_APPROVAL,
        order_number="ORD-12345",
        reply_draft={"text": "Wir prüfen den Versandstatus Ihrer Bestellung."},
        knowledge_sources=[],
        review_reason="Antwort benötigt eine Freigabe.",
    )

    result = save_workflow_result(ticket=ticket_updated)

    assert result.id == ticket_id
    assert result.category == TicketCategories.SHIPPING_STATUS
    assert result.status == TicketStatus.WAITING_FOR_APPROVAL
    assert result.reply_draft == ticket_updated.reply_draft
    assert result.knowledge_sources == []
    assert result.review_reason == ticket_updated.review_reason
    assert result.order_number == "ORD-12345"

    stored = db.get(Tickets, ticket_id)
    assert stored is not None

    assert stored.category == TicketCategories.SHIPPING_STATUS
    assert stored.status == TicketStatus.WAITING_FOR_APPROVAL
    assert stored.reply_draft == ticket_updated.reply_draft
    assert stored.knowledge_sources == []
    assert stored.review_reason == ticket_updated.review_reason
    assert stored.text == "Meine Bestellung ist noch nicht angekommen."
    assert stored.user_id == user_id
    assert stored.order_number == "ORD-12345"


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


@pytest.fixture
def process_ticket_record(
    db: Session, monkeypatch: MonkeyPatch, test_session_factory: sessionmaker
) -> Tickets:
    monkeypatch.setattr("backend.jobs.SessionLocal", test_session_factory)
    user = Users(
        user_role=UserRole.CUSTOMER,
        email="process-ticket@example.com",
        hashed_password="test-password-hash",
    )
    db.add(user)
    db.flush()
    ticket = Tickets(
        user_id=user.id,
        text="Meine Bestellung ist noch nicht angekommen.",
        status=TicketStatus.PENDING,
    )
    db.add(ticket)
    db.flush()
    return ticket


@pytest.fixture
def process_ticket_dependencies() -> Iterator[tuple[Mock, Mock, Mock]]:
    with (
        patch("backend.jobs.QdrantClient") as client,
        patch("backend.jobs.get_embedding_model"),
        patch(
            "backend.services.ticket_classification_service.TicketClassificationService"
        ),
        patch("backend.workflows.ticket_workflow.TicketWorkflow") as workflow,
        patch(
            "langgraph.checkpoint.postgres.PostgresSaver.from_conn_string"
        ) as checkpointer,
    ):
        yield client, workflow, checkpointer


@pytest.mark.parametrize(
    "result_status",
    [TicketStatus.WAITING_FOR_APPROVAL, TicketStatus.ESCALATED, TicketStatus.RESOLVED],
)
def test_process_ticket_persists_workflow_result(
    db: Session,
    process_ticket_record: Tickets,
    process_ticket_dependencies: tuple[Mock, Mock, Mock],
    result_status: TicketStatus,
) -> None:
    client, workflow, checkpointer = process_ticket_dependencies
    ticket_id = process_ticket_record.id
    user_id = process_ticket_record.user_id
    original_text = process_ticket_record.text
    result = {
        "category": TicketCategories.SHIPPING_STATUS.value,
        "status": result_status.value,
        "order_number": "ORD-12345",
        "reply_draft": {"reply_text": "Wir pruefen den Versandstatus."},
        "sources": [{"id": "source-1", "text": "Versandinformationen"}],
        "review_reason": "manual_review",
        "approved": None,
    }
    workflow.return_value.start.return_value = result

    process_ticket(ticket_id)

    workflow.return_value.start.assert_called_once()
    loaded_ticket = workflow.return_value.start.call_args.args[0]
    assert loaded_ticket.id == ticket_id
    assert loaded_ticket.text == original_text
    checkpointer.return_value.__enter__.return_value.setup.assert_called_once()
    client.return_value.close.assert_called_once()

    db.expunge_all()
    stored = db.get(Tickets, ticket_id)
    assert stored is not None
    assert stored.user_id == user_id
    assert stored.text == original_text
    assert stored.category == TicketCategories.SHIPPING_STATUS
    assert stored.status == result_status
    assert stored.order_number == result["order_number"]
    assert stored.reply_draft == result["reply_draft"]
    assert stored.knowledge_sources == result["sources"]
    assert stored.review_reason == result["review_reason"]
    assert stored.approved is None


@pytest.mark.parametrize(
    "ticket_status",
    [
        TicketStatus.PROCESSING,
        TicketStatus.WAITING_FOR_APPROVAL,
        TicketStatus.ESCALATED,
        TicketStatus.RESOLVED,
    ],
)
def test_process_ticket_leaves_non_pending_ticket_unchanged(
    db: Session,
    process_ticket_record: Tickets,
    process_ticket_dependencies: tuple[Mock, Mock, Mock],
    ticket_status: TicketStatus,
) -> None:
    client, workflow, checkpointer = process_ticket_dependencies
    process_ticket_record.status = ticket_status
    db.flush()
    ticket_id = process_ticket_record.id

    process_ticket(ticket_id)

    client.assert_not_called()
    workflow.assert_not_called()
    checkpointer.assert_not_called()
    db.expunge_all()
    stored = db.get(Tickets, ticket_id)
    assert stored is not None
    assert stored.status == ticket_status
    assert stored.category is None
    assert stored.reply_draft is None


def test_process_ticket_raises_when_ticket_not_found(
    monkeypatch: MonkeyPatch,
    test_session_factory: sessionmaker,
    process_ticket_dependencies: tuple[Mock, Mock, Mock],
) -> None:
    monkeypatch.setattr("backend.jobs.SessionLocal", test_session_factory)
    client, workflow, checkpointer = process_ticket_dependencies

    with pytest.raises(TicketRetrievalError, match="wurde nicht gefunden"):
        process_ticket(uuid4())

    client.assert_not_called()
    workflow.assert_not_called()
    checkpointer.assert_not_called()


@pytest.mark.parametrize("failure_stage", ["checkpointer", "workflow"])
def test_process_ticket_keeps_ticket_unchanged_when_processing_fails(
    db: Session,
    process_ticket_record: Tickets,
    process_ticket_dependencies: tuple[Mock, Mock, Mock],
    failure_stage: str,
) -> None:
    client, workflow, checkpointer = process_ticket_dependencies
    ticket_id = process_ticket_record.id
    error = RuntimeError("Verarbeitung fehlgeschlagen")
    if failure_stage == "checkpointer":
        checkpointer.return_value.__enter__.side_effect = error
    else:
        workflow.return_value.start.side_effect = error

    with pytest.raises(RuntimeError, match="Verarbeitung fehlgeschlagen"):
        process_ticket(ticket_id)

    client.return_value.close.assert_called_once()
    if failure_stage == "checkpointer":
        workflow.assert_not_called()
    else:
        workflow.return_value.start.assert_called_once()
    db.expunge_all()
    stored = db.get(Tickets, ticket_id)
    assert stored is not None
    assert stored.status == TicketStatus.PENDING
    assert stored.category is None
    assert stored.order_number is None
    assert stored.reply_draft is None
    assert stored.knowledge_sources is None
    assert stored.review_reason is None
    assert stored.approved is None


def test_get_embedding_model_loads_expected_model() -> None:
    from sentence_transformers import SentenceTransformer

    from backend.jobs import get_embedding_model

    model = get_embedding_model()

    assert isinstance(model, SentenceTransformer)
    assert model.tokenizer.name_or_path == (
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )
