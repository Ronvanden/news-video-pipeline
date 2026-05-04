"""BA 22.0–22.2 — Dashboard Local Preview Panel: Scan, Status-Karten, sichere Artefakt-URLs (ohne Secrets)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote

_LOCAL_PREVIEW_DIR_PREFIX = "local_preview_"
_LOCAL_PREVIEW_RESULT_JSON_NAMES = ("local_preview_result.json", "result.json")

# BA 22.2 — nur diese Basenamen dürfen über die Dashboard-Datei-Route ausgeliefert werden
LOCAL_PREVIEW_ALLOWED_FILENAMES: frozenset[str] = frozenset(
    {
        "preview_with_subtitles.mp4",
        "preview_video.mp4",
        "clean_video.mp4",
        "local_preview_report.md",
        "OPEN_ME.md",
        "local_preview_result.json",
    }
)
_LOCAL_PREVIEW_RUN_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,220}$")

_PF_STATUSES = frozenset({"pass", "warning", "fail"})
_WARN_LEVELS = frozenset({"INFO", "CHECK", "WARNING", "BLOCKING"})
_FOUNDER_CODES = frozenset({"GO_PREVIEW", "REVIEW_REQUIRED", "BLOCK"})
_VERDICTS = frozenset({"PASS", "WARNING", "FAIL"})


def default_local_preview_out_root() -> Path:
    """Repository-``output/`` relativ zu diesem Paket (keine Env-Abhängigkeit)."""
    return Path(__file__).resolve().parents[2] / "output"


def validate_local_preview_run_id(run_id: str) -> bool:
    """Kein Pfad-Separator / keine Traversal-Muster — nur sichere Run-IDs."""
    s = (run_id or "").strip()
    if not s or ".." in s or "/" in s or "\\" in s:
        return False
    return bool(_LOCAL_PREVIEW_RUN_ID_RE.fullmatch(s))


def local_preview_file_media_type(filename: str) -> str:
    if filename.endswith(".mp4"):
        return "video/mp4"
    if filename.endswith(".md"):
        return "text/markdown; charset=utf-8"
    if filename.endswith(".json"):
        return "application/json; charset=utf-8"
    return "application/octet-stream"


def build_local_preview_file_url(run_id: str, filename: str) -> str:
    """Relativer URL-Pfad für ``GET /founder/dashboard/local-preview/file/...``."""
    return f"/founder/dashboard/local-preview/file/{quote(run_id, safe='')}/{quote(filename, safe='')}"


def _safe_artifact_file(run_dir: Path, name: str) -> bool:
    p = run_dir / name
    try:
        if not p.exists():
            return False
        if p.is_symlink():
            return False
        return p.is_file()
    except OSError:
        return False


def local_preview_safe_resolve_file(out_root: Path, run_id: str, filename: str) -> Optional[Path]:
    """
    Liefert einen aufgelösten Dateipfad nur unter ``out_root/local_preview_<run_id>/``,
    ohne Symlinks auf Dateiebene, mit Whitelist für ``filename``.
    """
    if not validate_local_preview_run_id(run_id):
        return None
    if filename not in LOCAL_PREVIEW_ALLOWED_FILENAMES:
        return None
    try:
        root = out_root.resolve()
    except OSError:
        return None
    run_dir = root / f"{_LOCAL_PREVIEW_DIR_PREFIX}{run_id}"
    try:
        run_res = run_dir.resolve()
    except OSError:
        return None
    if run_res.is_symlink() or not run_res.is_dir():
        return None
    try:
        if run_res.parent.resolve() != root:
            return None
    except OSError:
        return None
    candidate = run_res / filename
    try:
        if candidate.is_symlink():
            return None
        resolved = candidate.resolve()
        resolved.relative_to(run_res)
    except (OSError, ValueError):
        return None
    if not resolved.is_file():
        return None
    return resolved


def build_file_urls_for_run(run_dir: Path, run_id: str) -> Dict[str, str]:
    """BA 22.2 — Dashboard-URLs nur wenn Datei physisch (ohne Symlink) vorhanden."""
    empty = {"preview_url": "", "report_url": "", "open_me_url": "", "result_json_url": ""}
    if not validate_local_preview_run_id(run_id):
        return dict(empty)
    preview_url = ""
    for cand in ("preview_with_subtitles.mp4", "preview_video.mp4", "clean_video.mp4"):
        if _safe_artifact_file(run_dir, cand):
            preview_url = build_local_preview_file_url(run_id, cand)
            break
    report_url = (
        build_local_preview_file_url(run_id, "local_preview_report.md")
        if _safe_artifact_file(run_dir, "local_preview_report.md")
        else ""
    )
    open_me_url = (
        build_local_preview_file_url(run_id, "OPEN_ME.md") if _safe_artifact_file(run_dir, "OPEN_ME.md") else ""
    )
    result_json_url = (
        build_local_preview_file_url(run_id, "local_preview_result.json")
        if _safe_artifact_file(run_dir, "local_preview_result.json")
        else ""
    )
    return {
        "preview_url": preview_url,
        "report_url": report_url,
        "open_me_url": open_me_url,
        "result_json_url": result_json_url,
    }


def _safe_is_dir(p: Path) -> bool:
    try:
        return p.is_dir()
    except OSError:
        return False


def _artifact_flags(run_dir: Path) -> Dict[str, bool]:
    def _f(rel: str) -> bool:
        try:
            p = (run_dir / rel).resolve()
            return p.is_file()
        except OSError:
            return False

    return {
        "open_me": _f("OPEN_ME.md"),
        "founder_report": _f("local_preview_report.md"),
        "preview_with_subtitles": _f("preview_with_subtitles.mp4"),
    }


def _read_json_file(path: Path) -> Optional[Dict[str, Any]]:
    try:
        if not path.is_file():
            return None
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
        return data if isinstance(data, dict) else None
    except (OSError, ValueError, json.JSONDecodeError):
        return None


def load_local_preview_saved_result(run_dir: Path) -> Optional[Dict[str, Any]]:
    """Liest ``local_preview_result.json`` oder ``result.json`` aus dem Run-Ordner."""
    for name in _LOCAL_PREVIEW_RESULT_JSON_NAMES:
        data = _read_json_file(run_dir / name)
        if data:
            return data
    return None


def _norm_pf(v: Any) -> str:
    t = str(v or "").strip().lower()
    if t in _PF_STATUSES:
        return t.upper()
    return "UNKNOWN"


def _norm_verdict(v: Any) -> str:
    t = str(v or "").strip().upper()
    if t in _VERDICTS:
        return t
    return "UNKNOWN"


def _norm_warn_level(v: Any) -> str:
    t = str(v or "").strip().upper()
    if t in _WARN_LEVELS:
        return t
    t2 = str(v or "").strip().lower()
    if t2 == "info":
        return "INFO"
    if t2 == "check":
        return "CHECK"
    if t2 == "warning":
        return "WARNING"
    if t2 == "blocking":
        return "BLOCKING"
    return "UNKNOWN"


def _norm_founder(v: Any) -> str:
    t = str(v or "").strip().upper()
    if t in _FOUNDER_CODES:
        return t
    return "UNKNOWN"


def build_status_cards_from_saved_result(data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Status-Karten aus Snapshot (BA 22.1) oder kompatiblem Pipeline-JSON-Subset.

    Fehlt die Datei oder ist sie unlesbar → UNKNOWN-Felder mit Hinweis.
    """
    if not isinstance(data, dict) or not data:
        return {
            "verdict": "UNKNOWN",
            "quality": "UNKNOWN",
            "subtitle_quality": "UNKNOWN",
            "sync_guard": "UNKNOWN",
            "warning_level": "UNKNOWN",
            "founder_decision": "UNKNOWN",
            "top_issue": "contract_file_missing",
            "next_step": "Neuen Local-Preview-Lauf ausführen (siehe docs/runbooks/local_preview_runbook.md).",
            "contract_present": False,
        }

    qc = data.get("quality_checklist") if isinstance(data.get("quality_checklist"), dict) else {}
    sq = data.get("subtitle_quality_check") if isinstance(data.get("subtitle_quality_check"), dict) else {}
    sg = data.get("sync_guard") if isinstance(data.get("sync_guard"), dict) else {}
    wc = data.get("warning_classification") if isinstance(data.get("warning_classification"), dict) else {}
    fq = data.get("founder_quality_decision") if isinstance(data.get("founder_quality_decision"), dict) else {}

    verdict = _norm_verdict(data.get("verdict"))
    quality = _norm_pf(qc.get("status"))
    subtitle_quality = _norm_pf(sq.get("status"))
    sync_guard = _norm_pf(sg.get("status"))
    warning_level = _norm_warn_level(wc.get("highest"))
    founder_decision = _norm_founder(fq.get("decision_code"))

    top_issue = str(fq.get("top_issue") or "").strip()
    if not top_issue and isinstance(wc.get("items"), list) and wc["items"]:
        first = wc["items"][0]
        if isinstance(first, dict):
            top_issue = str(first.get("code") or "").strip()
    next_step = str(fq.get("next_step") or "").strip()
    if not next_step:
        next_step = "Siehe OPEN_ME.md oder Runbook."

    return {
        "verdict": verdict,
        "quality": quality,
        "subtitle_quality": subtitle_quality,
        "sync_guard": sync_guard,
        "warning_level": warning_level,
        "founder_decision": founder_decision,
        "top_issue": top_issue or "—",
        "next_step": next_step,
        "contract_present": True,
    }


def _scan_run_dirs(out_root: Path) -> Tuple[List[Tuple[float, str, Path]], List[str]]:
    """Direkte Kinder ``local_preview_*``, keine Symlinks; absteigend nach mtime."""
    warnings: List[str] = []
    rows: List[Tuple[float, str, Path]] = []
    try:
        root = out_root.resolve()
    except OSError:
        warnings.append("local_preview_out_root_resolve_failed")
        return [], warnings

    if not _safe_is_dir(root):
        return [], warnings

    try:
        entries = list(root.iterdir())
    except OSError:
        warnings.append("local_preview_out_root_list_failed")
        return [], warnings

    for entry in entries:
        if entry.is_symlink():
            warnings.append(f"local_preview_scan_skipped_symlink:{entry.name}")
            continue
        if not entry.is_dir():
            continue
        name = entry.name
        if not name.startswith(_LOCAL_PREVIEW_DIR_PREFIX):
            continue
        try:
            mt = float(entry.stat().st_mtime)
        except OSError:
            warnings.append(f"local_preview_scan_skipped_stat:{name}")
            continue
        rows.append((mt, name, entry))

    rows.sort(key=lambda t: (-t[0], t[1]))
    return rows, warnings


def build_run_rows_payload(rows: List[Tuple[float, str, Path]], *, limit: int = 20) -> List[Dict[str, Any]]:
    """Wandelt sortierte Scan-Zeilen in Dashboard-Run-Objekte um."""
    cap = max(1, min(int(limit), 100))
    out: List[Dict[str, Any]] = []
    for _mt, name, path in rows[:cap]:
        rid = name[len(_LOCAL_PREVIEW_DIR_PREFIX) :] if name.startswith(_LOCAL_PREVIEW_DIR_PREFIX) else name
        try:
            p_res = str(path.resolve())
        except OSError:
            p_res = str(path)
        try:
            mtime = float(path.stat().st_mtime)
        except OSError:
            mtime = 0.0
        arts = _artifact_flags(path)
        saved = load_local_preview_saved_result(path)
        file_urls = build_file_urls_for_run(path, rid)
        row: Dict[str, Any] = {
            "dir_name": name,
            "run_id": rid,
            "path": p_res,
            "mtime_epoch": mtime,
            "artifacts": arts,
            "status_cards": build_status_cards_from_saved_result(saved),
            "file_urls": file_urls,
        }
        out.append(row)
    return out


def scan_local_preview_runs(out_root: Path, *, limit: int = 20) -> List[Dict[str, Any]]:
    """Kompakte Run-Metadaten für das Dashboard (keine Dateiinhalte)."""
    rows, _w = _scan_run_dirs(out_root)
    return build_run_rows_payload(rows, limit=limit)


def build_local_preview_panel_payload(
    *,
    out_root: Optional[Path] = None,
    runs_limit: int = 20,
) -> Dict[str, Any]:
    """
    JSON für ``GET /founder/dashboard/local-preview/panel``.

    ``result_contract``-Referenz entspricht BA 21.7 (id/schema_version — bei Änderung dort angleichen).
    """
    root = Path(out_root) if out_root is not None else default_local_preview_out_root()
    warnings: List[str] = []
    readable = False
    try:
        r = root.resolve()
        readable = _safe_is_dir(r)
    except OSError:
        warnings.append("local_preview_out_root_resolve_failed")
        r = root

    runs: List[Dict[str, Any]] = []
    if not readable:
        warnings.append("local_preview_out_root_missing_or_not_dir")
    else:
        rows, scan_extra = _scan_run_dirs(r)
        warnings.extend(scan_extra)
        runs = build_run_rows_payload(rows, limit=runs_limit)

    latest_status_cards: Optional[Dict[str, Any]] = None
    latest_file_urls: Dict[str, str] = {
        "preview_url": "",
        "report_url": "",
        "open_me_url": "",
        "result_json_url": "",
    }
    if runs:
        latest_status_cards = dict(runs[0].get("status_cards") or {})
        latest_file_urls = dict(runs[0].get("file_urls") or latest_file_urls)

    actions: List[Dict[str, Any]] = [
        {
            "id": "cli_mini_fixture",
            "label_de": "Mini E2E (Smoke) im Repo-Root",
            "kind": "shell",
            "example": "python scripts/run_local_preview_mini_fixture.py",
        },
        {
            "id": "cli_cleanup_dry_run",
            "label_de": "Alte Preview-Ordner listen (Dry-Run)",
            "kind": "shell",
            "example": "python scripts/cleanup_local_previews.py --out-root output",
        },
        {
            "id": "doc_runbook",
            "label_de": "Runbook (Start, Prüfen, Cleanup)",
            "kind": "doc",
            "path": "docs/runbooks/local_preview_runbook.md",
        },
    ]

    return {
        "panel_version": "ba22_local_preview_panel_v3",
        "result_contract": {"id": "local_preview_result_v1", "schema_version": 1},
        "out_root": str(r) if readable else str(root),
        "out_root_exists": readable,
        "runs": runs,
        "latest_status_cards": latest_status_cards,
        "latest_file_urls": latest_file_urls,
        "actions": actions,
        "warnings": warnings,
    }
