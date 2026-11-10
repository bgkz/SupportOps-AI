from datetime import UTC, datetime
from uuid import UUID

from backend.exceptions.auth import InvalidCredentialsError
from backend.exceptions.users import EmailNotVerifiedError, UserNotFoundError
from backend.models.users import UserRole, Users
from backend.repositories.users_repository import UsersRepository
from backend.schemas.users import ChangeEmailRequest, CreateUserRequest
from backend.security.passwords import hash_password, verify_password


class UsersService:
    def __init__(self, users_repo: UsersRepository):
        self.users_repo = users_repo

    def authenticate(self, email: str, password: str) -> Users:
        user = self.users_repo.get_by_email(email=email)
        if user is None or not verify_password(
            password=password,
            hashed_password=user.hashed_password,
        ):
            raise InvalidCredentialsError("Invalid email or password")

        if user.email_verified_at is None:
            raise EmailNotVerifiedError("Please verify your email before logging in")

        return user

    def verify_email(self, user_id: UUID) -> Users:
        user = self.get_user(user_id)
        user.email_verified_at = datetime.now(UTC)
        return self.update_user(user=user)

    def update_user(self, user: Users) -> Users:
        return self.users_repo.update(user=user)

    def change_email(self, user_id: UUID, request: ChangeEmailRequest) -> Users:
        user = self.get_user(user_id=user_id)
        user.email = str(request.email)
        return self.users_repo.update(user=user)

    def get_user(self, user_id: UUID) -> Users:
        user_found = self.users_repo.get(user_id)
        if user_found is None:
            raise UserNotFoundError("User not found")
        return user_found

    def create_user(self, create_user_request: CreateUserRequest) -> Users:
        hashed = hash_password(create_user_request.password.get_secret_value())
        return self.users_repo.add(
            Users(
                email=str(create_user_request.email),
                hashed_password=hashed,
                user_role=UserRole.CUSTOMER,
            )
        )
