import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.database import Base, get_db
from backend.main import app
from backend.models.orders import Orders
from backend.models.users import Users


@pytest.fixture
def client(db: Session):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        del app.dependency_overrides[get_db]


@pytest.fixture
def db():
    engine = create_engine(os.environ["TEST_DATABASE_URL"])

    with engine.connect() as connection:
        transaction = connection.begin()
        Base.metadata.create_all(connection)

        with Session(
            bind=connection,
            join_transaction_mode="create_savepoint",
        ) as session:
            yield session

        transaction.rollback()

    engine.dispose()
