from datetime import datetime
from uuid import UUID

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.exceptions.users import EmailAlreadyExistError, UserCreationError
from backend.models.users import UserRole, Users
from backend.repositories.users_repository import UsersRepository
from backend.security.passwords import hash_password


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

    assert duplicate_user.email == user.email

    repository.add(user=user)

    with pytest.raises(EmailAlreadyExistError, match="Email already exists"):
        repository.add(user=duplicate_user)
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
