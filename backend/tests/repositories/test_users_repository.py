from unittest.mock import Mock

import pytest
from psycopg.errors import NotNullViolation
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from backend.exceptions.users import EmailAlreadyExistError, UserCreationError
from backend.models.users import UserRole, Users
from backend.repositories.users_repository import UsersRepository


def test_add_not_null_violation():

    db = Mock(spec=Session)
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
