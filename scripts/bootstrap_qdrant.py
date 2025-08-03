#!/usr/bin/env python
"""
Bootstrap the Qdrant collection with jailbreak prompts.

Usage:
    python scripts/bootstrap_qdrant.py          # full 28k
    python scripts/bootstrap_qdrant.py --limit 8000
"""

from __future__ import annotations

import argparse
import sys
from typing import List

from datasets import load_dataset  # pip install datasets
from qdrant_client import QdrantClient
from tqdm import tqdm

from guardrail_proxy.filters.semantic_filter import bootstrap
from guardrail_proxy.config import settings

_DATASET = "HuggingFaceH4/jailbreak_dataset"  # actively maintained fork
_SPLIT = "train"  # single split


def _check_qdrant() -> None:
    try:
        cl = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port, timeout=2)
        cl.get_collections()
    except Exception as exc:  # noqa: BLE001
        print(f"❌  Cannot reach Qdrant at {settings.qdrant_host}:{settings.qdrant_port} – {exc}")
        sys.exit(1)


def _download_prompts(limit: int | None) -> List[str]:
    ds = load_dataset(_DATASET, split=_SPLIT, streaming=True)
    prompts = []
    for row in tqdm(ds, desc="Streaming jailbreak prompts", total=limit or 28_137):
        text = row.get("prompt") or row.get("jailbreak_query") or ""
        if text:
            prompts.append(text)
        if limit and len(prompts) >= limit:
            break
    return prompts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, help="Only ingest first N prompts.")
    args = parser.parse_args()

    _check_qdrant()

    prompts = _download_prompts(args.limit)
    print(f"📦  Vectorising {len(prompts):,} prompts → Qdrant")
    bootstrap(prompts)
    print("✅  Collection refreshed.")


if __name__ == "__main__":
    main()
