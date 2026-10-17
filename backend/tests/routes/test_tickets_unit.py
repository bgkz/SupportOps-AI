from unittest.mock import create_autospec
from uuid import uuid4

import pytest

from backend.dependencies.tickets import get_tickets_service
from backend.exceptions.tickets import (
    IdempotencyConflictError, TicketCreationError, TicketRetrievalError,
)
from backend.exceptions.users import UserNotFoundError, UserRetrievalError
from backend.main import app
from backend.schemas.tickets import CreateTicketRequest
from backend.services.tickets_service import TicketsService


@pytest.mark.parametrize(
    ("exception", "expected_status", "detail"),
    [
        (UserNotFoundError, 404, "User not found"),
        (IdempotencyConflictError, 409, "Key conflict"),
        (TicketCreationError, 500, "Ticket could not be created"),
        (TicketRetrievalError, 500, "Ticket creation could not be completed"),
        (UserRetrievalError, 500, "Ticket creation could not be completed"),
    ],
)
def test_create_ticket_maps_errors(client, monkeypatch, exception, expected_status, detail):
    monkeypatch.setattr("backend.security.api_key.BACKEND_API_KEY", "test-api-key")
    service = create_autospec(TicketsService, instance=True)
    message = detail if expected_status != 500 else "Internal database details"
    service.create_ticket.side_effect = exception(message)
    request = CreateTicketRequest(user_id=uuid4(), text="My shipment is missing")
    key = uuid4()
    app.dependency_overrides[get_tickets_service] = lambda: service
    try:
        response = client.post(
            "/tickets/",
            headers={"X-API-Key": "test-api-key", "Idempotency-Key": str(key)},
            json=request.model_dump(mode="json"),
        )
        assert response.status_code == expected_status
        assert response.json() == {"detail": detail}
        service.create_ticket.assert_called_once_with(request=request, idempotency_key=key)
    finally:
        del app.dependency_overrides[get_tickets_service]
