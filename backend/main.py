from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="FinGuard AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {"message": "FinGuard AI Backend is running"}


@app.get("/dashboard-metrics")
def dashboard_metrics():
    return {
        "risk_score": 82,
        "fraud_alerts": 24,
        "aml_cases": 13,
        "ai_predictions": 1284,
    }


@app.post("/copilot")
def copilot(request: dict):
    question = request.get("question", "").lower()

    if "fraud" in question:
        response = "Fraud activity is elevated. Prioritize suspicious high-value transactions."
    elif "credit" in question or "risk" in question:
        response = "Credit risk exposure is moderate with increased retail lending volatility."
    elif "aml" in question or "compliance" in question:
        response = "AML monitoring identified active compliance investigations requiring review."
    elif "audit" in question:
        response = "Audit logs show AI decisions, fraud alerts, AML reviews, and executive actions are being tracked."
    else:
        response = "FinGuard AI recommends reviewing dashboard metrics and generating an executive risk report."

    return {"response": response}


@app.post("/predict-credit-risk")
def predict_credit_risk(request: dict):
    income = float(request.get("income", 0))
    loan_amount = float(request.get("loan_amount", 0))
    credit_score = float(request.get("credit_score", 600))

    debt_ratio = loan_amount / income if income > 0 else 1

    risk_score = 0

    if credit_score < 580:
        risk_score += 40
    elif credit_score < 670:
        risk_score += 25
    else:
        risk_score += 10

    if debt_ratio > 0.6:
        risk_score += 40
    elif debt_ratio > 0.4:
        risk_score += 25
    else:
        risk_score += 10

    if risk_score >= 65:
        risk_level = "High"
    elif risk_score >= 40:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    return {
        "income": income,
        "loan_amount": loan_amount,
        "credit_score": credit_score,
        "debt_ratio": round(debt_ratio, 2),
        "risk_score": risk_score,
        "risk_level": risk_level,
        "recommendation": f"Credit risk is {risk_level}. Review affordability and repayment capacity.",
    }


@app.post("/predict-fraud-risk")
def predict_fraud_risk(request: dict):
    transaction_amount = float(request.get("transaction_amount", 0))
    transaction_frequency = int(request.get("transaction_frequency", 1))
    international_transfer = bool(request.get("international_transfer", False))

    fraud_score = 0

    if transaction_amount > 10000:
        fraud_score += 40
    elif transaction_amount > 5000:
        fraud_score += 25
    else:
        fraud_score += 10

    if transaction_frequency > 20:
        fraud_score += 35
    elif transaction_frequency > 10:
        fraud_score += 20
    else:
        fraud_score += 10

    if international_transfer:
        fraud_score += 25

    if fraud_score >= 70:
        fraud_level = "High"
    elif fraud_score >= 45:
        fraud_level = "Medium"
    else:
        fraud_level = "Low"

    return {
        "transaction_amount": transaction_amount,
        "transaction_frequency": transaction_frequency,
        "international_transfer": international_transfer,
        "fraud_score": fraud_score,
        "fraud_level": fraud_level,
        "recommendation": f"Fraud risk classified as {fraud_level}. Review transaction monitoring alerts.",
    }


@app.post("/predict-aml-risk")
def predict_aml_risk(request: dict):
    transaction_amount = float(request.get("transaction_amount", 0))
    country_risk = request.get("country_risk", "low").lower()
    cash_transaction = bool(request.get("cash_transaction", False))
    politically_exposed = bool(request.get("politically_exposed", False))

    aml_score = 0

    if transaction_amount > 15000:
        aml_score += 35
    elif transaction_amount > 7000:
        aml_score += 20
    else:
        aml_score += 10

    if country_risk == "high":
        aml_score += 30
    elif country_risk == "medium":
        aml_score += 20
    else:
        aml_score += 5

    if cash_transaction:
        aml_score += 20

    if politically_exposed:
        aml_score += 25

    if aml_score >= 70:
        aml_level = "High"
    elif aml_score >= 45:
        aml_level = "Medium"
    else:
        aml_level = "Low"

    return {
        "transaction_amount": transaction_amount,
        "country_risk": country_risk,
        "cash_transaction": cash_transaction,
        "politically_exposed": politically_exposed,
        "aml_score": aml_score,
        "aml_level": aml_level,
        "recommendation": f"AML risk classified as {aml_level}. Review KYC, source of funds, and transaction pattern.",
    }


@app.get("/fraud-alerts")
def fraud_alerts():
    return [
        {
            "id": 1,
            "customer": "Customer A",
            "amount": 12500,
            "risk": "High",
            "reason": "High-value international transfer",
        },
        {
            "id": 2,
            "customer": "Customer B",
            "amount": 6800,
            "risk": "Medium",
            "reason": "Unusual transaction frequency",
        },
        {
            "id": 3,
            "customer": "Customer C",
            "amount": 21000,
            "risk": "High",
            "reason": "Multiple high-value transfers",
        },
    ]


@app.get("/aml-cases")
def aml_cases():
    return [
        {
            "id": 1,
            "case": "Cross-border transfer anomaly",
            "level": "Critical",
            "status": "Open",
        },
        {
            "id": 2,
            "case": "Enhanced due diligence review",
            "level": "Medium",
            "status": "Under Review",
        },
        {
            "id": 3,
            "case": "Cash transaction monitoring",
            "level": "High",
            "status": "Escalated",
        },
    ]


@app.get("/audit-logs")
def audit_logs():
    return [
        {
            "action": "Fraud alert escalated",
            "user": "Risk Analyst",
            "time": "10 mins ago",
            "status": "Critical",
        },
        {
            "action": "AML case reviewed",
            "user": "Compliance Officer",
            "time": "35 mins ago",
            "status": "Completed",
        },
        {
            "action": "Credit risk report generated",
            "user": "Executive AI Copilot",
            "time": "1 hour ago",
            "status": "Generated",
        },
        {
            "action": "Suspicious transaction blocked",
            "user": "Fraud Engine",
            "time": "2 hours ago",
            "status": "Blocked",
        },
    ]


@app.get("/risk-trends")
def risk_trends():
    return [
        {"month": "Jan", "risk": 45, "fraud": 20, "aml": 15},
        {"month": "Feb", "risk": 52, "fraud": 25, "aml": 18},
        {"month": "Mar", "risk": 48, "fraud": 22, "aml": 17},
        {"month": "Apr", "risk": 70, "fraud": 40, "aml": 29},
        {"month": "May", "risk": 66, "fraud": 38, "aml": 31},
        {"month": "Jun", "risk": 82, "fraud": 50, "aml": 36},
    ]


@app.get("/system-health")
def system_health():
    return {
        "frontend": "Online",
        "backend": "Online",
        "ml_services": "Active",
        "database": "Connected",
        "copilot": "Ready",
    }