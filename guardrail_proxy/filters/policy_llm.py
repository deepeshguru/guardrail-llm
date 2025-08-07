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

from llama_cpp import Llama

model = Llama.from_pretrained(
	repo_id="TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF",
	filename="tinyllama-1.1b-chat-v1.0.Q2_K.gguf",
)


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
        temperature: float = 0.0,
        timeout: int = 30,
    ) -> None:
        self.temperature = temperature
        self.timeout = timeout

    def _query_model(self, prompt: str) -> str:
        # payload = {
        #     "model": model,
        #     "messages": [
        #         {"role": "system", "content": _default_prompt_header()},
        #         {"role": "user", "content": prompt},
        #     ],
        #     "temperature": self.temperature,
        #     "max_tokens": 1,
        # }
        # try:
        response = model.create_chat_completion(
            messages= [
                {"role": "system", "content": _default_prompt_header()},
                {"role": "user", "content": prompt},
                ],
            max_tokens=1,
            temperature=self.temperature,
            )
        text = response["choices"][0]["message"]["content"].strip().upper()
        return text
        # except Exception as exc:
        #     logger.warning("PolicyLLM fallback to FAIL-CLOSE: %s", exc)
        #     return self.BLOCK

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