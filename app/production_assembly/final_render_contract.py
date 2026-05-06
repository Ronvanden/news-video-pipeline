"""BA 28.5 — Final render dry-run contract from render_input_bundle (no ffmpeg call)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional


def _s(v: Any) -> str:
    return str(v or "").strip()


def build_final_render_dry_run_result(
    *,
    input_bundle: Dict[str, Any],
    input_bundle_path: Optional[str] = None,
) -> Dict[str, Any]:
    b = input_bundle if isinstance(input_bundle, dict) else {}
    missing: List[str] = []
    blocking: List[str] = []
    warnings: List[str] = []

    ready = bool(b.get("ready_for_render") is True)
    status = _s(b.get("render_readiness_status")).lower()
    if not ready or status in ("blocked", "needs_review"):
        blocking.append("not_ready_for_render")

    for k in ("asset_manifest_path", "production_summary_path"):
        if not _s(b.get(k)):
            missing.append(k)
    if not _s(b.get("motion_timeline_manifest_path")):
        warnings.append("motion_timeline_manifest_missing")

    would_render = ready and not blocking and not missing
    estimated_out = None
    if input_bundle_path:
        try:
            estimated_out = str((Path(input_bundle_path).resolve().parent / "final_render.mp4").resolve())
        except Exception:
            estimated_out = None

    steps = [
        {"step": "validate_inputs", "ok": bool(not missing), "missing": missing},
        {"step": "compose_timeline", "ok": bool(_s(b.get("motion_timeline_manifest_path"))), "note": "dry_run_only"},
        {"step": "build_ffmpeg_command", "ok": bool(would_render), "note": "preview_only_no_execution"},
    ]

    return {
        "ok": bool(would_render),
        "render_contract_version": "ba28_5_v1",
        "would_render": bool(would_render),
        "render_command_preview": "ffmpeg ... (dry-run preview only)",
        "input_bundle_path": input_bundle_path,
        "estimated_output_path": estimated_out,
        "missing_inputs": missing,
        "blocking_reasons": blocking,
        "warnings": list(dict.fromkeys([_s(w) for w in warnings if _s(w)])),
        "steps": steps,
    }

