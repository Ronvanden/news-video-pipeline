from fastapi import APIRouter, HTTPException
from app.models import GenerateScriptRequest, GenerateScriptResponse
from app.utils import (
    extract_text_from_url,
    summarize_text,
    translate_to_german,
    extract_key_points,
    ScriptGenerator,
    generate_title,
    count_words
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/generate-script", response_model=GenerateScriptResponse)
async def generate_script(request: GenerateScriptRequest):
    try:
        logger.info(f"Processing URL: {request.url}")
        
        # Extract text
        text, extraction_warnings = extract_text_from_url(request.url)
        if not text:
            raise HTTPException(status_code=400, detail="Could not extract text from URL")
        
        # Summarize
        summary = summarize_text(text, sentences_count=20)
        
        # Translate to target language
        if request.target_language == "de":
            translated = translate_to_german(summary)
        else:
            translated = summary  # Assume English
        
        # Extract key points
        key_points = extract_key_points(translated)
        
        # Generate title
        title = generate_title(translated)
        source_word_count = count_words(translated)
        
        # Generate script
        generator = ScriptGenerator()
        title, hook, chapters, full_script, mode, reason = generator.generate_script(
            title,
            key_points,
            request.duration_minutes,
            source_word_count,
        )
        
        # Sources and warnings
        sources = [request.url]
        warnings = extraction_warnings
        target_word_count = request.duration_minutes * 140
        actual_word_count = count_words(full_script)
        warnings.append(f"Target word count: {target_word_count}, Actual word count: {actual_word_count}")
        if actual_word_count < target_word_count * 0.5:
            warnings.append("Script is significantly shorter than target. Content may be insufficient for the requested duration.")
        if len(full_script) < 500:
            warnings.append("Script may be too short for 10-minute video")
        
        # Add mode warning (fallback stays short on purpose — no article padding)
        fallback_note = (
            "Fallback mode: script is condensed from the source and not artificially lengthened; "
            "duration target may be missed to avoid repeating article text."
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
        
        return GenerateScriptResponse(
            title=title,
            hook=hook,
            chapters=chapters,
            full_script=full_script,
            sources=sources,
            warnings=warnings
        )
    
    except Exception as e:
        logger.error(f"Error generating script: {type(e).__name__} message={str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")