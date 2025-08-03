#!/usr/bin/env python
"""
Calculate precision / recall / latency for Guardrail layers.

CSV is expected to contain:
    label              0 | 1
    score_rule         float   (binary 0/1 or prob)
    score_AB           float   (after semantic filter)
    score_ABC          float   (after policy LLM)

    rule_time_ms       float
    sem_time_ms        float
    policy_time_ms     float
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

DEFAULT_CSV = "results/layer_ABC_scores.csv"


def _eval(
    df: pd.DataFrame,
    score_col: str,
    latency_cols: List[str],
    name: str,
    thr: float = 0.5,
) -> None:
    labels = df["label"]
    preds = (df[score_col] >= thr).astype(int)

    tn, fp, fn, tp = confusion_matrix(labels, preds).ravel()
    precision = precision_score(labels, preds, zero_division=0)
    recall = recall_score(labels, preds, zero_division=0)
    f1 = f1_score(labels, preds, zero_division=0)
    acc = accuracy_score(labels, preds)
    fp_rate = fp / (fp + tn) if (fp + tn) else 0
    try:
        auroc = roc_auc_score(labels, df[score_col])
        auprc = average_precision_score(labels, df[score_col])
    except ValueError:
        auroc = auprc = float("nan")

    latency = df[latency_cols].sum(axis=1)
    print(f"\n📊  {name}")
    print(f"Precision:    {precision:.4f}")
    print(f"Recall:       {recall:.4f}")
    print(f"F1 Score:     {f1:.4f}")
    print(f"Accuracy:     {acc:.4f}")
    print(f"FP Rate:      {fp_rate:.4f}")
    print(f"AUROC:        {auroc:.4f}")
    print(f"AUPRC:        {auprc:.4f}")
    print(f"Median ms:    {latency.median():.2f}")
    print(f"P95 ms:       {latency.quantile(0.95):.2f}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default=DEFAULT_CSV, help="Path to scores CSV")
    args = parser.parse_args()

    path = Path(args.csv)
    if not path.exists():
        raise SystemExit(f"CSV not found: {path}")

    df = pd.read_csv(path)

    # Ensure missing latency columns default to 0
    for col in ("rule_time_ms", "sem_time_ms", "policy_time_ms"):
        df[col] = df.get(col, 0.0)

    _eval(df, "score_rule", ["rule_time_ms"], "Layer A (Rule)")
    _eval(df, "score_AB", ["rule_time_ms", "sem_time_ms"], "Layer A+B (Rule+Semantic)")
    _eval(
        df,
        "score_ABC",
        ["rule_time_ms", "sem_time_ms", "policy_time_ms"],
        "Layer A+B+C (Full stack)",
    )


if __name__ == "__main__":
    main()
