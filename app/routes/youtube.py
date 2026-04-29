"""YouTube-Kanal-Discovery: neueste Videos per RSS (ohne Data API)."""

from fastapi import APIRouter
from app.models import LatestVideosRequest, LatestVideosResponse
from app.youtube.service import get_latest_channel_videos
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


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
