"""BA 32.39 — Leonardo List Platform Models: sichere, key-freie Metadaten (kein CI-Live-Call)."""

from __future__ import annotations

import json
import socket
from typing import Any, Dict, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.production_connectors.leonardo_live_connector import LEONARDO_PLATFORM_MODELS_URL


def _http_status_warnings(code: int) -> List[str]:
    out: List[str] = [f"leonardo_models_http_error:{int(code)}"]
    if code == 401:
        out.append("leonardo_models_http_401")
    elif code == 403:
        out.append("leonardo_models_http_403")
    elif 500 <= code < 600:
        out.append("leonardo_models_http_5xx")
    return out


def _transport_warning(exc: BaseException) -> str:
    if isinstance(exc, URLError):
        r = getattr(exc, "reason", exc)
        if isinstance(r, socket.timeout) or r is socket.timeout:
            return "leonardo_models_url_error:timeout"
        return f"leonardo_models_url_error:{type(r).__name__}"
    return f"leonardo_models_url_error:{type(exc).__name__}"


def _sanitize_platform_model_row(raw: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(raw, dict):
        return None
    mid = str(raw.get("id") or "").strip()
    if not mid:
        return None
    name = raw.get("name")
    name_s = str(name).strip()[:512] if name is not None else ""
    desc = raw.get("description")
    if isinstance(desc, str):
        dlen = len(desc)
    elif desc is None:
        dlen = 0
    else:
        dlen = len(str(desc))
    gi = raw.get("generated_image")
    has_preview = isinstance(gi, dict) and bool(str(gi.get("id") or "").strip())
    return {
        "id": mid,
        "name": name_s,
        "featured": bool(raw.get("featured")),
        "nsfw": bool(raw.get("nsfw")),
        "description_char_count": min(dlen, 50_000),
        "has_preview_image": has_preview,
    }


def fetch_leonardo_platform_models_public(
    *,
    api_key: str,
    url: Optional[str] = None,
    timeout_seconds: float = 45.0,
) -> Tuple[bool, List[Dict[str, Any]], List[str]]:
    """
    GET /platformModels — nur aggregierte/sichere Felder pro Modell (keine Preview-URLs, keine Roh-Responses).
    Rückgabe: (ok, models, warnings)
    """
    warns: List[str] = []
    key = (api_key or "").strip()
    if not key:
        return False, [], ["leonardo_models_api_key_missing"]

    endpoint = (url or LEONARDO_PLATFORM_MODELS_URL or "").strip()
    if not endpoint:
        return False, [], ["leonardo_models_url_missing"]

    req = Request(
        endpoint,
        method="GET",
        headers={
            "Authorization": f"Bearer {key}",
            "Accept": "application/json",
        },
    )
    try:
        with urlopen(req, timeout=timeout_seconds) as resp:
            raw = resp.read()
            code = getattr(resp, "status", None) or resp.getcode()
            if int(code) != 200:
                warns.extend(_http_status_warnings(int(code)))
                return False, [], warns
    except HTTPError as e:
        warns.extend(_http_status_warnings(int(e.code)))
        return False, [], warns
    except (URLError, OSError, TimeoutError) as e:
        warns.append(_transport_warning(e))
        return False, [], warns

    try:
        parsed: Any = json.loads(raw.decode("utf-8", errors="replace"))
    except json.JSONDecodeError:
        warns.append("leonardo_models_response_invalid")
        return False, [], warns

    if not isinstance(parsed, dict):
        warns.append("leonardo_models_response_invalid")
        return False, [], warns

    rows = parsed.get("custom_models")
    if rows is None:
        warns.append("leonardo_models_response_invalid")
        return False, [], warns
    if not isinstance(rows, list):
        warns.append("leonardo_models_response_invalid")
        return False, [], warns

    models: List[Dict[str, Any]] = []
    for row in rows:
        s = _sanitize_platform_model_row(row)
        if s is not None:
            models.append(s)

    return True, models, warns
