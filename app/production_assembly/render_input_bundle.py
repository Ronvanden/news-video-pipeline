"""BA 28.4 — Render input bundle builder (no render)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def _s(v: Any) -> str:
    return str(v or "").strip()


def build_render_input_bundle(
    *,
    run_id: str,
    production_summary_path: Optional[str] = None,
    asset_manifest_path: Optional[str] = None,
    motion_clip_manifest_path: Optional[str] = None,
    motion_timeline_manifest_path: Optional[str] = None,
    subtitle_path: Optional[str] = None,
    voice_paths: Optional[List[str]] = None,
    clip_paths: Optional[List[str]] = None,
    image_paths: Optional[List[str]] = None,
    overlay_intents: Optional[List[str]] = None,
    ready_for_render: bool = False,
    render_readiness_status: str = "",
    warnings: Optional[List[str]] = None,
    blocking_reasons: Optional[List[str]] = None,
) -> Dict[str, Any]:
    return {
        "render_input_bundle_version": "ba28_4_v1",
        "run_id": _s(run_id),
        "ready_for_render": bool(ready_for_render),
        "render_readiness_status": _s(render_readiness_status),
        "production_summary_path": production_summary_path,
        "asset_manifest_path": asset_manifest_path,
        "motion_clip_manifest_path": motion_clip_manifest_path,
        "motion_timeline_manifest_path": motion_timeline_manifest_path,
        "subtitle_path": subtitle_path,
        "voice_paths": [p for p in (voice_paths or []) if _s(p)],
        "clip_paths": [p for p in (clip_paths or []) if _s(p)],
        "image_paths": [p for p in (image_paths or []) if _s(p)],
        "overlay_intents": [x for x in (overlay_intents or []) if _s(x)],
        "warnings": list(dict.fromkeys([_s(w) for w in (warnings or []) if _s(w)])),
        "blocking_reasons": list(dict.fromkeys([_s(b) for b in (blocking_reasons or []) if _s(b)])),
    }

