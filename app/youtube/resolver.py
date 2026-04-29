"""Kanal-URL → Channel-ID (UC…) ohne YouTube Data API."""

from __future__ import annotations

import re
from typing import List, Optional, Tuple
from urllib.parse import urlparse, unquote

import httpx

_CHANNEL_ID_RE = re.compile(r"UC[a-zA-Z0-9_-]{22}")
# channelId in JSON / meta
_CHANNEL_ID_JSON_RE = re.compile(r'"channelId"\s*:\s*"(UC[a-zA-Z0-9_-]{22})"')
_BROWSE_ID_RE = re.compile(r'"browseId"\s*:\s*"(UC[a-zA-Z0-9_-]{22})"')
_CANONICAL_CHANNEL_RE = re.compile(
    r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']https?://(?:www\.)?youtube\.com/channel/(UC[a-zA-Z0-9_-]{22})',
    re.IGNORECASE,
)
_CHANNEL_PATH_RE = re.compile(
    r'https?://(?:www\.)?youtube\.com/channel/(UC[a-zA-Z0-9_-]{22})',
    re.IGNORECASE,
)

_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "de,en;q=0.9",
}
_HTTP_TIMEOUT = httpx.Timeout(20.0, connect=15.0)


def _first_channel_id_from_text(html: str) -> Optional[str]:
    if not html:
        return None
    m = _CANONICAL_CHANNEL_RE.search(html)
    if m:
        return m.group(1)
    m = _CHANNEL_PATH_RE.search(html)
    if m:
        return m.group(1)
    m = _CHANNEL_ID_JSON_RE.search(html)
    if m:
        return m.group(1)
    m = _BROWSE_ID_RE.search(html)
    if m:
        return m.group(1)
    m = _CHANNEL_ID_RE.search(html)
    if m:
        return m.group(0)
    return None


def normalize_channel_input(channel_url: str) -> str:
    raw = (channel_url or "").strip()
    if not raw:
        return ""
    if not raw.startswith(("http://", "https://")):
        if raw.startswith("@"):
            return f"https://www.youtube.com/{raw}"
        if _CHANNEL_ID_RE.fullmatch(raw.strip()):
            return f"https://www.youtube.com/channel/{raw.strip()}"
        return f"https://www.youtube.com/@{raw.lstrip('@')}"
    return raw


def extract_channel_id_from_url(url: str) -> Optional[str]:
    """Nur aus der URL ohne Netzwerk, falls möglich."""
    try:
        parsed = urlparse(url)
    except Exception:
        return None
    host = (parsed.netloc or "").lower()
    if "youtube.com" not in host and "youtu.be" not in host:
        return None
    path = unquote(parsed.path or "")
    # /channel/UC...
    if "/channel/" in path:
        part = path.split("/channel/", 1)[-1].strip("/").split("/")[0]
        if part.startswith("UC") and len(part) >= 24:
            m = _CHANNEL_ID_RE.match(part)
            if m:
                return m.group(0)
    q = parsed.query or ""
    if "channel_id=" in q.lower():
        for seg in q.split("&"):
            if "=" in seg:
                k, v = seg.split("=", 1)
                if k.lower() == "channel_id":
                    cid = unquote(v)
                    m = _CHANNEL_ID_RE.search(cid)
                    if m:
                        return m.group(0)
    return None


def resolve_channel_id(channel_url: str) -> Tuple[Optional[str], List[str]]:
    """
    Liefert UC-Channel-ID oder None. warnings sammelt Hinweise (z. B. Handle-Grenzen).
    """
    warnings: List[str] = []
    normalized = normalize_channel_input(channel_url)
    if not normalized:
        warnings.append("Leere channel_url: bitte eine gültige YouTube-Kanal-URL oder @Handle angeben.")
        return None, warnings

    direct = extract_channel_id_from_url(normalized)
    if direct:
        return direct, warnings

    parsed = urlparse(normalized)
    path_raw = parsed.path or ""
    path_lower = path_raw.lower()
    if "/watch" in path_lower or "/shorts/" in path_lower or "/embed/" in path_lower:
        warnings.append(
            "Diese URL verweist auf ein Video (watch/shorts/embed), nicht auf einen Kanal. "
            "Bitte @Handle oder /channel/UC… verwenden."
        )
        return None, warnings

    path = path_raw.lower()
    needs_resolve = (
        "/@" in path
        or path.startswith("/c/")
        or path.startswith("/user/")
        or (
            parsed.path
            and parsed.path.strip("/")
            and "/channel/" not in path
            and "youtu.be" not in parsed.netloc
        )
    )
    if not needs_resolve:
        warnings.append(
            "Konnte keine Channel-ID aus der URL ableiten. "
            "Nutzen Sie /channel/UC…, eine @Handle-URL oder die reine UC-ID."
        )
        return None, warnings

    try:
        with httpx.Client(timeout=_HTTP_TIMEOUT, headers=_DEFAULT_HEADERS, follow_redirects=True) as client:
            r = client.get(normalized)
        if r.status_code != 200:
            warnings.append(
                f"Kanalseite nicht lesbar (HTTP {r.status_code}). "
                "YouTube kann die Anfrage blockieren oder die URL ist ungültig."
            )
            return None, warnings
        html = r.text or ""
        html_l = html.lower()
        if "consent.youtube.com" in html or "consentui" in html_l or "before you continue" in html_l:
            warnings.append(
                "YouTube lieferte eine Cookie-/Einwilligungsseite statt der Kanalseite; "
                "@Handle- oder Custom-URL-Auflösung ist ohne Session-Cookies oft nicht möglich. "
                "Robuster: https://www.youtube.com/channel/UC… (Channel-ID; RSS bleibt ohne API-Key)."
            )
            return None, warnings
        cid = _first_channel_id_from_text(html)
        if cid:
            if "/@" in path:
                warnings.append(
                    "@Handle-URLs werden über die öffentliche Kanalseite in eine Channel-ID aufgelöst; "
                    "bei A/B-Tests, Bot-Schutz oder Layout-Änderungen kann das fehlschlagen — dann /channel/UC… verwenden."
                )
            elif path.startswith("/c/") or path.startswith("/user/"):
                warnings.append(
                    "Custom-URLs (/c/…, /user/…) werden über die HTML-Kanalseite aufgelöst; "
                    "bei Layout-Änderungen kann das unzuverlässig sein — /channel/UC… ist robuster."
                )
            return cid, warnings
        warnings.append(
            "Handle- oder Custom-URL konnte nicht zuverlässig in eine Channel-ID aufgelöst werden "
            "(keine Channel-ID im HTML gefunden). Direktlink: https://www.youtube.com/channel/UC…"
        )
        return None, warnings
    except httpx.HTTPError as e:
        warnings.append(f"Netzwerkfehler bei Kanal-Auflösung: {type(e).__name__}")
        return None, warnings
