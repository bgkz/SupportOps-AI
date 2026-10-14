from unittest.mock import Mock, patch

from backend.models.users import UserRole
from backend.repositories.users_repository import UsersRepository
from backend.schemas.users import CreateUserRequest
from backend.services.users_service import UsersService


def test_create_user_hashes_password_and_passes_user_to_repository() -> None:
    repo_mock = Mock(spec=UsersRepository)
    repo_mock.add = Mock()
    service = UsersService(users_repo=repo_mock)
    request = CreateUserRequest(
        email="example@outlook.com",
        password="Secret Password 123",
    )

    with patch(
        "backend.services.users_service.hash_password",
        return_value="fake-hash",
    ) as hash_password_mock:
        service.create_user(create_user_request=request)

    hash_password_mock.assert_called_once_with("Secret Password 123")
    repo_mock.add.assert_called_once()

    user = repo_mock.add.call_args.args[0]

    assert user.email == request.email
    assert user.hashed_password == "fake-hash"
    assert user.user_role == UserRole.CUSTOMER
