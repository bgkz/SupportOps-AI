import secrets

from fastapi import APIRouter, HTTPException, Response, status
from fastapi.params import Depends

from backend.dependencies.email_verification_tokens import (
    get_email_verification_tokens_service,
)
from backend.dependencies.users import get_sessions_service, get_users_service
from backend.exceptions.auth import InvalidCredentialsError
from backend.exceptions.email_verification_tokens import (
    EmailVerificationTokenExpiredError,
    EmailVerificationTokenNotFound,
    EmailVerificationTokenRetrievalError,
)
from backend.exceptions.users import (
    EmailAlreadyExistError,
    UserCreationError,
    UserNotFoundError,
    UserRetrievalError,
    UserUpdateError,
)
from backend.jobs.auth import send_email_verification
from backend.redis_queue import job
from backend.schemas.auth import LoginRequest, RegisterRequest
from backend.schemas.users import UserResponse
from backend.services.email_verification_tokens_service import (
    EmailVerificationTokensService,
)
from backend.services.sessions_service import SessionsService
from backend.services.users_service import UsersService

router = APIRouter(prefix="/auth")


@router.post("/login", response_model=UserResponse, status_code=status.HTTP_200_OK)
def login(
    login_request: LoginRequest,
    response: Response,
    users_service: UsersService = Depends(get_users_service),  # noqa: B008
    sessions_service: SessionsService = Depends(get_sessions_service),  # noqa: B008
):
    try:
        user = users_service.authenticate(
            email=login_request.email,
            password=login_request.password.get_secret_value(),
        )

        session_id = sessions_service.create_session(user_id=user.id)

        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=86400,
        )

        return user

    except UserRetrievalError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error)
        )
    except InvalidCredentialsError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
        ) from error


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    register_request: RegisterRequest,
    users_service: UsersService = Depends(get_users_service),  # noqa: B008
    email_verification_tokens_service: EmailVerificationTokensService = Depends(  # noqa: B008
        get_email_verification_tokens_service
    ),
):

    try:
        user = users_service.create_user(create_user_request=register_request)
        token_hash = secrets.token_urlsafe(32)
        email_verification_tokens_service.create_token(
            user_id=user.id, token_hash=token_hash
        )

        job.enqueue(send_email_verification, register_request.email, token_hash)

    except EmailAlreadyExistError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error
    except UserCreationError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error


@router.get(
    "/verify-email", response_model=UserResponse, status_code=status.HTTP_200_OK
)
def verify_email(
    token: str,
    users_service: UsersService = Depends(get_users_service),  # noqa: B008
    email_verification_tokens_service: EmailVerificationTokensService = Depends(  # noqa: B008
        get_email_verification_tokens_service
    ),
):
    try:
        verification_token = email_verification_tokens_service.verify(token_hash=token)
        return users_service.verify_email(
            user_id=verification_token.user_id,
        )

    except EmailVerificationTokenNotFound as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))
    except EmailVerificationTokenExpiredError as error:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail=str(error))
    except EmailVerificationTokenRetrievalError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error
    except UserNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))
    except UserUpdateError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error))

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error
