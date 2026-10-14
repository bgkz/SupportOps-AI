from datetime import datetime
from uuid import UUID

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.dependencies.users import get_users_service
from backend.exceptions.users import EmailAlreadyExistError, UserNotFoundError
from backend.models.users import UserRole, Users
from backend.schemas.users import CreateUserRequest
from backend.security.passwords import hash_password, verify_password


def test_get_user_raises_not_found_for_unknown_id(db: Session) -> None:
    service = get_users_service(db=db)
    with pytest.raises(UserNotFoundError, match="User not found"):
        service.get_user(user_id=UUID("550e8400-e29b-41d4-a716-446655440000"))


def test_get_user_returns_existing_user(db: Session) -> None:
    service = get_users_service(db=db)
    hashed = hash_password("LongPassword123")
    expected_user = Users(
        email="valid-email@outlook.de",
        hashed_password=hashed,
        user_role=UserRole.CUSTOMER,
    )
    db.add(expected_user)
    db.flush()

    user_id = expected_user.id
    db.expunge_all()

    user_found = service.get_user(user_id=user_id)

    assert user_found is not None
    assert user_found.id == user_id
    assert user_found.email == "valid-email@outlook.de"
    assert user_found.hashed_password == hashed
    assert user_found.user_role == UserRole.CUSTOMER


def test_create_user_duplicate_email_with_whitespace(db: Session) -> None:
    service = get_users_service(db=db)
    password = "langes Passwort 123"

    request = CreateUserRequest(email="example@outlook.de", password=password)
    duplicate_request = CreateUserRequest(
        email="  example@outlook.de  ", password=password
    )

    assert duplicate_request.email == request.email

    service.create_user(create_user_request=request)

    with pytest.raises(EmailAlreadyExistError):
        service.create_user(create_user_request=duplicate_request)

    db.expunge_all()

    stmt = select(func.count()).select_from(Users).where(Users.email == request.email)
    count = db.execute(stmt).scalar_one()

    assert count == 1


def test_create_user_with_hash_like_password(db: Session) -> None:
    service = get_users_service(db=db)
    password = "$argon2id$v=19$m=65536,t=3,p=4$g2vGCeDo/CkiOu+XciV/Cw$akkU/Q1okx/ywuyb4U+0aMmahBYYBnDEWgQI7B10EIc"
    request = CreateUserRequest(email="example@outlook.de", password=password)

    user_created = service.create_user(create_user_request=request)

    assert user_created.hashed_password != password
    assert verify_password(password, user_created.hashed_password)


def test_create_user_duplicate(db: Session) -> None:
    service = get_users_service(db=db)
    password = "langes Passwort 123"
    request = CreateUserRequest(email="example@outlook.de", password=password)
    duplicate_request = CreateUserRequest(email="example@outlook.de", password=password)

    service.create_user(create_user_request=request)
    with pytest.raises(EmailAlreadyExistError, match="Email already exists"):
        service.create_user(create_user_request=duplicate_request)

    valid_request_after_duplicate = CreateUserRequest(
        email="valid-email@outlook.de", password="Some Safe Password 12345"
    )

    service.create_user(create_user_request=valid_request_after_duplicate)

    db.expunge_all()

    stmt = select(func.count()).select_from(Users).where(Users.email == request.email)
    count = db.execute(stmt).scalar_one()
    assert count == 1

    stmt = (
        select(func.count())
        .select_from(Users)
        .where(Users.email == valid_request_after_duplicate.email)
    )
    assert db.execute(stmt).scalar_one() == 1


def test_create_user(db: Session) -> None:
    service = get_users_service(db=db)
    password = "langes Passwort 123"
    request = CreateUserRequest(email="example@outlook.de", password=password)

    user_created = service.create_user(create_user_request=request)

    assert isinstance(user_created.id, UUID)
    assert user_created.email == "example@outlook.de"
    assert user_created.hashed_password != password
    assert verify_password(
        password=password, hashed_password=user_created.hashed_password
    )
    assert user_created.user_role == UserRole.CUSTOMER
    assert isinstance(user_created.created_at, datetime)
    assert isinstance(user_created.updated_at, datetime)

    user_id = user_created.id
    db.expunge_all()

    user_from_db = db.get(Users, user_id)

    assert user_from_db is not None
    assert user_from_db.email == request.email
    assert user_from_db.user_role == UserRole.CUSTOMER
    assert verify_password(password, user_from_db.hashed_password)
