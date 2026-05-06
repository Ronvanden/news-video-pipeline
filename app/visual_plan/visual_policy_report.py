"""BA 26.4c — Visual Policy Report (Operator-Transparenz, additive Felder).

Ziel: Rohprompt vs. effektiver Provider-Prompt sichtbar machen und eine einfache Ampel liefern,
ohne bestehende Contracts zu brechen.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Literal, Tuple

from app.visual_plan.visual_no_text import append_no_text_guard
from app.visual_plan.visual_provider_router import normalize_visual_asset_kind

VisualPolicyStatusLiteral = Literal["safe", "text_extracted", "needs_review"]

_GUARD_MARKER = "[visual_no_text_guard_v26_4]"


def _s(v: Any) -> str:
    return str(v or "").strip()


def _list_str(v: Any) -> List[str]:
    if not v:
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


def _has_guard(prompt: str) -> bool:
    return _GUARD_MARKER in (prompt or "")


def _routing_mismatch(asset_kind: str, routed_provider: str) -> bool:
    k = normalize_visual_asset_kind(asset_kind or "")
    rp = (routed_provider or "").strip().lower()
    if not k or not rp:
        return False
    if k in ("motion_clip",) and rp != "runway":
        return True
    if k in ("thumbnail_base",) and rp != "openai_images":
        return True
    if k in ("cinematic_broll", "atmosphere_still") and rp not in ("leonardo", "openai_images"):
        return True
    if k in ("final_text_overlay", "subtitle", "lower_third", "title_card", "label") and rp != "render_layer":
        return True
    return False


def provider_routing_reason(
    *,
    asset_kind: str,
    text_sensitive: bool,
    routed_provider: str,
    routed_image_provider: str = "",
) -> str:
    k = normalize_visual_asset_kind(asset_kind or "")
    rp = (routed_provider or "").strip().lower()
    rip = (routed_image_provider or "").strip().lower()

    if k in ("final_text_overlay", "subtitle", "lower_third", "title_card", "label"):
        base = rip or "leonardo"
        if text_sensitive:
            base = "openai_images"
        return f"{k} routed to render_layer (base_still={base})"
    if text_sensitive:
        return "text_sensitive asset routed to openai_images"
    if k == "motion_clip":
        return "motion_clip routed to runway"
    if k == "thumbnail_base":
        return "thumbnail_base routed to openai_images"
    if k in ("cinematic_broll", "atmosphere_still"):
        return f"{k} routed to leonardo"
    if rp:
        return f"{k or 'visual_asset'} routed to {rp}"
    return "default routing applied"


def build_visual_policy_fields(
    *,
    visual_prompt_raw: str,
    visual_prompt_effective: str,
    overlay_intent: Iterable[str] | None = None,
    text_sensitive: bool = False,
    visual_asset_kind: str = "",
    routed_visual_provider: str = "",
    routed_image_provider: str = "",
    require_guard_for_effective: bool = True,
) -> Dict[str, Any]:
    """
    Liefert additive Operator-Felder:
      - visual_text_guard_applied
      - visual_policy_status
      - visual_policy_warnings
      - provider_routing_reason
    """
    raw = _s(visual_prompt_raw)
    eff = _s(visual_prompt_effective)
    ov = [x for x in _list_str(list(overlay_intent or [])) if x]
    ts = bool(text_sensitive)

    guard_applied = _has_guard(eff)
    warnings: List[str] = []

    if ov:
        warnings.append("overlay_text_extracted")
    if guard_applied:
        warnings.append("no_text_guard_applied")
    elif require_guard_for_effective and eff:
        warnings.append("no_text_guard_missing")

    rp = _s(routed_visual_provider)
    if ts and rp == "openai_images":
        warnings.append("provider_routed_due_to_text_sensitive")
    if _routing_mismatch(visual_asset_kind, rp):
        warnings.append("provider_routing_mismatch_asset_kind")

    status: VisualPolicyStatusLiteral = "safe"
    if ov and ts and guard_applied:
        status = "text_extracted"
    else:
        if ts and not ov:
            status = "needs_review"
        if require_guard_for_effective and eff and not guard_applied:
            status = "needs_review"
        if _routing_mismatch(visual_asset_kind, rp):
            status = "needs_review"
        if not eff:
            status = "needs_review"

    return {
        "visual_prompt_raw": raw,
        "visual_prompt_effective": eff,
        "visual_text_guard_applied": bool(guard_applied),
        "visual_policy_status": status,
        "visual_policy_warnings": warnings,
        "provider_routing_reason": provider_routing_reason(
            asset_kind=visual_asset_kind,
            text_sensitive=ts,
            routed_provider=rp,
            routed_image_provider=routed_image_provider,
        ),
    }


def ensure_effective_prompt(prompt: str) -> Tuple[str, bool]:
    """Für Manifeste: wenn kein Guard vorhanden, Guard anfügen (idempotent)."""
    p = _s(prompt)
    if not p:
        return append_no_text_guard(""), True
    if _has_guard(p):
        return p, True
    return append_no_text_guard(p), True

