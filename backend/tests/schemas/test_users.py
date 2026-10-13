from datetime import datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

from backend.config import PASSWORD_MIN_LENGTH
from backend.models.users import UserRole, Users
from backend.schemas.users import CreateUserRequest, CreateUserResponse

VALID_TEST_PASSWORD = "langes-passwort-123"
VALID_TEST_EMAIL = "example_email@outlook.com"

TEST_USER_ID = UUID("550e8400-e29b-41d4-a716-446655440000")
TEST_CREATED_AT = datetime(2026, 10, 13, 10, 30, 0)
TEST_UPDATED_AT = datetime(2026, 10, 13, 11, 45, 0)


def test_create_user_response_from_json() -> None:
    data = """
    {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "user_role": "support_agent",
        "email": "example_email@outlook.com",
        "created_at": "2026-10-13T10:30:00",
        "updated_at": "2026-10-13T11:45:00"
    }
    """

    response = CreateUserResponse.model_validate_json(data)

    assert response.id == TEST_USER_ID
    assert response.user_role == UserRole.SUPPORT_AGENT
    assert response.email == VALID_TEST_EMAIL
    assert response.created_at == TEST_CREATED_AT
    assert response.updated_at == TEST_UPDATED_AT


def test_create_user_response_from_strings() -> None:
    response = CreateUserResponse(
        id=str(TEST_USER_ID),
        user_role="customer",
        email=VALID_TEST_EMAIL,
        created_at="2026-10-13T10:30:00",
        updated_at="2026-10-13T11:45:00",
    )

    assert response.id == TEST_USER_ID
    assert response.user_role == UserRole.CUSTOMER
    assert response.created_at == TEST_CREATED_AT
    assert response.updated_at == TEST_UPDATED_AT


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("id", "invalid-UUID"),
        ("user_role", "unkown"),
        ("email", "invalid email"),
        ("created_at", "no date"),
        ("updated_at", "no date"),
    ],
)
def test_create_user_response_invalid_values(field: str, invalid_value: str) -> None:
    values = {
        "id": TEST_USER_ID,
        "user_role": UserRole.CUSTOMER,
        "email": VALID_TEST_EMAIL,
        "created_at": TEST_CREATED_AT,
        "updated_at": TEST_UPDATED_AT,
    }

    values[field] = invalid_value

    with pytest.raises(ValidationError) as exc_info:
        CreateUserResponse.model_validate(values)

    assert [error["loc"] for error in exc_info.value.errors()] == [(field,)]


def test_create_user_response_from_attributes() -> None:
    user = Users(
        id=TEST_USER_ID,
        user_role=UserRole.CUSTOMER,
        email=VALID_TEST_EMAIL,
        hashed_password="test-hash",
        created_at=TEST_CREATED_AT,
        updated_at=TEST_UPDATED_AT,
    )

    response = CreateUserResponse.model_validate(user)

    assert response.id == user.id
    assert response.email == user.email
    assert response.user_role == UserRole.CUSTOMER
    assert response.created_at == TEST_CREATED_AT
    assert response.updated_at == TEST_UPDATED_AT
    assert "hashed_password" not in response.model_dump()


def test_create_user_response_valid_values() -> None:
    response = CreateUserResponse(
        id=TEST_USER_ID,
        user_role=UserRole.CUSTOMER,
        email=VALID_TEST_EMAIL,
        created_at=TEST_CREATED_AT,
        updated_at=TEST_UPDATED_AT,
    )

    assert response.id == TEST_USER_ID
    assert response.user_role == UserRole.CUSTOMER
    assert response.email == VALID_TEST_EMAIL
    assert response.created_at == TEST_CREATED_AT
    assert response.updated_at == TEST_UPDATED_AT


@pytest.mark.parametrize("password", ["", " ", "a" * (PASSWORD_MIN_LENGTH - 1)])
def test_create_user_rejects_invalid_password(password: str) -> None:
    with pytest.raises(ValidationError) as exc_info:
        CreateUserRequest(email=VALID_TEST_EMAIL, password=password)

    assert [error["loc"] for error in exc_info.value.errors()] == [("password",)]


@pytest.mark.parametrize(
    "password", ["a" * PASSWORD_MIN_LENGTH, "a" * (PASSWORD_MIN_LENGTH + 1)]
)
def test_create_user_accepts_valid_password(password: str) -> None:
    request = CreateUserRequest(email=VALID_TEST_EMAIL, password=password)

    assert request.password.get_secret_value() == password


def test_create_user_valid_email_valid_password() -> None:
    request = CreateUserRequest(email=VALID_TEST_EMAIL, password=VALID_TEST_PASSWORD)

    assert request.email == VALID_TEST_EMAIL
    assert request.password.get_secret_value() == VALID_TEST_PASSWORD


@pytest.mark.parametrize("email", ["keine-email", "user@", "@example.com"])
def test_create_user_rejects_invalid_email(email: str) -> None:
    with pytest.raises(ValidationError) as exc_info:
        CreateUserRequest(
            email=email,
            password=VALID_TEST_PASSWORD,
        )

    assert [error["loc"] for error in exc_info.value.errors()] == [("email",)]
