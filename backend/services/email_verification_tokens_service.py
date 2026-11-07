from datetime import UTC, datetime, timedelta
from uuid import UUID

from backend.exceptions.email_verification_tokens import (
    EmailVerificationTokenExpiredError,
    EmailVerificationTokenNotFound,
)
from backend.models.email_verification_tokens import EmailVerificationTokens
from backend.repositories.email_verification_tokens_repository import (
    EmailVerificationTokensRepository,
)


class EmailVerificationTokensService:
    def __init__(self, repo: EmailVerificationTokensRepository):
        self.repo = repo

    def verify(self, token_hash: str) -> EmailVerificationTokens:
        token = self.repo.get_by_token_hash(token_hash=token_hash)
        if token is None:
            raise EmailVerificationTokenNotFound("Token not found")
        if token.expires_at <= datetime.now(UTC):
            raise EmailVerificationTokenExpiredError(
                "Verification link has expired. Please request a new one."
            )
        return token

    def create_token(self, user_id: UUID, token_hash: str) -> EmailVerificationTokens:
        return self.repo.add(
            EmailVerificationTokens(
                user_id=user_id,
                token_hash=token_hash,
                expires_at=datetime.now(UTC) + timedelta(minutes=30),
            )
        )
