"""BA 26.8c — Visual Cost Tracking (heuristisch, keine Billing-API).

Reine Schätzung: keine echte Abrechnung, keine Provider-Calls.
Kosten werden pro Asset und aggregiert pro Manifest berechnet.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from app.config import settings


def _s(v: Any) -> str:
    return str(v or "").strip()


def _f(v: Any) -> Optional[float]:
    try:
        if v is None:
            return None
        return float(v)
    except Exception:
        return None


def get_default_visual_unit_costs() -> Dict[str, float]:
    """EUR per generated unit (image or clip). Public params; no secrets."""
    # Prefer settings values (env-driven) if present; otherwise hard defaults.
    return {
        "openai_images": float(getattr(settings, "visual_cost_openai_image_eur", 0.08)),
        "leonardo": float(getattr(settings, "visual_cost_leonardo_image_eur", 0.05)),
        "runway": float(getattr(settings, "visual_cost_runway_clip_eur", 0.25)),
        "seedance": float(getattr(settings, "visual_cost_seedance_clip_eur", 0.20)),
        "render_layer": float(getattr(settings, "visual_cost_render_layer_eur", 0.0)),
        "unknown": 0.0,
    }


def _detect_provider(asset: Dict[str, Any]) -> str:
    # Priority order from BA 26.8c spec.
    keys = (
        "provider_used",
        "recommended_provider",
        "manual_provider_override",
        "routed_visual_provider",
        "routed_image_provider",
        "image_provider_routed",
        "video_provider_routed",
    )
    for k in keys:
        v = _s(asset.get(k))
        if v:
            return v.lower()
    return "unknown"


def estimate_visual_asset_cost(
    asset: Dict[str, Any],
    unit_costs: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Returns:
      - provider, unit_cost_eur, estimate_eur, warnings[]
    """
    uc = dict(unit_costs or get_default_visual_unit_costs())
    provider = _detect_provider(asset)
    warns: List[str] = []
    unit = float(uc.get(provider, uc.get("unknown", 0.0)))
    if provider not in uc and provider != "unknown":
        warns.append(f"visual_cost_unknown_provider:{provider}")
    if provider == "unknown":
        warns.append("visual_cost_provider_unknown")
    warns.append("visual_cost_estimate_only")
    return {
        "provider": provider,
        "unit_cost_eur": float(unit),
        "estimate_eur": float(unit),
        "warnings": warns,
    }


def apply_visual_cost_to_asset(
    asset: Dict[str, Any],
    unit_costs: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    a = dict(asset or {})
    est = estimate_visual_asset_cost(a, unit_costs=unit_costs)
    a["visual_cost_estimate_eur"] = float(est["estimate_eur"])
    a.setdefault("visual_cost_actual_eur", None)
    a["visual_cost_currency"] = "EUR"
    a["visual_cost_source"] = "estimate"
    a["visual_provider_unit_cost"] = float(est["unit_cost_eur"])
    a["visual_cost_warning"] = ";".join([w for w in (est.get("warnings") or []) if w]) if est.get("warnings") else ""
    a["visual_cost_version"] = "ba26_8c_v1"

    # Optional: patch provider_candidates[].estimated_cost to match unit cost (EUR)
    cands = a.get("provider_candidates")
    if isinstance(cands, list):
        uc = dict(unit_costs or get_default_visual_unit_costs())
        patched: List[Dict[str, Any]] = []
        for c in cands:
            if not isinstance(c, dict):
                continue
            p = _s(c.get("provider")).lower() or "unknown"
            c2 = dict(c)
            c2["estimated_cost"] = float(uc.get(p, uc.get("unknown", 0.0)))
            patched.append(c2)
        a["provider_candidates"] = patched

    return a


def build_visual_cost_summary(
    assets: List[Dict[str, Any]],
    unit_costs: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    uc = dict(unit_costs or get_default_visual_unit_costs())
    total_est = 0.0
    total_act = 0.0
    breakdown: Dict[str, float] = {}
    unknown_cnt = 0
    warn_cnt = 0

    for a in assets or []:
        if not isinstance(a, dict):
            continue
        prov = _detect_provider(a)
        est = _f(a.get("visual_cost_estimate_eur"))
        if est is None:
            # compute on the fly if missing
            unit = float(uc.get(prov, uc.get("unknown", 0.0)))
            est = unit
        total_est += float(est)
        breakdown[prov] = float(breakdown.get(prov, 0.0) + float(est))
        if prov == "unknown" or prov not in uc:
            unknown_cnt += 1
        if _s(a.get("visual_cost_warning")):
            warn_cnt += 1
        act = _f(a.get("visual_cost_actual_eur"))
        if act is not None:
            total_act += float(act)

    return {
        "visual_total_estimated_cost_eur": round(float(total_est), 4),
        "visual_total_actual_cost_eur": round(float(total_act), 4) if total_act else 0.0,
        "visual_cost_currency": "EUR",
        "visual_cost_breakdown_by_provider": dict(sorted(breakdown.items(), key=lambda x: x[0])),
        "visual_cost_unknown_provider_count": int(unknown_cnt),
        "visual_cost_warning_count": int(warn_cnt),
        "visual_cost_version": "ba26_8c_v1",
    }

