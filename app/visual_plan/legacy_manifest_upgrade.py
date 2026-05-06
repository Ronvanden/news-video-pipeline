"""BA 29.1 — Legacy asset_manifest upgrade (pure dict helpers, no I/O, no provider calls)."""

from __future__ import annotations

import copy
from collections import Counter
from typing import Any, Dict, List

from app.visual_plan.asset_override import ensure_asset_override_defaults
from app.visual_plan.visual_no_text import append_no_text_guard

# Keep in sync with app.visual_plan.visual_no_text._GUARD_MARKER (public contract for manifests).
_VISUAL_NO_TEXT_GUARD_MARKER = "[visual_no_text_guard_v26_4]"

_LEGACY_POLICY_WARNING = "legacy_manifest_guard_patched_for_smoke"


def _s(v: Any) -> str:
    return str(v or "").strip()


def _has_text_guard(asset: Dict[str, Any]) -> bool:
    if bool(asset.get("visual_text_guard_applied")):
        return True
    blob = " ".join(
        [
            _s(asset.get("visual_prompt_effective")),
            _s(asset.get("prompt_used_effective")),
            _s(asset.get("visual_prompt")),
        ]
    )
    return _VISUAL_NO_TEXT_GUARD_MARKER in blob


def _asset_override_incomplete(asset: Dict[str, Any]) -> bool:
    keys = (
        "asset_decision_status",
        "manual_override_applied",
        "manual_override_reason",
        "manual_prompt_override",
        "manual_provider_override",
        "selected_asset_path",
        "candidate_asset_paths",
        "replacement_history",
        "locked_for_render",
    )
    for k in keys:
        if k not in asset:
            return True
    if not isinstance(asset.get("candidate_asset_paths"), list):
        return True
    if not isinstance(asset.get("replacement_history"), list):
        return True
    return False


def detect_legacy_asset_manifest_issues(manifest: Dict[str, Any]) -> Dict[str, Any]:
    """
    Detect missing / legacy fields for modern production / approval / cost paths.
    Does not mutate ``manifest``.
    """
    m = manifest if isinstance(manifest, dict) else {}
    manifest_issues: List[str] = []
    manifest_optional: List[str] = []

    if not isinstance(m.get("visual_cost_summary"), dict):
        manifest_issues.append("visual_cost_summary_missing")
    if not isinstance(m.get("production_asset_approval_result"), dict):
        manifest_issues.append("production_asset_approval_result_missing")

    assets_list = m.get("assets")
    assets = [a for a in (assets_list if isinstance(assets_list, list) else []) if isinstance(a, dict)]

    ref_payload_ok = isinstance(m.get("reference_provider_payload_summary"), dict) or any(
        isinstance(a.get("reference_provider_payloads"), dict) for a in assets
    )
    if not ref_payload_ok:
        manifest_optional.append("reference_provider_payloads_missing")
    if not isinstance(m.get("continuity_wiring_summary"), dict):
        manifest_optional.append("continuity_summary_missing")

    rows: List[Dict[str, Any]] = []
    cnt: Counter[str] = Counter()

    for a in assets:
        issues: List[str] = []
        optional: List[str] = []
        if not _s(a.get("visual_prompt_effective")):
            issues.append("visual_prompt_effective_missing")
        if not _has_text_guard(a):
            issues.append("visual_text_guard_missing")
        if not _s(a.get("visual_policy_status")):
            issues.append("visual_policy_status_missing")
        w = a.get("visual_policy_warnings")
        if w is None or not isinstance(w, list):
            issues.append("visual_policy_warnings_missing")
        if _asset_override_incomplete(a):
            issues.append("asset_override_fields_missing")
        if not isinstance(a.get("reference_provider_payloads"), dict):
            optional.append("reference_provider_payloads_missing")

        rows.append(
            {
                "scene_number": a.get("scene_number"),
                "issues": list(dict.fromkeys(issues)),
                "optional_issues": list(dict.fromkeys(optional)),
            }
        )
        for it in issues:
            cnt[it] += 1

    return {
        "manifest_issues": list(dict.fromkeys(manifest_issues)),
        "manifest_optional_issues": list(dict.fromkeys(manifest_optional)),
        "assets": rows,
        "issue_counts": dict(sorted(cnt.items(), key=lambda x: x[0])),
        "assets_checked": len(assets),
        "detector_version": "ba29_1_v1",
    }


def build_legacy_manifest_upgrade_summary(manifest: Dict[str, Any]) -> Dict[str, Any]:
    """Compact summary for an ``asset_manifest`` (before or after upgrade)."""
    m = manifest if isinstance(manifest, dict) else {}
    det = detect_legacy_asset_manifest_issues(m)
    assets_n = len([a for a in (m.get("assets") or []) if isinstance(a, dict)])
    return {
        "summary_version": "ba29_1_v1",
        "legacy_manifest_upgrade_version": m.get("legacy_manifest_upgrade_version"),
        "legacy_manifest_upgrade_mode": m.get("legacy_manifest_upgrade_mode"),
        "assets_total": int(assets_n),
        "detect": det,
    }


def upgrade_legacy_asset_manifest(
    manifest: Dict[str, Any],
    *,
    mode: str = "smoke_safe",
) -> Dict[str, Any]:
    """
    Return a deep copy of ``manifest`` with additive BA 29.1 fields per asset and manifest markers.

    Does not remove keys. Does not overwrite non-empty ``visual_policy_status``.
    """
    issues_before = detect_legacy_asset_manifest_issues(manifest)
    out = copy.deepcopy(manifest) if isinstance(manifest, dict) else {}
    if not isinstance(out.get("assets"), list):
        out["assets"] = list(out.get("assets") or [])

    patched_assets: List[Any] = []
    for item in out["assets"]:
        if not isinstance(item, dict):
            patched_assets.append(item)
            continue
        a = copy.deepcopy(item)

        a = ensure_asset_override_defaults(a)

        eff_existing = _s(a.get("visual_prompt_effective"))
        if eff_existing:
            base = eff_existing
        else:
            base = _s(a.get("visual_prompt")) or _s(a.get("prompt_used_effective")) or ""

        a["visual_prompt_effective"] = append_no_text_guard(base)
        a["visual_text_guard_applied"] = True

        if not _s(a.get("visual_policy_status")):
            a["visual_policy_status"] = "safe"

        w0 = a.get("visual_policy_warnings")
        if isinstance(w0, list):
            pol_list = [_s(x) for x in w0 if _s(x)]
        elif isinstance(w0, str) and _s(w0):
            pol_list = [_s(w0)]
        else:
            pol_list = []
        if _LEGACY_POLICY_WARNING not in pol_list:
            pol_list.append(_LEGACY_POLICY_WARNING)
        a["visual_policy_warnings"] = pol_list

        patched_assets.append(a)

    out["assets"] = patched_assets
    out["legacy_manifest_upgrade_version"] = "ba29_1_v1"
    out["legacy_manifest_upgrade_mode"] = _s(mode) or "smoke_safe"

    summ = build_legacy_manifest_upgrade_summary(out)
    summ["issues_before"] = issues_before
    out["legacy_manifest_upgrade_summary"] = summ

    return out
