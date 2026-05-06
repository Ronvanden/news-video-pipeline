"""BA 27.0 — Real End-to-End Production Pack V1 (file-based).

Ziel: vorhandene Artefakte (script/scene pack/asset manifest/approval/cost/compare) in einen
kopierbaren Produktionsordner bündeln. Keine Live-Provider-Calls, keine Secrets.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Dict, Iterable, List, Literal, Optional, Tuple

from app.visual_plan.reference_payload_mirror import (
    build_reference_payload_mirror_summary,
    mirror_reference_payloads_by_scene,
)
from app.visual_plan.asset_manifest_reference_index import build_asset_manifest_reference_index
from app.visual_plan.visual_production_preflight import build_visual_production_preflight_result

RenderReadinessStatus = Literal["ready", "needs_review", "blocked"]

from app.visual_plan.reference_library import build_reference_library_summary, read_reference_library


def _s(v: Any) -> str:
    return str(v or "").strip()


def _is_safe_file(p: Path) -> bool:
    try:
        if p.is_symlink() or not p.is_file():
            return False
        return True
    except OSError:
        return False


def _file_size_bytes_or_none(p: Path) -> Optional[int]:
    try:
        if p.is_symlink() or not p.is_file():
            return None
        return int(p.stat().st_size)
    except OSError:
        return None


def _read_json_or_none(path: Optional[Path]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    if path is None:
        return None, "path_missing"
    p = Path(path).resolve()
    if not p.is_file():
        return None, "file_missing"
    try:
        return json.loads(p.read_text(encoding="utf-8")), None
    except Exception as exc:
        return None, f"json_unreadable:{type(exc).__name__}"


def _write_json(path: Path, obj: Dict[str, Any]) -> Path:
    p = Path(path).resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return p


def _classify_asset_bucket(p: Path) -> str:
    ext = p.suffix.lower()
    if ext in (".png", ".jpg", ".jpeg", ".webp", ".gif"):
        return "images"
    if ext in (".mp4", ".mov", ".webm", ".mkv", ".avi"):
        return "clips"
    if ext in (".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"):
        return "voice"
    if ext in (".srt", ".ass", ".vtt", ".json", ".txt"):
        return "overlays"
    return "assets"


def _resolve_maybe_relative(path_str: str, *, base_dir: Path) -> Path:
    s = _s(path_str)
    if not s:
        return Path()
    p = Path(s)
    if p.is_absolute():
        return p.resolve()
    return (base_dir / p).resolve()


def _iter_asset_file_candidates(asset: Dict[str, Any]) -> Iterable[Tuple[str, str]]:
    # key -> path string (priority order)
    for k in (
        "selected_asset_path",
        "generated_image_path",
        "image_path",
        "video_path",
        "clip_path",
        "voice_path",
    ):
        v = asset.get(k)
        if isinstance(v, str) and _s(v):
            yield k, v


def _providers_used_from_assets(assets: List[Dict[str, Any]]) -> List[str]:
    out: List[str] = []
    for a in assets:
        if not isinstance(a, dict):
            continue
        prov = _s(
            a.get("provider_used")
            or a.get("manual_provider_override")
            or a.get("recommended_provider")
            or a.get("routed_visual_provider")
            or a.get("routed_image_provider")
            or ""
        ).lower()
        if prov:
            out.append(prov)
    return sorted(set(out))


def _visual_policy_counts_from_assets(assets: List[Dict[str, Any]]) -> Dict[str, int]:
    safe = 0
    text_extracted = 0
    needs_review = 0
    guard_applied = 0
    text_sensitive = 0
    for a in assets:
        if not isinstance(a, dict):
            continue
        st = _s(a.get("visual_policy_status") or "").lower()
        if st == "safe":
            safe += 1
        elif st == "text_extracted":
            text_extracted += 1
        elif st == "needs_review":
            needs_review += 1
        # guard applied: prefer explicit field, fallback to marker in effective prompt
        g = a.get("visual_text_guard_applied")
        if g is None:
            effp = _s(a.get("visual_prompt_effective") or a.get("prompt_used_effective") or "")
            g = "[visual_no_text_guard_v26_4]" in effp
        if bool(g):
            guard_applied += 1
        if bool(a.get("text_sensitive")):
            text_sensitive += 1
        else:
            oi = a.get("overlay_intent")
            if isinstance(oi, list) and len([x for x in oi if _s(x)]) > 0:
                text_sensitive += 1
    return {
        "safe_count": int(safe),
        "text_extracted_count": int(text_extracted),
        "needs_review_count": int(needs_review),
        "guard_applied_count": int(guard_applied),
        "text_sensitive_count": int(text_sensitive),
    }


def _asset_decision_counts_from_assets(assets: List[Dict[str, Any]]) -> Dict[str, int]:
    accepted = 0
    locked = 0
    pending = 0
    rejected = 0
    needs_regen = 0
    for a in assets:
        if not isinstance(a, dict):
            continue
        st = _s(a.get("asset_decision_status") or "pending").lower()
        if st == "accepted":
            accepted += 1
        elif st == "locked":
            locked += 1
        elif st == "rejected":
            rejected += 1
        elif st == "needs_regeneration":
            needs_regen += 1
        else:
            pending += 1
        if bool(a.get("locked_for_render")) and st != "locked":
            locked += 1
            if st == "accepted":
                accepted = max(0, accepted - 1)
            elif st not in ("rejected", "needs_regeneration"):
                pending = max(0, pending - 1)
    return {
        "accepted_count": int(accepted),
        "locked_count": int(locked),
        "pending_count": int(pending),
        "rejected_count": int(rejected),
        "needs_regeneration_count": int(needs_regen),
    }


def collect_production_pack_inputs(source_paths: Dict[str, Any]) -> Dict[str, Any]:
    """
    source_paths keys (all optional):
      asset_manifest, scene_asset_pack, script_json, voice_manifest, overlay_manifest, render_manifest,
      visual_cost_summary, provider_quality_summary, production_summary
    """
    out: Dict[str, Any] = {"paths": {}, "loaded": {}, "warnings": []}
    for k, v in (source_paths or {}).items():
        if v is None:
            continue
        out["paths"][k] = str(v)
    # load core jsons
    for key in (
        "asset_manifest",
        "scene_asset_pack",
        "script_json",
        "voice_manifest",
        "overlay_manifest",
        "render_manifest",
        "visual_cost_summary",
        "provider_quality_summary",
        "production_summary",
        "reference_library",
        "motion_clip_manifest",
    ):
        p = source_paths.get(key) if isinstance(source_paths, dict) else None
        doc, err = _read_json_or_none(Path(p) if p else None)
        out["loaded"][key] = doc
        if err and p:
            out["warnings"].append(f"{key}:{err}")
    return out


def _approval_to_readiness(
    approval_status: str,
    *,
    warnings: List[str],
) -> Tuple[bool, RenderReadinessStatus]:
    st = _s(approval_status).lower()
    if st == "approved":
        return True, "ready"
    if st == "needs_review":
        return False, "needs_review"
    if st == "blocked":
        return False, "blocked"
    warnings.append("approval_status_unknown_or_missing")
    return False, "blocked"


def build_production_summary(
    *,
    run_id: str,
    copied_files: List[Dict[str, Any]],
    missing_optional_files: List[str],
    missing_asset_files: List[str],
    asset_manifest: Optional[Dict[str, Any]],
    scene_asset_pack: Optional[Dict[str, Any]],
    script_data: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    warnings: List[str] = []
    blocking_reasons: List[str] = []

    assets: List[Dict[str, Any]] = []
    if isinstance(asset_manifest, dict) and isinstance(asset_manifest.get("assets"), list):
        assets = [a for a in asset_manifest.get("assets") if isinstance(a, dict)]

    approval_result = None
    if isinstance(asset_manifest, dict) and isinstance(asset_manifest.get("production_asset_approval_result"), dict):
        approval_result = asset_manifest.get("production_asset_approval_result")

    approval_status = _s(approval_result.get("approval_status") if isinstance(approval_result, dict) else "")
    if not approval_status:
        warnings.append("approval_result_missing")
        approval_status = "blocked"

    ready_for_render, readiness_status = _approval_to_readiness(approval_status, warnings=warnings)
    if readiness_status == "blocked":
        blocking_reasons.append("render_not_ready_due_to_approval_status")

    if isinstance(approval_result, dict):
        blocking_reasons.extend([_s(x) for x in (approval_result.get("blocking_reasons") or []) if _s(x)])
        warnings.extend([_s(x) for x in (approval_result.get("warnings") or []) if _s(x)])

    scenes_count = 0
    if isinstance(scene_asset_pack, dict):
        scenes = scene_asset_pack.get("scenes")
        if isinstance(scenes, list):
            scenes_count = len([x for x in scenes if isinstance(x, dict)])
    if scenes_count <= 0 and assets:
        scenes_count = len(assets)

    providers_used = _providers_used_from_assets(assets) if assets else []

    visual_policy_summary = _visual_policy_counts_from_assets(assets) if assets else {
        "safe_count": 0,
        "text_extracted_count": 0,
        "needs_review_count": 0,
        "guard_applied_count": 0,
        "text_sensitive_count": 0,
    }

    asset_decision_summary = _asset_decision_counts_from_assets(assets) if assets else {
        "accepted_count": 0,
        "locked_count": 0,
        "pending_count": 0,
        "rejected_count": 0,
        "needs_regeneration_count": 0,
    }

    visual_cost_summary = None
    if isinstance(asset_manifest, dict) and isinstance(asset_manifest.get("visual_cost_summary"), dict):
        visual_cost_summary = asset_manifest.get("visual_cost_summary")

    reference_library_summary = None
    # If a reference library is copied into the pack, we will additionally set reference_library_path there.
    # Here we only compute summary if a library doc is provided through pack build (see build_production_pack).

    continuity_wiring_summary = None
    if isinstance(asset_manifest, dict) and isinstance(asset_manifest.get("continuity_wiring_summary"), dict):
        continuity_wiring_summary = asset_manifest.get("continuity_wiring_summary")
    elif assets:
        # best-effort: if per-asset wiring exists, compute minimal counts
        prepared = 0
        missing = 0
        needs_review = 0
        none = 0
        for a in assets:
            st = _s(a.get("continuity_provider_preparation_status")).lower()
            if st == "prepared":
                prepared += 1
            elif st == "missing_reference":
                missing += 1
            elif st == "needs_review":
                needs_review += 1
            else:
                none += 1
        continuity_wiring_summary = {
            "assets_checked": int(len(assets)),
            "prepared_count": int(prepared),
            "missing_reference_count": int(missing),
            "needs_review_count": int(needs_review),
            "none_count": int(none),
            "warnings": [],
            "continuity_wiring_version": "ba27_2_v1",
        }

    reference_provider_payload_summary = None
    if isinstance(asset_manifest, dict) and isinstance(asset_manifest.get("reference_provider_payload_summary"), dict):
        reference_provider_payload_summary = asset_manifest.get("reference_provider_payload_summary")

    motion_clip_summary = None
    if isinstance(asset_manifest, dict) and isinstance(asset_manifest.get("motion_clip_manifest"), dict):
        mm = asset_manifest.get("motion_clip_manifest")
        if isinstance(mm, dict) and isinstance(mm.get("summary"), dict):
            motion_clip_summary = dict(mm.get("summary") or {})

    # BA 27.6 — mirror reference payloads into scene-like pack objects (summary only)
    reference_payload_mirror_summary = None
    if assets and isinstance(scene_asset_pack, dict):
        exp = scene_asset_pack.get("scene_expansion") if isinstance(scene_asset_pack.get("scene_expansion"), dict) else None
        beats = exp.get("expanded_scene_assets") if isinstance(exp, dict) else None
        if isinstance(beats, list) and beats:
            beats_dicts = [b for b in beats if isinstance(b, dict)]
            _mirrored, mirr = mirror_reference_payloads_by_scene(beats_dicts, assets)
            reference_payload_mirror_summary = {
                "mirror": mirr,
                "mirrored_items_summary": build_reference_payload_mirror_summary(_mirrored),
                "reference_payload_mirror_version": "ba27_6_v1",
            }
    # de-dupe & clamp list sizes
    warnings_u = list(dict.fromkeys([w for w in warnings if _s(w)]))
    blocks_u = list(dict.fromkeys([b for b in blocking_reasons if _s(b)]))

    title = ""
    if isinstance(script_data, dict):
        title = _s(script_data.get("title"))
    if not title and isinstance(scene_asset_pack, dict):
        title = _s(scene_asset_pack.get("title"))

    return {
        "run_id": _s(run_id),
        "pack_version": "ba27_0_v1",
        "ready_for_render": bool(ready_for_render),
        "render_readiness_status": readiness_status,
        "approval_status": approval_status,
        "blocking_reasons": blocks_u,
        "warnings": warnings_u,
        "generated_at": None,  # keep deterministic for tests
        "files": {
            "copied_files": copied_files,
            "missing_optional_files": sorted(set([_s(x) for x in missing_optional_files if _s(x)])),
            "missing_asset_files": sorted(set([_s(x) for x in missing_asset_files if _s(x)])),
        },
        "title": title,
        "scenes_count": int(scenes_count),
        "providers_used": providers_used,
        "visual_policy_summary": visual_policy_summary,
        "asset_decision_summary": asset_decision_summary,
        "visual_cost_summary": visual_cost_summary,
        "production_asset_approval_result": approval_result,
        "reference_library_path": None,
        "reference_library_summary": reference_library_summary,
        "continuity_wiring_summary": continuity_wiring_summary,
        "reference_provider_payload_summary": reference_provider_payload_summary,
        "reference_payload_mirror_summary": reference_payload_mirror_summary,
        "visual_production_preflight_result": build_visual_production_preflight_result(
            asset_manifest=asset_manifest if isinstance(asset_manifest, dict) else None,
            production_summary={
                "ready_for_render": bool(ready_for_render),
                "approval_status": approval_status,
                # BA 27.9: preflight only needs presence signals; keep summary deterministic
                "asset_manifest_reference_index": None,
                "asset_manifest_reference_index_path": None,
            },
        ),
        "motion_clip_manifest_path": None,
        "motion_clip_summary": motion_clip_summary,
        "render_input_bundle_path": None,
    }


def build_production_pack_reference(
    pack_result: Dict[str, Any],
    production_summary: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    BA 27.0b — Small, cockpit-friendly reference object (no re-render).
    """
    pr = pack_result if isinstance(pack_result, dict) else {}
    pack_dir = _s(pr.get("pack_dir"))
    summary = production_summary if isinstance(production_summary, dict) else pr.get("summary")
    if not isinstance(summary, dict):
        summary = {}

    prod_summary_path = ""
    if pack_dir:
        prod_summary_path = str((Path(pack_dir).resolve() / "production_summary.json"))

    files_written = pr.get("files_written") if isinstance(pr.get("files_written"), list) else []
    copied_files = None
    if isinstance(summary.get("files"), dict) and isinstance(summary["files"].get("copied_files"), list):
        copied_files = summary["files"].get("copied_files") or []

    assets_copied_count = 0
    if isinstance(copied_files, list):
        assets_copied_count = len([x for x in copied_files if isinstance(x, dict) and _s(x.get("kind")) == "asset" and _s(x.get("status")) in ("copied", "written")])

    return {
        "pack_version": "ba27_0_v1",
        "pack_dir": pack_dir,
        "production_summary_path": prod_summary_path,
        "ready_for_render": bool(summary.get("ready_for_render")) if isinstance(summary, dict) else bool(pr.get("ready_for_render")),
        "render_readiness_status": _s(summary.get("render_readiness_status") if isinstance(summary, dict) else pr.get("render_readiness_status")),
        "approval_status": _s(summary.get("approval_status") if isinstance(summary, dict) else pr.get("approval_status")),
        "blocking_reasons": summary.get("blocking_reasons") if isinstance(summary.get("blocking_reasons"), list) else (pr.get("blocking_reasons") or []),
        "warnings": summary.get("warnings") if isinstance(summary.get("warnings"), list) else (pr.get("warnings") or []),
        "files_written": list(files_written),
        "assets_copied_count": int(assets_copied_count),
        "created_by": "ba27_0b_snapshot_wiring",
    }


def write_production_pack_readme(*, pack_dir: Path, summary: Dict[str, Any]) -> Path:
    out = Path(pack_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    rid = _s(summary.get("run_id"))
    ready = bool(summary.get("ready_for_render"))
    st = _s(summary.get("render_readiness_status"))
    appr = _s(summary.get("approval_status"))
    blocks = summary.get("blocking_reasons") if isinstance(summary.get("blocking_reasons"), list) else []
    warns = summary.get("warnings") if isinstance(summary.get("warnings"), list) else []
    lines: List[str] = [
        "# Production Pack V1",
        "",
        "## Status",
        f"- Run ID: `{rid}`",
        f"- Renderbereit: **{str(ready).lower()}**",
        f"- Render-Status: `{st}`",
        f"- Approval status: `{appr}`",
        "",
        "## Key Files",
        f"- Production Summary: `{out / 'production_summary.json'}`",
        f"- Asset Manifest: `{out / 'asset_manifest.json'}`",
        f"- Production Asset Approval: `{out / 'production_asset_approval.json'}`",
        f"- Scene Asset Pack: `{out / 'scene_asset_pack.json'}`",
        f"- Script: `{out / 'script.json'}`",
        "",
        "## Assets",
        f"- Assets root: `{out / 'assets'}`",
        f"  - images: `{out / 'assets' / 'images'}`",
        f"  - clips: `{out / 'assets' / 'clips'}`",
        f"  - voice: `{out / 'assets' / 'voice'}`",
        f"  - overlays: `{out / 'assets' / 'overlays'}`",
        "",
    ]
    lines.append("## Blocking Reasons")
    if blocks:
        for b in blocks[:80]:
            lines.append(f"- {b}")
    else:
        lines.append("- Keine")
    lines.append("")
    lines.append("## Warnings")
    if warns:
        for w in warns[:120]:
            lines.append(f"- {w}")
    else:
        lines.append("- Keine")
    lines.append("")
    # BA 27.3 — Continuity (read-only, counts only)
    cs = summary.get("continuity_wiring_summary") if isinstance(summary.get("continuity_wiring_summary"), dict) else None
    if cs is not None:
        lines.append("## Kontinuität")
        lines.append(
            "- vorbereitet: "
            + str(cs.get("prepared_count", 0))
            + " · Referenz fehlt: "
            + str(cs.get("missing_reference_count", 0))
            + " · Prüfung nötig: "
            + str(cs.get("needs_review_count", 0))
            + " · keine: "
            + str(cs.get("none_count", 0))
        )
        lines.append("")
    p = out / "README_PRODUCTION_PACK.md"
    p.write_text("\n".join(lines), encoding="utf-8")
    return p


def build_production_pack(
    *,
    run_id: str,
    output_root: str | Path,
    source_paths: Dict[str, Any],
    pack_dir: str | Path | None = None,
    copy_assets: bool = True,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Creates output/production_pack_<run_id>/ with core jsons and copied assets.
    Returns dict with ok, pack_dir, summary, copied_files, warnings, blocking_reasons, files_written.
    """
    rid = _s(run_id)
    out_root = Path(output_root).resolve()
    target_dir = Path(pack_dir).resolve() if pack_dir else (out_root / f"production_pack_{rid}").resolve()

    inputs = collect_production_pack_inputs(source_paths)
    loaded = inputs.get("loaded") if isinstance(inputs.get("loaded"), dict) else {}

    asset_manifest = loaded.get("asset_manifest") if isinstance(loaded, dict) else None
    scene_asset_pack = loaded.get("scene_asset_pack") if isinstance(loaded, dict) else None
    script_data = loaded.get("script_json") if isinstance(loaded, dict) else None
    reference_library_doc = loaded.get("reference_library") if isinstance(loaded, dict) else None
    motion_clip_manifest_doc = loaded.get("motion_clip_manifest") if isinstance(loaded, dict) else None

    copied_files: List[Dict[str, Any]] = []
    missing_optional_files: List[str] = []
    missing_asset_files: List[str] = []
    files_written: List[str] = []

    # Determine manifest base dir for resolving relative asset paths
    asset_manifest_path = source_paths.get("asset_manifest") if isinstance(source_paths, dict) else None
    manifest_base = Path(asset_manifest_path).resolve().parent if asset_manifest_path else Path.cwd()

    def _copy_json(src_path: Optional[Path], dst_name: str, *, optional: bool = True) -> None:
        if src_path is None:
            if optional:
                missing_optional_files.append(dst_name)
            return
        src = Path(src_path).resolve()
        dst = target_dir / dst_name
        if not src.is_file():
            if optional:
                missing_optional_files.append(dst_name)
            return
        if dry_run:
            copied_files.append(
                {"kind": "json", "src": str(src), "dst": str(dst), "status": "dry_run_skipped", "bytes": _file_size_bytes_or_none(src)}
            )
            return
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied_files.append({"kind": "json", "src": str(src), "dst": str(dst), "status": "copied", "bytes": _file_size_bytes_or_none(dst)})
        files_written.append(str(dst))

    # Copy or write core json artefacts (copy preferred to preserve original fields)
    _copy_json(Path(source_paths.get("script_json")) if source_paths.get("script_json") else None, "script.json")
    _copy_json(Path(source_paths.get("scene_asset_pack")) if source_paths.get("scene_asset_pack") else None, "scene_asset_pack.json")
    _copy_json(Path(source_paths.get("asset_manifest")) if source_paths.get("asset_manifest") else None, "asset_manifest.json")
    _copy_json(Path(source_paths.get("voice_manifest")) if source_paths.get("voice_manifest") else None, "voice_manifest.json")
    _copy_json(Path(source_paths.get("overlay_manifest")) if source_paths.get("overlay_manifest") else None, "overlay_manifest.json")
    _copy_json(Path(source_paths.get("render_manifest")) if source_paths.get("render_manifest") else None, "render_manifest.json")
    _copy_json(Path(source_paths.get("visual_cost_summary")) if source_paths.get("visual_cost_summary") else None, "visual_cost_summary.json")
    _copy_json(Path(source_paths.get("provider_quality_summary")) if source_paths.get("provider_quality_summary") else None, "provider_quality_summary.json")
    _copy_json(Path(source_paths.get("reference_library")) if source_paths.get("reference_library") else None, "reference_library.json")
    _copy_json(Path(source_paths.get("motion_clip_manifest")) if source_paths.get("motion_clip_manifest") else None, "motion_clip_manifest.json")

    # Production asset approval json (from manifest result; do not recompute if missing)
    approval = None
    if isinstance(asset_manifest, dict) and isinstance(asset_manifest.get("production_asset_approval_result"), dict):
        approval = asset_manifest.get("production_asset_approval_result")
    if dry_run:
        copied_files.append(
            {
                "kind": "json",
                "src": "asset_manifest.production_asset_approval_result",
                "dst": str(target_dir / "production_asset_approval.json"),
                "status": "dry_run_skipped",
                "bytes": None,
            }
        )
    else:
        if approval is not None:
            _write_json(target_dir / "production_asset_approval.json", approval)
            files_written.append(str((target_dir / "production_asset_approval.json").resolve()))
            copied_files.append(
                {
                    "kind": "json",
                    "src": "asset_manifest.production_asset_approval_result",
                    "dst": str((target_dir / "production_asset_approval.json").resolve()),
                    "status": "written",
                    "bytes": _file_size_bytes_or_none((target_dir / "production_asset_approval.json").resolve()),
                }
            )
        else:
            missing_optional_files.append("production_asset_approval.json")

    # Copy asset files referenced in asset_manifest
    copied_asset_map: Dict[str, str] = {}  # src->dst
    if copy_assets and isinstance(asset_manifest, dict) and isinstance(asset_manifest.get("assets"), list):
        for a in asset_manifest.get("assets") or []:
            if not isinstance(a, dict):
                continue
            for key, path_str in _iter_asset_file_candidates(a):
                src_p = _resolve_maybe_relative(path_str, base_dir=manifest_base)
                if not src_p or not _s(path_str):
                    continue
                if str(src_p) in copied_asset_map:
                    continue
                if not _is_safe_file(src_p):
                    missing_asset_files.append(f"{key}:{path_str}")
                    continue
                bucket = _classify_asset_bucket(src_p)
                dst_dir = target_dir / "assets" / bucket
                dst = (dst_dir / src_p.name).resolve()
                if dry_run:
                    copied_files.append(
                        {"kind": "asset", "src": str(src_p), "dst": str(dst), "status": "dry_run_skipped", "bytes": _file_size_bytes_or_none(src_p)}
                    )
                    copied_asset_map[str(src_p)] = str(dst)
                    continue
                dst_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_p, dst)
                copied_asset_map[str(src_p)] = str(dst)
                copied_files.append({"kind": "asset", "src": str(src_p), "dst": str(dst), "status": "copied", "bytes": _file_size_bytes_or_none(dst)})
                files_written.append(str(dst))

    # Build summary + README
    summary = build_production_summary(
        run_id=rid,
        copied_files=copied_files,
        missing_optional_files=missing_optional_files,
        missing_asset_files=missing_asset_files,
        asset_manifest=asset_manifest if isinstance(asset_manifest, dict) else None,
        scene_asset_pack=scene_asset_pack if isinstance(scene_asset_pack, dict) else None,
        script_data=script_data if isinstance(script_data, dict) else None,
    )
    if isinstance(motion_clip_manifest_doc, dict):
        summary["motion_clip_manifest_path"] = str((target_dir / "motion_clip_manifest.json").resolve())
        if summary.get("motion_clip_summary") is None and isinstance(motion_clip_manifest_doc.get("summary"), dict):
            summary["motion_clip_summary"] = dict(motion_clip_manifest_doc.get("summary") or {})

    # BA 27.1: reference library summary (optional)
    if isinstance(reference_library_doc, dict) and _s(source_paths.get("reference_library")):
        summary["reference_library_path"] = str((target_dir / "reference_library.json").resolve())
        try:
            assets_for_ref = []
            if isinstance(asset_manifest, dict) and isinstance(asset_manifest.get("assets"), list):
                assets_for_ref = [a for a in asset_manifest.get("assets") if isinstance(a, dict)]
            summary["reference_library_summary"] = build_reference_library_summary(reference_library_doc, assets=assets_for_ref)
        except Exception:
            # keep summary robust; warnings already tracked elsewhere
            summary["reference_library_summary"] = {"reference_assets_count": 0, "types_count": {}, "warnings": ["reference_library_summary_failed"]}

    if not dry_run:
        # BA 27.7 — write compact reference index (optional but default-on when manifest present)
        try:
            if isinstance(asset_manifest, dict) and isinstance(asset_manifest.get("assets"), list):
                idx = build_asset_manifest_reference_index(asset_manifest)
                _write_json(target_dir / "asset_manifest_reference_index.json", idx)
                files_written.append(str((target_dir / "asset_manifest_reference_index.json").resolve()))
                # also surface in production summary
                summary["asset_manifest_reference_index_path"] = str(
                    (target_dir / "asset_manifest_reference_index.json").resolve()
                )
        except Exception:
            summary.setdefault("warnings", [])
            if isinstance(summary.get("warnings"), list):
                summary["warnings"].append("asset_manifest_reference_index_write_failed")

        _write_json(target_dir / "production_summary.json", summary)
        files_written.append(str((target_dir / "production_summary.json").resolve()))
        write_production_pack_readme(pack_dir=target_dir, summary=summary)
        files_written.append(str((target_dir / "README_PRODUCTION_PACK.md").resolve()))

    out = {
        "ok": True,
        "pack_dir": str(target_dir),
        "ready_for_render": bool(summary.get("ready_for_render")),
        "render_readiness_status": _s(summary.get("render_readiness_status")),
        "approval_status": _s(summary.get("approval_status")),
        "blocking_reasons": summary.get("blocking_reasons") if isinstance(summary.get("blocking_reasons"), list) else [],
        "warnings": summary.get("warnings") if isinstance(summary.get("warnings"), list) else [],
        "files_written": files_written,
        "summary": summary,
    }

    # BA 27.0b: write compact reference file for snapshot/cockpit wiring
    ref = build_production_pack_reference(out, production_summary=summary)
    out["production_pack_summary"] = ref
    if not dry_run:
        _write_json(target_dir / "production_pack_reference.json", ref)
        files_written.append(str((target_dir / "production_pack_reference.json").resolve()))

    return out

