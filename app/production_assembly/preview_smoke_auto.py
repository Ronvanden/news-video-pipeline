"""BA 29.2c/29.2d — Preview smoke auto-runner helpers (path discovery, manifest prep, bundle repair)."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from app.visual_plan.asset_approval_gate import apply_production_asset_approval_to_manifest
from app.visual_plan.legacy_manifest_upgrade import detect_legacy_asset_manifest_issues, upgrade_legacy_asset_manifest
from app.visual_plan.visual_costs import apply_visual_cost_to_asset, build_visual_cost_summary, get_default_visual_unit_costs

from app.production_assembly.render_input_bundle import build_render_input_bundle

_PREVIEW_SMOKE_VERSION = "ba29_2c_v1"

_MEDIA_PATH_ASSET_KEYS: Tuple[str, ...] = (
    "selected_asset_path",
    "generated_image_path",
    "image_path",
    "video_path",
    "clip_path",
    "voice_path",
)


def preserve_or_absolutize_asset_media_paths(
    manifest: Dict[str, Any],
    *,
    source_manifest_path: Path,
) -> Dict[str, Any]:
    """
    BA 29.2d — Resolve relative media paths in ``assets[]`` against the **source**
    manifest directory so prepared copies under ``.preview_smoke_work`` still point
    at real files. Additive ``media_path_preservation_summary`` on the manifest.
    """
    out = copy.deepcopy(manifest)
    source_dir = Path(source_manifest_path).resolve().parent
    warnings: List[str] = []
    absolutized = 0
    missing = 0

    assets = out.get("assets")
    if not isinstance(assets, list):
        out["media_path_preservation_summary"] = {
            "media_path_preservation_version": "ba29_2d_v1",
            "media_paths_absolutized_count": 0,
            "media_paths_missing_count": 0,
            "warnings": [],
        }
        return out

    for idx, a in enumerate(assets):
        if not isinstance(a, dict):
            continue
        for key in _MEDIA_PATH_ASSET_KEYS:
            if key not in a:
                continue
            raw = a.get(key)
            if raw is None:
                continue
            s = str(raw).strip()
            if not s:
                continue
            p = Path(s)
            if p.is_absolute():
                resolved = p.resolve()
                if resolved.is_file():
                    if str(resolved) != s:
                        a[key] = str(resolved)
                else:
                    missing += 1
                    warnings.append(f"asset[{idx}].{key}:missing_absolute:{s}")
                continue
            candidate = (source_dir / p).resolve()
            if candidate.is_file():
                a[key] = str(candidate)
                absolutized += 1
            else:
                missing += 1
                warnings.append(f"asset[{idx}].{key}:missing_relative:{candidate}")

    out["media_path_preservation_summary"] = {
        "media_path_preservation_version": "ba29_2d_v1",
        "media_paths_absolutized_count": int(absolutized),
        "media_paths_missing_count": int(missing),
        "warnings": warnings,
    }
    return out


def is_usable_asset_manifest(path: Path) -> bool:
    """True if JSON has non-empty ``assets`` list with at least one dict."""
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    assets = doc.get("assets")
    if not isinstance(assets, list) or not assets:
        return False
    return any(isinstance(a, dict) for a in assets)


def find_newest_usable_asset_manifest(
    output_root: Path,
    *,
    _rglob: Optional[Callable[[Path, str], List[Path]]] = None,
) -> Optional[Path]:
    """
    Newest ``asset_manifest.json`` under ``output_root`` (by mtime), excluding
    ``.preview_smoke_work`` trees. Returns None if none usable.
    """
    root = output_root.resolve()
    if not root.is_dir():
        return None

    def _glob(base: Path, pattern: str) -> List[Path]:
        return list(base.rglob(pattern))

    glob_fn = _rglob or _glob
    candidates: List[Path] = []
    for p in glob_fn(root, "asset_manifest.json"):
        try:
            if not p.is_file():
                continue
            if ".preview_smoke_work" in p.parts:
                continue
            if not is_usable_asset_manifest(p):
                continue
            candidates.append(p)
        except OSError:
            continue
    if not candidates:
        return None
    candidates.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return candidates[0]


def run_cost_tracking_on_manifest(manifest: Dict[str, Any], *, unit_costs: Optional[Dict[str, float]] = None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    out = dict(manifest or {})
    assets = out.get("assets")
    if not isinstance(assets, list) or not assets:
        raise ValueError("asset_manifest.assets empty or missing")
    uc = dict(unit_costs or get_default_visual_unit_costs())
    patched: List[Dict[str, Any]] = []
    for a in assets:
        if isinstance(a, dict):
            patched.append(apply_visual_cost_to_asset(a, unit_costs=uc))
        else:
            patched.append({"raw": str(a)})
    out["assets"] = patched
    summary = build_visual_cost_summary(patched, unit_costs=uc)
    out["visual_cost_summary"] = summary
    out["visual_cost_tracking_run"] = {"version": "ba26_8c_v1"}
    return out, summary


def prepare_asset_manifest_for_smoke(
    src: Path,
    work_dir: Path,
    *,
    run_id: str,
) -> Tuple[Path, Dict[str, Any]]:
    """
    Optionally legacy-upgrade, cost-track if missing, always re-apply approval gate.
    Writes ``asset_manifest_prepared_<run_id>.json`` under work_dir.
    """
    work_dir.mkdir(parents=True, exist_ok=True)
    doc = json.loads(Path(src).read_text(encoding="utf-8"))
    report: Dict[str, Any] = {
        "source_path": str(Path(src).resolve()),
        "legacy_upgrade_applied": False,
        "cost_tracking_applied": False,
        "approval_gate_applied": True,
    }

    issues = detect_legacy_asset_manifest_issues(doc)
    need_upgrade = bool(issues.get("manifest_issues")) or any(
        isinstance(r, dict) and bool(r.get("issues")) for r in (issues.get("assets") or [])
    )
    if need_upgrade:
        doc = upgrade_legacy_asset_manifest(doc)
        report["legacy_upgrade_applied"] = True

    if not isinstance(doc.get("visual_cost_summary"), dict):
        doc, _summ = run_cost_tracking_on_manifest(doc)
        report["cost_tracking_applied"] = True

    doc = preserve_or_absolutize_asset_media_paths(doc, source_manifest_path=Path(src).resolve())
    report["media_path_preservation_summary"] = doc.get("media_path_preservation_summary")

    doc = apply_production_asset_approval_to_manifest(doc)
    out_path = work_dir / f"asset_manifest_prepared_{run_id}.json"
    out_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report["prepared_path"] = str(out_path.resolve())
    return out_path, report


def ensure_bundle_has_media_paths(bundle: Dict[str, Any], bundle_path: Path) -> Tuple[Dict[str, Any], bool]:
    """
    If ``image_paths`` and ``clip_paths`` are both empty, rebuild bundle with embedded
    ``asset_manifest`` hydration. Returns (bundle_dict, rebuilt_flag).
    """
    imgs = [x for x in (bundle.get("image_paths") or []) if str(x or "").strip()]
    clips = [x for x in (bundle.get("clip_paths") or []) if str(x or "").strip()]
    if imgs or clips:
        return bundle, False
    amp = bundle.get("asset_manifest_path")
    if not amp or not Path(str(amp)).is_file():
        return bundle, False
    am_path = Path(str(amp)).resolve()
    try:
        am = json.loads(am_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return bundle, False
    new_b = build_render_input_bundle(
        run_id=str(bundle.get("run_id") or "smoke"),
        production_summary_path=bundle.get("production_summary_path"),
        asset_manifest_path=str(am_path),
        asset_manifest=am,
        motion_clip_manifest_path=bundle.get("motion_clip_manifest_path"),
        motion_timeline_manifest_path=bundle.get("motion_timeline_manifest_path"),
        subtitle_path=bundle.get("subtitle_path"),
        voice_paths=list(bundle.get("voice_paths") or []) if isinstance(bundle.get("voice_paths"), list) else [],
        clip_paths=[],
        image_paths=[],
        overlay_intents=list(bundle.get("overlay_intents") or []) if isinstance(bundle.get("overlay_intents"), list) else [],
        ready_for_render=bool(bundle.get("ready_for_render")),
        render_readiness_status=str(bundle.get("render_readiness_status") or ""),
        warnings=list(bundle.get("warnings") or []) if isinstance(bundle.get("warnings"), list) else [],
        blocking_reasons=list(bundle.get("blocking_reasons") or []) if isinstance(bundle.get("blocking_reasons"), list) else [],
    )
    bundle_path.write_text(json.dumps(new_b, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return new_b, True


def classify_preview_smoke_failure(
    *,
    preview_result: Optional[Dict[str, Any]],
    bundle: Optional[Dict[str, Any]],
) -> str:
    """Return one of: ``ffmpeg``, ``bundle``, ``asset_media``, ``unknown``."""
    pr = preview_result if isinstance(preview_result, dict) else {}
    b = bundle if isinstance(bundle, dict) else {}

    if pr.get("error_code") == "ffmpeg_missing" or pr.get("ffmpeg_available") is False:
        return "ffmpeg"

    imgs = [x for x in (b.get("image_paths") or []) if str(x or "").strip()]
    clips = [x for x in (b.get("clip_paths") or []) if str(x or "").strip()]
    summ = b.get("media_path_hydration_summary") if isinstance(b.get("media_path_hydration_summary"), dict) else {}
    try:
        hyd_n = int(summ.get("images_found", 0) or 0) + int(summ.get("clips_found", 0) or 0)
    except (TypeError, ValueError):
        hyd_n = 0
    has_bundle_media = bool(imgs or clips)

    br = [str(x) for x in (pr.get("blocking_reasons") or []) if str(x or "").strip()]
    br_join = " ".join(br).lower()
    err_c = str(pr.get("error_code") or "").lower()

    if not has_bundle_media and hyd_n <= 0:
        if (
            "no_preview_scenes_derived" in br_join
            or "no_media_segments_built" in br_join
            or "no_media" in br_join
            or err_c == "no_media"
        ):
            return "asset_media"

    if any("concat_failed" in x.lower() or "image_segment_failed" in x.lower() for x in br):
        return "ffmpeg"
    if any("ffmpeg" in x.lower() and "ffmpeg_missing" not in x.lower() for x in br):
        return "ffmpeg"

    if br:
        return "bundle"
    return "unknown"


def write_preview_smoke_open_me_report(summary: Dict[str, Any], output_dir: Path) -> Path:
    """
    BA 30.1 — Operator-readable ``OPEN_PREVIEW_SMOKE.md`` (German copy). JSON keys in ``summary`` stay English.
    """
    out_dir = Path(output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "OPEN_PREVIEW_SMOKE.md"

    pr = summary.get("preview_result") if isinstance(summary.get("preview_result"), dict) else {}
    ok = bool(summary.get("ok"))
    status_de = "**Erfolgreich**" if ok else "**Blockiert**"

    def _p(key: str) -> str:
        v = summary.get(key)
        return str(v).strip() if v else ""

    video = str(pr.get("output_video_path") or "").strip()
    prev_json = _p("local_preview_render_result_path")
    prod_summ = _p("production_run_summary_path")
    bundle_p = _p("render_input_bundle_path")
    pack_p = _p("production_pack_path")

    dur = pr.get("duration_seconds")
    try:
        dur_s = f"{float(dur):.1f} s" if dur is not None else "—"
    except (TypeError, ValueError):
        dur_s = "—"

    scenes = pr.get("scenes_rendered")
    scenes_s = str(int(scenes)) if scenes is not None else "—"
    uimg = pr.get("used_images_count")
    uclip = pr.get("used_clips_count")
    uimg_s = str(int(uimg)) if uimg is not None else "—"
    uclip_s = str(int(uclip)) if uclip is not None else "—"

    ff = pr.get("ffmpeg_available")
    ff_s = "ja" if ff is True else ("nein" if ff is False else "—")

    op_br = summary.get("operator_blocking_reasons") if isinstance(summary.get("operator_blocking_reasons"), list) else []
    pr_br = pr.get("blocking_reasons") if isinstance(pr.get("blocking_reasons"), list) else []
    blocking = list(dict.fromkeys([str(x).strip() for x in (list(op_br) + list(pr_br)) if str(x or "").strip()]))
    if not ok and summary.get("failure_class") and str(summary.get("failure_class")).strip():
        blocking.insert(0, f"failure_class:{summary.get('failure_class')}")

    warns = pr.get("warnings") if isinstance(pr.get("warnings"), list) else []
    warn_lines = [str(w).strip() for w in warns if str(w or "").strip()]

    lines: List[str] = [
        "# Preview Smoke Ergebnis",
        "",
        "## Status",
        "",
        status_de,
        "",
        "## Lauf",
        "",
        f"- **Run ID:** `{summary.get('run_id', '')}`",
        "",
        "## Pfade",
        "",
        f"- **Video (lokal):** `{video or '—'}`",
        f"- **Preview-Result (JSON):** `{prev_json or '—'}`",
        f"- **Production-Run-Summary:** `{prod_summ or '—'}`",
        f"- **Render-Input-Bundle:** `{bundle_p or '—'}`",
    ]
    if pack_p:
        lines.append(f"- **Production Pack:** `{pack_p}`")
    else:
        lines.append("- **Production Pack:** — (nicht verfügbar)")

    lines.extend(
        [
            "",
            "## Preview-Kennzahlen",
            "",
            f"- **Dauer:** {dur_s}",
            f"- **Szenen gerendert:** {scenes_s}",
            f"- **Genutzte Bilder:** {uimg_s}",
            f"- **Genutzte Clips:** {uclip_s}",
            f"- **FFmpeg verfügbar:** {ff_s}",
            "",
            "## Blockierende Gründe",
            "",
        ]
    )
    if blocking:
        for b in blocking:
            lines.append(f"- {b}")
    else:
        lines.append("- *(keine)*")

    lines.extend(["", "## Warnungen", ""])
    if warn_lines:
        for w in warn_lines:
            lines.append(f"- {w}")
    else:
        lines.append("- *(keine)*")

    lines.extend(
        [
            "",
            "## Nächste Schritte",
            "",
            "1. **Video öffnen:** Lokale MP4 im Player prüfen (Pfad siehe oben).",
            "2. **Preview bewerten:** Bild/Ton/Timing grob gegen Erwartung checken.",
        ]
    )
    if ok:
        lines.extend(
            [
                "3. **Wenn in Ordnung:** Human Preview Review freigeben (`scripts/patch_human_preview_review.py` bzw. dokumentierter Gate-Pfad).",
                "4. **Wenn nicht in Ordnung:** Assets, Prompts oder Clip-Eingaben im Pack/Manifest prüfen und Smoke erneut fahren.",
            ]
        )
    else:
        lines.extend(
            [
                "3. **Fehler eingrenzen:** Blockierende Gründe und Warnungen oben abarbeiten (Bundle, Medienpfade, FFmpeg).",
                "4. **Nach Fix:** Preview-Smoke erneut ausführen (`scripts/run_preview_smoke_auto.py`).",
            ]
        )

    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _attach_open_preview_smoke_report(summary: Dict[str, Any], report_dir: Path) -> None:
    """Mutates ``summary`` with ``open_preview_smoke_report_path``; non-fatal errors → ``open_preview_smoke_write_warnings``."""
    try:
        p = write_preview_smoke_open_me_report(summary, report_dir)
        summary["open_preview_smoke_report_path"] = str(p.resolve())
    except Exception as e:
        summary["open_preview_smoke_report_path"] = ""
        w = summary.get("open_preview_smoke_write_warnings")
        if not isinstance(w, list):
            w = []
        w.append(f"open_preview_smoke_report_failed:{type(e).__name__}:{str(e)[:200]}")
        summary["open_preview_smoke_write_warnings"] = w


def build_preview_smoke_auto_summary(
    *,
    run_id: str,
    ok: bool,
    source_manifest: str,
    prepared_manifest: str,
    bundle_path: str,
    bundle: Dict[str, Any],
    preview_result: Optional[Dict[str, Any]],
    preparation_report: Dict[str, Any],
    failure_class: str,
    bundle_repaired: bool,
) -> Dict[str, Any]:
    return {
        "preview_smoke_version": _PREVIEW_SMOKE_VERSION,
        "run_id": run_id,
        "ok": bool(ok),
        "failure_class": failure_class if not ok else None,
        "source_asset_manifest": source_manifest,
        "prepared_asset_manifest": prepared_manifest,
        "render_input_bundle_path": bundle_path,
        "bundle_ready_for_render": bool(bundle.get("ready_for_render")),
        "bundle_repaired": bool(bundle_repaired),
        "image_paths_count": len([x for x in (bundle.get("image_paths") or []) if str(x or "").strip()]),
        "clip_paths_count": len([x for x in (bundle.get("clip_paths") or []) if str(x or "").strip()]),
        "media_path_hydration_summary": bundle.get("media_path_hydration_summary"),
        "preview_result": preview_result,
        "preparation_report": preparation_report,
    }


def execute_preview_smoke_auto(
    *,
    run_id: str,
    output_root: Path,
    asset_manifest: Optional[Path] = None,
    run_controlled_production_run_fn: Optional[Callable[..., Dict[str, Any]]] = None,
    run_local_preview_from_bundle_fn: Optional[Callable[..., Dict[str, Any]]] = None,
    duration_target_seconds: int = 45,
    provider: str = "auto",
    max_timeline_scenes: int = 5,
) -> Tuple[Dict[str, Any], int]:
    """
    BA 29.2c — Find/prepare manifest, run BA 29.0, repair bundle media paths if needed,
    run local preview, return (summary_dict, exit_code). No live providers/uploads.

    ``max_timeline_scenes``: forwarded to ``run_controlled_production_run`` (default **5**).
    """
    from app.production_assembly.controlled_production_run import run_controlled_production_run
    from app.production_assembly.local_preview_render import run_local_preview_from_bundle

    out_root = Path(output_root).resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    rid = str(run_id)
    work_dir = out_root / ".preview_smoke_work" / rid
    work_dir.mkdir(parents=True, exist_ok=True)

    src = Path(asset_manifest).resolve() if asset_manifest is not None else find_newest_usable_asset_manifest(out_root)
    if src is None or not src.is_file():
        summ = {
            "preview_smoke_version": _PREVIEW_SMOKE_VERSION,
            "run_id": rid,
            "ok": False,
            "failure_class": "bundle",
            "operator_blocking_reasons": ["no_usable_asset_manifest_under_output_root"],
            "source_asset_manifest": str(asset_manifest) if asset_manifest else "",
            "prepared_asset_manifest": "",
            "render_input_bundle_path": "",
            "bundle_ready_for_render": False,
            "bundle_repaired": False,
            "image_paths_count": 0,
            "clip_paths_count": 0,
            "media_path_hydration_summary": None,
            "preview_result": None,
            "preparation_report": {},
            "local_preview_render_result_path": "",
            "production_run_summary_path": "",
            "production_pack_path": "",
        }
        _attach_open_preview_smoke_report(summ, work_dir)
        return summ, 2

    prepared_path, prep_report = prepare_asset_manifest_for_smoke(src, work_dir, run_id=rid)
    prod_fn = run_controlled_production_run_fn or run_controlled_production_run
    prev_fn = run_local_preview_from_bundle_fn or run_local_preview_from_bundle

    try:
        prod = prod_fn(
            run_id=rid,
            output_root=out_root,
            asset_manifest_path=prepared_path,
            scene_asset_pack=None,
            script_json=None,
            duration_target_seconds=int(duration_target_seconds),
            provider=str(provider),
            render_local_preview=False,
            max_timeline_scenes=int(max_timeline_scenes),
        )
    except Exception as e:
        summ = {
            "preview_smoke_version": _PREVIEW_SMOKE_VERSION,
            "run_id": rid,
            "ok": False,
            "failure_class": "bundle",
            "operator_blocking_reasons": [f"controlled_production_run_failed:{type(e).__name__}"],
            "failure_detail": str(e)[:800],
            "source_asset_manifest": str(src.resolve()),
            "prepared_asset_manifest": str(prepared_path.resolve()),
            "render_input_bundle_path": "",
            "bundle_ready_for_render": False,
            "bundle_repaired": False,
            "image_paths_count": 0,
            "clip_paths_count": 0,
            "media_path_hydration_summary": None,
            "preview_result": None,
            "preparation_report": prep_report,
            "local_preview_render_result_path": "",
            "production_run_summary_path": "",
            "production_pack_path": "",
        }
        _attach_open_preview_smoke_report(summ, work_dir)
        return summ, 4

    bundle_path = Path(str(prod.get("bundle_path") or "")).resolve()
    bundle = prod.get("bundle") if isinstance(prod.get("bundle"), dict) else {}
    prod_summary_path = str(prod.get("first_real_production_run_summary_path") or "")

    bundle_checks = {
        "ready_for_render": bool(bundle.get("ready_for_render")),
        "image_paths_nonempty": bool([x for x in (bundle.get("image_paths") or []) if str(x or "").strip()]),
        "clip_paths_nonempty": bool([x for x in (bundle.get("clip_paths") or []) if str(x or "").strip()]),
        "media_path_hydration_summary": bundle.get("media_path_hydration_summary"),
    }

    bundle_repaired = False
    if bundle_path.is_file():
        bundle, bundle_repaired = ensure_bundle_has_media_paths(bundle, bundle_path)
        bundle_checks_after = {
            "ready_for_render": bool(bundle.get("ready_for_render")),
            "image_paths_nonempty": bool([x for x in (bundle.get("image_paths") or []) if str(x or "").strip()]),
            "clip_paths_nonempty": bool([x for x in (bundle.get("clip_paths") or []) if str(x or "").strip()]),
            "media_path_hydration_summary": bundle.get("media_path_hydration_summary"),
        }
    else:
        bundle_checks_after = dict(bundle_checks)

    preview_out = work_dir / "local_preview"
    preview_out.mkdir(parents=True, exist_ok=True)
    timeline = prod.get("timeline") if isinstance(prod.get("timeline"), dict) else None

    preview_result = prev_fn(
        bundle=bundle,
        bundle_path=str(bundle_path) if bundle_path.is_file() else "",
        output_dir=preview_out,
        output_video_name=f"local_preview_{rid}.mp4",
        timeline_override=timeline,
        default_scene_seconds=5.0,
    )
    result_path = preview_out / "local_preview_render_result.json"
    result_path.write_text(json.dumps(preview_result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    ok = bool(preview_result.get("ok"))
    fail_cls = classify_preview_smoke_failure(preview_result=preview_result, bundle=bundle)
    if not ok and fail_cls == "unknown" and not bundle_path.is_file():
        fail_cls = "bundle"

    summary = build_preview_smoke_auto_summary(
        run_id=rid,
        ok=ok,
        source_manifest=str(src.resolve()),
        prepared_manifest=str(prepared_path.resolve()),
        bundle_path=str(bundle_path) if bundle_path.is_file() else "",
        bundle=bundle,
        preview_result=preview_result,
        preparation_report=prep_report,
        failure_class=fail_cls,
        bundle_repaired=bundle_repaired,
    )
    summary["bundle_checks_before_repair"] = bundle_checks
    summary["bundle_checks_after_repair"] = bundle_checks_after
    summary["local_preview_render_result_path"] = str(result_path.resolve())
    summary["production_run_summary_path"] = prod_summary_path
    summary["preview_output_dir"] = str(preview_out.resolve())
    pr_br = [str(x) for x in (preview_result.get("blocking_reasons") or []) if str(x or "").strip()]
    if pr_br:
        summary["operator_blocking_reasons"] = pr_br
    pd = prod.get("pack_dir")
    summary["production_pack_path"] = str(Path(str(pd)).resolve()) if pd else ""
    _attach_open_preview_smoke_report(summary, work_dir)
    exit_code = 0 if ok else 3
    return summary, exit_code
