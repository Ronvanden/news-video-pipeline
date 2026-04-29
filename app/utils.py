import logging
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
try:
    import openai
except ImportError:
    openai = None

logger = logging.getLogger(__name__)

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
    
    def generate_script(self, title: str, key_points: List[str], duration_minutes: int, source_word_count: int = 0) -> Tuple[str, List[dict], str, str, str]:
        """Generate script structure based on duration. Returns hook, chapters, full_script, mode, reason."""
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
        
        if openai and settings.openai_api_key:
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
    ) -> Tuple[str, List[dict], str, str, str]:
        """Generate script using OpenAI."""
        try:
            client = openai.OpenAI(api_key=settings.openai_api_key)
            
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
            
            response = client.chat.completions.create(
                model=settings.openai_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=3000,
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            
            result = response.choices[0].message.content
            import json
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
            if full_script_words < min_word_count:
                logger.warning(f"LLM output too short ({full_script_words} words), extending locally")
                full_script = self._extend_script(full_script, key_points, title_text, target_word_count, min_word_count)
                full_script_words = count_words(full_script)
                if full_script_words < min_word_count:
                    logger.warning(f"Extended script still too short ({full_script_words} words), fallback to local generation")
                    return self._generate_fallback(
                        title,
                        key_points,
                        duration_minutes,
                        target_word_count,
                        num_chapters,
                        min_word_count,
                        max_word_count,
                        source_word_count,
                    )
            
            return title_text, hook, chapters, full_script, "llm", ""
        
        except openai.APIError as e:
            status_code = getattr(e, 'status_code', 'unknown')
            message = getattr(e, 'message', str(e))
            logger.error(f"OpenAI API error: {type(e).__name__} status={status_code} message={message}")
            sanitized_reason = f"API error {status_code}"
        except openai.RateLimitError as e:
            message = getattr(e, 'message', str(e))
            logger.error(f"OpenAI rate limit: {type(e).__name__} message={message}")
            sanitized_reason = "Rate limit exceeded"
        except openai.AuthenticationError as e:
            message = getattr(e, 'message', str(e))
            logger.error(f"OpenAI auth error: {type(e).__name__} message={message}")
            sanitized_reason = "Authentication failed"
        except openai.OpenAIError as e:
            message = getattr(e, 'message', str(e))
            logger.error(f"OpenAI error: {type(e).__name__} message={message}")
            sanitized_reason = "OpenAI request failed"
        except json.JSONDecodeError as e:
            logger.error(f"OpenAI JSON parse error: {type(e).__name__} message={str(e)}")
            sanitized_reason = "Invalid response format"
        except Exception as e:
            logger.error(f"OpenAI generation failed: {type(e).__name__} message={str(e)}")
            sanitized_reason = f"Unexpected error: {type(e).__name__}"
        
        logger.info("Falling back to local generation")
        hook, chapters, full_script, _, _ = self._generate_fallback(
            title,
            key_points,
            duration_minutes,
            target_word_count,
            num_chapters,
            min_word_count,
            max_word_count,
            source_word_count,
        )
        return hook, chapters, full_script, "fallback", sanitized_reason
    
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
    ) -> Tuple[str, List[dict], str, str, str]:
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
        current_word_count = count_words(full_script)
        while current_word_count < target_word_count:
            additional = self._build_additional_narrative(target_word_count - current_word_count, key_points)
            if not additional:
                break
            full_script = f"{full_script}\n\n{additional}"
            current_word_count = count_words(full_script)
        
        return hook, chapters, full_script, "fallback", ""
    
    def _expand_key_points(self, key_points: List[str], target_word_count: int) -> List[str]:
        """Expand key points to reach target word count without hallucinating."""
        current_words = sum(len(point.split()) for point in key_points)
        expanded = key_points.copy()
        if current_words >= target_word_count * 0.75:
            return expanded
        
        for point in key_points:
            if current_words >= target_word_count * 0.9:
                break
            if len(expanded) < target_word_count // 60:
                rephrased = f"Das Wichtigste daran ist: {point}"
            else:
                rephrased = f"Außerdem zeigt sich: {point}"
            expanded.append(rephrased)
            current_words += len(rephrased.split())
        
        return expanded

    def _build_chapter_content(self, title: str, points: List[str]) -> str:
        """Build chapter content from key points with added explanation."""
        sentences = []
        for point in points:
            sentences.append(f"{point}."
                             if point.endswith('.') else f"{point}.")
            sentences.append(f"Dazu lässt sich ergänzen, dass {point.lower()}" if len(point.split()) < 15 else f"Dazu gehört vor allem: {point.lower()}")
        if len(sentences) < 4:
            sentences.append("Diese Aspekte sind wichtig, um das Thema umfassend zu verstehen.")
        return " ".join(sentences)

    def _build_additional_narrative(self, missing_words: int, key_points: List[str]) -> str:
        """Add more narrative content when the fallback script is too short."""
        if missing_words <= 0:
            return ""
        narrative = [
            "Wir vertiefen die Perspektive und betrachten zusätzliche Zusammenhänge, die für das Verständnis wichtig sind.",
            "Dabei achten wir darauf, bei belegbaren Fakten zu bleiben und die zentrale Aussage klar herauszuarbeiten.",
        ]
        if key_points:
            narrative.append(f"Insbesondere sind die folgenden Punkte zu beachten: {', '.join(key_points[:3])}.")
        return " ".join(narrative)

    def _extend_script(self, script: str, key_points: List[str], title: str, target_word_count: int, min_word_count: int) -> str:
        """Extend an LLM script with additional non-hallucinating narrative."""
        if count_words(script) >= min_word_count:
            return script

        additional_parts = [
            "Darüber hinaus ordnen wir den bisherigen Inhalt ein und erklären, welche Bedeutung er für die aktuelle Debatte hat.",
        ]
        if key_points:
            for i, point in enumerate(key_points[:6], start=1):
                additional_parts.append(
                    f"Punkt {i}: {point}. Diese Aussage lässt sich in den größeren Kontext einordnen, weil sie grundlegende Fragen zur Umsetzung und zu den möglichen Konsequenzen aufwirft."
                )
        additional_parts.append(
            "Wir beschreiben nun, welche Auswirkungen diese Entwicklungen auf die Betroffenen haben könnten und worauf man in den kommenden Wochen achten sollte."
        )
        additional_parts.append(
            "Zum Abschluss fassen wir zusammen, warum diese Entwicklung weiter beobachtet werden sollte und welche Fragen noch offen bleiben."
        )

        extended = f"{script}\n\n" + "\n\n".join(additional_parts)
        while count_words(extended) < target_word_count:
            extended += "\n\n" + (
                "Zusätzlich betrachten wir die Risiken und Chancen, die sich aus dieser Lage ergeben. "
                "Wichtig ist dabei, klar zwischen den vorhandenen Fakten und den noch offenen Fragen zu unterscheiden."
            )
        return extended


def generate_title(text: str) -> str:
    """Generate a title from text."""
    first_sentence = text.split('.')[0]
    return first_sentence[:100] if first_sentence else "News Video"