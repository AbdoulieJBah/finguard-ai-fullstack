# FinGuard AI

Full-stack AI-powered banking intelligence platform.

## Tech Stack

- Frontend: Next.js, React, TypeScript, Tailwind CSS
- Backend: FastAPI, Python
- Charts: Recharts
- AI/ML: Scikit-learn-ready backend architecture
- API Docs: FastAPI Swagger UI

---

## Features

- Executive Banking Dashboard
- Credit Risk Prediction
- Fraud Detection Monitoring
- AML Case Monitoring
- AI Banking Copilot
- Audit Logs
- FastAPI Backend APIs
- Real-time Frontend ↔ Backend Integration

---

## Project Structure

```text
finguard-ai/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   └── venv/
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   └── components/
│   ├── package.json
│   └── ...
│
├── .gitignore
└── README.md
```

---

## Run Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend URL:

```text
http://localhost:3000
```

---

## Run Backend

```bash
cd backend

python -m venv venv

# Windows
.\venv\Scripts\activate

pip install -r requirements.txt

python -m uvicorn main:app --reload
```

Backend URL:

```text
http://localhost:8000
```

API Documentation:

```text
http://localhost:8000/docs
```

---

## Backend APIs

### Dashboard Metrics

```http
GET /dashboard-metrics
```

### AI Copilot

```http
POST /copilot
```

### Credit Risk Prediction

```http
POST /predict-credit-risk
```

### Fraud Risk Prediction

```http
POST /predict-fraud-risk
```

### AML Risk Prediction

```http
POST /predict-aml-risk
```

### Fraud Alerts

```http
GET /fraud-alerts
```

### AML Cases

```http
GET /aml-cases
```

### Audit Logs

```http
GET /audit-logs
```

### Risk Trends

```http
GET /risk-trends
```

### System Health

```http
GET /system-health
```

---

## Future Enhancements

- PostgreSQL Database
- Real Machine Learning Models
- OpenAI/Gemini Integration
- Docker Deployment
- AWS/Azure Deployment
- Authentication & RBAC
- Real-time WebSocket Monitoring
- PDF Executive Reports
- Kafka Streaming Pipelines
- Vector Database + RAG AI Copilot

---

## Author

Abdoulie Bah

AI Engineer | Data Analyst | Full-Stack AI Developer