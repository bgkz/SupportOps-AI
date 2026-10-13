import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.database import Base
from backend.models.orders import Orders
from backend.models.users import Users


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
