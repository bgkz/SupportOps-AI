from datetime import datetime
from uuid import UUID

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from backend.exceptions.users import EmailAlreadyExistError, UserCreationError
from backend.models.users import UserRole, Users
from backend.repositories.users_repository import UsersRepository
from backend.security.passwords import hash_password


def test_add_user_invalid_role(db: Session) -> None:
    repository = UsersRepository(db)
    hashed = hash_password("Test-Passwort-123")
    invalid_user = Users(
        user_role="unknown",
        email="test.user@example.com",
        hashed_password=hashed,
    )

    with pytest.raises(
        UserCreationError, match="User could not be created"
    ) as exc_info:
        repository.add(user=invalid_user)
    assert isinstance(exc_info.value.__cause__, SQLAlchemyError)

    assert db.scalar(select(func.count()).select_from(Users)) == 0


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("user_role", None),
        ("email", None),
        ("hashed_password", None),
    ],
)
def test_add_user_none_attributes(
    db: Session, field: str, invalid_value: str | None
) -> None:
    repository = UsersRepository(db)
    hashed = hash_password("Test-Passwort-123")
    invalid_user = Users(
        user_role=UserRole.SUPPORT_AGENT,
        email="test.user@example.com",
        hashed_password=hashed,
    )

    setattr(invalid_user, field, invalid_value)

    with pytest.raises(
        UserCreationError, match="Required user field is missing"
    ) as exc_info:
        repository.add(user=invalid_user)
    assert isinstance(exc_info.value.__cause__, SQLAlchemyError)

    assert db.scalar(select(func.count()).select_from(Users)) == 0


def test_add_user_duplicate(db: Session) -> None:
    repository = UsersRepository(db)
    hashed = hash_password("Test-Passwort-123")

    user = Users(
        user_role=UserRole.CUSTOMER,
        email="test.user@example.com",
        hashed_password=hashed,
    )

    duplicate_user = Users(
        user_role=UserRole.CUSTOMER,
        email=user.email,
        hashed_password=hashed,
    )

    repository.add(user=user)

    with pytest.raises(
        EmailAlreadyExistError, match="Email already exists"
    ) as exc_info:
        repository.add(user=duplicate_user)

    assert isinstance(exc_info.value.__cause__, IntegrityError)

    count = db.scalar(
        select(func.count()).select_from(Users).where(Users.email == user.email)
    )

    assert count == 1


def test_add_user(db: Session) -> None:
    repository = UsersRepository(db)
    hashed = hash_password("Test-Passwort-123")

    user = Users(
        user_role=UserRole.CUSTOMER,
        email="test.user@example.com",
        hashed_password=hashed,
    )

    user_added = repository.add(user=user)

    assert isinstance(user_added.id, UUID)
    assert user_added.user_role == UserRole.CUSTOMER
    assert user_added.email == "test.user@example.com"
    assert isinstance(user_added.created_at, datetime)
    assert isinstance(user_added.updated_at, datetime)

    user_id = user_added.id
    db.expunge_all()

    stored_user = db.get(Users, user_id)

    assert stored_user is not None
    assert stored_user.email == "test.user@example.com"
    assert stored_user.user_role == UserRole.CUSTOMER
    assert stored_user.hashed_password == hashed
