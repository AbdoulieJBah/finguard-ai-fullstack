"""Fraud scorecard: a logistic regression on binned features, trained on PaySim (see ml/).

The model is additive in log-odds, so each prediction splits exactly into one contribution
per feature (these are exact SHAP values for this model class):

    logit(x) = base_value + sum_f [ w_f(bin_f(x)) - E[w_f] ]

Inference is plain Python with no numerical libraries, so it adds nothing to the API's install.
The training script checks that this module reproduces its own predictions exactly.
"""
from __future__ import annotations

import json
import math
from bisect import bisect_right
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

MODEL_PATH = Path(__file__).with_name("fraud_scorecard.json")
TRANSACTION_TYPES = ("TRANSFER", "CASH_OUT")


@dataclass(frozen=True)
class Contribution:
    feature: str
    label: str
    value: str
    contribution: float  # change in log-odds versus an average transaction


@dataclass(frozen=True)
class FraudScore:
    probability: float
    level: str
    logit: float
    base_value: float
    contributions: list[Contribution]
    model_version: str


def bin_index(feature: dict, inputs: dict) -> int:
    """Map raw inputs to the feature's bin. Must stay identical to the training code."""
    kind = feature["kind"]
    if kind == "value_bins":
        value = float(inputs[feature["input"]])
        if feature.get("zero_bin") and value <= 0:
            return 0
        offset = 1 if feature.get("zero_bin") else 0
        return offset + bisect_right(feature["edges"], value)
    if kind == "ratio_bins":
        balance = float(inputs["sender_balance"])
        if balance <= 0:
            return 0
        return 1 + bisect_right(feature["edges"], float(inputs["amount"]) / balance)
    if kind == "hour_bins":
        return int(inputs["hour"]) % 24 // feature["width"]
    if kind == "category":
        return feature["categories"].index(inputs[feature["input"]])
    raise ValueError(f"Unknown feature kind: {kind}")


def _money(value: float) -> str:
    return f"{value:,.2f}"


def describe(feature: dict, inputs: dict) -> str:
    name = feature["name"]
    if name == "amount":
        return _money(float(inputs["amount"]))
    if name == "sender_balance":
        return _money(float(inputs["sender_balance"]))
    if name == "balance_share":
        balance = float(inputs["sender_balance"])
        if balance <= 0:
            return "Sender had no balance"
        return f"{float(inputs['amount']) / balance:.0%} of the sender's balance"
    if name == "hour":
        hour = int(inputs["hour"]) % 24
        return f"{hour:02d}:00 UTC"
    if name == "transaction_type":
        return str(inputs["transaction_type"]).replace("_", " ").lower()
    return str(inputs.get(feature["input"], ""))


class FraudModel:
    def __init__(self, spec: dict):
        self.spec = spec
        self.version: str = spec["version"]
        self.features: list[dict] = spec["features"]
        self.base_value: float = spec["base_value"]
        self.thresholds: dict = spec["thresholds"]

    @classmethod
    def load(cls, path: Path = MODEL_PATH) -> "FraudModel":
        return cls(json.loads(path.read_text()))

    def score(self, amount: float, sender_balance: float, hour: int, transaction_type: str = "TRANSFER") -> FraudScore:
        if transaction_type not in TRANSACTION_TYPES:
            raise ValueError(f"transaction_type must be one of {TRANSACTION_TYPES}")
        inputs = {"amount": amount, "sender_balance": sender_balance, "hour": hour, "transaction_type": transaction_type}
        logit = self.base_value
        contributions: list[Contribution] = []
        for feature in self.features:
            phi = feature["weights"][bin_index(feature, inputs)] - feature["expected"]
            logit += phi
            contributions.append(Contribution(feature["name"], feature["label"], describe(feature, inputs), phi))
        contributions.sort(key=lambda c: abs(c.contribution), reverse=True)
        probability = 1.0 / (1.0 + math.exp(-logit))
        if probability >= self.thresholds["high"]:
            level = "High"
        elif probability >= self.thresholds["medium"]:
            level = "Medium"
        else:
            level = "Low"
        return FraudScore(probability, level, logit, self.base_value, contributions, self.version)

    def card(self) -> dict:
        """Public summary for the model card endpoint."""
        keys = ("name", "version", "trained_at", "algorithm", "data", "split", "thresholds", "metrics", "comparison", "baseline", "importance", "limitations")
        return {key: self.spec[key] for key in keys if key in self.spec}


@lru_cache(maxsize=1)
def get_model() -> FraudModel:
    return FraudModel.load()
