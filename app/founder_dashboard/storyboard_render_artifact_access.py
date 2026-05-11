"""Safe read-only access for Storyboard local render artifacts."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional, Tuple

STORYBOARD_RENDER_ALLOWED_SUFFIXES = frozenset({".mp4", ".json", ".txt", ".md"})
_MAX_STORYBOARD_RENDER_ARTIFACT_BYTES = 1024 * 1024 * 1024
_RUN_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,160}$")


def storyboard_render_artifact_media_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".mp4":
        return "video/mp4"
    if suffix == ".json":
        return "application/json; charset=utf-8"
    if suffix == ".md":
        return "text/markdown; charset=utf-8"
    return "text/plain; charset=utf-8"


def _safe_run_id(run_id: str) -> bool:
    s = (run_id or "").strip()
    if not s or ".." in s or "/" in s or "\\" in s:
        return False
    return bool(_RUN_ID_RE.fullmatch(s))


def _safe_relative_path(relative_path: str) -> bool:
    s = (relative_path or "").strip()
    if not s or "\x00" in s:
        return False
    parts = Path(s.replace("\\", "/")).parts
    return all(part not in {"", ".", ".."} and "/" not in part and "\\" not in part for part in parts)


def resolve_storyboard_render_artifact_path(
    output_root: Path,
    run_id: str,
    relative_path: str,
    *,
    max_bytes: int = _MAX_STORYBOARD_RENDER_ARTIFACT_BYTES,
) -> Tuple[Optional[Path], str]:
    """Resolve a Storyboard render artifact under output/storyboard_runs/<run_id>/."""
    if not _safe_run_id(run_id):
        return None, "forbidden"
    if not _safe_relative_path(relative_path):
        return None, "forbidden"

    try:
        base = (output_root / "storyboard_runs" / run_id).resolve()
        candidate = (base / relative_path.replace("\\", "/")).resolve()
    except (OSError, RuntimeError):
        return None, "not_found"

    try:
        candidate.relative_to(base)
    except ValueError:
        return None, "forbidden"

    if candidate.is_symlink():
        return None, "forbidden"
    if not candidate.exists():
        return None, "not_found"
    if not candidate.is_file():
        return None, "forbidden"
    if candidate.suffix.lower() not in STORYBOARD_RENDER_ALLOWED_SUFFIXES:
        return None, "forbidden"

    try:
        size = candidate.stat().st_size
    except OSError:
        return None, "not_found"
    if size > max_bytes:
        return None, "too_large"
    return candidate, "ok"
