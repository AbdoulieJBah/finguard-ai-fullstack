from __future__ import annotations

import sqlite3

from app.config import normalise_database_url
from app.migrate import set_aside_legacy_sqlite


def test_database_urls_use_psycopg():
    assert normalise_database_url("postgres://u:p@host/db?sslmode=require") == "postgresql+psycopg://u:p@host/db?sslmode=require"
    assert normalise_database_url("postgresql://u:p@host/db") == "postgresql+psycopg://u:p@host/db"
    assert normalise_database_url("postgresql+psycopg://u:p@host/db") == "postgresql+psycopg://u:p@host/db"
    assert normalise_database_url("sqlite:///x.db") == "sqlite:///x.db"


def test_pre_migration_sqlite_file_is_moved_aside(tmp_path):
    path = tmp_path / "old.db"
    connection = sqlite3.connect(path)
    connection.execute("CREATE TABLE users (id INTEGER PRIMARY KEY)")
    connection.commit()
    connection.close()
    set_aside_legacy_sqlite(f"sqlite:///{path}")
    assert not path.exists()
    assert (tmp_path / "old.db.legacy").exists()


def test_migrated_sqlite_file_is_left_alone(tmp_path):
    path = tmp_path / "current.db"
    connection = sqlite3.connect(path)
    connection.execute("CREATE TABLE users (id INTEGER PRIMARY KEY)")
    connection.execute("CREATE TABLE alembic_version (version_num VARCHAR(32))")
    connection.commit()
    connection.close()
    set_aside_legacy_sqlite(f"sqlite:///{path}")
    assert path.exists()
