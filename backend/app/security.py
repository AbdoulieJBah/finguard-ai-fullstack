"""Password hashing, bearer sessions and role checks."""
from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from .config import SESSION_HOURS, password_iterations
from .db import get_db
from .models import SessionToken, User, utcnow

ADMIN = "Administrator"
COMPLIANCE = "Compliance Officer"
ANALYST = "Risk Analyst"
STAFF_ROLES = (ADMIN, COMPLIANCE, ANALYST)
AUDIT_ROLES = (ADMIN, COMPLIANCE)

_ALGORITHM = "pbkdf2_sha256"


def hash_password(password: str, iterations: int | None = None) -> str:
    """Encode as `pbkdf2_sha256$iterations$salt$hash` so the work factor can be raised later."""
    iterations = iterations or password_iterations()
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations)
    return f"{_ALGORITHM}${iterations}${salt}${base64.b64encode(digest).decode()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt, expected = encoded.split("$", 3)
        if algorithm != _ALGORITHM:
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), int(iterations))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(base64.b64encode(digest).decode(), expected)


def check_unknown_user_password(password: str) -> None:
    """Spend the same hashing time for an unknown email as for a wrong password (no account probing)."""
    verify_password(password, f"{_ALGORITHM}${password_iterations()}$unknown-user$")


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_session(db: Session, user: User) -> tuple[str, datetime]:
    token = secrets.token_urlsafe(32)
    expires_at = utcnow() + timedelta(hours=SESSION_HOURS)
    db.execute(delete(SessionToken).where(SessionToken.expires_at <= utcnow()))
    db.add(SessionToken(token_hash=hash_token(token), user_id=user.id, expires_at=expires_at))
    return token, expires_at


def bearer_token(authorization: str | None) -> str | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.removeprefix("Bearer ").strip()
    return token or None


def current_user(
    db: Annotated[Session, Depends(get_db)],
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    token = bearer_token(authorization)
    if token is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Authentication required", headers={"WWW-Authenticate": "Bearer"}
        )
    user = db.scalar(
        select(User)
        .join(SessionToken, SessionToken.user_id == User.id)
        .where(SessionToken.token_hash == hash_token(token), SessionToken.expires_at > utcnow())
    )
    if user is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Session expired or invalid", headers={"WWW-Authenticate": "Bearer"}
        )
    return user


def require_roles(*roles: str):
    """Dependency factory: the signed-in user must hold one of `roles`."""

    def dependency(user: Annotated[User, Depends(current_user)]) -> User:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Your role does not have access to this resource")
        return user

    return dependency


CurrentUser = Annotated[User, Depends(current_user)]
StaffUser = Annotated[User, Depends(require_roles(*STAFF_ROLES))]
AuditUser = Annotated[User, Depends(require_roles(*AUDIT_ROLES))]
DbSession = Annotated[Session, Depends(get_db)]
