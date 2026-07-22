# FinGuard AI

FinGuard is a full-stack demo banking operations and risk-intelligence application. It combines a persistent account ledger and authenticated payments with credit, fraud, AML, audit, and system-health dashboards.

> Demo software only. It does not connect to payment rails and must not be used for real customer funds or production banking decisions.

## What works

- Secure password hashing and bearer-session authentication
- Persistent SQLite accounts, balances, and double-entry internal transfers
- Transaction history and audit events
- Atomic balance updates with ownership, recipient, currency, and funds validation
- Credit, fraud, and AML risk assessment APIs
- Responsive Next.js account, payment, dashboard, copilot, audit, and monitoring screens
- Interactive OpenAPI documentation at `http://localhost:8000/docs`

## Start locally

Requirements: Python 3.10+ and Node.js 20+.

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

In another terminal:

```powershell
cd frontend
Copy-Item .env.example .env.local
npm install
npm run dev
```

Open `http://localhost:3000/login` and use:

- Email: `demo@finguard.ai`
- Password: `FinGuard123!`

The SQLite database is created automatically at `backend/finguard.db`. Set `FINGUARD_DB_PATH` to use a different location and `FINGUARD_CORS_ORIGINS` (comma-separated) for other frontend origins.

## Verification

```powershell
cd frontend
npm run lint
npm run build

cd ..\backend
python -m py_compile main.py
```

## Production hardening

Before any real deployment, replace SQLite with a managed transactional database, place sessions behind an identity provider with MFA/RBAC, use a secrets manager, add idempotency keys and payment approval workflows, encrypt sensitive data, and complete independent security/compliance testing.
