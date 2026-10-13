import pytest
from pydantic import ValidationError

from backend.config import PASSWORD_MIN_LENGTH
from backend.schemas.users import CreateUserRequest

VALID_TEST_PASSWORD = "langes-passwort-123"
VALID_TEST_EMAIL = "example_email@outlook.com"


@pytest.mark.parametrize("password", ["", " ", "a" * (PASSWORD_MIN_LENGTH - 1)])
def test_create_user_rejects_invalid_password(password: str) -> None:
    with pytest.raises(ValidationError) as exc_info:
        CreateUserRequest(email=VALID_TEST_EMAIL, password=password)

    assert exc_info.value.errors()[0]["loc"] == ("password",)


@pytest.mark.parametrize(
    "password", ["a" * PASSWORD_MIN_LENGTH, "a" * (PASSWORD_MIN_LENGTH + 1)]
)
def test_create_user_accepts_valid_password(password: str) -> None:
    request = CreateUserRequest(email=VALID_TEST_EMAIL, password=password)

    assert request.password.get_secret_value() == password


def test_create_user_valid_email_valid_password() -> None:
    create_user_request = CreateUserRequest(
        email=VALID_TEST_EMAIL, password=VALID_TEST_PASSWORD
    )

    assert create_user_request.email == VALID_TEST_EMAIL
    assert create_user_request.password.get_secret_value() == VALID_TEST_PASSWORD


@pytest.mark.parametrize("email", ["keine-email", "user@", "@example.com"])
def test_create_user_rejects_invalid_email(email: str):
    with pytest.raises(ValidationError) as exc_info:
        CreateUserRequest(
            email=email,
            password=VALID_TEST_PASSWORD,
        )

    assert exc_info.value.errors()[0]["loc"] == ("email",)
