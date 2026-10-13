from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from backend.exceptions.users import EmailAlreadyExistError, UserCreationError
from backend.models.users import Users


class UsersRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, user: Users) -> Users:
        try:
            self.db.add(user)
            self.db.flush()
            self.db.refresh(user)
            self.db.commit()

            return user
        except IntegrityError as error:
            self.db.rollback()
            raise EmailAlreadyExistError("Email already exists") from error
        except SQLAlchemyError as error:
            self.db.rollback()
            raise UserCreationError("User could not be created") from error
