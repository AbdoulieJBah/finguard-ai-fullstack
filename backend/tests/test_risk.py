from __future__ import annotations

from sqlalchemy import func, select

from app.models import Alert, RiskAssessment
from app.risk import aml_risk, credit_risk, fraud_risk

HIGH_FRAUD = {"transaction_amount": 12_500, "transaction_frequency": 25, "international_transfer": True}
LOW_FRAUD = {"transaction_amount": 120, "transaction_frequency": 2, "international_transfer": False}
CRITICAL_AML = {"transaction_amount": 20_000, "country_risk": "High", "cash_transaction": True, "politically_exposed": True}


def test_rules_are_explainable():
    result = fraud_risk(12_500, 25, True)
    assert (result.score, result.level) == (100, "High")
    assert any("International" in factor for factor in result.factors)
    low = fraud_risk(120, 2, False)
    assert (low.score, low.level) == (20, "Low")
    credit, ratio = credit_risk(50_000, 35_000, 600)
    assert ratio == 0.7 and credit.level == "High" and len(credit.factors) == 2
    aml = aml_risk(20_000, "high", True, True)
    assert aml.score == 110 and aml.level == "High"


def test_high_fraud_assessment_is_logged_and_opens_an_alert(client, analyst, admin):
    before = client.get("/dashboard-metrics", headers=admin).json()
    response = client.post("/predict-fraud-risk", json=HIGH_FRAUD, headers=analyst)
    assert response.status_code == 200
    body = response.json()
    assert body["fraud_level"] == "High" and body["alert_id"] is not None
    assert body["factors"] and body["engine"] == "rules-1.0"
    after = client.get("/dashboard-metrics", headers=admin).json()
    assert after["fraud_alerts"] == before["fraud_alerts"] + 1
    assert after["assessments_logged"] == before["assessments_logged"] + 1
    alerts = client.get("/alerts", params={"kind": "fraud"}, headers=analyst).json()
    assert alerts[0]["id"] == body["alert_id"] and alerts[0]["status"] == "Open"


def test_low_fraud_assessment_opens_no_alert(client, analyst, session):
    alerts_before = session.scalar(select(func.count()).select_from(Alert))
    body = client.post("/predict-fraud-risk", json=LOW_FRAUD, headers=analyst).json()
    assert body["fraud_level"] == "Low" and body["alert_id"] is None
    assert session.scalar(select(func.count()).select_from(Alert)) == alerts_before
    assessment = session.get(RiskAssessment, body["assessment_id"])
    assert assessment is not None and assessment.kind == "fraud" and assessment.score == body["fraud_score"]


def test_aml_accepts_any_case_and_raises_critical_case(client, compliance):
    response = client.post("/predict-aml-risk", json=CRITICAL_AML, headers=compliance)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["country_risk"] == "high" and body["aml_level"] == "High"
    case = next(a for a in client.get("/alerts", params={"kind": "aml"}, headers=compliance).json() if a["id"] == body["alert_id"])
    assert case["level"] == "Critical"


def test_invalid_risk_input_is_rejected(client, analyst):
    assert client.post("/predict-aml-risk", json={"transaction_amount": 100, "country_risk": "unknown"}, headers=analyst).status_code == 422
    assert client.post("/predict-credit-risk", json={"income": 0, "loan_amount": 1, "credit_score": 700}, headers=analyst).status_code == 422


def test_credit_assessment_returns_debt_ratio_and_factors(client, analyst):
    body = client.post("/predict-credit-risk", json={"income": 50_000, "loan_amount": 20_000, "credit_score": 720}, headers=analyst).json()
    assert body["debt_ratio"] == 0.4 and body["risk_level"] == "Low" and len(body["factors"]) == 2


def test_alert_filters(client, analyst):
    every = client.get("/alerts", params={"state": "all", "limit": 200}, headers=analyst).json()
    assert every, "seed data should contain alerts"
    open_only = client.get("/alerts", params={"limit": 200}, headers=analyst).json()
    assert all(alert["status"] != "Closed" for alert in open_only)
    fraud = client.get("/alerts", params={"kind": "fraud", "state": "all"}, headers=analyst).json()
    assert all(alert["kind"] == "fraud" for alert in fraud)
