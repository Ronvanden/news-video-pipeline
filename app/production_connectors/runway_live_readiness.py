"""BA 32.1 — Runway Live Readiness für die Pipeline-Motion-Schicht.

Einzelclip-Live-Lauf existiert separat als ``scripts/runway_image_to_video_smoke.py``
(ENV ``RUNWAY_API_KEY``, keine Secrets hier).

Die Batch-Pipeline über ``build_motion_clip_result`` bleibt absichtlich **Dry-Run/Stub**,
bis ein kontrollierter Connector angebunden ist (kein Fake-Live).

Alle öffentlichen Strings sind operator-sicher (keine Secrets, keine .env-Inhalte).
"""

from __future__ import annotations

from typing import Any, Dict, List

# True sobald ``motion_provider_adapter`` echte Runway-Clips erzeugen kann (BA-Follow-up).
RUNWAY_LIVE_CONNECTOR_IMPLEMENTED: bool = False

_REASON_NOT_IMPLEMENTED = "runway_live_connector_not_implemented"


def augment_motion_clip_manifest_summary(
    base_summary: Dict[str, Any],
    *,
    allow_live_motion: bool,
    max_live_motion_clips: int,
) -> Dict[str, Any]:
    """
    Ergänzt ``motion_clip_manifest.summary`` um klare Runway-/Pipeline-Lage.

    - ``runway_live_available``: ob Live-Clips in dieser Pipeline möglich sind.
    - ``pipeline_motion_mode``: immer ``dry_run_stub_only`` bis Connector aktiv ist.
    """
    out = dict(base_summary)
    out["runway_live_available"] = bool(RUNWAY_LIVE_CONNECTOR_IMPLEMENTED)
    out["runway_live_connector_implemented"] = bool(RUNWAY_LIVE_CONNECTOR_IMPLEMENTED)
    out["pipeline_motion_mode"] = "dry_run_stub_only"
    if not RUNWAY_LIVE_CONNECTOR_IMPLEMENTED:
        out["runway_live_reason"] = _REASON_NOT_IMPLEMENTED

    gw: List[str] = []
    existing = out.get("global_warnings")
    if isinstance(existing, list):
        gw.extend(str(x) for x in existing if str(x or "").strip())

    if allow_live_motion:
        gw.append("runway_live_motion_requested_but_connector_not_implemented")
        gw.append("motion_stub_pipeline_no_real_runway_clip_from_motion_adapter")

    out["global_warnings"] = list(dict.fromkeys([x for x in gw if x]))

    if int(max_live_motion_clips or 0) > 0:
        out["runway_live_motion_clip_budget"] = int(max_live_motion_clips)

    return out


def controlled_run_blocking_reasons_for_live_motion(*, allow_live_motion: bool) -> List[str]:
    """Explizite Blocker, wenn Operator Live-Motion will, Connector aber fehlt."""
    if not allow_live_motion:
        return []
    if RUNWAY_LIVE_CONNECTOR_IMPLEMENTED:
        return []
    return ["runway_live_motion_requested_but_connector_not_implemented"]
