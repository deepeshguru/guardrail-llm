from datasets import load_dataset
from guardrail_midsem.app.filters.filter_semantic import bootstrap

def main():
    jb = load_dataset(
        "JailbreakV-28K/JailBreakV-28k",  # Dataset name
        "JailBreakV_28K",                 # Config name
        split="JailBreakV_28K",           # Use a valid split from the dataset
        streaming=False
    )
    prompts = [row["jailbreak_query"] for row in jb if row["jailbreak_query"]]
    print(f"Vectorising {len(prompts):,} attack prompts …")
    bootstrap(prompts)
    print("✅  Qdrant collection refreshed with JailBreakV-28K.")
if __name__ == "__main__":
    main()
