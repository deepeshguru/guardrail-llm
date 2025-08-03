# guardrail_proxy/config.py
"""
Central runtime settings.  Values can be overridden via environment variables
(e.g., `export QDRANT_HOST=my-qdrant`).

Only settings that multiple modules need should live here; everything else
goes into the respective YAML file.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ------------ Vector DB (semantic layer) -----------------
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    base_semantic_threshold: float = 0.42  # role deltas are added/removed

    # ------------ Service endpoints --------------------------
    policy_llm_endpoint: str = "http://127.0.0.1:8080/completion"
    llm_backend_url: str = "http://localhost:1234/v1/chat/completions"

    # ------------ Audit log ----------------------------------
    audit_log_path: str = "logs/audit.jsonl"

    model_config = SettingsConfigDict(env_prefix="", env_file=".env", extra="ignore")


settings = Settings()
