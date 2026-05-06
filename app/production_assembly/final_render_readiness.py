"""BA 29.5 — Final render readiness after human preview review (no render)."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from app.production_assembly.human_preview_review import normalize_human_preview_review_result

_READINESS_VERSION = "ba29_5_v1"

ReadinessStatus = Literal["ready", "needs_review", "blocked"]


def _s(v: Any) -> str:
    return str(v or "").strip()


def build_final_render_readiness_result(
    *,
    production_summary: Dict[str, Any],
    final_render_dry_run: Optional[Dict[str, Any]] = None,
    local_preview_render_result: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Combine technical signals (dry-run / local preview) with human_preview_review_result.
    """
    ps = production_summary if isinstance(production_summary, dict) else {}
    hr = normalize_human_preview_review_result(
        ps.get("human_preview_review_result") if isinstance(ps.get("human_preview_review_result"), dict) else None
    )
    warns: List[str] = []
    blocking: List[str] = []

    preview_doc = local_preview_render_result
    if preview_doc is None and isinstance(ps.get("local_preview_render_result"), dict):
        preview_doc = ps.get("local_preview_render_result")

    preview_ok = bool(isinstance(preview_doc, dict) and preview_doc.get("ok") is True and _s(preview_doc.get("output_video_path")))
    if not preview_ok:
        warns.append("local_preview_missing_or_failed")

    dry_doc = final_render_dry_run
    dry_ok = True
    if isinstance(dry_doc, dict):
        dry_ok = bool(dry_doc.get("ok") is True)
        if not dry_ok:
            warns.append("final_render_dry_run_not_ok")

    technical_ready = bool(preview_ok and dry_ok)

    human_st = _s(hr.get("review_status")).lower()
    human_approved = human_st == "approved" and bool(hr.get("approved_for_final_render"))

    if human_st == "rejected":
        blocking.append("human_preview_rejected")
        status: ReadinessStatus = "blocked"
    elif human_st in ("pending", "needs_changes"):
        if human_st == "pending":
            blocking.append("human_preview_pending")
        else:
            blocking.append("human_preview_needs_changes")
        status = "needs_review"
    elif not human_approved:
        blocking.append("human_preview_not_approved_for_final_render")
        status = "needs_review"
    elif not technical_ready:
        blocking.append("technical_inputs_not_ready")
        status = "needs_review"
    else:
        status = "ready"

    ok = status == "ready"

    return {
        "ok": bool(ok),
        "readiness_status": status,
        "technical_ready": bool(technical_ready),
        "human_review_approved": bool(human_approved),
        "blocking_reasons": list(dict.fromkeys([_s(b) for b in blocking if _s(b)])),
        "warnings": list(dict.fromkeys([_s(w) for w in warns if _s(w)])),
        "readiness_version": _READINESS_VERSION,
    }
