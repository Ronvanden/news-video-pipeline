"""BA 30.9 — sichere read-only Auslieferung von Fresh-Preview-Textartefakten unter ``output/``."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional, Tuple

_ALLOWED_SUFFIXES = frozenset({".md", ".json", ".txt"})
_MAX_ARTIFACT_BYTES = 1024 * 1024
_PREVIEW_SMOKE_SUMMARY_RE = re.compile(r"^preview_smoke_auto_summary_.+\.json$")
_RENDER_INPUT_BUNDLE_RE = re.compile(r"^render_input_bundle_.+\.json$")
_MOTION_TIMELINE_MANIFEST_RE = re.compile(r"^motion_timeline_manifest_.+\.json$")
_MOTION_CLIP_MANIFEST_RE = re.compile(r"^motion_clip_manifest_.+\.json$")


def fresh_preview_artifact_media_type(path: Path) -> str:
    s = path.suffix.lower()
    if s == ".json":
        return "application/json; charset=utf-8"
    if s == ".md":
        return "text/markdown; charset=utf-8"
    if s == ".txt":
        return "text/plain; charset=utf-8"
    return "text/plain; charset=utf-8"


def _safe_segment(seg: str) -> bool:
    s = (seg or "").strip()
    if not s or ".." in s or "/" in s or "\\" in s:
        return False
    return True


def resolve_fresh_preview_artifact_path(
    out_root: Path,
    requested: str,
    *,
    max_bytes: int = _MAX_ARTIFACT_BYTES,
) -> Tuple[Optional[Path], str]:
    """
    Liefert einen aufgelösten Dateipfad oder ``None`` und einen Grundcode.

    Erlaubte Zonen unter ``out_root.resolve()``:
    - gesamter Unterbaum ``fresh_topic_preview/`` (nur .md / .json / .txt)
    - ``preview_smoke_auto_summary_<run_id>.json`` direkt unter ``output/``
    - ``.preview_smoke_work/<run_id>/OPEN_PREVIEW_SMOKE.md``
    - unter ``output/`` (genau eine Pfadkomponente): ``render_input_bundle_<run_id>.json``,
      ``motion_timeline_manifest_<run_id>.json``, ``motion_clip_manifest_<run_id>.json``
    - ``.preview_smoke_work/<run_id>/local_preview/local_preview_render_result.json``

    Keine Symlinks, keine Ordner, kein Path Traversal außerhalb von ``output``.
    """
    if not isinstance(requested, str) or not requested.strip():
        return None, "empty"
    s = requested.strip()
    if "\x00" in s:
        return None, "forbidden"

    try:
        out_abs = out_root.resolve()
    except OSError:
        return None, "forbidden"

    try:
        fresh_base = (out_abs / "fresh_topic_preview").resolve()
    except OSError:
        fresh_base = out_abs / "fresh_topic_preview"

    raw = Path(s)
    try:
        cand = raw.resolve() if raw.is_absolute() else (out_abs / raw).resolve()
    except (OSError, RuntimeError):
        return None, "not_found"

    try:
        cand.relative_to(out_abs)
    except ValueError:
        return None, "forbidden"

    if cand.is_symlink():
        return None, "forbidden"
    if not cand.exists():
        return None, "not_found"
    if not cand.is_file():
        return None, "forbidden"

    suf = cand.suffix.lower()
    if suf not in _ALLOWED_SUFFIXES:
        return None, "forbidden"

    ok_zone = False
    try:
        cand.relative_to(fresh_base)
        ok_zone = True
    except ValueError:
        pass

    if not ok_zone:
        try:
            rel = cand.relative_to(out_abs)
        except ValueError:
            return None, "forbidden"
        parts = rel.parts
        if len(parts) == 1 and (
            _PREVIEW_SMOKE_SUMMARY_RE.match(parts[0])
            or _RENDER_INPUT_BUNDLE_RE.match(parts[0])
            or _MOTION_TIMELINE_MANIFEST_RE.match(parts[0])
            or _MOTION_CLIP_MANIFEST_RE.match(parts[0])
        ):
            ok_zone = True
        elif (
            len(parts) == 3
            and parts[0] == ".preview_smoke_work"
            and parts[2] == "OPEN_PREVIEW_SMOKE.md"
            and _safe_segment(parts[1])
        ):
            ok_zone = True
        elif (
            len(parts) == 4
            and parts[0] == ".preview_smoke_work"
            and _safe_segment(parts[1])
            and parts[2] == "local_preview"
            and parts[3] == "local_preview_render_result.json"
        ):
            ok_zone = True

    if not ok_zone:
        return None, "forbidden"

    try:
        sz = cand.stat().st_size
    except OSError:
        return None, "not_found"
    if sz > max_bytes:
        return None, "too_large"

    return cand, "ok"
