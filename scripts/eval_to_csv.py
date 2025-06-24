import csv, json, pathlib, time
from tqdm import tqdm
from datasets import load_dataset, Dataset
from guardrail_midsem.app.filters.filter_rule import pattern_match_score
from guardrail_midsem.app.filters.filter_semantic import cosine_similarity_score

CSV_OUT = pathlib.Path("results/layer_AB_scores.csv")
CSV_OUT.parent.mkdir(parents=True, exist_ok=True)

def extract_attack_text(row: dict) -> str | None:
    """
    Return the first non-empty text field in `row`.
    Works for both RedTeam_2K and future schema changes.
    """
    CANDIDATE_KEYS = (
        "question",          # ← current RedTeam_2K
        "redteam_query",
        "jailbreak_query",
        "prompt", "text", "query",
    )
    for key in CANDIDATE_KEYS:
        text = row.get(key)
        if isinstance(text, str) and text.strip():
            return text
    # Fallback: grab any str value that looks like natural language
    for v in row.values():
        if isinstance(v, str) and sum(c.isalpha() for c in v) > 10:
            return v
    return None

def load_attack() -> list[dict]:
    rt = load_dataset(
        "JailbreakV-28K/JailBreakV-28k",
        "RedTeam_2K",
        split="RedTeam_2K",
        streaming=False,
    )
    attacks = [
        {"text": extract_attack_text(row), "label": 1}
        for row in rt
        if extract_attack_text(row) is not None
    ]
    assert attacks, "❗ No attack prompts extracted—check dataset schema."
    return attacks

def load_benign():
    path = pathlib.Path("datasets/benign_oasst1_10k.jsonl")
    with path.open(encoding="utf-8") as f:
        rows = (json.loads(line) for line in f)
        return [{"text": r.get("text") or r.get("prompt"), "label": 0}
                for r in rows if (r.get("text") or r.get("prompt"))]

def main():
    samples = load_attack() + load_benign()
    with CSV_OUT.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "score_rule", "score_sem", "score_AB",
            "label", "rule_time_ms", "sem_time_ms"
        ])
        for row in tqdm(samples, desc="Evaluating"):
            prompt, label = row["text"], row["label"]
            t0 = time.time()
            s_rule = pattern_match_score(prompt)
            t1 = time.time()
            s_sem  = cosine_similarity_score(prompt)
            t2 = time.time()

            score_ab = max(s_rule, s_sem)        # ← give it a clear name

            rule_ms = (t1 - t0) * 1000
            sem_ms  = (t2 - t1) * 1000

            writer.writerow(
                [s_rule, s_sem, score_ab, label, rule_ms, sem_ms]
            )
    print("✅  Saved ROC/PR input to", CSV_OUT)
if __name__ == "__main__":
    main()
