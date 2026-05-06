"""Lädt JSON-Templates aus app/templates/prompt_planning/."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List


def _templates_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "templates" / "prompt_planning"


@lru_cache(maxsize=1)
def list_prompt_template_keys() -> List[str]:
    d = _templates_dir()
    if not d.is_dir():
        return []
    return sorted(p.stem for p in d.glob("*.json"))


@lru_cache(maxsize=16)
def load_prompt_template(template_key: str) -> Dict[str, Any]:
    path = _templates_dir() / f"{template_key}.json"
    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)
    if data.get("template_key") != template_key:
        raise ValueError(
            f"template_key mismatch in {path.name}: expected {template_key!r}, "
            f"got {data.get('template_key')!r}"
        )
    return data


def load_all_prompt_templates() -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for key in list_prompt_template_keys():
        out[key] = load_prompt_template(key)
    return out
