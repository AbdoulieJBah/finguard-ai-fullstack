from __future__ import annotations

from sqlalchemy import func, select

from app.models import IdempotencyKey, Transaction


def balances(client, headers) -> dict[str, float]:
    return {a["account_number"]: a["balance"] for a in client.get("/accounts", headers=headers).json()}


def operating_id(client, headers) -> int:
    return next(a["id"] for a in client.get("/accounts", headers=headers).json() if a["account_number"] == "FG10000001")


def transfer(client, headers, amount=250.5, key=None, **overrides):
    body = {"from_account_id": operating_id(client, headers), "to_account_number": "FG10000002", "amount": amount, "description": "Treasury allocation"}
    body.update(overrides)
    extra = {"Idempotency-Key": key} if key else {}
    return client.post("/transfers", json=body, headers={**headers, **extra})


def transaction_count(session) -> int:
    return session.scalar(select(func.count()).select_from(Transaction))


def test_transfer_moves_money_atomically(client, admin, session):
    before = balances(client, admin)
    count_before = transaction_count(session)
    response = transfer(client, admin, amount=250.5)
    assert response.status_code == 201, response.text
    body = response.json()
    after = balances(client, admin)
    assert after["FG10000001"] == round(before["FG10000001"] - 250.5, 2)
    assert after["FG10000002"] == round(before["FG10000002"] + 250.5, 2)
    assert body["available_balance"] == after["FG10000001"]
    assert transaction_count(session) == count_before + 2
    history = client.get("/transactions", headers=admin).json()
    assert {t["reference"] for t in history} >= {body["reference"], body["reference"] + "-IN"}


def test_insufficient_funds_changes_nothing(client, admin, session):
    before = balances(client, admin)
    count_before = transaction_count(session)
    response = transfer(client, admin, amount=999_999)
    assert response.status_code == 409
    assert response.json()["detail"] == "Insufficient funds"
    assert balances(client, admin) == before
    assert transaction_count(session) == count_before


def test_unknown_recipient_and_self_transfer_are_rejected(client, admin):
    assert transfer(client, admin, to_account_number="FG99999999").status_code == 404
    assert transfer(client, admin, to_account_number="FG10000001").status_code == 409


def test_cannot_spend_from_someone_elses_account(client, admin, analyst):
    body = {"from_account_id": operating_id(client, admin), "to_account_number": "FG10000002", "amount": 10, "description": "Not mine"}
    response = client.post("/transfers", json=body, headers=analyst)
    assert response.status_code == 404


def test_amount_validation(client, admin):
    assert transfer(client, admin, amount=1.005).status_code == 422  # more than two decimals
    assert transfer(client, admin, amount=-5).status_code == 422
    assert transfer(client, admin, amount=0).status_code == 422


def test_retry_with_same_idempotency_key_pays_once(client, admin, session):
    before = balances(client, admin)
    count_before = transaction_count(session)
    first = transfer(client, admin, amount=100, key="payment-123")
    second = transfer(client, admin, amount=100, key="payment-123")
    assert first.status_code == 201 and second.status_code == 201
    assert second.json() == first.json()
    assert second.headers.get("idempotent-replayed") == "true"
    assert balances(client, admin)["FG10000001"] == round(before["FG10000001"] - 100, 2)
    assert transaction_count(session) == count_before + 2


def test_reusing_a_key_for_a_different_payment_is_refused(client, admin):
    assert transfer(client, admin, amount=100, key="payment-abc").status_code == 201
    response = transfer(client, admin, amount=200, key="payment-abc")
    assert response.status_code == 409
    assert "different payment" in response.json()["detail"]


def test_rejected_payment_does_not_use_up_the_key(client, admin, session):
    assert transfer(client, admin, amount=999_999, key="payment-xyz").status_code == 409
    assert session.scalar(select(func.count()).select_from(IdempotencyKey)) == 0
    assert transfer(client, admin, amount=999_999, key="payment-xyz").status_code == 409
    response = transfer(client, admin, amount=50, key="payment-xyz")
    assert response.status_code == 201


def test_different_keys_make_separate_payments(client, admin):
    before = balances(client, admin)
    assert transfer(client, admin, amount=10, key="a-1").status_code == 201
    assert transfer(client, admin, amount=10, key="a-2").status_code == 201
    assert balances(client, admin)["FG10000001"] == round(before["FG10000001"] - 20, 2)
