#!/usr/bin/env python
"""
Evaluate all three guardrail layers and dump CSV for calc_metrics.py.

CLI flags:
    --attacks N     limit attack rows
    --benign N      limit benign rows
    --role fixed_role|auto
    --out  path.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import time
from pathlib import Path
from typing import Dict, List

from datasets import load_dataset
from tqdm import tqdm

from guardrail_proxy.filters.rule_filter import RuleFilter
from guardrail_proxy.filters.semantic_filter import SemanticFilter
from guardrail_proxy.filters.policy_llm import PolicyLLM
from guardrail_proxy.utils.role_context import role_cfg

# ----------------------------------------------------------------------------------
DEFAULT_CSV = Path("results/layer_ABC_scores.csv")
DEFAULT_CSV.parent.mkdir(parents=True, exist_ok=True)

rule_layer = RuleFilter("config/regex_patterns.yaml")
semantic_layer = SemanticFilter("http://localhost:6333")
policy_layer = PolicyLLM()  # endpoint via env var

# ----------------------------------------------------------------------------------
def extract_attack_text(row: Dict) -> str | None:
    for key in (
        "question",
        "redteam_query",
        "jailbreak_query",
        "prompt",
        "text",
        "query",
    ):
        txt = row.get(key)
        if isinstance(txt, str) and txt.strip():
            return txt
    return None


def load_attacks(limit: int | None) -> List[Dict]:
    ds = load_dataset("HuggingFaceH4/jailbreak_dataset", split="train", streaming=True)
    rows = []
    for row in ds:
        txt = extract_attack_text(row)
        if txt:
            rows.append({"text": txt, "label": 1})
            if limit and len(rows) >= limit:
                break
    return rows


def load_benign(limit: int | None) -> List[Dict]:
    path = Path("datasets/benign_oasst1_10k.jsonl")
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            if limit and len(rows) >= limit:
                break
            txt = json.loads(line).get("text")
            if txt:
                rows.append({"text": txt, "label": 0})
    return rows


def random_role() -> str:
    r = random.random()
    if r < 0.75:
        return "guest"
    if r < 0.95:
        return "employee"
    return "admin"


# ----------------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--attacks", type=int, help="limit attack rows")
    parser.add_argument("--benign", type=int, help="limit benign rows")
    parser.add_argument("--role", default="auto", help="'guest'|'employee'|'admin'|'auto'")
    parser.add_argument("--out", type=Path, default=DEFAULT_CSV)
    args = parser.parse_args()

    samples = load_attacks(args.attacks) + load_benign(args.benign)
    random.shuffle(samples)

    with args.out.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "score_rule",
                "score_sem",
                "score_policy",
                "score_ABC",
                "label",
                "role",
                "rule_time_ms",
                "sem_time_ms",
                "policy_time_ms",
            ]
        )

        for row in tqdm(samples, desc="Evaluating"):
            prompt, label = row["text"], row["label"]

            role = args.role if args.role != "auto" else random_role()

            # --- Rule layer
            t0 = time.time()
            s_rule = 1.0 if rule_layer.is_blocked(prompt, role) else 0.0
            t1 = time.time()

            # --- Semantic layer
            s_sem = 1.0 if semantic_layer.is_blocked(prompt, role) else 0.0
            t2 = time.time()

            # --- Policy layer
            s_pol = 1.0 if policy_layer.is_blocked(prompt, role) else 0.0
            t3 = time.time()

            score_abc = max(s_rule, s_sem, s_pol)

            writer.writerow(
                [
                    s_rule,
                    s_sem,
                    s_pol,
                    score_abc,
                    label,
                    role,
                    (t1 - t0) * 1000,
                    (t2 - t1) * 1000,
                    (t3 - t2) * 1000,
                ]
            )

    print(f"✅  Saved scores → {args.out}")


if __name__ == "__main__":
    main()
