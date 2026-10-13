from sqlalchemy.orm import Session

from backend.models.users import Users
from backend.repositories.users_repository import UsersRepository


def test_add_user(db: Session) -> None:
    repository = UsersRepository(db)
    user = Users()
