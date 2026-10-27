"""Request bodies, validated by Pydantic."""
from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator

Money = Annotated[Decimal, Field(gt=0, le=1_000_000, max_digits=12, decimal_places=2)]


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class TransferRequest(BaseModel):
    from_account_id: int
    to_account_number: str = Field(min_length=8, max_length=20)
    amount: Money
    description: str = Field(default="Internal transfer", min_length=2, max_length=120)


class CreditRiskRequest(BaseModel):
    income: float = Field(gt=0, le=1_000_000_000)
    loan_amount: float = Field(gt=0, le=1_000_000_000)
    credit_score: int = Field(ge=300, le=850)


class FraudRiskRequest(BaseModel):
    transaction_amount: float = Field(gt=0, le=1_000_000_000)
    transaction_frequency: int = Field(ge=1, le=10_000)
    international_transfer: bool = False


class AmlRiskRequest(BaseModel):
    transaction_amount: float = Field(gt=0, le=1_000_000_000)
    country_risk: Literal["low", "medium", "high"] = "low"
    cash_transaction: bool = False
    politically_exposed: bool = False

    @field_validator("country_risk", mode="before")
    @classmethod
    def _lowercase(cls, value: object) -> object:
        return value.strip().lower() if isinstance(value, str) else value


class CopilotRequest(BaseModel):
    question: str = Field(min_length=2, max_length=500)
