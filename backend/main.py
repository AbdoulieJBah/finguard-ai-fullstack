from __future__ import annotations

import hashlib
import os
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("FINGUARD_DB_PATH", BASE_DIR / "finguard.db"))

app = FastAPI(
    title="FinGuard Banking API",
    version="1.0.0",
    description="Demo banking ledger and risk-intelligence API.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("FINGUARD_CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=8)


class TransferRequest(BaseModel):
    from_account_id: int
    to_account_number: str = Field(min_length=8, max_length=20)
    amount: float = Field(gt=0, le=1_000_000)
    description: str = Field(default="Internal transfer", min_length=2, max_length=120)


class CreditRiskRequest(BaseModel):
    income: float = Field(gt=0)
    loan_amount: float = Field(gt=0)
    credit_score: int = Field(ge=300, le=850)


class FraudRiskRequest(BaseModel):
    transaction_amount: float = Field(gt=0)
    transaction_frequency: int = Field(ge=1)
    international_transfer: bool = False


class AmlRiskRequest(BaseModel):
    transaction_amount: float = Field(gt=0)
    country_risk: str = "low"
    cash_transaction: bool = False
    politically_exposed: bool = False


class CopilotRequest(BaseModel):
    question: str = Field(min_length=2, max_length=500)


def password_hash(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000).hex()


@contextmanager
def db():
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_db() -> None:
    with db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL, salt TEXT NOT NULL, role TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY, user_id INTEGER NOT NULL, expires_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, account_number TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL, type TEXT NOT NULL, currency TEXT NOT NULL DEFAULT 'EUR',
                balance_cents INTEGER NOT NULL CHECK(balance_cents >= 0), status TEXT NOT NULL DEFAULT 'active',
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT, reference TEXT UNIQUE NOT NULL,
                account_id INTEGER NOT NULL, counterparty TEXT NOT NULL, amount_cents INTEGER NOT NULL,
                direction TEXT NOT NULL, category TEXT NOT NULL, description TEXT NOT NULL,
                created_at TEXT NOT NULL, status TEXT NOT NULL,
                FOREIGN KEY(account_id) REFERENCES accounts(id)
            );
            CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT NOT NULL, actor TEXT NOT NULL,
                status TEXT NOT NULL, created_at TEXT NOT NULL
            );
            """
        )
        if not conn.execute("SELECT 1 FROM users LIMIT 1").fetchone():
            salt = secrets.token_hex(16)
            conn.execute(
                "INSERT INTO users(name,email,password_hash,salt,role) VALUES(?,?,?,?,?)",
                ("Abdoulie Bah", "demo@finguard.ai", password_hash("FinGuard123!", salt), salt, "Administrator"),
            )
            user_id = conn.execute("SELECT id FROM users WHERE email=?", ("demo@finguard.ai",)).fetchone()["id"]
            conn.executemany(
                "INSERT INTO accounts(user_id,account_number,name,type,currency,balance_cents) VALUES(?,?,?,?,?,?)",
                [(user_id, "FG10000001", "Operating Account", "Checking", "EUR", 248_650_75),
                 (user_id, "FG10000002", "Reserve Account", "Savings", "EUR", 875_420_00)],
            )
            account_id = conn.execute("SELECT id FROM accounts WHERE account_number='FG10000001'").fetchone()["id"]
            samples = [
                ("SEPA-24091", account_id, "Nordic Cloud GmbH", 12_450_00, "credit", "Revenue", "Invoice settlement"),
                ("CARD-88104", account_id, "AWS Europe", -3_284_19, "debit", "Infrastructure", "Cloud services"),
                ("SEPA-24077", account_id, "Berlin Office GmbH", -8_900_00, "debit", "Operations", "Office lease"),
                ("SEPA-24063", account_id, "Atlas Partners", 34_800_00, "credit", "Revenue", "Consulting payment"),
            ]
            for index, row in enumerate(samples):
                conn.execute(
                    "INSERT INTO transactions(reference,account_id,counterparty,amount_cents,direction,category,description,created_at,status) VALUES(?,?,?,?,?,?,?,?,?)",
                    (*row, (datetime.now(timezone.utc) - timedelta(days=index + 1)).isoformat(), "completed"),
                )


@app.on_event("startup")
def startup() -> None:
    init_db()


def current_user(authorization: Annotated[str | None, Header()] = None) -> sqlite3.Row:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authentication required")
    token = authorization.removeprefix("Bearer ").strip()
    with db() as conn:
        row = conn.execute(
            "SELECT u.* FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token=? AND s.expires_at>?",
            (token, now_iso()),
        ).fetchone()
    if not row:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expired or invalid")
    return row


def account_json(row: sqlite3.Row) -> dict:
    return {"id": row["id"], "account_number": row["account_number"], "name": row["name"],
            "type": row["type"], "currency": row["currency"], "balance": row["balance_cents"] / 100,
            "status": row["status"]}


@app.get("/")
def home():
    return {"message": "FinGuard Banking API is running", "docs": "/docs"}


@app.get("/health")
def health():
    with db() as conn:
        conn.execute("SELECT 1")
    return {"status": "healthy", "database": "connected", "timestamp": now_iso()}


@app.post("/auth/login")
def login(payload: LoginRequest):
    with db() as conn:
        user = conn.execute("SELECT * FROM users WHERE lower(email)=lower(?)", (payload.email,)).fetchone()
        if not user or password_hash(payload.password, user["salt"]) != user["password_hash"]:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
        token = secrets.token_urlsafe(32)
        expires = (datetime.now(timezone.utc) + timedelta(hours=12)).isoformat()
        conn.execute("DELETE FROM sessions WHERE expires_at<=?", (now_iso(),))
        conn.execute("INSERT INTO sessions(token,user_id,expires_at) VALUES(?,?,?)", (token, user["id"], expires))
        conn.execute("INSERT INTO audit_events(action,actor,status,created_at) VALUES(?,?,?,?)", ("Secure session started", user["name"], "Completed", now_iso()))
    return {"access_token": token, "token_type": "bearer", "expires_at": expires,
            "user": {"id": user["id"], "name": user["name"], "email": user["email"], "role": user["role"]}}


@app.get("/me")
def me(user: Annotated[sqlite3.Row, Depends(current_user)]):
    return {"id": user["id"], "name": user["name"], "email": user["email"], "role": user["role"]}


@app.get("/accounts")
def accounts(user: Annotated[sqlite3.Row, Depends(current_user)]):
    with db() as conn:
        rows = conn.execute("SELECT * FROM accounts WHERE user_id=? ORDER BY id", (user["id"],)).fetchall()
    return [account_json(row) for row in rows]


@app.get("/transactions")
def transactions(user: Annotated[sqlite3.Row, Depends(current_user)], account_id: int | None = None,
                 limit: int = Query(50, ge=1, le=200)):
    params: list[object] = [user["id"]]
    clause = ""
    if account_id is not None:
        clause = " AND a.id=?"
        params.append(account_id)
    params.append(limit)
    with db() as conn:
        rows = conn.execute(
            f"SELECT t.*,a.account_number FROM transactions t JOIN accounts a ON a.id=t.account_id WHERE a.user_id=?{clause} ORDER BY t.created_at DESC LIMIT ?",
            params,
        ).fetchall()
    return [{"id": r["id"], "reference": r["reference"], "account_number": r["account_number"],
             "counterparty": r["counterparty"], "amount": r["amount_cents"] / 100, "direction": r["direction"],
             "category": r["category"], "description": r["description"], "created_at": r["created_at"], "status": r["status"]} for r in rows]


@app.post("/transfers", status_code=201)
def transfer(payload: TransferRequest, user: Annotated[sqlite3.Row, Depends(current_user)]):
    amount_cents = round(payload.amount * 100)
    if amount_cents <= 0:
        raise HTTPException(422, "Amount must be at least 0.01")
    with db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        source = conn.execute("SELECT * FROM accounts WHERE id=? AND user_id=?", (payload.from_account_id, user["id"])).fetchone()
        target = conn.execute("SELECT * FROM accounts WHERE account_number=?", (payload.to_account_number,)).fetchone()
        if not source:
            raise HTTPException(404, "Source account not found")
        if not target:
            raise HTTPException(404, "Recipient account not found")
        if source["id"] == target["id"]:
            raise HTTPException(409, "Choose a different recipient account")
        if source["currency"] != target["currency"]:
            raise HTTPException(409, "Cross-currency transfers are not supported")
        if source["balance_cents"] < amount_cents:
            raise HTTPException(409, "Insufficient funds")
        conn.execute("UPDATE accounts SET balance_cents=balance_cents-? WHERE id=?", (amount_cents, source["id"]))
        conn.execute("UPDATE accounts SET balance_cents=balance_cents+? WHERE id=?", (amount_cents, target["id"]))
        reference = f"FG-{datetime.now(timezone.utc):%Y%m%d}-{secrets.token_hex(3).upper()}"
        created = now_iso()
        conn.execute("INSERT INTO transactions(reference,account_id,counterparty,amount_cents,direction,category,description,created_at,status) VALUES(?,?,?,?,?,?,?,?,?)",
                     (reference, source["id"], target["name"], -amount_cents, "debit", "Transfer", payload.description, created, "completed"))
        conn.execute("INSERT INTO transactions(reference,account_id,counterparty,amount_cents,direction,category,description,created_at,status) VALUES(?,?,?,?,?,?,?,?,?)",
                     (reference + "-IN", target["id"], source["name"], amount_cents, "credit", "Transfer", payload.description, created, "completed"))
        conn.execute("INSERT INTO audit_events(action,actor,status,created_at) VALUES(?,?,?,?)",
                     (f"Transfer {reference} approved", user["name"], "Completed", created))
        balance = (source["balance_cents"] - amount_cents) / 100
    return {"reference": reference, "status": "completed", "amount": amount_cents / 100,
            "currency": source["currency"], "available_balance": balance, "created_at": created}


@app.get("/dashboard-metrics")
def dashboard_metrics():
    with db() as conn:
        predictions = conn.execute("SELECT COUNT(*) count FROM audit_events").fetchone()["count"]
    return {"risk_score": 64, "fraud_alerts": 3, "aml_cases": 3, "ai_predictions": 1284 + predictions}


@app.post("/predict-credit-risk")
def predict_credit_risk(request: CreditRiskRequest):
    debt_ratio = request.loan_amount / request.income
    risk_score = (40 if request.credit_score < 580 else 25 if request.credit_score < 670 else 10) + (40 if debt_ratio > .6 else 25 if debt_ratio > .4 else 10)
    level = "High" if risk_score >= 65 else "Medium" if risk_score >= 40 else "Low"
    return {**request.model_dump(), "debt_ratio": round(debt_ratio, 2), "risk_score": risk_score, "risk_level": level,
            "recommendation": f"Credit risk is {level}. Review affordability and repayment capacity."}


@app.post("/predict-fraud-risk")
def predict_fraud_risk(request: FraudRiskRequest):
    score = (40 if request.transaction_amount > 10000 else 25 if request.transaction_amount > 5000 else 10) + (35 if request.transaction_frequency > 20 else 20 if request.transaction_frequency > 10 else 10) + (25 if request.international_transfer else 0)
    level = "High" if score >= 70 else "Medium" if score >= 45 else "Low"
    return {**request.model_dump(), "fraud_score": score, "fraud_level": level,
            "recommendation": f"Fraud risk classified as {level}. Review transaction monitoring alerts."}


@app.post("/predict-aml-risk")
def predict_aml_risk(request: AmlRiskRequest):
    country = request.country_risk.lower()
    if country not in {"low", "medium", "high"}:
        raise HTTPException(422, "country_risk must be low, medium, or high")
    score = (35 if request.transaction_amount > 15000 else 20 if request.transaction_amount > 7000 else 10) + ({"high": 30, "medium": 20, "low": 5}[country]) + (20 if request.cash_transaction else 0) + (25 if request.politically_exposed else 0)
    level = "High" if score >= 70 else "Medium" if score >= 45 else "Low"
    return {**request.model_dump(), "country_risk": country, "aml_score": score, "aml_level": level,
            "recommendation": f"AML risk classified as {level}. Review KYC, source of funds, and transaction pattern."}


@app.post("/copilot")
def copilot(request: CopilotRequest):
    question = request.question.lower()
    if "fraud" in question: response = "Fraud activity is elevated. Prioritize suspicious high-value transactions."
    elif "credit" in question or "risk" in question: response = "Portfolio risk is moderate. Review affordability for higher debt-to-income applications."
    elif "aml" in question or "compliance" in question: response = "Three AML investigations require review; prioritize high-risk cross-border activity."
    elif "balance" in question: response = "Open Accounts to see current available balances and recent ledger activity."
    else: response = "Review risk alerts, account liquidity, and outstanding compliance cases before approving material transfers."
    return {"response": response}


@app.get("/fraud-alerts")
def fraud_alerts():
    return [{"id": 1, "customer": "Customer A", "amount": 12500, "risk": "High", "reason": "High-value international transfer"}, {"id": 2, "customer": "Customer B", "amount": 6800, "risk": "Medium", "reason": "Unusual transaction frequency"}, {"id": 3, "customer": "Customer C", "amount": 21000, "risk": "High", "reason": "Multiple high-value transfers"}]


@app.get("/aml-cases")
def aml_cases():
    return [{"id": 1, "case": "Cross-border transfer anomaly", "level": "Critical", "status": "Open"}, {"id": 2, "case": "Enhanced due diligence review", "level": "Medium", "status": "Under Review"}, {"id": 3, "case": "Cash transaction monitoring", "level": "High", "status": "Escalated"}]


@app.get("/audit-logs")
def audit_logs():
    with db() as conn:
        rows = conn.execute("SELECT action,actor,status,created_at FROM audit_events ORDER BY id DESC LIMIT 20").fetchall()
    defaults = [{"action": "Fraud alert escalated", "user": "Risk Analyst", "time": "10 mins ago", "status": "Critical"}, {"action": "AML case reviewed", "user": "Compliance Officer", "time": "35 mins ago", "status": "Completed"}]
    return ([{"action": r["action"], "user": r["actor"], "time": r["created_at"], "status": r["status"]} for r in rows] + defaults)


@app.get("/risk-trends")
def risk_trends():
    return [{"month": "Jan", "risk": 45, "fraud": 20, "aml": 15}, {"month": "Feb", "risk": 52, "fraud": 25, "aml": 18}, {"month": "Mar", "risk": 48, "fraud": 22, "aml": 17}, {"month": "Apr", "risk": 70, "fraud": 40, "aml": 29}, {"month": "May", "risk": 66, "fraud": 38, "aml": 31}, {"month": "Jun", "risk": 64, "fraud": 35, "aml": 28}]


@app.get("/system-health")
def system_health():
    with db() as conn: conn.execute("SELECT 1")
    return {"frontend": "Online", "backend": "Online", "ml_services": "Active", "database": "Connected", "copilot": "Ready"}


init_db()
