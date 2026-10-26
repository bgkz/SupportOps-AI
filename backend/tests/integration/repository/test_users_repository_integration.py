from datetime import datetime
from uuid import UUID, uuid4

import pytest
from psycopg.errors import NotNullViolation, UniqueViolation
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, InvalidRequestError, SQLAlchemyError
from sqlalchemy.orm import Session

from backend.exceptions.users import (
    EmailAlreadyExistError,
    UserCreationError,
    UserUpdateError,
)
from backend.models.users import UserRole, Users
from backend.repositories.users_repository import UsersRepository
from backend.security.passwords import hash_password


def test_update_rejects_null_email(db: Session) -> None:
    repository = UsersRepository(db=db)
    old_timestamp = datetime(2020, 1, 1)
    user = repository.add(
        Users(
            email="original-email@outlook.de",
            hashed_password=hash_password(password="LongPassword123"),
            user_role=UserRole.CUSTOMER,
            updated_at=old_timestamp,
        )
    )
    user_id = user.id
    user.email = None

    with pytest.raises(UserUpdateError, match="User could not be updated") as exc_info:
        repository.update(user=user)

    cause = exc_info.value.__cause__
    assert isinstance(cause, IntegrityError)
    assert isinstance(cause.orig, NotNullViolation)

    db.expunge_all()

    stored_user = db.get(Users, user_id)

    assert stored_user is not None
    assert stored_user.email == "original-email@outlook.de"
    assert stored_user.updated_at == old_timestamp


def test_update_rejects_detached_user(db: Session) -> None:
    repository = UsersRepository(db=db)
    old_timestamp = datetime(2020, 1, 1)
    user = repository.add(
        Users(
            email="original-email@outlook.de",
            hashed_password=hash_password(password="LongPassword123"),
            user_role=UserRole.CUSTOMER,
            updated_at=old_timestamp,
        )
    )
    user_id = user.id

    db.expunge_all()
    user.email = "updated-email@outlook.de"

    with pytest.raises(UserUpdateError, match="User could not be updated") as exc_info:
        repository.update(user=user)

    assert isinstance(exc_info.value.__cause__, InvalidRequestError)

    stored_user = db.get(Users, user_id)

    assert stored_user is not None
    assert stored_user.email == "original-email@outlook.de"
    assert stored_user.updated_at == old_timestamp


def test_update_rejects_duplicate_email(db: Session) -> None:
    repository = UsersRepository(db=db)
    old_timestamp = datetime(2020, 1, 1)
    already_existing_email = "existing-email@outlook.de"
    repository.add(
        Users(
            email=already_existing_email,
            hashed_password=hash_password(password="LongPassword123"),
            user_role=UserRole.CUSTOMER,
            updated_at=old_timestamp,
        )
    )

    user = repository.add(
        Users(
            email="dummy-email@outlook.de",
            hashed_password=hash_password(password="LongPassword123"),
            user_role=UserRole.CUSTOMER,
            updated_at=old_timestamp,
        )
    )

    user_id = user.id

    user.email = already_existing_email

    with pytest.raises(
        EmailAlreadyExistError, match="Email already exists"
    ) as exc_info:
        repository.update(user=user)

    cause = exc_info.value.__cause__
    assert isinstance(cause, IntegrityError)
    assert isinstance(cause.orig, UniqueViolation)

    db.expunge_all()

    stored_user = db.get(Users, user_id)

    assert stored_user is not None
    assert stored_user.email == "dummy-email@outlook.de"
    assert stored_user.updated_at == old_timestamp


def test_update_changes_target_email_and_preserves_other_user_email(
    db: Session,
) -> None:
    repository = UsersRepository(db=db)
    old_timestamp = datetime(2020, 1, 1)
    target_user = repository.add(
        Users(
            email="valid-email@outlook.de",
            hashed_password=hash_password(password="LongPassword123"),
            user_role=UserRole.CUSTOMER,
            updated_at=old_timestamp,
        )
    )

    untouched_user = repository.add(
        Users(
            email="another-persons-email@outlook.de",
            hashed_password=hash_password(password="AnotherPassword123"),
            user_role=UserRole.CUSTOMER,
            updated_at=old_timestamp,
        )
    )
    user_id = target_user.id
    untouched_user_id = untouched_user.id

    target_user.email = "updated-email@outlook.de"
    updated_user = repository.update(user=target_user)

    assert updated_user is target_user
    assert updated_user.email == "updated-email@outlook.de"
    assert updated_user.updated_at > old_timestamp

    db.expunge_all()

    stored_user = db.get(Users, user_id)
    stored_untouched_user = db.get(Users, untouched_user_id)

    assert stored_user is not None
    assert stored_user.email == "updated-email@outlook.de"
    assert stored_user.updated_at > old_timestamp

    assert stored_untouched_user is not None
    assert stored_untouched_user.email == "another-persons-email@outlook.de"
    assert stored_untouched_user.updated_at == old_timestamp


def test_update_persists_changed_email(db: Session) -> None:
    repository = UsersRepository(db=db)
    old_timestamp = datetime(2020, 1, 1)
    user = repository.add(
        Users(
            email="original-email@example.com",
            hashed_password="fake-hash",
            user_role=UserRole.CUSTOMER,
            created_at=old_timestamp,
            updated_at=old_timestamp,
        )
    )
    user_id = user.id

    user.email = "updated-email@outlook.de"
    updated_user = repository.update(user=user)

    assert updated_user is user
    assert updated_user.email == "updated-email@outlook.de"

    assert updated_user.updated_at > old_timestamp
    assert updated_user.created_at == old_timestamp

    db.expunge_all()

    stored_user = db.get(Users, user_id)

    assert stored_user is not None
    assert stored_user.email == "updated-email@outlook.de"
    assert stored_user.updated_at > old_timestamp


def test_get_returns_target_user_when_multiple_users_exist(db: Session) -> None:

    repository = UsersRepository(db=db)
    target_user = repository.add(
        Users(
            email="valid-email@outlook.de",
            hashed_password=hash_password(password="LongPassword123"),
            user_role=UserRole.CUSTOMER,
        )
    )
    repository.add(
        Users(
            email="another-cool-email@outlook.de",
            hashed_password=hash_password(password="solid-password-xDxDxD"),
            user_role=UserRole.CUSTOMER,
        )
    )

    assert db.scalar(select(func.count()).select_from(Users)) == 2

    target_user_id = target_user.id
    db.expunge_all()

    target_user_found = repository.get(user_id=target_user_id)

    assert target_user_found is not None
    assert target_user_found.id == target_user_id
    assert target_user_found.email == "valid-email@outlook.de"


def test_get_returns_none_for_unknown_user_id(db: Session) -> None:
    repository = UsersRepository(db=db)
    user = repository.get(user_id=uuid4())

    assert user is None


def test_get_returns_existing_user(db: Session) -> None:
    hashed = hash_password(password="LongPassword123")
    repository = UsersRepository(db=db)
    user_added = repository.add(
        Users(
            email="valid-email@outlook.de",
            hashed_password=hashed,
            user_role=UserRole.CUSTOMER,
        )
    )
    user_id = user_added.id
    db.expunge_all()
    user_found = repository.get(user_id=user_id)

    assert user_found is not None
    assert user_found.id == user_id
    assert user_found.email == "valid-email@outlook.de"
    assert isinstance(user_found.created_at, datetime)
    assert isinstance(user_found.updated_at, datetime)
    assert user_found.hashed_password == hashed
    assert user_found.user_role == UserRole.CUSTOMER


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
