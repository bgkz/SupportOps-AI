from uuid import UUID

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.models.users import UserRole, Users
from backend.schemas.users import CreateUserResponse
from backend.security.passwords import verify_password


@pytest.mark.parametrize(
    ("payload", "missing_fields"),
    [
        ({"email": "valid-mail@outlook.de"}, {"password"}),
        ({"password": "valid-password123"}, {"email"}),
        ({}, {"email", "password"}),
    ],
)
def test_create_user_rejects_missing_fields(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    db: Session,
    payload: dict[str, str],
    missing_fields: set[str],
) -> None:
    monkeypatch.setattr(
        "backend.security.api_key.BACKEND_API_KEY",
        "test-api-key",
    )

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
    assert all(error["msg"] == "Field required" for error in errors)

    assert db.execute(select(func.count()).select_from(Users)).scalar_one() == 0


@pytest.mark.parametrize(
    ("email", "password"),
    [
        ("", "Secret Password 123"),
        (None, "Secret Password 123"),
        ("   ", "Secret Password 123"),
        ("example@outlook.com", "sss"),
        ("example@outlook.com", None),
        ("example@outlook.com", ""),
        ("keine-email", "Secret Password 123"),
    ],
)
def test_create_user_rejects_invalid_request(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    db: Session,
    email: str | None,
    password: str | None,
) -> None:
    monkeypatch.setattr(
        "backend.security.api_key.BACKEND_API_KEY",
        "test-api-key",
    )
    response = client.post(
        "/users/",
        headers={"X-API-Key": "test-api-key"},
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    assert db.execute(select(func.count()).select_from(Users)).scalar_one() == 0


def test_create_user_rejects_duplicate_email(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, db: Session
) -> None:
    monkeypatch.setattr(
        "backend.security.api_key.BACKEND_API_KEY",
        "test-api-key",
    )

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


def test_create_user(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, db: Session
) -> None:
    monkeypatch.setattr(
        "backend.security.api_key.BACKEND_API_KEY",
        "test-api-key",
    )
    response = client.post(
        "/users/",
        headers={"X-API-Key": "test-api-key"},
        json={
            "email": "example@outlook.com",
            "password": "Secret Password 123",
        },
    )

    assert "password" not in response.json()
    assert "hashed_password" not in response.json()

    assert response.status_code == status.HTTP_201_CREATED
    create_user_response = CreateUserResponse.model_validate(response.json())
    assert isinstance(create_user_response.id, UUID)
    assert create_user_response.user_role == UserRole.CUSTOMER
    assert str(create_user_response.email) == "example@outlook.com"

    user = db.get(Users, create_user_response.id)
    assert user is not None
    assert user.email == "example@outlook.com"
    assert verify_password("Secret Password 123", user.hashed_password)
