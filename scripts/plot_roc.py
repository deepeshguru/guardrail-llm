import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

# ----------------------------------------------------------------------------------
# INPUT – replace with the CSV you log after running 20 k prompts.
# CSV columns: score (float 0 – 1), label (1 = jailbreak, 0 = benign)
csv_path = Path("results/layer_AB_scores.csv")
df = pd.read_csv(csv_path)           # ← real data
print(df["label"].value_counts())
print(df.dtypes)

scores = df["score_AB"].to_numpy()
labels = df["label"].to_numpy()
# ----------------------------------------------------------------------------------

# ROC in pure NumPy (keeps dependency footprint tiny)
order = np.argsort(-scores)
labels_sorted = labels[order]
tpr, fpr = [], []
tp = fp = 0
pos_total = labels.sum()
neg_total = len(labels) - pos_total
for lab in labels_sorted:
    if lab == 1:
        tp += 1
    else:
        fp += 1
    tpr.append(tp / pos_total)
    fpr.append(fp / neg_total)

plt.figure()
plt.plot(fpr, tpr, linewidth=2)
plt.plot([0, 1], [0, 1], linestyle="--")          # chance
plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.title("ROC curve – Layer A + B")
plt.tight_layout()
plt.savefig("figures/roc_curve.png", dpi=300)
