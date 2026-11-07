from fastapi import Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.repositories.email_verification_tokens_repository import (
    EmailVerificationTokensRepository,
)
from backend.services.email_verification_tokens_service import (
    EmailVerificationTokensService,
)


def get_email_verification_tokens_service(
    db: Session = Depends(get_db),  # noqa: B008
) -> EmailVerificationTokensService:
    return EmailVerificationTokensService(repo=EmailVerificationTokensRepository(db=db))
