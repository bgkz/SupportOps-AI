from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.exceptions.email_verification_tokens import (
    EmailVerificationTokenCreationError,
    EmailVerificationTokenRetrievalError,
)
from backend.models.email_verification_tokens import EmailVerificationTokens


class EmailVerificationTokensRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_token_hash(self, token_hash: str) -> EmailVerificationTokens | None:
        statement = select(EmailVerificationTokens).where(
            EmailVerificationTokens.token_hash == token_hash
        )
        try:
            return self.db.execute(statement).scalar_one_or_none()
        except SQLAlchemyError as error:
            raise EmailVerificationTokenRetrievalError(
                "Verification Token could not be retrieved"
            ) from error

    def add(self, token: EmailVerificationTokens) -> EmailVerificationTokens:
        try:
            self.db.add(token)
            self.db.flush()
            self.db.refresh(token)
            self.db.commit()
            return token
        except SQLAlchemyError as error:
            self.db.rollback()
            raise EmailVerificationTokenCreationError(
                "Email verification token could not be created"
            ) from error
