"""BA 26.9c — Production Asset Approval Gate (asset_manifest-based, dry, no provider calls)."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Tuple

ApprovalStatusLiteral = Literal["approved", "blocked", "needs_review"]


def _s(v: Any) -> str:
    return str(v or "").strip()


def _b(v: Any) -> bool:
    return bool(v is True)


def _list_str(v: Any) -> List[str]:
    if v is None:
        return []
    if isinstance(v, list):
        out: List[str] = []
        for x in v:
            t = _s(x)
            if t:
                out.append(t)
        return out
    t = _s(v)
    return [t] if t else []


def _is_overlay_kind(kind: str) -> bool:
    k = _s(kind).lower()
    return k in ("final_text_overlay", "subtitle", "lower_third", "title_card", "label")


def _asset_kind(asset: Dict[str, Any]) -> str:
    return _s(asset.get("visual_asset_kind") or asset.get("asset_type") or "")


def _provider_effective(asset: Dict[str, Any]) -> str:
    return _s(
        asset.get("provider_used")
        or asset.get("manual_provider_override")
        or asset.get("recommended_provider")
        or asset.get("routed_visual_provider")
        or asset.get("routed_image_provider")
        or asset.get("image_provider_routed")
        or asset.get("video_provider_routed")
        or ""
    ).lower()


def _selected_asset_path(asset: Dict[str, Any]) -> str:
    return _s(asset.get("selected_asset_path") or asset.get("generated_image_path") or asset.get("image_path") or asset.get("video_path") or "")


def evaluate_production_asset_approval(
    manifest: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Returns production_asset_approval_result dict:
      ok, approval_status, blocking_reasons, warnings, counts...
    """
    assets = manifest.get("assets")
    if not isinstance(assets, list) or not assets:
        return {
            "ok": False,
            "approval_status": "blocked",
            "blocking_reasons": ["asset_manifest_assets_missing_or_empty"],
            "warnings": [],
            "assets_checked": 0,
            "accepted_count": 0,
            "locked_count": 0,
            "needs_review_count": 0,
            "missing_asset_count": 0,
            "overlay_pending_count": 0,
            "cost_warning_count": 0,
            "gate_version": "ba26_9c_v1",
        }

    blockers: List[str] = []
    warns: List[str] = []
    accepted = 0
    locked = 0
    needs_review = 0
    missing = 0
    overlay_pending = 0
    cost_warn = 0

    for a in assets:
        if not isinstance(a, dict):
            continue
        sn = int(a.get("scene_number", 0) or 0)
        kind = _asset_kind(a)
        prov = _provider_effective(a)
        decision = _s(a.get("asset_decision_status") or "pending").lower()
        is_locked = _b(a.get("locked_for_render")) or decision == "locked"
        pol = _s(a.get("visual_policy_status") or "")
        text_sensitive = _b(a.get("text_sensitive")) or bool(_list_str(a.get("overlay_intent")))
        overlay_intent = _list_str(a.get("overlay_intent"))
        guard_applied = a.get("visual_text_guard_applied")
        if guard_applied is None:
            # fallback: check marker in effective prompt if present
            effp = _s(a.get("visual_prompt_effective") or a.get("prompt_used_effective") or "")
            guard_applied = "[visual_no_text_guard_v26_4]" in effp
        guard_applied = bool(guard_applied)

        sel = _selected_asset_path(a)
        has_media = bool(sel)

        if decision == "accepted":
            accepted += 1
        if is_locked:
            locked += 1
        if pol == "needs_review":
            needs_review += 1
            blockers.append(f"scene_{sn}:visual_policy_needs_review")

        if decision in ("rejected", "needs_regeneration"):
            blockers.append(f"scene_{sn}:decision_{decision}")

        # Guard must exist for non-render assets
        if prov != "render_layer" and not guard_applied:
            blockers.append(f"scene_{sn}:no_text_guard_missing")

        # text_sensitive must have overlay_intent (per spec)
        if _b(a.get("text_sensitive")) and not overlay_intent:
            blockers.append(f"scene_{sn}:text_sensitive_missing_overlay_intent")

        # Provider used should be present for generated non-render assets (best effort)
        if prov != "render_layer" and not _s(a.get("provider_used")) and not _s(a.get("generation_mode")):
            warns.append(f"scene_{sn}:provider_used_missing")

        # Missing asset file reference for non-render providers is blocking
        if prov != "render_layer" and not has_media:
            missing += 1
            blockers.append(f"scene_{sn}:missing_asset_path")

        # Overlay kinds: render_layer expects overlay_intent; missing is pending overlay (needs_review)
        if _is_overlay_kind(kind) or prov == "render_layer":
            if not overlay_intent:
                overlay_pending += 1
                warns.append(f"scene_{sn}:overlay_intent_missing_for_render_layer")

        # Cost warnings: if present in asset
        if _s(a.get("visual_cost_warning")):
            cost_warn += 1

    # Deduplicate
    blockers_u = list(dict.fromkeys([b for b in blockers if b]))
    warns_u = list(dict.fromkeys([w for w in warns if w]))

    status: ApprovalStatusLiteral
    ok: bool
    if blockers_u:
        status = "blocked"
        ok = False
    elif needs_review > 0 or overlay_pending > 0:
        status = "needs_review"
        ok = True
    else:
        status = "approved"
        ok = True

    return {
        "ok": ok,
        "approval_status": status,
        "blocking_reasons": blockers_u,
        "warnings": warns_u,
        "assets_checked": len([x for x in assets if isinstance(x, dict)]),
        "accepted_count": int(accepted),
        "locked_count": int(locked),
        "needs_review_count": int(needs_review),
        "missing_asset_count": int(missing),
        "overlay_pending_count": int(overlay_pending),
        "cost_warning_count": int(cost_warn),
        "gate_version": "ba26_9c_v1",
    }


def apply_production_asset_approval_to_manifest(manifest: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(manifest or {})
    out["production_asset_approval_result"] = evaluate_production_asset_approval(out)
    return out

