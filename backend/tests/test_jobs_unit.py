from unittest.mock import patch
from uuid import uuid4

import pytest

from backend.jobs import process_ticket
from backend.models.tickets import TicketCategories, Tickets, TicketStatus


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
        patch("backend.jobs.update_ticket") as mock_update_ticket,
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
        mock_update_ticket.assert_not_called()


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
        patch("backend.jobs.update_ticket") as mock_update_ticket,
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
        mock_update_ticket.assert_not_called()


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
            "backend.jobs.update_ticket", return_value=fake_ticket
        ) as mock_update_ticket,
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
    mock_update_ticket.assert_called_once_with(fake_ticket)
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
