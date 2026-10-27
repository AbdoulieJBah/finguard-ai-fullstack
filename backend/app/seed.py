"""Demo data: three staff users, two accounts and six months of simulated risk history.

Everything here is simulated. Assessments are scored by the real rule engine, and the
same alert rules as the live API decide which ones open fraud alerts or AML cases.
"""
from __future__ import annotations

import json
import random
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .models import Account, Alert, AuditEvent, RiskAssessment, Transaction, User, utcnow
from .risk import ENGINE_VERSION, RiskResult, aml_risk, credit_risk, fraud_risk
from .security import ADMIN, ANALYST, COMPLIANCE, hash_password
from .utils import month_start

DEMO_PASSWORD = "FinGuard123!"
DEMO_USERS = [
    ("Abdoulie Bah", "demo@finguard.ai", ADMIN),
    ("Risk Analyst (demo)", "analyst@finguard.ai", ANALYST),
    ("Compliance Officer (demo)", "compliance@finguard.ai", COMPLIANCE),
]


def seed(db: Session) -> bool:
    """Insert demo data into an empty database. Returns False if data already exists."""
    if db.scalar(select(func.count()).select_from(User)):
        return False
    try:
        users = [User(name=name, email=email, role=role, password_hash=hash_password(DEMO_PASSWORD)) for name, email, role in DEMO_USERS]
        db.add_all(users)
        db.flush()
        admin = users[0]
        operating = Account(user_id=admin.id, account_number="FG10000001", name="Operating Account", type="Checking", currency="EUR", balance_cents=248_650_75, status="active")
        reserve = Account(user_id=admin.id, account_number="FG10000002", name="Reserve Account", type="Savings", currency="EUR", balance_cents=875_420_00, status="active")
        db.add_all([operating, reserve])
        db.flush()
        now = utcnow()
        samples = [
            ("SEPA-24091", "Nordic Cloud GmbH", 12_450_00, "credit", "Revenue", "Invoice settlement"),
            ("CARD-88104", "AWS Europe", -3_284_19, "debit", "Infrastructure", "Cloud services"),
            ("SEPA-24077", "Berlin Office GmbH", -8_900_00, "debit", "Operations", "Office lease"),
            ("SEPA-24063", "Atlas Partners", 34_800_00, "credit", "Revenue", "Consulting payment"),
        ]
        for index, (reference, counterparty, cents, direction, category, description) in enumerate(samples):
            db.add(Transaction(reference=reference, account_id=operating.id, counterparty=counterparty, amount_cents=cents, direction=direction, category=category, description=description, status="completed", created_at=now - timedelta(days=index + 1)))
        _seed_risk_history(db, users[1], now)
        db.add(AuditEvent(action="Demo data initialised (simulated)", actor="System", status="Completed", created_at=now))
        db.commit()
        return True
    except IntegrityError:
        # Another process seeded the database at the same moment.
        db.rollback()
        return False


def _seed_risk_history(db: Session, analyst: User, now: datetime) -> None:
    rng = random.Random(42)
    for months_back in range(5, -1, -1):
        start = month_start(now, months_back)
        end = month_start(now, months_back - 1) if months_back > 0 else now
        intensity = 1 + (5 - months_back) * 0.12  # risk drifts upwards over the period
        for _ in range(16 + rng.randint(0, 6)):
            created_at = start + timedelta(seconds=rng.random() * (end - start).total_seconds())
            kind = rng.choice(["credit", "fraud", "fraud", "aml"])
            if kind == "credit":
                inputs = {"income": float(rng.randint(18, 140) * 1000), "loan_amount": float(rng.randint(5, 90) * 1000), "credit_score": rng.randint(520, 820)}
                result, _ = credit_risk(inputs["income"], inputs["loan_amount"], inputs["credit_score"])
                amount = inputs["loan_amount"]
            elif kind == "fraud":
                inputs = {"transaction_amount": round(rng.lognormvariate(8.3, 0.9) * intensity, 2), "transaction_frequency": rng.randint(1, 28), "international_transfer": rng.random() < 0.35}
                result = fraud_risk(inputs["transaction_amount"], inputs["transaction_frequency"], inputs["international_transfer"])
                amount = inputs["transaction_amount"]
            else:
                inputs = {"transaction_amount": round(rng.lognormvariate(8.8, 0.8) * intensity, 2), "country_risk": rng.choice(["low", "low", "medium", "high"]), "cash_transaction": rng.random() < 0.3, "politically_exposed": rng.random() < 0.12}
                result = aml_risk(inputs["transaction_amount"], inputs["country_risk"], inputs["cash_transaction"], inputs["politically_exposed"])
                amount = inputs["transaction_amount"]
            assessment = RiskAssessment(kind=kind, score=result.score, level=result.level, inputs=json.dumps({**inputs, "simulated": True}, sort_keys=True), engine=ENGINE_VERSION, user_id=analyst.id, created_at=created_at)
            db.add(assessment)
            if kind != "credit" and result.level == "High":
                db.flush()
                _seed_alert(db, rng, kind, assessment, result, amount, now)


def _seed_alert(db: Session, rng: random.Random, kind: str, assessment: RiskAssessment, result: RiskResult, amount: float, now: datetime) -> None:
    age_days = (now - assessment.created_at).days
    if age_days > 21 and rng.random() < 0.85:
        status = "Closed"
    else:
        status = rng.choice(["Open", "Open", "Under Review", "Escalated"])
    if kind == "fraud":
        title, level = "High fraud risk transaction", "High"
    else:
        title, level = "AML case: enhanced due diligence", "Critical" if result.score >= 85 else "High"
    subject = f"Customer {chr(65 + rng.randrange(26))}-{rng.randint(100, 999)} (simulated)"
    db.add(Alert(kind=kind, title=title, subject=subject, level=level, status=status, reason="; ".join(result.factors)[:500], amount_cents=round(amount * 100), assessment_id=assessment.id, created_at=assessment.created_at))
