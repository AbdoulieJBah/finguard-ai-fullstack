from __future__ import annotations

import hashlib
import json
import secrets
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..fraud_checks import check_payment
from ..models import Account, IdempotencyKey, Transaction, User, utcnow
from ..schemas import TransferRequest
from ..security import CurrentUser, DbSession
from ..utils import iso, record_audit

router = APIRouter(tags=["banking"])

IDEMPOTENCY_TTL = timedelta(hours=24)


def utc_hour() -> int:
    """Hour used by the fraud model (a function so tests can fix the time)."""
    return utcnow().hour


def account_json(account: Account) -> dict:
    return {
        "id": account.id,
        "account_number": account.account_number,
        "name": account.name,
        "type": account.type,
        "currency": account.currency,
        "balance": account.balance_cents / 100,
        "status": account.status,
    }


@router.get("/accounts")
def list_accounts(user: CurrentUser, db: DbSession) -> list[dict]:
    accounts = db.scalars(select(Account).where(Account.user_id == user.id).order_by(Account.id))
    return [account_json(account) for account in accounts]


@router.get("/transactions")
def list_transactions(
    user: CurrentUser,
    db: DbSession,
    account_id: int | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[dict]:
    query = (
        select(Transaction, Account.account_number)
        .join(Account, Account.id == Transaction.account_id)
        .where(Account.user_id == user.id)
        .order_by(Transaction.created_at.desc(), Transaction.id.desc())
        .limit(limit)
    )
    if account_id is not None:
        query = query.where(Account.id == account_id)
    return [
        {
            "id": tx.id,
            "reference": tx.reference,
            "account_number": account_number,
            "counterparty": tx.counterparty,
            "amount": tx.amount_cents / 100,
            "direction": tx.direction,
            "category": tx.category,
            "description": tx.description,
            "created_at": iso(tx.created_at),
            "status": tx.status,
        }
        for tx, account_number in db.execute(query)
    ]


def _request_hash(payload: TransferRequest, amount_cents: int) -> str:
    canonical = json.dumps(
        {
            "from_account_id": payload.from_account_id,
            "to_account_number": payload.to_account_number,
            "amount_cents": amount_cents,
            "description": payload.description,
        },
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


def _replay(record: IdempotencyKey, request_hash: str) -> JSONResponse:
    if record.request_hash != request_hash:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "This Idempotency-Key was already used for a different payment. Use a new key for a new payment.",
        )
    return JSONResponse(
        content=json.loads(record.response_body),
        status_code=record.status_code,
        headers={"Idempotent-Replayed": "true"},
    )


def _find_key(db: Session, user: User, key: str) -> IdempotencyKey | None:
    return db.scalar(
        select(IdempotencyKey).where(
            IdempotencyKey.user_id == user.id,
            IdempotencyKey.key == key,
            IdempotencyKey.created_at > utcnow() - IDEMPOTENCY_TTL,
        )
    )


def _move_funds(db: Session, user: User, payload: TransferRequest, amount_cents: int) -> dict:
    source = db.scalar(select(Account).where(Account.id == payload.from_account_id, Account.user_id == user.id))
    if source is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Source account not found")
    target = db.scalar(select(Account).where(Account.account_number == payload.to_account_number))
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Recipient account not found")
    if source.id == target.id:
        raise HTTPException(status.HTTP_409_CONFLICT, "Choose a different recipient account")
    if source.currency != target.currency:
        raise HTTPException(status.HTTP_409_CONFLICT, "Cross-currency transfers are not supported")
    if source.status != "active" or target.status != "active":
        raise HTTPException(status.HTTP_409_CONFLICT, "Both accounts must be active")
    balance_before_cents = source.balance_cents

    # Lock both rows in a fixed order (PostgreSQL) so concurrent opposite transfers cannot deadlock.
    db.execute(
        select(Account.id).where(Account.id.in_([source.id, target.id])).order_by(Account.id).with_for_update()
    ).all()
    # The balance check and the debit are one statement, so two concurrent payments cannot overdraw.
    debit = db.execute(
        update(Account)
        .where(Account.id == source.id, Account.balance_cents >= amount_cents)
        .values(balance_cents=Account.balance_cents - amount_cents)
        .execution_options(synchronize_session=False)
    )
    if debit.rowcount != 1:
        raise HTTPException(status.HTTP_409_CONFLICT, "Insufficient funds")
    db.execute(
        update(Account)
        .where(Account.id == target.id)
        .values(balance_cents=Account.balance_cents + amount_cents)
        .execution_options(synchronize_session=False)
    )

    now = utcnow()
    reference = f"FG-{now:%Y%m%d}-{secrets.token_hex(4).upper()}"
    db.add_all(
        [
            Transaction(
                reference=reference, account_id=source.id, counterparty=target.name, amount_cents=-amount_cents,
                direction="debit", category="Transfer", description=payload.description, status="completed",
                created_at=now,
            ),
            Transaction(
                reference=f"{reference}-IN", account_id=target.id, counterparty=source.name,
                amount_cents=amount_cents, direction="credit", category="Transfer",
                description=payload.description, status="completed", created_at=now,
            ),
        ]
    )
    record_audit(db, f"Transfer {reference} completed", user.name)
    # Every payment is scored by the fraud model; high-risk payments open an alert for review.
    check = check_payment(
        db,
        user,
        amount=amount_cents / 100,
        sender_balance=balance_before_cents / 100,
        hour=utc_hour(),
        transaction_type="TRANSFER",
        subject=f"Payment {reference} from {source.account_number}",
    )
    db.flush()
    balance_cents = db.scalar(select(Account.balance_cents).where(Account.id == source.id))
    return {
        "reference": reference,
        "status": "completed",
        "amount": amount_cents / 100,
        "currency": source.currency,
        "available_balance": balance_cents / 100,
        "created_at": iso(now),
        "fraud_check": {
            "level": check.score.level,
            "probability": round(check.score.probability, 6),
            "score": round(check.score.probability * 100),
            "alert_id": check.alert.id if check.alert else None,
            "assessment_id": check.assessment.id,
            "top_factors": [
                {"label": c.label, "value": c.value, "contribution": round(c.contribution, 4)}
                for c in check.score.contributions[:3]
            ],
            "model_version": check.score.model_version,
        },
    }


@router.post("/transfers", status_code=status.HTTP_201_CREATED)
def create_transfer(
    payload: TransferRequest,
    user: CurrentUser,
    db: DbSession,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key", max_length=255)] = None,
):
    """Move money between two accounts atomically.

    Send an `Idempotency-Key` header (any unique string per payment). If the same request is retried
    with the same key, for example after a timeout, the original result is returned and nothing is
    paid twice.
    """
    amount_cents = int(payload.amount * 100)
    request_hash = _request_hash(payload, amount_cents)
    key = idempotency_key.strip() if idempotency_key else None

    if key:
        existing = _find_key(db, user, key)
        if existing is not None:
            return _replay(existing, request_hash)
        db.execute(delete(IdempotencyKey).where(IdempotencyKey.created_at <= utcnow() - IDEMPOTENCY_TTL))

    try:
        if key:
            # Claim the key first, in the same database transaction as the payment.
            claim = IdempotencyKey(
                user_id=user.id, key=key, request_hash=request_hash, status_code=0, response_body="{}"
            )
            db.add(claim)
            db.flush()
        result = _move_funds(db, user, payload, amount_cents)
        if key:
            claim.status_code = status.HTTP_201_CREATED
            claim.response_body = json.dumps(result)
        db.commit()
    except IntegrityError:
        # Another request with the same key committed first: answer with its result.
        db.rollback()
        existing = _find_key(db, user, key) if key else None
        if existing is None:
            raise
        return _replay(existing, request_hash)
    except HTTPException:
        db.rollback()  # A rejected payment does not use up the key.
        raise
    return result
