
from .filters.filter_rule import is_prompt_injection_rule
from .filters.filter_semantic import is_prompt_injection_semantic

def evaluate_prompt(prompt: str) -> dict:
    verdicts = {
        "rule": is_prompt_injection_rule(prompt),
        "semantic": is_prompt_injection_semantic(prompt),
    }
    allow = not (verdicts["rule"] or verdicts["semantic"])
    return {"allow": allow, "details": verdicts}
