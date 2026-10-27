from __future__ import annotations

import os
from datetime import datetime, timezone

from sqlalchemy import func, select

from app.models import Alert, RiskAssessment


def test_dashboard_numbers_come_from_the_database(client, analyst, session):
    metrics = client.get("/dashboard-metrics", headers=analyst).json()
    open_fraud = session.scalar(select(func.count()).select_from(Alert).where(Alert.kind == "fraud", Alert.status != "Closed"))
    open_aml = session.scalar(select(func.count()).select_from(Alert).where(Alert.kind == "aml", Alert.status != "Closed"))
    total = session.scalar(select(func.count()).select_from(RiskAssessment))
    assert metrics["fraud_alerts"] == open_fraud
    assert metrics["aml_cases"] == open_aml
    assert metrics["assessments_logged"] == total > 0
    assert 0 <= metrics["risk_score"] <= 110


def test_risk_trends_cover_six_months(client, analyst):
    trends = client.get("/risk-trends", headers=analyst).json()
    assert len(trends) == 6
    assert set(trends[0]) == {"month", "risk", "fraud", "aml"}
    assert trends[-1]["month"] == datetime.now(timezone.utc).strftime("%b")
    assert any(month["risk"] > 0 for month in trends)


def test_audit_log_is_restricted_to_admin_and_compliance(client, admin, compliance, analyst):
    assert client.get("/audit-logs", headers=analyst).status_code == 403
    assert client.get("/audit-logs", headers=compliance).status_code == 200
    body = client.get("/audit-logs", headers=admin).json()
    assert body["total_events"] >= len(body["items"]) > 0
    for item in body["items"]:
        datetime.fromisoformat(item["time"])  # real timestamps only, no invented entries
    assert any(item["action"] == "Secure session started" for item in body["items"])


def test_system_health_is_measured(client, analyst):
    body = client.get("/system-health", headers=analyst).json()
    assert body["database"] == "Connected"
    assert isinstance(body["database_latency_ms"], float)
    expected = "PostgreSQL" if os.getenv("TEST_DATABASE_URL") else "SQLite"
    assert body["database_engine"] == expected
    assert body["persistent_storage"] is (expected == "PostgreSQL")


def test_copilot_answers_with_live_numbers(client, analyst):
    metrics = client.get("/dashboard-metrics", headers=analyst).json()
    answer = client.post("/copilot", json={"question": "What is the fraud situation?"}, headers=analyst).json()["response"]
    assert f"{metrics['fraud_alerts']} open fraud alerts" in answer


def test_copilot_reports_the_users_own_balances(client, admin):
    answer = client.post("/copilot", json={"question": "What is my balance?"}, headers=admin).json()["response"]
    assert "EUR 1,124,070.75" in answer
