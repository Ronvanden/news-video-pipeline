"""BA 26.6c — Scene Image Replacement / Manual Override (pure dict helpers).

Diese Helfer verändern nur das Asset-Dict (typisch aus asset_manifest.json assets[]).
Keine Provider-Calls, keine Persistenz, deterministisch testbar.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

AssetDecisionStatusLiteral = Literal[
    "pending",
    "accepted",
    "rejected",
    "locked",
    "needs_regeneration",
]

ManualProviderOverrideLiteral = Literal[
    "openai_images",
    "leonardo",
    "runway",
    "render_layer",
]


def _s(v: Any) -> str:
    return str(v or "").strip()


def _now(now_iso: Optional[str]) -> str:
    # Deterministisch: Default leer; CLI kann echten Timestamp setzen.
    return _s(now_iso)


def ensure_asset_override_defaults(asset: Dict[str, Any]) -> Dict[str, Any]:
    """Stellt additive Override-Felder sicher (ohne bestehende Felder zu entfernen)."""
    a = dict(asset or {})
    a.setdefault("asset_decision_status", "pending")
    a.setdefault("manual_override_applied", False)
    a.setdefault("manual_override_reason", None)
    a.setdefault("manual_prompt_override", None)
    a.setdefault("manual_provider_override", None)
    a.setdefault("selected_asset_path", None)
    a.setdefault("candidate_asset_paths", [])
    a.setdefault("replacement_history", [])
    a.setdefault("locked_for_render", False)

    if not isinstance(a.get("candidate_asset_paths"), list):
        a["candidate_asset_paths"] = []
    if not isinstance(a.get("replacement_history"), list):
        a["replacement_history"] = []
    return a


def _append_history(
    asset: Dict[str, Any],
    *,
    action: str,
    reason: Optional[str],
    now_iso: Optional[str],
) -> Dict[str, Any]:
    a = ensure_asset_override_defaults(asset)
    hist: List[Dict[str, Any]] = list(a.get("replacement_history") or [])
    entry: Dict[str, Any] = {
        "action": _s(action) or "update",
        "reason": _s(reason) or None,
        "now_iso": _now(now_iso) or None,
        "scene_number": int(a.get("scene_number") or 0) if str(a.get("scene_number") or "").isdigit() else a.get("scene_number"),
        "selected_asset_path": a.get("selected_asset_path"),
        "manual_provider_override": a.get("manual_provider_override"),
        "manual_prompt_override": a.get("manual_prompt_override"),
        "asset_decision_status": a.get("asset_decision_status"),
        "provider_used": a.get("provider_used"),
        "image_path": a.get("image_path"),
        "video_path": a.get("video_path"),
    }
    hist.append(entry)
    a["replacement_history"] = hist
    return a


def apply_scene_asset_override(
    asset: Dict[str, Any],
    *,
    selected_asset_path: Optional[str] = None,
    manual_provider_override: Optional[str] = None,
    manual_prompt_override: Optional[str] = None,
    manual_override_reason: Optional[str] = None,
    decision_status: Optional[str] = None,
    candidate_asset_paths: Optional[List[str]] = None,
    now_iso: Optional[str] = None,
) -> Dict[str, Any]:
    a = ensure_asset_override_defaults(asset)

    if candidate_asset_paths is not None:
        a["candidate_asset_paths"] = [p for p in (candidate_asset_paths or []) if _s(p)]

    if selected_asset_path is not None:
        a["selected_asset_path"] = _s(selected_asset_path) or None
        a["manual_override_applied"] = True

    if manual_provider_override is not None:
        mp = _s(manual_provider_override) or None
        a["manual_provider_override"] = mp
        if mp is not None:
            a["manual_override_applied"] = True

    if manual_prompt_override is not None:
        mp2 = _s(manual_prompt_override) or None
        a["manual_prompt_override"] = mp2
        if mp2 is not None:
            a["manual_override_applied"] = True

    if manual_override_reason is not None:
        a["manual_override_reason"] = _s(manual_override_reason) or None

    if decision_status is not None:
        ds = _s(decision_status)
        if ds:
            a["asset_decision_status"] = ds
            if ds == "locked":
                a["locked_for_render"] = True
            if ds in ("pending", "needs_regeneration", "rejected"):
                a["locked_for_render"] = False

    return _append_history(a, action="apply_override", reason=manual_override_reason, now_iso=now_iso)


def mark_scene_asset_accepted(asset: Dict[str, Any], reason: Optional[str] = None, *, now_iso: Optional[str] = None) -> Dict[str, Any]:
    a = ensure_asset_override_defaults(asset)
    a["asset_decision_status"] = "accepted"
    a["locked_for_render"] = False
    if reason is not None:
        a["manual_override_reason"] = _s(reason) or None
    return _append_history(a, action="mark_accepted", reason=reason, now_iso=now_iso)


def mark_scene_asset_rejected(asset: Dict[str, Any], reason: Optional[str] = None, *, now_iso: Optional[str] = None) -> Dict[str, Any]:
    a = ensure_asset_override_defaults(asset)
    a["asset_decision_status"] = "rejected"
    a["locked_for_render"] = False
    if reason is not None:
        a["manual_override_reason"] = _s(reason) or None
    return _append_history(a, action="mark_rejected", reason=reason, now_iso=now_iso)


def mark_scene_asset_locked(asset: Dict[str, Any], reason: Optional[str] = None, *, now_iso: Optional[str] = None) -> Dict[str, Any]:
    a = ensure_asset_override_defaults(asset)
    a["asset_decision_status"] = "locked"
    a["locked_for_render"] = True
    if reason is not None:
        a["manual_override_reason"] = _s(reason) or None
    return _append_history(a, action="mark_locked", reason=reason, now_iso=now_iso)


def request_scene_asset_regeneration(asset: Dict[str, Any], reason: Optional[str] = None, *, now_iso: Optional[str] = None) -> Dict[str, Any]:
    a = ensure_asset_override_defaults(asset)
    a["asset_decision_status"] = "needs_regeneration"
    a["locked_for_render"] = False
    if reason is not None:
        a["manual_override_reason"] = _s(reason) or None
    return _append_history(a, action="request_regeneration", reason=reason, now_iso=now_iso)

