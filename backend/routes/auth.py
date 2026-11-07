import secrets

from fastapi import APIRouter, HTTPException, status
from fastapi.params import Depends

from backend.dependencies.email_verification_tokens import (
    get_email_verification_tokens_service,
)
from backend.dependencies.users import get_users_service
from backend.exceptions.email_verification_tokens import (
    EmailVerificationTokenExpiredError,
    EmailVerificationTokenNotFound,
    EmailVerificationTokenRetrievalError,
)
from backend.exceptions.users import (
    EmailAlreadyExistError,
    UserCreationError,
    UserNotFoundError,
    UserUpdateError,
)
from backend.jobs.auth import send_email_verification
from backend.redis_queue import job
from backend.schemas.auth import RegisterRequest
from backend.schemas.users import UserResponse
from backend.services.email_verification_tokens_service import (
    EmailVerificationTokensService,
)
from backend.services.users_service import UsersService

router = APIRouter(prefix="/auth")


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
