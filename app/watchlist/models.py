"""Watchlist-spezifische Request-/Response-Modelle (Phase 5 V1 Schritt 1)."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator
from typing import List, Literal, Optional

ChannelStatusLiteral = Literal["active", "paused", "error"]
CheckIntervalLiteral = Literal["manual", "hourly", "daily", "weekly"]


class WatchlistChannelCreateRequest(BaseModel):
    channel_url: str = Field(..., min_length=1)
    check_interval: CheckIntervalLiteral = "manual"
    max_results: int = Field(default=5, ge=1, le=50)
    auto_generate_script: bool = False
    auto_review_script: bool = True
    target_language: str = "de"
    duration_minutes: int = Field(default=10, ge=1, le=60)
    min_score: int = Field(default=40, ge=0, le=100)
    ignore_shorts: bool = True
    notes: str = ""

    @field_validator("channel_url")
    @classmethod
    def channel_url_strip(cls, v: str) -> str:
        s = (v or "").strip()
        return s


class WatchlistChannel(BaseModel):
    id: str
    channel_url: str
    channel_id: str
    channel_name: str
    status: ChannelStatusLiteral = "active"
    check_interval: CheckIntervalLiteral = "manual"
    max_results: int = Field(..., ge=1, le=50)
    auto_generate_script: bool = False
    auto_review_script: bool = True
    target_language: str = "de"
    duration_minutes: int = Field(..., ge=1, le=60)
    min_score: int = Field(..., ge=0, le=100)
    ignore_shorts: bool = True
    created_at: str
    updated_at: str
    last_checked_at: Optional[str] = None
    last_success_at: Optional[str] = None
    last_error: str = ""
    notes: str = ""


class CreateWatchlistChannelResponse(BaseModel):
    channel: Optional[WatchlistChannel] = None
    warnings: List[str] = Field(default_factory=list)


class ListWatchlistChannelsResponse(BaseModel):
    channels: List[WatchlistChannel] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


ProcessedVideoStatusLiteral = Literal["seen", "skipped"]
ChannelCheckItemStatusLiteral = Literal["new", "known", "skipped"]


class ProcessedVideo(BaseModel):
    id: str
    channel_id: str
    video_id: str
    video_url: str
    title: str
    published_at: str
    first_seen_at: str
    status: ProcessedVideoStatusLiteral
    score: int = 0
    reason: str = ""
    is_short: bool = False
    skip_reason: str = ""
    script_job_id: Optional[str] = None
    review_result_id: Optional[str] = None
    last_error: str = ""


class ChannelCheckVideoItem(BaseModel):
    title: str = ""
    url: str = ""
    video_id: str = ""
    published_at: str = ""
    score: int = 0
    reason: str = ""
    is_short: bool = False
    status: ChannelCheckItemStatusLiteral = "new"
    skip_reason: str = ""


class CheckWatchlistChannelResponse(BaseModel):
    channel_id: str
    new_videos: List[ChannelCheckVideoItem] = Field(default_factory=list)
    known_videos: List[ChannelCheckVideoItem] = Field(default_factory=list)
    skipped_videos: List[ChannelCheckVideoItem] = Field(default_factory=list)
    created_processed_videos: int = 0
    warnings: List[str] = Field(default_factory=list)
