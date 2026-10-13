import pytest

from backend.security.passwords import hash_password, verify_password


@pytest.mark.parametrize("password", ["", " ieoioeioeoewewew", "xx xx"])
def test_hash_password(password: str) -> None:
    hashed = hash_password(password=password)

    assert hashed != password
    assert verify_password(password=password, hashed_password=hashed)
    assert not verify_password(password="test test", hashed_password=hashed)


def test_hash_password_uses_random_salt() -> None:

    password = "Test-Password"

    assert hash_password(password=password) != hash_password(password=password)
