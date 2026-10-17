from unittest.mock import create_autospec
from uuid import uuid4

import pytest

from backend.exceptions.tickets import (
    DuplicateIdempotencyKeyError,
    IdempotencyConflictError,
    TicketCreationError,
)
from backend.exceptions.users import UserNotFoundError
from backend.models.tickets import Tickets
from backend.repositories.tickets_repository import TicketsRepository
from backend.schemas.tickets import CreateTicketRequest
from backend.services.tickets_service import TicketsService
from backend.services.users_service import UsersService


@pytest.mark.parametrize("concurrent", [False, True])
@pytest.mark.parametrize("same_text", [False, True])
def test_replay_returns_existing_ticket_or_rejects_changed_text(concurrent, same_text):
    repo = create_autospec(TicketsRepository, instance=True)
    users = create_autospec(UsersService, instance=True)
    request = CreateTicketRequest(user_id=uuid4(), text="My shipment is missing")
    key = uuid4()
    existing = Tickets(
        user_id=request.user_id, idempotency_key=key,
        text=request.text if same_text else "A different ticket text",
    )
    if concurrent:
        repo.get_by_idempotency_key.side_effect = [None, existing]
        repo.add.side_effect = DuplicateIdempotencyKeyError()
    else:
        repo.get_by_idempotency_key.return_value = existing
    service = TicketsService(repo, users)

    if same_text:
        assert service.create_ticket(request, key) is existing
    else:
        with pytest.raises(IdempotencyConflictError):
            service.create_ticket(request, key)
    users.get_user.assert_called_once_with(user_id=request.user_id)
    assert repo.add.call_count == int(concurrent)


def test_create_stores_supplied_key():
    repo = create_autospec(TicketsRepository, instance=True)
    users = create_autospec(UsersService, instance=True)
    repo.get_by_idempotency_key.return_value = None
    request = CreateTicketRequest(user_id=uuid4(), text="My shipment is missing")
    key = uuid4()
    result = TicketsService(repo, users).create_ticket(request, key)
    assert result is repo.add.return_value
    ticket = repo.add.call_args.args[0]
    assert (ticket.user_id, ticket.text, ticket.idempotency_key) == (
        request.user_id, request.text, key,
    )


def test_missing_user_does_not_create_ticket():
    repo = create_autospec(TicketsRepository, instance=True)
    users = create_autospec(UsersService, instance=True)
    users.get_user.side_effect = UserNotFoundError()
    request = CreateTicketRequest(user_id=uuid4(), text="My shipment is missing")
    with pytest.raises(UserNotFoundError):
        TicketsService(repo, users).create_ticket(request, uuid4())
    repo.add.assert_not_called()


def test_concurrent_ticket_disappeared_is_creation_error():
    repo = create_autospec(TicketsRepository, instance=True)
    users = create_autospec(UsersService, instance=True)
    repo.get_by_idempotency_key.return_value = None
    repo.add.side_effect = DuplicateIdempotencyKeyError()
    request = CreateTicketRequest(user_id=uuid4(), text="My shipment is missing")
    with pytest.raises(TicketCreationError):
        TicketsService(repo, users).create_ticket(request, uuid4())
