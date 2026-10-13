from unittest.mock import Mock, patch

import pytest
from sqlalchemy.engine import make_url

from backend.config import DATABASE_URL
from backend.database import engine, get_db


def test_get_db_closes_session_on_error() -> None:

    session = Mock()

    with patch("backend.database.SessionLocal", return_value=session):
        generator = get_db()

        assert next(generator) is session

        with pytest.raises(RuntimeError, match="Test-Fehler"):
            generator.throw(RuntimeError("Test-Fehler"))

        session.close.assert_called_once()


def test_engine_uses_database_url() -> None:
    assert engine.url == make_url(DATABASE_URL)


def test_get_db_closes_session() -> None:
    session = Mock()

    with patch("backend.database.SessionLocal", return_value=session):
        generator = get_db()

        assert next(generator) is session
        session.close.assert_not_called()

        generator.close()

        session.close.assert_called_once()
