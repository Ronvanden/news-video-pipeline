"""BA 26.5 — OpenAI Images Adapter V1 (dry-run + optional live, isolated).

- Kein Secret im Code; API-Key nur aus Settings/ENV.
- Tests dürfen ohne Key laufen (dry-run).
- Live-Fehler sind kontrolliert (ok=false + error_code, kein Crash).
"""

from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.config import settings


@dataclass(frozen=True)
class OpenAIImageGenerationResult:
    ok: bool
    provider: str
    dry_run: bool
    model: str
    size: str
    prompt_used: str
    output_path: str
    bytes_written: int
    warnings: List[str]
    error_code: str
    error_message: str

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # ensure JSON-friendly
        d["warnings"] = list(self.warnings or [])
        return d


_DEFAULT_API_BASE = "https://api.openai.com"


def _openai_image_http_warning(status: int) -> str:
    """Sichere Warn-Codes ohne Response-Body (BA 32.69)."""
    s = int(status)
    if s == 400:
        return "openai_image_http_400"
    if s == 401:
        return "openai_image_http_401"
    if s == 403:
        return "openai_image_http_403"
    if s == 429:
        return "openai_image_http_429"
    if 500 <= s <= 599:
        return "openai_image_http_5xx"
    return f"openai_image_http_error:{s}"


def _openai_images_error_code_for_http(status: int) -> str:
    s = int(status)
    if s in (400, 401, 403, 429):
        return f"openai_images_http_{s}"
    if 500 <= s <= 599:
        return "openai_images_http_5xx"
    return "openai_images_http_error"


def _effective_openai_api_key() -> str:
    # Prefer environment OPENAI_API_KEY; fallback to settings.openai_api_key (env_file handled by pydantic_settings).
    k = (os.environ.get("OPENAI_API_KEY") or "").strip()
    if k:
        return k
    return (getattr(settings, "openai_api_key", "") or "").strip()


def _write_clean_placeholder_png(path: Path, *, size: str) -> int:
    # Clean background, no readable text. Uses PIL (already project dependency via asset runner tests).
    try:
        from PIL import Image
    except Exception:
        path.write_bytes(b"\x89PNG\r\n\x1a\n")
        return 8

    w, h = 1024, 1024
    if isinstance(size, str) and "x" in size:
        try:
            a, b = size.lower().split("x", 1)
            w = max(32, min(2048, int(a)))
            h = max(32, min(2048, int(b)))
        except Exception:
            w, h = 1024, 1024

    im = Image.new("RGB", (w, h), color=(18, 22, 28))
    im.save(path, format="PNG")
    return int(path.stat().st_size) if path.is_file() else 0


def generate_openai_image_from_prompt(
    prompt: str,
    output_path: str | Path,
    *,
    dry_run: bool = True,
    size: str = "1024x1024",
    model: Optional[str] = None,
    api_base: str = _DEFAULT_API_BASE,
    timeout_seconds: float = 30.0,
) -> OpenAIImageGenerationResult:
    """
    Dry-run: schreibt optional eine clean placeholder PNG (ohne Text) und liefert ok=true.
    Live: POST /v1/images/generations, erwartet b64_json, schreibt PNG.
    """
    warns: List[str] = []
    out = Path(output_path).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    p_used = (prompt or "").strip()
    if not p_used:
        p_used = "Clean editorial background, negative space for later overlay, no readable text."
        warns.append("openai_images_empty_prompt_defaulted")

    # Reihenfolge: Aufrufparameter → OPENAI_IMAGE_MODEL → Settings → Default gpt-image-2 (Smoke: testweise z. B. gpt-image-1).
    eff_model = (
        model
        or (os.environ.get("OPENAI_IMAGE_MODEL") or "").strip()
        or str(getattr(settings, "openai_image_model", "") or "").strip()
        or "gpt-image-2"
    ).strip()
    eff_size = (size or getattr(settings, "openai_image_size", "") or "1024x1024").strip()

    if dry_run:
        bw = _write_clean_placeholder_png(out, size=eff_size)
        return OpenAIImageGenerationResult(
            ok=True,
            provider="openai_images",
            dry_run=True,
            model=eff_model,
            size=eff_size,
            prompt_used=p_used,
            output_path=str(out),
            bytes_written=int(bw),
            warnings=warns + ["openai_images_dry_run_placeholder_written"],
            error_code="",
            error_message="",
        )

    key = _effective_openai_api_key()
    if not key:
        return OpenAIImageGenerationResult(
            ok=False,
            provider="openai_images",
            dry_run=False,
            model=eff_model,
            size=eff_size,
            prompt_used=p_used,
            output_path=str(out),
            bytes_written=0,
            warnings=warns + ["openai_api_key_missing"],
            error_code="openai_api_key_missing",
            error_message="OPENAI_API_KEY is not set (empty).",
        )

    url = (api_base or _DEFAULT_API_BASE).rstrip("/") + "/v1/images/generations"
    body = {
        "model": eff_model,
        "prompt": p_used,
        "size": eff_size,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}",
        "Accept": "application/json",
    }
    req = Request(url, data=json.dumps(body).encode("utf-8"), method="POST", headers=headers)
    try:
        with urlopen(req, timeout=float(timeout_seconds)) as resp:
            code = getattr(resp, "status", None) or resp.getcode()
            raw = resp.read()
    except HTTPError as e:
        status = int(getattr(e, "code", 0) or 0)
        http_warn = _openai_image_http_warning(status)
        extra: List[str] = [http_warn]
        if status == 403:
            extra.append(f"openai_image_model_access_denied:{eff_model}")
        ec = _openai_images_error_code_for_http(status)
        return OpenAIImageGenerationResult(
            ok=False,
            provider="openai_images",
            dry_run=False,
            model=eff_model,
            size=eff_size,
            prompt_used=p_used,
            output_path=str(out),
            bytes_written=0,
            warnings=warns + extra,
            error_code=ec,
            error_message=f"HTTP {status}",
        )
    except (URLError, OSError, ValueError) as e:
        return OpenAIImageGenerationResult(
            ok=False,
            provider="openai_images",
            dry_run=False,
            model=eff_model,
            size=eff_size,
            prompt_used=p_used,
            output_path=str(out),
            bytes_written=0,
            warnings=warns + [f"openai_images_network_error:{type(e).__name__}"],
            error_code="openai_images_network_error",
            error_message=str(e)[:240],
        )

    if int(code) != 200:
        status = int(code)
        http_warn = _openai_image_http_warning(status)
        extra: List[str] = [http_warn]
        if status == 403:
            extra.append(f"openai_image_model_access_denied:{eff_model}")
        ec = _openai_images_error_code_for_http(status)
        return OpenAIImageGenerationResult(
            ok=False,
            provider="openai_images",
            dry_run=False,
            model=eff_model,
            size=eff_size,
            prompt_used=p_used,
            output_path=str(out),
            bytes_written=0,
            warnings=warns + extra,
            error_code=ec,
            error_message=f"HTTP {status}",
        )

    try:
        parsed = json.loads(raw.decode("utf-8", errors="replace"))
    except json.JSONDecodeError:
        return OpenAIImageGenerationResult(
            ok=False,
            provider="openai_images",
            dry_run=False,
            model=eff_model,
            size=eff_size,
            prompt_used=p_used,
            output_path=str(out),
            bytes_written=0,
            warnings=warns + ["openai_images_response_not_json"],
            error_code="openai_images_response_not_json",
            error_message="invalid JSON",
        )

    data = parsed.get("data") if isinstance(parsed, dict) else None
    if not isinstance(data, list) or not data:
        return OpenAIImageGenerationResult(
            ok=False,
            provider="openai_images",
            dry_run=False,
            model=eff_model,
            size=eff_size,
            prompt_used=p_used,
            output_path=str(out),
            bytes_written=0,
            warnings=warns + ["openai_images_response_missing_data"],
            error_code="openai_images_response_missing_data",
            error_message="missing data[]",
        )

    first = data[0] if isinstance(data[0], dict) else {}
    b64 = first.get("b64_json")
    if not isinstance(b64, str) or not b64.strip():
        return OpenAIImageGenerationResult(
            ok=False,
            provider="openai_images",
            dry_run=False,
            model=eff_model,
            size=eff_size,
            prompt_used=p_used,
            output_path=str(out),
            bytes_written=0,
            warnings=warns + ["openai_images_missing_b64_json"],
            error_code="openai_images_missing_b64_json",
            error_message="missing b64_json",
        )

    try:
        blob = base64.b64decode(b64.encode("utf-8"), validate=False)
        out.write_bytes(blob)
        bw = int(out.stat().st_size) if out.is_file() else 0
        ok = bw > 0
    except Exception as e:
        return OpenAIImageGenerationResult(
            ok=False,
            provider="openai_images",
            dry_run=False,
            model=eff_model,
            size=eff_size,
            prompt_used=p_used,
            output_path=str(out),
            bytes_written=0,
            warnings=warns + [f"openai_images_write_failed:{type(e).__name__}"],
            error_code="openai_images_write_failed",
            error_message=str(e)[:240],
        )

    return OpenAIImageGenerationResult(
        ok=bool(ok),
        provider="openai_images",
        dry_run=False,
        model=eff_model,
        size=eff_size,
        prompt_used=p_used,
        output_path=str(out),
        bytes_written=int(bw),
        warnings=warns,
        error_code="",
        error_message="",
    )

