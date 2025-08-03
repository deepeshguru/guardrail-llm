#!/usr/bin/env python
"""
Download a benign English subset (N rows) from OpenAssistant OASST1.

Usage:
    python scripts/download_benign_dataset.py --num 8000 \
          --out datasets/benign_oasst1_8k.jsonl
"""

from __future__ import annotations

import argparse
import json
import random
import pathlib
from typing import List

from datasets import load_dataset
from tqdm import tqdm


def detox_score(row) -> float:
    tox = (row.get("detoxify") or {}).get("toxicity", 0.0)
    return float(tox)


def is_clean(row, role: str) -> bool:
    if role != "both" and row.get("role") != role:
        return False
    return (
        not row.get("synthetic", False)
        and not row.get("deleted", False)
        and row.get("review_result") is True
        and row.get("lang") == "en"
        and detox_score(row) < 0.01
        and row.get("text")
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--num", type=int, default=10_000, help="Number of rows")
    parser.add_argument("--out", type=pathlib.Path, default="datasets/benign_oasst1_10k.jsonl")
    parser.add_argument("--role", choices=["assistant", "user", "both"], default="assistant")
    args = parser.parse_args()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    ds = load_dataset("openassistant/oasst1", split="train", streaming=True)

    chosen: List[str] = []
    bar = tqdm(total=args.num, desc="collecting")
    rand = random.Random(42)

    for row in ds:
        if is_clean(row, args.role):
            chosen.append(row["text"])
            bar.update()
            if len(chosen) >= args.num:
                break
    bar.close()

    rand.shuffle(chosen)

    with args.out.open("w", encoding="utf-8") as f:
        for text in chosen:
            f.write(json.dumps({"text": text}, ensure_ascii=False) + "\n")

    print(f"✅  wrote {len(chosen):,} benign rows → {args.out}")


if __name__ == "__main__":
    main()
