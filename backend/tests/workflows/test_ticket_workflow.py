from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from backend.exceptions.tickets import TicketApprovalConflictError
from backend.workflows.ticket_workflow import TicketWorkflow


def test_resume_returns_saved_result_without_resuming_again():
    ticket_id = uuid4()
    saved_result = {
        "approved": True,
        "status": "resolved",
        "review_reason": "draft_approved",
    }

    # Nur resume() testen, ohne externe Dienste aufzubauen.
    workflow = TicketWorkflow.__new__(TicketWorkflow)
    workflow.routing_graph = Mock()
    workflow.routing_graph.get_state.return_value = SimpleNamespace(
        values=saved_result,
        tasks=(),
    )

    result = workflow.resume(ticket_id, approved=True)

    assert result == saved_result
    workflow.routing_graph.get_state.assert_called_once_with(
        {"configurable": {"thread_id": str(ticket_id)}}
    )
    workflow.routing_graph.invoke.assert_not_called()


def test_resume_rejects_conflicting_decision():
    workflow = TicketWorkflow.__new__(TicketWorkflow)
    workflow.routing_graph = Mock()
    workflow.routing_graph.get_state.return_value = SimpleNamespace(
        values={"approved": True},
        tasks=(),
    )

    with pytest.raises(
        TicketApprovalConflictError,
        match="A different approval decision",
    ):
        workflow.resume(uuid4(), approved=False)

    workflow.routing_graph.invoke.assert_not_called()
