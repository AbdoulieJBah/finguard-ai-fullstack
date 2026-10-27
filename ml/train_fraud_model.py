#!/usr/bin/env python3
"""Train FinGuard's fraud model on the PaySim dataset.

    pip install -r ml/requirements.txt
    python ml/train_fraud_model.py --data path/to/paysim.zip      (or the extracted .csv)

PaySim (Lopez-Rojas, Elmir and Axelsson, 2016) is a simulated mobile-money log of 6.3 million
transactions with fraud labels: https://www.kaggle.com/datasets/ealaxi/paysim1 (CC BY-SA 4.0).

What it does
  * Keeps TRANSFER and CASH_OUT rows (PaySim fraud only occurs in these two types).
  * Uses only inputs FinGuard has when a payment is made: amount, sender balance before,
    share of the balance moved, hour of day, transaction type. Recipient balances are left
    out on purpose: in PaySim they are often not updated for fraud rows, an artefact of the
    simulator that a real ledger (and FinGuard) never produces.
  * Splits by time (steps): first 60% of rows to train, next 20% to choose settings and
    thresholds, last 20% as an untouched test set.
  * Compares two model families against four class-imbalance strategies (none, class
    weights, random undersampling, SMOTE) and selects on validation PR-AUC only.
  * Deploys the best additive scorecard (binned logistic regression): every score splits
    exactly into one contribution per feature, so each alert can be explained.

Outputs
  backend/app/ml/fraud_scorecard.json   model read by the API
  ml/report/metrics.json and *.png      evaluation details
  ml/MODEL_CARD.md                      generated model card
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, precision_recall_curve, roc_auc_score
from sklearn.neighbors import NearestNeighbors

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.ml.fraud import FraudModel  # noqa: E402  pure-Python scorer used by the API

SEED = 42
TYPES = ["TRANSFER", "CASH_OUT"]
RATIO_EDGES = [0.1, 0.25, 0.5, 0.75, 0.9, 0.999, 1.000001]
HOUR_WIDTH = 3
STRATEGIES = ["none", "class_weight", "undersample", "smote"]
RESAMPLED_RATIO = 0.1  # minority:majority after undersampling or SMOTE
C_GRID = [0.03, 0.3, 3.0]
STRATEGY_NAMES = {"none": "no rebalancing", "class_weight": "class weights", "undersample": "random undersampling", "smote": "SMOTE"}


def log(message: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)


# ---------------------------------------------------------------- data

def load_paysim(path: Path) -> pd.DataFrame:
    columns = ["step", "type", "amount", "oldbalanceOrg", "isFraud"]
    df = pd.read_csv(path, usecols=columns, dtype={"step": "int32", "type": "category", "amount": "float64", "oldbalanceOrg": "float64", "isFraud": "int8"})
    return prepare(df)


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    df = df[df["type"].isin(TYPES)].copy()
    return pd.DataFrame(
        {
            "step": df["step"].to_numpy(),
            "amount": df["amount"].to_numpy(dtype="float64"),
            "sender_balance": df["oldbalanceOrg"].to_numpy(dtype="float64"),
            "hour": ((df["step"].to_numpy() - 1) % 24).astype("int64"),
            "transaction_type": df["type"].astype(str).to_numpy(),
            "is_fraud": df["isFraud"].to_numpy(dtype="int8"),
        }
    )


def synthetic_paysim(n: int, rng: np.random.Generator) -> pd.DataFrame:
    """PaySim-shaped random data, only for testing this script without the real file."""
    step = np.sort(rng.integers(1, 744, n))
    fraud = rng.random(n) < 0.004
    kind = np.where(rng.random(n) < 0.6, "CASH_OUT", "TRANSFER")
    balance = np.where(rng.random(n) < 0.3, 0.0, rng.lognormal(10.5, 1.6, n))
    amount = rng.lognormal(11.2, 1.3, n)
    amount = np.where(fraud, np.where(balance > 0, balance, amount), amount)
    night = rng.random(n) < 0.5
    step = np.where(fraud & night, step - (step - 1) % 24 + rng.integers(0, 6, n), step)
    return prepare(pd.DataFrame({"step": step, "type": kind, "amount": amount, "oldbalanceOrg": balance, "isFraud": fraud.astype("int8")}))


def time_split(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    steps = df["step"].to_numpy()
    cut_valid, cut_test = np.quantile(steps, [0.6, 0.8])
    parts = {
        "train": df[steps <= cut_valid],
        "validation": df[(steps > cut_valid) & (steps <= cut_test)],
        "test": df[steps > cut_test],
    }
    info = {
        name: {
            "steps": [int(part["step"].min()), int(part["step"].max())],
            "rows": int(len(part)),
            "frauds": int(part["is_fraud"].sum()),
            "fraud_rate": float(part["is_fraud"].mean()),
        }
        for name, part in parts.items()
    }
    return parts["train"].reset_index(drop=True), parts["validation"].reset_index(drop=True), parts["test"].reset_index(drop=True), info


# ---------------------------------------------------------------- scorecard features

def nice(value: float) -> float:
    return float(f"{value:.2g}")


def quantile_edges(values: np.ndarray, n_bins: int) -> list[float]:
    quantiles = np.quantile(values, np.linspace(0, 1, n_bins + 1)[1:-1])
    return sorted({nice(q) for q in quantiles if q > 0})


def fmt(value: float) -> str:
    return f"{value:,.0f}" if value >= 10 else f"{value:g}"


def build_features(train: pd.DataFrame) -> list[dict]:
    positive_balances = train.loc[train["sender_balance"] > 0, "sender_balance"].to_numpy()
    features = [
        {"name": "amount", "label": "Amount", "kind": "value_bins", "input": "amount", "edges": quantile_edges(train["amount"].to_numpy(), 10)},
        {"name": "sender_balance", "label": "Sender balance before", "kind": "value_bins", "input": "sender_balance", "zero_bin": True, "edges": quantile_edges(positive_balances, 8)},
        {"name": "balance_share", "label": "Share of balance moved", "kind": "ratio_bins", "edges": RATIO_EDGES},
        {"name": "hour", "label": "Hour of day", "kind": "hour_bins", "width": HOUR_WIDTH},
        {"name": "transaction_type", "label": "Transaction type", "kind": "category", "input": "transaction_type", "categories": TYPES},
    ]
    for feature in features:
        feature["bin_labels"] = bin_labels(feature)
        feature["n_bins"] = len(feature["bin_labels"])
    return features


def interval_labels(edges: list[float], as_percent: bool = False) -> list[str]:
    show = (lambda v: f"{v:.1%}" if v < 1 else f"{v:.0%}") if as_percent else fmt
    labels = [f"< {show(edges[0])}"]
    labels += [f"{show(low)} to {show(high)}" for low, high in zip(edges[:-1], edges[1:])]
    labels.append(f">= {show(edges[-1])}")
    return labels


def bin_labels(feature: dict) -> list[str]:
    kind = feature["kind"]
    if kind == "value_bins":
        return (["0"] if feature.get("zero_bin") else []) + interval_labels(feature["edges"])
    if kind == "ratio_bins":
        labels = interval_labels(feature["edges"], as_percent=True)
        labels[-2] = "entire balance"
        labels[-1] = "more than the balance"
        return ["sender had no balance"] + labels
    if kind == "hour_bins":
        width = feature["width"]
        return [f"{start:02d}:00-{start + width - 1:02d}:59" for start in range(0, 24, width)]
    return [category.replace("_", " ").lower() for category in feature["categories"]]


def bin_indices(feature: dict, df: pd.DataFrame) -> np.ndarray:
    """Vectorised twin of app.ml.fraud.bin_index (checked against it after training)."""
    kind = feature["kind"]
    if kind == "value_bins":
        values = df[feature["input"]].to_numpy(dtype="float64")
        index = np.searchsorted(feature["edges"], values, side="right")
        return np.where(values <= 0, 0, index + 1) if feature.get("zero_bin") else index
    if kind == "ratio_bins":
        balance = df["sender_balance"].to_numpy(dtype="float64")
        amount = df["amount"].to_numpy(dtype="float64")
        ratio = amount / np.where(balance > 0, balance, 1.0)
        return np.where(balance <= 0, 0, 1 + np.searchsorted(feature["edges"], ratio, side="right"))
    if kind == "hour_bins":
        return (df["hour"].to_numpy() % 24) // feature["width"]
    return pd.Categorical(df[feature["input"]], categories=feature["categories"]).codes.astype("int64")


def one_hot(features: list[dict], df: pd.DataFrame) -> sparse.csr_matrix:
    rows = np.arange(len(df))
    blocks = [
        sparse.csr_matrix((np.ones(len(df)), (rows, bin_indices(f, df))), shape=(len(df), f["n_bins"]))
        for f in features
    ]
    return sparse.hstack(blocks, format="csr")


def raw_matrix(df: pd.DataFrame) -> np.ndarray:
    """Features for gradient boosting (NaN share when the sender had no balance)."""
    balance = df["sender_balance"].to_numpy(dtype="float64")
    amount = df["amount"].to_numpy(dtype="float64")
    share = np.where(balance > 0, np.minimum(amount / np.where(balance > 0, balance, 1.0), 5.0), np.nan)
    return np.column_stack([np.log10(amount + 1), np.log10(balance + 1), share, df["hour"].to_numpy(), (df["transaction_type"] == "CASH_OUT").to_numpy()])


# ---------------------------------------------------------------- class imbalance

def smote(df_pos: pd.DataFrame, n_new: int, rng: np.random.Generator, k: int = 5) -> pd.DataFrame:
    """SMOTE (Chawla et al., 2002) in log-amount / log-balance / hour / type space."""
    space = np.column_stack(
        [np.log10(df_pos["amount"] + 1), np.log10(df_pos["sender_balance"] + 1), df_pos["hour"], df_pos["transaction_type"] == "CASH_OUT"]
    ).astype("float64")
    scale = space.std(axis=0)
    scale[scale == 0] = 1.0
    neighbours = NearestNeighbors(n_neighbors=min(k + 1, len(space))).fit(space / scale).kneighbors(space / scale, return_distance=False)[:, 1:]
    base = rng.integers(0, len(space), n_new)
    partner = neighbours[base, rng.integers(0, neighbours.shape[1], n_new)]
    new = space[base] + rng.random((n_new, 1)) * (space[partner] - space[base])
    return pd.DataFrame(
        {
            "step": -1,
            "amount": np.maximum(10 ** new[:, 0] - 1, 0.01),
            "sender_balance": np.maximum(10 ** new[:, 1] - 1, 0.0),
            "hour": np.rint(new[:, 2]).astype("int64") % 24,
            "transaction_type": np.where(np.rint(new[:, 3]) >= 1, "CASH_OUT", "TRANSFER"),
            "is_fraud": 1,
        }
    )


def rebalance(strategy: str, train: pd.DataFrame, rng: np.random.Generator):
    """Return (training rows, sample weights, log-odds correction back to the true prior)."""
    y = train["is_fraud"].to_numpy()
    n_pos, n_neg = int(y.sum()), int(len(y) - y.sum())
    if strategy == "none":
        return train, None, 0.0
    if strategy == "class_weight":
        weights = np.where(y == 1, len(y) / (2 * n_pos), len(y) / (2 * n_neg))
        return train, weights, -math.log(n_neg / n_pos)
    if strategy == "undersample":
        keep = min(1.0, n_pos / (RESAMPLED_RATIO * n_neg))
        mask = (y == 1) | (rng.random(len(y)) < keep)
        return train[mask].reset_index(drop=True), None, math.log(keep)
    if strategy == "smote":
        n_new = max(0, int(RESAMPLED_RATIO * n_neg) - n_pos)
        synthetic = smote(train[y == 1], n_new, rng)
        return pd.concat([train, synthetic], ignore_index=True), None, -math.log((n_pos + n_new) / n_pos)
    raise ValueError(strategy)


# ---------------------------------------------------------------- models

def sigmoid(z: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-z))


def fit_scorecard(features, data, weights, shift, valid):
    X, y = one_hot(features, data), data["is_fraud"].to_numpy()
    X_valid, y_valid = one_hot(features, valid), valid["is_fraud"].to_numpy()
    best = None
    for c in C_GRID:
        model = LogisticRegression(C=c, max_iter=3000)
        model.fit(X, y, sample_weight=weights)
        ap = average_precision_score(y_valid, model.decision_function(X_valid))
        if best is None or ap > best[0]:
            best = (ap, c, model)
    _, c, model = best
    return {"model": model, "C": c, "shift": shift, "logit": lambda df, m=model, s=shift: m.decision_function(one_hot(features, df)) + s}


def fit_boosting(data, weights, shift):
    model = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.1, max_leaf_nodes=31, l2_regularization=1.0, early_stopping=False, random_state=SEED)
    model.fit(raw_matrix(data), data["is_fraud"].to_numpy(), sample_weight=weights)
    return {"model": model, "shift": shift, "logit": lambda df, m=model, s=shift: m.decision_function(raw_matrix(df)) + s}


# ---------------------------------------------------------------- evaluation

def threshold_metrics(y: np.ndarray, p: np.ndarray, threshold: float) -> dict:
    flagged = p >= threshold
    tp = int((flagged & (y == 1)).sum())
    fp = int((flagged & (y == 0)).sum())
    fn = int((~flagged & (y == 1)).sum())
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"threshold": float(threshold), "precision": precision, "recall": recall, "f1": f1, "true_positives": tp, "false_positives": fp, "false_negatives": fn, "alerts_per_10k": float(flagged.mean() * 10_000)}


def choose_thresholds(y_valid: np.ndarray, p_valid: np.ndarray) -> dict:
    precision, recall, thresholds = precision_recall_curve(y_valid, p_valid)
    f1 = np.where(precision + recall > 0, 2 * precision * recall / np.maximum(precision + recall, 1e-12), 0)[:-1]
    high = float(thresholds[int(np.argmax(f1))])  # best F1 on validation: opens an alert
    reaching = thresholds[recall[:-1] >= 0.99]  # catch 99% of validation fraud: logged for monitoring
    medium = float(reaching.max()) if len(reaching) else high / 10
    if medium >= high:
        medium = high / 10
    return {"high": high, "medium": medium}


def calibration_table(y: np.ndarray, p: np.ndarray) -> list[dict]:
    edges = [0, 0.001, 0.01, 0.05, 0.1, 0.2, 0.5, 1.000001]
    rows = []
    for low, high in zip(edges[:-1], edges[1:]):
        mask = (p >= low) & (p < high)
        if mask.sum():
            rows.append({"range": f"{low:g}-{min(high, 1):g}", "count": int(mask.sum()), "mean_predicted": float(p[mask].mean()), "observed_rate": float(y[mask].mean())})
    return rows


def evaluate(y: np.ndarray, logit: np.ndarray) -> dict:
    p = sigmoid(logit)
    return {"pr_auc": float(average_precision_score(y, p)), "roc_auc": float(roc_auc_score(y, p)), "brier": float(brier_score_loss(y, p))}


def export_scorecard(features: list[dict], fitted: dict, train: pd.DataFrame) -> tuple[list[dict], float]:
    coef = fitted["model"].coef_.ravel()
    intercept = float(fitted["model"].intercept_[0] + fitted["shift"])
    exported, start, base = [], 0, intercept
    for feature in features:
        weights = coef[start : start + feature["n_bins"]]
        start += feature["n_bins"]
        share = np.bincount(bin_indices(feature, train), minlength=feature["n_bins"]) / len(train)
        expected = float(np.dot(share, weights))
        base += expected
        exported.append({**feature, "weights": [float(w) for w in weights], "expected": expected, "bin_share": [float(s) for s in share]})
    return exported, base


def plots(report_dir: Path, curves: dict, calibration: list[dict], importance: list[dict]) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    for name, (precision, recall, ap) in curves.items():
        ax.plot(recall, precision, label=f"{name} (PR-AUC {ap:.3f})")
    ax.set(xlabel="Recall", ylabel="Precision", title="Test set precision-recall", xlim=(0, 1), ylim=(0, 1.02))
    ax.legend(loc="lower left", fontsize=8)
    fig.tight_layout()
    fig.savefig(report_dir / "precision_recall.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(5, 4.5))
    ax.plot([0, 1], [0, 1], linestyle="--", color="grey", linewidth=1)
    ax.scatter([r["mean_predicted"] for r in calibration], [r["observed_rate"] for r in calibration], s=[max(10, math.log10(r["count"] + 1) * 25) for r in calibration])
    ax.set(xlabel="Mean predicted probability", ylabel="Observed fraud rate", title="Calibration (test set)", xlim=(0, 1), ylim=(0, 1))
    fig.tight_layout()
    fig.savefig(report_dir / "calibration.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 3.2))
    ax.barh([i["label"] for i in importance][::-1], [i["mean_abs_contribution"] for i in importance][::-1], color="#22d3ee")
    ax.set(xlabel="Mean |contribution| to log-odds (test set)", title="What drives the score")
    fig.tight_layout()
    fig.savefig(report_dir / "feature_importance.png", dpi=150)
    plt.close(fig)


def write_model_card(path: Path, spec: dict) -> None:
    test = spec["metrics"]["test"]
    lines = [
        "# Model card: FinGuard fraud scorecard",
        "",
        f"*Version {spec['version']}, trained {spec['trained_at'][:10]}. Generated by `ml/train_fraud_model.py`; do not edit by hand.*",
        "",
        "## What it does",
        "Scores each payment for fraud risk at the moment it is made, using only what FinGuard knows then: the amount, the sender's balance before the payment, the share of that balance being moved, the hour of day and the transaction type. Scores at or above the High threshold open a fraud alert; Medium scores are logged for monitoring.",
        "",
        f"**Algorithm:** {spec['algorithm']}",
        "",
        "Because the model is additive in log-odds, every score splits exactly into one contribution per feature (exact SHAP values for this model class). The API returns these contributions with each score.",
        "",
        "## Data",
        f"{spec['data']['description']} Source: {spec['data']['source']} (licence {spec['data']['license']}). Rows used: {spec['data']['rows']:,} TRANSFER and CASH_OUT transactions, of which {spec['data']['frauds']:,} are fraud ({spec['data']['fraud_rate']:.2%}).",
        "",
        "| Split (by time) | Steps | Rows | Frauds | Fraud rate |",
        "| --- | --- | --- | --- | --- |",
    ]
    for name, info in spec["split"].items():
        lines.append(f"| {name} | {info['steps'][0]}-{info['steps'][1]} | {info['rows']:,} | {info['frauds']:,} | {info['fraud_rate']:.2%} |")
    lines += [
        "",
        "## Model selection",
        f"Two model families, four ways of handling the class imbalance (about 1 fraud in {round(1 / spec['data']['fraud_rate']):,} payments). Settings were chosen on the validation split only; the test split was used once, for the final numbers.",
        "",
        "| Model | Imbalance handling | Validation PR-AUC | Test PR-AUC | Test ROC-AUC |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in spec["comparison"]:
        marker = " (deployed)" if row.get("deployed") else ""
        lines.append(f"| {row['model']}{marker} | {STRATEGY_NAMES[row['strategy']]} | {row['validation']['pr_auc']:.3f} | {row['test']['pr_auc']:.3f} | {row['test']['roc_auc']:.3f} |")
    best_boost = max((r for r in spec["comparison"] if r["model"].startswith("Gradient")), key=lambda r: r["validation"]["pr_auc"])
    deployed = next(r for r in spec["comparison"] if r.get("deployed"))
    gap = best_boost["test"]["pr_auc"] - deployed["test"]["pr_auc"]
    if gap > 0:
        comparison = (f"The best gradient-boosting variant (chosen on validation, {STRATEGY_NAMES[best_boost['strategy']]}) scores {gap:.3f} higher test PR-AUC. "
                      "The scorecard is deployed anyway because each of its alerts can be explained exactly, which matters for analysts reviewing alerts and for model-risk governance.")
    else:
        comparison = (f"The best gradient-boosting variant (chosen on validation, {STRATEGY_NAMES[best_boost['strategy']]}) scores {-gap:.3f} lower test PR-AUC, "
                      "so here the simpler, fully explainable model is also the more accurate one. Class-imbalance handling made little difference to the scorecard.")
    lines += [
        "",
        f"The deployed model is the scorecard with the best validation PR-AUC ({STRATEGY_NAMES[deployed['strategy']]}). {comparison}",
        "",
        "## Test results (deployed model)",
        f"PR-AUC {test['pr_auc']:.3f} · ROC-AUC {test['roc_auc']:.3f} · Brier score {test['brier']:.4f}",
        "",
        "| Level | Probability threshold | Precision | Recall | Alerts per 10,000 payments |",
        "| --- | --- | --- | --- | --- |",
        f"| High (opens an alert) | {spec['thresholds']['high']:.3f} | {test['at_high']['precision']:.1%} | {test['at_high']['recall']:.1%} | {test['at_high']['alerts_per_10k']:.1f} |",
        f"| Medium or above | {spec['thresholds']['medium']:.3f} | {test['at_medium']['precision']:.1%} | {test['at_medium']['recall']:.1%} | {test['at_medium']['alerts_per_10k']:.1f} |",
        "",
        "Rule baselines on the same test set:",
        "",
        "| Rule | Precision | Recall | Same alerts as the model's High level |",
        "| --- | --- | --- | --- |",
    ]
    for rule in spec["baseline"]:
        lines.append(f"| {rule['rule']} | {rule['precision']:.1%} | {rule['recall']:.1%} | {rule['overlap_with_model_high']:.1%} |")
    closest = max(spec["baseline"], key=lambda r: r["overlap_with_model_high"])
    extra = test["at_medium"]["true_positives"] - test["at_high"]["true_positives"]
    lines += [
        "",
        "## What these numbers mean",
        f"On PaySim, the model's High alerts are {closest['overlap_with_model_high']:.1%} the same payments as the one-line rule \"{closest['rule']}\". "
        "The simulated fraud has one dominant pattern, so a single rule already captures it and the near-perfect scores say more about the simulator than about the model.",
        "",
        f"What the model adds here: graded scores rather than a yes/no rule (the Medium band catches {extra:,} more test frauds), an exact explanation of every score, "
        "and a training and evaluation pipeline that can be re-run on a bank's own labelled payments, where single rules perform far worse.",
    ]
    lines += ["", "## What drives the score", "", "| Feature | Mean absolute contribution (log-odds) |", "| --- | --- |"]
    for item in spec["importance"]:
        lines.append(f"| {item['label']} | {item['mean_abs_contribution']:.2f} |")
    lines += ["", "![Precision-recall](report/precision_recall.png) ![Calibration](report/calibration.png)", "", "## Limitations"]
    lines += [f"- {item}" for item in spec["limitations"]]
    path.write_text("\n".join(lines) + "\n")


# ---------------------------------------------------------------- main

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--data", type=Path, help="PaySim CSV or the Kaggle zip")
    source.add_argument("--synthetic", type=int, help="use N rows of random PaySim-shaped data (pipeline test only)")
    parser.add_argument("--model-out", type=Path, default=ROOT / "backend" / "app" / "ml" / "fraud_scorecard.json")
    parser.add_argument("--report-dir", type=Path, default=ROOT / "ml" / "report")
    parser.add_argument("--card-out", type=Path, default=ROOT / "ml" / "MODEL_CARD.md")
    args = parser.parse_args()
    rng = np.random.default_rng(SEED)

    if args.synthetic:
        log(f"Generating {args.synthetic:,} synthetic rows (pipeline test only)")
        df = synthetic_paysim(args.synthetic, rng)
    else:
        log(f"Loading {args.data}")
        df = load_paysim(args.data)
    log(f"{len(df):,} TRANSFER/CASH_OUT rows, {int(df['is_fraud'].sum()):,} frauds")

    train, valid, test, split = time_split(df)
    for name, info in split.items():
        log(f"  {name}: steps {info['steps']}, {info['rows']:,} rows, fraud rate {info['fraud_rate']:.3%}")
    features = build_features(train)
    y_valid, y_test = valid["is_fraud"].to_numpy(), test["is_fraud"].to_numpy()

    results = []
    for strategy in STRATEGIES:
        data, weights, shift = rebalance(strategy, train, np.random.default_rng(SEED))
        log(f"Scorecard / {strategy}: {len(data):,} rows")
        card = fit_scorecard(features, data, weights, shift, valid)
        results.append({"model": "Scorecard (binned logistic regression)", "strategy": strategy, "fitted": card, "C": card["C"]})
        log(f"Gradient boosting / {strategy}")
        results.append({"model": "Gradient boosting (HistGradientBoosting)", "strategy": strategy, "fitted": fit_boosting(data, weights, shift)})
    for row in results:
        row["validation"] = evaluate(y_valid, row["fitted"]["logit"](valid))
        row["test"] = evaluate(y_test, row["fitted"]["logit"](test))
        log(f"  {row['model'][:18]:18s} {row['strategy']:12s} valid PR-AUC {row['validation']['pr_auc']:.3f}  test PR-AUC {row['test']['pr_auc']:.3f}")

    chosen = max((r for r in results if r["model"].startswith("Scorecard")), key=lambda r: r["validation"]["pr_auc"])
    chosen["deployed"] = True
    fitted = chosen["fitted"]
    p_valid, p_test = sigmoid(fitted["logit"](valid)), sigmoid(fitted["logit"](test))
    thresholds = choose_thresholds(y_valid, p_valid)
    exported, base_value = export_scorecard(features, fitted, train)

    # Feature importance: mean |contribution| on the test set.
    importance = []
    for feature in exported:
        contribution = np.asarray(feature["weights"])[bin_indices(feature, test)] - feature["expected"]
        importance.append({"feature": feature["name"], "label": feature["label"], "mean_abs_contribution": float(np.abs(contribution).mean())})
    importance.sort(key=lambda i: i["mean_abs_contribution"], reverse=True)

    share = (test["amount"] / test["sender_balance"].where(test["sender_balance"] > 0)).to_numpy()
    entire = (share >= 0.999) & (share < 1.000001)
    baseline = []
    for name, flagged in [
        ("Moves the entire balance (99.9% to 100%)", entire),
        ("Moves the entire balance and is a TRANSFER", entire & (test["transaction_type"] == "TRANSFER").to_numpy()),
        ("Amount above 10,000 (from the old rules)", (test["amount"] > 10_000).to_numpy()),
    ]:
        tp = int((flagged & (y_test == 1)).sum())
        model_high = p_test >= thresholds["high"]
        overlap = int((flagged & model_high).sum()) / max(int((flagged | model_high).sum()), 1)
        baseline.append({"rule": name, "precision": tp / max(int(flagged.sum()), 1), "recall": tp / max(int(y_test.sum()), 1), "overlap_with_model_high": overlap})

    spec = {
        "name": "FinGuard fraud scorecard",
        "version": "1.0.0" if not args.synthetic else "0.0.0-synthetic",
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "algorithm": f"Logistic regression on binned features (additive scorecard), L2 regularisation C={chosen['C']}, "
        + ("trained on the data as it is (no rebalancing scored best on validation)." if chosen["strategy"] == "none"
           else f"class imbalance handled by {STRATEGY_NAMES[chosen['strategy']]}, with the log-odds corrected back to the true fraud rate."),
        "data": {
            "source": "PaySim, Kaggle ealaxi/paysim1" if not args.synthetic else "synthetic test data",
            "license": "CC BY-SA 4.0",
            "description": "PaySim is a simulated mobile-money transaction log (Lopez-Rojas, Elmir and Axelsson, 2016) built from one month of real transactions of an African mobile-money service.",
            "rows": int(len(df)),
            "frauds": int(df["is_fraud"].sum()),
            "fraud_rate": float(df["is_fraud"].mean()),
        },
        "split": split,
        "features": exported,
        "base_value": base_value,
        "thresholds": thresholds,
        "metrics": {
            "validation": {**evaluate(y_valid, fitted["logit"](valid)), "at_high": threshold_metrics(y_valid, p_valid, thresholds["high"])},
            "test": {
                **evaluate(y_test, fitted["logit"](test)),
                "at_high": threshold_metrics(y_test, p_test, thresholds["high"]),
                "at_medium": threshold_metrics(y_test, p_test, thresholds["medium"]),
                "calibration": calibration_table(y_test, p_test),
            },
        },
        "comparison": [
            {"model": r["model"], "strategy": r["strategy"], "validation": r["validation"], "test": r["test"], **({"deployed": True} if r.get("deployed") else {})}
            for r in results
        ],
        "baseline": baseline,
        "importance": importance,
        "limitations": [
            "The near-perfect test scores reflect how simple PaySim's fraud is: almost every fraud empties an account to the cent, which legitimate PaySim payments rarely do. Real fraud is far harder to separate; expect much lower precision and recall on real data.",
            "Trained on simulated data. PaySim amounts are in the simulator's currency and FinGuard applies them to euros unchanged; the bins should be re-fitted on a bank's own labelled payments before any real use.",
            "PaySim's hour of day is simulation time; FinGuard scores with the UTC hour of the payment.",
            "Fraud in PaySim is dominated by one pattern (an account emptied by a transfer, then cashed out), so the model mostly learns that pattern. It will not recognise fraud that looks different.",
            "Recipient balances were excluded because PaySim leaves them unchanged for many fraud rows, a simulator artefact that a real ledger does not have.",
            "The model sees one payment at a time: no customer history, device, location or velocity features.",
            "Contributions are measured against an average PaySim payment, and almost half of PaySim's senders have a zero balance while many others pay more than their balance. A normal partial payment is therefore unusual in the data, so 'share of balance moved' can raise the score slightly even for a low-risk payment.",
            "The fraud rate in the test period (later in the simulation) is about four times the training rate, so probabilities in the middle range are underestimated; the ranking (PR-AUC) is what was optimised.",
        ],
    }

    # The API scores with the pure-Python module: confirm it reproduces these predictions exactly.
    model = FraudModel(spec)
    sample = test.sample(n=min(2000, len(test)), random_state=SEED)
    expected_logit = fitted["logit"](sample)
    worst = max(
        abs(model.score(row.amount, row.sender_balance, int(row.hour), row.transaction_type).logit - expected)
        for row, expected in zip(sample.itertuples(index=False), expected_logit)
    )
    if worst > 1e-8:
        raise SystemExit(f"Exported scorecard does not reproduce training predictions (max difference {worst})")
    log(f"Export check passed: API scorer matches training predictions (max difference {worst:.1e})")

    args.model_out.parent.mkdir(parents=True, exist_ok=True)
    args.model_out.write_text(json.dumps(spec, indent=1) + "\n")
    args.report_dir.mkdir(parents=True, exist_ok=True)
    (args.report_dir / "metrics.json").write_text(json.dumps({k: spec[k] for k in ("split", "metrics", "comparison", "baseline", "importance", "thresholds")}, indent=1) + "\n")
    curves = {}
    for row in results:
        family = "Scorecard" if row["model"].startswith("Scorecard") else "Gradient boosting"
        best_family = max((r for r in results if r["model"] == row["model"]), key=lambda r: r["validation"]["pr_auc"])
        if row is best_family:
            precision, recall, _ = precision_recall_curve(y_test, sigmoid(row["fitted"]["logit"](test)))
            curves[f"{family}, {STRATEGY_NAMES[row['strategy']]}"] = (precision, recall, row["test"]["pr_auc"])
    plots(args.report_dir, curves, spec["metrics"]["test"]["calibration"], importance)
    write_model_card(args.card_out, spec)
    test_metrics = spec["metrics"]["test"]
    log(f"Deployed: scorecard / {chosen['strategy']} (C={chosen['C']}). Test PR-AUC {test_metrics['pr_auc']:.3f}, "
        f"High: precision {test_metrics['at_high']['precision']:.1%} recall {test_metrics['at_high']['recall']:.1%}")
    log(f"Wrote {args.model_out}, {args.report_dir}, {args.card_out}")


if __name__ == "__main__":
    main()
