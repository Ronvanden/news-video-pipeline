"""BA 32.40 — OpenAI Image (Singular): Canonical Spike-Wrapping über den bestehenden Images-Adapter."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

from app.production_connectors.openai_images_adapter import (
    OpenAIImageGenerationResult,
    generate_openai_image_from_prompt,
)

_RESPONSE_INVALID_CODES = frozenset(
    {
        "openai_images_response_not_json",
        "openai_images_response_missing_data",
        "openai_images_missing_b64_json",
    }
)


def _safe_generation_fail_tag(error_code: str) -> str:
    ec = (error_code or "error").strip()
    if ec.startswith("openai_images_"):
        ec = ec[len("openai_images_") :]
    ec = ec.replace(":", "_")
    return ec[:96] if ec else "error"


def _strip_prompt_from_adapter_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    out = {k: v for k, v in d.items() if k != "prompt_used"}
    return out


def run_openai_image_live_to_png(
    visual_prompt_effective: str,
    dest_png: Path,
    *,
    size: str = "1024x1024",
    model: str | None = None,
    timeout_seconds: float = 120.0,
) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    Live-Generierung ohne Dry-Run. Rückgabe: (ok, warnings, result_meta_public)
    — ``result_meta_public`` gefüllt nur bei Erfolg (ohne vollständigen Prompt).
    """
    res = generate_openai_image_from_prompt(
        visual_prompt_effective,
        dest_png,
        dry_run=False,
        size=size,
        model=model,
        timeout_seconds=float(timeout_seconds),
    )
    ok, warns = _finalize_openai_image_live_result(res)
    meta: Dict[str, Any] = openai_adapter_result_public_dict(res) if res.ok else {}
    return ok, warns, meta


def _finalize_openai_image_live_result(res: OpenAIImageGenerationResult) -> Tuple[bool, List[str]]:
    warns: List[str] = []
    mdl = str(res.model or "").strip()
    warns.append(f"openai_image_model:{mdl or 'unknown'}")
    warns.append("openai_image_provider:openai_image")
    warns.append("openai_image_transport:images_api")
    sz = str(res.size or "").strip()
    if sz:
        warns.append(f"openai_image_size:{sz}")

    if res.ok:
        # Adapter-Warnungen (z. B. defaulted prompt) ohne Roh-Payload
        for w in list(res.warnings or []):
            if str(w).strip():
                warns.append(str(w))
        return True, warns

    ec = str(res.error_code or "").strip()
    if ec == "openai_api_key_missing":
        warns.append("openai_image_key_missing_fallback_placeholder")
        return False, warns

    if ec in _RESPONSE_INVALID_CODES:
        warns.append("openai_image_response_invalid")

    tag = _safe_generation_fail_tag(ec)
    warns.append(f"openai_image_generation_failed:{tag}")
    for w in list(res.warnings or []):
        s = str(w).strip()
        if s:
            warns.append(s)
    return False, warns


def openai_adapter_result_public_dict(res: OpenAIImageGenerationResult) -> Dict[str, Any]:
    """Manifest-sicheres dict ohne vollständigen Prompt-Text."""
    return _strip_prompt_from_adapter_dict(res.to_dict())
