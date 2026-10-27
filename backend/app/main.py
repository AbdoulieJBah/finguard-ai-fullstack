"""FastAPI application: wiring, startup and public endpoints."""
from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from . import db
from .config import APP_VERSION, cors_origins, database_url, seed_demo_data
from .migrate import run_migrations, set_aside_legacy_sqlite
from .routers import auth, banking, insights, risk
from .seed import seed


def init_database(url: str | None = None) -> None:
    url = url or database_url()
    set_aside_legacy_sqlite(url)
    db.configure(url)
    run_migrations(url)
    if seed_demo_data():
        with db.SessionLocal() as session:
            seed(session)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    init_database()
    yield


app = FastAPI(
    title="FinGuard Banking API",
    version=APP_VERSION,
    description="Demo banking ledger and risk-intelligence API. All data is simulated.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Idempotency-Key"],
    expose_headers=["Idempotent-Replayed"],
)
app.include_router(auth.router)
app.include_router(banking.router)
app.include_router(risk.router)
app.include_router(insights.router)


@app.get("/", tags=["public"])
def home() -> dict:
    return {"message": "FinGuard Banking API is running", "version": APP_VERSION, "docs": "/docs"}


@app.get("/health", tags=["public"])
def health():
    """Liveness check for the hosting platform. Reveals no data."""
    try:
        with db.SessionLocal() as session:
            session.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return JSONResponse({"status": "unhealthy"}, status_code=503)
    return {"status": "healthy"}
