"""Rule-based risk scoring (v1).

These are transparent scorecards, not trained models: each rule adds points and records why,
so every score can be explained. Trained models can replace them behind the same functions.
"""
from __future__ import annotations

from dataclasses import dataclass, field

ENGINE_VERSION = "rules-1.0"


@dataclass(frozen=True)
class RiskResult:
    score: int
    level: str
    recommendation: str
    factors: list[str] = field(default_factory=list)


def _level(score: int, high: int, medium: int) -> str:
    return "High" if score >= high else "Medium" if score >= medium else "Low"


def credit_risk(income: float, loan_amount: float, credit_score: int) -> tuple[RiskResult, float]:
    debt_ratio = loan_amount / income
    factors: list[str] = []
    if credit_score < 580:
        score, factors = 40, [f"Credit score {credit_score} is below 580 (poor)"]
    elif credit_score < 670:
        score, factors = 25, [f"Credit score {credit_score} is below 670 (fair)"]
    else:
        score, factors = 10, [f"Credit score {credit_score} is 670 or above (good)"]
    if debt_ratio > 0.6:
        score += 40
        factors.append(f"Loan is {debt_ratio:.0%} of annual income (above 60%)")
    elif debt_ratio > 0.4:
        score += 25
        factors.append(f"Loan is {debt_ratio:.0%} of annual income (40-60%)")
    else:
        score += 10
        factors.append(f"Loan is {debt_ratio:.0%} of annual income (40% or less)")
    level = _level(score, high=65, medium=40)
    recommendation = {
        "High": "Decline or require collateral; affordability is weak.",
        "Medium": "Approve only after an affordability review.",
        "Low": "Eligible for standard approval.",
    }[level]
    return RiskResult(score, level, recommendation, factors), round(debt_ratio, 2)


def fraud_risk(amount: float, frequency: int, international: bool) -> RiskResult:
    factors: list[str] = []
    if amount > 10_000:
        score = 40
        factors.append(f"High value: {amount:,.2f} (above 10,000)")
    elif amount > 5_000:
        score = 25
        factors.append(f"Elevated value: {amount:,.2f} (above 5,000)")
    else:
        score = 10
    if frequency > 20:
        score += 35
        factors.append(f"{frequency} transactions in the period (above 20)")
    elif frequency > 10:
        score += 20
        factors.append(f"{frequency} transactions in the period (above 10)")
    else:
        score += 10
    if international:
        score += 25
        factors.append("International transfer")
    level = _level(score, high=70, medium=45)
    recommendation = {
        "High": "Hold the payment and contact the customer before release.",
        "Medium": "Allow, but add to the monitoring queue for review.",
        "Low": "No action needed.",
    }[level]
    return RiskResult(score, level, recommendation, factors or ["No risk indicators triggered"])


def aml_risk(amount: float, country_risk: str, cash: bool, politically_exposed: bool) -> RiskResult:
    factors: list[str] = []
    if amount > 15_000:
        score = 35
        factors.append(f"Large amount: {amount:,.2f} (above 15,000)")
    elif amount > 7_000:
        score = 20
        factors.append(f"Amount {amount:,.2f} above 7,000")
    else:
        score = 10
    score += {"high": 30, "medium": 20, "low": 5}[country_risk]
    if country_risk != "low":
        factors.append(f"{country_risk.capitalize()}-risk jurisdiction")
    if cash:
        score += 20
        factors.append("Cash transaction")
    if politically_exposed:
        score += 25
        factors.append("Politically exposed person (PEP)")
    level = _level(score, high=70, medium=45)
    recommendation = {
        "High": "Open an AML case: run enhanced due diligence and verify source of funds.",
        "Medium": "Request supporting documents and monitor the relationship.",
        "Low": "Standard customer due diligence is sufficient.",
    }[level]
    return RiskResult(score, level, recommendation, factors or ["No risk indicators triggered"])
