"""Gemeinsame Hilfen für lokale Video-Pfade in Scene-/Beat-JSON (BA 26.3+)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

VIDEO_PATH_KEYS: Tuple[str, ...] = (
    "video_path",
    "local_video_path",
    "clip_path",
    "runway_clip_path",
    "asset_video_path",
)
VIDEO_SUFFIXES = {".mp4", ".mov", ".webm"}


def beat_duration_seconds(b: Dict[str, Any]) -> Optional[int]:
    for key in ("duration_seconds", "estimated_duration_seconds"):
        raw = b.get(key)
        if raw is None:
            continue
        try:
            v = int(raw)
            if v > 0:
                return v
        except (TypeError, ValueError):
            continue
    return None


def validate_local_video_file(path: Path) -> Tuple[bool, List[str]]:
    warns: List[str] = []
    try:
        if path.is_symlink():
            return False, [f"local_video_symlink_rejected:{path.name}"]
    except (OSError, ValueError):
        warns.append(f"local_video_symlink_check_failed:{path.name}")
    if not path.is_file():
        return False, [f"local_video_not_a_file:{path.name}"]
    suf = path.suffix.lower()
    if suf not in VIDEO_SUFFIXES:
        return False, [f"local_video_bad_extension:{suf or 'none'}"]
    return True, warns


def pick_local_video_from_beat(b: Dict[str, Any], pack_path: Path) -> Tuple[Optional[Path], List[str]]:
    """
    Erstes gültiges Video-Feld aus dem Beat; relative Pfade relativ zum scene_asset_pack-Ordner.
    """
    warnings: List[str] = []
    pack_parent = pack_path.parent.resolve()
    for key in VIDEO_PATH_KEYS:
        raw = b.get(key)
        if raw is None:
            continue
        s = str(raw).strip()
        if not s:
            continue
        try:
            cand = Path(s)
        except OSError:
            warnings.append(f"local_video_path_unparseable:{key}")
            continue
        if not cand.is_absolute():
            cand = (pack_parent / cand).resolve()
        else:
            cand = cand.resolve()
        ok, w = validate_local_video_file(cand)
        warnings.extend(w)
        if ok:
            return cand, warnings
        warnings.append(f"local_video_invalid:{key}")
    return None, warnings
