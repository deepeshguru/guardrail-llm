import re, yaml
from importlib.resources import files
from typing import Dict, List
import pathlib
_CFG_PATH = files("guardrail_proxy").joinpath("config/regex_patterns.yaml")


class RuleFilter:
    def __init__(self, cfg_file: str | None = None):
        yaml_text = (
            pathlib.Path(cfg_file).read_text(encoding="utf-8")
            if cfg_file
            else _CFG_PATH.read_text(encoding="utf-8")
        )
        raw: Dict = yaml.safe_load(yaml_text) or {}
        # raw can be dict(role → patterns) or list
        self.patterns: Dict[str, List[re.Pattern]] = {}
        if isinstance(raw, dict):
            for role, plist in raw.items():
                self.patterns[role] = [re.compile(p, re.I) for p in plist]
        else:  # list
            self.patterns["default"] = [re.compile(p, re.I) for p in raw]

    # ---------------------------------------------------------
    def is_blocked(self, text: str, role: str = "guest") -> bool:
        pats = (
            self.patterns.get(role, [])
            + self.patterns.get("default", [])
        )
        return any(p.search(text) for p in pats)
