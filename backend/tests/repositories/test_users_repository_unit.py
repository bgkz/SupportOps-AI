from datetime import UTC, datetime
from unittest.mock import Mock, call
from uuid import UUID

import pytest
from psycopg.errors import NotNullViolation, UniqueViolation
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from backend.exceptions.users import (
    EmailAlreadyExistError,
    UserCreationError,
    UserRetrievalError,
    UserUpdateError,
)
from backend.models.users import UserRole, Users
from backend.repositories.users_repository import UsersRepository


@pytest.mark.parametrize(
    ("orig_exc", "constraint_name", "expected_exception", "expected_message"),
    [
        (
            UniqueViolation,
            "users_email_key",
            EmailAlreadyExistError,
            "Email already exists",
        ),
        (UniqueViolation, "users_pkey", UserUpdateError, "User could not be updated"),
        (UniqueViolation, None, UserUpdateError, "User could not be updated"),
        (Exception, None, UserUpdateError, "User could not be updated"),
    ],
    ids=[
        "email-unique-violation",
        "other-unique-constraint",
        "missing-constraint-name",
        "other-integrity-error",
    ],
)
@pytest.mark.parametrize("operation", ["flush", "commit"])
def test_update_rolls_back_on_update_error(
    operation: str,
    orig_exc: type[Exception],
    constraint_name: str | None,
    expected_exception: type[Exception],
    expected_message: str,
) -> None:
    db = Mock(spec=Session)
    original_error = orig_exc("Update failed")
    if isinstance(original_error, UniqueViolation) and constraint_name is not None:
        original_error = UniqueViolation(
            "Update failed",
            info={ord("n"): constraint_name.encode()},
        )
    error = IntegrityError(
        statement=None,
        params=None,
        orig=original_error,
    )
    getattr(db, operation).side_effect = error
    repo = UsersRepository(db=db)
    user = Users(
        id=UUID("550e8400-e29b-41d4-a716-446655440000"),
        user_role=UserRole.CUSTOMER,
        email="test.user@example.com",
        hashed_password="fake-hash",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    with pytest.raises(expected_exception, match=expected_message) as exc_info:
        repo.update(user=user)

    assert exc_info.value.__cause__ is error
    expected_calls = [call.flush()]
    if operation == "commit":
        expected_calls.extend([call.refresh(user), call.commit()])
    expected_calls.append(call.rollback())
    assert db.mock_calls == expected_calls


@pytest.mark.parametrize("operation", ["flush", "refresh", "commit"])
def test_update_rolls_back_on_database_error(operation: str) -> None:
    db = Mock(spec=Session)
    error = SQLAlchemyError("Database unavailable")
    getattr(db, operation).side_effect = error
    repo = UsersRepository(db=db)
    user = Users(
        id=UUID("550e8400-e29b-41d4-a716-446655440000"),
        user_role=UserRole.CUSTOMER,
        email="test.user@example.com",
        hashed_password="fake-hash",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    with pytest.raises(UserUpdateError) as exc_info:
        repo.update(user=user)

    assert exc_info.value.__cause__ is error
    db.rollback.assert_called_once()

    if operation != "commit":
        db.commit.assert_not_called()


def test_update_commits_refreshes_and_returns_user() -> None:
    user = Users(
        id=UUID("550e8400-e29b-41d4-a716-446655440000"),
        user_role=UserRole.CUSTOMER,
        email="test.user@example.com",
        hashed_password="fake-hash",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    db = Mock(spec=Session)
    repo = UsersRepository(db=db)

    updated_user = repo.update(user=user)

    assert user is updated_user

    assert db.mock_calls == [
        call.flush(),
        call.refresh(user),
        call.commit(),
    ]


def test_get_wraps_database_error_in_user_retrieval_error() -> None:
    db = Mock(spec=Session)
    error = SQLAlchemyError("Database unavailable")
    db.get.side_effect = error
    repo = UsersRepository(db=db)

    with pytest.raises(
        UserRetrievalError, match="User could not be retrieved"
    ) as exc_info:
        repo.get(user_id=UUID("550e8400-e29b-41d4-a716-446655440000"))

    assert exc_info.value.__cause__ is error


def test_get_returns_none_for_unknown_user_id() -> None:
    db = Mock(spec=Session)
    db.get.return_value = None
    user_id = UUID("550e8400-e29b-41d4-a716-446655440000")
    repo = UsersRepository(db=db)

    user = repo.get(user_id=user_id)

    assert user is None
    db.get.assert_called_once_with(Users, user_id)


def test_get_returns_user_from_session() -> None:
    db = Mock(spec=Session)
    expected_user = Users(
        id=UUID("550e8400-e29b-41d4-a716-446655440000"),
        user_role=UserRole.CUSTOMER,
        email="test.user@example.com",
        hashed_password="fake-hash",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db.get.return_value = expected_user

    repo = UsersRepository(db=db)
    user = repo.get(user_id=expected_user.id)

    assert user is expected_user
    db.get.assert_called_once_with(Users, expected_user.id)


def test_add_not_null_violation():

    db = Mock(spec=Session)

    db.flush.side_effect = IntegrityError(
        statement=None,
        params=None,
        orig=NotNullViolation("Testfehler"),
    )
    repo = UsersRepository(db)

    with pytest.raises(
        UserCreationError, match="Required user field is missing"
    ) as exc_info:
        repo.add(Users(user_role=None))

    assert isinstance(exc_info.value.__cause__.orig, NotNullViolation)

    db.rollback.assert_called_once()
    db.commit.assert_not_called()


@pytest.mark.parametrize(
    ("exception", "expected_exception"),
    [
        (
            IntegrityError(statement=None, params=None, orig=Exception("Testfehler")),
            EmailAlreadyExistError,
        ),
        (SQLAlchemyError("Testfehler"), UserCreationError),
    ],
)
@pytest.mark.parametrize("operation", ["add", "flush", "refresh", "commit"])
def test_add_user_rolls_back_on_database_error(
    exception: SQLAlchemyError,
    expected_exception: type[Exception],
    operation: str,
) -> None:
    db = Mock(spec=Session)
    getattr(db, operation).side_effect = exception
    repo = UsersRepository(db)
    user = Users(
        user_role=UserRole.CUSTOMER,
        email="test.user@example.com",
        hashed_password="test-hash",
    )

    with pytest.raises(expected_exception) as exc_info:
        repo.add(user=user)

    assert exc_info.value.__cause__ is exception
    db.rollback.assert_called_once()
    if operation == "commit":
        db.commit.assert_called_once()
    else:
        db.commit.assert_not_called()


def test_add_commits_and_returns_user() -> None:
    expected_user = Users(
        id=UUID("550e8400-e29b-41d4-a716-446655440000"),
        user_role=UserRole.CUSTOMER,
        email="test.user@example.com",
        hashed_password="fake-hash",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db = Mock(spec=Session)
    repo = UsersRepository(db=db)
    user_added = repo.add(user=expected_user)

    assert user_added is expected_user
    db.add.assert_called_once_with(expected_user)
    db.flush.assert_called_once()
    db.refresh.assert_called_once_with(expected_user)
    db.commit.assert_called_once()
    db.rollback.assert_not_called()
