"""
Orchestration for POST /review-script. V1: local heuristics only.
"""

import logging

from app.models import (
    ReviewIssue,
    ReviewRecommendation,
    ReviewScriptRequest,
    ReviewScriptResponse,
)
from app.review.originality import analyze_originality

logger = logging.getLogger(__name__)


def review_script(request: ReviewScriptRequest) -> ReviewScriptResponse:
    """
    Run originality review. Does not raise for normal inputs; unexpected errors
    degrade to a conservative high-risk response (no HTTP 500 from service).
    """
    try:
        return analyze_originality(request)
    except Exception as e:
        logger.error(
            "review_script unexpected failure: %s",
            type(e).__name__,
            exc_info=True,
        )
        return ReviewScriptResponse(
            risk_level="high",
            originality_score=0,
            similarity_flags=[],
            issues=[
                ReviewIssue(
                    severity="critical",
                    code="review_internal_error",
                    message="Review could not be completed; treat as high risk until re-run.",
                    evidence_hint=None,
                )
            ],
            recommendations=[
                ReviewRecommendation(
                    priority="high",
                    action="Retry the review request; contact ops if the error persists.",
                    rationale="An unexpected error occurred during heuristic analysis.",
                )
            ],
            warnings=[
                "Review service encountered an unexpected error; result is conservative (high risk).",
            ],
        )
