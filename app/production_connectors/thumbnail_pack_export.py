"""BA 32.77 — Thumbnail Pack Export (read/normalize only).

Loads ``thumbnail_batch_overlay_result.json`` (BA 32.76) from a run output tree.
No providers, no secrets, no uploads.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

_THUMBNAIL_PACK_VERSION = "ba32_77_v1"
_BATCH_RESULT_NAME = "thumbnail_batch_overlay_result.json"


def _empty_pack(status: str) -> Dict[str, Any]:
    return {
        "thumbnail_pack_version": _THUMBNAIL_PACK_VERSION,
        "thumbnail_pack_status": status,
        "thumbnail_pack_path": "",
        "thumbnail_pack_result_path": "",
        "thumbnail_recommended_path": "",
        "thumbnail_recommended_text_lines": [],
        "thumbnail_recommended_style_preset": "",
        "thumbnail_variants": [],
        "thumbnail_generated_count": 0,
        "thumbnail_top_score": None,
        "thumbnail_recommended_score": None,
    }


def _normalize_variant(row: Dict[str, Any]) -> Dict[str, Any]:
    lines = row.get("text_lines")
    if not isinstance(lines, list):
        lines = []
    lines = [str(x) for x in lines if str(x or "").strip()]
    try:
        sc = int(row.get("score"))
    except (TypeError, ValueError):
        sc = 0
    return {
        "output_id": str(row.get("output_id") or ""),
        "score": sc,
        "style_preset": str(row.get("style_preset") or ""),
        "text_lines": lines,
        "output_path": str(row.get("output_path") or ""),
    }


def normalize_thumbnail_pack_from_batch_report(
    raw: Dict[str, Any],
    *,
    result_path: Path,
) -> Dict[str, Any]:
    """Build thumbnail_pack dict from already-loaded BA 32.76 JSON."""
    base = _empty_pack("no_outputs")
    rp = result_path.resolve()
    base["thumbnail_pack_path"] = str(rp.parent)
    base["thumbnail_pack_result_path"] = str(rp)
    base["thumbnail_batch_overlay_version"] = str(raw.get("thumbnail_batch_overlay_version") or "")

    outs = raw.get("outputs")
    rows: List[Dict[str, Any]] = []
    if isinstance(outs, list):
        for item in outs:
            if isinstance(item, dict):
                rows.append(_normalize_variant(item))

    base["thumbnail_variants"] = rows
    base["thumbnail_generated_count"] = len(rows)
    if rows:
        base["thumbnail_top_score"] = max(int(x["score"]) for x in rows)
    else:
        try:
            base["thumbnail_generated_count"] = int(raw.get("generated_count") or 0)
        except (TypeError, ValueError):
            base["thumbnail_generated_count"] = 0

    rec = raw.get("recommended_thumbnail")
    if isinstance(rec, dict):
        nv = _normalize_variant(rec)
        base["thumbnail_recommended_path"] = nv["output_path"]
        base["thumbnail_recommended_score"] = nv["score"]
        base["thumbnail_recommended_text_lines"] = list(nv["text_lines"])
        base["thumbnail_recommended_style_preset"] = str(nv["style_preset"] or "")
    else:
        base["thumbnail_recommended_path"] = ""
        base["thumbnail_recommended_score"] = None
        base["thumbnail_recommended_text_lines"] = []
        base["thumbnail_recommended_style_preset"] = ""

    ok = bool(raw.get("ok"))
    if not ok or base["thumbnail_generated_count"] <= 0:
        base["thumbnail_pack_status"] = "no_outputs"
    elif base["thumbnail_recommended_path"]:
        base["thumbnail_pack_status"] = "ready"
    else:
        base["thumbnail_pack_status"] = "partial"

    return base


def discover_thumbnail_batch_overlay_reports(output_dir: str | Path) -> List[Path]:
    root = Path(output_dir).resolve()
    if not root.is_dir():
        return []
    found = sorted({p.resolve() for p in root.rglob(_BATCH_RESULT_NAME) if p.is_file()})
    return list(found)


def pick_best_batch_overlay_report(paths: List[Path]) -> Optional[Path]:
    if not paths:
        return None
    if len(paths) == 1:
        return paths[0]

    def _score(p: Path) -> tuple:
        try:
            raw = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return (-2, 0, str(p))
        o = 1 if bool(raw.get("ok")) else 0
        try:
            n = int(raw.get("generated_count") or 0)
        except (TypeError, ValueError):
            n = 0
        return (o, n, str(p))

    return sorted(paths, key=_score, reverse=True)[0]


def load_thumbnail_pack_v1(*, output_dir: str | Path) -> Dict[str, Any]:
    """
    Load/normalize thumbnail pack from disk. Never raises; no secrets in output.
    """
    reports = discover_thumbnail_batch_overlay_reports(output_dir)
    chosen = pick_best_batch_overlay_report(reports)
    if chosen is None:
        return _empty_pack("missing_report")
    try:
        raw = json.loads(chosen.read_text(encoding="utf-8"))
    except Exception:
        return _empty_pack("load_error")
    if not isinstance(raw, dict):
        return _empty_pack("load_error")
    return normalize_thumbnail_pack_from_batch_report(raw, result_path=chosen)
