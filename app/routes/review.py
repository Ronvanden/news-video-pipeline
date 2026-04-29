"""POST /review-script — originality / redaction risk heuristics (Phase 4 V1)."""

import logging

from fastapi import APIRouter

from app.models import ReviewScriptRequest, ReviewScriptResponse
from app.review.service import review_script

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/review-script", response_model=ReviewScriptResponse)
async def review_script_endpoint(request: ReviewScriptRequest):
    """
    Technical/editorial risk assessment only — not legal advice, not a publish approval.
    """
    logger.info(
        "review-script: source_type=%s source_url_len=%d source_text_len=%d generated_len=%d",
        request.source_type,
        len(request.source_url or ""),
        len(request.source_text or ""),
        len(request.generated_script or ""),
    )
    return review_script(request)
