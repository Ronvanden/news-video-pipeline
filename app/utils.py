import logging
import json
from typing import Any, Dict, List, Optional, Tuple
import re
from urllib.parse import urlparse, parse_qs
import trafilatura
from youtube_transcript_api import YouTubeTranscriptApi
from deep_translator import GoogleTranslator
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from app.config import settings
from app.story_engine.conformance import apply_template_conformance
from app.story_engine.templates import (
    chapter_band_for_template_duration,
    normalize_story_template_id,
    story_template_blueprint_prompt_de,
    story_template_prompt_addon_de,
)
import httpx
try:
    import openai
except ImportError:
    openai = None

logger = logging.getLogger(__name__)

# Cloud Run / Container: ausreichend lange Connect-/Read-Timeouts, weniger aggressive Retries als Default.
_OPENAI_CONNECT_TIMEOUT_S = 20.0
_OPENAI_READ_WRITE_POOL_TIMEOUT_S = 60.0
_OPENAI_MAX_RETRIES = 2


def _openai_httpx_timeout() -> httpx.Timeout:
    return httpx.Timeout(
        connect=_OPENAI_CONNECT_TIMEOUT_S,
        read=_OPENAI_READ_WRITE_POOL_TIMEOUT_S,
        write=_OPENAI_READ_WRITE_POOL_TIMEOUT_S,
        pool=_OPENAI_READ_WRITE_POOL_TIMEOUT_S,
    )


def build_openai_http_client() -> httpx.Client:
    """Synchroner httpx-Client mit festen Timeouts für OpenAI-Aufrufe."""
    return httpx.Client(
        timeout=_openai_httpx_timeout(),
        limits=httpx.Limits(max_keepalive_connections=5, max_connections=20),
    )


def _effective_openai_api_key() -> str:
    """Key für Bearer-Header: führende/nachgestellte Whitespaces entfernen. Leer => kein LLM. Niemals loggen."""
    return (settings.openai_api_key or "").strip()


def build_openai_client():
    """
    OpenAI-Sync-Client mit explizitem httpx-Client, Timeouts und max_retries.
    Mit Kontextmanager nutzen: ``with build_openai_client() as client: ...``
    """
    if not openai:
        raise RuntimeError("openai package not installed")
    key = _effective_openai_api_key()
    if not key:
        raise RuntimeError("OpenAI client build without non-empty API key")
    return openai.OpenAI(
        api_key=key,
        max_retries=_OPENAI_MAX_RETRIES,
        http_client=build_openai_http_client(),
    )


def check_openai_endpoint_reachability(
    probe_timeout_s: float = 10.0,
) -> Tuple[bool, str]:
    """
    Interner Erreichbarkeitscheck (HTTPS zu api.openai.com, ohne Auth, kein Secret).
    Für Ops/Diagnose; nicht als öffentlicher Debug-Endpunkt mit Schlüsselausgabe verwenden.
    """
    url = "https://api.openai.com/"
    try:
        timeout = httpx.Timeout(probe_timeout_s, connect=min(probe_timeout_s, 15.0))
        with httpx.Client(timeout=timeout) as client:
            r = client.get(url)
        return True, f"reachability_ok status_code={r.status_code}"
    except Exception as e:
        note = _sanitize_openai_text(repr(e), max_len=240)
        return False, f"{type(e).__name__}: {note}"


def _safe_request_url_meta(request: object) -> str:
    """Nur Schema/Host/Pfad-Anfang — keine Query (könnte sensible Parameter tragen)."""
    try:
        url = getattr(request, "url", None)
        if url is None:
            return ""
        u = str(url).split("?", 1)[0]
        p = urlparse(u)
        path = (p.path or "")[:64]
        return f"{p.scheme}://{p.netloc}{path}"[:200]
    except Exception:
        return "unavailable"


def _log_openai_connection_error_details(exc: BaseException) -> None:
    """Zusätzliche, sanitisierte Diagnose bei Verbindungs-/Timeout-Fehlern (keine Secrets)."""
    if not openai or not isinstance(exc, openai.APIConnectionError):
        return
    req = getattr(exc, "request", None)
    has_req = req is not None
    has_resp = getattr(exc, "response", None) is not None
    parts = [
        f"type={type(exc).__name__}",
        f"has_request={has_req}",
        f"has_response={has_resp}",
    ]
    if has_req:
        parts.append(f"request_meta={_safe_request_url_meta(req)}")
    cause = exc.__cause__
    if cause is not None:
        parts.append(f"cause_type={type(cause).__name__}")
        parts.append(f"cause_repr={_sanitize_openai_text(repr(cause), max_len=280)}")
    ctx = exc.__context__
    if ctx is not None and ctx is not cause:
        parts.append(f"context_type={type(ctx).__name__}")
        parts.append(f"context_repr={_sanitize_openai_text(repr(ctx), max_len=280)}")
    logger.error("OpenAI connection diagnostics: %s", " ".join(parts))

_SECRET_PATTERNS = (
    # Maskierte oder kurze sk-...-Fragmente (OpenAI liefert z. B. sk-inval***0000)
    (re.compile(r"sk-[A-Za-z0-9_*.-]{4,}"), "[REDACTED_KEY]"),
    (re.compile(r"(?i)Bearer\s+[A-Za-z0-9._+=-]{12,}"), "Bearer [REDACTED]"),
    (re.compile(r"(?i)(api[_-]?key|authorization)\s*[:=]\s*[^\s\"']{8,}"), r"\1=[REDACTED]"),
)


def _sanitize_openai_text(text: str, max_len: int = 200) -> str:
    """Strip likely secrets and truncate for logs and client-facing warnings."""
    if not text:
        return ""
    t = text.replace("\n", " ").replace("\r", " ").strip()
    for pattern, repl in _SECRET_PATTERNS:
        t = pattern.sub(repl, t)
    if len(t) > max_len:
        t = t[: max_len - 3].rstrip() + "..."
    return t


def _extract_first_json_object(text: str) -> str:
    """
    Best-effort JSON repair: extract the first top-level {...} object substring.
    Returns "" if no plausible object found.
    """
    if not text:
        return ""
    s = text.strip()
    start = s.find("{")
    if start < 0:
        return ""
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(s)):
        ch = s[i]
        if in_str:
            if esc:
                esc = False
                continue
            if ch == "\\":
                esc = True
                continue
            if ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
            continue
        if ch == "{":
            depth += 1
            continue
        if ch == "}":
            depth -= 1
            if depth == 0:
                return s[start : i + 1].strip()
            continue
    return ""


def _parse_llm_json_object(value: object) -> dict:
    """
    Strictly prefer dict; otherwise parse JSON (with a small repair attempt).
    Raises ValueError/JSONDecodeError for unrepairable input.
    """
    if isinstance(value, dict):
        return value
    text = str(value or "").strip()
    if not text:
        raise ValueError("Empty LLM response")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        repaired = _extract_first_json_object(text)
        if not repaired:
            raise
        data = json.loads(repaired)
    if not isinstance(data, dict):
        raise ValueError(f"Invalid response format (expected object, got {type(data).__name__})")
    return data


def _openai_max_tokens_for_expansion(model: str, target_word_count: int) -> int:
    """
    Choose a sensible max_tokens budget for the expansion pass.
    Must be conservative for small-context models (e.g. gpt-3.5-turbo),
    but allow more headroom for newer models to reach ~1200-1500 words.
    """
    m = (model or "").lower().strip()
    # Heuristic: 1 word ~ 0.75 tokens (very rough). Add JSON overhead headroom.
    desired = int(target_word_count * 1.15) + 1200
    if "gpt-3.5" in m:
        # Keep below typical small-context limits to avoid hard failures.
        return max(2200, min(3000, desired))
    if "gpt-4o-mini" in m or "gpt-4o" in m or "gpt-4" in m:
        return max(3800, min(6500, desired))
    return max(2500, min(4500, desired))


SCRIPT_TARGET_WORDS_PER_MINUTE = 128


def target_word_count_for_duration_minutes(duration_minutes: int) -> int:
    """Voiceover-oriented target words; calibrated from ElevenLabs live smoke runs."""
    minutes = max(1, int(duration_minutes))
    return max(1, int(round(minutes * SCRIPT_TARGET_WORDS_PER_MINUTE)))


def _openai_nested_error_message(body: object) -> str:
    if not isinstance(body, dict):
        return ""
    err = body.get("error")
    if isinstance(err, dict):
        msg = err.get("message")
        if msg:
            return str(msg)
    return ""


def _coerce_openai_error_text(exc: BaseException) -> str:
    """Prefer API body JSON message; strip noisy client wrappers."""
    raw = ""
    if openai and isinstance(exc, openai.APIError):
        raw = _openai_nested_error_message(exc.body) or getattr(exc, "message", "") or str(exc)
    else:
        raw = getattr(exc, "message", "") or str(exc)
    m = re.match(r"Error code:\s*\d+\s*-\s*", raw)
    if m:
        raw = raw[m.end() :].strip()
    inner = _openai_nested_error_message_from_text(raw)
    return inner or raw


def _openai_nested_error_message_from_text(blob: str) -> str:
    """Best-effort: pull error.message from a stringified dict (when body wasn't parsed)."""
    if not blob or "message" not in blob:
        return ""
    m = re.search(r"['\"]message['\"]\s*:\s*['\"]([^'\"]{1,500})['\"]", blob)
    if m:
        return m.group(1)
    return ""


def _openai_error_summary(exc: BaseException) -> Tuple[str, str]:
    """
    Build (log_line, public_reason) for OpenAI errors.
    public_reason is safe to surface in API warnings (sanitized, no secrets).
    """
    cls = type(exc).__name__
    status = getattr(exc, "status_code", None)
    if status is None and getattr(exc, "response", None) is not None:
        try:
            status = exc.response.status_code
        except Exception:
            status = None

    raw = _coerce_openai_error_text(exc)

    safe = _sanitize_openai_text(raw, max_len=220)
    req_id = getattr(exc, "request_id", None) if openai and isinstance(exc, openai.APIStatusError) else None
    err_type = getattr(exc, "type", None) if openai and isinstance(exc, openai.APIError) else None
    code = getattr(exc, "code", None) if openai and isinstance(exc, openai.APIError) else None

    log_parts = [f"{cls}"]
    if status is not None:
        log_parts.append(f"status={status}")
    if err_type:
        log_parts.append(f"type={err_type}")
    if code:
        log_parts.append(f"code={code}")
    if req_id:
        log_parts.append(f"request_id={req_id}")
    log_parts.append(f"message={safe or '[no message]'}")

    log_line = " ".join(log_parts)

    if status is not None and safe:
        public = f"{cls} HTTP {status}: {safe}"
    elif status is not None:
        public = f"{cls} HTTP {status}"
    elif safe:
        public = f"{cls}: {safe}"
    else:
        public = cls

    return log_line, public


def extract_text_from_url(url: str) -> Tuple[str, List[str]]:
    """Extract text from news URL or YouTube transcript. Returns text and warnings."""
    warnings = []
    if "youtube.com" in url or "youtu.be" in url:
        text = extract_youtube_transcript(url)
    else:
        text, site_warnings = extract_news_text(url)
        warnings.extend(site_warnings)
    return text, warnings

def extract_news_text(url: str) -> Tuple[str, List[str]]:
    """Extract text from news article. Returns text and warnings."""
    warnings = []
    try:
        downloaded = trafilatura.fetch_url(url)
        text = trafilatura.extract(downloaded)
        if not text:
            return "", warnings
        
        # Check if it's a homepage
        if is_homepage(url):
            warnings.append("URL appears to be a homepage or index page. Use a specific article URL for better results.")
        
        # Clean the text
        text = clean_extracted_text(text)
        
        # Check if text is too short or generic
        if len(text.strip()) < 500:
            warnings.append("Extracted content is very short. The URL may not contain sufficient article text.")
        
        return text, warnings
    except Exception as e:
        logger.error(f"Error extracting news text: {e}")
        return "", warnings

def is_homepage(url: str) -> bool:
    """Check if URL appears to be a homepage or section/index page."""
    parsed = urlparse(url)
    path = parsed.path.strip('/').lower()
    if not path:
        return True
    if path in ['index', 'index.html', 'home', 'start', 'default']:
        return True
    if path.endswith('index.html'):
        return True

    # Treat direct article files as article URLs, not homepages.
    if path.endswith('.html') and '/' in path:
        return False
    if '/artikel/' in path or '/meldung/' in path or '/news/' in path:
        return False

    # Specific site heuristics for tagesschau
    if 'tagesschau.de' in parsed.netloc:
        # Section pages like /inland/, /ausland/, /wirtschaft/ are not articles
        section_roots = {
            'inland', 'ausland', 'wirtschaft', 'politik', 'finanzen', 'ratgeber',
            'sport', 'wissen', 'kultur', 'digital', 'gesundheit', 'service', 'wirtschaft'
        }
        first_segment = path.split('/')[0]
        if first_segment in section_roots and len(path.split('/')) == 1:
            return True
        if first_segment in section_roots and path.count('/') == 1 and not path.endswith('.html'):
            return True

    return False

def clean_extracted_text(text: str) -> str:
    """Clean extracted text by removing noise."""
    lines = text.split('\n')
    cleaned_lines = []
    noise_keywords = [
        'inhalte zeigen von',
        'externe anbieter',
        'mehr',
        'datenschutz',
        'cookie',
        'navigation',
        'social media',
        'folgen sie uns',
        'teilen',
        'kommentare',
        'anzeige',
        'werbung',
        'newsletter',
        'abonnieren'
    ]
    
    for line in lines:
        line_lower = line.lower().strip()
        if not any(keyword in line_lower for keyword in noise_keywords):
            # Also skip very short lines or lines with many non-alphabetic chars
            if len(line.strip()) > 10 and sum(c.isalpha() for c in line) / len(line) > 0.3:
                cleaned_lines.append(line.strip())
    
    return '\n'.join(cleaned_lines).strip()

def count_words(text: str) -> int:
    """Count words in text."""
    return len(text.split())

def extract_youtube_transcript(url: str) -> str:
    """Extract transcript from YouTube video (watch, youtu.be, shorts)."""
    vid = extract_video_id(url)
    if not vid:
        return ""
    return fetch_youtube_transcript_by_video_id(vid)


def _joined_transcript_text(fetched) -> str:
    """Build plain text from FetchedTranscript (snippets with .text)."""
    try:
        return " ".join(
            getattr(s, "text", "") or ""
            for s in fetched
            if getattr(s, "text", "")
        )
    except Exception:
        return ""


def fetch_youtube_transcript_by_video_id(video_id: str) -> str:
    """
    Fetch caption text for a video id via youtube-transcript-api (no Data API).
    Tries preferred languages first, then any available track.
    Compatible with youtube-transcript-api instance API (fetch/list).
    """
    if not video_id:
        return ""
    api = YouTubeTranscriptApi()
    try:
        fetched = api.fetch(
            video_id, languages=["de", "en", "en-US", "en-GB"]
        )
        text = _joined_transcript_text(fetched)
        if text.strip():
            return text
    except Exception as first_exc:
        logger.info(
            "Primary transcript fetch failed for video_id=%s: %s",
            video_id,
            type(first_exc).__name__,
        )
    try:
        transcript_list = api.list(video_id)
        for tr in transcript_list:
            try:
                fetched = tr.fetch()
                text = _joined_transcript_text(fetched)
                if text.strip():
                    return text
            except Exception:
                continue
    except Exception as e:
        logger.info(
            "Transcript listing failed for video_id=%s: %s",
            video_id,
            type(e).__name__,
        )
    return ""


WARN_TRANSCRIPT_UNAVAILABLE = "Transcript not available for this video."


def check_youtube_transcript_available_by_video_id(
    video_id: str,
) -> Tuple[bool, List[str]]:
    """
    Prüft, ob für ein Video ein Untertitel-/Transkript-Text abrufbar ist — ohne dauerhafte
    Speicherung von Rohtranskripten und ohne Transkripttext zu loggen.

    Nutzt dieselbe Abruflogik wie ``fetch_youtube_transcript_by_video_id`` /
    ``generate_script_from_youtube_video``.
    """
    warnings: List[str] = []
    vid = (video_id or "").strip()
    if not vid:
        warnings.append("Could not parse a YouTube video id.")
        return False, warnings
    try:
        text = fetch_youtube_transcript_by_video_id(vid)
        if (text or "").strip():
            return True, []
        warnings.append(WARN_TRANSCRIPT_UNAVAILABLE)
        return False, warnings
    except Exception as e:
        logger.info(
            "Transcript availability check failed for video_id=%s: %s",
            vid,
            type(e).__name__,
        )
        warnings.append(
            "Transcript availability could not be verified (technical error)."
        )
        return False, warnings


def extract_video_id(url: str) -> str:
    """Extract YouTube video ID from watch, youtu.be, shorts, or embed URLs."""
    raw = (url or "").strip()
    if not raw:
        return ""
    parsed = urlparse(raw)
    host = (parsed.hostname or "").lower().rstrip(".")
    path = (parsed.path or "").strip("/")

    if host == "youtu.be":
        part = path.split("/")[0] if path else ""
        return _normalize_video_id(part)

    if host in ("www.youtube.com", "youtube.com", "m.youtube.com", "www.youtube-nocookie.com"):
        if path.startswith("watch") or path == "watch":
            qs = parse_qs(parsed.query)
            v = (qs.get("v") or [""])[0]
            return _normalize_video_id(v.split("&")[0] if v else "")
        if path.startswith("shorts/"):
            part = path.split("/", 1)[1].split("/")[0] if "/" in path else ""
            return _normalize_video_id(part.split("?")[0])
        if path.startswith("embed/"):
            part = path.split("/", 1)[1].split("/")[0] if "/" in path else ""
            return _normalize_video_id(part.split("?")[0])
        if path.startswith("live/"):
            part = path.split("/", 1)[1].split("/")[0] if "/" in path else ""
            return _normalize_video_id(part.split("?")[0])

    return ""


def _normalize_video_id(fragment: str) -> str:
    """Keep typical 11-char YouTube ids; strip query junk."""
    if not fragment:
        return ""
    vid = fragment.strip()
    if "&" in vid:
        vid = vid.split("&", 1)[0]
    m = re.match(r"^([A-Za-z0-9_-]{11})", vid)
    if m:
        return m.group(1)
    return ""


def build_script_response_from_extracted_text(
    *,
    extracted_text: str,
    source_url: str,
    target_language: str,
    duration_minutes: int,
    extraction_warnings: Optional[List[str]] = None,
    extra_warnings: Optional[List[str]] = None,
    video_template: str = "generic",
    template_conformance_level: str = "warn",
) -> Tuple[str, str, List[dict], str, List[str], List[str]]:
    """
    Shared pipeline: summarized/structured script from plain text (article or transcript).
    Returns title, hook, chapters (dicts), full_script, sources, warnings.
    """
    warnings: List[str] = list(extraction_warnings or [])
    if extra_warnings:
        warnings.extend(extra_warnings)

    tpl_id, tpl_ws = normalize_story_template_id(video_template)
    warnings.extend(tpl_ws)

    summary = summarize_text(extracted_text, sentences_count=20)

    if target_language == "de":
        translated = translate_to_german(summary)
    else:
        translated = summary

    key_points = extract_key_points(translated)
    title = generate_title(translated)
    source_word_count = count_words(translated)

    generator = ScriptGenerator()
    title, hook, chapters, full_script, mode, reason = generator.generate_script(
        title,
        key_points,
        duration_minutes,
        source_word_count,
        video_template=tpl_id,
    )

    sources = [source_url]
    target_word_count = target_word_count_for_duration_minutes(duration_minutes)
    script_for_count = full_script
    if not (script_for_count or "").strip():
        parts = [hook]
        for ch in chapters or []:
            if isinstance(ch, dict):
                parts.append(str(ch.get("title") or ""))
                parts.append(str(ch.get("content") or ""))
        script_for_count = "\n\n".join(p for p in parts if str(p or "").strip())
    actual_word_count = count_words(script_for_count)
    warnings.append(f"Target word count: {target_word_count}, Actual word count: {actual_word_count}")
    if actual_word_count < target_word_count * 0.75:
        warnings.append("script_below_target_after_expansion")
        warnings.append("duration_target_unreachable_due_to_short_script")
        if target_word_count >= 512:
            warnings.append("longform_expansion_below_target")
    if actual_word_count < target_word_count * 0.5:
        warnings.append(
            "Script is significantly shorter than target. Content may be insufficient for the requested duration."
        )
    if len(script_for_count) < 500:
        warnings.append("Script may be too short for 10-minute video")

    fallback_note = (
        "Fallback mode: script is condensed from the source and not artificially lengthened; "
        "duration target may be missed to avoid repeating the source text."
    )
    if mode == "llm":
        warnings.append("Generated using LLM mode")
        if reason:
            warnings.append(reason)
    elif reason:
        r = reason.rstrip(".")
        warnings.append(f"LLM generation failed: {r}. {fallback_note}")
    else:
        warnings.append(fallback_note)

    cw, _ = apply_template_conformance(
        template_conformance_level=template_conformance_level,
        template_id=tpl_id,
        hook=hook,
        chapters=chapters,
        full_script=full_script,
        duration_minutes=duration_minutes,
    )
    warnings.extend(cw)

    return title, hook, chapters, full_script, sources, warnings


def generate_script_from_youtube_video(
    video_url: str,
    target_language: str = "de",
    duration_minutes: int = 10,
    video_template: str = "generic",
    template_conformance_level: str = "warn",
):
    """
    Gleiche fachliche Pipeline wie ``POST /youtube/generate-script``, ohne HTTP.
    Liefert immer ``GenerateScriptResponse`` — keine Exceptions bei erwartbaren Transcript-Problemen.
    """
    from app.models import GenerateScriptResponse

    transcript_warning = (
        "Quelle: YouTube-Untertitel/Transkript; das Skript ist eine eigenständige "
        "deutschsprachige Story-Formulierung, keine wörtliche Abschrift."
    )
    try:
        video_id = extract_video_id(video_url)
        if not video_id:
            return GenerateScriptResponse(
                title="",
                hook="",
                chapters=[],
                full_script="",
                sources=[],
                warnings=[
                    "Could not parse a YouTube video id from video_url.",
                ],
            )

        canonical_url = f"https://www.youtube.com/watch?v={video_id}"
        transcript = fetch_youtube_transcript_by_video_id(video_id)
        if not (transcript or "").strip():
            return GenerateScriptResponse(
                title="",
                hook="",
                chapters=[],
                full_script="",
                sources=[canonical_url],
                warnings=[WARN_TRANSCRIPT_UNAVAILABLE],
            )

        title, hook, chapters, full_script, sources, warnings = (
            build_script_response_from_extracted_text(
                extracted_text=transcript,
                source_url=canonical_url,
                target_language=target_language,
                duration_minutes=duration_minutes,
                extraction_warnings=[],
                extra_warnings=[transcript_warning],
                video_template=video_template,
                template_conformance_level=template_conformance_level,
            )
        )

        return GenerateScriptResponse(
            title=title,
            hook=hook,
            chapters=chapters,
            full_script=full_script,
            sources=sources,
            warnings=warnings,
        )
    except Exception as e:
        logger.error(
            "generate_script_from_youtube_video failed: %s message=%s",
            type(e).__name__,
            str(e)[:300],
        )
        return GenerateScriptResponse(
            title="",
            hook="",
            chapters=[],
            full_script="",
            sources=[],
            warnings=[
                "Die Anfrage konnte nicht vollständig verarbeitet werden. "
                f"Technischer Hinweis: {type(e).__name__}.",
            ],
        )


def build_script_dict_from_youtube_source(
    *,
    source_youtube_url: str,
    duration_minutes: int,
    target_language: str = "de",
    video_template: str = "generic",
    template_conformance_level: str = "warn",
    rewrite_style: Optional[str] = None,
) -> Tuple[Optional[Dict[str, Any]], bool, List[str], List[str]]:
    """
    BA 32.58 — Transkript → neues Skript (kein 1:1-Transkript; gleiche Pipeline wie /youtube/generate-script).

    Rückgabe: ``(script_dict | None, transcript_available, warnings, blocking_reasons)``.
    """
    blocking: List[str] = []
    warns: List[str] = []
    raw_u = (source_youtube_url or "").strip()
    if not raw_u:
        return None, False, warns, ["youtube_transcript_missing"]

    video_id = extract_video_id(raw_u)
    if not video_id:
        return None, False, warns, ["youtube_url_invalid"]

    transcript = fetch_youtube_transcript_by_video_id(video_id)
    transcript_ok = bool((transcript or "").strip())
    if not transcript_ok:
        warns.extend(["transcript_missing", "youtube_transcript_unavailable"])
        return None, False, warns, ["youtube_transcript_missing"]

    canonical_url = f"https://www.youtube.com/watch?v={video_id}"
    extra = [
        "youtube_source_rewrite_used",
        "transcript_used_as_source_material",
        "Quelle: YouTube-Untertitel/Transkript; das Skript ist eine eigenständige "
        "deutschsprachige Story-Formulierung, keine wörtliche Abschrift.",
    ]
    rs = (rewrite_style or "").strip()
    if rs:
        extra.append(f"youtube_rewrite_style:{rs}")

    title, hook, chapters, full_script, sources, gen_warns = build_script_response_from_extracted_text(
        extracted_text=transcript,
        source_url=canonical_url,
        target_language=target_language,
        duration_minutes=max(1, int(duration_minutes)),
        extraction_warnings=[],
        extra_warnings=extra,
        video_template=video_template,
        template_conformance_level=template_conformance_level,
    )
    warns.extend(list(gen_warns or []))
    script: Dict[str, Any] = {
        "title": title,
        "hook": hook,
        "chapters": chapters,
        "full_script": full_script,
        "sources": list(sources or []),
        "warnings": warns,
    }
    return script, True, warns, blocking


def summarize_text(text: str, sentences_count: int = 10) -> str:
    """Summarize text using LSA."""
    try:
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = LsaSummarizer()
        summary = summarizer(parser.document, sentences_count)
        return " ".join([str(sentence) for sentence in summary])
    except LookupError:
        logger.warning("NLTK tokenizer data not found, using simple fallback summarization")
        # Fallback: return first N sentences
        sentences = re.split(r'[.!?]+', text)
        summary_sentences = sentences[:sentences_count]
        return " ".join(summary_sentences).strip()
    except Exception as e:
        logger.error(f"Error summarizing text: {e}")
        return text[:1000]  # Fallback

def translate_to_german(text: str) -> str:
    """Translate text to German."""
    try:
        translator = GoogleTranslator(source='auto', target='de')
        return translator.translate(text)
    except Exception as e:
        logger.error(f"Error translating text: {e}")
        return text

def extract_key_points(text: str) -> List[str]:
    """Extract key points from text."""
    # Simple sentence splitting
    sentences = re.split(r'[.!?]+', text)
    return [s.strip() for s in sentences if len(s.strip()) > 20][:10]

class ScriptGenerator:
    """Generator for video scripts with fallback options."""
    
    def generate_script(
        self,
        title: str,
        key_points: List[str],
        duration_minutes: int,
        source_word_count: int = 0,
        *,
        video_template: str = "generic",
    ) -> Tuple[str, str, List[dict], str, str, str]:
        """Generate script structure based on duration. Returns title, hook, chapters, full_script, mode, reason."""
        tid, _ = normalize_story_template_id(video_template)
        target_word_count = target_word_count_for_duration_minutes(duration_minutes)
        min_word_count = max(int(target_word_count * 0.85), 200)
        max_word_count = int(target_word_count * 1.15)
        
        # Determine number of chapters based on duration; clamp to template blueprint band (BA 9.1)
        if duration_minutes <= 6:
            num_chapters = 4
        elif duration_minutes <= 10:
            num_chapters = 6
        else:
            num_chapters = 8
        low, high = chapter_band_for_template_duration(tid, duration_minutes)
        num_chapters = max(low, min(high, num_chapters))
        if openai and _effective_openai_api_key():
            return self._generate_with_openai(
                title,
                key_points,
                duration_minutes,
                target_word_count,
                num_chapters,
                min_word_count,
                max_word_count,
                source_word_count,
                video_template=tid,
            )
        return self._generate_fallback(
            title,
            key_points,
            duration_minutes,
            target_word_count,
            num_chapters,
            min_word_count,
            max_word_count,
            source_word_count,
            video_template=tid,
        )
    
    def _generate_with_openai(
        self,
        title: str,
        key_points: List[str],
        duration_minutes: int,
        target_word_count: int,
        num_chapters: int,
        min_word_count: int,
        max_word_count: int,
        source_word_count: int,
        *,
        video_template: str = "generic",
    ) -> Tuple[str, str, List[dict], str, str, str]:
        """Generate script using OpenAI."""
        try:
            source_note = "" if source_word_count >= target_word_count else (
                "Die Quelle enthält weniger Text als die gewünschte Dauer. Bitte ergänze das Skript mit zusätzlicher Kontext-Einordnung und Analyse, ohne neue Fakten zu erfinden.")
            addon = story_template_prompt_addon_de(video_template)
            addon_block = f"\n\nFormat-Vorgaben (zusätzlich):\n{addon}\n" if addon else ""
            bp = story_template_blueprint_prompt_de(video_template, duration_minutes)
            if bp:
                addon_block += f"\nStruktur-Blueprint (Orientierung):\n{bp}\n"
            prompt = f"""
Erstelle ein YouTube-Video-Skript auf Deutsch aus den bereitgestellten Informationen.

Titel: {title}
Key Points: {'; '.join(key_points)}

Ziel:
- Dauer: {duration_minutes} Minuten
- Zielwortanzahl: {target_word_count} Wörter
- Mindestwortanzahl: {min_word_count} Wörter
- Maximalwortanzahl: {max_word_count} Wörter
- Kapitel: {num_chapters}

{source_note}
{addon_block}
Laengen-Regie:
- Die Zielwortanzahl ist verbindlich: Schreibe nahe {target_word_count} Woerter und mindestens {min_word_count} Woerter.
- Eine Antwort unter {min_word_count} Woertern gilt als zu kurz und muss vor der Ausgabe erweitert werden.
- Kein Telegrammstil: Jeder Hauptpunkt braucht mehrere erklaerende Saetze, klare Uebergaenge und gesprochenen Kontext.
- Bei YouTube-Transkripten oder Quelltexten: vorhandenes Material ausfuehrlicher paraphrasieren und einordnen, ohne neue Fakten zu erfinden.
- Wenn die Quelle knapp ist: erklaere Bedeutung, Kontext, Unsicherheiten und moegliche Folgen vorsichtig, statt neue Details zu behaupten.
- Schreibe das `full_script` als echten Sprechertext; Kapitelinhalte duerfen nicht nur Stichpunkte sein.

Baue folgende Struktur ein:
1. Ein starker Hook
2. Ein kurzes Intro
3. {num_chapters} Kapitel mit klaren Titeln und ausführlichem Inhalt
4. Kontext und Einordnung
5. Analyse oder Bewertung
6. Offene Fragen oder zukünftige Entwicklung
7. Fazit
8. Call-to-Action

Antworte nur mit gültigem JSON, ohne zusätzlichen Text, Codeblöcke oder Markdown.
Gib die Antwort exakt als Objekt zurück:
{{
    "title": "Video-Titel",
    "hook": "Hook text",
    "chapters": [{{"title": "Kapitel 1: Titel", "content": "Inhalt"}}],
    "full_script": "Vollständiges Skript"
}}
"""
            with build_openai_client() as client:
                response = client.chat.completions.create(
                    model=settings.openai_model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=3000,
                    temperature=0.0,
                    response_format={"type": "json_object"},
                )

            result = response.choices[0].message.content
            data = _parse_llm_json_object(result)
            
            title_text = data.get("title") or title
            hook = data.get("hook") or f"Entdecken Sie: {title_text}"
            chapters = data.get("chapters") if isinstance(data.get("chapters"), list) else []
            full_script = data.get("full_script") or data.get("script") or ""
            if not str(full_script).strip() and chapters:
                parts = [str(hook or "").strip()]
                for ch in chapters:
                    if isinstance(ch, dict):
                        parts.append(str(ch.get("title") or "").strip())
                        parts.append(str(ch.get("content") or "").strip())
                full_script = "\n\n".join(p for p in parts if p)
            
            full_script_words = count_words(full_script)
            if full_script_words >= min_word_count:
                return title_text, hook, chapters, full_script, "llm", ""

            # Valid LLM JSON, but clearly too short: do NOT fallback.
            # Instead, run a second expansion pass that extends the existing script toward target length.
            expanded = self._expand_llm_script_with_openai(
                title=title_text,
                key_points=key_points,
                duration_minutes=duration_minutes,
                target_word_count=target_word_count,
                min_word_count=min_word_count,
                max_word_count=max_word_count,
                current_hook=hook,
                current_chapters=chapters,
                current_full_script=full_script,
            )
            if expanded:
                ex_title, ex_hook, ex_chapters, ex_full = expanded
                before = full_script_words
                after = count_words(ex_full)

                # If still very short, allow one more expansion attempt (max 2 expansion calls total).
                # Never fallback just due to shortness.
                if after > before and after < min_word_count:
                    expanded2 = self._expand_llm_script_with_openai(
                        title=ex_title or title_text,
                        key_points=key_points,
                        duration_minutes=duration_minutes,
                        target_word_count=target_word_count,
                        min_word_count=min_word_count,
                        max_word_count=max_word_count,
                        current_hook=ex_hook or hook,
                        current_chapters=ex_chapters if isinstance(ex_chapters, list) else chapters,
                        current_full_script=ex_full,
                    )
                    if expanded2:
                        ex2_title, ex2_hook, ex2_chapters, ex2_full = expanded2
                        after2 = count_words(ex2_full)
                        if after2 > after:
                            ex_title, ex_hook, ex_chapters, ex_full, after = (
                                ex2_title,
                                ex2_hook,
                                ex2_chapters,
                                ex2_full,
                                after2,
                            )

                # Accept only if it materially improves length/coverage and stays roughly within bounds.
                if after > before and after <= int(max_word_count * 1.25) and (
                    after >= min_word_count or after >= int(before * 1.15) or abs(target_word_count - after) < abs(target_word_count - before)
                ):
                    if after < min_word_count:
                        repaired_ex_full = self._deterministic_length_repair(
                            current_full_script=ex_full,
                            key_points=key_points,
                            target_word_count=target_word_count,
                            min_word_count=min_word_count,
                            max_word_count=max_word_count,
                        )
                        repaired_ex_words = count_words(repaired_ex_full)
                        if repaired_ex_words > after:
                            reason = (
                                "LLM longform expansion repaired toward target length"
                                if target_word_count >= 512 and repaired_ex_words >= min_word_count
                                else "LLM expansion repaired toward target length"
                            )
                            if repaired_ex_words < min_word_count:
                                reason = "LLM expansion still below target"
                            return (
                                ex_title or title_text,
                                ex_hook or hook,
                                ex_chapters if isinstance(ex_chapters, list) else chapters,
                                repaired_ex_full,
                                "llm",
                                reason,
                            )
                    if after < min_word_count:
                        reason = "LLM expansion still below target"
                    else:
                        reason = "LLM script expanded toward target length"
                    return (
                        ex_title or title_text,
                        ex_hook or hook,
                        ex_chapters if isinstance(ex_chapters, list) else chapters,
                        ex_full,
                        "llm",
                        reason,
                    )

            repaired_full = self._deterministic_length_repair(
                current_full_script=full_script,
                key_points=key_points,
                target_word_count=target_word_count,
                min_word_count=min_word_count,
                max_word_count=max_word_count,
            )
            repaired_words = count_words(repaired_full)
            if repaired_words > full_script_words:
                if repaired_words < min_word_count:
                    reason = "LLM output shorter than target; deterministic repair still below target"
                else:
                    reason = "LLM output expanded with deterministic safe repair"
                return title_text, hook, chapters, repaired_full, "llm", reason

            logger.warning(
                "LLM output below minimum word band (%s words, min=%s); expansion not applied",
                full_script_words,
                min_word_count,
            )
            return title_text, hook, chapters, full_script, "llm", "LLM output shorter than target"
        
        except openai.OpenAIError as e:
            _log_openai_connection_error_details(e)
            log_line, sanitized_reason = _openai_error_summary(e)
            logger.error("OpenAI request failed: %s", log_line)
        except json.JSONDecodeError as e:
            logger.error("OpenAI JSON parse error: %s message=%s", type(e).__name__, str(e)[:300])
            sanitized_reason = "Invalid response format (JSON)"
        except Exception as e:
            safe = _sanitize_openai_text(str(e), max_len=200)
            logger.error("OpenAI generation failed: %s message=%s", type(e).__name__, safe or str(type(e).__name__))
            sanitized_reason = f"{type(e).__name__}" + (f": {safe}" if safe else "")
        
        logger.info("Falling back to local generation")
        _, hook, chapters, full_script, _, _ = self._generate_fallback(
            title,
            key_points,
            duration_minutes,
            target_word_count,
            num_chapters,
            min_word_count,
            max_word_count,
            source_word_count,
            video_template=video_template,
        )
        return title, hook, chapters, full_script, "fallback", sanitized_reason

    def _expand_llm_script_with_openai(
        self,
        *,
        title: str,
        key_points: List[str],
        duration_minutes: int,
        target_word_count: int,
        min_word_count: int,
        max_word_count: int,
        current_hook: str,
        current_chapters: List[dict],
        current_full_script: str,
    ) -> Optional[Tuple[str, str, List[dict], str]]:
        """
        Second-pass expansion: keep the existing script as baseline, deepen chapters and add context/analysis
        without inventing new factual claims. Never triggers fallback; returns None on any failure.
        """
        if not (openai and _effective_openai_api_key()):
            return None
        try:
            chapters_json = json.dumps(current_chapters or [], ensure_ascii=False)
        except Exception:
            chapters_json = "[]"

        current_words = count_words(current_full_script or "")
        target_min_words = max(1, int(min_word_count))
        target_max_words = max(int(max_word_count), int(target_word_count))
        missing_to_min = max(0, target_min_words - current_words)
        # Ask for concrete NEW text. Short videos must stay near their real target
        # instead of aiming for long-form filler that later fails the word-band guard.
        if target_word_count <= 400:
            desired_new_words = max(60, min(260, missing_to_min + 60))
        else:
            desired_new_words = max(120, min(900, missing_to_min + 160))

        expansion_prompt = f"""
Du bist Redaktions- und Story-Producer für ein YouTube-News-Video.
Erweitere das bestehende Skript gezielt und deutlich Richtung Ziel-Länge, ohne neue unbelegte Fakten zu erfinden.

WICHTIG:
- Du darfst NICHT kürzen. Das bestehende Skript bleibt vollständig erhalten; du fügst neue Passagen hinzu, ordnest um und glättest Übergänge.
- Wenn du umstrukturierst, stelle sicher, dass der Inhalt insgesamt länger wird (nicht nur umformuliert).
- Keine neuen konkreten Behauptungen/Details hinzufügen, die nicht aus den Key Points oder dem vorhandenen Skript ableitbar sind.
- Wenn du Kontext gibst, formuliere ihn als Einordnung/Erklärung/Allgemeinwissen, ohne neue Ereignis-Fakten zu behaupten.
- Keine Wiederholungen: vermeide doppelte Aussagen, wiederholte Hooks/CTAs und redundante Formulierungen.
- Keine 1:1-Übernahmen aus Quellen oder aus dem bestehenden Skript: paraphrasiere und baue neue Übergänge/Moderation ein.
- Vertiefe bestehende Kapitel: mehr Erklärung, Einordnung, Konsequenzen, Pro/Contra-Abwägung, offene Fragen, aber ohne Fakten zu erfinden.
- Mehr Sprechertext: klare Übergänge zwischen Kapiteln, kurze Zusammenfassungen, Einordnung, warum es wichtig ist.
- Ergänze Kontext/Definitionen (z. B. was eine Regel/Verordnung bedeutet) nur als Erklärung, nicht als neue Nachricht.
- Behalte Stil und Sprache: Deutsch, YouTube-tauglich.

Ziel (konkret):
- Dauer: {duration_minutes} Minuten
- Zielwortanzahl (Plan): {target_word_count}
- Mindestwortanzahl: {min_word_count}
- Maximalwortanzahl: {max_word_count}
- Aktuelle Wortanzahl (IST): {current_words}
- Fehlende Wörter bis mindestens {target_min_words}: {missing_to_min}
- Zielbereich fürs finale Skript: {target_min_words}–{target_max_words} Wörter

KLARE ANWEISUNG:
- Erweitere das Skript auf **mindestens {target_min_words} Wörter** (besser: nahe {target_word_count} und im Bereich {target_min_words}–{target_max_words}).
- Fuege etwa {desired_new_words} neue Woerter hinzu, sofern du das ohne neue Fakten und ohne Wiederholungen sauber kannst.
- Das finale Skript soll nahe {target_word_count} Woerter landen; vermeide sowohl Unterlaenge als auch kuenstliche Ueberlaenge.
- Nutze dafür vor allem: Übergänge, Moderation, Einordnung, Definitionen, „Warum ist das relevant?“, mögliche Konsequenzen, Abwägungen, offene Fragen, Fazit, CTA.
- Wenn das nicht sauber möglich ist, bleibe so nah wie möglich am Zielbereich und markiere Unsicherheiten indirekt durch vorsichtige Formulierungen (ohne Fakten zu erfinden).

Ausgabe-Qualität:
- `full_script` soll wie ein gesprochenes Skript wirken (Sprechertext), mit Absätzen und klaren Übergängen.
- Baue nach jedem Kapitel 2–4 Sätze Überleitung ein (ohne Wiederholung des Kapitels).
- Ergänze am Ende ein klares Fazit + Call-to-Action (ohne den Hook zu wiederholen).
- Ergänze zusätzlich 2–3 kurze Blöcke zur Einordnung, z. B.: „Was heißt das praktisch?“, „Warum ist das politisch/gesellschaftlich relevant?“, „Welche Fragen sind offen?“

Key Points (Fakten-Anker, keine neuen Fakten hinzufügen):
{'; '.join([p for p in key_points if p.strip()])}

Bestehendes Skript (muss als Basis erhalten bleiben, aber darf umstrukturiert/verbessert werden):
Titel: {title}
Hook: {current_hook}
Chapters JSON: {chapters_json}
Full Script:
{current_full_script}

Antworte nur mit gültigem JSON, ohne zusätzlichen Text, Codeblöcke oder Markdown.
Bevorzugtes Ausgabeformat (APPEND, um Kürzungen zu vermeiden):
{{
  "additional_script": "NEUER Sprechertext zum Anhängen (ca. {desired_new_words} zusätzliche Wörter, ohne Wiederholungen)",
  "additional_chapters": [{{"title": "...", "content": "..."}}]
}}
Wenn du unbedingt das komplette Objekt liefern willst, darfst du alternativ dieses Format liefern:
{{
  "title": "...",
  "hook": "...",
  "chapters": [{{"title": "...", "content": "..."}}],
  "full_script": "..."
}}
"""

        with build_openai_client() as client:
            response = client.chat.completions.create(
                model=settings.openai_model,
                messages=[{"role": "user", "content": expansion_prompt}],
                max_tokens=_openai_max_tokens_for_expansion(settings.openai_model, target_word_count),
                temperature=0.0,
                response_format={"type": "json_object"},
            )
        data = _parse_llm_json_object(response.choices[0].message.content)

        # Preferred: append-only
        additional_script = data.get("additional_script") or ""
        additional_chapters = data.get("additional_chapters") if isinstance(data.get("additional_chapters"), list) else []
        if str(additional_script).strip():
            ex_title = title
            ex_hook = current_hook
            ex_chapters = list(current_chapters or [])
            if additional_chapters:
                ex_chapters.extend(additional_chapters)
            ex_full = (current_full_script or "").rstrip() + "\n\n" + str(additional_script).strip()
            return ex_title, ex_hook, ex_chapters, ex_full

        # Fallback: full rewrite object
        ex_title = data.get("title") or title
        ex_hook = data.get("hook") or current_hook
        ex_chapters = data.get("chapters") if isinstance(data.get("chapters"), list) else (current_chapters or [])
        ex_full = data.get("full_script") or data.get("script") or ""
        if not str(ex_full).strip():
            return None
        return ex_title, ex_hook, ex_chapters, str(ex_full)

    def _deterministic_length_repair(
        self,
        *,
        current_full_script: str,
        key_points: List[str],
        target_word_count: int,
        min_word_count: int,
        max_word_count: int,
    ) -> str:
        """Safely add spoken context from existing material when LLM expansion under-shoots."""
        base = str(current_full_script or "").strip()
        if not base:
            return base
        current_words = count_words(base)
        if current_words >= min_word_count:
            return base

        safe_points = [re.sub(r"\s+", " ", str(p or "").strip()) for p in key_points if str(p or "").strip()]
        safe_points = [p for p in safe_points if count_words(p) >= 4][:4]
        if not safe_points:
            safe_points = ["die bereits genannten Punkte aus der Quelle"]

        additions: List[str] = []
        for idx, point in enumerate(safe_points, start=1):
            additions.append(
                "Zur Einordnung: Der vorhandene Quelltext setzt hier vor allem einen Schwerpunkt auf "
                f"{point}. Wichtig ist, diese Aussage nicht isoliert zu betrachten, sondern im Zusammenhang "
                "mit den bereits genannten Punkten zu hören."
            )
            if idx == 1:
                additions.append(
                    "Für die Zuschauerinnen und Zuschauer hilft deshalb ein ruhiger Blick auf die Abfolge: "
                    "Welche Behauptung steht im Raum, welche Reaktion wird beschrieben, und welche Frage "
                    "bleibt danach offen?"
                )
            elif idx == 2:
                additions.append(
                    "Das ist keine neue Behauptung, sondern eine vorsichtige Zusammenfassung der vorhandenen "
                    "Informationen: Erst die Einordnung macht sichtbar, warum der Konflikt für die weitere "
                    "Debatte relevant sein kann."
                )

            candidate = base + "\n\n" + "\n\n".join(additions)
            words = count_words(candidate)
            if words >= min_word_count or words >= target_word_count:
                if words <= int(max_word_count * 1.25):
                    return candidate
                break

        neutral_bridges = [
            (
                "Noch einmal zusammengefasst: Entscheidend ist hier nicht, zusätzliche Details zu behaupten, "
                "sondern die vorhandenen Aussagen sauber zu sortieren. So wird klarer, welche Punkte belegt "
                "aus dem Ausgangsmaterial stammen und wo lediglich offene Fragen für die weitere Debatte bleiben."
            ),
            (
                "Für die Erzählung bedeutet das: Wir bleiben nah am Material, paraphrasieren die bekannten "
                "Aussagen und erklären ihre mögliche Bedeutung vorsichtig. Genau diese Trennung zwischen "
                "Quelle, Einordnung und offener Frage macht das Skript belastbarer."
            ),
            (
                "Am Ende bleibt deshalb vor allem ein Prüfauftrag: Welche Aussage trägt wirklich, welche "
                "Reaktion ist nur eine Interpretation, und welche Punkte müssten mit zusätzlichem Material "
                "weiter überprüft werden?"
            ),
        ]
        for bridge in neutral_bridges:
            additions.append(bridge)
            candidate = base + "\n\n" + "\n\n".join(additions)
            words = count_words(candidate)
            if words >= min_word_count or words >= target_word_count:
                if words <= int(max_word_count * 1.25):
                    return candidate
                break

        candidate = base + "\n\n" + "\n\n".join(additions)
        if count_words(candidate) <= int(max_word_count * 1.25):
            return candidate
        # Keep the repair conservative if the source was already close to the upper band.
        return base

    # NOTE: Use try/except in caller; never bubble expansion errors into fallback.
    
    def _generate_fallback(
        self,
        title: str,
        key_points: List[str],
        duration_minutes: int,
        target_word_count: int,
        num_chapters: int,
        min_word_count: int,
        max_word_count: int,
        source_word_count: int,
        *,
        video_template: str = "generic",
    ) -> Tuple[str, str, List[dict], str, str, str]:
        """Fallback script generation."""
        addon = story_template_prompt_addon_de(video_template)
        hook = f"Entdecken Sie die neuesten Entwicklungen in diesem spannenden Thema: {title}"
        if video_template and video_template != "generic" and addon:
            hook = f"Heute mit Blick auf die Faktenlage: {title}"

        chapters = []
        full_script_parts = [hook]
        intro = (
            "Hallo und herzlich willkommen! In diesem Video ordnen wir das Thema ein — "
            "nachvollziehbar und ohne Spekulation über unbekannte Details."
        )
        if addon:
            first_line = addon.split("\n")[0].strip()
            if first_line:
                intro = (
                    "Hallo und herzlich willkommen! "
                    + first_line
                    + " Wir gehen die bekannten Punkte Schritt für Schritt durch."
                )
        full_script_parts.append(intro)
        
        if not key_points:
            chapter_title = "Einführung"
            chapter_content = (
                "In diesem Video besprechen wir die verfügbaren Fakten und bringen sie in einen größeren Kontext. "
                "Wir erklären, warum das Thema aktuell relevant ist und welche Entwicklungen besonders im Fokus stehen."
            )
            chapters.append({"title": chapter_title, "content": chapter_content})
            full_script_parts.append(f"{chapter_title}\n{chapter_content}")
        else:
            expanded_points = self._expand_key_points(key_points, target_word_count)
            
            points_per_chapter = max(1, len(expanded_points) // num_chapters)
            for i in range(0, len(expanded_points), points_per_chapter):
                chapter_points = expanded_points[i:i + points_per_chapter]
                section_index = len(chapters) + 1
                first_point = chapter_points[0]
                chapter_title = f"Kapitel {section_index}: {first_point.split('.')[0][:90]}"
                chapter_content = self._build_chapter_content(chapter_title, chapter_points)
                chapters.append({"title": chapter_title, "content": chapter_content})
                full_script_parts.append(f"{chapter_title}\n{chapter_content}")
        
        context = (
            "Kontext: Um das Thema besser einzuordnen, betrachten wir es im Zusammenhang aktueller Entwicklungen und möglicher Konsequenzen. "
            "Dabei bleiben wir bei den belegbaren Informationen und unterscheiden klar zwischen bekannten Fakten und längerfristigen Trends."
        )
        full_script_parts.append(context)
        
        analysis = (
            "Analyse: Diese Entwicklung zeigt, wie eng verschiedene Faktoren miteinander verbunden sind. "
            "Wir beleuchten, welche Auswirkungen dies für die wichtigsten Akteure und für das Publikum haben kann."
        )
        full_script_parts.append(analysis)
        
        questions = (
            "Offene Fragen: Welche Folgen könnten sich in den nächsten Wochen zeigen? Welche Entscheidungen stehen als nächstes an, und wo gibt es noch Unklarheiten?"
        )
        full_script_parts.append(questions)
        
        conclusion = (
            "Fazit: Zusammengefasst bleibt das Thema relevant und zeigt deutlich, warum es weiter beobachtet werden muss. "
            "Wir haben die wichtigsten Punkte zusammengefasst und zeigen, was als Nächstes wichtig ist."
        )
        full_script_parts.append(conclusion)
        
        cta = (
            "Wenn Ihnen diese Analyse geholfen hat, abonnieren Sie den Kanal für mehr Hintergrundberichte und aktivieren Sie die Benachrichtigungen. "
            "Teilen Sie Ihre Meinung gern in den Kommentaren."
        )
        full_script_parts.append(cta)
        
        full_script = "\n\n".join(full_script_parts)
        return title, hook, chapters, full_script, "fallback", ""
    
    def _expand_key_points(self, key_points: List[str], target_word_count: int) -> List[str]:
        """Use each extracted point once; do not repeat source sentences to pad length."""
        del target_word_count  # length targets are handled via warnings, not duplication
        return [p.strip() for p in key_points if p.strip()]

    def _build_chapter_content(self, title: str, points: List[str]) -> str:
        """One bullet per fact; no second sentence that re-quotes the same line."""
        if not points:
            return (
                "Aus der Quelle lassen sich hier keine weiteren Einzelpunkte sauber ausgliedern; "
                "wir bleiben bei einer knappen Zusammenfassung ohne Wiederholung des Fließtexts."
            )
        bullets = []
        seen_lower = set()
        for point in points:
            p = point.strip().rstrip(".")
            if not p:
                continue
            key = p.lower()[:120]
            if key in seen_lower:
                continue
            seen_lower.add(key)
            bullets.append(f"– {p}.")
        return " ".join(bullets) if bullets else self._build_chapter_content(title, [])

def generate_title(text: str) -> str:
    """Generate a title from text."""
    first_sentence = text.split('.')[0]
    return first_sentence[:100] if first_sentence else "News Video"
