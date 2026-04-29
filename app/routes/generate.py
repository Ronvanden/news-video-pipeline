from fastapi import APIRouter, HTTPException
from app.models import GenerateScriptRequest, GenerateScriptResponse
from app.utils import (
    extract_text_from_url,
    summarize_text,
    translate_to_german,
    extract_key_points,
    ScriptGenerator,
    generate_title
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/generate-script", response_model=GenerateScriptResponse)
async def generate_script(request: GenerateScriptRequest):
    try:
        logger.info(f"Processing URL: {request.url}")
        
        # Extract text
        text = extract_text_from_url(request.url)
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
        
        # Generate script
        generator = ScriptGenerator()
        hook, chapters, full_script = generator.generate_script(title, key_points, request.duration_minutes)
        
        # Sources and warnings
        sources = [request.url]
        warnings = []
        if len(full_script) < 500:
            warnings.append("Script may be too short for 10-minute video")
        
        return GenerateScriptResponse(
            title=title,
            hook=hook,
            chapters=chapters,
            full_script=full_script,
            sources=sources,
            warnings=warnings
        )
    
    except Exception as e:
        logger.error(f"Error generating script: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")