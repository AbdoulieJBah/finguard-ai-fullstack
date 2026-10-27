"""Small helpers shared by the routers."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from .models import AuditEvent, User, utcnow


def as_utc(value: datetime) -> datetime:
    """SQLite returns naive datetimes; everything is stored in UTC, so attach the zone."""
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def iso(value: datetime) -> str:
    return as_utc(value).isoformat()


def month_start(now: datetime, months_back: int) -> datetime:
    year, month = now.year, now.month - months_back
    while month <= 0:
        month += 12
        year -= 1
    return datetime(year, month, 1, tzinfo=timezone.utc)


def record_audit(db: Session, action: str, actor: str, status: str = "Completed") -> None:
    db.add(AuditEvent(action=action[:255], actor=actor[:255], status=status, created_at=utcnow()))


def user_json(user: User) -> dict:
    return {"id": user.id, "name": user.name, "email": user.email, "role": user.role}
