"""Score payments with the trained fraud model, log the assessment and open alerts."""
from __future__ import annotations

import json
from dataclasses import dataclass

from sqlalchemy.orm import Session

from .ml.fraud import FraudScore, get_model
from .models import Alert, RiskAssessment, User, utcnow
from .utils import record_audit


@dataclass
class FraudCheck:
    score: FraudScore
    assessment: RiskAssessment
    alert: Alert | None


def engine_name() -> str:
    return f"fraud-scorecard-{get_model().version}"


def explain(score: FraudScore, limit: int = 3) -> str:
    """The features that pushed the score up the most, as a sentence for alerts."""
    raising = [c for c in score.contributions if c.contribution > 0][:limit]
    if not raising:
        return "No single feature raised the risk"
    return "; ".join(f"{c.label}: {c.value}" for c in raising)


def check_payment(
    db: Session,
    user: User | None,
    *,
    amount: float,
    sender_balance: float,
    hour: int,
    transaction_type: str,
    subject: str,
) -> FraudCheck:
    score = get_model().score(amount, sender_balance, hour, transaction_type)
    inputs = {"amount": amount, "sender_balance": sender_balance, "hour": hour, "transaction_type": transaction_type}
    assessment = RiskAssessment(
        kind="fraud",
        score=round(score.probability * 100),
        level=score.level,
        inputs=json.dumps(inputs, sort_keys=True),
        engine=engine_name(),
        user_id=user.id if user else None,
        created_at=utcnow(),
    )
    db.add(assessment)
    db.flush()
    alert = None
    if score.level == "High":
        alert = Alert(
            kind="fraud",
            title="Payment flagged by the fraud model",
            subject=subject[:120],
            level="High",
            status="Open",
            reason=explain(score)[:500],
            amount_cents=round(amount * 100),
            assessment_id=assessment.id,
            created_at=assessment.created_at,
        )
        db.add(alert)
        db.flush()
        if user is not None:
            record_audit(db, f"Fraud alert #{alert.id} opened by the fraud model", user.name, status="Open")
    return FraudCheck(score, assessment, alert)


def score_json(check: FraudCheck) -> dict:
    score = check.score
    return {
        "probability": round(score.probability, 6),
        "score": round(score.probability * 100),
        "level": score.level,
        "logit": round(score.logit, 6),
        "base_value": round(score.base_value, 6),
        "contributions": [
            {"feature": c.feature, "label": c.label, "value": c.value, "contribution": round(c.contribution, 6)}
            for c in score.contributions
        ],
        "thresholds": get_model().thresholds,
        "assessment_id": check.assessment.id,
        "alert_id": check.alert.id if check.alert else None,
        "model_version": score.model_version,
    }
