"""BA 32.70 — Minimaler OpenAI-Image-Live-Smoke (ein Call, strukturierte Ausgabe, kein Modell-Fallback)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.production_connectors.openai_image_connector import run_openai_image_live_to_png

_DEFAULT_SMOKE_PROMPT = (
    "Minimal editorial test frame: soft neutral gradient, generous negative space, "
    "no readable text, no logos, abstract calm tones for video overlay."
)

_SECRET_SKISH = re.compile(r"\bsk-[a-zA-Z0-9_-]{8,}\b")


def sanitize_openai_image_smoke_warnings(warnings: List[str]) -> List[str]:
    """Keine Secrets in Reports (defensive; Stack sollte ohnehin keine Keys ausgeben)."""
    out: List[str] = []
    for w in warnings:
        s = str(w)
        if _SECRET_SKISH.search(s):
            continue
        if "Bearer " in s:
            continue
        out.append(s)
    return out


def _model_from_warnings(warnings: List[str]) -> str:
    for w in warnings:
        if str(w).startswith("openai_image_model:"):
            return str(w).split(":", 1)[1].strip() or "unknown"
    return "unknown"


def run_openai_image_smoke_v1(
    dest_png: Path,
    *,
    model: Optional[str] = None,
    size: str = "1024x1024",
    prompt: Optional[str] = None,
    timeout_seconds: float = 120.0,
) -> Dict[str, Any]:
    """
    Genau ein Live-Call über ``run_openai_image_live_to_png`` (kein Dry-Run, kein automatischer Modellwechsel).

    Rückgabe: nur sichere Felder — keine API-Response-Bodies, keine Roh-Header.
    """
    text = (prompt or _DEFAULT_SMOKE_PROMPT).strip() or _DEFAULT_SMOKE_PROMPT
    ok, warns, meta = run_openai_image_live_to_png(
        text,
        Path(dest_png),
        size=size,
        model=model,
        timeout_seconds=float(timeout_seconds),
    )
    warns_pub = sanitize_openai_image_smoke_warnings(warns)
    dest = Path(dest_png).resolve()
    out_path = str(dest) if ok and dest.is_file() and dest.stat().st_size > 0 else ""
    mdl = str((meta or {}).get("model") or "").strip() or _model_from_warnings(warns_pub)
    sz = str((meta or {}).get("size") or size).strip()
    bw = int((meta or {}).get("bytes_written") or 0) if ok else 0
    return {
        "ok": bool(ok),
        "provider": "openai_image",
        "model": mdl,
        "size": sz,
        "output_path": out_path,
        "bytes_written": bw,
        "warnings": warns_pub,
        "smoke_version": "ba32_70_v1",
    }
