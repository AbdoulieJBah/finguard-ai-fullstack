"""Apply Alembic migrations programmatically at startup."""
from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

from alembic import command
from alembic.config import Config

from .config import BACKEND_DIR

log = logging.getLogger("finguard")


def alembic_config(url: str) -> Config:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    config.attributes["configure_logger"] = False
    return config


def set_aside_legacy_sqlite(url: str) -> None:
    """FinGuard 1.0 created its SQLite tables without migrations. Move such a file aside and start fresh."""
    if not url.startswith("sqlite:///"):
        return
    path = Path(url.removeprefix("sqlite:///"))
    if not path.exists():
        return
    connection = sqlite3.connect(path)
    try:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    finally:
        connection.close()
    if "users" in tables and "alembic_version" not in tables:
        legacy = path.with_name(path.name + ".legacy")
        path.replace(legacy)
        log.warning("Moved pre-migration SQLite database to %s", legacy)


def run_migrations(url: str) -> None:
    command.upgrade(alembic_config(url), "head")
