import pandas as pd
from sklearn.metrics import (
    confusion_matrix, precision_score, recall_score, f1_score,
    accuracy_score, roc_auc_score, average_precision_score
)

CSV_PATH = "results/layer_AB_scores.csv"

def evaluate_layer(df, score_col, name):
    preds = (df[score_col] >= 0.5).astype(int)
    labels = df["label"]

    tn, fp, fn, tp = confusion_matrix(labels, preds).ravel()

    precision = precision_score(labels, preds)
    recall = recall_score(labels, preds)
    f1 = f1_score(labels, preds)
    acc = accuracy_score(labels, preds)
    fp_rate = fp / (fp + tn) if (fp + tn) > 0 else 0
    try:
        auroc = roc_auc_score(labels, df[score_col])
        auprc = average_precision_score(labels, df[score_col])
    except ValueError:
        auroc = auprc = float('nan')

    # Latency: use only available time fields
    if name == "Layer A":
        latency = df["rule_time_ms"]
    else:
        latency = df["rule_time_ms"] + df["sem_time_ms"]

    print(f"\n📊 {name}")
    print(f"Precision:    {precision:.4f}")
    print(f"Recall:       {recall:.4f}")
    print(f"F1 Score:     {f1:.4f}")
    print(f"Accuracy:     {acc:.4f}")
    print(f"FP Rate:      {fp_rate:.4f}")
    print(f"AUROC:        {auroc:.4f}")
    print(f"AUPRC:        {auprc:.4f}")
    print(f"Median ms:    {latency.median():.2f}")
    print(f"P95 ms:       {latency.quantile(0.95):.2f}")

def main():
    df = pd.read_csv(CSV_PATH)

    # Ensure timing columns exist
    if "rule_time_ms" not in df.columns:
        df["rule_time_ms"] = 0.0
    if "sem_time_ms" not in df.columns:
        df["sem_time_ms"] = 0.0

    LAYER_A_COL = "score_rule"
    LAYER_AB_COL = "score_AB"

    evaluate_layer(df, LAYER_A_COL,  "Layer A")
    evaluate_layer(df, LAYER_AB_COL, "Layer A + B")

if __name__ == "__main__":
    main()

