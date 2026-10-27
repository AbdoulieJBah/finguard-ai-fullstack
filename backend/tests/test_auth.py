from __future__ import annotations

import pytest
from sqlalchemy import select

from app.models import AuditEvent, SessionToken
from app.security import hash_password, verify_password

from .conftest import ADMIN_EMAIL, DEMO_PASSWORD, login

PROTECTED = [
    ("get", "/me", None),
    ("post", "/auth/logout", None),
    ("get", "/accounts", None),
    ("get", "/transactions", None),
    ("post", "/transfers", {"from_account_id": 1, "to_account_number": "FG10000002", "amount": 1, "description": "Test"}),
    ("post", "/predict-credit-risk", {"income": 50000, "loan_amount": 20000, "credit_score": 700}),
    ("post", "/predict-fraud-risk", {"transaction_amount": 100, "transaction_frequency": 1}),
    ("post", "/predict-aml-risk", {"transaction_amount": 100}),
    ("post", "/predict-fraud-model", {"amount": 100, "sender_balance": 1000}),
    ("get", "/models/fraud", None),
    ("get", "/alerts", None),
    ("get", "/dashboard-metrics", None),
    ("get", "/risk-trends", None),
    ("get", "/audit-logs", None),
    ("get", "/system-health", None),
    ("post", "/copilot", {"question": "fraud?"}),
]


@pytest.mark.parametrize(("method", "path", "body"), PROTECTED)
def test_every_data_endpoint_requires_sign_in(client, method, path, body):
    response = client.request(method, path, json=body)
    assert response.status_code == 401
    assert response.headers.get("www-authenticate") == "Bearer"


@pytest.mark.parametrize(("method", "path", "body"), PROTECTED)
def test_invalid_token_is_rejected(client, method, path, body):
    response = client.request(method, path, json=body, headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401


def test_public_endpoints_reveal_no_data(client):
    assert client.get("/").status_code == 200
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json() == {"status": "healthy"}


def test_login_returns_token_and_user(client):
    response = client.post("/auth/login", json={"email": ADMIN_EMAIL.upper(), "password": DEMO_PASSWORD})
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == ADMIN_EMAIL
    assert body["user"]["role"] == "Administrator"
    me = client.get("/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.json()["email"] == ADMIN_EMAIL


@pytest.mark.parametrize("email", [ADMIN_EMAIL, "nobody@finguard.ai"])
def test_failed_sign_in_is_rejected_and_audited(client, session, email):
    response = client.post("/auth/login", json={"email": email, "password": "wrong-password"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"
    event = session.scalar(select(AuditEvent).where(AuditEvent.action == "Failed sign-in attempt"))
    assert event is not None and event.actor == email and event.status == "Failed"


def test_logout_revokes_the_session(client):
    headers = login(client)
    assert client.post("/auth/logout", headers=headers).status_code == 204
    assert client.get("/me", headers=headers).status_code == 401


def test_session_tokens_are_stored_hashed(client, session):
    token = login(client)["Authorization"].removeprefix("Bearer ")
    stored = session.scalars(select(SessionToken.token_hash)).all()
    assert stored and token not in stored


def test_password_hashing_round_trip():
    encoded = hash_password("correct horse battery", iterations=1000)
    assert encoded.startswith("pbkdf2_sha256$1000$")
    assert verify_password("correct horse battery", encoded)
    assert not verify_password("wrong", encoded)
    assert not verify_password("anything", "garbage")
