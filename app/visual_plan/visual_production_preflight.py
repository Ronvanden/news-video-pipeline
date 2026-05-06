"""BA 27.9 — Visual production preflight summary (read-only, no calls)."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

PreflightStatus = Literal["ready", "needs_review", "blocked"]


def _s(v: Any) -> str:
    return str(v or "").strip()


def build_visual_production_preflight_result(
    *,
    asset_manifest: Optional[Dict[str, Any]] = None,
    production_summary: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    man = asset_manifest if isinstance(asset_manifest, dict) else {}
    ps = production_summary if isinstance(production_summary, dict) else {}

    blocking: List[str] = []
    warns: List[str] = []
    checks: Dict[str, Any] = {}
    counts: Dict[str, Any] = {}

    has_manifest = isinstance(man, dict) and isinstance(man.get("assets"), list)
    checks["asset_manifest_present"] = bool(has_manifest)

    approval = man.get("production_asset_approval_result") if isinstance(man.get("production_asset_approval_result"), dict) else None
    checks["approval_gate_present"] = bool(isinstance(approval, dict))
    approval_status = _s(approval.get("approval_status") if isinstance(approval, dict) else "")
    checks["approval_status"] = approval_status

    ready_for_render = bool(ps.get("ready_for_render") is True)
    checks["ready_for_render"] = ready_for_render

    has_cost = isinstance(man.get("visual_cost_summary"), dict)
    checks["visual_cost_summary_present"] = bool(has_cost)

    ref_index_present = bool(ps.get("asset_manifest_reference_index_path") or ps.get("asset_manifest_reference_index"))
    checks["reference_index_present"] = ref_index_present

    ref_payloads_present = isinstance(man.get("reference_provider_payload_summary"), dict) or any(
        isinstance(a, dict) and isinstance(a.get("reference_provider_payloads"), dict)
        for a in (man.get("assets") or [])
        if isinstance(man.get("assets"), list)
    )
    checks["reference_payloads_present"] = bool(ref_payloads_present)

    cont_summary_present = isinstance(man.get("continuity_wiring_summary"), dict)
    checks["continuity_summary_present"] = bool(cont_summary_present)

    if not has_manifest:
        blocking.append("asset_manifest_missing_or_invalid")
    if not isinstance(approval, dict):
        blocking.append("approval_gate_missing")
    elif approval_status == "blocked":
        blocking.append("approval_status_blocked")
    elif approval_status == "needs_review":
        warns.append("approval_status_needs_review")
    elif approval_status != "approved":
        warns.append("approval_status_unknown")

    # non-blocking quality signals
    if not has_cost:
        warns.append("visual_cost_summary_missing")
    if not ref_index_present:
        warns.append("asset_manifest_reference_index_missing")
    if not ref_payloads_present:
        warns.append("reference_provider_payloads_missing")
    if not cont_summary_present:
        warns.append("continuity_summary_missing")

    # status decision
    status: PreflightStatus
    if blocking:
        status = "blocked"
    elif approval_status == "approved" and ready_for_render:
        status = "ready" if not warns else "needs_review"
    else:
        status = "needs_review"

    ok = status != "blocked"

    return {
        "ok": bool(ok),
        "preflight_status": status,
        "blocking_reasons": list(dict.fromkeys([_s(x) for x in blocking if _s(x)])),
        "warnings": list(dict.fromkeys([_s(x) for x in warns if _s(x)])),
        "checks": checks,
        "counts": counts,
        "preflight_version": "ba27_9_v1",
    }

