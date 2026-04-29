from pydantic import BaseModel, Field
from typing import List

class GenerateScriptRequest(BaseModel):
    url: str
    target_language: str = "de"
    duration_minutes: int = 10


class YouTubeGenerateScriptRequest(BaseModel):
    video_url: str = Field(..., min_length=1)
    target_language: str = "de"
    duration_minutes: int = 10

class Chapter(BaseModel):
    title: str
    content: str

class GenerateScriptResponse(BaseModel):
    title: str
    hook: str
    chapters: List[Chapter]
    full_script: str
    sources: List[str]
    warnings: List[str]


class LatestVideosRequest(BaseModel):
    channel_url: str = Field(..., min_length=1)
    max_results: int = Field(5, ge=1, le=50)


class LatestVideoItem(BaseModel):
    title: str
    url: str
    video_id: str
    published_at: str
    summary: str
    score: int
    reason: str


class LatestVideosResponse(BaseModel):
    channel: str
    videos: List[LatestVideoItem]
    warnings: List[str]