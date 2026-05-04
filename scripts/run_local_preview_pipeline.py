"""BA 20.9 / BA 20.10 — Lokale Preview-Pipeline + Founder-Markdown-Report."""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_BUILD_SCRIPT = ROOT / "scripts" / "build_subtitle_file.py"
_RENDER_SCRIPT = ROOT / "scripts" / "render_final_story_video.py"
_BURN_SCRIPT = ROOT / "scripts" / "burn_in_subtitles_preview.py"


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _s(v: Any) -> str:
    if v is None:
        return ""
    return str(v).strip()


def _list_str(x: Any) -> List[str]:
    if x is None:
        return []
    if isinstance(x, list):
        return [str(i) for i in x if i is not None and str(i).strip() != ""]
    if isinstance(x, (str, int, float, bool)):
        t = str(x).strip()
        return [t] if t else []
    return [str(x)]


def build_ffmpeg_setup_hint(missing_tools: List[str]) -> str:
    """BA 21.0d — Kurzer Windows-/PowerShell-Hinweis zur FFmpeg-Installation."""
    lines = [
        "winget install Gyan.FFmpeg",
        "",
        "Danach PowerShell neu öffnen und prüfen:",
        "ffmpeg -version",
        "ffprobe -version",
    ]
    hint = "\n".join(lines)
    if missing_tools:
        hint += "\n\nFalls winget nicht verfügbar ist: FFmpeg manuell installieren und PATH setzen."
    return hint


def check_local_ffmpeg_tools(
    *,
    _which: Optional[Callable[[str], Optional[str]]] = None,
    _run: Optional[Callable[..., Any]] = None,
    _timeout_sec: float = 5.0,
) -> Dict[str, Any]:
    """
    BA 21.0d — Lokaler Operator-Guard: ffmpeg/ffprobe im PATH und `-version` erreichbar.

    `_which` / `_run` nur für Tests injizieren (z. B. Mock von shutil.which / subprocess.run).
    """
    which_fn = _which or shutil.which
    run_fn = _run or subprocess.run
    warnings: List[str] = []
    missing_tools: List[str] = []

    def _probe(name: str) -> Dict[str, Any]:
        path = which_fn(name) or ""
        if not path:
            missing_tools.append(name)
            return {"available": False, "version": "", "path": ""}
        cmd = [path, "-version"]
        try:
            proc = run_fn(
                cmd,
                capture_output=True,
                text=True,
                timeout=_timeout_sec,
            )
        except subprocess.TimeoutExpired:
            warnings.append(f"{name}_version_check_timeout")
            return {"available": False, "version": "", "path": str(path)}
        except OSError:
            warnings.append(f"{name}_version_check_os_error")
            return {"available": False, "version": "", "path": str(path)}
        if getattr(proc, "returncode", 1) != 0:
            warnings.append(f"{name}_version_check_failed")
            return {"available": False, "version": "", "path": str(path)}
        out = (getattr(proc, "stdout", None) or "") or ""
        first = out.strip().splitlines()[0] if out.strip() else ""
        ver = (first[:200]).strip() if first else ""
        if not ver:
            warnings.append(f"{name}_version_parse_empty")
            return {"available": False, "version": "", "path": str(path)}
        return {"available": True, "version": ver, "path": str(path)}

    ffmpeg_i = _probe("ffmpeg")
    ffprobe_i = _probe("ffprobe")
    ok = bool(ffmpeg_i.get("available")) and bool(ffprobe_i.get("available"))
    setup_hint = "" if ok else build_ffmpeg_setup_hint(missing_tools)

    return {
        "ok": ok,
        "ffmpeg": ffmpeg_i,
        "ffprobe": ffprobe_i,
        "missing_tools": list(missing_tools),
        "warnings": warnings,
        "setup_hint": setup_hint,
    }


def _iter_steps(steps: Any) -> Iterator[Tuple[str, Any]]:
    if steps is None:
        return
    if isinstance(steps, dict):
        for k, v in steps.items():
            yield str(k), v
    elif isinstance(steps, list):
        for i, v in enumerate(steps):
            yield f"step_{i}", v


def _classify_step(name: str, step: Any) -> Tuple[str, str, List[str]]:
    """Gibt (PASS|WARNING|FAIL|SKIPPED, output_kurz, step_warnings) zurück."""
    if step is None:
        return ("SKIPPED", "nicht verfügbar", [])
    if not isinstance(step, dict):
        return ("WARNING", _s(step)[:200] or "nicht verfügbar", [])
    sw = _list_str(step.get("warnings"))
    n = (name or "").lower()

    if "build" in n:
        ok_b = bool(step.get("ok"))
        out = _s(step.get("subtitle_manifest_path")) or _s(step.get("output_dir")) or "nicht verfügbar"
        if not ok_b:
            return ("FAIL", out, sw)
        return ("PASS" if not sw else "WARNING", out, sw)

    if "render" in n:
        if step.get("video_created") is True:
            out = _s(step.get("output_path")) or "Video erstellt (Pfad unbekannt)"
            return ("PASS" if not sw else "WARNING", out, sw)
        if step.get("video_created") is False:
            return ("FAIL", _s(step.get("output_path")) or "kein Output", sw)
        return ("WARNING", "video_created fehlt oder unklar", sw)

    if "burn" in n:
        if step.get("skipped") is True:
            return ("SKIPPED", _s(step.get("output_video_path")), sw)
        if step.get("ok") is False:
            return ("FAIL", _s(step.get("output_video_path")), sw)
        if step.get("ok") is True:
            out = _s(step.get("output_video_path")) or "nicht verfügbar"
            return ("PASS" if not sw else "WARNING", out, sw)
        return ("WARNING", "ok fehlt oder unklar", sw)

    if "video_created" in step:
        if step.get("video_created") is True:
            out = _s(step.get("output_path")) or "Video erstellt"
            return ("PASS" if not sw else "WARNING", out, sw)
        return ("FAIL", _s(step.get("output_path")) or "kein Output", sw)

    if step.get("skipped") is True:
        return ("SKIPPED", _s(step.get("output_video_path")), sw)

    if "ok" in step:
        ok_b = bool(step.get("ok"))
        out = (
            _s(step.get("subtitle_manifest_path"))
            or _s(step.get("output_video_path"))
            or _s(step.get("output_dir"))
            or "nicht verfügbar"
        )
        if not ok_b:
            return ("FAIL", out, sw)
        return ("PASS" if not sw else "WARNING", out, sw)

    return ("WARNING", "Step ohne erkanntes Schema", sw)


def _collect_local_preview_warnings(result: Any) -> List[str]:
    """Top-Level- und Step-Warnungen zusammenführen (Reihenfolge, ohne Duplikate)."""
    if not isinstance(result, dict):
        return []
    seen: set[str] = set()
    out: List[str] = []
    for w in _list_str(result.get("warnings")):
        if w not in seen:
            seen.add(w)
            out.append(w)
    for _name, step in _iter_steps(result.get("steps")):
        if isinstance(step, dict):
            for w in _list_str(step.get("warnings")):
                if w not in seen:
                    seen.add(w)
                    out.append(w)
    return out


# BA 21.0e — diese Codes dürfen ein lokales Preview-Ergebnis nicht als FAIL werten (Operator-Idempotenz).
_LOCAL_PREVIEW_NON_BLOCKING_BLOCKING_REASONS = frozenset(
    {
        "preview_with_subtitles_already_exists",
    }
)


def sanitize_local_preview_blocking_reasons(blocking: Any) -> List[str]:
    """Filtert bekannte nicht-blockierende blocking_reasons für Verdict und Reports."""
    return [b for b in _list_str(blocking) if b not in _LOCAL_PREVIEW_NON_BLOCKING_BLOCKING_REASONS]


def compute_local_preview_verdict(result: Any) -> str:
    """PASS | WARNING | FAIL — tolerant bei fehlenden Keys."""
    if not isinstance(result, dict):
        return "FAIL"
    ok = bool(result.get("ok"))
    blocking = sanitize_local_preview_blocking_reasons(result.get("blocking_reasons"))
    if not ok or blocking:
        return "FAIL"
    top_w = _list_str(result.get("warnings"))
    step_issue = False
    for _name, step in _iter_steps(result.get("steps")):
        status, _out, sw = _classify_step(_name, step)
        if status in ("FAIL", "SKIPPED", "WARNING"):
            step_issue = True
        if sw:
            step_issue = True
    if top_w or step_issue:
        return "WARNING"
    return "PASS"


def local_preview_next_step_for_verdict(verdict: str) -> str:
    """Kurzer nächster Schritt für Founder/Operator (PASS/WARNING/FAIL)."""
    v = (verdict or "FAIL").strip().upper()
    if v == "PASS":
        return "Öffne die Preview-Datei und prüfe Bild, Ton, Untertitel-Timing."
    if v == "WARNING":
        return "Öffne die Preview, prüfe die Warnungen und entscheide, ob ein Repair nötig ist."
    return "Behebe zuerst die Blocking Reasons und starte den lokalen Preview-Lauf erneut."


# Gemeinsame Pfad-Logik (BA 20.11 Smoke, BA 20.12 OPEN_ME, Founder Report; BA 21.0c Reihenfolge)
_PREVIEW_VIDEO_PATH_KEYS = (
    "preview_video",
    "preview_with_subtitles",
    "subtitled_preview",
    "burned_in_preview",
    "final_preview",
)


def resolve_local_preview_video_path(paths: Any) -> str:
    """Ersten nicht-leeren Vorschau-Pfad aus paths, sonst clean_video, sonst leer."""
    if not isinstance(paths, dict):
        return ""
    for k in _PREVIEW_VIDEO_PATH_KEYS:
        p = _s(paths.get(k))
        if p:
            return p
    return _s(paths.get("clean_video"))


def colocate_local_preview_video(result: dict) -> dict:
    """
    BA 21.0c — Kopiert preview_with_subtitles.mp4 ins pipeline_dir-Paket (ohne Quelle zu löschen).

    Setzt paths[\"preview_with_subtitles\"] und paths[\"preview_video\"] bevorzugt auf die
    zentrale Kopie; paths[\"burnin_preview_source\"] hält optional den ursprünglichen Burn-in-Pfad.
    Fehler oder fehlende Quelle: Warnung, kein Crash; Quelle == Ziel: kein Copy.
    """
    if not isinstance(result, dict):
        return {}
    out = dict(result)
    paths = dict(out.get("paths") or {})
    out["paths"] = paths

    pd_str = _s(out.get("pipeline_dir"))
    if not pd_str:
        return out

    try:
        pipeline_dir = Path(pd_str).resolve()
    except OSError:
        w = _list_str(out.get("warnings"))
        w.append("preview_colocation_pipeline_dir_invalid")
        out["warnings"] = w
        return out

    src_str = _s(paths.get("preview_with_subtitles"))
    if not src_str and isinstance(out.get("steps"), dict):
        st = out["steps"].get("burnin_preview")
        if isinstance(st, dict):
            src_str = _s(st.get("output_video_path"))

    if not src_str:
        return out

    try:
        src = Path(src_str).resolve()
    except OSError:
        w = _list_str(out.get("warnings"))
        w.append("preview_colocation_source_invalid")
        out["warnings"] = w
        return out

    dest = (pipeline_dir / "preview_with_subtitles.mp4").resolve()

    if not src.is_file():
        w = _list_str(out.get("warnings"))
        w.append("preview_colocation_source_missing")
        out["warnings"] = w
        return out

    if src != dest:
        paths.setdefault("burnin_preview_source", str(src))

    if src == dest:
        paths["preview_with_subtitles"] = str(dest)
        paths["preview_video"] = str(dest)
        return out

    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
    except OSError:
        w = _list_str(out.get("warnings"))
        w.append("preview_colocation_copy_failed")
        out["warnings"] = w
        return out

    paths["burnin_preview_source"] = paths.get("burnin_preview_source") or str(src)
    paths["preview_with_subtitles"] = str(dest)
    paths["preview_video"] = str(dest)
    return out


def resolve_local_preview_report_path(result: Any) -> str:
    """Founder-Report-Pfad: report_path oder paths[\"founder_report\"]."""
    if not isinstance(result, dict):
        return ""
    rp = _s(result.get("report_path"))
    if rp:
        return rp
    paths = result.get("paths")
    if isinstance(paths, dict):
        return _s(paths.get("founder_report"))
    return ""


def resolve_local_preview_open_me_path(result: Any) -> str:
    """OPEN_ME.md-Pfad: open_me_path oder paths[\"open_me\"]."""
    if not isinstance(result, dict):
        return ""
    o = _s(result.get("open_me_path"))
    if o:
        return o
    paths = result.get("paths")
    if isinstance(paths, dict):
        return _s(paths.get("open_me"))
    return ""


def _safe_operator_path(p: Any) -> Optional[Path]:
    t = _s(p)
    if not t:
        return None
    try:
        return Path(t)
    except (TypeError, ValueError):
        return None


def _quality_checklist_status_to_verdict(st: str) -> str:
    return {"pass": "PASS", "warning": "WARNING", "fail": "FAIL"}.get((st or "fail").lower().strip(), "FAIL")


def build_local_preview_quality_checklist(result: dict) -> Dict[str, Any]:
    """BA 21.1 — Lokale Artefakt-/Bedienbarkeits-Checkliste (keine Video-Pixel-Analyse)."""
    r = result if isinstance(result, dict) else {}
    paths = r.get("paths")
    if not isinstance(paths, dict):
        paths = {}
    items: List[Dict[str, Any]] = []
    agg_warnings = _collect_local_preview_warnings(r)
    blocking_eff = sanitize_local_preview_blocking_reasons(r.get("blocking_reasons"))

    preview_path = resolve_local_preview_video_path(paths)
    pp = _safe_operator_path(preview_path)
    preview_exists = pp is not None and pp.is_file()
    size_b: Optional[int] = None
    stat_err = False
    if preview_exists and pp is not None:
        try:
            size_b = int(pp.stat().st_size)
        except OSError:
            stat_err = True
            size_b = None

    if preview_exists:
        items.append(
            {
                "id": "preview_video_exists",
                "label": "Preview video exists",
                "status": "pass",
                "detail": "file present",
                "path": preview_path,
            }
        )
    else:
        items.append(
            {
                "id": "preview_video_exists",
                "label": "Preview video exists",
                "status": "fail",
                "detail": "missing or not a file",
                "path": preview_path,
            }
        )

    if not preview_exists:
        items.append(
            {
                "id": "preview_video_non_empty",
                "label": "Preview video non-empty",
                "status": "fail",
                "detail": "no preview file",
                "path": preview_path,
            }
        )
    elif stat_err:
        items.append(
            {
                "id": "preview_video_non_empty",
                "label": "Preview video non-empty",
                "status": "warning",
                "detail": "could not stat file",
                "path": preview_path,
            }
        )
    elif (size_b or 0) == 0:
        items.append(
            {
                "id": "preview_video_non_empty",
                "label": "Preview video non-empty",
                "status": "fail",
                "detail": "file is 0 bytes",
                "path": preview_path,
            }
        )
    else:
        items.append(
            {
                "id": "preview_video_non_empty",
                "label": "Preview video non-empty",
                "status": "pass",
                "detail": f"{size_b} bytes",
                "path": preview_path,
            }
        )

    frp = resolve_local_preview_report_path(r) or _s(paths.get("founder_report"))
    fr = _safe_operator_path(frp)
    if fr is not None and fr.is_file():
        items.append(
            {
                "id": "founder_report_exists",
                "label": "Founder report exists",
                "status": "pass",
                "detail": "",
                "path": frp,
            }
        )
    else:
        items.append(
            {
                "id": "founder_report_exists",
                "label": "Founder report exists",
                "status": "fail",
                "detail": "missing or not a file",
                "path": frp,
            }
        )

    omp = resolve_local_preview_open_me_path(r) or _s(paths.get("open_me"))
    om = _safe_operator_path(omp)
    if om is not None and om.is_file():
        items.append(
            {
                "id": "open_me_exists",
                "label": "OPEN_ME exists",
                "status": "pass",
                "detail": "",
                "path": omp,
            }
        )
    else:
        items.append(
            {
                "id": "open_me_exists",
                "label": "OPEN_ME exists",
                "status": "fail",
                "detail": "missing or not a file",
                "path": omp,
            }
        )

    if not blocking_eff:
        items.append(
            {
                "id": "blocking_reasons_clear",
                "label": "Blocking reasons clear",
                "status": "pass",
                "detail": "no blocking reasons after sanitize",
                "path": "",
            }
        )
    else:
        tail = ", ".join(blocking_eff[:5])
        if len(blocking_eff) > 5:
            tail += "…"
        items.append(
            {
                "id": "blocking_reasons_clear",
                "label": "Blocking reasons clear",
                "status": "fail",
                "detail": tail,
                "path": "",
            }
        )

    if agg_warnings:
        items.append(
            {
                "id": "warnings_present",
                "label": "Warnings present",
                "status": "warning",
                "detail": f"{len(agg_warnings)} warning(s)",
                "path": "",
            }
        )
    else:
        items.append(
            {
                "id": "warnings_present",
                "label": "Warnings present",
                "status": "pass",
                "detail": "no warnings",
                "path": "",
            }
        )

    has_fail = any(str(it.get("status", "")).lower() == "fail" for it in items)
    has_warn = any(str(it.get("status", "")).lower() == "warning" for it in items)
    if has_fail:
        overall = "fail"
    elif has_warn:
        overall = "warning"
    else:
        overall = "pass"

    nxt = local_preview_next_step_for_verdict(_quality_checklist_status_to_verdict(overall))

    return {
        "status": overall,
        "items": items,
        "warnings": list(agg_warnings),
        "blocking_reasons": list(blocking_eff),
        "next_step": nxt,
    }


def build_local_preview_open_me(result: dict) -> str:
    """BA 20.12 — Kurzer Einstieg für den Preview-Ordner (OPEN_ME.md)."""
    verdict = compute_local_preview_verdict(result if isinstance(result, dict) else {})
    r = result if isinstance(result, dict) else {}
    paths = r.get("paths")
    if not isinstance(paths, dict):
        paths = {}

    preview_v = resolve_local_preview_video_path(paths) or "nicht verfügbar"
    report_p = resolve_local_preview_report_path(r) or "nicht verfügbar"
    clean_v = _s(paths.get("clean_video")) or "nicht verfügbar"
    sub_f = _s(paths.get("subtitles_srt_path")) or _s(paths.get("subtitle_manifest")) or "nicht verfügbar"
    pipe_d = _s(r.get("pipeline_dir")) or "nicht verfügbar"

    tw = _list_str(r.get("warnings"))
    br = sanitize_local_preview_blocking_reasons(r.get("blocking_reasons"))

    lines: List[str] = [
        "# Local Preview Package",
        "",
        "## Status",
        f"Verdict: **{verdict}**",
        "",
        "## Open First",
        f"Preview Video: `{preview_v}`",
        f"Founder Report: `{report_p}`",
        "",
        "## What This Is",
        "Dieser Ordner enthält einen lokalen Preview-Lauf der Video-Pipeline.",
        "",
        "## Key Artefacts",
        f"- Clean Video: `{clean_v}`",
        f"- Preview Video: `{preview_v}`",
        f"- Subtitle File: `{sub_f}`",
        f"- Founder Report: `{report_p}`",
        f"- Pipeline Folder: `{pipe_d}`",
        "",
        "## Warnings",
    ]
    if tw:
        for w in tw:
            lines.append(f"- {w}")
    else:
        lines.append("- Keine")

    lines.extend(["", "## Blocking Reasons"])
    if br:
        for b in br:
            lines.append(f"- {b}")
    else:
        lines.append("- Keine")

    qc = r.get("quality_checklist")
    if isinstance(qc, dict) and qc.get("items"):
        lines.extend(["", "## Quality Checklist"])
        for it in qc.get("items") or []:
            if not isinstance(it, dict):
                continue
            tag = str(it.get("status", "fail")).upper()
            lab = _s(it.get("label")) or _s(it.get("id"))
            lines.append(f"- [{tag}] {lab}")
        lines.append("")

    lines.extend(["", "## Next Step", local_preview_next_step_for_verdict(verdict), ""])
    return "\n".join(lines)


def write_local_preview_open_me(result: dict) -> dict:
    """
    Setzt open_me_markdown; schreibt optional OPEN_ME.md unter pipeline_dir.
    Bei Fehler: open_me_build_failed / open_me_write_failed, kein Crash.
    """
    if not isinstance(result, dict):
        result = {}
    out = dict(result)
    paths = dict(out.get("paths") or {})
    out["paths"] = paths
    try:
        md = build_local_preview_open_me(out)
    except Exception:
        md = (
            "# Local Preview Package\n\n"
            "## Status\nVerdict: **FAIL**\n\n"
            "(OPEN_ME konnte nicht aufgebaut werden — Rohresultat prüfen.)\n"
        )
        w = _list_str(out.get("warnings"))
        w.append("open_me_build_failed")
        out["warnings"] = w
    out["open_me_markdown"] = md

    pd = _s(out.get("pipeline_dir"))
    if not pd:
        return out

    try:
        op = Path(pd) / "OPEN_ME.md"
        op.parent.mkdir(parents=True, exist_ok=True)
        op.write_text(md, encoding="utf-8")
        omp = str(op.resolve())
        out["open_me_path"] = omp
        paths["open_me"] = omp
    except OSError:
        w = _list_str(out.get("warnings"))
        w.append("open_me_write_failed")
        out["warnings"] = w
    return out


def build_local_preview_founder_report(result: dict) -> str:
    """BA 20.10 — Markdown-Report für Founder/Operator aus Aggregat-Ergebnis der Preview-Pipeline."""
    verdict = compute_local_preview_verdict(result if isinstance(result, dict) else {})
    r = result if isinstance(result, dict) else {}
    paths = r.get("paths")
    if not isinstance(paths, dict):
        paths = {}
    preview_path = resolve_local_preview_video_path(paths)
    clean_path = _s(paths.get("clean_video"))
    open_path = preview_path or clean_path or "nicht verfügbar"
    preview_yes = bool(preview_path)
    run_id = _s(r.get("run_id")) or "nicht verfügbar"
    pipeline_dir = _s(r.get("pipeline_dir")) or "nicht verfügbar"

    lines: List[str] = [
        "# Local Preview Founder Report",
        "",
        "## Verdict",
        f"Status: **{verdict}**",
        "",
        "## Preview",
        f"Preview erzeugt: **{'ja' if preview_yes else 'nein'}**",
        f"Datei öffnen: `{open_path}`",
        "",
        "## Run",
        f"Run ID: `{run_id}`",
        f"Pipeline Ordner: `{pipeline_dir}`",
        "",
        "## Steps",
    ]
    steps_obj = r.get("steps")
    if steps_obj is None or (isinstance(steps_obj, dict) and not steps_obj) or (isinstance(steps_obj, list) and not steps_obj):
        lines.append("- *(keine Step-Daten)*")
    else:
        for step_name, step in _iter_steps(steps_obj):
            status, out, sw = _classify_step(step_name, step)
            lines.append(f"- **{step_name}**: {status}")
            lines.append(f"  - output: `{out or 'nicht verfügbar'}`")
            if sw:
                lines.append(f"  - warning: {', '.join(sw)}")
            else:
                lines.append("  - warning: *(keine)*")

    lines.extend(["", "## Warnings"])
    tw = _list_str(r.get("warnings"))
    if tw:
        for w in tw:
            lines.append(f"- {w}")
    else:
        lines.append("- *(keine)*")

    lines.extend(["", "## Blocking Reasons"])
    br = sanitize_local_preview_blocking_reasons(r.get("blocking_reasons"))
    if br:
        for b in br:
            lines.append(f"- {b}")
    else:
        lines.append("- *(keine)*")

    qc = r.get("quality_checklist")
    if isinstance(qc, dict) and qc.get("items"):
        lines.extend(["", "## Quality Checklist"])
        for it in qc.get("items") or []:
            if not isinstance(it, dict):
                continue
            tag = str(it.get("status", "fail")).upper()
            lab = _s(it.get("label")) or _s(it.get("id"))
            det = _s(it.get("detail"))
            pth = _s(it.get("path"))
            mid = f" — {det}" if det else ""
            if pth:
                mid = f"{mid} (`{pth}`)" if mid else f" (`{pth}`)"
            lines.append(f"- [{tag}] {lab}{mid}")
        lines.append("")

    lines.extend(["", "## Next Step"])
    lines.append(local_preview_next_step_for_verdict(verdict))
    lines.append("")
    return "\n".join(lines)


def write_local_preview_founder_report(result: dict) -> dict:
    """
    Ergänzt result um report_markdown; schreibt optional local_preview_report.md unter pipeline_dir.
    Bei Schreibfehler: Warnung founder_report_write_failed, kein Crash.
    """
    if not isinstance(result, dict):
        result = {}
    out = dict(result)
    paths = dict(out.get("paths") or {})
    out["paths"] = paths
    try:
        md = build_local_preview_founder_report(out)
    except Exception:
        md = (
            "# Local Preview Founder Report\n\n"
            "## Verdict\nStatus: **FAIL**\n\n"
            "(Report konnte nicht aufgebaut werden — Rohdaten prüfen.)\n"
        )
        w = _list_str(out.get("warnings"))
        w.append("founder_report_build_failed")
        out["warnings"] = w
    out["report_markdown"] = md

    pd = _s(out.get("pipeline_dir"))
    if not pd:
        return out

    try:
        rp = Path(pd) / "local_preview_report.md"
        rp.parent.mkdir(parents=True, exist_ok=True)
        rp.write_text(md, encoding="utf-8")
        report_path = str(rp.resolve())
        paths["founder_report"] = report_path
        out["report_path"] = report_path
    except OSError:
        w = _list_str(out.get("warnings"))
        w.append("founder_report_write_failed")
        out["warnings"] = w
    return out


def finalize_local_preview_operator_artifacts(result: dict) -> dict:
    """
    Founder Report (BA 20.10), OPEN_ME (BA 20.12), Quality Checklist (BA 21.1).

    Checklist nach erstem Schreiben von Report/OPEN_ME, dann erneutes Schreiben mit Abschnitt.
    """
    out = write_local_preview_founder_report(result)
    out = write_local_preview_open_me(out)
    try:
        out["quality_checklist"] = build_local_preview_quality_checklist(out)
    except Exception:
        w = _list_str(out.get("warnings"))
        w.append("quality_checklist_build_failed")
        out["warnings"] = w
        out["quality_checklist"] = {
            "status": "fail",
            "items": [],
            "warnings": _collect_local_preview_warnings(out),
            "blocking_reasons": sanitize_local_preview_blocking_reasons(out.get("blocking_reasons")),
            "next_step": local_preview_next_step_for_verdict("FAIL"),
        }
    out = write_local_preview_founder_report(out)
    out = write_local_preview_open_me(out)
    return out


def run_local_preview_pipeline(
    timeline_manifest: Path,
    narration_script: Path,
    *,
    out_root: Path,
    run_id: str,
    motion_mode: str = "static",
    subtitle_mode: str = "simple",
    subtitle_style: str = "classic",
    subtitle_source: str = "narration",
    audio_path: Optional[Path] = None,
    force_burn: bool = False,
    ffmpeg_bin: Optional[str] = None,
    ffprobe_bin: Optional[str] = None,
    build_subtitle_pack_fn: Optional[Callable[..., Dict[str, Any]]] = None,
    render_final_story_video_fn: Optional[Callable[..., Dict[str, Any]]] = None,
    burn_in_subtitles_preview_fn: Optional[Callable[..., Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Reihenfolge: build_subtitle_file → render_final_story_video (ohne Legacy-Burn-in) → burn_in_subtitles_preview.
    Injektion der *_fn-Parameter nur für Tests.
    """
    rid = (run_id or "").strip() or str(uuid.uuid4())
    out_root_p = Path(out_root).resolve()
    pipeline_dir = out_root_p / f"local_preview_{rid}"
    pipeline_dir.mkdir(parents=True, exist_ok=True)
    clean_video = pipeline_dir / "clean_video.mp4"

    warnings: List[str] = []
    blocking: List[str] = []

    build_mod = _load_module("build_subtitle_file_dyn", _BUILD_SCRIPT)
    render_mod = _load_module("render_final_story_video_dyn", _RENDER_SCRIPT)
    burn_mod = _load_module("burn_in_subtitles_preview_dyn", _BURN_SCRIPT)

    b_fn = build_subtitle_pack_fn or build_mod.build_subtitle_pack
    r_fn = render_final_story_video_fn or render_mod.render_final_story_video
    u_fn = burn_in_subtitles_preview_fn or burn_mod.burn_in_subtitles_preview

    def _finalize(raw: Dict[str, Any]) -> Dict[str, Any]:
        return finalize_local_preview_operator_artifacts(raw)

    step_build = b_fn(
        Path(narration_script).resolve(),
        timeline_manifest_path=Path(timeline_manifest).resolve(),
        out_root=out_root_p,
        run_id=rid,
        subtitle_mode=subtitle_mode,
        subtitle_source=subtitle_source,
        subtitle_style=subtitle_style,
        audio_path=audio_path,
    )
    warnings.extend(list(step_build.get("warnings") or []))
    blocking.extend(list(step_build.get("blocking_reasons") or []))

    if not step_build.get("ok"):
        return _finalize(
            {
                "ok": False,
                "run_id": rid,
                "pipeline_dir": str(pipeline_dir),
                "steps": {"build_subtitles": step_build, "render_clean": None, "burnin_preview": None},
                "paths": {
                    "subtitle_manifest": step_build.get("subtitle_manifest_path") or "",
                    "clean_video": "",
                    "preview_with_subtitles": "",
                },
                "warnings": warnings,
                "blocking_reasons": sanitize_local_preview_blocking_reasons(blocking)
                or ["build_subtitles_failed"],
            }
        )

    sub_man = Path(str(step_build["subtitle_manifest_path"])).resolve()

    step_render = r_fn(
        Path(timeline_manifest).resolve(),
        output_video=clean_video,
        motion_mode=motion_mode,
        subtitle_path=None,
        ffmpeg_bin=ffmpeg_bin,
        ffprobe_bin=ffprobe_bin,
        run_id=rid,
        write_output_manifest=True,
        manifest_root=out_root_p,
    )
    warnings.extend(list(step_render.get("warnings") or []))
    blocking.extend(list(step_render.get("blocking_reasons") or []))

    if not step_render.get("video_created"):
        return _finalize(
            {
                "ok": False,
                "run_id": rid,
                "pipeline_dir": str(pipeline_dir),
                "steps": {"build_subtitles": step_build, "render_clean": step_render, "burnin_preview": None},
                "paths": {
                    "subtitle_manifest": str(sub_man),
                    "clean_video": str(clean_video),
                    "preview_with_subtitles": "",
                },
                "warnings": warnings,
                "blocking_reasons": sanitize_local_preview_blocking_reasons(blocking)
                or ["render_clean_failed"],
            }
        )

    step_burn = u_fn(
        clean_video,
        sub_man,
        out_root=out_root_p,
        run_id=rid,
        force=force_burn,
        ffmpeg_bin=ffmpeg_bin,
    )
    warnings.extend(list(step_burn.get("warnings") or []))
    blocking.extend(list(step_burn.get("blocking_reasons") or []))
    blocking = sanitize_local_preview_blocking_reasons(blocking)

    preview_path = str(step_burn.get("output_video_path") or "")
    burn_ok = bool(step_burn.get("ok"))
    skipped = bool(step_burn.get("skipped"))
    overall_ok = burn_ok and (skipped or bool(preview_path))

    raw_result: Dict[str, Any] = {
        "ok": overall_ok and not blocking,
        "run_id": rid,
        "pipeline_dir": str(pipeline_dir),
        "steps": {
            "build_subtitles": step_build,
            "render_clean": step_render,
            "burnin_preview": step_burn,
        },
        "paths": {
            "subtitle_manifest": str(sub_man),
            "clean_video": str(clean_video.resolve()) if clean_video.is_file() else str(clean_video),
            "preview_with_subtitles": preview_path,
        },
        "warnings": warnings,
        "blocking_reasons": blocking,
    }
    return _finalize(colocate_local_preview_video(raw_result))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="BA 20.9 / BA 20.10 — Lokale Preview-Pipeline + optional Founder-Markdown-Report."
    )
    parser.add_argument("--timeline-manifest", type=Path, required=True, dest="timeline_manifest")
    parser.add_argument("--narration-script", type=Path, required=True, dest="narration_script")
    parser.add_argument("--out-root", type=Path, default=ROOT / "output", dest="out_root")
    parser.add_argument("--run-id", default="", dest="run_id")
    parser.add_argument(
        "--motion-mode",
        choices=("static", "basic"),
        default="static",
        dest="motion_mode",
        help="Weiter an render_final_story_video (Default static = weniger ffmpeg-Risiko)",
    )
    parser.add_argument(
        "--subtitle-mode",
        choices=("none", "simple"),
        default="simple",
        dest="subtitle_mode",
    )
    parser.add_argument(
        "--subtitle-style",
        choices=("classic", "word_by_word", "typewriter", "karaoke", "none"),
        default="classic",
        dest="subtitle_style",
    )
    parser.add_argument(
        "--subtitle-source",
        choices=("narration", "audio"),
        default="narration",
        dest="subtitle_source",
    )
    parser.add_argument("--audio-path", type=Path, default=None, dest="audio_path")
    parser.add_argument(
        "--force-burn",
        action="store_true",
        dest="force_burn",
        help="Weiter an burn_in_subtitles_preview --force",
    )
    parser.add_argument(
        "--print-report",
        action="store_true",
        dest="print_report",
        help="Nach dem JSON den Markdown-Founder-Report (BA 20.10) auf stdout ausgeben",
    )
    args = parser.parse_args()

    meta = run_local_preview_pipeline(
        args.timeline_manifest,
        args.narration_script,
        out_root=args.out_root,
        run_id=(args.run_id or "").strip() or str(uuid.uuid4()),
        motion_mode=args.motion_mode,
        subtitle_mode=args.subtitle_mode,
        subtitle_style=args.subtitle_style,
        subtitle_source=args.subtitle_source,
        audio_path=args.audio_path,
        force_burn=bool(args.force_burn),
    )
    md = meta.pop("report_markdown", None)
    print(json.dumps(meta, ensure_ascii=False, indent=2))
    if args.print_report and md:
        print("\n---\n")
        print(md, end="" if str(md).endswith("\n") else "\n")
    return 0 if meta.get("ok") else 3


if __name__ == "__main__":
    raise SystemExit(main())
