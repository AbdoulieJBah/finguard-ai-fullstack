from __future__ import annotations

import json
from typing import Annotated, Literal

from fastapi import APIRouter, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..fraud_checks import check_payment, score_json
from ..ml.fraud import get_model
from ..models import Alert, RiskAssessment, User, utcnow
from ..risk import ENGINE_VERSION, RiskResult, aml_risk, credit_risk, fraud_risk
from ..schemas import AmlRiskRequest, CreditRiskRequest, FraudModelRequest, FraudRiskRequest
from ..security import DbSession, StaffUser
from ..utils import iso, record_audit

router = APIRouter(tags=["risk"])


def save_assessment(db: Session, kind: str, result: RiskResult, inputs: dict, user: User | None) -> RiskAssessment:
    assessment = RiskAssessment(
        kind=kind,
        score=result.score,
        level=result.level,
        inputs=json.dumps(inputs, sort_keys=True),
        engine=ENGINE_VERSION,
        user_id=user.id if user else None,
        created_at=utcnow(),
    )
    db.add(assessment)
    db.flush()
    if user is not None:
        record_audit(db, f"{kind.upper() if kind == 'aml' else kind.capitalize()} risk assessed: {result.level}", user.name)
    return assessment


def raise_alert(
    db: Session, kind: str, assessment: RiskAssessment, result: RiskResult, amount: float, subject: str
) -> Alert:
    if kind == "fraud":
        title, level = "High fraud risk transaction", "High"
    else:
        title, level = "AML case: enhanced due diligence", "Critical" if result.score >= 85 else "High"
    alert = Alert(
        kind=kind,
        title=title,
        subject=subject,
        level=level,
        status="Open",
        reason="; ".join(result.factors)[:500],
        amount_cents=round(amount * 100),
        assessment_id=assessment.id,
        created_at=assessment.created_at,
    )
    db.add(alert)
    db.flush()
    return alert


def alert_json(alert: Alert) -> dict:
    return {
        "id": alert.id,
        "kind": alert.kind,
        "title": alert.title,
        "subject": alert.subject,
        "level": alert.level,
        "status": alert.status,
        "reason": alert.reason,
        "amount": alert.amount_cents / 100 if alert.amount_cents is not None else None,
        "assessment_id": alert.assessment_id,
        "created_at": iso(alert.created_at),
    }


@router.post("/predict-credit-risk")
def predict_credit_risk(payload: CreditRiskRequest, user: StaffUser, db: DbSession) -> dict:
    result, debt_ratio = credit_risk(payload.income, payload.loan_amount, payload.credit_score)
    assessment = save_assessment(db, "credit", result, payload.model_dump(), user)
    db.commit()
    return {
        **payload.model_dump(),
        "debt_ratio": debt_ratio,
        "risk_score": result.score,
        "risk_level": result.level,
        "recommendation": result.recommendation,
        "factors": result.factors,
        "assessment_id": assessment.id,
        "engine": ENGINE_VERSION,
    }


@router.post("/predict-fraud-risk")
def predict_fraud_risk(payload: FraudRiskRequest, user: StaffUser, db: DbSession) -> dict:
    result = fraud_risk(payload.transaction_amount, payload.transaction_frequency, payload.international_transfer)
    assessment = save_assessment(db, "fraud", result, payload.model_dump(), user)
    alert = None
    if result.level == "High":
        alert = raise_alert(db, "fraud", assessment, result, payload.transaction_amount, f"Assessment #{assessment.id}")
        record_audit(db, f"Fraud alert #{alert.id} opened", user.name, status="Open")
    db.commit()
    return {
        **payload.model_dump(),
        "fraud_score": result.score,
        "fraud_level": result.level,
        "recommendation": result.recommendation,
        "factors": result.factors,
        "assessment_id": assessment.id,
        "alert_id": alert.id if alert else None,
        "engine": ENGINE_VERSION,
    }


@router.post("/predict-fraud-model")
def predict_fraud_model(payload: FraudModelRequest, user: StaffUser, db: DbSession) -> dict:
    """Score a payment with the trained fraud scorecard and explain the score feature by feature."""
    hour = payload.hour if payload.hour is not None else utcnow().hour
    check = check_payment(
        db,
        user,
        amount=payload.amount,
        sender_balance=payload.sender_balance,
        hour=hour,
        transaction_type=payload.transaction_type,
        subject="Manual assessment",
    )
    if check.alert is not None:
        check.alert.subject = f"Assessment #{check.assessment.id}"
    record_audit(db, f"Fraud model assessment: {check.score.level}", user.name)
    db.commit()
    return {**payload.model_dump(), "hour": hour, **score_json(check)}


@router.get("/models/fraud")
def fraud_model_card(user: StaffUser) -> dict:
    """Model card: training data, validation method, test metrics, thresholds and limitations."""
    return get_model().card()


@router.post("/predict-aml-risk")
def predict_aml_risk(payload: AmlRiskRequest, user: StaffUser, db: DbSession) -> dict:
    result = aml_risk(
        payload.transaction_amount, payload.country_risk, payload.cash_transaction, payload.politically_exposed
    )
    assessment = save_assessment(db, "aml", result, payload.model_dump(), user)
    alert = None
    if result.level == "High":
        alert = raise_alert(db, "aml", assessment, result, payload.transaction_amount, f"Assessment #{assessment.id}")
        record_audit(db, f"AML case #{alert.id} opened", user.name, status="Open")
    db.commit()
    return {
        **payload.model_dump(),
        "aml_score": result.score,
        "aml_level": result.level,
        "recommendation": result.recommendation,
        "factors": result.factors,
        "assessment_id": assessment.id,
        "alert_id": alert.id if alert else None,
        "engine": ENGINE_VERSION,
    }


@router.get("/alerts")
def list_alerts(
    user: StaffUser,
    db: DbSession,
    kind: Literal["fraud", "aml"] | None = None,
    state: Literal["open", "all"] = "open",
    limit: Annotated[int, Query(ge=1, le=200)] = 20,
) -> list[dict]:
    query = select(Alert).order_by(Alert.created_at.desc(), Alert.id.desc()).limit(limit)
    if kind is not None:
        query = query.where(Alert.kind == kind)
    if state == "open":
        query = query.where(Alert.status != "Closed")
    return [alert_json(alert) for alert in db.scalars(query)]
