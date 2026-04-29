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
    """Check if URL appears to be a homepage."""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    path = parsed.path.strip('/')
    # Common homepage indicators
    if not path or path in ['index', 'home', 'start']:
        return True
    # For specific sites like tagesschau
    if 'tagesschau.de' in url and not any(keyword in path for keyword in ['artikel', 'meldung', 'nachrichten']):
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
    
    def generate_script(self, title: str, key_points: List[str], duration_minutes: int) -> Tuple[str, List[dict], str, str, str]:
        """Generate script structure based on duration. Returns hook, chapters, full_script, mode, reason."""
        target_word_count = duration_minutes * 140
        
        # Determine number of chapters based on duration
        if duration_minutes <= 6:
            num_chapters = 3
        elif duration_minutes <= 10:
            num_chapters = 5
        else:
            num_chapters = 7
        
        if openai and settings.openai_api_key:
            return self._generate_with_openai(title, key_points, duration_minutes, target_word_count, num_chapters)
        return self._generate_fallback(title, key_points, duration_minutes, target_word_count, num_chapters)
    
    def _generate_with_openai(self, title: str, key_points: List[str], duration_minutes: int, target_word_count: int, num_chapters: int) -> Tuple[str, List[dict], str, str, str]:
        """Generate script using OpenAI."""
        try:
            client = openai.OpenAI(api_key=settings.openai_api_key)
            
            prompt = f"""
            Erstelle ein YouTube-Video-Skript basierend auf folgenden Informationen:
            
            Titel: {title}
            Key Points: {'; '.join(key_points)}
            Dauer: {duration_minutes} Minuten (ca. {target_word_count} Wörter)
            Anzahl Kapitel: {num_chapters}
            
            Struktur des Skripts:
            - Hook (einleitender Satz)
            - Intro (Begrüßung)
            - {num_chapters} Kapitel mit Titeln und Inhalt
            - Kontext/Einordnung
            - Fazit
            - Call-to-Action
            
            Antworte nur mit einem gültigen JSON-Objekt, ohne zusätzlichen Text, Markdown oder Backticks.
            Gib das Ergebnis als JSON zurück:
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
                max_tokens=2000,
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
        hook, chapters, full_script, _, _ = self._generate_fallback(title, key_points, duration_minutes, target_word_count, num_chapters)
        return hook, chapters, full_script, "fallback", sanitized_reason
    
    def _generate_fallback(self, title: str, key_points: List[str], duration_minutes: int, target_word_count: int, num_chapters: int) -> Tuple[str, List[dict], str, str, str]:
        """Fallback script generation."""
        hook = f"Entdecken Sie die neuesten Entwicklungen in diesem spannenden Thema: {title}"
        
        chapters = []
        full_script_parts = [hook]
        
        intro = "Hallo und herzlich willkommen zu diesem Video! Heute beschäftigen wir uns mit einem wichtigen Thema."
        full_script_parts.append(intro)
        
        if not key_points:
            # Fallback bei wenig Inhalt
            chapter_title = "Einführung"
            chapter_content = "In diesem Video besprechen wir aktuelle Entwicklungen zum Thema. Wir werden die verfügbaren Informationen analysieren und einordnen."
            chapters.append({"title": chapter_title, "content": chapter_content})
            full_script_parts.append(f"{chapter_title}\n{chapter_content}")
        else:
            # Expand key_points if needed to reach target
            expanded_points = self._expand_key_points(key_points, target_word_count)
            
            points_per_chapter = max(1, len(expanded_points) // num_chapters)
            for i in range(0, len(expanded_points), points_per_chapter):
                chapter_points = expanded_points[i:i+points_per_chapter]
                first_point = chapter_points[0]
                chapter_title = f"Kapitel {len(chapters)+1}: {first_point.split('.')[0][:100]}"
                chapter_content = "\n".join(chapter_points)
                chapters.append({"title": chapter_title, "content": chapter_content})
                full_script_parts.append(f"{chapter_title}\n{chapter_content}")
        
        # Add context/einordnung
        context = "Um dieses Thema besser zu verstehen, betrachten wir es im größeren Kontext aktueller Entwicklungen."
        full_script_parts.append(context)
        
        # Fazit
        conclusion = "Zusammenfassend lässt sich sagen, dass dieses Thema weiterhin von großer Bedeutung ist."
        full_script_parts.append(conclusion)
        
        # CTA
        cta = "Wenn Ihnen dieses Video gefallen hat, vergessen Sie nicht zu liken, zu abonnieren und die Glocke zu aktivieren für mehr Inhalte!"
        full_script_parts.append(cta)
        
        full_script = "\n\n".join(full_script_parts)
        
        return hook, chapters, full_script, "fallback", ""
    
    def _expand_key_points(self, key_points: List[str], target_word_count: int) -> List[str]:
        """Expand key points to reach target word count without hallucinating."""
        current_words = sum(len(point.split()) for point in key_points)
        if current_words >= target_word_count * 0.8:  # Close enough
            return key_points
        
        expanded = key_points.copy()
        # Repeat and rephrase slightly
        for point in key_points:
            if current_words < target_word_count:
                # Add a rephrased version
                rephrased = f"Außerdem ist zu erwähnen: {point}"
                expanded.append(rephrased)
                current_words += len(rephrased.split())
        
        return expanded

def generate_title(text: str) -> str:
    """Generate a title from text."""
    first_sentence = text.split('.')[0]
    return first_sentence[:100] if first_sentence else "News Video"