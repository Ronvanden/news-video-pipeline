"""BA 10.6/10.7 — Founder Dashboard (HTML + optionale JSON-Config)."""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from app.founder_dashboard.html import get_founder_dashboard_html

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
                "BA 19.0 run_asset_runner.py (placeholder PNGs + manifest)",
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


@router.get("/founder/dashboard/config")
async def founder_dashboard_config() -> dict:
    """Statische Meta-Infos für Ops/Integrationstests (keine Secrets)."""
    return {
        "dashboard_version": "10.7-v1",
        "auth": False,
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
