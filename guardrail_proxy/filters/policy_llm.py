# guardrail_proxy/layers/policy_llm.py
"""
Layer C: Policy-LLM filter

Uses TinyLlama-1.1B-Chat (4-bit AWQ) served by vLLM (or any OpenAI-compatible
endpoint) to classify a prompt as SAFE / UNSAFE / ESCALATE.

Return True  ➜  block request
Return False ➜  allow request
"""

from __future__ import annotations

import httpx
import logging
from functools import lru_cache
from typing import Final

logger = logging.getLogger(__name__)

from importlib.resources import files
import yaml
from pathlib import Path

@lru_cache(maxsize=1)
def _default_prompt_header() -> str:
    yaml_path = Path(__file__).resolve().parents[2] / "config" / "policy.yaml"
    yaml_text = yaml_path.read_text()
    data = yaml.safe_load(yaml_text)
    return data["system_prompt"]


class PolicyLLM:
    """
    Thin blocking wrapper around a small alignment-policy model.
    """

    SAFE: Final[str] = "SAFE"
    BLOCK: Final[str] = "UNSAFE"
    ESCALATE: Final[str] = "ESCALATE"

    def __init__(
        self,
        endpoint: str = "http://127.0.0.1:8080/v1/chat/completions",
        model: str = "tinyllama-policy",
        temperature: float = 0.0,
        timeout: int = 30,
    ) -> None:
        self.endpoint = endpoint
        self.model = model
        self.temperature = temperature
        self.timeout = timeout

    def _query_model(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": _default_prompt_header()},
                {"role": "user", "content": prompt},
            ],
            "temperature": self.temperature,
            "max_tokens": 1,
        }
        # try:
        r = httpx.post(self.endpoint, json=payload, timeout=self.timeout)
        r.raise_for_status()
        text = r.json()["choices"][0]["message"]["content"].strip().upper()
        #     return text
        # except Exception as exc:  # noqa: BLE001
        #     logger.warning("Policy-LLM fallback to FAIL-CLOSE: %s", exc)
        #     return self.BLOCK  # fail-close

    # --------------------------------------------------------------------- #
    # public API                                                             #
    # --------------------------------------------------------------------- #

    def is_blocked(self, text: str, role: str = "guest") -> bool:
        """
        Query the policy model and interpret output token.

        Admins may receive 'ESCALATE' instead of outright block – handled
        by URCF in main proxy.
        """
        label = self._query_model(text)
        return label == self.BLOCK

    def get_label(self, text: str) -> str:
        return self._query_model(text)