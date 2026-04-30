"""Firestore-Testfixtures (BA 6.6.1) — nur mit ENABLE_TEST_FIXTURES; kein YouTube-/Transcript-Abruf."""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional, Tuple

from app.models import Chapter
from app.utils import count_words
from app.watchlist.models import (
    GeneratedScript,
    ProductionJob,
    ScriptJob,
)


class DevFixtureConflictError(Exception):
    """Bereits ein ScriptJob/generated_scripts-Eintrag unter dieser Fixture-ID."""


_DEV_FIXTURE_PREFIX = "dev_fixture_"
_RE_SUFFIX = re.compile(r"^[A-Za-z0-9_-]+$")


def _utc_now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def finalize_fixture_job_id(fixture_id: Optional[str]) -> str:
    """``dev_fixture_<Suffix>``; Suffix zufällig oder aus ``fixture_id``."""
    suf = (fixture_id or "").strip()
    if not suf:
        return f"{_DEV_FIXTURE_PREFIX}{uuid.uuid4().hex[:16]}"
    if not _RE_SUFFIX.fullmatch(suf):
        raise ValueError("fixture_id: nur A–Z a–z 0–9 _ - erlaubt.")
    if len(suf) > 80:
        raise ValueError("fixture_id: maximal 80 Zeichen.")
    return f"{_DEV_FIXTURE_PREFIX}{suf}"


def _sample_chapters_and_script(job_id_short: str) -> Tuple[List[Chapter], str]:
    c1 = (
        "Kurzfassung: Dieses Skript wird nur für Entwicklungstests erzeugt. "
        "Es verweist auf keine echte Videotranskription und braucht keinen API-Zugriff."
    )
    c2 = (
        "Hintergrund: Strukturierte Kapitel helfen später bei Szenenplan und Schnittplanung.\n\n"
        "Zweiter Absatz im gleichen Kapitel zeigt mehrzeilige Inhalte ohne YouTube-Fetch."
    )
    c3 = (
        "Fazit: Mit einem abgeschlossenen ScriptJob und diesem Text lassen sich "
        "„create-production-job“, „scene-plan/generate“, Review und Produktionsroutinen testen."
    )
    chapters = [
        Chapter(title="Einordnung und Hook", content=c1),
        Chapter(title="Kontext (mehrteilige Szene)", content=c2),
        Chapter(title="Fazit", content=c3),
    ]
    full_script = (
        "\n\n".join(ch.content.strip() for ch in chapters)
        + "\n\n[Fixture-Marker "
        + job_id_short
        + "]\n\n"
        + "(Nur lokaler Test — nicht für Veröffentlichung.)"
    )
    return chapters, full_script


if TYPE_CHECKING:
    from app.watchlist.firestore_repo import FirestoreWatchlistRepository


def seed_completed_script_job_fixture(
    *,
    fixture_job_id_raw: Optional[str],
    create_production_job: bool,
    repo: "FirestoreWatchlistRepository",
) -> Tuple[
    ScriptJob,
    GeneratedScript,
    Optional[ProductionJob],
    List[str],
]:
    """
    Schreibt completed ``script_job``, ``generated_script`` und optional ``production_jobs``.

    Raises:
        DevFixtureConflictError: Wenn bereits ein Eintrag unter derselben Job-ID besteht.
    """
    jid = finalize_fixture_job_id(fixture_job_id_raw)

    if repo.get_script_job(jid) is not None:
        raise DevFixtureConflictError(jid)
    if repo.get_generated_script(jid) is not None:
        raise DevFixtureConflictError(jid)

    now = _utc_now_iso()
    chapters, full_script = _sample_chapters_and_script(jid)
    wc = count_words(full_script)
    vid_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    gs = GeneratedScript(
        id=jid,
        script_job_id=jid,
        source_url=vid_url,
        source_type="youtube_transcript",
        title=f"Dev Fixture Skript ({jid})",
        hook="Festes Testskript ohne Transkript — nur mit ENABLE_TEST_FIXTURES.",
        chapters=chapters,
        full_script=full_script,
        sources=["https://example.com/dev_fixture_source"],
        warnings=["Dies ist ein Nur-Test-Artefakt (ENABLE_TEST_FIXTURES)."],
        word_count=wc,
        video_template="generic",
        created_at=now,
    )

    job = ScriptJob(
        id=jid,
        video_id=jid,
        channel_id="UC_DEV_FIXTURE",
        video_url=vid_url,
        status="completed",
        source_type="youtube_transcript",
        target_language="de",
        duration_minutes=10,
        video_template="generic",
        created_at=now,
        started_at=now,
        completed_at=now,
        error="",
        error_code="",
        generated_script_id=jid,
        review_result_id=None,
        attempt_count=1,
        last_attempt_at=now,
    )

    repo.create_generated_script(gs)
    repo.create_script_job(job)

    pj_done: Optional[ProductionJob] = None
    warns: List[str] = []

    if create_production_job:
        if repo.get_production_job(jid) is not None:
            warns.append(
                "production_jobs existierte bereits unter derselben ID; übersprungen."
            )
        else:
            pj = ProductionJob(
                id=jid,
                generated_script_id=jid,
                script_job_id=jid,
                status="queued",
                content_category="dev_fixture",
                visual_style="",
                narrator_style="",
                thumbnail_prompt="",
                video_template="generic",
                created_at=now,
                updated_at=now,
            )
            repo.create_production_job(pj)
            pj_done = pj

    return job, gs, pj_done, warns
