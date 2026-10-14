from unittest.mock import Mock, patch

import pytest

from backend.exceptions.users import EmailAlreadyExistError, UserCreationError
from backend.models.users import UserRole
from backend.repositories.users_repository import UsersRepository
from backend.schemas.users import CreateUserRequest
from backend.services.users_service import UsersService


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
