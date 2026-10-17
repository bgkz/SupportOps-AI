from datetime import datetime
from uuid import UUID

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.dependencies.users import get_users_service
from backend.exceptions.users import EmailAlreadyExistError, UserNotFoundError
from backend.models.users import UserRole, Users
from backend.schemas.users import ChangeEmailRequest, CreateUserRequest
from backend.security.passwords import hash_password, verify_password


def test_change_email_accepts_current_email_and_preserves_timestamp(db: Session) -> None:
    service = get_users_service(db=db)
    user_id = UUID("550e8400-e29b-41d4-a716-446655440000")
    email = "valid-email@outlook.de"
    old_timestamp = datetime(2020, 1, 1)
    hashed = hash_password("LongPassword123")

    db.add(
        Users(
            id=user_id,
            email=email,
            hashed_password=hashed,
            user_role=UserRole.CUSTOMER,
            created_at=old_timestamp,
            updated_at=old_timestamp,
        )
    )
    db.commit()
    db.expunge_all()

    changed_user = service.change_email(
        user_id=user_id, request=ChangeEmailRequest(email=email)
    )

    assert changed_user.id == user_id
    assert changed_user.email == email
    assert changed_user.updated_at == old_timestamp

    db.expunge_all()
    persisted_user = db.get(Users, user_id)

    assert persisted_user is not None
    assert persisted_user.email == email
    assert persisted_user.hashed_password == hashed
    assert persisted_user.user_role == UserRole.CUSTOMER
    assert persisted_user.created_at == old_timestamp
    assert persisted_user.updated_at == old_timestamp


def test_change_email_raises_not_found_for_unknown_id(db: Session) -> None:
    with pytest.raises(UserNotFoundError, match="User not found"):
        get_users_service(db=db).change_email(
            user_id=UUID("b72f409e-6c83-4d15-9a20-e8f153c067bd"),
            request=ChangeEmailRequest(email="example@example.com"),
        )


def test_change_email_rejects_duplicate_email(db: Session) -> None:
    service = get_users_service(db=db)
    user_id = UUID("550e8400-e29b-41d4-a716-446655440000")
    old_timestamp = datetime(2020, 1, 1)
    hashed = hash_password("LongPassword123")

    another_user_id = UUID("b72f409e-6c83-4d15-9a20-e8f153c067bd")
    another_user_hashed = hash_password("AnotherPassword123")

    db.add_all(
        [
            Users(
                id=user_id,
                email="valid-email@outlook.de",
                hashed_password=hashed,
                user_role=UserRole.CUSTOMER,
                created_at=old_timestamp,
                updated_at=old_timestamp,
            ),
            Users(
                id=another_user_id,
                email="another-email@outlook.de",
                hashed_password=another_user_hashed,
                user_role=UserRole.CUSTOMER,
                created_at=old_timestamp,
                updated_at=old_timestamp,
            ),
        ]
    )
    db.commit()

    with pytest.raises(EmailAlreadyExistError, match="Email already exists"):
        service.change_email(
            user_id=user_id,
            request=ChangeEmailRequest(email="another-email@outlook.de"),
        )

    db.expunge_all()

    untouched_user = db.get(Users, user_id)

    assert untouched_user is not None
    assert untouched_user.email == "valid-email@outlook.de"
    assert untouched_user.updated_at == old_timestamp

    other_user = db.get(Users, another_user_id)

    assert other_user is not None
    assert other_user.email == "another-email@outlook.de"
    assert other_user.updated_at == old_timestamp


def test_change_email_persists_email_and_preserves_other_fields(db: Session) -> None:
    service = get_users_service(db=db)
    user_id = UUID("550e8400-e29b-41d4-a716-446655440000")
    old_timestamp = datetime(2020, 1, 1)
    hashed = hash_password("LongPassword123")

    db.add(
        Users(
            id=user_id,
            email="valid-email@outlook.de",
            hashed_password=hashed,
            user_role=UserRole.CUSTOMER,
            created_at=old_timestamp,
            updated_at=old_timestamp,
        )
    )
    db.flush()
    db.expunge_all()

    changed_user = service.change_email(
        user_id=user_id,
        request=ChangeEmailRequest(email="changed-email@example.com"),
    )

    assert changed_user.id == user_id
    assert changed_user.email == "changed-email@example.com"

    db.expunge_all()

    persisted_user = db.get(Users, user_id)

    assert persisted_user is not None
    assert persisted_user.email == "changed-email@example.com"
    assert persisted_user.hashed_password == hashed
    assert persisted_user.user_role == UserRole.CUSTOMER
    assert persisted_user.created_at == old_timestamp
    assert persisted_user.updated_at > old_timestamp


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
