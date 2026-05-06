"""BA 27.6 — Mirror reference payload fields across scene-like objects (pure dict helpers)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


_FIELDS = (
    # BA 27.4/27.5
    "reference_provider_payloads",
    "recommended_reference_provider_payload",
    "reference_provider_payload_status",
    "reference_provider_payload_version",
    # BA 27.2/27.3 (continuity)
    "continuity_provider_preparation_status",
    "continuity_provider_payload_stub",
    "continuity_prompt_hint",
    "continuity_reference_paths",
    "continuity_reference_types",
    "reference_asset_ids",
    "continuity_strength",
)


def _s(v: Any) -> str:
    return str(v or "").strip()


def _is_empty(v: Any) -> bool:
    if v is None:
        return True
    if v is False:
        return False
    if v == 0:
        return False
    if isinstance(v, str):
        return _s(v) == ""
    if isinstance(v, (list, dict, tuple, set)):
        return len(v) == 0
    return False


def _scene_key(obj: Dict[str, Any]) -> Optional[int]:
    for k in ("scene_number", "scene_index"):
        if k in obj:
            try:
                n = int(obj.get(k))
                if n >= 1:
                    return n
            except Exception:
                pass
    return None


def extract_reference_payload_fields(asset: Dict[str, Any]) -> Dict[str, Any]:
    src = asset if isinstance(asset, dict) else {}
    out: Dict[str, Any] = {}
    for k in _FIELDS:
        if k in src:
            out[k] = src.get(k)
    return out


def merge_reference_payload_fields(target: Dict[str, Any], source: Dict[str, Any]) -> Dict[str, Any]:
    """Additive merge: only fills missing/empty target values from source."""
    t = dict(target or {})
    s = source if isinstance(source, dict) else {}
    for k in _FIELDS:
        if k not in s:
            continue
        if k in t and not _is_empty(t.get(k)):
            continue
        t[k] = s.get(k)
    return t


def mirror_reference_payloads_by_scene(
    target_items: List[Dict[str, Any]],
    asset_items: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    idx: Dict[int, Dict[str, Any]] = {}
    for a in asset_items or []:
        if not isinstance(a, dict):
            continue
        sk = _scene_key(a)
        if sk is None:
            continue
        idx[sk] = a

    out: List[Dict[str, Any]] = []
    matched = 0
    warnings: List[str] = []
    for it in target_items or []:
        if not isinstance(it, dict):
            continue
        sk = _scene_key(it)
        if sk is None:
            out.append(dict(it))
            warnings.append("target_item_missing_scene_key")
            continue
        src = idx.get(sk)
        if not isinstance(src, dict):
            out.append(dict(it))
            continue
        merged = merge_reference_payload_fields(it, extract_reference_payload_fields(src))
        out.append(merged)
        matched += 1

    summary = {
        "targets_checked": int(len([x for x in target_items or [] if isinstance(x, dict)])),
        "assets_indexed": int(len(idx)),
        "matched_count": int(matched),
        "unmatched_target_count": int(
            max(0, len([x for x in target_items or [] if isinstance(x, dict)]) - matched)
        ),
        "warnings": list(dict.fromkeys([w for w in warnings if _s(w)])),
        "reference_payload_mirror_version": "ba27_6_v1",
    }
    return out, summary


def build_reference_payload_mirror_summary(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    any_payload = 0
    prepared = 0
    missing = 0
    needs_review = 0
    not_supported = 0
    none = 0
    for it in items or []:
        if not isinstance(it, dict):
            continue
        if "reference_provider_payloads" in it or "recommended_reference_provider_payload" in it:
            any_payload += 1
        st = _s(it.get("reference_provider_payload_status") or "").lower()
        if st == "prepared":
            prepared += 1
        elif st == "missing_reference":
            missing += 1
        elif st == "needs_review":
            needs_review += 1
        elif st == "not_supported":
            not_supported += 1
        elif st == "none" or st == "":
            none += 1
        else:
            none += 1
    return {
        "items_checked": int(len([x for x in items or [] if isinstance(x, dict)])),
        "items_with_any_payload_fields": int(any_payload),
        "prepared_count": int(prepared),
        "missing_reference_count": int(missing),
        "needs_review_count": int(needs_review),
        "not_supported_count": int(not_supported),
        "none_count": int(none),
        "reference_payload_mirror_version": "ba27_6_v1",
    }

