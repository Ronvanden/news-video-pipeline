"""BA 27.2 — Continuity-Aware Prompt Wiring (V1, file-based, no live reference uploads).

V1 goal: propagate reference library + per-asset reference attachments into additive manifest fields,
so operators can see what would be sent to providers later (stub only).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple

PreparationStatus = Literal["none", "prepared", "missing_reference", "needs_review"]


def _s(v: Any) -> str:
    return str(v or "").strip()


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


def _ref_index(reference_library: Optional[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    lib = reference_library if isinstance(reference_library, dict) else {}
    ras = lib.get("reference_assets")
    if not isinstance(ras, list):
        return {}
    out: Dict[str, Dict[str, Any]] = {}
    for r in ras:
        if not isinstance(r, dict):
            continue
        rid = _s(r.get("id"))
        if rid and rid not in out:
            out[rid] = r
    return out


def build_continuity_prompt_hint(asset: Dict[str, Any], reference_library: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """
    Returns dict: { "continuity_prompt_hint": str|None, "warnings": [] }
    Does NOT overwrite a non-empty existing hint.
    """
    a = asset if isinstance(asset, dict) else {}
    existing = _s(a.get("continuity_prompt_hint"))
    if existing:
        return {"continuity_prompt_hint": existing, "warnings": []}

    ids = _list_str(a.get("reference_asset_ids"))
    if not ids:
        return {"continuity_prompt_hint": None, "warnings": []}

    idx = _ref_index(reference_library)
    notes: List[str] = []
    missing: List[str] = []
    for rid in ids[:6]:
        r = idx.get(rid)
        if not r:
            missing.append(rid)
            continue
        n = _s(r.get("continuity_notes")) or _s(r.get("label"))
        if n:
            notes.append(n)

    # keep it short; if no notes available, at least reference IDs
    hint_parts: List[str] = []
    if notes:
        hint_parts.append("; ".join(notes[:3]))
    else:
        hint_parts.append("Keep continuity with references: " + ", ".join(ids[:3]))

    hint = "Continuity: " + " / ".join([p for p in hint_parts if p]) if hint_parts else ""
    hint = hint.strip() or None

    warns: List[str] = []
    if missing:
        warns.append("continuity_missing_reference_ids:" + ",".join(missing[:20]))
    return {"continuity_prompt_hint": hint, "warnings": warns}


def apply_continuity_prompt_wiring_to_asset(
    asset: Dict[str, Any],
    reference_library: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    a = dict(asset or {})
    ids = _list_str(a.get("reference_asset_ids"))
    idx = _ref_index(reference_library)

    # Determine preparation status
    status: PreparationStatus
    if not ids:
        status = "none"
    else:
        missing = [rid for rid in ids if rid not in idx]
        if str(a.get("reference_policy_status") or "").strip().lower() == "needs_review":
            status = "needs_review"
        elif missing:
            status = "missing_reference"
        else:
            status = "prepared"

    # Compute reference paths/types/provider_hints
    ref_paths: List[str] = []
    ref_types: List[str] = []
    provider_hints: List[str] = []
    for rid in ids:
        r = idx.get(rid)
        if not r:
            continue
        p = _s(r.get("path"))
        if p:
            ref_paths.append(p)
        t = _s(r.get("type"))
        if t:
            ref_types.append(t)
        ph = _s(r.get("provider_hint"))
        if ph:
            provider_hints.append(ph)

    # Build hint unless already present
    hint_res = build_continuity_prompt_hint(a, reference_library=reference_library)
    if not _s(a.get("continuity_prompt_hint")):
        a["continuity_prompt_hint"] = hint_res.get("continuity_prompt_hint")

    a["continuity_reference_paths"] = list(dict.fromkeys(ref_paths))
    a["continuity_reference_types"] = list(dict.fromkeys(ref_types))
    a["continuity_provider_preparation_status"] = status

    # Provider payload stub (no enforced provider format)
    unique_hint = _s(a.get("continuity_prompt_hint"))
    unique_strength = _s(a.get("continuity_strength")) or "medium"
    provider_hint = None
    if provider_hints:
        u = sorted(set([p for p in provider_hints if p]))
        provider_hint = u[0] if len(u) == 1 else "none"

    a["continuity_provider_payload_stub"] = {
        "reference_asset_ids": ids,
        "reference_paths": a.get("continuity_reference_paths") or [],
        "continuity_strength": unique_strength,
        "continuity_prompt_hint": unique_hint or "",
        "provider_hint": provider_hint,
        "no_live_upload": True,
    }
    a["continuity_wiring_version"] = "ba27_2_v1"

    # Optional: keep existing reference_provider_status if present (from BA 27.1)
    # Do not rename or overwrite it.
    return a


def build_continuity_wiring_summary(assets: List[Dict[str, Any]]) -> Dict[str, Any]:
    prepared = 0
    missing = 0
    needs_review = 0
    none = 0
    warnings: List[str] = []
    for a in assets or []:
        if not isinstance(a, dict):
            continue
        st = _s(a.get("continuity_provider_preparation_status")).lower()
        if st == "prepared":
            prepared += 1
        elif st == "missing_reference":
            missing += 1
        elif st == "needs_review":
            needs_review += 1
        else:
            none += 1
        # If hint builder wrote warnings earlier, we don't persist per-asset warnings; keep minimal summary.
    return {
        "assets_checked": int(len([x for x in assets or [] if isinstance(x, dict)])),
        "prepared_count": int(prepared),
        "missing_reference_count": int(missing),
        "needs_review_count": int(needs_review),
        "none_count": int(none),
        "warnings": list(dict.fromkeys([w for w in warnings if _s(w)])),
        "continuity_wiring_version": "ba27_2_v1",
    }


def apply_continuity_prompt_wiring_to_manifest(
    manifest: Dict[str, Any],
    reference_library: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    m = dict(manifest or {})
    assets = m.get("assets")
    if not isinstance(assets, list):
        assets = []
        m["assets"] = assets
    patched_assets: List[Dict[str, Any]] = []
    for a in assets:
        if not isinstance(a, dict):
            continue
        patched_assets.append(apply_continuity_prompt_wiring_to_asset(a, reference_library=reference_library))
    m["assets"] = patched_assets
    m["continuity_wiring_summary"] = build_continuity_wiring_summary(patched_assets)
    return m

