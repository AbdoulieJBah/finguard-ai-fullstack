from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Response, status
from sqlalchemy import delete, func, select

from ..models import SessionToken, User
from ..schemas import LoginRequest
from ..security import (
    CurrentUser,
    DbSession,
    bearer_token,
    check_unknown_user_password,
    create_session,
    hash_token,
    verify_password,
)
from ..utils import iso, record_audit, user_json

router = APIRouter(tags=["auth"])


@router.post("/auth/login")
def login(payload: LoginRequest, db: DbSession) -> dict:
    email = payload.email.strip().lower()
    user = db.scalar(select(User).where(func.lower(User.email) == email))
    if user is None:
        check_unknown_user_password(payload.password)
    if user is None or not verify_password(payload.password, user.password_hash):
        record_audit(db, "Failed sign-in attempt", email, status="Failed")
        db.commit()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    token, expires_at = create_session(db, user)
    record_audit(db, "Secure session started", user.name)
    db.commit()
    return {"access_token": token, "token_type": "bearer", "expires_at": iso(expires_at), "user": user_json(user)}


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(user: CurrentUser, db: DbSession, authorization: Annotated[str | None, Header()] = None) -> Response:
    token = bearer_token(authorization)
    if token:
        db.execute(delete(SessionToken).where(SessionToken.token_hash == hash_token(token)))
    record_audit(db, "Session ended", user.name)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me")
def me(user: CurrentUser) -> dict:
    return user_json(user)
