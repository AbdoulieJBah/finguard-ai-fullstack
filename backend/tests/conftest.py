"""Each test gets a fresh, migrated and seeded database.

SQLite by default; set TEST_DATABASE_URL to run the same tests against PostgreSQL (CI does both).
"""
from __future__ import annotations

import os

import pytest

os.environ.setdefault("FINGUARD_PBKDF2_ITERATIONS", "1000")  # fast hashing in tests only

DEMO_PASSWORD = "FinGuard123!"
ADMIN_EMAIL = "demo@finguard.ai"
ANALYST_EMAIL = "analyst@finguard.ai"
COMPLIANCE_EMAIL = "compliance@finguard.ai"


def _reset_postgres(url: str) -> None:
    from sqlalchemy import create_engine, text

    from app.models import Base

    engine = create_engine(url)
    with engine.begin() as connection:
        Base.metadata.drop_all(connection)
        connection.execute(text("DROP TABLE IF EXISTS alembic_version"))
    engine.dispose()


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from app import db
    from app.config import normalise_database_url

    if db._engine is not None:
        db._engine.dispose()
    test_url = os.getenv("TEST_DATABASE_URL", "").strip()
    if test_url:
        url = normalise_database_url(test_url)
        _reset_postgres(url)
        monkeypatch.setenv("DATABASE_URL", url)
    else:
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.setenv("FINGUARD_DB_PATH", str(tmp_path / "finguard_test.db"))

    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


def login(client, email: str = ADMIN_EMAIL, password: str = DEMO_PASSWORD) -> dict[str, str]:
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture()
def admin(client) -> dict[str, str]:
    return login(client, ADMIN_EMAIL)


@pytest.fixture()
def analyst(client) -> dict[str, str]:
    return login(client, ANALYST_EMAIL)


@pytest.fixture()
def compliance(client) -> dict[str, str]:
    return login(client, COMPLIANCE_EMAIL)


@pytest.fixture()
def session(client):
    """A database session on the same database the app is using."""
    from app import db

    with db.SessionLocal() as s:
        yield s
