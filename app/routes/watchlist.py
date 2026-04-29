"""Watchlist-Endpunkte (Phase 5 V1 Schritt 1 — CRUD-Anfang)."""

import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.watchlist.firestore_repo import FirestoreUnavailableError
from app.watchlist.models import (
    CreateWatchlistChannelResponse,
    ListWatchlistChannelsResponse,
    WatchlistChannelCreateRequest,
)
from app.watchlist import service as watchlist_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/watchlist/channels",
    response_model=CreateWatchlistChannelResponse,
)
async def watchlist_create_channel(req: WatchlistChannelCreateRequest):
    try:
        return watchlist_service.create_channel(req)
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore is not reachable."
        logger.warning("watchlist POST /watchlist/channels failed: Firestore unavailable")
        body = CreateWatchlistChannelResponse(channel=None, warnings=[msg])
        return JSONResponse(status_code=503, content=body.model_dump())


@router.get(
    "/watchlist/channels",
    response_model=ListWatchlistChannelsResponse,
)
async def watchlist_list_channels():
    try:
        return watchlist_service.list_channels()
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore is not reachable."
        logger.warning("watchlist GET failed: FirestoreUnavailableError")
        body = ListWatchlistChannelsResponse(channels=[], warnings=[msg])
        return JSONResponse(status_code=503, content=body.model_dump())
