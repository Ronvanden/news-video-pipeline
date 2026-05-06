"""BA 27.1 — Visual Reference Library / Continuity Anchors (V1, file-based).

V1 scope:
- Reference library JSON schema + normalization + summary
- Attach reference IDs to assets (additive)
- No provider calls, no uploads, no secrets.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple

ReferenceType = Literal[
    "character",
    "location",
    "object",
    "style",
    "thumbnail_style",
    "other",
]
ProviderHint = Literal["openai_images", "leonardo", "runway", "seedance", "none"]
Strength = Literal["low", "medium", "high"]
ReferencePolicyStatus = Literal["none", "attached", "missing_reference", "needs_review"]


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


def _valid_type(t: str) -> ReferenceType:
    tt = _s(t).lower()
    if tt in ("character", "location", "object", "style", "thumbnail_style", "other"):
        return tt  # type: ignore[return-value]
    return "other"


def _valid_strength(s: Any) -> Strength:
    ss = _s(s).lower()
    if ss in ("low", "medium", "high"):
        return ss  # type: ignore[return-value]
    return "medium"


def _valid_provider_hint(p: Any) -> Optional[ProviderHint]:
    pp = _s(p).lower()
    if not pp:
        return None
    if pp in ("openai_images", "leonardo", "runway", "seedance", "none"):
        return pp  # type: ignore[return-value]
    return None


def normalize_reference_asset(ref: Dict[str, Any]) -> Dict[str, Any]:
    r = dict(ref or {})
    rid = _s(r.get("id"))
    if not rid:
        rid = f"ref_{uuid.uuid4().hex[:12]}"
    rtype = _valid_type(_s(r.get("type") or "other"))
    path = _s(r.get("path"))
    r["id"] = rid
    r["type"] = rtype
    r["path"] = path
    r["label"] = _s(r.get("label")) or None
    r["usage"] = _s(r.get("usage")) or None
    r["continuity_notes"] = _s(r.get("continuity_notes")) or _s(r.get("notes")) or None
    r["provider_hint"] = _valid_provider_hint(r.get("provider_hint"))
    r["reference_strength"] = _valid_strength(r.get("reference_strength") or r.get("strength"))
    r["safety_notes"] = _list_str(r.get("safety_notes"))
    r["created_by"] = "ba27_1_reference_library_v1"
    return r


def build_reference_library(
    reference_assets: List[Dict[str, Any]],
    *,
    run_id: str | None = None,
) -> Dict[str, Any]:
    warns: List[str] = []
    assets_norm: List[Dict[str, Any]] = []
    seen: set[str] = set()
    dupes: List[str] = []

    for raw in reference_assets or []:
        if not isinstance(raw, dict):
            warns.append("reference_asset_invalid_type")
            continue
        r = normalize_reference_asset(raw)
        rid = _s(r.get("id"))
        if rid in seen:
            dupes.append(rid)
            continue
        seen.add(rid)
        if not _s(r.get("path")):
            warns.append(f"reference_asset_path_missing:{rid}")
        else:
            # best-effort existence check (relative to CWD)
            p = Path(_s(r.get("path")))
            try:
                check = p if p.is_absolute() else (Path.cwd() / p)
                if not check.exists():
                    warns.append(f"reference_asset_path_not_found:{rid}")
            except OSError:
                warns.append(f"reference_asset_path_check_failed:{rid}")
        assets_norm.append(r)

    if dupes:
        warns.append("reference_asset_duplicate_ids:" + ",".join(sorted(set(dupes))[:50]))

    return {
        "reference_library_version": "ba27_1_v1",
        "run_id": _s(run_id) or None,
        "reference_assets": assets_norm,
        "warnings": list(dict.fromkeys([w for w in warns if _s(w)])),
    }


def attach_reference_ids_to_asset(
    asset: Dict[str, Any],
    reference_ids: List[str],
    *,
    continuity_strength: str = "medium",
    continuity_prompt_hint: Optional[str] = None,
    reference_provider_status: Optional[str] = None,
) -> Dict[str, Any]:
    a = dict(asset or {})
    ids_in = [_s(x) for x in (reference_ids or []) if _s(x)]
    ids_unique = list(dict.fromkeys(ids_in))
    existing = a.get("reference_asset_ids")
    if isinstance(existing, list):
        merged = list(dict.fromkeys([_s(x) for x in existing if _s(x)] + ids_unique))
    else:
        merged = ids_unique
    a["reference_asset_ids"] = merged
    a["continuity_strength"] = _valid_strength(continuity_strength)
    a["continuity_notes"] = _s(a.get("continuity_notes")) or None
    if continuity_prompt_hint is not None:
        a["continuity_prompt_hint"] = _s(continuity_prompt_hint) or None
    else:
        # keep existing if present; do not delete
        a["continuity_prompt_hint"] = _s(a.get("continuity_prompt_hint")) or None
    if reference_provider_status is not None:
        a["reference_provider_status"] = _s(reference_provider_status) or None
    a["reference_policy_status"] = "attached" if merged else "none"
    return a


def _library_id_set(reference_library: Dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    ras = reference_library.get("reference_assets")
    if isinstance(ras, list):
        for r in ras:
            if isinstance(r, dict):
                rid = _s(r.get("id"))
                if rid:
                    ids.add(rid)
    return ids


def _evaluate_reference_policy_status(asset: Dict[str, Any], *, library_ids: set[str]) -> ReferencePolicyStatus:
    ids = asset.get("reference_asset_ids")
    ids_list = [x for x in ids if _s(x)] if isinstance(ids, list) else []
    if not ids_list:
        return "none"
    missing = [rid for rid in ids_list if rid not in library_ids]
    if missing:
        return "missing_reference"
    strength = _s(asset.get("continuity_strength")).lower()
    if strength and strength not in ("low", "medium", "high"):
        return "needs_review"
    return "attached"


def build_reference_library_summary(
    reference_library: Dict[str, Any],
    assets: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    lib = reference_library if isinstance(reference_library, dict) else {}
    ras = lib.get("reference_assets") if isinstance(lib.get("reference_assets"), list) else []
    type_counts = {k: 0 for k in ("character", "location", "object", "style", "thumbnail_style", "other")}
    for r in ras:
        if not isinstance(r, dict):
            continue
        t = _valid_type(_s(r.get("type")))
        type_counts[t] = int(type_counts.get(t, 0)) + 1

    library_ids = _library_id_set(lib)
    assets_with_refs = 0
    missing_refs = 0
    needs_review = 0
    if assets:
        for a in assets:
            if not isinstance(a, dict):
                continue
            st = _evaluate_reference_policy_status(a, library_ids=library_ids)
            if st != "none":
                assets_with_refs += 1
            if st == "missing_reference":
                missing_refs += 1
            if st == "needs_review":
                needs_review += 1

    return {
        "reference_assets_count": int(len([x for x in ras if isinstance(x, dict)])),
        "types_count": type_counts,
        "assets_with_references_count": int(assets_with_refs),
        "missing_references_count": int(missing_refs),
        "needs_review_count": int(needs_review),
        "warnings": list(dict.fromkeys([_s(w) for w in (lib.get("warnings") or []) if _s(w)])),
    }


def write_reference_library(path: str | Path, reference_library: Dict[str, Any]) -> Path:
    p = Path(path).resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(reference_library, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return p


def read_reference_library(path: str | Path) -> Dict[str, Any]:
    p = Path(path).resolve()
    return json.loads(p.read_text(encoding="utf-8"))

