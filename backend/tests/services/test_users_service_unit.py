from datetime import UTC, datetime
from unittest.mock import DEFAULT, Mock, create_autospec, patch
from uuid import UUID

import pytest

from backend.exceptions.users import (
    EmailAlreadyExistError,
    UserCreationError,
    UserNotFoundError,
    UserRetrievalError,
    UserUpdateError,
)
from backend.models.users import UserRole, Users
from backend.repositories.users_repository import UsersRepository
from backend.schemas.users import ChangeEmailRequest, CreateUserRequest
from backend.services.users_service import UsersService


@pytest.mark.parametrize(
    ("exception", "exception_msg"),
    [
        (EmailAlreadyExistError, "Email already exists"),
        (UserUpdateError, "User could not be updated"),
    ],
)
def test_change_email_propagates_update_errors(
    exception: type[Exception], exception_msg: str
) -> None:
    user_id = UUID("550e8400-e29b-41d4-a716-446655440000")
    repo = create_autospec(UsersRepository, instance=True)
    existing_user = Users(
        id=user_id,
        user_role=UserRole.CUSTOMER,
        email="test.user@example.com",
        hashed_password="fake-hash",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    repo.get.return_value = existing_user
    error = exception(exception_msg)
    repo.update.side_effect = error

    service = UsersService(users_repo=repo)

    with pytest.raises(exception, match=exception_msg) as exc_info:
        service.change_email(
            user_id=user_id, request=ChangeEmailRequest(email="test-email@mail.de")
        )

    assert exc_info.value is error
    repo.get.assert_called_once_with(user_id)
    repo.update.assert_called_once_with(user=existing_user)


def test_change_email_propagates_user_retrieval_error() -> None:
    user_id = UUID("550e8400-e29b-41d4-a716-446655440000")
    repo = create_autospec(UsersRepository, instance=True)
    error = UserRetrievalError("User could not be retrieved")
    repo.get.side_effect = error
    service = UsersService(users_repo=repo)

    with pytest.raises(
        UserRetrievalError, match="User could not be retrieved"
    ) as exc_info:
        service.change_email(
            user_id=user_id, request=ChangeEmailRequest(email="test-email@mail.de")
        )

    assert exc_info.value is error

    repo.get.assert_called_once_with(user_id)
    repo.update.assert_not_called()


def test_change_email_raises_not_found_for_unknown_user() -> None:
    user_id = UUID("550e8400-e29b-41d4-a716-446655440000")
    repo = create_autospec(UsersRepository, instance=True)
    repo.get.return_value = None
    service = UsersService(users_repo=repo)

    with pytest.raises(UserNotFoundError, match="User not found"):
        service.change_email(
            user_id=user_id, request=ChangeEmailRequest(email="test-email@mail.de")
        )

    repo.get.assert_called_once_with(user_id)
    repo.update.assert_not_called()


def test_change_email_updates_existing_user_and_returns_repository_result() -> None:
    user_id = UUID("550e8400-e29b-41d4-a716-446655440000")
    expected_email = "updated-email@example.com"
    request = ChangeEmailRequest(email=expected_email)
    repo = create_autospec(UsersRepository, instance=True)
    existing_user = Users(
        id=user_id,
        user_role=UserRole.CUSTOMER,
        email="test.user@example.com",
        hashed_password="fake-hash",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    repo.get.return_value = existing_user

    def check_update(*, user: Users) -> object:
        assert user is existing_user
        assert user.email == expected_email
        return DEFAULT

    repo.update.side_effect = check_update

    service = UsersService(users_repo=repo)

    updated_user = service.change_email(user_id=user_id, request=request)

    assert existing_user.email == expected_email
    assert updated_user is repo.update.return_value

    repo.get.assert_called_once_with(user_id)
    repo.update.assert_called_once_with(user=existing_user)


def test_get_user_propagates_repository_error() -> None:
    repo = Mock(spec=UsersRepository)
    error = UserRetrievalError("User could not be retrieved")
    repo.get.side_effect = error
    user_id = UUID("550e8400-e29b-41d4-a716-446655440000")
    service = UsersService(users_repo=repo)

    with pytest.raises(
        UserRetrievalError, match="User could not be retrieved"
    ) as exc_info:
        service.get_user(user_id=user_id)

    assert exc_info.value is error
    repo.get.assert_called_once_with(user_id)


def test_get_user_raises_not_found_when_repository_returns_none() -> None:
    repo = Mock(spec=UsersRepository)
    repo.get.return_value = None
    user_id = UUID("550e8400-e29b-41d4-a716-446655440000")
    service = UsersService(users_repo=repo)

    with pytest.raises(UserNotFoundError, match="User not found"):
        service.get_user(user_id=user_id)

    repo.get.assert_called_once_with(user_id)


def test_get_user_returns_user_from_repository() -> None:
    repo = Mock(spec=UsersRepository)

    expected_user = Users(
        id=UUID("550e8400-e29b-41d4-a716-446655440000"),
        user_role=UserRole.CUSTOMER,
        email="test.user@example.com",
        hashed_password="fake-hash",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    repo.get.return_value = expected_user
    service = UsersService(users_repo=repo)
    user_found = service.get_user(user_id=expected_user.id)

    assert user_found is expected_user
    repo.get.assert_called_once_with(expected_user.id)


@pytest.mark.parametrize(
    ("exception", "exception_msg"),
    [
        (UserCreationError, "User could not be created"),
        (EmailAlreadyExistError, "Email already exists"),
    ],
)
def test_create_user_propagates_repository_errors(
    exception: type[Exception], exception_msg: str
) -> None:
    repo_mock = Mock(spec=UsersRepository)
    error = exception(exception_msg)
    repo_mock.add.side_effect = error
    service = UsersService(users_repo=repo_mock)
    request = CreateUserRequest(
        email="example@outlook.com",
        password="Secret Password 123",
    )

    with (
        patch(
            "backend.services.users_service.hash_password",
            return_value="fake-hash",
        ),
        pytest.raises(exception, match=exception_msg) as exc_info,
    ):
        service.create_user(create_user_request=request)

    assert exc_info.value is error


def test_create_user_hashes_password_and_passes_user_to_repository() -> None:
    repo_mock = Mock(spec=UsersRepository)
    service = UsersService(users_repo=repo_mock)
    request = CreateUserRequest(
        email="example@outlook.com",
        password="Secret Password 123",
    )

    with patch(
        "backend.services.users_service.hash_password",
        return_value="fake-hash",
    ) as hash_password_mock:
        result = service.create_user(create_user_request=request)

    assert result is repo_mock.add.return_value
    hash_password_mock.assert_called_once_with("Secret Password 123")
    repo_mock.add.assert_called_once()

    user = repo_mock.add.call_args.args[0]

    assert user.email == request.email
    assert user.hashed_password == "fake-hash"
    assert user.user_role == UserRole.CUSTOMER
