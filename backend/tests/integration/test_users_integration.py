from datetime import datetime
from uuid import UUID, uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.models.users import UserRole, Users
from backend.schemas.users import UserResponse
from backend.security.passwords import hash_password, verify_password


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
def test_change_email_rejects_invalid_or_missing_api_key(
    client: TestClient,
    headers: dict[str, str],
) -> None:
    response = client.patch(
        f"/users/{uuid4()}/email",
        headers=headers,
        json={"email": "example@example.com"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "API-Key missing or invalid"


def test_change_email_returns_422_when_user_id_is_invalid(client: TestClient) -> None:
    response = client.patch(
        "/users/not-a-uuid/email",
        headers={"X-API-Key": "test-api-key"},
        json={"email": "updated.user@example.com"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert any(
        error["loc"] == ["path", "user_id"] and error["type"] == "uuid_parsing"
        for error in response.json()["detail"]
    )


def test_change_email_rejects_missing_email(client: TestClient) -> None:
    response = client.patch(
        f"/users/{uuid4()}/email",
        headers={"X-API-Key": "test-api-key"},
        json={},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert any(
        error["loc"] == ["body", "email"] and error["type"] == "missing"
        for error in response.json()["detail"]
    )


def test_change_email_returns_409_when_email_already_exists(
    client: TestClient, db: Session
) -> None:
    old_timestamp = datetime(2020, 1, 1)
    user = Users(
        id=uuid4(),
        user_role=UserRole.CUSTOMER,
        email="target.user@example.com",
        hashed_password=hash_password("TestPassword123!"),
        created_at=old_timestamp,
        updated_at=old_timestamp,
    )
    other_user = Users(
        id=uuid4(),
        user_role=UserRole.CUSTOMER,
        email="other.user@example.com",
        hashed_password=hash_password("OtherPassword123!"),
        created_at=old_timestamp,
        updated_at=old_timestamp,
    )
    db.add_all([user, other_user])
    db.commit()
    response = client.patch(
        f"/users/{user.id}/email",
        headers={"X-API-Key": "test-api-key"},
        json={"email": "other.user@example.com"},
    )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["detail"] == "Email already exists"
    db.refresh(user)
    db.refresh(other_user)

    assert user.email == "target.user@example.com"
    assert user.updated_at == old_timestamp

    assert other_user.email == "other.user@example.com"
    assert other_user.updated_at == old_timestamp


def test_change_email_returns_404_when_user_not_found(client: TestClient) -> None:
    response = client.patch(
        f"/users/{uuid4()}/email",
        headers={"X-API-Key": "test-api-key"},
        json={"email": "update.target@example.com"},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "User not found"


def test_change_email_updates_only_target_user(client: TestClient, db: Session) -> None:
    old_timestamp = datetime(2020, 1, 1)
    target_user = Users(
        id=uuid4(),
        user_role=UserRole.CUSTOMER,
        email="target.user@example.com",
        hashed_password=hash_password("TestPassword123!"),
        created_at=old_timestamp,
        updated_at=old_timestamp,
    )
    other_user = Users(
        id=uuid4(),
        user_role=UserRole.CUSTOMER,
        email="other.user@example.com",
        hashed_password=hash_password("OtherPassword123!"),
        created_at=old_timestamp,
        updated_at=old_timestamp,
    )
    db.add_all([target_user, other_user])
    db.commit()
    response = client.patch(
        f"/users/{target_user.id}/email",
        headers={"X-API-Key": "test-api-key"},
        json={"email": "update.target@example.com"},
    )

    assert response.status_code == status.HTTP_200_OK
    db.refresh(target_user)
    db.refresh(other_user)

    assert target_user.email == "update.target@example.com"
    assert target_user.updated_at > old_timestamp

    assert other_user.email == "other.user@example.com"
    assert other_user.updated_at == old_timestamp


def test_change_email_with_same_email_returns_200_and_preserves_updated_at(
    client: TestClient, db: Session
) -> None:
    old_timestamp = datetime(2020, 1, 1)
    email = "test.user@example.com"
    user = Users(
        id=uuid4(),
        user_role=UserRole.CUSTOMER,
        email=email,
        hashed_password=hash_password("TestPassword123!"),
        created_at=old_timestamp,
        updated_at=old_timestamp,
    )
    db.add(user)
    db.commit()
    response = client.patch(
        f"/users/{user.id}/email",
        headers={"X-API-Key": "test-api-key"},
        json={"email": email},
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "password" not in data
    assert "hashed_password" not in data
    user_response = UserResponse.model_validate(data)
    assert user_response.id == user.id
    assert user_response.email == email
    assert user_response.user_role == user.user_role
    assert user_response.created_at == old_timestamp
    assert user_response.updated_at == old_timestamp

    db.refresh(user)
    assert user.email == email
    assert user.updated_at == old_timestamp


@pytest.mark.parametrize(
    "invalid_email",
    [
        "",
        "   ",
        None,
        "invalid-email",
        "user@",  # Domain fehlt
        "@example.com",  # Lokaler Teil fehlt
        "user@@example.com",
        "user name@example.com",  # Leerzeichen im lokalen Teil
        "user@exam ple.com",  # Leerzeichen in der Domain
        "user@example..com",
        "user@-example.com",
        "@@@@@@@.com",
    ],
    ids=[
        "empty-email",
        "whitespace-email",
        "null-email",
        "missing-at-sign",
        "missing-domain",
        "missing-local-part",
        "multiple-at-signs",
        "space-in-local-part",
        "space-in-domain",
        "consecutive-dots-in-domain",
        "domain-starts-with-hyphen",
        "only-at-signs-before-dot",
    ],
)
def test_change_email_rejects_invalid_email_requests(
    client: TestClient, invalid_email: str | None
) -> None:

    response = client.patch(
        f"/users/{uuid4()}/email",
        headers={"X-API-Key": "test-api-key"},
        json={"email": invalid_email},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    assert any(error["loc"] == ["body", "email"] for error in response.json()["detail"])


def test_change_email_updates_user_and_returns_response_model(
    client: TestClient, db: Session
) -> None:

    old_timestamp = datetime(2020, 1, 1)
    new_email = "updated-email@example.com"
    original_password_hash = hash_password("TestPassword123!")
    test_user = Users(
        id=uuid4(),
        user_role=UserRole.CUSTOMER,
        email="test.user@example.com",
        hashed_password=original_password_hash,
        created_at=old_timestamp,
        updated_at=old_timestamp,
    )
    db.add(test_user)
    db.commit()

    response = client.patch(
        f"/users/{test_user.id}/email",
        headers={"X-API-Key": "test-api-key"},
        json={"email": new_email},
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "password" not in data
    assert "hashed_password" not in data
    user_response = UserResponse.model_validate(data)
    assert user_response.id == test_user.id
    assert user_response.email == new_email
    assert user_response.user_role == test_user.user_role
    assert user_response.created_at == old_timestamp
    assert user_response.updated_at > old_timestamp

    db.refresh(test_user)
    assert test_user.email == new_email
    assert test_user.updated_at == user_response.updated_at
    assert test_user.hashed_password == original_password_hash


def test_get_user_returns_422_when_user_id_is_invalid(
    client: TestClient,
) -> None:
    response = client.get(
        "/users/not-a-uuid",
        headers={"X-API-Key": "test-api-key"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert any(
        error["loc"] == ["path", "user_id"] and error["type"] == "uuid_parsing"
        for error in response.json()["detail"]
    )


@pytest.mark.parametrize(
    "headers",
    [
        {"X-API-Key": "wrong-api-key"},
        {},
    ],
    ids=["invalid-api-key", "missing-api-key"],
)
def test_get_user_rejects_invalid_or_missing_api_key(
    client: TestClient,
    headers: dict[str, str],
) -> None:
    response = client.get(f"/users/{uuid4()}", headers=headers)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "API-Key missing or invalid"


def test_get_user_returns_404_when_user_not_found(
    client: TestClient, db: Session
) -> None:
    existing_user = Users(
        id=uuid4(),
        user_role=UserRole.CUSTOMER,
        email="test.user@example.com",
        hashed_password=hash_password("TestPassword123!"),
        created_at=datetime(2026, 1, 1, 12, 0, 0),
        updated_at=datetime(2026, 1, 2, 14, 30, 0),
    )
    db.add(existing_user)
    db.commit()

    missing_user_id = UUID("550e8400-e29b-41d4-a716-446655440000")

    response = client.get(
        f"/users/{missing_user_id}",
        headers={"X-API-Key": "test-api-key"},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "User not found"


def test_get_user_returns_expected_public_fields(
    client: TestClient,
    db: Session,
) -> None:
    expected_user = Users(
        id=uuid4(),
        user_role=UserRole.CUSTOMER,
        email="test.user@example.com",
        hashed_password=hash_password("TestPassword123!"),
        created_at=datetime(2026, 1, 1, 12, 0, 0),
        updated_at=datetime(2026, 1, 2, 14, 30, 0),
    )
    db.add(expected_user)
    db.commit()

    response = client.get(
        f"/users/{expected_user.id}",
        headers={"X-API-Key": "test-api-key"},
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert "password" not in data
    assert "hashed_password" not in data

    user_response = UserResponse.model_validate(data)

    assert user_response.id == expected_user.id
    assert user_response.user_role == expected_user.user_role
    assert user_response.email == expected_user.email
    assert user_response.created_at == expected_user.created_at
    assert user_response.updated_at == expected_user.updated_at


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
