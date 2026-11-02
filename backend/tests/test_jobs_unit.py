from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from backend.exceptions.tickets import TicketApprovalConflictError, TicketRetrievalError
from backend.jobs import (
    get_embedding_model,
    get_ticket,
    process_ticket,
    save_ticket_approval,
    save_workflow_result,
)
from backend.models.tickets import TicketCategories, Tickets, TicketStatus


def test_get_embedding_model() -> None:
    get_embedding_model.cache_clear()

    try:
        with patch("sentence_transformers.SentenceTransformer") as mock_constructor:
            model = get_embedding_model()
            cached_model = get_embedding_model()

        mock_constructor.assert_called_once_with(
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
        assert model is mock_constructor.return_value
        assert cached_model is model
    finally:
        get_embedding_model.cache_clear()


def test_get_ticket_propagates_session_enter_error() -> None:
    ticket_id = uuid4()
    db = Mock(spec=Session)

    with patch("backend.jobs.SessionLocal.begin") as mock_begin:
        mock_begin.return_value.__enter__.return_value = db
        mock_begin.return_value.__enter__.side_effect = RuntimeError(
            "Datenbankverbindung fehlgeschlagen"
        )

        with pytest.raises(RuntimeError, match="Datenbankverbindung fehlgeschlagen"):
            get_ticket(ticket_id=ticket_id)

    db.get.assert_not_called()


def test_get_ticket_raises_error_when_ticket_not_found() -> None:
    ticket_id = uuid4()
    db = Mock(spec=Session)
    db.get.return_value = None

    with patch("backend.jobs.SessionLocal.begin") as mock_begin:
        mock_begin.return_value.__enter__.return_value = db

        with pytest.raises(TicketRetrievalError, match="wurde nicht gefunden"):
            get_ticket(ticket_id=ticket_id)

    db.get.assert_called_once_with(Tickets, ticket_id)


def test_get_ticket_returns_ticket() -> None:
    ticket_id = uuid4()
    ticket = Tickets(
        id=ticket_id,
        user_id=uuid4(),
        text="Test Ticket",
    )

    db = Mock(spec=Session)
    db.get.return_value = ticket

    with patch("backend.jobs.SessionLocal.begin") as mock_begin:
        mock_begin.return_value.__enter__.return_value = db

        result = get_ticket(ticket_id=ticket_id)

    assert result is ticket
    db.get.assert_called_once_with(Tickets, ticket_id)


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
    ticket_status: TicketStatus,
) -> None:
    ticket_id = uuid4()
    stored = Tickets(
        id=ticket_id,
        status=ticket_status,
        reply_draft={"reply_text": "Bestehende Antwort"},
    )
    ticket = Tickets(
        id=ticket_id,
        status=TicketStatus.WAITING_FOR_APPROVAL,
        reply_draft={"reply_text": "Neue Antwort"},
    )

    db = Mock(spec=Session)
    db.get.return_value = stored

    with patch("backend.jobs.SessionLocal.begin") as mock_begin:
        mock_begin.return_value.__enter__.return_value = db

        result = save_workflow_result(ticket)

    assert result is stored
    assert stored.status is ticket_status
    assert stored.reply_draft == {"reply_text": "Bestehende Antwort"}
    db.get.assert_called_once_with(Tickets, ticket_id, with_for_update=True)


def test_save_workflow_result_raises_error_when_ticket_not_found() -> None:
    db = Mock(spec=Session)
    db.get.return_value = None

    ticket = Tickets(id=uuid4())

    with patch("backend.jobs.SessionLocal.begin") as mock_begin:
        mock_begin.return_value.__enter__.return_value = db

        with pytest.raises(TicketRetrievalError, match="wurde nicht gefunden"):
            save_workflow_result(ticket=ticket)

    db.get.assert_called_once_with(Tickets, ticket.id, with_for_update=True)


@pytest.mark.parametrize("review_reason", ["draft_requires_review", None])
def test_save_workflow_result_copies_workflow_fields(review_reason: str | None) -> None:
    ticket_id = uuid4()
    stored = Tickets(
        id=ticket_id,
        status=TicketStatus.PENDING,
        review_reason="alter Grund",
    )
    ticket = Tickets(
        id=ticket_id,
        category=TicketCategories.DAMAGED_GOODS,
        status=TicketStatus.WAITING_FOR_APPROVAL,
        order_number="AB-0042",
        reply_draft={"reply_text": "Bitte senden Sie uns Fotos."},
        knowledge_sources=[{"id": "source-1"}],
        review_reason=review_reason,
    )

    db = Mock(spec=Session)
    db.get.return_value = stored

    with patch("backend.jobs.SessionLocal.begin") as mock_begin:
        mock_begin.return_value.__enter__.return_value = db

        result = save_workflow_result(ticket)

    assert result is stored
    assert stored.category == ticket.category
    assert stored.status == ticket.status
    assert stored.order_number == ticket.order_number
    assert stored.reply_draft == ticket.reply_draft
    assert stored.knowledge_sources == ticket.knowledge_sources
    assert stored.review_reason == ticket.review_reason
    db.get.assert_called_once_with(Tickets, ticket_id, with_for_update=True)


@pytest.mark.parametrize(
    ("invalid_ticket", "expected_exc", "exc_message"),
    [
        (None, TicketRetrievalError, "wurde nicht gefunden"),
        (
            Tickets(status=TicketStatus.PENDING),
            TicketApprovalConflictError,
            "Das Ticket wartet nicht auf Freigabe",
        ),
        (
            Tickets(reply_draft=None, status=TicketStatus.WAITING_FOR_APPROVAL),
            TicketApprovalConflictError,
            "Es gibt keinen Antwortentwurf zur Freigabe.",
        ),
    ],
)
def test_save_ticket_approval_raises_errors(
    invalid_ticket: Tickets | None,
    expected_exc: type[Exception],
    exc_message: str,
) -> None:
    ticket_id = uuid4()
    db = Mock(spec=Session)
    db.get.return_value = invalid_ticket
    with patch("backend.jobs.SessionLocal.begin") as mock_begin:
        mock_begin.return_value.__enter__.return_value = db

        with pytest.raises(expected_exception=expected_exc, match=exc_message):
            save_ticket_approval(ticket_id=ticket_id, approved=True)

    db.get.assert_called_once_with(Tickets, ticket_id, with_for_update=True)


@pytest.mark.parametrize(
    ("stored_approved", "approved"),
    [(False, True), (True, False)],
)
def test_save_ticket_approval_rejects_conflicting_decision(
    stored_approved: bool, approved: bool
) -> None:
    ticket_id = uuid4()
    fake_ticket = Tickets(
        id=ticket_id,
        status=TicketStatus.WAITING_FOR_APPROVAL,
        reply_draft={"reply_text": "Antwortentwurf"},
        approved=stored_approved,
    )
    db = Mock(spec=Session)
    db.get.return_value = fake_ticket

    with patch("backend.jobs.SessionLocal.begin") as mock_begin:
        mock_begin.return_value.__enter__.return_value = db

        with pytest.raises(
            TicketApprovalConflictError, match="A different approval decision has already been recorded"
        ):
            save_ticket_approval(ticket_id=ticket_id, approved=approved)

    assert fake_ticket.approved is stored_approved
    db.get.assert_called_once_with(Tickets, ticket_id, with_for_update=True)


@pytest.mark.parametrize(
    ("stored_approved", "approved"),
    [
        pytest.param(None, True, id="new-approval"),
        pytest.param(None, False, id="new-rejection"),
        pytest.param(True, True, id="repeated-approval"),
        pytest.param(False, False, id="repeated-rejection"),
    ],
)
def test_save_ticket_approval_saves_decision(
    stored_approved: bool | None, approved: bool
) -> None:
    ticket_id = uuid4()
    fake_ticket = Tickets(
        id=ticket_id,
        user_id=uuid4(),
        text="Meine Bestellung AB-0042 ist beschädigt angekommen.",
        reply_draft={
            "reply_text": "Es tut uns leid, dass Ihre Bestellung AB-0042 beschädigt angekommen ist. Bitte senden Sie uns Fotos der beschädigten Ware.",
            "source_ids": ["source-1"],
            "needs_manual_review": True,
        },
        status=TicketStatus.WAITING_FOR_APPROVAL,
        approved=stored_approved,
    )

    db = Mock(spec=Session)
    db.get.return_value = fake_ticket
    with patch("backend.jobs.SessionLocal.begin") as mock_begin:
        mock_begin.return_value.__enter__.return_value = db

        result = save_ticket_approval(ticket_id=ticket_id, approved=approved)

    assert result is fake_ticket
    assert result.approved is approved
    db.get.assert_called_once_with(Tickets, ticket_id, with_for_update=True)


def test_process_ticket_closes_client_when_workflow_start_fails() -> None:
    ticket_id = uuid4()
    fake_ticket = Tickets(
        id=ticket_id,
        user_id=uuid4(),
        text="Meine Bestellung AB-0042 ist beschädigt angekommen.",
        status=TicketStatus.PENDING,
    )

    with (
        patch("backend.jobs.get_embedding_model"),
        patch(
            "backend.services.ticket_classification_service.TicketClassificationService"
        ),
        patch(
            "backend.workflows.ticket_workflow.TicketWorkflow"
        ) as mock_workflow_class,
        patch("backend.jobs.get_ticket", return_value=fake_ticket) as mock_get_ticket,
        patch("backend.jobs.save_workflow_result") as mock_save_workflow_result,
        patch("backend.jobs.QdrantClient") as mock_qdrant_client,
        patch(
            "langgraph.checkpoint.postgres.PostgresSaver.from_conn_string"
        ) as mock_checkpointer_context,
    ):
        mock_workflow_class.return_value.start.side_effect = RuntimeError(
            "Workflow fehlgeschlagen"
        )
        checkpointer = mock_checkpointer_context.return_value.__enter__.return_value

        with pytest.raises(RuntimeError, match="Workflow fehlgeschlagen"):
            process_ticket(ticket_id)

        mock_get_ticket.assert_called_once_with(ticket_id)
        checkpointer.setup.assert_called_once()
        mock_workflow_class.return_value.start.assert_called_once_with(fake_ticket)
        mock_qdrant_client.return_value.close.assert_called_once()
        mock_save_workflow_result.assert_not_called()


def test_process_ticket_closes_client_when_checkpointer_enter_fails() -> None:
    ticket_id = uuid4()
    fake_ticket = Tickets(
        id=ticket_id,
        user_id=uuid4(),
        text="Meine Bestellung AB-0042 ist beschädigt angekommen.",
        status=TicketStatus.PENDING,
    )

    with (
        patch(
            "backend.workflows.ticket_workflow.TicketWorkflow"
        ) as mock_workflow_class,
        patch("backend.jobs.get_ticket", return_value=fake_ticket) as mock_get_ticket,
        patch("backend.jobs.save_workflow_result") as mock_save_workflow_result,
        patch("backend.jobs.QdrantClient") as mock_qdrant_client,
        patch(
            "langgraph.checkpoint.postgres.PostgresSaver.from_conn_string"
        ) as mock_checkpointer_context,
    ):
        mock_checkpointer_context.return_value.__enter__.side_effect = RuntimeError(
            "Checkpoint-Verbindung fehlgeschlagen"
        )

        with pytest.raises(RuntimeError, match="Checkpoint-Verbindung fehlgeschlagen"):
            process_ticket(ticket_id)

        mock_get_ticket.assert_called_once_with(ticket_id)
        mock_workflow_class.assert_not_called()
        mock_qdrant_client.return_value.close.assert_called_once()
        mock_save_workflow_result.assert_not_called()


def test_process_ticket_qdrant_client_has_error_so_ticket_workflow_doesnt_start() -> (
    None
):
    ticket_id = uuid4()
    fake_ticket = Tickets(
        id=ticket_id,
        user_id=uuid4(),
        text="Meine Bestellung AB-0042 ist beschädigt angekommen.",
        status=TicketStatus.PENDING,
    )

    with (
        patch("backend.jobs.get_ticket", return_value=fake_ticket) as mock_get_ticket,
        patch("backend.jobs.QdrantClient") as mock_qdrant_client,
        patch(
            "backend.workflows.ticket_workflow.TicketWorkflow"
        ) as mock_workflow_class,
    ):
        mock_qdrant_client.side_effect = RuntimeError(
            "Qdrant-Client konnte nicht erstellt werden"
        )

        with pytest.raises(RuntimeError, match="Qdrant-Client"):
            process_ticket(ticket_id)

        mock_get_ticket.assert_called_once_with(ticket_id)

        mock_workflow_class.assert_not_called()


def test_process_ticket_saves_workflow_result_and_closes_client() -> None:
    ticket_id = uuid4()
    fake_ticket = Tickets(
        id=ticket_id,
        user_id=uuid4(),
        text="Meine Bestellung AB-0042 ist beschädigt angekommen.",
        status=TicketStatus.PENDING,
    )
    fake_result = {
        "category": "damaged_goods",
        "status": "waiting_for_approval",
        "order_number": "AB-0042",
        "reply_draft": {
            "reply_text": "Bitte senden Sie uns Fotos des Schadens.",
            "source_ids": ["source-1"],
            "needs_manual_review": True,
        },
        "sources": [
            {
                "id": "source-1",
                "text": "Bei beschädigter Ware Fotos anfordern.",
                "source": "damaged_goods.md",
            }
        ],
        "review_reason": "draft_requires_review",
        "approved": None,
    }
    with (
        patch("backend.jobs.get_ticket", return_value=fake_ticket) as mock_get_ticket,
        patch(
            "backend.jobs.save_workflow_result", return_value=fake_ticket
        ) as mock_save_workflow_result,
        patch(
            "backend.workflows.ticket_workflow.TicketWorkflow"
        ) as mock_workflow_class,
        patch("backend.jobs.QdrantClient") as mock_qdrant_client,
        patch("backend.jobs.get_embedding_model") as mock_embedding_model,
        patch(
            "backend.services.ticket_classification_service.TicketClassificationService"
        ) as mock_classification_service,
        patch(
            "langgraph.checkpoint.postgres.PostgresSaver.from_conn_string"
        ) as mock_checkpointer_context,
    ):
        mock_workflow = mock_workflow_class.return_value
        mock_workflow.start.return_value = fake_result
        process_ticket(ticket_id=ticket_id)

    checkpointer = mock_checkpointer_context.return_value.__enter__.return_value
    mock_get_ticket.assert_called_once_with(ticket_id)
    checkpointer.setup.assert_called_once()
    mock_workflow_class.assert_called_once_with(
        ticket_classification_service=mock_classification_service.return_value,
        sentence_transformer_model=mock_embedding_model.return_value,
        qdrant_client=mock_qdrant_client.return_value,
        checkpointer=checkpointer,
    )
    mock_workflow.start.assert_called_once_with(fake_ticket)
    mock_save_workflow_result.assert_called_once_with(fake_ticket)
    mock_qdrant_client.return_value.close.assert_called_once()

    assert fake_ticket.category == TicketCategories.DAMAGED_GOODS
    assert fake_ticket.status == TicketStatus.WAITING_FOR_APPROVAL
    assert fake_ticket.order_number == fake_result["order_number"]
    assert fake_ticket.reply_draft == fake_result["reply_draft"]
    assert fake_ticket.knowledge_sources == fake_result["sources"]
    assert fake_ticket.review_reason == fake_result["review_reason"]
    assert fake_ticket.approved is None


@pytest.mark.parametrize(
    "ticket_status",
    [
        TicketStatus.WAITING_FOR_APPROVAL,
        TicketStatus.ESCALATED,
        TicketStatus.PROCESSING,
        TicketStatus.RESOLVED,
    ],
)
def test_process_ticket_stops_when_ticket_status_is_not_pending(
    ticket_status: TicketStatus,
) -> None:
    ticket_id = uuid4()
    fake_ticket = Tickets(
        id=ticket_id,
        user_id=uuid4(),
        text="Meine Bestellung AB-0042 ist beschädigt angekommen.",
        status=ticket_status,
    )

    with (
        patch("backend.jobs.get_ticket", return_value=fake_ticket) as mock_get_ticket,
        patch("backend.jobs.QdrantClient") as mock_qdrant_client,
        patch(
            "backend.workflows.ticket_workflow.TicketWorkflow"
        ) as mock_workflow_class,
    ):
        process_ticket(ticket_id)

    mock_get_ticket.assert_called_once_with(ticket_id)
    mock_workflow_class.assert_not_called()
    mock_qdrant_client.assert_not_called()
