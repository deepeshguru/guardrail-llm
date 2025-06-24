"""
Audit logger for Guardrail Proxy (mid-sem).

• Writes one JSON-line per decision to `logs/audit.jsonl`
• Masks obvious PII (emails, phone numbers, 16-digit numbers, IPv4)
"""

from __future__ import annotations
import json, re, datetime, pathlib
from typing import Any, Dict

_LOG_PATH = pathlib.Path("logs/audit.jsonl")
_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

# ---------- simple PII redaction regexes ----------
_PATTERNS = [
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", re.I),   # email
    re.compile(r"\b\d{10,16}\b"),                                           # long numbers
    re.compile(r"\b\d{3}[-\s]\d{2}[-\s]\d{4}\b"),                           # SSN style
    re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),                             # IPv4
    re.compile(r"\+?\d{1,4}[-\s]\d{6,}", re.I),                             # phone
]

def _mask(text: str) -> str:
    for pat in _PATTERNS:
        text = pat.sub("[REDACTED]", text)
    return text

# ---------------------------------------------------

def write_audit(record: Dict[str, Any]) -> None:
    """
    Record structure:
        {
            "prompt": str,
            "response": str,
            "verdict": {"rule_score": ..., "semantic_score": ..., "blocked": bool}
        }
    """
    safe = {
        "timestamp": datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z",
        **record,
    }
    # mask PII in prompt / response
    safe["prompt"]   = _mask(safe.get("prompt", ""))
    safe["response"] = _mask(safe.get("response", ""))

    with _LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(safe, ensure_ascii=False) + "\n")
