import logging
import json
from typing import List, Tuple
import re
from urllib.parse import urlparse
import trafilatura
from youtube_transcript_api import YouTubeTranscriptApi
from deep_translator import GoogleTranslator
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from app.config import settings
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
    """Extract transcript from YouTube video."""
    try:
        video_id = extract_video_id(url)
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'de'])
        text = " ".join([item['text'] for item in transcript])
        return text
    except Exception as e:
        logger.error(f"Error extracting YouTube transcript: {e}")
        return ""

def extract_video_id(url: str) -> str:
    """Extract YouTube video ID from URL."""
    parsed = urlparse(url)
    if parsed.hostname == 'youtu.be':
        return parsed.path[1:]
    if parsed.hostname in ('www.youtube.com', 'youtube.com'):
        if parsed.path == '/watch':
            return parsed.query.split('v=')[1].split('&')[0]
    return ""

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
    
    def generate_script(self, title: str, key_points: List[str], duration_minutes: int, source_word_count: int = 0) -> Tuple[str, str, List[dict], str, str, str]:
        """Generate script structure based on duration. Returns title, hook, chapters, full_script, mode, reason."""
        target_word_count = duration_minutes * 140
        min_word_count = max(int(target_word_count * 0.85), 200)
        max_word_count = int(target_word_count * 1.15)
        
        # Determine number of chapters based on duration
        if duration_minutes <= 6:
            num_chapters = 4
        elif duration_minutes <= 10:
            num_chapters = 6
        else:
            num_chapters = 8
        
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
            )
        return self._generate_fallback(title, key_points, duration_minutes, target_word_count, num_chapters, min_word_count, max_word_count, source_word_count)
    
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
    ) -> Tuple[str, str, List[dict], str, str, str]:
        """Generate script using OpenAI."""
        try:
            source_note = "" if source_word_count >= target_word_count else (
                "Die Quelle enthält weniger Text als die gewünschte Dauer. Bitte ergänze das Skript mit zusätzlicher Kontext-Einordnung und Analyse, ohne neue Fakten zu erfinden.")
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
            if isinstance(result, dict):
                data = result
            else:
                text = str(result).strip()
                try:
                    data = json.loads(text)
                except json.JSONDecodeError:
                    preview = text[:200]
                    logger.error(f"OpenAI response parse failed, preview={preview!r}")
                    raise
            
            if not isinstance(data, dict):
                logger.error(f"OpenAI response parsed to non-dict type: {type(data).__name__}")
                raise ValueError("Invalid response format")
            
            title_text = data.get("title") or title
            hook = data.get("hook") or f"Entdecken Sie: {title_text}"
            chapters = data.get("chapters") if isinstance(data.get("chapters"), list) else []
            full_script = data.get("full_script") or data.get("script") or ""
            
            full_script_words = count_words(full_script)
            llm_short_reason = ""
            if full_script_words < min_word_count:
                logger.warning(
                    "LLM output below minimum word band (%s words, min=%s); keeping LLM output (no fallback, no padding)",
                    full_script_words,
                    min_word_count,
                )
                llm_short_reason = "LLM output shorter than target"

            return title_text, hook, chapters, full_script, "llm", llm_short_reason
        
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
        )
        return title, hook, chapters, full_script, "fallback", sanitized_reason
    
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
    ) -> Tuple[str, str, List[dict], str, str, str]:
        """Fallback script generation."""
        hook = f"Entdecken Sie die neuesten Entwicklungen in diesem spannenden Thema: {title}"
        
        chapters = []
        full_script_parts = [hook]
        intro = "Hallo und herzlich willkommen! In diesem Video analysieren wir die wichtigsten Aspekte des Themas und ordnen sie ein."
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