from unittest.mock import patch
from uuid import uuid4

import pytest

from backend.jobs import process_ticket
from backend.models.tickets import Tickets, TicketStatus


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
    ):
        process_ticket(ticket_id)

    mock_get_ticket.assert_called_once_with(ticket_id)
    mock_qdrant_client.assert_not_called()
