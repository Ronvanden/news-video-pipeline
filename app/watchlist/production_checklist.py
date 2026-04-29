"""BA 7.3 — Hilfslogik für Production-Checklisten (Firestore-agnostisch)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.watchlist.firestore_repo import FirestoreWatchlistRepository
from app.watchlist.models import ProductionChecklist


PRODUCTION_STATUS_ORDER: List[str] = [
    "queued",
    "planning_ready",
    "assets_ready",
    "voice_ready",
    "editing_ready",
    "upload_ready",
    "published",
]


def _rank(status: str) -> int:
    s = (status or "").strip()
    if s in PRODUCTION_STATUS_ORDER:
        return PRODUCTION_STATUS_ORDER.index(s)
    return -1


def compute_target_production_status(
    *,
    current_status: str,
    production_job_id: str,
    repo: FirestoreWatchlistRepository,
    checklist: Optional[ProductionChecklist],
) -> Optional[str]:
    """Neuer Ziel-Status oder None wenn unverändert / nicht automatisch gesetzt werden soll."""
    if current_status in ("failed", "skipped"):
        return None
    if current_status in ("in_progress", "completed"):
        return None

    rank = 0
    try:
        if repo.get_scene_plan(production_job_id):
            rank = max(rank, 1)
        if repo.get_scene_assets(production_job_id):
            rank = max(rank, 2)
        if repo.get_voice_plan(production_job_id):
            rank = max(rank, 3)
    except Exception:
        return None

    if checklist is not None:
        if checklist.editing_ready:
            rank = max(rank, 4)
        if checklist.upload_ready:
            rank = max(rank, 5)
        if checklist.published:
            rank = max(rank, 6)

    target = PRODUCTION_STATUS_ORDER[rank]
    if target == current_status:
        return None
    cur_r = _rank(current_status)
    if cur_r < 0:
        # unbekannter Status: vorsichtig auf Ziel setzen
        return target
    if rank < cur_r:
        return None
    return target


def auto_checklist_booleans(
    repo: FirestoreWatchlistRepository,
    production_job_id: str,
) -> Dict[str, Any]:
    """Felder, die aus vorhandenen Artefakten abgeleitet werden (überschreibt true, nie false erzwingen)."""
    pid = (production_job_id or "").strip()
    out: Dict[str, Any] = {}
    if not pid:
        return out

    try:
        pj = repo.get_production_job(pid)
    except Exception:
        return out

    script_ok = False
    if pj is not None:
        gid = (pj.generated_script_id or "").strip()
        if gid:
            try:
                gs = repo.get_generated_script(gid)
                script_ok = gs is not None
            except Exception:
                script_ok = False
    out["script_ready"] = script_ok

    try:
        out["scene_plan_ready"] = repo.get_scene_plan(pid) is not None
        out["scene_assets_ready"] = repo.get_scene_assets(pid) is not None
        out["voice_plan_ready"] = repo.get_voice_plan(pid) is not None
        out["render_manifest_ready"] = repo.get_render_manifest(pid) is not None
    except Exception:
        return out
    return out
