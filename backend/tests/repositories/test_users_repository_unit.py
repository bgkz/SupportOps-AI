from datetime import UTC, datetime
from unittest.mock import Mock
from uuid import UUID

import pytest
from psycopg.errors import NotNullViolation
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from backend.exceptions.users import (
    EmailAlreadyExistError,
    UserCreationError,
    UserRetrievalError,
)
from backend.models.users import UserRole, Users
from backend.repositories.users_repository import UsersRepository


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
