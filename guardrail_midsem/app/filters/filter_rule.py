import re, yaml, pathlib
from ..config import settings

_CFG_FILE = pathlib.Path("config/regex_patterns.yml")
if _CFG_FILE.exists():
    patterns_raw = yaml.safe_load(_CFG_FILE)
else:
    patterns_raw = settings.regex_patterns          # fallback to built-ins

compiled = [re.compile(p, re.I) if "(?i)" not in p else re.compile(p)
            for p in patterns_raw]

def is_prompt_injection_rule(prompt: str) -> bool:
    """Return True if prompt matches any dangerous regex pattern."""
    for pattern in compiled_patterns:
        if pattern.search(prompt):
            return True
    return False

def pattern_match_score(prompt: str) -> float:
    return 1.0 if is_prompt_injection_rule(prompt) else 0.0