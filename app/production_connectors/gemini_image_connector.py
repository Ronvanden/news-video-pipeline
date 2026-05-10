"""BA 32.41 — Gemini / Nano Banana Image Connector (minimal, live; tests mock HTTP).

- Keine Secrets loggen (API-Key nie in Warnings / stdout).
- Keine vollständigen Prompts in Warnings.
- Keine Response-Bodies ausgeben (nur PNG schreiben + sichere Codes).
"""

from __future__ import annotations

import base64
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_GEMINI_IMAGE_MODEL = "gemini-2.5-flash-image"
DEFAULT_GEMINI_IMAGE_TIMEOUT_SECONDS = 120.0
DEFAULT_GEMINI_IMAGE_ENDPOINT_BASE = "https://generativelanguage.googleapis.com/v1beta/models/"

_RESPONSE_INVALID = "gemini_image_response_invalid"
_DETAIL_NO_INLINE_DATA = "gemini_image_no_inline_data"
_DETAIL_NO_IMAGE_PART = "gemini_image_no_image_part"
_DETAIL_EMPTY_IMAGE_BYTES = "gemini_image_empty_image_bytes"
_POST_MAX_ATTEMPTS = 3
_POST_BACKOFF_BASE_SEC = 0.7


class GeminiInvalidImageResponse(Exception):
    """Antwort ohne verwertbare Bildbytes (kein Body-Logging, keine Secrets)."""

    __slots__ = ()


def _effective_transport() -> str:
    raw = (os.environ.get("GEMINI_IMAGE_TRANSPORT") or "rest").strip().lower()
    return "sdk" if raw in ("sdk", "genai", "google_genai", "google-genai") else "rest"


def _http_status_warnings(code: int) -> List[str]:
    c = int(code)
    out: List[str] = []
    if c == 400:
        out.append("gemini_image_http_400")
    elif c == 401:
        out.append("gemini_image_http_401")
    elif c == 403:
        out.append("gemini_image_http_403")
    elif c == 429:
        out.append("gemini_image_http_429")
    elif 500 <= c < 600:
        out.append("gemini_image_http_5xx")
    out.append(f"gemini_image_http_error:{c}")
    return out


def _should_retry_http(code: int) -> bool:
    c = int(code)
    return c == 429 or (500 <= c < 600)


def _transport_diag(exc: BaseException) -> List[str]:
    if isinstance(exc, TimeoutError):
        return ["gemini_image_timeout"]
    if isinstance(exc, URLError):
        return ["gemini_image_url_error"]
    return [f"gemini_image_post_failed:{type(exc).__name__}"]


def _effective_gemini_api_key() -> str:
    # Repo-Konvention: erstmal GEMINI_API_KEY, fallback GOOGLE_API_KEY.
    k = (os.environ.get("GEMINI_API_KEY") or "").strip()
    if k:
        return k
    return (os.environ.get("GOOGLE_API_KEY") or "").strip()


def _effective_gemini_model(model: Optional[str]) -> str:
    return (
        (model or "").strip()
        or (os.environ.get("GEMINI_IMAGE_MODEL") or "").strip()
        or DEFAULT_GEMINI_IMAGE_MODEL
    )


def _safe_fail_tag(s: str) -> str:
    v = (s or "error").strip().lower()
    v = v.replace(":", "_").replace(" ", "_")
    # keep short & log-safe
    return v[:96] if v else "error"


def _extract_first_inline_png_b64(parsed: Any) -> Optional[str]:
    """
    Erwartetes Schema (REST generateContent):
      candidates[0].content.parts[].inlineData.data (base64 PNG o. ä.)
    """
    if not isinstance(parsed, dict):
        return None
    cands = parsed.get("candidates")
    if not isinstance(cands, list) or not cands:
        return None
    cand0 = cands[0] if isinstance(cands[0], dict) else {}
    content = cand0.get("content") if isinstance(cand0, dict) else None
    if not isinstance(content, dict):
        return None
    parts = content.get("parts")
    if not isinstance(parts, list) or not parts:
        return None
    for p in parts:
        if not isinstance(p, dict):
            continue
        inline = p.get("inlineData")
        if not isinstance(inline, dict):
            continue
        data = inline.get("data")
        if isinstance(data, str) and data.strip():
            return data.strip()
    return None


def _classify_rest_missing_inline(parsed: Any) -> str:
    """Ein sicherer Detailcode, wenn keine verwertbaren inlineData-Bytes extrahiert werden."""
    if not isinstance(parsed, dict):
        return _DETAIL_NO_IMAGE_PART
    cands = parsed.get("candidates")
    if not isinstance(cands, list) or len(cands) == 0:
        return _DETAIL_NO_IMAGE_PART
    cand0 = cands[0]
    if not isinstance(cand0, dict):
        return _DETAIL_NO_IMAGE_PART
    content = cand0.get("content")
    if not isinstance(content, dict):
        return _DETAIL_NO_IMAGE_PART
    parts = content.get("parts")
    if not isinstance(parts, list) or len(parts) == 0:
        return _DETAIL_NO_IMAGE_PART
    saw_inline_dict = False
    for p in parts:
        if not isinstance(p, dict):
            continue
        inline = p.get("inlineData") or p.get("inline_data")
        if isinstance(inline, dict):
            saw_inline_dict = True
            data = inline.get("data")
            if isinstance(data, str) and data.strip():
                # Struktur sah nach Daten aus, Extraktion schlug fehl → leer/korrupt
                return _DETAIL_EMPTY_IMAGE_BYTES
    if not saw_inline_dict:
        return _DETAIL_NO_INLINE_DATA
    return _DETAIL_EMPTY_IMAGE_BYTES


def _sdk_available() -> bool:
    try:
        from google import genai  # type: ignore  # noqa: F401
        from google.genai import types  # type: ignore  # noqa: F401
        return True
    except Exception:
        return False


def _sdk_client(api_key: str):
    from google import genai  # type: ignore
    return genai.Client(api_key=api_key)


def _sdk_response_parts(resp: Any) -> List[Any]:
    """
    Normalize SDK response to a list of "parts" objects/dicts.
    We support both attribute-style and dict-style to keep this spike resilient.
    """
    try:
        parts = getattr(resp, "parts", None)
        if isinstance(parts, list) and parts:
            return parts
    except Exception:
        pass
    try:
        cands = getattr(resp, "candidates", None)
        if isinstance(cands, list) and cands:
            cand0 = cands[0]
            content = getattr(cand0, "content", None)
            parts = getattr(content, "parts", None)
            if isinstance(parts, list):
                return parts
    except Exception:
        pass
    if isinstance(resp, dict):
        cands = resp.get("candidates")
        if isinstance(cands, list) and cands and isinstance(cands[0], dict):
            content = cands[0].get("content")
            if isinstance(content, dict):
                parts = content.get("parts")
                if isinstance(parts, list):
                    return parts
    return []


def _sdk_extract_first_image_bytes(resp: Any) -> Optional[bytes]:
    for part in _sdk_response_parts(resp):
        if isinstance(part, dict):
            inline = part.get("inline_data") or part.get("inlineData") or part.get("inline_data".title())
            if isinstance(inline, dict):
                data = inline.get("data")
                if isinstance(data, (bytes, bytearray)):
                    return bytes(data)
                if isinstance(data, str) and data.strip():
                    try:
                        return base64.b64decode(data.strip().encode("utf-8"), validate=False)
                    except Exception:
                        return None
        else:
            inline = getattr(part, "inline_data", None) or getattr(part, "inlineData", None)
            if inline is None:
                continue
            data = getattr(inline, "data", None)
            if isinstance(data, (bytes, bytearray)):
                return bytes(data)
            if isinstance(data, str) and data.strip():
                try:
                    return base64.b64decode(data.strip().encode("utf-8"), validate=False)
                except Exception:
                    return None
    return None


def _sdk_exception_diag(exc: BaseException) -> Tuple[List[str], bool]:
    """
    Map SDK exceptions to safe codes. We avoid reading response bodies.
    Returns: (diag_codes, retryable)
    """
    s = (str(exc) or "").lower()
    # Common "status" hints in Google APIs.
    if "429" in s or "resource_exhausted" in s or "rate limit" in s or "quota" in s:
        d = _http_status_warnings(429)
        return d + ["gemini_image_sdk_error:rate_limited"], True
    if "401" in s or "unauth" in s or "unauthenticated" in s:
        d = _http_status_warnings(401)
        return d + ["gemini_image_sdk_error:auth_failed"], False
    if "403" in s or "permission_denied" in s or "forbidden" in s:
        d = _http_status_warnings(403)
        return d + ["gemini_image_sdk_error:permission_denied"], False
    if "500" in s or "503" in s or "internal" in s or "unavailable" in s:
        d = _http_status_warnings(503)
        return d + ["gemini_image_sdk_error:transient"], True
    tag = _safe_fail_tag(type(exc).__name__)
    return [f"gemini_image_sdk_error:{tag}"], False


def _sdk_generate_image_bytes(
    *,
    api_key: str,
    model: str,
    prompt: str,
) -> bytes:
    client = _sdk_client(api_key)
    models = getattr(client, "models", None)
    if models is None:
        raise RuntimeError("sdk_models_missing")
    gen = getattr(models, "generate_content", None) or getattr(models, "generateContent", None)
    if not callable(gen):
        raise RuntimeError("sdk_generate_content_missing")
    # Offizielle Doku-Struktur (BA 32.44): types.GenerateContentConfig + types.ImageConfig
    from google.genai import types  # type: ignore

    resp = gen(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(aspect_ratio="1:1"),
        ),
    )
    blob = _sdk_extract_first_image_bytes(resp)
    if not blob:
        raise ValueError("sdk_response_missing_image")
    return blob


def _rest_generate_image_bytes(
    *,
    api_key: str,
    model: str,
    prompt: str,
    timeout_seconds: float,
    warns: List[str],
) -> bytes:
    # REST Docs: POST https://generativelanguage.googleapis.com/v1beta/models/<model>:generateContent
    url = f"{DEFAULT_GEMINI_IMAGE_ENDPOINT_BASE}{model}:generateContent"
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        # Safe default: request image modality; Gemini kann TEXT+IMAGE liefern.
        "generationConfig": {"responseModalities": ["IMAGE"]},
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        # Docs: x-goog-api-key header
        "x-goog-api-key": api_key,
    }

    raw = b""
    last_http: Optional[int] = None
    for attempt in range(_POST_MAX_ATTEMPTS):
        try:
            req = Request(url, data=json.dumps(body).encode("utf-8"), method="POST", headers=headers)
            with urlopen(req, timeout=float(timeout_seconds)) as resp:
                code = getattr(resp, "status", None) or resp.getcode()
                raw = resp.read() or b""
            last_http = int(code)
            if int(code) != 200:
                diag = _http_status_warnings(int(code))
                if _should_retry_http(int(code)) and attempt < _POST_MAX_ATTEMPTS - 1:
                    warns.extend(diag)
                    warns.append(f"gemini_image_retry_{attempt + 1}_after:{diag[0]}")
                    time.sleep(_POST_BACKOFF_BASE_SEC * (attempt + 1))
                    continue
                warns.extend(diag)
                raise HTTPError(url, int(code), "non-200", {}, None)  # handled below uniformly
            break
        except HTTPError as e:
            code_i = int(getattr(e, "code", 0) or 0)
            last_http = code_i
            diag = _http_status_warnings(code_i)
            if _should_retry_http(code_i) and attempt < _POST_MAX_ATTEMPTS - 1:
                warns.extend(diag)
                warns.append(f"gemini_image_retry_{attempt + 1}_after:{diag[0]}")
                time.sleep(_POST_BACKOFF_BASE_SEC * (attempt + 1))
                continue
            warns.extend(diag)
            raise
        except (URLError, OSError, TimeoutError, ValueError) as e:
            diag = _transport_diag(e)
            if attempt < _POST_MAX_ATTEMPTS - 1 and (diag[0] in ("gemini_image_timeout", "gemini_image_url_error")):
                warns.extend(diag)
                warns.append(f"gemini_image_retry_{attempt + 1}_after:{diag[0]}")
                time.sleep(_POST_BACKOFF_BASE_SEC * (attempt + 1))
                continue
            warns.extend(diag)
            raise
    else:  # pragma: no cover
        if last_http is not None:
            warns.extend(_http_status_warnings(int(last_http)))
        raise RuntimeError("rest_exhausted")

    try:
        parsed: Any = json.loads(raw.decode("utf-8", errors="replace"))
    except json.JSONDecodeError:
        warns.append(_RESPONSE_INVALID)
        warns.append(_DETAIL_NO_IMAGE_PART)
        raise GeminiInvalidImageResponse()

    b64 = _extract_first_inline_png_b64(parsed)
    if not b64:
        warns.append(_RESPONSE_INVALID)
        warns.append(_classify_rest_missing_inline(parsed))
        raise GeminiInvalidImageResponse()

    try:
        decoded = base64.b64decode(b64.encode("utf-8"), validate=False)
    except Exception:
        warns.append(_RESPONSE_INVALID)
        warns.append(_DETAIL_EMPTY_IMAGE_BYTES)
        raise GeminiInvalidImageResponse()
    if not decoded:
        warns.append(_RESPONSE_INVALID)
        warns.append(_DETAIL_EMPTY_IMAGE_BYTES)
        raise GeminiInvalidImageResponse()
    return decoded


def run_gemini_image_live_to_png(
    visual_prompt_effective: str,
    dest_png: Path,
    *,
    model: Optional[str] = None,
    timeout_seconds: float = DEFAULT_GEMINI_IMAGE_TIMEOUT_SECONDS,
) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    Live-Call gegen Gemini generateContent (TEXT+IMAGE response). Rückgabe:
      (ok, warnings, result_meta_public)

    result_meta_public ist nur bei Erfolg gefüllt (ohne Prompt/Key/Body).
    """
    warns: List[str] = []
    eff_model = _effective_gemini_model(model)
    warns.append(f"gemini_image_model:{eff_model}")
    warns.append("gemini_image_provider:gemini_image")

    key = _effective_gemini_api_key()
    if not key:
        warns.append("gemini_image_key_missing_fallback_placeholder")
        return False, warns, {}

    prompt = (visual_prompt_effective or "").strip()
    if not prompt:
        # Kein Prompt in Warnungen; nur safe-code.
        warns.append("gemini_image_prompt_empty")
        prompt = "Clean editorial background, no readable text."

    transport = _effective_transport()
    if transport == "sdk" and not _sdk_available():
        warns.append("gemini_image_sdk_unavailable_fallback_rest")
        transport = "rest"
    warns.append(f"gemini_image_transport:{transport}")

    def _sdk_fetch_with_http_retries() -> Optional[bytes]:
        """HTTP-429/5xx-Retries wie BA 32.43; ValueError „missing image“ → GeminiInvalidImageResponse."""
        blob_local: Optional[bytes] = None
        for attempt in range(_POST_MAX_ATTEMPTS):
            try:
                blob_local = _sdk_generate_image_bytes(api_key=key, model=eff_model, prompt=prompt)
                break
            except ValueError as ve:
                if str(ve) == "sdk_response_missing_image":
                    warns.append(_RESPONSE_INVALID)
                    warns.append(_DETAIL_NO_IMAGE_PART)
                    raise GeminiInvalidImageResponse() from ve
                raise
            except Exception as e:
                diag, retryable = _sdk_exception_diag(e)
                warns.extend(diag)
                if retryable and attempt < _POST_MAX_ATTEMPTS - 1:
                    warns.append(f"gemini_image_retry_{attempt + 1}_after:{diag[0]}")
                    time.sleep(_POST_BACKOFF_BASE_SEC * (attempt + 1))
                    continue
                if any(d.startswith("gemini_image_http_error:") for d in diag):
                    for d in diag:
                        if d.startswith("gemini_image_http_error:"):
                            code = d.split(":", 1)[1]
                            warns.append(f"gemini_image_generation_failed:http_{code}")
                            break
                else:
                    warns.append(f"gemini_image_generation_failed:{_safe_fail_tag(type(e).__name__)}")
                return None
        if not blob_local:
            warns.append("gemini_image_generation_failed:exhausted")
            return None
        return blob_local

    invalid_round = 0
    invalid_retries_used = 0
    while invalid_round < 2:
        blob: Optional[bytes] = None
        try:
            if transport == "sdk":
                blob = _sdk_fetch_with_http_retries()
                if blob is None:
                    return False, warns, {}
            else:
                blob = _rest_generate_image_bytes(
                    api_key=key,
                    model=eff_model,
                    prompt=prompt,
                    timeout_seconds=float(timeout_seconds),
                    warns=warns,
                )
        except GeminiInvalidImageResponse:
            if invalid_round == 0:
                warns.append("gemini_image_retry_1_after:gemini_image_response_invalid")
                invalid_retries_used = 1
                invalid_round += 1
                continue
            warns.append("gemini_image_generation_failed:invalid_response_exhausted")
            return False, warns, {}
        except HTTPError as e:
            code_i = int(getattr(e, "code", 0) or 0)
            warns.append(f"gemini_image_generation_failed:http_{code_i}")
            return False, warns, {}
        except Exception as e:
            warns.append(f"gemini_image_generation_failed:{_safe_fail_tag(type(e).__name__)}")
            return False, warns, {}

        try:
            dest_png.parent.mkdir(parents=True, exist_ok=True)
            dest_png.write_bytes(blob or b"")
            bw = int(dest_png.stat().st_size) if dest_png.is_file() else 0
        except Exception as e:
            warns.append(f"gemini_image_generation_failed:write_{_safe_fail_tag(type(e).__name__)}")
            return False, warns, {}

        if bw <= 0:
            warns.append(_RESPONSE_INVALID)
            warns.append(_DETAIL_EMPTY_IMAGE_BYTES)
            if invalid_round == 0:
                warns.append("gemini_image_retry_1_after:gemini_image_response_invalid")
                invalid_retries_used = 1
                invalid_round += 1
                continue
            warns.append("gemini_image_generation_failed:invalid_response_exhausted")
            return False, warns, {}

        meta = {
            "ok": True,
            "model": eff_model,
            "bytes_written": bw,
            "gemini_invalid_response_retries_used": invalid_retries_used,
        }
        return True, warns, meta

    return False, warns, {}

