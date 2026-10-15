from datetime import UTC, datetime
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from backend.dependencies.users import get_users_service
from backend.exceptions.users import (
    EmailAlreadyExistError,
    UserCreationError,
    UserNotFoundError,
    UserRetrievalError,
)
from backend.main import app
from backend.models.users import UserRole, Users
from backend.schemas.users import CreateUserRequest, UserResponse
from backend.services.users_service import UsersService


@pytest.fixture(autouse=True)
def configure_test_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "backend.security.api_key.BACKEND_API_KEY",
        "test-api-key",
    )


@pytest.mark.parametrize(
    ("exception", "exception_msg", "expected_status"),
    [
        (
            UserNotFoundError,
            "User not found",
            status.HTTP_404_NOT_FOUND,
        ),
        (
            UserRetrievalError,
            "User could not be retrieved",
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ),
    ],
    ids=["user-not-found", "user-retrieval-error"],
)
def test_get_user_maps_service_errors_to_http_responses(
    client: TestClient,
    exception: type[Exception],
    exception_msg: str,
    expected_status: int,
) -> None:
    user_id = uuid4()
    service_mock = Mock(spec=UsersService)
    service_mock.get_user.side_effect = exception(exception_msg)
    app.dependency_overrides[get_users_service] = lambda: service_mock

    try:
        response = client.get(
            f"/users/{user_id}",
            headers={"X-API-Key": "test-api-key"},
        )

        assert response.status_code == expected_status
        assert response.json() == {"detail": exception_msg}
        service_mock.get_user.assert_called_once_with(user_id)

    finally:
        del app.dependency_overrides[get_users_service]


def test_get_user_returns_existing_user(client: TestClient) -> None:

    user_id = UUID("550e8400-e29b-41d4-a716-446655440000")
    expected_user = Users(
        id=user_id,
        user_role=UserRole.CUSTOMER,
        email="test.user@example.com",
        hashed_password="test-password-hash",
        created_at=datetime(2026, 1, 1, 12, 0, 0),
        updated_at=datetime(2026, 1, 2, 14, 30, 0),
    )
    service_mock = Mock(spec=UsersService)
    service_mock.get_user.return_value = expected_user

    app.dependency_overrides[get_users_service] = lambda: service_mock

    try:
        response = client.get(
            f"/users/{user_id}",
            headers={"X-API-Key": "test-api-key"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "id": str(user_id),
            "user_role": "customer",
            "email": "test.user@example.com",
            "created_at": "2026-01-01T12:00:00",
            "updated_at": "2026-01-02T14:30:00",
        }

        service_mock.get_user.assert_called_once_with(user_id)

    finally:
        del app.dependency_overrides[get_users_service]


def test_create_user_passes_request_to_service(client: TestClient) -> None:
    service_mock = Mock(spec=UsersService)
    request = CreateUserRequest(
        email="someemail@outlook.de", password="Somepassword123"
    )

    expected_response = UserResponse(
        id=uuid4(),
        email=request.email,
        user_role=UserRole.CUSTOMER,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    service_mock.create_user.return_value = expected_response
    app.dependency_overrides[get_users_service] = lambda: service_mock

    try:
        response = client.post(
            "/users/",
            headers={"X-API-Key": "test-api-key"},
            json={
                "email": str(request.email),
                "password": request.password.get_secret_value(),
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json() == expected_response.model_dump(mode="json")
        service_mock.create_user.assert_called_once_with(
            create_user_request=request,
        )

    finally:
        del app.dependency_overrides[get_users_service]


@pytest.mark.parametrize(
    ("exception", "exception_msg", "expected_status"),
    [
        (
            UserCreationError,
            "User could not be created",
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ),
        (EmailAlreadyExistError, "Email already exists", status.HTTP_409_CONFLICT),
    ],
    ids=["user-creation-error", "duplicate-email"],
)
def test_create_user_maps_service_errors_to_http_responses(
    client: TestClient,
    exception: type[Exception],
    exception_msg: str,
    expected_status: int,
) -> None:
    service_mock = Mock(spec=UsersService)
    service_mock.create_user.side_effect = exception(exception_msg)

    app.dependency_overrides[get_users_service] = lambda: service_mock

    try:
        response = client.post(
            "/users/",
            headers={"X-API-Key": "test-api-key"},
            json={
                "email": "someemail@outlook.de",
                "password": "Some password 123",
            },
        )

        service_mock.create_user.assert_called_once()

        assert response.status_code == expected_status
        assert response.json()["detail"] == exception_msg

    finally:
        del app.dependency_overrides[get_users_service]
