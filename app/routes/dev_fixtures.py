"""Dev/Test Fixtures (BA 6.6.1) — nur aktiv mit ENABLE_TEST_FIXTURES."""

import logging
from typing import Optional

from fastapi import APIRouter, Body, HTTPException

from app.config import settings
from app.watchlist.firestore_repo import (
    FirestoreUnavailableError,
    FirestoreWatchlistRepository,
)
from app.watchlist.models import (
    DevFixtureCompletedScriptJobRequest,
    DevFixtureCompletedScriptJobResponse,
)
from app.watchlist.dev_fixture_seed import (
    DevFixtureConflictError,
    seed_completed_script_job_fixture,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dev", tags=["dev_fixtures BA 6.6.1"])


@router.post(
    "/fixtures/completed-script-job",
    response_model=DevFixtureCompletedScriptJobResponse,
)
async def dev_fixture_completed_script_job(
    body: Optional[DevFixtureCompletedScriptJobRequest] = Body(None),
):
    """Legt einen abgeschlossenen ScriptJob + GeneratedScript (+ optional ProductionJob) ohne YouTube-Anruf.

    Aktivierung: Umgebungsvariable ``ENABLE_TEST_FIXTURES=true`` (Produktion: ausgelassen).

    IDs beginnen immer mit ``dev_fixture_``.
    """
    if not getattr(settings, "enable_test_fixtures", False):
        raise HTTPException(
            status_code=403,
            detail="Testfixtures sind deaktiviert. Set ENABLE_TEST_FIXTURES=true nur in Dev/Test.",
        )

    payload = body or DevFixtureCompletedScriptJobRequest()

    repo = FirestoreWatchlistRepository()
    try:
        job, _gs, pj, warns = seed_completed_script_job_fixture(
            fixture_job_id_raw=payload.fixture_id,
            create_production_job=payload.create_production_job,
            repo=repo,
        )
    except DevFixtureConflictError as e:
        jid = str(e.args[0] if e.args else "")
        logger.debug("Dev fixture conflict: existing job_id=%s", jid)
        raise HTTPException(
            status_code=409,
            detail=f"Fixture-ID bereits vergeben oder Dokument vorhanden: {jid}",
        )
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore nicht erreichbar."
        logger.warning("dev fixture seed failed: Firestore")
        raise HTTPException(status_code=503, detail=msg)

    out = DevFixtureCompletedScriptJobResponse(
        job_id=job.id,
        generated_script_id=job.generated_script_id or job.id,
        production_job_id=(pj.id if pj else None),
        production_job_created=pj is not None,
        warnings=warns,
    )
    return out
