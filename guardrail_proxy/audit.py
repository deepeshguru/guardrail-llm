"""
Append one masked JSON line per decision to `logs/audit.jsonl`
(override path via AUDIT_LOG_PATH env var).

Thread-safe, UTC-timestamped.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import pathlib
import re
import sys
from typing import Any, Dict
from guardrail_proxy.config import settings
 #  Path setup
 # ------------------------------------------------------------------ #
_LOG_PATH = pathlib.Path(os.getenv("AUDIT_LOG_PATH", settings.audit_log_path))

_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------ #
#  PII patterns (compiled once)
# ------------------------------------------------------------------ #
_PATS = [
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", re.I),  # email
    re.compile(r"\b\d{16}\b"),                                            # 16-digit (card)
    re.compile(r"\b\d{10,15}\b"),                                         # phone / long #
    re.compile(r"\b\d{3}[-\s]\d{2}[-\s]\d{4}\b"),                         # SSN
    re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),                           # IPv4
]

def _mask(txt: str) -> str:
    for pat in _PATS:
        txt = pat.sub("[REDACTED]", txt)
    return txt

# ------------------------------------------------------------------ #
#  Atomic append helper (Unix & Windows)
# ------------------------------------------------------------------ #
def _atomic_append(path: pathlib.Path, text: str) -> None:
    flags = os.O_APPEND | os.O_CREAT | os.O_WRONLY
    # 0o644 rw-r--r-- (POSIX); ignored on Windows
    fd = os.open(path, flags, 0o644)
    try:
        os.write(fd, text.encode("utf-8"))
    finally:
        os.close(fd)

# ------------------------------------------------------------------ #
#  Public API
# ------------------------------------------------------------------ #
def write_audit(record: Dict[str, Any]) -> None:
    """
    Append *record* to audit log after masking PII.

    Expected keys:
        prompt   : user prompt
        response : upstream response (may be "")
        verdict  : rule / semantic / policy details
    """
    safe: Dict[str, Any] = {
        "timestamp": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        **record,
    }
    safe["prompt"]   = _mask(safe.get("prompt", ""))
    safe["response"] = _mask(safe.get("response", ""))

    _atomic_append(_LOG_PATH, json.dumps(safe, ensure_ascii=False) + "\n")


# Backward-compat alias
log = write_audit

# ------------------------------------------------------------------ #
#  CLI helper: `python -m guardrail_proxy.audit latest`
# ------------------------------------------------------------------ #
if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "latest":
    try:
        print(list(_LOG_PATH.open(encoding="utf-8"))[-5:])
    except FileNotFoundError:
        print("No audit log yet.")
