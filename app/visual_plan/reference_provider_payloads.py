"""BA 27.4 — Reference-Aware Provider Adapter Preparation (payload stubs, no live calls)."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Tuple

SupportedMode = Literal[
    "none",
    "prompt_hint_only",
    "image_reference_prepared",
    "image_to_video_reference_prepared",
]
PayloadStatus = Literal["prepared", "not_supported", "missing_reference", "needs_review", "none"]


def _s(v: Any) -> str:
    return str(v or "").strip()


def _list_str(v: Any) -> List[str]:
    if v is None:
        return []
    if isinstance(v, list):
        return [t for t in (_s(x) for x in v) if t]
    t = _s(v)
    return [t] if t else []


def _provider_priority(asset: Dict[str, Any]) -> str:
    for k in (
        "provider_used",
        "recommended_provider",
        "manual_provider_override",
        "routed_visual_provider",
        "routed_image_provider",
    ):
        v = _s(asset.get(k))
        if v:
            return v.lower()
    # fallback if references exist
    if _list_str(asset.get("reference_asset_ids")):
        return "openai_images"
    return ""


def _asset_kind(asset: Dict[str, Any]) -> str:
    return _s(asset.get("visual_asset_kind") or asset.get("asset_type") or "").lower()


def _base_reference_inputs(asset: Dict[str, Any]) -> Tuple[List[str], List[str], str, str, Optional[str]]:
    ids = _list_str(asset.get("reference_asset_ids"))
    paths = _list_str(asset.get("continuity_reference_paths"))
    strength = _s(asset.get("continuity_strength") or "medium").lower()
    hint = _s(asset.get("continuity_prompt_hint") or "")
    provider_hint = _s(asset.get("provider_hint") or "")
    if not provider_hint:
        stub = asset.get("continuity_provider_payload_stub")
        if isinstance(stub, dict):
            provider_hint = _s(stub.get("provider_hint") or "")
    return ids, paths, strength, hint, (provider_hint or None)


def build_reference_provider_payload(asset: Dict[str, Any], *, provider: str | None = None) -> Dict[str, Any]:
    a = asset if isinstance(asset, dict) else {}
    prov = (_s(provider) or "").lower()
    ids, paths, strength, hint, provider_hint = _base_reference_inputs(a)
    cont_status = _s(a.get("continuity_provider_preparation_status") or "").lower()
    ref_pol = _s(a.get("reference_policy_status") or "").lower()

    status: PayloadStatus
    if not ids:
        status = "none"
    elif cont_status == "missing_reference":
        status = "missing_reference"
    elif cont_status == "needs_review" or ref_pol == "needs_review":
        status = "needs_review"
    else:
        status = "prepared"

    supported_mode: SupportedMode = "none"
    warnings: List[str] = []

    kind = _asset_kind(a)
    has_ref_paths = bool(paths)

    if not prov:
        prov = "openai_images"

    if prov == "render_layer":
        return {
            "provider": prov,
            "supported_mode": "prompt_hint_only",
            "reference_asset_ids": ids,
            "reference_paths": paths,
            "continuity_strength": strength,
            "continuity_prompt_hint": hint,
            "provider_hint": provider_hint,
            "no_live_upload": True,
            "status": "not_supported" if ids else "none",
            "warnings": ["render_layer_reference_not_applicable"] if ids else [],
        }

    if status in ("none", "missing_reference", "needs_review"):
        supported_mode = "prompt_hint_only" if (hint or ids) else "none"
    else:
        if prov == "openai_images":
            supported_mode = "image_reference_prepared" if has_ref_paths else "prompt_hint_only"
        elif prov == "leonardo":
            # keep conservative: allow stub but do not promise support
            supported_mode = "image_reference_prepared" if has_ref_paths else "prompt_hint_only"
            warnings.append("leonardo_reference_support_stub_only_v1")
        elif prov in ("runway", "seedance"):
            is_motion = kind == "motion_clip" or bool(_s(a.get("video_path")))
            if is_motion and has_ref_paths:
                supported_mode = "image_to_video_reference_prepared"
            elif has_ref_paths:
                supported_mode = "image_reference_prepared"
            else:
                supported_mode = "prompt_hint_only"
        else:
            supported_mode = "prompt_hint_only" if (hint or ids) else "none"
            warnings.append(f"unknown_provider_reference_stub:{prov}")

    if ids and supported_mode == "none":
        supported_mode = "prompt_hint_only"

    if ids and status == "prepared" and supported_mode == "none":
        status = "not_supported"

    out = {
        "provider": prov,
        "supported_mode": supported_mode,
        "reference_asset_ids": ids,
        "reference_paths": paths,
        "continuity_strength": strength,
        "continuity_prompt_hint": hint,
        "provider_hint": provider_hint,
        "no_live_upload": True,
        "status": status,
        "warnings": list(dict.fromkeys([w for w in warnings if _s(w)])),
    }
    # BA 27.5 — provider-specific stub format (no live upload, no calls)
    if prov == "openai_images":
        out["payload_format"] = "openai_images_reference_stub_v1"
        out["payload"] = {
            "provider": "openai_images",
            "no_live_upload": True,
            "continuity_strength": strength,
            "continuity_prompt_hint": hint,
            "reference_images": [{"input_type": "file_path", "path": p} for p in paths],
        }
    # BA 27.8 — provider-specific stub formats (no live upload, no calls)
    elif prov == "runway":
        out["payload_format"] = "runway_reference_stub_v1"
        out["payload"] = {
            "provider": "runway",
            "no_live_upload": True,
            "mode": "image_to_video_reference",
            "init_images": [{"input_type": "file_path", "path": p} for p in paths],
            "motion_prompt_hint": hint,
            "continuity_strength": strength,
            "scene_motion_kind": kind or "unknown",
        }
    elif prov == "seedance":
        out["payload_format"] = "seedance_reference_stub_v1"
        out["payload"] = {
            "provider": "seedance",
            "no_live_upload": True,
            "mode": "image_to_video_reference",
            "reference_images": [{"input_type": "file_path", "path": p} for p in paths],
            "continuity_prompt_hint": hint,
            "continuity_strength": strength,
        }
    elif prov == "leonardo":
        out["payload_format"] = "leonardo_reference_stub_v1"
        out["payload"] = {
            "provider": "leonardo",
            "no_live_upload": True,
            "mode": "prompt_hint_only",
            "reference_prompt_hint": hint,
            "reference_images_stub": [{"input_type": "file_path", "path": p} for p in paths],
            "continuity_strength": strength,
        }
    return out


def apply_reference_provider_payload_to_asset(asset: Dict[str, Any]) -> Dict[str, Any]:
    a = dict(asset or {})
    payloads: Dict[str, Any] = {}
    for prov in ("openai_images", "leonardo", "runway", "seedance"):
        payloads[prov] = build_reference_provider_payload(a, provider=prov)
    a["reference_provider_payloads"] = payloads

    chosen = _provider_priority(a)
    recommended = None
    if chosen:
        recommended = payloads.get(chosen) if isinstance(payloads, dict) else None
    a["recommended_reference_provider_payload"] = recommended

    st = "none"
    if isinstance(recommended, dict):
        st = _s(recommended.get("status") or "none") or "none"
    a["reference_provider_payload_status"] = st
    a["reference_provider_payload_version"] = "ba27_4_v1"
    return a


def build_reference_provider_payload_summary(assets: List[Dict[str, Any]]) -> Dict[str, Any]:
    prepared = 0
    missing = 0
    needs_review = 0
    not_supported = 0
    none = 0
    providers_prepared: Dict[str, int] = {}
    warnings: List[str] = []
    for a in assets or []:
        if not isinstance(a, dict):
            continue
        st = _s(a.get("reference_provider_payload_status") or "").lower()
        if st == "prepared":
            prepared += 1
        elif st == "missing_reference":
            missing += 1
        elif st == "needs_review":
            needs_review += 1
        elif st == "not_supported":
            not_supported += 1
        else:
            none += 1
        rec = a.get("recommended_reference_provider_payload")
        if isinstance(rec, dict) and _s(rec.get("status")).lower() == "prepared":
            p = _s(rec.get("provider")).lower()
            if p:
                providers_prepared[p] = int(providers_prepared.get(p, 0)) + 1
    return {
        "assets_checked": int(len([x for x in assets or [] if isinstance(x, dict)])),
        "prepared_count": int(prepared),
        "missing_reference_count": int(missing),
        "needs_review_count": int(needs_review),
        "not_supported_count": int(not_supported),
        "none_count": int(none),
        "providers_prepared": providers_prepared,
        "warnings": list(dict.fromkeys([w for w in warnings if _s(w)])),
        "reference_provider_payload_version": "ba27_4_v1",
    }


def apply_reference_provider_payloads_to_manifest(manifest: Dict[str, Any]) -> Dict[str, Any]:
    m = dict(manifest or {})
    assets = m.get("assets")
    if not isinstance(assets, list):
        assets = []
    patched: List[Dict[str, Any]] = []
    for a in assets:
        if not isinstance(a, dict):
            continue
        patched.append(apply_reference_provider_payload_to_asset(a))
    m["assets"] = patched
    m["reference_provider_payload_summary"] = build_reference_provider_payload_summary(patched)
    return m

