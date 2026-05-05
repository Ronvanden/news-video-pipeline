"""BA 10.6/10.7 — Founder Dashboard (HTML + optionale JSON-Config)."""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from app.founder_dashboard.html import get_founder_dashboard_html
from app.founder_dashboard.final_render_dry_run import build_final_render_dry_run_for_local_preview
from app.founder_dashboard.local_preview_panel import (
    build_local_preview_panel_payload,
    default_local_preview_out_root,
    now_iso_utc,
    load_local_preview_human_approval,
    local_preview_file_media_type,
    local_preview_safe_resolve_run_dir,
    local_preview_safe_resolve_file,
    load_local_preview_saved_result,
    build_file_urls_for_run,
    build_status_cards_from_saved_result,
    build_approval_gate_from_run,
    validate_local_preview_run_id,
)

router = APIRouter(tags=["founder-dashboard"])


@router.get("/founder/dashboard", response_class=HTMLResponse)
async def founder_dashboard_page() -> HTMLResponse:
    """Read-only Single-Page-UI; Story-Engine nur clientseitig per fetch."""
    return HTMLResponse(content=get_founder_dashboard_html())


def production_proof_summary_payload() -> dict:
    """Read-only Kanon: Founder Proof-of-Production / Manual-URL-Spine (keine Secrets)."""
    return {
        "summary_version": "production-proof-v1",
        "motto": "produce_one_real_asset_end_to_end",
        "canonical_spine": {
            "primary_http": {
                "method": "POST",
                "path": "/story-engine/prompt-plan",
                "required_for_full_plan": ["manual_source_url"],
                "optional": ["manual_url_rewrite_mode", "template_override", "allow_live_provider_execution"],
            },
            "pipeline_code": "app.prompt_engine.pipeline.build_production_prompt_plan",
            "includes_ba_layers_on_plan": [
                "BA 12 production assembly",
                "BA 13 publishing preparation",
                "BA 14 performance feedback",
                "BA 15 production acceleration",
                "BA 16 monetization scale",
                "BA 17.0 viral upgrade (advisory, pre-assembly)",
                "BA 18.0 scene expansion (multi-beat prompts, pre-assembly)",
                "BA 19.0/20.2 run_asset_runner.py (placeholder or Leonardo live + manifest)",
                "BA 19.1 build_timeline_manifest.py (timeline_manifest.json)",
                "BA 19.2 render_final_story_video.py (local MP4 via ffmpeg)",
                "BA 20.0 build_full_voiceover.py (narration + smoke MP3 + manifest)",
                "BA 20.1 build_full_voiceover.py (ElevenLabs / OpenAI TTS optional)",
            ],
        },
        "script_only_fast_path": {
            "note": "GenerateScriptResponse contract only — does not attach BA12–16 plan fields.",
            "endpoints": [
                {"method": "POST", "path": "/generate-script"},
                {"method": "POST", "path": "/youtube/generate-script"},
            ],
        },
        "cli_helpers": [
            {"script": "scripts/run_url_to_demo.py", "role": "Single-URL → condensed JSON (rewrite + hooks + demo hints)"},
            {"script": "scripts/build_first_demo_video.py", "role": "Local MP4 from image + audio paths"},
            {"script": "scripts/run_batch_url_demo.py", "role": "Batch URLs"},
            {"script": "scripts/run_watch_approval.py", "role": "Watch approval radar (local JSON)"},
            {"script": "scripts/build_timeline_manifest.py", "role": "BA 19.1 — asset_manifest → timeline_manifest.json"},
            {"script": "scripts/render_final_story_video.py", "role": "BA 19.2 — timeline + images + audio → MP4 (ffmpeg)"},
            {"script": "scripts/build_full_voiceover.py", "role": "BA 20.0/20.1 — narration + smoke or ElevenLabs/OpenAI TTS MP3"},
            {"script": "scripts/run_asset_runner.py", "role": "BA 19.0/20.2 — scene_asset_pack → PNGs + asset_manifest (placeholder or Leonardo live)"},
        ],
        "docs": [
            "PIPELINE_PLAN.md — Founder Production Mode / Proof of Production",
            "GOLD_PRODUCTION_STANDARD.md — Firestore production_jobs reference path",
        ],
    }


@router.get("/founder/production-proof/summary")
async def founder_production_proof_summary() -> dict:
    """Kompakte Orientierung für Proof-of-Production (statisch, kein SaaS)."""
    return production_proof_summary_payload()


@router.get("/founder/dashboard/local-preview/panel")
async def founder_local_preview_panel() -> dict:
    """BA 22.0 — read-only Local-Preview-Übersicht (Artefakt-Flags, Pfade, CLI-/Doku-Aktionen)."""
    return build_local_preview_panel_payload()


@router.get("/founder/dashboard/local-preview/file/{run_id}/{filename}")
async def founder_local_preview_file(run_id: str, filename: str) -> FileResponse:
    """BA 22.2 — sichere Auslieferung nur aus ``output/local_preview_<run_id>/`` (Whitelist, kein Symlink)."""
    path = local_preview_safe_resolve_file(default_local_preview_out_root(), run_id, filename)
    if path is None:
        raise HTTPException(status_code=404, detail="not found")
    return FileResponse(
        path,
        media_type=local_preview_file_media_type(filename),
    )


_BA223_RUN_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,80}$")


def _validate_ba223_run_id(run_id: str) -> bool:
    s = (run_id or "").strip()
    if not s or ".." in s or "/" in s or "\\" in s:
        return False
    return bool(_BA223_RUN_ID_RE.fullmatch(s))


class LocalPreviewRunMiniFixtureRequest(BaseModel):
    run_id: str = Field(default="mini_e2e", min_length=1, max_length=80)
    force_burn: bool = False
    skip_preflight: bool = False

    model_config = {"extra": "forbid"}

class LocalPreviewApprovalNoteRequest(BaseModel):
    note: str = Field(default="", max_length=400)

    model_config = {"extra": "forbid"}


_lp_pipeline_mod: Optional[Any] = None


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_local_preview_pipeline_mod() -> Any:
    """Lädt `scripts/run_local_preview_pipeline.py` einmalig als Modul (kein subprocess)."""
    global _lp_pipeline_mod
    if _lp_pipeline_mod is not None:
        return _lp_pipeline_mod
    root = _repo_root()
    p = root / "scripts" / "run_local_preview_pipeline.py"
    spec = importlib.util.spec_from_file_location("run_local_preview_pipeline_ba223", p)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {p}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _lp_pipeline_mod = mod
    return mod


def _ba223_fixture_paths() -> tuple[Path, Path]:
    root = _repo_root()
    d = root / "fixtures" / "local_preview_mini"
    return d / "mini_timeline_manifest.json", d / "mini_narration.txt"


def _ba223_preflight_check() -> Dict[str, Any]:
    return dict(_load_local_preview_pipeline_mod().check_local_ffmpeg_tools())


def _ba223_run_mini_fixture(*, out_root: Path, run_id: str, force_burn: bool) -> Dict[str, Any]:
    """Startet den festen Mini-Fixture-Run (ohne freie Pfade aus Request)."""
    timeline, narration = _ba223_fixture_paths()
    pl = _load_local_preview_pipeline_mod()
    return dict(
        pl.run_local_preview_pipeline(
            timeline,
            narration,
            out_root=out_root,
            run_id=run_id,
            motion_mode="static",
            subtitle_mode="simple",
            subtitle_style="typewriter",
            subtitle_source="narration",
            audio_path=None,
            force_burn=bool(force_burn),
        )
    )


@router.post("/founder/dashboard/local-preview/run-mini-fixture")
async def founder_local_preview_run_mini_fixture(req: LocalPreviewRunMiniFixtureRequest) -> dict:
    """
    BA 22.3 — Operator-Button: startet den festen Mini-Fixture-Preview-Lauf (lokal/dev),
    ohne freie Pfade, ohne Cloud/Provider-Calls.
    """
    run_id = (req.run_id or "").strip() or "mini_e2e"
    if not _validate_ba223_run_id(run_id):
        raise HTTPException(status_code=422, detail="invalid run_id")
    out_root = default_local_preview_out_root()

    if not req.skip_preflight:
        chk = await run_in_threadpool(_ba223_preflight_check)
        if not chk.get("ok"):
            return {
                "ok": False,
                "message": "Preflight fehlgeschlagen (ffmpeg/ffprobe).",
                "run_id": run_id,
                "preflight": chk,
                "warnings": list(chk.get("warnings") or []),
                "blocking_reasons": list(chk.get("missing_tools") or []),
            }

    try:
        result = await run_in_threadpool(_ba223_run_mini_fixture, out_root=out_root, run_id=run_id, force_burn=req.force_burn)
    except Exception as e:
        msg = str(getattr(e, "message", "") or str(e) or "unknown error")
        if len(msg) > 400:
            msg = msg[:397] + "..."
        return {
            "ok": False,
            "message": "Mini-Fixture Preview-Lauf fehlgeschlagen: " + msg,
            "run_id": run_id,
            "warnings": [],
            "blocking_reasons": ["exception"],
        }

    verdict = str(result.get("verdict") or "").strip().upper() or "UNKNOWN"
    compact = {
        "result_contract": result.get("result_contract"),
        "verdict": verdict,
        "warning_classification": result.get("warning_classification"),
        "founder_quality_decision": result.get("founder_quality_decision"),
        "quality_checklist": result.get("quality_checklist"),
        "subtitle_quality_check": result.get("subtitle_quality_check"),
        "sync_guard": result.get("sync_guard"),
        "warnings": result.get("warnings") or [],
        "blocking_reasons": result.get("blocking_reasons") or [],
        "paths": result.get("paths") or {},
    }
    panel = build_local_preview_panel_payload()
    return {
        "ok": True,
        "message": "Preview-Lauf abgeschlossen.",
        "run_id": run_id,
        "result": compact,
        "panel": panel,
        "warnings": list(result.get("warnings") or []),
        "blocking_reasons": list(result.get("blocking_reasons") or []),
    }


def _build_approval_gate_for_run_dir(run_dir: Path, run_id: str) -> Dict[str, Any]:
    saved = load_local_preview_saved_result(run_dir)
    scards = build_status_cards_from_saved_result(saved)
    urls = build_file_urls_for_run(run_dir, run_id)
    appr = load_local_preview_human_approval(run_dir)
    return build_approval_gate_from_run(run_id=run_id, status_cards=scards, file_urls=urls, approval_doc=appr)


@router.post("/founder/dashboard/local-preview/approve/{run_id}")
async def founder_local_preview_approve(run_id: str, req: LocalPreviewApprovalNoteRequest) -> dict:
    """BA 22.5 — schreibt `human_approval.json` (approved), nur unter output/local_preview_<run_id>/."""
    if not validate_local_preview_run_id(run_id):
        raise HTTPException(status_code=422, detail="invalid run_id")
    out_root = default_local_preview_out_root()
    run_dir = local_preview_safe_resolve_run_dir(out_root, run_id)
    if run_dir is None:
        raise HTTPException(status_code=404, detail="run not found")

    gate = await run_in_threadpool(_build_approval_gate_for_run_dir, run_dir, run_id)
    if not gate.get("actions", {}).get("approve_enabled"):
        return JSONResponse(
            status_code=409,
            content={
                "ok": False,
                "run_id": run_id,
                "approval_gate": gate,
                "message": gate.get("reason") or "not eligible",
            },
        )

    def _write():
        doc = {
            "schema_version": "local_preview_human_approval_v1",
            "run_id": run_id,
            "status": "approved",
            "approved_at": now_iso_utc(),
            "approved_by": "local_operator",
            "note": (req.note or "").strip(),
            "source": "dashboard",
        }
        (run_dir / "human_approval.json").write_text(
            __import__("json").dumps(doc, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    await run_in_threadpool(_write)
    gate2 = await run_in_threadpool(_build_approval_gate_for_run_dir, run_dir, run_id)
    return {"ok": True, "run_id": run_id, "approval_gate": gate2, "message": "approved"}


@router.post("/founder/dashboard/local-preview/revoke-approval/{run_id}")
async def founder_local_preview_revoke_approval(run_id: str, req: LocalPreviewApprovalNoteRequest) -> dict:
    """BA 22.5 — schreibt `human_approval.json` (revoked)."""
    if not validate_local_preview_run_id(run_id):
        raise HTTPException(status_code=422, detail="invalid run_id")
    out_root = default_local_preview_out_root()
    run_dir = local_preview_safe_resolve_run_dir(out_root, run_id)
    if run_dir is None:
        raise HTTPException(status_code=404, detail="run not found")

    gate = await run_in_threadpool(_build_approval_gate_for_run_dir, run_dir, run_id)
    if not gate.get("actions", {}).get("revoke_enabled"):
        return JSONResponse(
            status_code=409,
            content={"ok": False, "run_id": run_id, "approval_gate": gate, "message": "revoke not allowed"},
        )

    def _write():
        doc = {
            "schema_version": "local_preview_human_approval_v1",
            "run_id": run_id,
            "status": "revoked",
            "approved_at": now_iso_utc(),
            "approved_by": "local_operator",
            "note": (req.note or "").strip(),
            "source": "dashboard",
        }
        (run_dir / "human_approval.json").write_text(
            __import__("json").dumps(doc, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    await run_in_threadpool(_write)
    gate2 = await run_in_threadpool(_build_approval_gate_for_run_dir, run_dir, run_id)
    return {"ok": True, "run_id": run_id, "approval_gate": gate2, "message": "revoked"}


@router.post("/founder/dashboard/local-preview/final-render/dry-run/{run_id}")
async def founder_local_preview_final_render_dry_run(run_id: str) -> dict:
    """BA 24.2 — read-only Dry-Run: prüft Gates + baut Final-Render-Contract (keine Dateien)."""
    if not validate_local_preview_run_id(run_id):
        raise HTTPException(status_code=422, detail="invalid run_id")
    out_root = default_local_preview_out_root()
    res = await run_in_threadpool(build_final_render_dry_run_for_local_preview, run_id=run_id, out_root=out_root)
    if not res.get("ok"):
        # missing run dir -> 404; alles andere -> 400
        msg = str(res.get("message") or "dry-run failed")
        if "not found" in msg:
            raise HTTPException(status_code=404, detail=msg)
        raise HTTPException(status_code=400, detail=msg)
    return res


@router.get("/founder/dashboard/config")
async def founder_dashboard_config() -> dict:
    """Statische Meta-Infos für Ops/Integrationstests (keine Secrets)."""
    return {
        "dashboard_version": "10.7-v1",
        "auth": False,
        "local_preview_panel_relative": {"method": "GET", "path": "/founder/dashboard/local-preview/panel"},
        "local_preview_run_mini_fixture_relative": {
            "method": "POST",
            "path": "/founder/dashboard/local-preview/run-mini-fixture",
        },
        "local_preview_approve_relative": {
            "method": "POST",
            "path": "/founder/dashboard/local-preview/approve/{run_id}",
        },
        "local_preview_revoke_approval_relative": {
            "method": "POST",
            "path": "/founder/dashboard/local-preview/revoke-approval/{run_id}",
        },
        "local_preview_final_render_dry_run_relative": {
            "method": "POST",
            "path": "/founder/dashboard/local-preview/final-render/dry-run/{run_id}",
        },
        "local_preview_file_relative": {
            "method": "GET",
            "path": "/founder/dashboard/local-preview/file/{run_id}/{filename}",
        },
        "production_proof_summary_relative": {"method": "GET", "path": "/founder/production-proof/summary"},
        "story_engine_relative": {
            "export_package": {"method": "POST", "path": "/story-engine/export-package"},
            "export_package_preview": {"method": "POST", "path": "/story-engine/export-package/preview"},
            "provider_readiness": {"method": "POST", "path": "/story-engine/provider-readiness"},
            "provider_prompts_optimize": {"method": "POST", "path": "/story-engine/provider-prompts/optimize"},
            "thumbnail_ctr": {"method": "POST", "path": "/story-engine/thumbnail-ctr"},
            "export_formats": {"method": "GET", "path": "/story-engine/export-formats"},
            "template_selector": {"method": "GET", "path": "/story-engine/template-selector"},
        },
    }
