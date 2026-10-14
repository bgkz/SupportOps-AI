from uuid import UUID

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.models.users import UserRole, Users
from backend.schemas.users import UserResponse
from backend.security.passwords import verify_password


@pytest.fixture(autouse=True)
def configure_test_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "backend.security.api_key.BACKEND_API_KEY",
        "test-api-key",
    )


@pytest.mark.parametrize(
    "headers",
    [
        {"X-API-Key": "wrong-api-key"},
        {},
    ],
    ids=["invalid-api-key", "missing-api-key"],
)
def test_create_user_rejects_invalid_or_missing_api_key(
    client: TestClient,
    db: Session,
    headers: dict[str, str],
) -> None:
    response = client.post(
        "/users/",
        headers=headers,
        json={
            "email": "example@outlook.com",
            "password": "Secret Password 123",
        },
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "API-Key missing or invalid"
    assert db.execute(select(func.count()).select_from(Users)).scalar_one() == 0


@pytest.mark.parametrize(
    ("payload", "missing_fields"),
    [
        ({"email": "valid-mail@outlook.de"}, {"password"}),
        ({"password": "valid-password123"}, {"email"}),
        ({}, {"email", "password"}),
    ],
    ids=["missing-password", "missing-email", "missing-both-fields"],
)
def test_create_user_rejects_missing_fields(
    client: TestClient,
    db: Session,
    payload: dict[str, str],
    missing_fields: set[str],
) -> None:
    response = client.post(
        "/users/",
        headers={"X-API-Key": "test-api-key"},
        json=payload,
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    errors = response.json()["detail"]
    assert {tuple(error["loc"]) for error in errors} == {
        ("body", field) for field in missing_fields
    }
    assert all(error["type"] == "missing" for error in errors)

    assert db.execute(select(func.count()).select_from(Users)).scalar_one() == 0


@pytest.mark.parametrize(
    ("email", "password", "invalid_field"),
    [
        ("", "Secret Password 123", "email"),
        (None, "Secret Password 123", "email"),
        ("   ", "Secret Password 123", "email"),
        ("example@outlook.com", "sss", "password"),
        ("example@outlook.com", None, "password"),
        ("example@outlook.com", "", "password"),
        ("keine-email", "Secret Password 123", "email"),
    ],
    ids=[
        "empty-email",
        "null-email",
        "whitespace-email",
        "short-password",
        "null-password",
        "empty-password",
        "malformed-email",
    ],
)
def test_create_user_rejects_invalid_request(
    client: TestClient,
    db: Session,
    email: str | None,
    password: str | None,
    invalid_field: str,
) -> None:
    response = client.post(
        "/users/",
        headers={"X-API-Key": "test-api-key"},
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    errors = response.json()["detail"]
    assert {tuple(error["loc"]) for error in errors} == {("body", invalid_field)}

    assert db.execute(select(func.count()).select_from(Users)).scalar_one() == 0


def test_create_user_rejects_duplicate_email(client: TestClient, db: Session) -> None:
    response = client.post(
        "/users/",
        headers={"X-API-Key": "test-api-key"},
        json={
            "email": "example@outlook.com",
            "password": "Secret Password 123",
        },
    )
    assert response.status_code == status.HTTP_201_CREATED

    response_duplicate_email = client.post(
        "/users/",
        headers={"X-API-Key": "test-api-key"},
        json={
            "email": "example@outlook.com",
            "password": "Secret Password 123",
        },
    )

    assert response_duplicate_email.status_code == status.HTTP_409_CONFLICT
    assert response_duplicate_email.json()["detail"] == "Email already exists"

    stmt = (
        select(func.count())
        .select_from(Users)
        .where(Users.email == "example@outlook.com")
    )
    assert db.execute(stmt).scalar_one() == 1


def test_create_user(client: TestClient, db: Session) -> None:
    response = client.post(
        "/users/",
        headers={"X-API-Key": "test-api-key"},
        json={
            "email": "example@outlook.com",
            "password": "Secret Password 123",
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "password" not in data
    assert "hashed_password" not in data

    create_user_response = UserResponse.model_validate(data)
    assert isinstance(create_user_response.id, UUID)
    assert create_user_response.user_role == UserRole.CUSTOMER
    assert str(create_user_response.email) == "example@outlook.com"

    user = db.get(Users, create_user_response.id)
    assert user is not None
    assert user.email == "example@outlook.com"
    assert verify_password("Secret Password 123", user.hashed_password)
