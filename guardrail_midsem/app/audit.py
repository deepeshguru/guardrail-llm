"""
Audit logger for Guardrail-LLM.

• Appends one JSON-line per decision to `logs/audit.jsonl`
• Masks common PII (e-mail, phone, credit-card-like numbers, IPv4, SSN)
"""

from __future__ import annotations
import json, re, datetime, pathlib
from typing import Any, Dict

# ------------------------------------------------------------------
# Configurable output path (fallback to logs/audit.jsonl)
# ------------------------------------------------------------------
try:
    from .config import settings
    _LOG_PATH = pathlib.Path(settings.audit_log_path)
except Exception:  # settings may not be loaded yet
    _LOG_PATH = pathlib.Path("logs/audit.jsonl")

_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------
# One-time-compiled PII patterns
# ------------------------------------------------------------------
_PATS = [
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", re.I),  # email
    re.compile(r"\b\d{16}\b"),                                            # 16-digit (card-like)
    re.compile(r"\b\d{10,15}\b"),                                         # long numbers / phones
    re.compile(r"\b\d{3}[-\s]\d{2}[-\s]\d{4}\b"),                         # SSN
    re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),                           # IPv4
]

def _mask(txt: str) -> str:
    for pat in _PATS:
        txt = pat.sub("[REDACTED]", txt)
    return txt

# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------
def write_audit(record: Dict[str, Any]) -> None:
    """
    Append *record* to the audit log after masking PII.

    Expected keys:
        prompt   : original user prompt
        response : upstream LLM response (may be empty if blocked)
        verdict  : dict with rule/semantic scores & allow/blocked flag
    """
    safe = {
        "timestamp": datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z",
        **record,
    }
    safe["prompt"]   = _mask(safe.get("prompt", ""))
    safe["response"] = _mask(safe.get("response", ""))

    with _LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(safe, ensure_ascii=False) + "\n")

# Backward-compat alias
log = write_audit
