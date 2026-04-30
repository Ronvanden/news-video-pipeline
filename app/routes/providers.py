"""Provider-Konfiguration (BA 7.6): Status/Dry-run/Budget ohne Secrets, keine Provider-Calls."""

import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.watchlist import service as watchlist_service
from app.watchlist.firestore_repo import FirestoreUnavailableError
from app.watchlist.models import (
    ListProviderConfigsResponse,
    ProviderConfig,
    ProviderConfigUpsertRequest,
    ProviderSeedDefaultsResponse,
    ProviderStatusResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/providers/configs",
    response_model=ListProviderConfigsResponse,
)
async def providers_list_configs():
    try:
        return watchlist_service.list_provider_configs_service()
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore ist nicht erreichbar."
        logger.warning("GET /providers/configs failed: Firestore unavailable")
        body = ListProviderConfigsResponse(configs=[], warnings=[msg])
        return JSONResponse(status_code=503, content=body.model_dump())


@router.post(
    "/providers/configs/{provider_name}/upsert",
    response_model=ProviderConfig,
)
async def providers_upsert_config(
    provider_name: str,
    body: ProviderConfigUpsertRequest,
):
    """Keine Secrets — nur Stammdaten wie enabled/dry_run/Budget-Schätzungen."""
    try:
        return watchlist_service.upsert_provider_config_service(provider_name, body)
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore ist nicht erreichbar."
        raise HTTPException(status_code=503, detail=msg)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post(
    "/providers/configs/seed-defaults",
    response_model=ProviderSeedDefaultsResponse,
)
async def providers_seed_default_configs(apply_writes: bool = False):
    """BA 8.6: Vier Standard-Slots (openai, voice_default, image_default, render_default).

    Ohne ``apply_writes=true`` nur Vorschau (keine Firestore-Writes).
    """
    try:
        return watchlist_service.seed_default_provider_configs_service(
            apply_writes=apply_writes,
        )
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore ist nicht erreichbar."
        logger.warning(
            "POST /providers/configs/seed-defaults failed: Firestore unavailable"
        )
        raise HTTPException(status_code=503, detail=msg)


@router.get(
    "/providers/status",
    response_model=ProviderStatusResponse,
)
async def providers_status():
    try:
        return watchlist_service.get_provider_status_service()
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore ist nicht erreichbar."
        logger.warning("GET /providers/status failed: Firestore unavailable")
        raise HTTPException(status_code=503, detail=msg)
