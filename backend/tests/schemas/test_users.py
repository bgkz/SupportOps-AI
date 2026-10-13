import pytest
from pydantic import ValidationError

from backend.schemas.users import CreateUserRequest

VALID_TEST_PASSWORD = "langes-passwort-123"


def test_create_user_valid_email() -> None:
    create_user_request = CreateUserRequest(
        email="example_email@outlook.com", password=VALID_TEST_PASSWORD
    )

    assert create_user_request.email == "example_email@outlook.com"
    assert create_user_request.password.get_secret_value() == VALID_TEST_PASSWORD


@pytest.mark.parametrize("email", ["keine-email", "user@", "@example.com"])
def test_create_user_rejects_invalid_email(email: str):
    with pytest.raises(ValidationError):
        CreateUserRequest(
            email=email,
            password=VALID_TEST_PASSWORD,
        )
