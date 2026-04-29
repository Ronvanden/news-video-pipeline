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
