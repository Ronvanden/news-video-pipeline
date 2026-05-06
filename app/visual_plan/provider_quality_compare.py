"""BA 26.7c — Provider Quality Compare Smoke (dry, heuristisch, pure dict helpers).

Bewertet pro Asset (typisch asset_manifest.json assets[]) eine Provider-Empfehlung und Kandidatenliste,
ohne Provider live aufzurufen.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Tuple

from app.visual_plan.visual_costs import get_default_visual_unit_costs

ProviderLiteral = Literal["leonardo", "openai_images", "runway", "render_layer"]
CompareStatusLiteral = Literal["not_run", "dry_run_ready", "completed", "needs_review"]


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


def _norm_kind(asset: Dict[str, Any]) -> str:
    # prefer explicit visual_asset_kind; fallback to asset_type (manifest) or other hints
    k = _s(asset.get("visual_asset_kind") or "")
    if k:
        return k.lower()
    at = _s(asset.get("asset_type") or "")
    return at.lower()


def _effective_prompt(asset: Dict[str, Any]) -> str:
    return _s(
        asset.get("prompt_used_effective")
        or asset.get("visual_prompt_effective")
        or asset.get("visual_prompt")
        or ""
    )


def _provider_used(asset: Dict[str, Any]) -> str:
    return _s(
        asset.get("provider_used")
        or asset.get("manual_provider_override")
        or asset.get("routed_visual_provider")
        or ""
    ).lower()


def _is_overlay_kind(kind: str) -> bool:
    return kind in ("final_text_overlay", "subtitle", "lower_third", "title_card", "label")


def _pref_for_kind(kind: str, *, text_sensitive: bool, overlay_intent: List[str]) -> ProviderLiteral:
    if _is_overlay_kind(kind):
        return "render_layer"
    if kind == "motion_clip":
        return "runway"
    if kind == "thumbnail_base":
        return "openai_images"
    if text_sensitive or overlay_intent:
        return "openai_images"
    if kind in ("cinematic_broll", "atmosphere_still", "keyframe_still", "keyframe"):
        return "leonardo"
    # conservative default for visuals
    return "leonardo"


def _candidate_score(pref: ProviderLiteral, cand: ProviderLiteral, *, needs_review: bool) -> int:
    if needs_review:
        return 35 if cand == pref else 25
    if cand == pref:
        return 90
    # plausible alternatives
    if pref in ("openai_images", "leonardo") and cand in ("openai_images", "leonardo"):
        return 68
    # render_layer only makes sense for overlay kinds; runway for motion
    return 35


def _estimated_cost(provider: ProviderLiteral) -> float:
    uc = get_default_visual_unit_costs()
    return float(uc.get(str(provider), uc.get("unknown", 0.0)))


def compare_visual_providers_for_asset(asset: Dict[str, Any]) -> Dict[str, Any]:
    a = dict(asset or {})
    kind = _norm_kind(a)
    overlay_intent = _list_str(a.get("overlay_intent"))
    text_sensitive = _b(a.get("text_sensitive")) or bool(overlay_intent)

    manual = _s(a.get("manual_provider_override") or "")
    locked = _b(a.get("locked_for_render")) or (_s(a.get("asset_decision_status")) == "locked")
    policy_status = _s(a.get("visual_policy_status") or "")
    needs_review = policy_status == "needs_review"

    routed = _s(a.get("routed_visual_provider") or "")
    prov_used = _provider_used(a)

    pref = _pref_for_kind(kind, text_sensitive=text_sensitive, overlay_intent=overlay_intent)
    recommended: ProviderLiteral = pref
    reason = ""
    status: CompareStatusLiteral = "dry_run_ready"

    notes_acc: List[str] = []
    if needs_review:
        status = "needs_review"
        notes_acc.append("visual_policy_needs_review")
        reason = "visual policy needs review"

    if manual:
        recommended = manual.lower()  # type: ignore[assignment]
        reason = "manual provider override"
        notes_acc.append("manual_provider_override_applied")

    if locked:
        # choose "already used" provider if known; else keep current recommendation
        if prov_used in ("openai_images", "leonardo", "runway", "render_layer"):
            recommended = prov_used  # type: ignore[assignment]
        elif routed in ("openai_images", "leonardo", "runway", "render_layer"):
            recommended = routed.lower()  # type: ignore[assignment]
        notes_acc.append("asset_locked_for_render")
        if status != "needs_review":
            status = "completed"
        if not reason:
            reason = "asset locked for render"

    # candidate generation
    candidates: List[Dict[str, Any]] = []
    prompt_eff = _effective_prompt(a)
    gen_path = _s(a.get("generated_image_path") or a.get("image_path") or a.get("video_path") or "")

    for prov in ("leonardo", "openai_images", "runway", "render_layer"):
        p: ProviderLiteral = prov  # type: ignore[assignment]
        sc = _candidate_score(recommended, p, needs_review=needs_review)
        cn: List[str] = []
        if p == recommended:
            cn.append("recommended")
        if manual and p == recommended:
            cn.append("manual_override")
        if locked:
            cn.append("locked_context")
        if _is_overlay_kind(kind) and p == "render_layer":
            cn.append("overlay_kind")
        if kind == "motion_clip" and p == "runway":
            cn.append("motion_kind")
        if kind in ("cinematic_broll", "atmosphere_still") and p == "leonardo":
            cn.append("broll_kind")
        if kind == "thumbnail_base" and p == "openai_images":
            cn.append("thumbnail_kind")
        if text_sensitive and p == "openai_images":
            cn.append("text_sensitive")
        if needs_review:
            cn.append("needs_review")
        candidates.append(
            {
                "provider": p,
                "prompt_used_effective": prompt_eff,
                "dry_run": True,
                "generated_asset_path": gen_path,
                "quality_score": int(sc),
                "quality_notes": cn + notes_acc,
                "policy_status": policy_status or "unknown",
                "estimated_cost": float(_estimated_cost(p)),
            }
        )

    # ensure recommended exists in candidates
    if not any(c.get("provider") == recommended for c in candidates):
        recommended = pref

    if not reason:
        reason = f"heuristic preference for kind={kind or 'unknown'}"

    return {
        "provider_candidates": candidates,
        "recommended_provider": recommended,
        "provider_quality_reason": reason,
        "provider_compare_status": status,
        "provider_compare_version": "ba26_7c_v1",
    }


def apply_provider_quality_compare(asset: Dict[str, Any]) -> Dict[str, Any]:
    """Additiv: hängt Compare-Felder an ein Asset-Dict an."""
    a = dict(asset or {})
    comp = compare_visual_providers_for_asset(a)
    a.update(comp)
    return a


def build_provider_quality_summary(assets: List[Dict[str, Any]]) -> Dict[str, Any]:
    checked = 0
    needs = 0
    manual = 0
    locked = 0
    counts: Dict[str, int] = {"leonardo": 0, "openai_images": 0, "runway": 0, "render_layer": 0}

    for a in assets or []:
        if not isinstance(a, dict):
            continue
        checked += 1
        if _s(a.get("provider_compare_status")) == "needs_review":
            needs += 1
        if _s(a.get("manual_provider_override")):
            manual += 1
        if _b(a.get("locked_for_render")) or _s(a.get("asset_decision_status")) == "locked":
            locked += 1
        rp = _s(a.get("recommended_provider")).lower()
        if rp in counts:
            counts[rp] += 1

    return {
        "ok": True,
        "assets_checked": checked,
        "recommended_provider_counts": counts,
        "needs_review_count": needs,
        "manual_override_count": manual,
        "locked_count": locked,
        "provider_compare_version": "ba26_7c_v1",
    }

