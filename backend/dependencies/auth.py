from typing import Annotated
from uuid import UUID

from fastapi import Cookie, Depends, HTTPException, status

from backend.dependencies.users import get_users_service
from backend.exceptions.users import UserNotFoundError
from backend.models.users import Users
from backend.redis_queue import redis_connection
from backend.services.sessions_service import SessionsService
from backend.services.users_service import UsersService


def get_sessions_service() -> SessionsService:
    return SessionsService(redis_connection=redis_connection)


def get_current_user(
    session_id: Annotated[str | None, Cookie()] = None,
    sessions_service: SessionsService = Depends(get_sessions_service),  # noqa: B008
    users_service: UsersService = Depends(get_users_service),  # noqa: B008
) -> Users:
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    session = sessions_service.get_session(session_id=session_id)

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session invalid or expired",
        )

    try:
        return users_service.get_user(user_id=UUID(session["user_id"]))
    except UserNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated, User does not exist",
        ) from error
