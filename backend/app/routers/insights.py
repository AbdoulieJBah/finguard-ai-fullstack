from __future__ import annotations

import time
from datetime import timedelta
from statistics import mean
from typing import Annotated

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from sqlalchemy import func, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..config import APP_VERSION
from ..models import Account, Alert, AuditEvent, RiskAssessment, utcnow
from ..ml.fraud import get_model
from ..risk import ENGINE_VERSION
from ..schemas import CopilotRequest
from ..security import AuditUser, DbSession, StaffUser
from ..utils import as_utc, iso, month_start

router = APIRouter(tags=["insights"])

STARTED_AT = time.monotonic()
ENGINE_NAMES = {"postgresql": "PostgreSQL", "sqlite": "SQLite"}


def _count(db: Session, *conditions) -> int:
    return db.scalar(select(func.count()).select_from(Alert).where(*conditions)) or 0


def compute_metrics(db: Session) -> dict:
    since = utcnow() - timedelta(days=30)
    average = db.scalar(select(func.avg(RiskAssessment.score)).where(RiskAssessment.created_at >= since))
    return {
        "risk_score": round(float(average)) if average is not None else 0,
        "fraud_alerts": _count(db, Alert.kind == "fraud", Alert.status != "Closed"),
        "aml_cases": _count(db, Alert.kind == "aml", Alert.status != "Closed"),
        "high_priority_alerts": _count(db, Alert.status != "Closed", Alert.level.in_(["High", "Critical"])),
        "assessments_logged": db.scalar(select(func.count()).select_from(RiskAssessment)) or 0,
        "assessments_30d": db.scalar(
            select(func.count()).select_from(RiskAssessment).where(RiskAssessment.created_at >= since)
        )
        or 0,
    }


@router.get("/dashboard-metrics")
def dashboard_metrics(user: StaffUser, db: DbSession) -> dict:
    """Live figures computed from the database (open alerts, recent assessments)."""
    return compute_metrics(db)


@router.get("/risk-trends")
def risk_trends(user: StaffUser, db: DbSession) -> list[dict]:
    """Last six months: average assessment score and the number of fraud alerts and AML cases opened."""
    now = utcnow()
    starts = [month_start(now, back) for back in range(5, -1, -1)]
    buckets = {(start.year, start.month): {"scores": [], "fraud": 0, "aml": 0} for start in starts}
    for created_at, score in db.execute(
        select(RiskAssessment.created_at, RiskAssessment.score).where(RiskAssessment.created_at >= starts[0])
    ):
        moment = as_utc(created_at)
        bucket = buckets.get((moment.year, moment.month))
        if bucket is not None:
            bucket["scores"].append(score)
    for created_at, kind in db.execute(select(Alert.created_at, Alert.kind).where(Alert.created_at >= starts[0])):
        moment = as_utc(created_at)
        bucket = buckets.get((moment.year, moment.month))
        if bucket is not None and kind in ("fraud", "aml"):
            bucket[kind] += 1
    return [
        {
            "month": start.strftime("%b"),
            "risk": round(mean(buckets[(start.year, start.month)]["scores"]))
            if buckets[(start.year, start.month)]["scores"]
            else 0,
            "fraud": buckets[(start.year, start.month)]["fraud"],
            "aml": buckets[(start.year, start.month)]["aml"],
        }
        for start in starts
    ]


@router.get("/audit-logs")
def audit_logs(user: AuditUser, db: DbSession, limit: Annotated[int, Query(ge=1, le=200)] = 50) -> dict:
    """Restricted to Administrators and Compliance Officers."""
    events = db.scalars(select(AuditEvent).order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc()).limit(limit))
    since = utcnow() - timedelta(hours=24)
    return {
        "items": [
            {"id": event.id, "action": event.action, "user": event.actor, "time": iso(event.created_at), "status": event.status}
            for event in events
        ],
        "total_events": db.scalar(select(func.count()).select_from(AuditEvent)) or 0,
        "assessments_logged": db.scalar(select(func.count()).select_from(RiskAssessment)) or 0,
        "failed_logins_24h": db.scalar(
            select(func.count())
            .select_from(AuditEvent)
            .where(AuditEvent.status == "Failed", AuditEvent.action == "Failed sign-in attempt", AuditEvent.created_at >= since)
        )
        or 0,
    }


@router.get("/system-health")
def system_health(user: StaffUser, db: DbSession):
    """Measured on each request: database round-trip, engine and uptime."""
    bind = db.get_bind()
    engine_name = ENGINE_NAMES.get(bind.dialect.name, bind.dialect.name)
    body = {
        "backend": "Online",
        "version": APP_VERSION,
        "database_engine": engine_name,
        "persistent_storage": bind.dialect.name != "sqlite",
        "risk_engine": f"Fraud: trained scorecard {get_model().version} · credit and AML: rules ({ENGINE_VERSION})",
        "copilot": "Rule-based",
        "uptime_seconds": int(time.monotonic() - STARTED_AT),
        "checked_at": iso(utcnow()),
    }
    try:
        started = time.perf_counter()
        db.execute(text("SELECT 1"))
        body.update(database="Connected", database_latency_ms=round((time.perf_counter() - started) * 1000, 1))
        return body
    except SQLAlchemyError:
        body.update(database="Unavailable", database_latency_ms=None)
        return JSONResponse(body, status_code=503)


@router.post("/copilot")
def copilot(payload: CopilotRequest, user: StaffUser, db: DbSession) -> dict:
    """Keyword-routed answers built from live data (an LLM can replace this behind the same endpoint)."""
    question = payload.question.lower()
    metrics = compute_metrics(db)
    if "fraud" in question:
        high_fraud = _count(db, Alert.kind == "fraud", Alert.status != "Closed", Alert.level.in_(["High", "Critical"]))
        answer = (
            f"There are {metrics['fraud_alerts']} open fraud alerts, {high_fraud} of them rated High or Critical. "
            "Start with the largest amounts on the Fraud Detection page."
        )
    elif any(word in question for word in ("aml", "compliance", "laundering", "kyc")):
        answer = (
            f"{metrics['aml_cases']} AML cases are open. Prioritise Critical cases and those involving "
            "politically exposed persons or high-risk jurisdictions."
        )
    elif any(word in question for word in ("balance", "account", "liquidity", "cash")):
        rows = db.execute(select(Account.currency, func.sum(Account.balance_cents)).where(Account.user_id == user.id).group_by(Account.currency)).all()
        if rows:
            totals = ", ".join(f"{currency} {cents / 100:,.2f}" for currency, cents in rows)
            answer = f"Your accounts hold {totals} in total. Open Accounts for the latest ledger activity."
        else:
            answer = "You have no accounts in FinGuard."
    elif any(word in question for word in ("credit", "risk", "score")):
        answer = (
            f"The average risk score over the last 30 days is {metrics['risk_score']}/100 "
            f"across {metrics['assessments_30d']} assessments."
        )
    else:
        answer = (
            f"Summary: {metrics['fraud_alerts']} open fraud alerts, {metrics['aml_cases']} open AML cases and an "
            f"average 30-day risk score of {metrics['risk_score']}/100. Ask about fraud, AML, credit risk or balances."
        )
    return {"response": answer, "engine": "rule-based"}
