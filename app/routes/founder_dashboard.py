"""BA 10.6/10.7 — Founder Dashboard (HTML + optionale JSON-Config)."""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from app.founder_dashboard.html import get_founder_dashboard_html

router = APIRouter(tags=["founder-dashboard"])


@router.get("/founder/dashboard", response_class=HTMLResponse)
async def founder_dashboard_page() -> HTMLResponse:
    """Read-only Single-Page-UI; Story-Engine nur clientseitig per fetch."""
    return HTMLResponse(content=get_founder_dashboard_html())


@router.get("/founder/dashboard/config")
async def founder_dashboard_config() -> dict:
    """Statische Meta-Infos für Ops/Integrationstests (keine Secrets)."""
    return {
        "dashboard_version": "10.7-v1",
        "auth": False,
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
