from fastapi import APIRouter, HTTPException
from app.models import GenerateScriptRequest, GenerateScriptResponse
from app.utils import extract_text_from_url, build_script_response_from_extracted_text
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
        
        title, hook, chapters, full_script, sources, warnings = (
            build_script_response_from_extracted_text(
                extracted_text=text,
                source_url=request.url,
                target_language=request.target_language,
                duration_minutes=request.duration_minutes,
                extraction_warnings=extraction_warnings,
                video_template=getattr(request, "video_template", None) or "generic",
                template_conformance_level=(
                    getattr(request, "template_conformance_level", None) or "warn"
                ),
            )
        )

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