from uuid import UUID

from psycopg.errors import NotNullViolation, UniqueViolation
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from backend.exceptions.users import (
    EmailAlreadyExistError,
    UserCreationError,
    UserRetrievalError,
    UserUpdateError,
)
from backend.models.users import Users


class UsersRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def update(self, user: Users) -> Users:
        try:
            self.db.flush()
            self.db.refresh(user)
            self.db.commit()
            return user
        except IntegrityError as error:
            self.db.rollback()
            if isinstance(error.orig, UniqueViolation):
                raise EmailAlreadyExistError("Email already exists") from error
            raise UserUpdateError("User could not be updated") from error
        except SQLAlchemyError as error:
            self.db.rollback()
            raise UserUpdateError("User could not be updated") from error

    def get(self, user_id: UUID) -> Users | None:
        try:
            return self.db.get(Users, user_id)
        except SQLAlchemyError as error:
            raise UserRetrievalError("User could not be retrieved") from error

    def add(self, user: Users) -> Users:
        try:
            self.db.add(user)
            self.db.flush()
            self.db.refresh(user)
            self.db.commit()

            return user
        except IntegrityError as error:
            self.db.rollback()
            if isinstance(error.orig, NotNullViolation):
                raise UserCreationError("Required user field is missing") from error
            raise EmailAlreadyExistError("Email already exists") from error
        except SQLAlchemyError as error:
            self.db.rollback()
            raise UserCreationError("User could not be created") from error
