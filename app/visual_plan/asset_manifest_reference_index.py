"""BA 27.7 — Build compact reference index from asset_manifest.assets[]."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def _s(v: Any) -> str:
    return str(v or "").strip()


def _list_str(v: Any) -> List[str]:
    if v is None:
        return []
    if isinstance(v, list):
        return [t for t in (_s(x) for x in v) if t]
    t = _s(v)
    return [t] if t else []


_COMPACT_FIELDS = (
    "scene_number",
    "scene_index",
    "asset_id",
    "reference_asset_ids",
    "continuity_strength",
    "continuity_prompt_hint",
    "continuity_provider_preparation_status",
    "continuity_reference_paths",
    "continuity_reference_types",
    "reference_provider_payload_status",
    "recommended_reference_provider_payload",
    "reference_provider_payloads",
    "reference_provider_payload_version",
    "continuity_wiring_version",
)


def build_asset_manifest_reference_index(asset_manifest: Dict[str, Any]) -> Dict[str, Any]:
    man = asset_manifest if isinstance(asset_manifest, dict) else {}
    assets = man.get("assets")
    if not isinstance(assets, list):
        assets = []

    by_scene_number: Dict[str, Any] = {}
    prepared = 0
    missing = 0
    needs_review = 0
    none = 0
    warnings: List[str] = []

    for a in assets:
        if not isinstance(a, dict):
            continue
        try:
            sn = int(a.get("scene_number") or a.get("scene_index") or 0)
        except Exception:
            sn = 0
        if sn <= 0:
            continue
        row: Dict[str, Any] = {}
        for k in _COMPACT_FIELDS:
            if k in a:
                row[k] = a.get(k)
        row["scene_number"] = sn

        st = _s(row.get("reference_provider_payload_status")).lower()
        if st == "prepared":
            prepared += 1
        elif st == "missing_reference":
            missing += 1
        elif st == "needs_review":
            needs_review += 1
        else:
            none += 1

        by_scene_number[str(sn)] = row

    summary = {
        "scenes_indexed": int(len(by_scene_number)),
        "prepared_count": int(prepared),
        "missing_reference_count": int(missing),
        "needs_review_count": int(needs_review),
        "none_count": int(none),
        "warnings": list(dict.fromkeys([w for w in warnings if _s(w)])),
    }

    return {
        "asset_manifest_reference_index_version": "ba27_7_v1",
        "by_scene_number": by_scene_number,
        "summary": summary,
    }

