"""BA 10.6/10.7 — Founder Dashboard (HTML + optionale JSON-Config)."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse

from app.founder_dashboard.html import get_founder_dashboard_html
from app.founder_dashboard.local_preview_panel import (
    build_local_preview_panel_payload,
    default_local_preview_out_root,
    local_preview_file_media_type,
    local_preview_safe_resolve_file,
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


@router.get("/founder/dashboard/config")
async def founder_dashboard_config() -> dict:
    """Statische Meta-Infos für Ops/Integrationstests (keine Secrets)."""
    return {
        "dashboard_version": "10.7-v1",
        "auth": False,
        "local_preview_panel_relative": {"method": "GET", "path": "/founder/dashboard/local-preview/panel"},
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
