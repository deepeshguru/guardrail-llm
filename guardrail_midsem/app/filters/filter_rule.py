import re
import yaml
import pathlib
from ..config import settings

# ------------------------------------------------------------------
_CFG_FILE = pathlib.Path("config/regex_patterns.yml")

if _CFG_FILE.exists():
    raw_text = _CFG_FILE.read_text(encoding="utf-8")
    patterns_raw = yaml.safe_load(raw_text) or []
else:
    patterns_raw = settings.regex_patterns or []

# compile once
compiled_patterns = [
    re.compile(p, re.I) if "(?i)" not in p else re.compile(p)
    for p in patterns_raw
]

# ------------------------------------------------------------------
def is_prompt_injection_rule(prompt: str) -> bool:
    """Return True if prompt matches any dangerous regex pattern."""
    return any(p.search(prompt) for p in compiled_patterns)

def pattern_match_score(prompt: str) -> float:
    """Binary score: 1.0 if rule layer flags the prompt, else 0.0."""
    return 1.0 if is_prompt_injection_rule(prompt) else 0.0
