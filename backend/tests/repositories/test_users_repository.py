from unittest.mock import Mock

import pytest
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from backend.exceptions.users import EmailAlreadyExistError, UserCreationError
from backend.models.users import UserRole, Users
from backend.repositories.users_repository import UsersRepository


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
def test_rollback(
    exception: SQLAlchemyError, expected_exception: type[Exception]
) -> None:
    db = Mock(spec=Session)
    db.add.side_effect = exception
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
    db.commit.assert_not_called()
