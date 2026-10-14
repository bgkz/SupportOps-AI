from datetime import UTC, datetime
from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from backend.dependencies.users import get_users_service
from backend.exceptions.users import EmailAlreadyExistError, UserCreationError
from backend.main import app
from backend.models.users import UserRole
from backend.schemas.users import CreateUserRequest, UserResponse
from backend.services.users_service import UsersService


@pytest.fixture(autouse=True)
def configure_test_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "backend.security.api_key.BACKEND_API_KEY",
        "test-api-key",
    )


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
