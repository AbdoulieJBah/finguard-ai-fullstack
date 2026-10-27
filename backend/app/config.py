"""Runtime configuration, read from environment variables."""
from __future__ import annotations

import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
APP_VERSION = "1.1.0"
SESSION_HOURS = 12


def normalise_database_url(url: str) -> str:
    """Accept the URL formats Neon, Railway and Heroku hand out and use the psycopg 3 driver."""
    url = url.strip()
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


def database_url() -> str:
    """PostgreSQL when DATABASE_URL is set (production); a local SQLite file otherwise (development)."""
    url = os.getenv("DATABASE_URL", "").strip()
    if url:
        return normalise_database_url(url)
    path = Path(os.getenv("FINGUARD_DB_PATH", str(BACKEND_DIR / "finguard_dev.db")))
    return f"sqlite:///{path}"


def cors_origins() -> list[str]:
    raw = os.getenv("FINGUARD_CORS_ORIGINS", "http://localhost:3000")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def seed_demo_data() -> bool:
    return os.getenv("FINGUARD_SEED_DEMO", "true").strip().lower() not in {"0", "false", "no"}


def password_iterations() -> int:
    """PBKDF2 work factor for new password hashes (OWASP 2023 guidance: 600,000 for SHA-256)."""
    return int(os.getenv("FINGUARD_PBKDF2_ITERATIONS", "600000"))
