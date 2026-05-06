"""Fetch a Leonardo generation result safely by ID."""

from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pydantic import BaseModel, Field

LEONARDO_GENERATION_ENDPOINT = "https://cloud.leonardo.ai/api/rest/v1/generations/{generation_id}"


class LeonardoGenerationFetchResult(BaseModel):
    """Safe JSON result for a Leonardo generation GET request."""

    http_attempted: bool = False
    http_status: Optional[int] = None
    method: str = "GET"
    request_url: Optional[str] = None
    header_names: List[str] = Field(default_factory=list)
    generation_id: str = ""
    generation_status: Optional[str] = None
    image_urls: List[str] = Field(default_factory=list)
    response_shape_summary: Dict[str, str] = Field(default_factory=dict)
    response_text_preview: str = ""
    warnings: List[str] = Field(default_factory=list)


def _shape_summary(response: Dict[str, Any]) -> Dict[str, str]:
    return {str(k): type(v).__name__ for k, v in sorted(response.items())}


def _response_preview(response: Dict[str, Any]) -> str:
    raw = response.get("raw_text")
    if isinstance(raw, str):
        text = raw
    else:
        text = json.dumps(response, ensure_ascii=False, sort_keys=True)
    return text[:300]


def _parse_response(raw_bytes: bytes) -> Dict[str, Any]:
    try:
        parsed = json.loads(raw_bytes.decode("utf-8", errors="replace"))
    except json.JSONDecodeError:
        return {"raw_text": raw_bytes[:2048].decode("utf-8", errors="replace")}
    return parsed if isinstance(parsed, dict) else {"value": parsed}


def _generation_object(response: Dict[str, Any]) -> Dict[str, Any]:
    for key in ("generations_by_pk", "generation", "data"):
        value = response.get(key)
        if isinstance(value, dict):
            return value
    return response


def _extract_status(response: Dict[str, Any]) -> Optional[str]:
    generation = _generation_object(response)
    for key in ("status", "generation_status", "generationStatus"):
        value = generation.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _collect_urls(value: Any, out: List[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in ("url", "image_url", "imageUrl", "asset_url") and isinstance(child, str):
                if child.startswith(("http://", "https://")) and child not in out:
                    out.append(child)
            else:
                _collect_urls(child, out)
    elif isinstance(value, list):
        for child in value:
            _collect_urls(child, out)


def _extract_image_urls(response: Dict[str, Any]) -> List[str]:
    urls: List[str] = []
    _collect_urls(_generation_object(response), urls)
    return urls


def _safe_header_names(headers: Dict[str, str]) -> List[str]:
    return sorted(headers.keys(), key=str.lower)


def fetch_leonardo_generation_result(
    generation_id: str,
    *,
    timeout_seconds: float = 25.0,
    max_attempts: int = 3,
    retry_sleep_seconds: float = 5.0,
) -> LeonardoGenerationFetchResult:
    """GET a Leonardo generation by ID without logging secrets."""
    gid = (generation_id or "").strip()
    warnings: List[str] = []
    if not gid:
        return LeonardoGenerationFetchResult(
            generation_id="",
            warnings=["generation_id_missing"],
        )

    endpoint = LEONARDO_GENERATION_ENDPOINT.format(generation_id=gid)
    api_key = (os.getenv("LEONARDO_API_KEY") or "").strip()
    if not api_key:
        return LeonardoGenerationFetchResult(
            method="GET",
            request_url=endpoint,
            generation_id=gid,
            warnings=["leonardo_api_key_missing_no_http_attempt"],
        )

    attempts = max(1, min(int(max_attempts), 3))
    headers = {
        "Authorization": f"Bearer {api_key}",
        "accept": "application/json",
    }
    header_names = _safe_header_names(headers)
    last_warning: Optional[str] = None

    for attempt in range(1, attempts + 1):
        request = Request(
            endpoint,
            method="GET",
            headers=headers,
        )
        try:
            with urlopen(request, timeout=timeout_seconds) as response:
                raw = response.read()
                status = getattr(response, "status", None) or response.getcode()
                parsed = _parse_response(raw)
                return LeonardoGenerationFetchResult(
                    http_attempted=True,
                    http_status=int(status) if status is not None else None,
                    method="GET",
                    request_url=endpoint,
                    header_names=header_names,
                    generation_id=gid,
                    generation_status=_extract_status(parsed),
                    image_urls=_extract_image_urls(parsed),
                    response_shape_summary=_shape_summary(parsed),
                    response_text_preview=_response_preview(parsed),
                    warnings=warnings,
                )
        except HTTPError as exc:
            last_warning = f"leonardo_http_error:{exc.code}"
            try:
                parsed = _parse_response(exc.read())
            except Exception:
                parsed = {"http_error": True, "code": exc.code}
            parsed.setdefault("http_error", True)
            parsed.setdefault("code", exc.code)
            if attempt < attempts:
                time.sleep(retry_sleep_seconds)
                continue
            return LeonardoGenerationFetchResult(
                http_attempted=True,
                http_status=int(exc.code),
                method="GET",
                request_url=endpoint,
                header_names=header_names,
                generation_id=gid,
                generation_status=_extract_status(parsed),
                image_urls=_extract_image_urls(parsed),
                response_shape_summary=_shape_summary(parsed),
                response_text_preview=_response_preview(parsed),
                warnings=warnings + [last_warning],
            )
        except URLError as exc:
            reason = getattr(exc, "reason", exc)
            last_warning = f"leonardo_url_error:{reason}"
            if attempt < attempts:
                time.sleep(retry_sleep_seconds)
                continue
            return LeonardoGenerationFetchResult(
                http_attempted=True,
                method="GET",
                request_url=endpoint,
                header_names=header_names,
                generation_id=gid,
                response_shape_summary={"url_error": "bool"},
                response_text_preview=json.dumps({"url_error": True})[:300],
                warnings=warnings + [last_warning],
            )

    return LeonardoGenerationFetchResult(
        http_attempted=True,
        method="GET",
        request_url=endpoint,
        header_names=header_names,
        generation_id=gid,
        warnings=warnings + (["leonardo_get_retry_exhausted"] if last_warning is None else [last_warning]),
    )
