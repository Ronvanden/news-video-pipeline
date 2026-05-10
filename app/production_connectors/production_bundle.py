"""BA 32.79 — Production Bundle / Final Output Pack V1 (local copy only).

No providers, no secrets, no uploads, no new rendering.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.production_connectors.thumbnail_pack_export import discover_thumbnail_batch_overlay_reports, pick_best_batch_overlay_report

_BUNDLE_VERSION = "ba32_79_v1"
_BATCH_JSON = "thumbnail_batch_overlay_result.json"
_OPEN_ME_NAME = "OPEN_ME_VIDEO_RESULT.html"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _clean(s: Optional[str]) -> str:
    return (s or "").strip()


def _warn_sanitize(w: str) -> str:
    t = str(w or "").strip()
    if not t:
        return ""
    low = t.lower()
    if "bearer " in low or "sk-" in low or "authorization" in low:
        return "production_bundle_warning_sanitized"
    if len(t) > 240:
        return t[:220] + "…"
    return t


def _safe_copy(*, src: Path, dest: Path, label: str) -> Dict[str, Any]:
    row: Dict[str, Any] = {
        "label": label,
        "source_path": str(src),
        "bundle_path": str(dest),
        "exists": False,
        "bytes_written": 0,
    }
    try:
        if not src.is_file():
            return row
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        row["exists"] = True
        row["bytes_written"] = int(dest.stat().st_size)
    except OSError:
        row["exists"] = False
    return row


def build_production_bundle_v1(
    *,
    output_dir: str | Path,
    run_id: Optional[str] = None,
    final_video_path: Optional[str] = None,
    script_path: Optional[str] = None,
    scene_asset_pack_path: Optional[str] = None,
    asset_manifest_path: Optional[str] = None,
    open_me_path: Optional[str] = None,
    thumbnail_pack: Optional[Dict[str, Any]] = None,
    warnings: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Creates ``output_dir/production_bundle/`` and copies known artifacts.
    Never raises; collects warnings. No file content inspection for secrets.
    """
    warns: List[str] = list(warnings or [])
    out_root = Path(output_dir).resolve()
    bundle_root = out_root / "production_bundle"
    manifest_path = bundle_root / "production_bundle_manifest.json"

    bundled: List[Dict[str, Any]] = []
    final_bundle_path: Optional[str] = None
    rec_thumb_bundle_path: Optional[str] = None

    if not out_root.is_dir():
        warns.append(_warn_sanitize("production_bundle_output_dir_not_found"))
        st = "missing"
        return {
            "production_bundle_version": _BUNDLE_VERSION,
            "production_bundle_status": st,
            "production_bundle_path": str(bundle_root),
            "production_bundle_manifest_path": str(manifest_path),
            "bundled_files": bundled,
            "recommended_thumbnail_bundle_path": None,
            "final_video_bundle_path": None,
            "warnings": warns,
        }

    try:
        bundle_root.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        warns.append(_warn_sanitize(f"production_bundle_mkdir_failed:{type(e).__name__}"))
        return {
            "production_bundle_version": _BUNDLE_VERSION,
            "production_bundle_status": "missing",
            "production_bundle_path": str(bundle_root),
            "production_bundle_manifest_path": str(manifest_path),
            "bundled_files": bundled,
            "recommended_thumbnail_bundle_path": None,
            "final_video_bundle_path": None,
            "warnings": warns,
        }

    def _copy_pair(label: str, src_s: Optional[str], dest_name: str) -> Dict[str, Any]:
        sp = _clean(src_s)
        if not sp:
            warns.append(f"production_bundle_missing_source:{label}")
            return {
                "label": label,
                "source_path": "",
                "bundle_path": str(bundle_root / dest_name),
                "exists": False,
                "bytes_written": 0,
            }
        src = Path(sp)
        dest = bundle_root / dest_name
        r = _safe_copy(src=src, dest=dest, label=label)
        if not r["exists"]:
            warns.append(f"production_bundle_copy_failed:{label}")
        return r

    # final_video.mp4 (fixed name in bundle)
    fv = _copy_pair("final_video", final_video_path, "final_video.mp4")
    bundled.append(fv)
    if fv.get("exists"):
        final_bundle_path = str(Path(fv["bundle_path"]).resolve())

    bundled.append(_copy_pair("script", script_path, "script.json"))
    bundled.append(_copy_pair("scene_asset_pack", scene_asset_pack_path, "scene_asset_pack.json"))
    bundled.append(_copy_pair("asset_manifest", asset_manifest_path, "asset_manifest.json"))

    # Thumbnail batch JSON
    tp = thumbnail_pack if isinstance(thumbnail_pack, dict) else {}
    batch_src = _clean(str(tp.get("thumbnail_pack_result_path") or ""))
    if not batch_src:
        found = pick_best_batch_overlay_report(discover_thumbnail_batch_overlay_reports(out_root))
        if found is not None:
            batch_src = str(found)
    b_row = _copy_pair("thumbnail_batch_overlay_result", batch_src or None, _BATCH_JSON)
    bundled.append(b_row)

    # Recommended thumbnail → recommended_thumbnail.png
    rec_src = _clean(str(tp.get("thumbnail_recommended_path") or ""))
    if rec_src:
        src = Path(rec_src)
        dest = bundle_root / "recommended_thumbnail.png"
        r = _safe_copy(src=src, dest=dest, label="recommended_thumbnail")
        bundled.append(r)
        if r.get("exists"):
            rec_thumb_bundle_path = str(Path(r["bundle_path"]).resolve())
        else:
            warns.append("production_bundle_recommended_thumbnail_copy_failed")
    else:
        bundled.append(
            {
                "label": "recommended_thumbnail",
                "source_path": "",
                "bundle_path": str(bundle_root / "recommended_thumbnail.png"),
                "exists": False,
                "bytes_written": 0,
            }
        )
        tp_st = str(tp.get("thumbnail_pack_status") or "") if isinstance(tp, dict) else ""
        if tp_st == "ready":
            warns.append("production_bundle_no_recommended_thumbnail_source")

    # OPEN_ME
    om = _clean(open_me_path or "")
    if om:
        om_row = _copy_pair("OPEN_ME_VIDEO_RESULT", om, _OPEN_ME_NAME)
        bundled.append(om_row)
        if not om_row.get("exists"):
            warns.append("production_bundle_open_me_copy_failed")
    else:
        bundled.append(
            {
                "label": "OPEN_ME_VIDEO_RESULT",
                "source_path": "",
                "bundle_path": str(bundle_root / _OPEN_ME_NAME),
                "exists": False,
                "bytes_written": 0,
            }
        )
        warns.append("production_bundle_open_me_source_missing")

    # Status: missing ohne final_video; ready wenn Kernartefakte + OPEN_ME + empfohlenes Thumbnail; sonst partial
    has_final = bool(final_bundle_path)
    has_script = any(x.get("label") == "script" and x.get("exists") for x in bundled)
    has_pack = any(x.get("label") == "scene_asset_pack" and x.get("exists") for x in bundled)
    has_manifest = any(x.get("label") == "asset_manifest" and x.get("exists") for x in bundled)
    has_open_me = any(x.get("label") == "OPEN_ME_VIDEO_RESULT" and x.get("exists") for x in bundled)
    has_thumb = bool(rec_thumb_bundle_path)
    core = has_script and has_pack and has_manifest

    if not has_final:
        st = "missing"
    elif core and has_open_me and has_thumb:
        st = "ready"
    elif has_final:
        st = "partial"
    else:
        st = "missing"

    manifest_body: Dict[str, Any] = {
        "run_id": _clean(run_id) or None,
        "created_at": _utc_now_iso(),
        "production_bundle_version": _BUNDLE_VERSION,
        "status": st,
        "bundled_files": bundled,
        "recommended_thumbnail_bundle_path": rec_thumb_bundle_path,
        "final_video_bundle_path": final_bundle_path,
        "source_output_dir": str(out_root),
        "warnings": [_warn_sanitize(w) for w in warns if _warn_sanitize(w)],
    }
    try:
        manifest_path.write_text(json.dumps(manifest_body, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except OSError as e:
        warns.append(_warn_sanitize(f"production_bundle_manifest_write_failed:{type(e).__name__}"))

    return {
        "production_bundle_version": _BUNDLE_VERSION,
        "production_bundle_status": st,
        "production_bundle_path": str(bundle_root.resolve()),
        "production_bundle_manifest_path": str(manifest_path.resolve()),
        "bundled_files": bundled,
        "recommended_thumbnail_bundle_path": rec_thumb_bundle_path,
        "final_video_bundle_path": final_bundle_path,
        "warnings": [_warn_sanitize(w) for w in warns if _warn_sanitize(w)],
    }
