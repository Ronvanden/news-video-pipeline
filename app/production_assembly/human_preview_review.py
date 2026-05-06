"""BA 29.4 — Human preview review gate (file-based, no dashboard writes)."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

ReviewStatus = Literal["pending", "approved", "rejected", "needs_changes"]

_REVIEW_VERSION = "ba29_4_v1"


def _s(v: Any) -> str:
    return str(v or "").strip()


def default_human_preview_review_result() -> Dict[str, Any]:
    return {
        "review_status": "pending",
        "reviewer": "",
        "review_notes": "",
        "approved_for_final_render": False,
        "blocking_reasons": [],
        "review_version": _REVIEW_VERSION,
    }


def normalize_human_preview_review_result(raw: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    base = default_human_preview_review_result()
    if not isinstance(raw, dict):
        return base
    out = {**base, **raw}
    out["review_version"] = _REVIEW_VERSION
    st = _s(out.get("review_status")).lower()
    if st not in ("pending", "approved", "rejected", "needs_changes"):
        st = "pending"
    out["review_status"] = st
    if not isinstance(out.get("blocking_reasons"), list):
        out["blocking_reasons"] = []
    out["blocking_reasons"] = [_s(x) for x in out["blocking_reasons"] if _s(x)]
    if st == "approved":
        if isinstance(raw, dict) and "approved_for_final_render" in raw:
            out["approved_for_final_render"] = bool(raw.get("approved_for_final_render"))
        else:
            out["approved_for_final_render"] = True
    else:
        out["approved_for_final_render"] = False
    return out


def apply_human_preview_review_patch(
    summary: Dict[str, Any],
    *,
    review_status: str,
    reviewer: str = "",
    review_notes: str = "",
    approved_for_final_render: Optional[bool] = None,
) -> Dict[str, Any]:
    """Return updated production_summary dict (shallow copy of wrapper, merged review)."""
    out = dict(summary or {})
    prev = normalize_human_preview_review_result(out.get("human_preview_review_result") if isinstance(out.get("human_preview_review_result"), dict) else None)
    st = _s(review_status).lower()
    if st not in ("pending", "approved", "rejected", "needs_changes"):
        st = "pending"
    prev["review_status"] = st
    prev["reviewer"] = _s(reviewer)
    prev["review_notes"] = _s(review_notes)

    if approved_for_final_render is not None:
        prev["approved_for_final_render"] = bool(approved_for_final_render)
    else:
        if st == "approved":
            prev["approved_for_final_render"] = True
        elif st in ("rejected", "pending", "needs_changes"):
            prev["approved_for_final_render"] = False

    blocks: List[str] = []
    if st == "rejected":
        blocks.append("human_preview_rejected")
    elif st == "needs_changes":
        blocks.append("human_preview_needs_changes")
    prev["blocking_reasons"] = list(dict.fromkeys(blocks))
    out["human_preview_review_result"] = prev
    return out
