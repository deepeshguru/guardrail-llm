#!/usr/bin/env python
"""
Plot ROC curves for one or more score columns in your results CSV.

Usage:
    python scripts/plot_roc.py \
        --csv results/layer_ABC_scores.csv \
        --cols score_rule score_AB score_ABC
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def roc_from_scores(scores: np.ndarray, labels: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    order = np.argsort(-scores)
    labels_sorted = labels[order]
    tp = fp = 0
    pos_total = labels.sum()
    neg_total = len(labels) - pos_total
    tpr, fpr = [], []
    for lab in labels_sorted:
        if lab == 1:
            tp += 1
        else:
            fp += 1
        tpr.append(tp / pos_total if pos_total else 0)
        fpr.append(fp / neg_total if neg_total else 0)
    return np.array(fpr), np.array(tpr)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, default="results/layer_ABC_scores.csv")
    parser.add_argument("--cols", nargs="+", default=["score_rule", "score_AB", "score_ABC"])
    parser.add_argument("--out", type=Path, default="figures/roc_curve.png")
    args = parser.parse_args()

    df = pd.read_csv(args.csv)
    labels = df["label"].to_numpy()

    plt.figure()
    for col in args.cols:
        if col not in df.columns:
            print(f"⚠️  Column '{col}' not found in CSV – skipping.")
            continue
        fpr, tpr = roc_from_scores(df[col].to_numpy(), labels)
        plt.plot(fpr, tpr, label=col, linewidth=2)

    plt.plot([0, 1], [0, 1], linestyle="--", linewidth=1)  # chance
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC curves – Guardrail layers")
    plt.legend()
    plt.tight_layout()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(args.out, dpi=300)
    print(f"✅  ROC plot saved → {args.out}")


if __name__ == "__main__":
    main()
