# scripts/download_benign_dataset.py
import json, random, pathlib
from datasets import load_dataset
from tqdm import tqdm

OUT = pathlib.Path("datasets/benign_oasst1_10k.jsonl")
OUT.parent.mkdir(parents=True, exist_ok=True)

ds = load_dataset("openassistant/oasst1", split="train", streaming=False)

def detox_score(row) -> float:
    """Return toxicity score or 0.0 if field missing/None."""
    tox = row.get("detoxify") or {}
    return float(tox.get("toxicity", 0.0))

def is_clean(row) -> bool:
    return (
        row.get("role") == "assistant"
        and not row.get("synthetic", False)
        and not row.get("deleted", False)
        and row.get("review_result") is True
        and row.get("lang") == "en"
        and detox_score(row) < 0.01          # strict filter
        and row.get("text")                  # non-empty text
    )

clean_rows = [r for r in tqdm(ds, desc="filtering") if is_clean(r)]
random.seed(42)
random.shuffle(clean_rows)
clean_rows = clean_rows[:10_000]

with OUT.open("w", encoding="utf-8") as f:
    for r in clean_rows:
        f.write(json.dumps({"text": r["text"]}, ensure_ascii=False) + "\n")

print(f"✅  wrote {len(clean_rows)} benign rows → {OUT}")
