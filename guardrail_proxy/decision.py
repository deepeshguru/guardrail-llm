from typing import Dict

from guardrail_proxy.filters.rule_filter import RuleFilter
from guardrail_proxy.filters.semantic_filter import SemanticFilter
from guardrail_proxy.filters.policy_llm import PolicyLLM

rule_layer = RuleFilter("config/regex_patterns.yaml")
semantic_layer = SemanticFilter()
policy_layer = PolicyLLM()  # endpoint via env var

def evaluate_prompt(prompt: str, role: str = "guest") -> Dict:
    verdicts = {
        "rule":     rule_layer.is_blocked(prompt, role=role),
        "semantic": semantic_layer.is_blocked(prompt, role=role),
        "policy":   policy_layer.is_blocked(prompt, role=role),
    }
    allow = all(not v for v in verdicts.values())
    return {"allow": allow, "details": verdicts, "role": role}
