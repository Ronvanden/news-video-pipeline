"""YouTube-Kanal-Discovery: neueste Videos per RSS (ohne Data API)."""

from fastapi import APIRouter
from app.models import (
    LatestVideosRequest,
    LatestVideosResponse,
    YouTubeGenerateScriptRequest,
    GenerateScriptResponse,
)
from app.youtube.service import get_latest_channel_videos
from app.utils import (
    extract_video_id,
    fetch_youtube_transcript_by_video_id,
    build_script_response_from_extracted_text,
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/youtube/generate-script", response_model=GenerateScriptResponse)
async def youtube_generate_script(request: YouTubeGenerateScriptRequest):
    """
    Transcript-basiertes Story-Skript (ohne YouTube Data API, ohne Persistenz).
    """
    try:
        video_id = extract_video_id(request.video_url)
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
                warnings=["Transcript not available for this video."],
            )

        title, hook, chapters, full_script, sources, warnings = (
            build_script_response_from_extracted_text(
                extracted_text=transcript,
                source_url=canonical_url,
                target_language=request.target_language,
                duration_minutes=request.duration_minutes,
                extraction_warnings=[],
                extra_warnings=[
                    "Quelle: YouTube-Untertitel/Transkript; das Skript ist eine eigenständige "
                    "deutschsprachige Story-Formulierung, keine wörtliche Abschrift."
                ],
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
            "youtube/generate-script failed: %s message=%s",
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
                f"Technischer Hinweis: {type(e).__name__}."
            ],
        )


@router.post("/youtube/latest-videos", response_model=LatestVideosResponse)
async def youtube_latest_videos(request: LatestVideosRequest):
    try:
        data = get_latest_channel_videos(request.channel_url, request.max_results)
        return LatestVideosResponse(**data)
    except Exception as e:
        logger.error("youtube/latest-videos failed: %s message=%s", type(e).__name__, str(e)[:300])
        return LatestVideosResponse(
            channel="",
            videos=[],
            warnings=[
                "Die Anfrage konnte nicht vollständig verarbeitet werden. "
                f"Technischer Hinweis: {type(e).__name__}."
            ],
        )
