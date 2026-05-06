"""BA 30.3/30.4 — Read-only snapshot + readiness gate for Fresh Topic Preview Smoke (Founder Dashboard)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

_FRESH_PREVIEW_SNAPSHOT_VERSION = "ba30_4_v1"
_SUMMARY_READ_MAX_BYTES = 512_000
_READ_JSON_MAX_BYTES = 512_000


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _resolve_output_root(output_root: Union[str, Path]) -> Path:
    p = Path(output_root)
    if not p.is_absolute():
        p = _repo_root() / p
    return p.resolve()


def _safe_is_file(path: Path) -> bool:
    try:
        return path.is_file() and not path.is_symlink()
    except OSError:
        return False


def _safe_is_dir(path: Path) -> bool:
    try:
        return path.is_dir() and not path.is_symlink()
    except OSError:
        return False


def _list_run_dirs(fresh_base: Path) -> List[Path]:
    out: List[Path] = []
    try:
        for child in fresh_base.iterdir():
            try:
                if child.name.startswith("."):
                    continue
                if _safe_is_dir(child):
                    out.append(child)
            except OSError:
                continue
    except OSError:
        return []
    return out


def _dir_mtime(p: Path) -> float:
    try:
        return float(p.stat().st_mtime)
    except OSError:
        return 0.0


def _read_json_capped(path: Path, *, max_bytes: int = _READ_JSON_MAX_BYTES) -> Optional[Dict[str, Any]]:
    if not _safe_is_file(path):
        return None
    try:
        sz = path.stat().st_size
        if sz > max_bytes:
            return None
        raw = path.read_text(encoding="utf-8")
        doc = json.loads(raw)
        return doc if isinstance(doc, dict) else None
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return None


def evaluate_fresh_preview_readiness(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """
    BA 30.4 — Additive readiness from an existing snapshot dict (paths + presence flags).
    Returns keys to merge: readiness_status, readiness_score, readiness_reasons, blocking_reasons, operator_next_step.
    """
    rb: List[str] = []
    rr: List[str] = []
    status = "ready"
    score = 100

    avail = bool(snapshot.get("fresh_preview_available"))
    if not avail:
        rb.append("fresh_preview_not_available")
        status = "blocked"
        score = 0
        return {
            "readiness_status": status,
            "readiness_score": score,
            "readiness_reasons": rr,
            "blocking_reasons": rb,
            "operator_next_step": snapshot.get("operator_next_step")
            or (
                "Fresh Preview Smoke starten: "
                "python scripts/run_fresh_topic_preview_smoke.py --run-id <id> --output-root output --topic \"…\""
            ),
        }

    sp = str(snapshot.get("script_path") or "").strip()
    pp = str(snapshot.get("scene_asset_pack_path") or "").strip()
    ap = str(snapshot.get("asset_manifest_path") or "").strip()

    if not snapshot.get("script_json_present"):
        rb.append("missing_script_json")
    elif sp:
        sdoc = _read_json_capped(Path(sp))
        if sdoc is None:
            rb.append("script_json_invalid_or_too_large")
        else:
            has_body = bool(
                (str(sdoc.get("title") or "").strip())
                or (str(sdoc.get("hook") or "").strip())
                or (str(sdoc.get("full_script") or "").strip())
                or (isinstance(sdoc.get("chapters"), list) and len(sdoc.get("chapters") or []) > 0)
            )
            if not has_body:
                rb.append("script_missing_usable_content")

    if not snapshot.get("scene_asset_pack_present"):
        rb.append("missing_scene_asset_pack")
    elif pp:
        pdoc = _read_json_capped(Path(pp))
        if pdoc is None:
            rb.append("scene_asset_pack_invalid_or_too_large")
        else:
            se = pdoc.get("scene_expansion")
            beats = se.get("expanded_scene_assets") if isinstance(se, dict) else None
            if not isinstance(beats, list) or not beats:
                rb.append("scene_asset_pack_missing_scenes")

    if not snapshot.get("asset_manifest_present"):
        rb.append("missing_asset_manifest")
    elif ap:
        adoc = _read_json_capped(Path(ap))
        if adoc is None:
            rb.append("asset_manifest_invalid_or_too_large")
        else:
            assets = adoc.get("assets")
            if not isinstance(assets, list) or not assets:
                rr.append("manifest_assets_empty")
            elif _manifest_assets_look_placeholder_only(assets):
                rr.append("manifest_assets_look_placeholder_only")

    if rb:
        status = "blocked"
        score = max(0, min(35, 28 - 4 * max(0, len(rb) - 1)))
        next_step = (
            "Pflichtartefakte vervollständigen oder Fresh-Smoke erneut ausführen. "
            "Siehe blocking_reasons im Snapshot."
        )
        return {
            "readiness_status": status,
            "readiness_score": score,
            "readiness_reasons": rr,
            "blocking_reasons": rb,
            "operator_next_step": next_step,
        }

    if not snapshot.get("preview_smoke_summary_present"):
        rr.append("missing_preview_smoke_auto_summary")
    else:
        summ_p = str(snapshot.get("preview_smoke_summary_path") or "").strip()
        if summ_p:
            sdoc = _read_json_capped(Path(summ_p))
            if sdoc is None:
                rr.append("preview_smoke_summary_unparseable")
            elif sdoc.get("ok") is not True:
                rr.append("preview_smoke_summary_ok_false")

    if not snapshot.get("open_preview_smoke_report_present"):
        rr.append("missing_open_preview_smoke_md")

    if rr:
        status = "warning"
        score = max(40, min(78, 72 - 6 * len(rr)))

    if status == "ready":
        score = min(100, 95)

    if status == "blocked":
        next_step = snapshot.get("operator_next_step") or "Run prüfen und blocking_reasons abarbeiten."
    elif status == "warning":
        next_step = (
            "Vorschau-Pipeline vervollständigen (ohne --dry-run), OPEN_PREVIEW_SMOKE.md und Summary prüfen. "
            "Bei nur-Placeholder-Assets optional --allow-live-assets nur mit Keys."
        )
    else:
        next_step = (
            snapshot.get("operator_next_step")
            or "OPEN_PREVIEW_SMOKE.md und MP4 prüfen; bei Bedarf Human Preview Review (patch_human_preview_review.py)."
        )

    return {
        "readiness_status": status,
        "readiness_score": int(score),
        "readiness_reasons": rr,
        "blocking_reasons": rb,
        "operator_next_step": next_step,
    }


def _manifest_assets_look_placeholder_only(assets: List[Any]) -> bool:
    if not assets:
        return False
    http_re = re.compile(r"https?://", re.I)
    for a in assets:
        if not isinstance(a, dict):
            continue
        for key in ("selected_asset_path", "image_path", "generated_image_path", "video_path", "clip_path"):
            raw = str(a.get(key) or "").strip()
            if http_re.search(raw):
                return False
            if raw.lower().endswith(".mp4") and not raw.lower().endswith("_placeholder.mp4"):
                if "placeholder" not in raw.lower():
                    return False
    return True


def _merge_readiness(base: Dict[str, Any]) -> Dict[str, Any]:
    r = evaluate_fresh_preview_readiness(base)
    out = dict(base)
    out.update(r)
    return out


def build_latest_fresh_preview_snapshot(output_root: Union[str, Path] = "output") -> Dict[str, Any]:
    """
    Scan ``<output_root>/fresh_topic_preview/<run_id>/`` for the newest run (by directory mtime).
    BA 30.4: merged ``evaluate_fresh_preview_readiness`` (additive gate fields).
    """
    warnings: List[str] = []
    empty_paths: Dict[str, str] = {
        "latest_run_id": "",
        "latest_run_dir": "",
        "script_path": "",
        "scene_asset_pack_path": "",
        "asset_manifest_path": "",
        "preview_smoke_summary_path": "",
        "open_preview_smoke_report_path": "",
        "operator_next_step": (
            "Fresh Preview Smoke starten: "
            "python scripts/run_fresh_topic_preview_smoke.py --run-id <id> --output-root output --topic \"…\""
        ),
    }

    try:
        root = _resolve_output_root(output_root)
    except OSError as e:
        return _merge_readiness(
            {
                "ok": False,
                "fresh_preview_snapshot_version": _FRESH_PREVIEW_SNAPSHOT_VERSION,
                "fresh_preview_available": False,
                **empty_paths,
                "script_json_present": False,
                "scene_asset_pack_present": False,
                "asset_manifest_present": False,
                "preview_smoke_summary_present": False,
                "open_preview_smoke_report_present": False,
                "warnings": [f"output_root_resolve_failed:{type(e).__name__}"],
            }
        )

    fresh_base = root / "fresh_topic_preview"
    if not _safe_is_dir(fresh_base):
        return _merge_readiness(
            {
                "ok": True,
                "fresh_preview_snapshot_version": _FRESH_PREVIEW_SNAPSHOT_VERSION,
                "fresh_preview_available": False,
                **empty_paths,
                "script_json_present": False,
                "scene_asset_pack_present": False,
                "asset_manifest_present": False,
                "preview_smoke_summary_present": False,
                "open_preview_smoke_report_present": False,
                "warnings": ["fresh_topic_preview_dir_absent"],
            }
        )

    candidates = _list_run_dirs(fresh_base)
    if not candidates:
        return _merge_readiness(
            {
                "ok": True,
                "fresh_preview_snapshot_version": _FRESH_PREVIEW_SNAPSHOT_VERSION,
                "fresh_preview_available": False,
                **empty_paths,
                "script_json_present": False,
                "scene_asset_pack_present": False,
                "asset_manifest_present": False,
                "preview_smoke_summary_present": False,
                "open_preview_smoke_report_present": False,
                "warnings": ["no_fresh_run_directories"],
            }
        )

    candidates.sort(key=_dir_mtime, reverse=True)
    run_dir = candidates[0]
    run_id = run_dir.name

    script_path = run_dir / "script.json"
    pack_path = run_dir / "scene_asset_pack.json"
    gen_dir = run_dir / f"generated_assets_{run_id}"
    am_path = gen_dir / "asset_manifest.json"
    summ_path = root / f"preview_smoke_auto_summary_{run_id}.json"
    open_default = root / ".preview_smoke_work" / run_id / "OPEN_PREVIEW_SMOKE.md"

    script_ok = _safe_is_file(script_path)
    pack_ok = _safe_is_file(pack_path)
    am_ok = _safe_is_file(am_path)
    summ_ok = _safe_is_file(summ_path)

    open_path_str = ""
    if summ_ok:
        try:
            sz = summ_path.stat().st_size
            if sz <= _SUMMARY_READ_MAX_BYTES:
                raw = summ_path.read_text(encoding="utf-8")
                doc = json.loads(raw)
                op = doc.get("open_preview_smoke_report_path")
                if op:
                    op_p = Path(str(op))
                    if _safe_is_file(op_p):
                        open_path_str = str(op_p.resolve())
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            warnings.append("preview_smoke_summary_parse_skipped")

    if not open_path_str and _safe_is_file(open_default):
        open_path_str = str(open_default.resolve())

    if not script_ok:
        warnings.append("missing_script_json")
    if not pack_ok:
        warnings.append("missing_scene_asset_pack")
    if not am_ok:
        warnings.append("missing_asset_manifest")
    if not summ_ok:
        warnings.append("missing_preview_smoke_auto_summary")
    open_present = bool(open_path_str)
    if not open_present:
        warnings.append("missing_open_preview_smoke_md")

    if am_ok and open_present:
        next_step = (
            "Lokale OPEN_PREVIEW_SMOKE.md öffnen, MP4 prüfen, bei Bedarf Human Preview Review setzen "
            "(scripts/patch_human_preview_review.py)."
        )
    elif am_ok and summ_ok:
        next_step = (
            "Preview-Summary vorhanden; OPEN_PREVIEW_SMOKE.md fehlt ggf. (nur --dry-run?). "
            "Erneut ohne --dry-run ausführen oder Report-Pfad im Summary prüfen."
        )
    elif am_ok:
        next_step = "Asset-Manifest vorhanden; vollständigen Preview-Smoke ausführen (ohne --dry-run), um Summary und Open-Me zu erhalten."
    else:
        next_step = (
            "Run-Ordner unvollständig. Fresh-Smoke erneut starten oder Asset-Runner-Fehler im Terminal prüfen."
        )

    base = {
        "ok": True,
        "fresh_preview_snapshot_version": _FRESH_PREVIEW_SNAPSHOT_VERSION,
        "fresh_preview_available": True,
        "latest_run_id": run_id,
        "latest_run_dir": str(run_dir.resolve()),
        "script_path": str(script_path.resolve()) if script_ok else "",
        "scene_asset_pack_path": str(pack_path.resolve()) if pack_ok else "",
        "asset_manifest_path": str(am_path.resolve()) if am_ok else "",
        "preview_smoke_summary_path": str(summ_path.resolve()) if summ_ok else "",
        "open_preview_smoke_report_path": open_path_str,
        "operator_next_step": next_step,
        "script_json_present": script_ok,
        "scene_asset_pack_present": pack_ok,
        "asset_manifest_present": am_ok,
        "preview_smoke_summary_present": summ_ok,
        "open_preview_smoke_report_present": open_present,
        "warnings": warnings,
    }
    return _merge_readiness(base)
