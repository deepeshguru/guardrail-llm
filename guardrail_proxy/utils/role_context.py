"""
User-role helpers:

1. `get_user_role(request)`      → "guest" | "employee" | "admin" (validated)
2. `role_cfg(role)`              → dict with thresholds / flags
3. `load_role_config()`          → full roles.yaml as dict (cached)
"""

from __future__ import annotations

import logging
import yaml
from functools import lru_cache
from importlib.resources import files
from typing import Any, Dict

from fastapi import Request

logger = logging.getLogger(__name__)

DEFAULT_ROLE = "guest"
ROLE_HEADER = "x-user-role"
_ROLES_YAML = files("guardrail_proxy").joinpath("config/roles.yaml")


@lru_cache(maxsize=1)
def load_role_config() -> Dict[str, Dict[str, Any]]:
    try:
        data = yaml.safe_load(_ROLES_YAML.read_text(encoding="utf-8")) or {}
        if DEFAULT_ROLE not in data:
            data[DEFAULT_ROLE] = {}  # ensure key exists
        return data
    except FileNotFoundError:
        logger.warning("roles.yaml not found, using empty config")
        return {DEFAULT_ROLE: {}}


def _jwt_role(token: str | None) -> str | None:  # pragma: no cover
    """Return role from JWT without verifying signature (best-effort)."""
    if not token:
        return None
    try:
        import jwt  # optional dependency
        decoded = jwt.decode(token, options={"verify_signature": False})
        role = str(decoded.get("role", "")).lower()
        return role or None
    except Exception:  # noqa: BLE001
        logger.debug("Could not parse JWT role", exc_info=True)
        return None


def get_user_role(request: Request) -> str:
    """Extract validated role; falls back to DEFAULT_ROLE."""
    cfg = load_role_config()

    # 1️⃣ explicit header
    role = request.headers.get(ROLE_HEADER)
    if role and role.lower() in cfg:
        return role.lower()

    # 2️⃣ JWT
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        jwt_role = _jwt_role(auth.split(" ", 1)[1])
        if jwt_role in cfg:
            return jwt_role

    # 3️⃣ default
    return DEFAULT_ROLE


def role_cfg(role: str) -> Dict[str, Any]:
    """Return the dict for the given role (never empty)."""
    cfg = load_role_config()
    return cfg.get(role, cfg[DEFAULT_ROLE])
