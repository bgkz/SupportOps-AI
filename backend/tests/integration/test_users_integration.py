import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.main import app


def test_create_user(client: TestClient) -> None:
    pass
