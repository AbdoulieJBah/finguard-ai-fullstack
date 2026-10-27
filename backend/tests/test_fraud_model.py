from __future__ import annotations

import math

import pytest
from sqlalchemy import func, select

from app.ml.fraud import FraudModel, get_model
from app.models import Alert, RiskAssessment

DRAIN_AT_NIGHT = {"amount": 180_000, "sender_balance": 180_000, "hour": 3, "transaction_type": "TRANSFER"}
ROUTINE = {"amount": 250, "sender_balance": 248_650.75, "hour": 14, "transaction_type": "TRANSFER"}


def test_contributions_add_up_to_the_score():
    model = get_model()
    for case in (DRAIN_AT_NIGHT, ROUTINE):
        score = model.score(**case)
        assert math.isclose(score.base_value + sum(c.contribution for c in score.contributions), score.logit, abs_tol=1e-9)
        assert math.isclose(score.probability, 1 / (1 + math.exp(-score.logit)), rel_tol=1e-12)
        assert {c.feature for c in score.contributions} == {"amount", "sender_balance", "balance_share", "hour", "transaction_type"}


def test_model_separates_an_emptied_account_from_a_routine_payment():
    model = get_model()
    drain, routine = model.score(**DRAIN_AT_NIGHT), model.score(**ROUTINE)
    assert drain.level == "High"
    assert routine.level == "Low"
    assert drain.probability > 50 * routine.probability
    top = drain.contributions[0]
    assert top.contribution > 0


def test_levels_follow_the_thresholds():
    model = get_model()
    score = model.score(**DRAIN_AT_NIGHT)
    assert score.probability >= model.thresholds["high"]
    assert model.thresholds["medium"] <= model.thresholds["high"]


def test_unknown_transaction_type_is_rejected():
    with pytest.raises(ValueError):
        get_model().score(100, 100, 3, "PAYMENT")


def test_model_file_is_complete():
    card = get_model().card()
    assert card["data"]["frauds"] > 0
    assert 0 < card["metrics"]["test"]["pr_auc"] <= 1
    assert any(row.get("deployed") for row in card["comparison"])
    assert card["limitations"]
    FraudModel(get_model().spec)  # round-trips


def test_predict_endpoint_explains_and_logs(client, analyst, session):
    before = session.scalar(select(func.count()).select_from(RiskAssessment))
    response = client.post("/predict-fraud-model", json={**DRAIN_AT_NIGHT, "transaction_type": "transfer"}, headers=analyst)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["level"] == "High" and body["alert_id"] is not None
    assert body["transaction_type"] == "TRANSFER"
    assert len(body["contributions"]) == 5
    assert math.isclose(body["base_value"] + sum(c["contribution"] for c in body["contributions"]), body["logit"], abs_tol=1e-5)
    assert session.scalar(select(func.count()).select_from(RiskAssessment)) == before + 1
    alert = session.get(Alert, body["alert_id"])
    assert alert is not None and alert.kind == "fraud" and alert.status == "Open"


def test_predict_endpoint_defaults_to_the_current_hour(client, analyst):
    body = client.post("/predict-fraud-model", json={"amount": 250, "sender_balance": 10_000}, headers=analyst).json()
    assert 0 <= body["hour"] <= 23


@pytest.mark.parametrize(
    "payload",
    [
        {"amount": -1, "sender_balance": 100},
        {"amount": 100, "sender_balance": -5},
        {"amount": 100, "sender_balance": 100, "hour": 24},
        {"amount": 100, "sender_balance": 100, "transaction_type": "PAYMENT"},
    ],
)
def test_predict_endpoint_validates_input(client, analyst, payload):
    assert client.post("/predict-fraud-model", json=payload, headers=analyst).status_code == 422


def test_model_card_endpoint(client, analyst):
    card = client.get("/models/fraud", headers=analyst).json()
    assert card["version"] == get_model().version
    assert {"pr_auc", "roc_auc", "at_high"} <= set(card["metrics"]["test"])
    assert "features" not in card  # weights stay server-side


def _operating(client, headers) -> dict:
    return next(a for a in client.get("/accounts", headers=headers).json() if a["account_number"] == "FG10000001")


def test_every_payment_is_scored(client, admin, session, monkeypatch):
    monkeypatch.setattr("app.routers.banking.utc_hour", lambda: 14)
    account = _operating(client, admin)
    response = client.post(
        "/transfers",
        json={"from_account_id": account["id"], "to_account_number": "FG10000002", "amount": 250, "description": "Routine"},
        headers=admin,
    )
    assert response.status_code == 201, response.text
    check = response.json()["fraud_check"]
    assert check["level"] == "Low" and check["alert_id"] is None
    assessment = session.get(RiskAssessment, check["assessment_id"])
    assert assessment is not None and assessment.engine.startswith("fraud-scorecard")


def test_payment_that_empties_an_account_at_night_opens_an_alert(client, admin, session, monkeypatch):
    monkeypatch.setattr("app.routers.banking.utc_hour", lambda: 3)
    account = _operating(client, admin)
    response = client.post(
        "/transfers",
        json={"from_account_id": account["id"], "to_account_number": "FG10000002", "amount": account["balance"], "description": "Everything"},
        headers=admin,
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["available_balance"] == 0
    check = body["fraud_check"]
    assert check["level"] == "High" and check["alert_id"] is not None
    alert = session.get(Alert, check["alert_id"])
    assert alert is not None and body["reference"] in alert.subject
    assert "Share of balance moved" in alert.reason
