"""Execution Queue (BA 7.8): Abbild von ``production_files`` auf ausführbare Jobs — ohne Provider."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from app.watchlist.cost_calculator import CategoryMoneyV1, estimated_cost_per_execution_job
from app.watchlist.firestore_repo import FirestoreUnavailableError, FirestoreWatchlistRepository
from app.watchlist.models import (
    ExecutionJob,
    ExecutionJobTypeLiteral,
    ProductionFileRecord,
    ProductionFileTypeLiteral,
    SceneAssets,
    VoicePlan,
)


def execution_job_document_id_from_production_file(record: ProductionFileRecord) -> str:
    rid = (record.id or "").strip()
    if rid.startswith("pfile_"):
        return "exjob_" + rid[6:]
    if rid:
        return "exjob_" + rid
    return "exjob_empty"


def map_file_type_to_job_type(ft: ProductionFileTypeLiteral) -> ExecutionJobTypeLiteral:
    if ft == "voice":
        return "voice_generate"
    if ft == "image":
        return "image_generate"
    if ft == "video":
        return "video_generate"
    if ft == "thumbnail":
        return "thumbnail_generate"
    return "export_package"


def priority_for_job(job_type: ExecutionJobTypeLiteral) -> int:
    if job_type == "voice_generate":
        return 1
    if job_type == "video_generate":
        return 2
    if job_type == "image_generate":
        return 3
    if job_type == "thumbnail_generate":
        return 4
    return 5


def scene_optional_from_production_file(pf: ProductionFileRecord) -> Optional[int]:
    sn = getattr(pf, "scene_number", 0)
    return int(sn) if isinstance(sn, int) and sn > 0 else None


def _load_assets(
    repo: FirestoreWatchlistRepository,
    pid: str,
) -> Tuple[Optional[SceneAssets], Optional[VoicePlan]]:
    try:
        sa = repo.get_scene_assets(pid)
        vp = repo.get_voice_plan(pid)
    except FirestoreUnavailableError:
        raise
    return sa, vp


def build_input_payload(
    pf: ProductionFileRecord,
    *,
    repo: FirestoreWatchlistRepository,
    production_job_id: str,
    job_type: ExecutionJobTypeLiteral,
) -> Dict[str, Any]:
    pid = production_job_id.strip()
    payload: Dict[str, Any] = {
        "storage_path": pf.storage_path or "",
        "production_file_type": pf.file_type,
        "planned_status": getattr(pf, "status", "planned"),
    }

    scene_no = getattr(pf, "scene_number", 0)
    idx = scene_no - 1 if isinstance(scene_no, int) and scene_no >= 1 else -1

    try:
        sa, vp = _load_assets(repo, pid)
    except FirestoreUnavailableError:
        raise

    hints: List[str] = []

    if job_type in ("image_generate", "video_generate") and sa is not None and idx >= 0:
        scenes = sa.scenes or []
        if idx < len(scenes):
            s = scenes[idx]
            payload["image_prompt"] = getattr(s, "image_prompt", "") or ""
            payload["video_prompt"] = getattr(s, "video_prompt", "") or ""
            payload["thumbnail_prompt"] = getattr(s, "thumbnail_prompt", "") or ""
            payload["scene_title"] = getattr(s, "title", "") or ""

    if job_type == "thumbnail_generate" and sa is not None and sa.scenes:
        tb = getattr(sa.scenes[0], "thumbnail_prompt", "") or ""
        payload["thumbnail_prompt"] = tb
        try:
            pj = repo.get_production_job(pid)
        except FirestoreUnavailableError:
            raise
        if pj is not None:
            ftp = getattr(pj, "thumbnail_prompt", "") or ""
            if ftp:
                payload["production_thumbnail_prompt"] = ftp

    if job_type == "voice_generate":
        if vp is not None and getattr(vp, "blocks", None) and idx >= 0:
            blocks = vp.blocks or []
            if idx < len(blocks):
                b = blocks[idx]
                payload["voice_text"] = getattr(b, "voice_text", "") or ""
                payload["tts_hint"] = getattr(b, "tts_provider_hint", "generic")
                payload["estimated_duration_seconds"] = getattr(
                    b, "estimated_duration_seconds", 1
                )
        elif sa is not None and idx >= 0:
            scs = getattr(sa, "scenes", None) or []
            if idx < len(scs):
                payload["voice_text"] = (
                    getattr(scs[idx], "voiceover_chunk", "") or ""
                )

    if job_type == "export_package":
        payload["formats"] = [pf.file_type]

    if not payload.get("voice_text") and job_type == "voice_generate":
        hints.append("Voice-Text fehlt in voice_plan/scene_assets — Felder später füllen.")

    payload["hints"] = "; ".join(hints)

    return payload


def build_execution_job_stub(
    pf: ProductionFileRecord,
    *,
    production_job_id: str,
    repo: FirestoreWatchlistRepository,
    cat: CategoryMoneyV1,
    file_type_counts: Dict[str, int],
    now_iso: str,
) -> ExecutionJob:
    eid = execution_job_document_id_from_production_file(pf)
    jt = map_file_type_to_job_type(pf.file_type)

    est = estimated_cost_per_execution_job(
        pf,
        cat=cat,
        file_type_counts=file_type_counts,
    )

    try:
        ip = build_input_payload(
            pf,
            repo=repo,
            production_job_id=production_job_id,
            job_type=jt,
        )
    except FirestoreUnavailableError:
        raise

    pj_id = production_job_id.strip()
    pj_fid = (pf.id or "").strip()

    ej = ExecutionJob(
        id=eid,
        production_job_id=pj_id,
        production_file_id=pj_fid or None,
        job_type=jt,
        provider_name=pf.provider_name,
        scene_number=scene_optional_from_production_file(pf),
        status="queued",
        priority=priority_for_job(jt),
        input_payload=ip,
        output_reference="",
        estimated_cost=est,
        error="",
        error_code="",
        created_at=now_iso,
        updated_at=now_iso,
    )
    return ej
