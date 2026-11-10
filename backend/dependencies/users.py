from fastapi import Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.redis_queue import redis_connection
from backend.repositories.users_repository import UsersRepository
from backend.services.sessions_service import SessionsService
from backend.services.users_service import UsersService


def get_users_service(
    db: Session = Depends(get_db),  # noqa: B008
) -> UsersService:
    return UsersService(users_repo=UsersRepository(db))


def get_sessions_service() -> SessionsService:
    return SessionsService(redis_connection=redis_connection)
