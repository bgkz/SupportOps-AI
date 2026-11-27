from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from backend.dependencies.auth import get_current_user
from backend.dependencies.tickets import get_tickets_service
from backend.exceptions.tickets import TicketApprovalConflictError, TicketApprovalPermissionError
from backend.main import app
from backend.models.users import UserRole
from backend.schemas.tickets import ApproveTicketRequest
from backend.services.tickets_service import TicketsService


@pytest.fixture
def ticket_context():
    service = Mock(spec=TicketsService)
    user = SimpleNamespace(id=uuid4(), user_role=UserRole.CUSTOMER)
    previous = app.dependency_overrides.copy()
    app.dependency_overrides[get_tickets_service] = lambda: service
    app.dependency_overrides[get_current_user] = lambda: user
    yield service, user
    app.dependency_overrides.clear()
    app.dependency_overrides.update(previous)


@pytest.mark.parametrize("endpoint", ["detail", "approval"])
def test_ticket_endpoints_require_login(client, ticket_context, endpoint):
    service, _ = ticket_context

    def unauthenticated():
        raise HTTPException(status_code=401, detail="Not authenticated")

    app.dependency_overrides[get_current_user] = unauthenticated
    ticket_id = uuid4()
    response = (
        client.get(f"/tickets/ticket/{ticket_id}")
        if endpoint == "detail"
        else client.post(f"/tickets/{ticket_id}/approval", json={"approved": True})
    )
    assert response.status_code == 401
    service.get_ticket.assert_not_called()
    service.approve_ticket.assert_not_called()


def test_customer_cannot_read_support_detail_or_approve(client, ticket_context):
    service, _ = ticket_context
    ticket_id = uuid4()
    assert client.get(f"/tickets/ticket/{ticket_id}").status_code == 403
    assert client.post(
        f"/tickets/{ticket_id}/approval", json={"approved": True}
    ).status_code == 403
    service.get_ticket.assert_not_called()
    service.approve_ticket.assert_not_called()


def test_user_ticket_route_checks_owner(client, ticket_context):
    service, user = ticket_context
    service.get_tickets_by_user.return_value = []
    assert client.get(f"/tickets/user/{user.id}").status_code == 200
    assert client.get(f"/tickets/user/{uuid4()}").status_code == 403
    service.get_tickets_by_user.assert_called_once_with(user_id=user.id)


def test_support_approval_uses_session_and_returns_conflict(client, ticket_context):
    service, user = ticket_context
    user.user_role = UserRole.SUPPORT_AGENT
    service.approve_ticket.side_effect = TicketApprovalConflictError("Conflicting decision")
    ticket_id = uuid4()
    response = client.post(f"/tickets/{ticket_id}/approval", json={"approved": True})
    assert response.status_code == 409
    assert response.json()["detail"] == "Conflicting decision"
    service.approve_ticket.assert_called_once_with(
        ticket_id=ticket_id,
        approve_ticket_request=ApproveTicketRequest(approved=True),
        current_user=user,
    )


def test_approval_rejects_body_identity(client, ticket_context):
    service, user = ticket_context
    user.user_role = UserRole.SUPPORT_AGENT
    response = client.post(
        f"/tickets/{uuid4()}/approval",
        json={"approved": True, "user_id": str(uuid4())},
    )
    assert response.status_code == 422
    service.approve_ticket.assert_not_called()


def test_service_rejects_customer_before_processing():
    service = TicketsService(Mock(), Mock(), Mock())
    user = SimpleNamespace(id=uuid4(), user_role=UserRole.CUSTOMER)
    with pytest.raises(TicketApprovalPermissionError):
        service.approve_ticket(uuid4(), ApproveTicketRequest(approved=True), user)
    service.tickets_repo.get_ticket.assert_not_called()
