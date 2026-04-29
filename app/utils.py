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

logger = logging.getLogger(__name__)

def extract_text_from_url(url: str) -> str:
    """Extract text from news URL or YouTube transcript."""
    if "youtube.com" in url or "youtu.be" in url:
        return extract_youtube_transcript(url)
    else:
        return extract_news_text(url)

def extract_news_text(url: str) -> str:
    """Extract text from news article."""
    try:
        downloaded = trafilatura.fetch_url(url)
        text = trafilatura.extract(downloaded)
        return text or ""
    except Exception as e:
        logger.error(f"Error extracting news text: {e}")
        return ""

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
    
    def generate_script(self, title: str, key_points: List[str], duration_minutes: int) -> Tuple[str, List[dict], str]:
        """Generate script structure."""
        hook = f"Entdecken Sie die neuesten Entwicklungen in diesem spannenden Thema: {title}"
        
        chapters = []
        full_script = hook + "\n\n"
        
        if not key_points:
            # Fallback bei wenig Inhalt
            chapter_title = "Einführung"
            chapter_content = "In diesem Video besprechen wir aktuelle Entwicklungen zum Thema."
            chapters.append({"title": chapter_title, "content": chapter_content})
            full_script += chapter_title + "\n" + chapter_content + "\n\n"
        else:
            points_per_chapter = max(1, len(key_points) // 3)
            for i in range(0, len(key_points), points_per_chapter):
                chapter_points = key_points[i:i+points_per_chapter]
                # Bessere Kapitel-Titel generieren
                first_point = chapter_points[0]
                # Verwende den ersten Satz oder bis zu 100 Zeichen ohne Abschneiden
                chapter_title = f"Kapitel {len(chapters)+1}: {first_point.split('.')[0][:100]}"
                if len(first_point.split('.')[0]) > 100:
                    chapter_title = chapter_title.rstrip()  # Entferne mögliche Leerzeichen
                chapter_content = "\n".join(chapter_points)
                chapters.append({"title": chapter_title, "content": chapter_content})
                full_script += chapter_title + "\n" + chapter_content + "\n\n"
        
        return hook, chapters, full_script

def generate_title(text: str) -> str:
    """Generate a title from text."""
    first_sentence = text.split('.')[0]
    return first_sentence[:100] if first_sentence else "News Video"