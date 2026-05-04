"""BA 20.9 / BA 20.10 — Lokale Preview-Pipeline + Founder-Markdown-Report."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
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


def _gather_local_preview_warnings_for_classification(result: Any) -> List[str]:
    """
    BA 21.4 — Alle Warn-Codes für Klassifikation (Top-Level, Steps, Sync Guard,
    Subtitle Quality, Quality-Checklist-Teilwarnungen), stabil und ohne Duplikate.
    """
    if not isinstance(result, dict):
        return []
    seen: set[str] = set()
    out: List[str] = []
    for w in _collect_local_preview_warnings(result):
        if w not in seen:
            seen.add(w)
            out.append(w)
    for key in ("sync_guard", "subtitle_quality_check", "quality_checklist"):
        sub = result.get(key)
        if isinstance(sub, dict):
            for w in _list_str(sub.get("warnings")):
                if w not in seen:
                    seen.add(w)
                    out.append(w)
    return out


# BA 21.4 — (prefix, level); längere Prefixe zuerst matchen (sortiert beim Laden).
_LOCAL_PREVIEW_WARN_CLASS_PREFIXES_RAW: List[Tuple[str, str]] = [
    # BLOCKING — Pipeline / IO / harte Abbrüche
    ("quality_checklist_build_failed", "BLOCKING"),
    ("founder_report_build_failed", "BLOCKING"),
    ("founder_report_write_failed", "BLOCKING"),
    ("open_me_build_failed", "BLOCKING"),
    ("open_me_write_failed", "BLOCKING"),
    ("subtitle_quality_build_failed", "BLOCKING"),
    ("sync_guard_build_failed", "BLOCKING"),
    ("ffmpeg_burnin_failed", "BLOCKING"),
    ("ffmpeg_missing", "BLOCKING"),
    ("input_video_missing", "BLOCKING"),
    ("build_failed", "BLOCKING"),
    ("burn_failed", "BLOCKING"),
    ("narration_script_missing", "BLOCKING"),
    ("narration_body_empty", "BLOCKING"),
    ("subtitle_audio_path_missing_or_invalid", "BLOCKING"),
    # WARNING — operative Abweichungen, Sync-Fails, Qualität
    ("sync_guard_fail", "WARNING"),
    ("sync_guard_warning", "WARNING"),
    ("sync_guard_subtitle_span_missing", "WARNING"),
    ("sync_guard_clean_video_missing", "WARNING"),
    ("sync_guard_preview_video_missing", "WARNING"),
    ("sync_guard_clean_vs_timeline_fail", "WARNING"),
    ("sync_guard_preview_vs_timeline_fail", "WARNING"),
    ("sync_guard_subtitle_vs_timeline_fail", "WARNING"),
    ("sync_guard_audio_vs_timeline_fail", "WARNING"),
    ("sync_guard_clean_vs_timeline_warn", "WARNING"),
    ("sync_guard_preview_vs_timeline_warn", "WARNING"),
    ("sync_guard_subtitle_vs_timeline_warn", "WARNING"),
    ("sync_guard_audio_vs_timeline_warn", "WARNING"),
    ("sync_guard_preview_vs_clean_warn", "WARNING"),
    ("sync_guard_timeline_missing", "WARNING"),
    ("subtitle_quality_fail", "WARNING"),
    ("subtitle_quality_warning", "WARNING"),
    ("subtitle_manifest_parse_failed", "WARNING"),
    ("subtitles_srt_missing", "WARNING"),
    ("subtitle_transcription_failed_fallback_narration", "WARNING"),
    ("subtitle_transcription_no_cues_fallback_narration", "WARNING"),
    ("subtitle_transcription_response_not_object", "WARNING"),
    ("build_warn", "WARNING"),
    ("burn_warn", "WARNING"),
    ("preview_colocation_pipeline_dir_invalid", "WARNING"),
    ("preview_colocation_source_invalid", "WARNING"),
    ("preview_colocation_source_missing", "WARNING"),
    ("preview_colocation_copy_failed", "WARNING"),
    ("audio_path_set_but_file_missing_silent_render", "WARNING"),
    ("audio_missing_silent_render", "WARNING"),
    ("motion_render_failed_fallback_static", "WARNING"),
    ("legacy_subtitle_path_burnin_used", "WARNING"),
    ("subtitle_burn_failed_fallback_no_subtitles", "WARNING"),
    ("subtitle_path_set_but_file_missing_skipped", "WARNING"),
    ("subtitle_file_empty_skipped", "WARNING"),
    ("audio_shorter_than_timeline_padded_or_continued", "WARNING"),
    # CHECK — Verifikation / Probe / übersprungene Vergleiche
    ("sync_guard_timeline_read_failed", "CHECK"),
    ("sync_guard_audio_probe_failed", "CHECK"),
    ("sync_guard_clean_probe_failed", "CHECK"),
    ("sync_guard_preview_probe_failed", "CHECK"),
    ("sync_guard_clean_vs_timeline_skipped", "CHECK"),
    ("sync_guard_preview_vs_timeline_skipped", "CHECK"),
    ("sync_guard_preview_vs_clean_skipped", "CHECK"),
    ("sync_guard_subtitle_vs_timeline_skipped", "CHECK"),
    ("ffprobe_missing_cannot_probe_audio", "CHECK"),
    ("audio_duration_probe_failed", "CHECK"),
    ("audio_duration_probe_empty", "CHECK"),
    ("timeline_manifest_invalid_ignored_for_duration", "CHECK"),
    ("word_by_word_requires_word_level_timing_not_in_srt_v1", "CHECK"),
    ("typewriter_v1_contract_only_srt_has_line_timing_only", "CHECK"),
    ("karaoke_requires_word_timing_srt_v1_line_timing_only", "CHECK"),
    # INFO — erwartbare Fallbacks / Idempotenz / harmlose Defaults
    ("preview_with_subtitles_already_exists", "INFO"),
    ("sync_guard_no_audio_file", "INFO"),
    ("subtitle_mode_unknown", "INFO"),
    ("subtitle_source_unknown", "INFO"),
    ("subtitle_style_unknown", "INFO"),
    ("subtitle_typewriter_ass_renderer_used", "INFO"),
    ("subtitle_burnin_safe_style_applied", "INFO"),
    ("subtitle_srt_wrapped_for_burnin", "INFO"),
    ("subtitle_style_none_skipped", "INFO"),
    ("subtitle_style_none_visual_suppressed", "INFO"),
    ("subtitle_style_none_contract_only", "INFO"),
    ("subtitle_mode_none_no_cues", "INFO"),
    ("subtitle_audio_transcription_env_missing_fallback_narration", "INFO"),
    ("subtitle_style_word_by_word_rendered_as_srt", "INFO"),
    ("subtitle_style_karaoke_fallback_to_srt_burnin", "INFO"),
    ("subtitle_typewriter_ass_failed_fallback_srt", "INFO"),
    ("subtitle_timeline_duration_used", "INFO"),
    ("subtitle_audio_duration_used", "INFO"),
    ("subtitle_duration_estimate_used", "INFO"),
]

_LOCAL_PREVIEW_WARN_CLASS_PREFIXES_SORTED: List[Tuple[str, str]] = sorted(
    _LOCAL_PREVIEW_WARN_CLASS_PREFIXES_RAW,
    key=lambda t: len(t[0]),
    reverse=True,
)


def classify_local_preview_warning(code: str) -> str:
    """BA 21.4 — INFO | CHECK | WARNING | BLOCKING für einen Warn-String."""
    c = (_s(code) or "").strip().lower()
    if not c:
        return "INFO"
    base = c.split(":", 1)[0].strip()
    for prefix, lvl in _LOCAL_PREVIEW_WARN_CLASS_PREFIXES_SORTED:
        if base == prefix or base.startswith(prefix + "_") or base.startswith(prefix + ":"):
            return lvl
    if base.endswith("_version_check_timeout") or base.endswith("_version_check_os_error"):
        return "CHECK"
    if base.endswith("_version_check_failed") or base.endswith("_version_parse_empty"):
        return "CHECK"
    if "not monotonic" in c or "overlapping cues" in c:
        return "WARNING"
    if base.startswith("sync_guard_"):
        return "CHECK"
    return "WARNING"


def build_local_preview_warning_classification(result: Any) -> Dict[str, Any]:
    """BA 21.4 — Aggregat: höchste Stufe, Zähler, Items mit Level."""
    codes = _gather_local_preview_warnings_for_classification(result)
    items: List[Dict[str, str]] = []
    counts = {"INFO": 0, "CHECK": 0, "WARNING": 0, "BLOCKING": 0}
    for code in codes:
        lvl = classify_local_preview_warning(code)
        items.append({"code": code, "level": lvl})
        if lvl in counts:
            counts[lvl] += 1
    highest = "INFO"
    for lvl in ("BLOCKING", "WARNING", "CHECK", "INFO"):
        if counts.get(lvl, 0) > 0:
            highest = lvl
            break
    bits = [f"{counts[k]} {k}" for k in ("BLOCKING", "WARNING", "CHECK", "INFO") if counts.get(k, 0)]
    summary = ", ".join(bits) if bits else "keine Warnungen"
    return {
        "highest": highest,
        "counts": counts,
        "items": items,
        "summary": summary,
    }


def _preview_subpack_status_str(pack: Any) -> str:
    if not isinstance(pack, dict):
        return ""
    return str(pack.get("status") or "").strip().lower()


def _pick_founder_quality_top_issue(result: dict, verdict: str) -> str:
    br = sanitize_local_preview_blocking_reasons(result.get("blocking_reasons"))
    if br:
        return f"Blocking: {br[0]}"
    qc = result.get("quality_checklist")
    if isinstance(qc, dict):
        for it in qc.get("items") or []:
            if isinstance(it, dict) and str(it.get("status", "")).lower() == "fail":
                lab = _s(it.get("label")) or _s(it.get("id"))
                return f"Quality-Checkliste: {lab or 'Check fehlgeschlagen'}"
    sq = result.get("subtitle_quality_check")
    if isinstance(sq, dict) and _preview_subpack_status_str(sq) == "fail":
        return _s(sq.get("summary")) or "Subtitle Quality: FAIL"
    sg = result.get("sync_guard")
    if isinstance(sg, dict) and _preview_subpack_status_str(sg) == "fail":
        return _s(sg.get("summary")) or "Sync Guard: FAIL"
    wc = result.get("warning_classification")
    if isinstance(wc, dict):
        for lvl in ("BLOCKING", "WARNING", "CHECK"):
            for it in wc.get("items") or []:
                if not isinstance(it, dict):
                    continue
                if str(it.get("level") or "").strip().upper() != lvl:
                    continue
                c = _s(it.get("code"))
                if c:
                    return f"Warnung [{lvl}]: {c}"
    if verdict == "WARNING":
        return "Verdict WARNING: Top-Level- oder Step-Warnungen prüfen."
    if verdict == "FAIL":
        return "Verdict FAIL: Pipeline ok/blocking prüfen."
    return "Kein dominanter Einzelpunkt — Preview inhaltlich plausibilisieren."


def founder_quality_next_step(decision_code: str) -> str:
    """Nächster Schritt abgeleitet von der Founder-Entscheidung (BA 21.5)."""
    c = (decision_code or "").strip().upper()
    if c == "BLOCK":
        return local_preview_next_step_for_verdict("FAIL")
    if c == "REVIEW_REQUIRED":
        return local_preview_next_step_for_verdict("WARNING")
    return local_preview_next_step_for_verdict("PASS")


def build_founder_quality_decision(result: Any) -> Dict[str, Any]:
    """
    BA 21.5 — Übersetzt Verdict, Quality-Checkliste, Subtitle Quality, Sync Guard und
    Warn-Klassifikation in eine stabile Founder-Entscheidung (Dashboard-tauglich).
    """
    r = result if isinstance(result, dict) else {}
    verdict = compute_local_preview_verdict(r)
    qc_st = _preview_subpack_status_str(r.get("quality_checklist"))
    sq_st = _preview_subpack_status_str(r.get("subtitle_quality_check"))
    sg_st = _preview_subpack_status_str(r.get("sync_guard"))
    wc = r.get("warning_classification") if isinstance(r.get("warning_classification"), dict) else {}
    wh = str(wc.get("highest") or "INFO").strip().upper()
    blocking_eff = sanitize_local_preview_blocking_reasons(r.get("blocking_reasons"))
    blocking_n = len(blocking_eff)

    block_hard = (
        verdict == "FAIL"
        or blocking_n > 0
        or qc_st == "fail"
        or sq_st == "fail"
        or sg_st == "fail"
        or wh == "BLOCKING"
    )
    review_soft = not block_hard and (
        verdict == "WARNING"
        or qc_st == "warning"
        or sq_st == "warning"
        or sg_st == "warning"
        or wh in ("WARNING", "CHECK")
    )

    if block_hard:
        code = "BLOCK"
        label = "Nicht freigeben — Blocker, FAIL-Verdict oder kritische Warnstufe."
    elif review_soft:
        code = "REVIEW_REQUIRED"
        label = "Kein harter Blocker — Founder-Review empfohlen (Warnungen oder Prüfpunkte)."
    else:
        code = "GO_PREVIEW"
        label = "Technisch durchweg grün — Preview inhaltlich prüfen."

    top_issue = _pick_founder_quality_top_issue(r, verdict)
    nxt = founder_quality_next_step(code)

    factors: List[str] = []
    if verdict != "PASS":
        factors.append(f"Verdict: {verdict}")
    if qc_st:
        factors.append(f"Quality-Checkliste: {qc_st.upper()}")
    if sq_st:
        factors.append(f"Subtitle Quality: {sq_st.upper()}")
    if sg_st:
        factors.append(f"Sync Guard: {sg_st.upper()}")
    factors.append(f"Höchste Warnstufe: {wh}")

    sig: Dict[str, Any] = {
        "verdict": verdict,
        "quality_checklist": qc_st,
        "subtitle_quality": sq_st,
        "sync_guard": sg_st,
        "warning_level_highest": wh,
        "blocking_reasons_count": blocking_n,
    }

    return {
        "decision_code": code,
        "decision_label_de": label,
        "top_issue": top_issue,
        "next_step": nxt,
        "signals": sig,
        "factors_de": factors[:8],
    }


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


# BA 21.2 — heuristische Subtitle-Timing-/Lesbarkeits-Schwellen (lokal, kein ffmpeg)
_SUBTITLE_Q_MAX_WORDS = 12
_SUBTITLE_Q_MAX_CHARS = 80
_SUBTITLE_Q_MIN_DUR = 0.25
_SUBTITLE_Q_MAX_DUR = 8.0
_SUBTITLE_Q_HIGH_CUE_COUNT = 200

# BA 21.3 — grobe Sync-/Dauer-Schwellen (lokal, ffprobe nur bei vorhandenen Dateien)
_SYNC_V_TL_PASS_ABS = 0.75
_SYNC_V_TL_PASS_PCT = 0.10
_SYNC_V_TL_WARN_ABS = 2.0
_SYNC_V_TL_WARN_PCT = 0.25
_SYNC_SUB_TL_WARN_PCT = 0.35
_SYNC_PREVIEW_CLEAN_PASS_ABS = 0.5
_SYNC_PREVIEW_CLEAN_PASS_PCT = 0.10

_SRT_TS_LINE_Q = re.compile(
    r"^\s*(\d{1,2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{1,2}):(\d{2}):(\d{2})[,.](\d{3})\s*$"
)


def _srt_hmsf_to_seconds_q(h: str, m: str, s: str, f: str) -> float:
    return int(h) * 3600 + int(m) * 60 + int(s) + int(f) / 1000.0


def _parse_srt_cues_simple(content: str) -> List[Dict[str, Any]]:
    raw = (content or "").replace("\r\n", "\n").replace("\r", "\n")
    stripped = raw.strip()
    if not stripped:
        return []
    cues: List[Dict[str, Any]] = []
    for block in re.split(r"\n\s*\n", stripped):
        lines = [ln for ln in block.split("\n") if ln is not None]
        if not lines:
            continue
        tli = 1 if lines[0].strip().isdigit() else 0
        if tli >= len(lines):
            continue
        m = _SRT_TS_LINE_Q.match((lines[tli] or "").strip())
        if not m:
            continue
        t0 = _srt_hmsf_to_seconds_q(m.group(1), m.group(2), m.group(3), m.group(4))
        t1 = _srt_hmsf_to_seconds_q(m.group(5), m.group(6), m.group(7), m.group(8))
        text = " ".join(x.strip() for x in lines[tli + 1 :] if x.strip())
        dur = t1 - t0
        if dur < 0:
            t1 = t0
            dur = 0.0
        cues.append({"start": float(t0), "end": float(t1), "text": text, "duration": float(max(t1 - t0, 0.0))})
    return cues


def _resolve_subtitle_manifest_path(result: dict, paths: Dict[str, Any]) -> str:
    for k in ("subtitle_manifest", "subtitle_manifest_path", "subtitle_path", "subtitle_file", "subtitles"):
        p = _s(paths.get(k))
        if p:
            return p
    steps = result.get("steps")
    if isinstance(steps, dict):
        b = steps.get("build_subtitles")
        if isinstance(b, dict):
            p = _s(b.get("subtitle_manifest_path"))
            if p:
                return p
    return ""


def _cue_list_from_manifest_doc(doc: Dict[str, Any], manifest_path: Path) -> Tuple[List[Dict[str, Any]], str]:
    """Cues aus Manifest-Listenfeldern oder referenziertem SRT."""
    for key in ("cues", "subtitles", "items", "entries"):
        raw = doc.get(key)
        if not isinstance(raw, list) or not raw:
            continue
        out: List[Dict[str, Any]] = []
        for obj in raw:
            if not isinstance(obj, dict):
                continue
            text = _s(obj.get("text") or obj.get("body") or obj.get("content"))
            s = obj.get("start_seconds", obj.get("start"))
            e = obj.get("end_seconds", obj.get("end"))
            try:
                t0 = float(s)
                t1 = float(e)
            except (TypeError, ValueError):
                continue
            out.append({"start": t0, "end": t1, "text": text, "duration": max(t1 - t0, 0.0)})
        if out:
            return out, f"manifest.{key}"
    srt_rel = _s(doc.get("subtitles_srt_path"))
    if srt_rel:
        srt_p = Path(srt_rel)
        if not srt_p.is_absolute():
            srt_p = (manifest_path.parent / srt_p).resolve()
        try:
            if srt_p.is_file():
                return _parse_srt_cues_simple(srt_p.read_text(encoding="utf-8", errors="replace")), str(srt_p)
        except OSError:
            return [], str(srt_p)
    return [], ""


def _probe_media_duration_seconds(
    path: Path,
    *,
    _run: Any = None,
    _which: Optional[Callable[[str], Optional[str]]] = None,
    _timeout_sec: float = 5.0,
) -> Tuple[Optional[float], Optional[str]]:
    """
    Liest Medien-Dauer per ffprobe (format=duration). Kein Crash nach außen.
    `_run` / `_which` nur für Tests injizieren.
    """
    run_fn = subprocess.run if _run is None else _run
    which_fn = shutil.which if _which is None else _which
    try:
        p = path.resolve()
    except OSError:
        return None, "path_resolve_failed"
    if not p.is_file():
        return None, "file_missing"
    ffprobe = which_fn("ffprobe")
    if not ffprobe:
        return None, "ffprobe_not_found"
    cmd = [
        ffprobe,
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(p),
    ]
    try:
        proc = run_fn(
            cmd,
            capture_output=True,
            text=True,
            timeout=_timeout_sec,
        )
    except subprocess.TimeoutExpired:
        return None, "ffprobe_timeout"
    except OSError:
        return None, "ffprobe_os_error"
    if getattr(proc, "returncode", 1) != 0:
        return None, "ffprobe_nonzero_exit"
    raw = (getattr(proc, "stdout", None) or "").strip()
    if not raw or raw == "N/A":
        return None, "duration_empty"
    try:
        return float(raw), None
    except ValueError:
        return None, "duration_parse_failed"


def _resolve_timeline_manifest_path_for_sync(result: dict, paths: Dict[str, Any]) -> str:
    for k in ("timeline_manifest", "timeline_manifest_path", "timeline_path"):
        p = _s(paths.get(k))
        if p:
            return p
    steps = result.get("steps")
    if isinstance(steps, dict):
        rr = steps.get("render_clean")
        if isinstance(rr, dict):
            p = _s(rr.get("timeline_manifest_path") or rr.get("timeline_path"))
            if p:
                return p
    sm = _resolve_subtitle_manifest_path(result, paths)
    smp = _safe_operator_path(sm)
    if smp is not None and smp.is_file():
        try:
            d = json.loads(smp.read_text(encoding="utf-8", errors="replace"))
            if isinstance(d, dict):
                rel = _s(d.get("timeline_manifest"))
                if rel:
                    pth = Path(rel)
                    if not pth.is_absolute():
                        pth = (smp.parent / pth).resolve()
                    if pth.is_file():
                        return str(pth)
        except (OSError, json.JSONDecodeError, ValueError, TypeError):
            pass
    return ""


def _sync_timeline_duration_seconds(doc: Dict[str, Any]) -> float:
    for key in ("total_duration_seconds", "estimated_total_duration_seconds", "estimated_duration_seconds"):
        v = doc.get(key)
        if v is not None:
            try:
                x = float(v)
                if x > 0.001:
                    return x
            except (TypeError, ValueError):
                pass
    tl = doc.get("timeline")
    if isinstance(tl, list) and tl:
        s = 0.0
        for seg in tl:
            if not isinstance(seg, dict):
                continue
            got = False
            for dk in ("duration_seconds", "estimated_duration_seconds", "duration"):
                v = seg.get(dk)
                if v is not None:
                    try:
                        s += max(0.0, float(v))
                        got = True
                        break
                    except (TypeError, ValueError):
                        pass
            if not got:
                s += 0.0
        if s > 0.001:
            return s
    scenes = doc.get("scenes")
    if isinstance(scenes, list) and scenes:
        s = 0.0
        for sc in scenes:
            if not isinstance(sc, dict):
                continue
            d = sc.get("duration_seconds")
            if d is None:
                d = sc.get("estimated_duration_seconds")
            try:
                if d is not None:
                    s += max(0.0, float(d))
            except (TypeError, ValueError):
                pass
        if s > 0.001:
            return s
    return 0.0


def _sync_resolve_audio_path(paths: Dict[str, Any], tl_doc: Optional[Dict[str, Any]], tl_file: Optional[Path]) -> str:
    ap = _s(paths.get("audio_path"))
    if ap:
        return ap
    if not isinstance(tl_doc, dict):
        return ""
    rel = _s(tl_doc.get("audio_path") or tl_doc.get("narration_audio_path"))
    if not rel:
        return ""
    p = Path(rel)
    if p.is_file():
        return str(p.resolve())
    if tl_file is not None:
        try:
            cand = (tl_file.parent / rel).resolve()
            if cand.is_file():
                return str(cand)
        except OSError:
            pass
    return ""


def _sync_subtitle_span_seconds(result: dict, paths: Dict[str, Any]) -> Optional[float]:
    mp_str = _resolve_subtitle_manifest_path(result, paths)
    mp = _safe_operator_path(mp_str)
    if mp is None or not mp.is_file():
        return None
    try:
        doc = json.loads(mp.read_text(encoding="utf-8", errors="replace"))
        if not isinstance(doc, dict):
            return None
        cues, _src = _cue_list_from_manifest_doc(doc, mp)
        if not cues:
            return None
        return max(float(c.get("end", 0.0)) for c in cues)
    except (OSError, json.JSONDecodeError, ValueError, TypeError):
        return None


def _sync_merge_item_status(*parts: str) -> str:
    if any(p == "fail" for p in parts):
        return "fail"
    if any(p == "warning" for p in parts):
        return "warning"
    return "pass"


def _sync_classify_video_vs_timeline(abs_delta: float, timeline_ref: float) -> str:
    if timeline_ref <= 0:
        return "warning"
    pct = abs_delta / timeline_ref
    if abs_delta <= _SYNC_V_TL_PASS_ABS or pct <= _SYNC_V_TL_PASS_PCT:
        return "pass"
    if abs_delta <= _SYNC_V_TL_WARN_ABS or pct <= _SYNC_V_TL_WARN_PCT:
        return "warning"
    return "fail"


def _sync_classify_subtitle_vs_timeline(abs_delta: float, timeline_ref: float) -> str:
    if timeline_ref <= 0:
        return "warning"
    pct = abs_delta / timeline_ref
    if abs_delta <= _SYNC_V_TL_PASS_ABS or pct <= _SYNC_V_TL_PASS_PCT:
        return "pass"
    if pct <= _SYNC_SUB_TL_WARN_PCT:
        return "warning"
    return "fail"


def _sync_classify_preview_vs_clean(abs_delta: float, clean_ref: float) -> str:
    if clean_ref <= 0:
        return "warning"
    pct = abs_delta / clean_ref
    if abs_delta <= _SYNC_PREVIEW_CLEAN_PASS_ABS or pct <= _SYNC_PREVIEW_CLEAN_PASS_PCT:
        return "pass"
    return "warning"


def build_local_preview_sync_guard(
    result: dict,
    *,
    _probe: Optional[Callable[[Path], Tuple[Optional[float], Optional[str]]]] = None,
) -> Dict[str, Any]:
    """BA 21.3 — Grobe Dauer-/Sync-Prüfung (Timeline, Untertitel, Audio, Videos); ffprobe optional injizierbar."""
    r = result if isinstance(result, dict) else {}
    paths = r.get("paths")
    if not isinstance(paths, dict):
        paths = {}

    probe_fn = _probe if _probe is not None else (lambda pth: _probe_media_duration_seconds(pth))

    def _it(
        iid: str,
        label: str,
        status: str,
        detail: str,
        value_seconds: Optional[float] = None,
    ) -> Dict[str, Any]:
        o: Dict[str, Any] = {
            "id": iid,
            "label": label,
            "status": status,
            "detail": detail,
        }
        if value_seconds is not None:
            o["value_seconds"] = float(value_seconds)
        return o

    items: List[Dict[str, Any]] = []
    sw: List[str] = []
    tl_path_str = _resolve_timeline_manifest_path_for_sync(r, paths)
    tl_file = _safe_operator_path(tl_path_str)
    tl_doc: Optional[Dict[str, Any]] = None
    tl_sec: Optional[float] = None
    if tl_path_str and tl_file is not None and tl_file.is_file():
        try:
            raw_tl = json.loads(tl_file.read_text(encoding="utf-8", errors="replace"))
            if isinstance(raw_tl, dict):
                tl_doc = raw_tl
                tnum = _sync_timeline_duration_seconds(raw_tl)
                tl_sec = tnum if tnum > 0.001 else None
        except (OSError, json.JSONDecodeError, ValueError, TypeError):
            sw.append("sync_guard_timeline_read_failed")
    if tl_sec is not None:
        items.append(
            _it(
                "timeline_duration_available",
                "Timeline duration available",
                "pass",
                f"from manifest ({tl_path_str})",
                tl_sec,
            )
        )
    else:
        items.append(
            _it(
                "timeline_duration_available",
                "Timeline duration available",
                "warning",
                "no usable timeline duration",
                None,
            )
        )
        sw.append("sync_guard_timeline_missing")

    sub_span = _sync_subtitle_span_seconds(r, paths)
    if sub_span is not None and sub_span > 0:
        items.append(
            _it(
                "subtitle_duration_available",
                "Subtitle duration available",
                "pass",
                "max cue end",
                sub_span,
            )
        )
    else:
        items.append(
            _it(
                "subtitle_duration_available",
                "Subtitle duration available",
                "warning",
                "could not derive subtitle span",
                None,
            )
        )
        sw.append("sync_guard_subtitle_span_missing")

    audio_path_str = _sync_resolve_audio_path(paths, tl_doc, tl_file)
    ap = _safe_operator_path(audio_path_str)
    audio_sec: Optional[float] = None
    if not audio_path_str or ap is None or not ap.is_file():
        items.append(
            _it(
                "audio_duration_available",
                "Audio duration available",
                "warning",
                "no audio file (silent render possible)",
                None,
            )
        )
        sw.append("sync_guard_no_audio_file")
    else:
        ad, ad_err = probe_fn(ap)
        audio_sec = ad
        if audio_sec is not None and audio_sec > 0:
            items.append(
                _it(
                    "audio_duration_available",
                    "Audio duration available",
                    "pass",
                    "ffprobe ok" if not ad_err else f"ffprobe: {ad_err}",
                    audio_sec,
                )
            )
        else:
            items.append(
                _it(
                    "audio_duration_available",
                    "Audio duration available",
                    "warning",
                    ad_err or "ffprobe failed",
                    None,
                )
            )
            sw.append("sync_guard_audio_probe_failed")

    clean_str = _s(paths.get("clean_video"))
    preview_str = resolve_local_preview_video_path(paths) or _s(paths.get("preview_with_subtitles"))
    cv = _safe_operator_path(clean_str)
    pv = _safe_operator_path(preview_str)
    clean_sec: Optional[float] = None
    preview_sec: Optional[float] = None

    if cv is not None and cv.is_file():
        cd, cd_err = probe_fn(cv)
        clean_sec = cd
        if clean_sec is not None and clean_sec > 0:
            items.append(
                _it(
                    "clean_video_duration_available",
                    "Clean video duration available",
                    "pass",
                    "ffprobe ok" if not cd_err else f"note: {cd_err}",
                    clean_sec,
                )
            )
        else:
            items.append(
                _it(
                    "clean_video_duration_available",
                    "Clean video duration available",
                    "warning",
                    cd_err or "ffprobe failed",
                    None,
                )
            )
            sw.append("sync_guard_clean_probe_failed")
    else:
        items.append(
            _it(
                "clean_video_duration_available",
                "Clean video duration available",
                "warning",
                "clean video missing",
                None,
            )
        )
        sw.append("sync_guard_clean_video_missing")

    if pv is not None and pv.is_file():
        pdur, pd_err = probe_fn(pv)
        preview_sec = pdur
        if preview_sec is not None and preview_sec > 0:
            items.append(
                _it(
                    "preview_video_duration_available",
                    "Preview video duration available",
                    "pass",
                    "ffprobe ok" if not pd_err else f"note: {pd_err}",
                    preview_sec,
                )
            )
        else:
            items.append(
                _it(
                    "preview_video_duration_available",
                    "Preview video duration available",
                    "warning",
                    pd_err or "ffprobe failed",
                    None,
                )
            )
            sw.append("sync_guard_preview_probe_failed")
    else:
        items.append(
            _it(
                "preview_video_duration_available",
                "Preview video duration available",
                "warning",
                "preview video missing",
                None,
            )
        )
        sw.append("sync_guard_preview_video_missing")

    tl_ref = float(tl_sec) if tl_sec is not None else 0.0

    if tl_sec is not None and clean_sec is not None:
        st = _sync_classify_video_vs_timeline(abs(clean_sec - tl_ref), tl_ref)
        items.append(
            _it(
                "clean_video_vs_timeline",
                "Clean video vs timeline",
                st,
                f"clean {clean_sec:.2f}s vs timeline {tl_ref:.2f}s",
                abs(clean_sec - tl_ref),
            )
        )
        if st == "fail":
            sw.append("sync_guard_clean_vs_timeline_fail")
        elif st == "warning":
            sw.append("sync_guard_clean_vs_timeline_warn")
    else:
        items.append(
            _it(
                "clean_video_vs_timeline",
                "Clean video vs timeline",
                "warning",
                "insufficient data for comparison",
                None,
            )
        )
        sw.append("sync_guard_clean_vs_timeline_skipped")

    if tl_sec is not None and preview_sec is not None:
        st = _sync_classify_video_vs_timeline(abs(preview_sec - tl_ref), tl_ref)
        items.append(
            _it(
                "preview_video_vs_timeline",
                "Preview video vs timeline",
                st,
                f"preview {preview_sec:.2f}s vs timeline {tl_ref:.2f}s",
                abs(preview_sec - tl_ref),
            )
        )
        if st == "fail":
            sw.append("sync_guard_preview_vs_timeline_fail")
        elif st == "warning":
            sw.append("sync_guard_preview_vs_timeline_warn")
    else:
        items.append(
            _it(
                "preview_video_vs_timeline",
                "Preview video vs timeline",
                "warning",
                "insufficient data for comparison",
                None,
            )
        )
        sw.append("sync_guard_preview_vs_timeline_skipped")

    if clean_sec is not None and preview_sec is not None:
        st = _sync_classify_preview_vs_clean(abs(preview_sec - clean_sec), clean_sec)
        items.append(
            _it(
                "preview_vs_clean_video",
                "Preview vs clean video",
                st,
                f"preview {preview_sec:.2f}s vs clean {clean_sec:.2f}s",
                abs(preview_sec - clean_sec),
            )
        )
        if st == "warning":
            sw.append("sync_guard_preview_vs_clean_warn")
    else:
        items.append(
            _it(
                "preview_vs_clean_video",
                "Preview vs clean video",
                "warning",
                "insufficient data for comparison",
                None,
            )
        )
        sw.append("sync_guard_preview_vs_clean_skipped")

    if tl_sec is not None and sub_span is not None:
        st = _sync_classify_subtitle_vs_timeline(abs(sub_span - tl_ref), tl_ref)
        items.append(
            _it(
                "subtitle_vs_timeline",
                "Subtitle vs timeline",
                st,
                f"subtitle end {sub_span:.2f}s vs timeline {tl_ref:.2f}s",
                abs(sub_span - tl_ref),
            )
        )
        if st == "fail":
            sw.append("sync_guard_subtitle_vs_timeline_fail")
        elif st == "warning":
            sw.append("sync_guard_subtitle_vs_timeline_warn")
    else:
        items.append(
            _it(
                "subtitle_vs_timeline",
                "Subtitle vs timeline",
                "warning",
                "insufficient data for comparison",
                None,
            )
        )
        sw.append("sync_guard_subtitle_vs_timeline_skipped")

    if tl_sec is None:
        ast = "warning"
        adetail = "no timeline baseline"
    elif audio_sec is None:
        ast = "pass"
        adetail = "no audio file; comparison skipped"
    else:
        ast = _sync_classify_video_vs_timeline(abs(audio_sec - tl_ref), tl_ref)
        adetail = f"audio {audio_sec:.2f}s vs timeline {tl_ref:.2f}s"
    items.append(
        _it(
            "audio_vs_timeline",
            "Audio vs timeline",
            ast,
            adetail,
            abs(audio_sec - tl_ref) if (audio_sec is not None and tl_sec is not None) else None,
        )
    )
    if ast == "fail":
        sw.append("sync_guard_audio_vs_timeline_fail")
    elif ast == "warning":
        sw.append("sync_guard_audio_vs_timeline_warn")

    _merge_ids = frozenset(
        {
            "timeline_duration_available",
            "clean_video_vs_timeline",
            "preview_video_vs_timeline",
            "preview_vs_clean_video",
            "subtitle_vs_timeline",
            "audio_vs_timeline",
        }
    )
    st_core = [str(it.get("status", "pass")).lower() for it in items if it.get("id") in _merge_ids]
    st_all = _sync_merge_item_status(*st_core) if st_core else "pass"
    if st_all == "fail":
        sw.append("sync_guard_fail")
    elif st_all == "warning":
        sw.append("sync_guard_warning")

    summary_bits = [f"status={st_all}"]
    if tl_sec is not None:
        summary_bits.append(f"tl={tl_sec:.1f}s")
    if sub_span is not None:
        summary_bits.append(f"sub={sub_span:.1f}s")
    if audio_sec is not None:
        summary_bits.append(f"aud={audio_sec:.1f}s")
    if clean_sec is not None:
        summary_bits.append(f"clean={clean_sec:.1f}s")
    if preview_sec is not None:
        summary_bits.append(f"pv={preview_sec:.1f}s")
    summary = "; ".join(summary_bits)[:240]

    return {
        "status": st_all,
        "items": items,
        "durations": {
            "timeline_seconds": tl_sec,
            "subtitle_seconds": sub_span,
            "audio_seconds": audio_sec,
            "clean_video_seconds": clean_sec,
            "preview_video_seconds": preview_sec,
        },
        "warnings": list(dict.fromkeys(sw)),
        "blocking_reasons": [],
        "summary": summary,
    }


def build_local_preview_subtitle_quality_check(result: dict) -> Dict[str, Any]:
    """BA 21.2 — Heuristischer Subtitle-/Cue-Check (Manifest + SRT, tolerant)."""
    r = result if isinstance(result, dict) else {}
    paths = r.get("paths")
    if not isinstance(paths, dict):
        paths = {}
    items: List[Dict[str, Any]] = []
    manifest_path_str = _resolve_subtitle_manifest_path(r, paths)
    mp = _safe_operator_path(manifest_path_str)
    doc: Dict[str, Any] = {}
    parse_err = ""

    if not manifest_path_str or mp is None or not mp.is_file():
        items.append(
            {
                "id": "subtitle_manifest_exists",
                "label": "Subtitle manifest exists",
                "status": "fail",
                "detail": "path missing or file not found",
                "path": manifest_path_str,
            }
        )
        for rest_id, lab in (
            ("subtitle_manifest_valid_json", "Subtitle manifest valid JSON"),
            ("subtitle_cues_present", "Subtitle cues present"),
            ("subtitle_cue_count_reasonable", "Subtitle cue count reasonable"),
            ("subtitle_cue_duration_valid", "Subtitle cue duration valid"),
            ("subtitle_cue_text_length_reasonable", "Subtitle cue text length reasonable"),
            ("subtitle_cue_word_count_reasonable", "Subtitle cue word count reasonable"),
            ("subtitle_cue_timing_order", "Subtitle cue timing order"),
        ):
            items.append(
                {"id": rest_id, "label": lab, "status": "fail", "detail": "no manifest", "path": manifest_path_str}
            )
        summary = "subtitle manifest missing"
        return {
            "status": "fail",
            "items": items,
            "warnings": ["subtitle_quality_manifest_missing"],
            "blocking_reasons": [],
            "summary": summary,
            "manifest_path": manifest_path_str,
            "cue_source": "",
            "cue_count": 0,
        }

    items.append(
        {
            "id": "subtitle_manifest_exists",
            "label": "Subtitle manifest exists",
            "status": "pass",
            "detail": "file present",
            "path": manifest_path_str,
        }
    )

    try:
        doc = json.loads(mp.read_text(encoding="utf-8", errors="replace"))
        if not isinstance(doc, dict):
            raise ValueError("not_object")
    except (OSError, json.JSONDecodeError, ValueError) as ex:
        parse_err = str(type(ex).__name__)
        items.append(
            {
                "id": "subtitle_manifest_valid_json",
                "label": "Subtitle manifest valid JSON",
                "status": "fail",
                "detail": parse_err or "parse error",
                "path": manifest_path_str,
            }
        )
        for rest_id, lab in (
            ("subtitle_cues_present", "Subtitle cues present"),
            ("subtitle_cue_count_reasonable", "Subtitle cue count reasonable"),
            ("subtitle_cue_duration_valid", "Subtitle cue duration valid"),
            ("subtitle_cue_text_length_reasonable", "Subtitle cue text length reasonable"),
            ("subtitle_cue_word_count_reasonable", "Subtitle cue word count reasonable"),
            ("subtitle_cue_timing_order", "Subtitle cue timing order"),
        ):
            items.append(
                {"id": rest_id, "label": lab, "status": "fail", "detail": "invalid manifest", "path": manifest_path_str}
            )
        return {
            "status": "fail",
            "items": items,
            "warnings": ["subtitle_quality_manifest_invalid_json"],
            "blocking_reasons": [],
            "summary": "subtitle manifest JSON invalid",
            "manifest_path": manifest_path_str,
            "cue_source": "",
            "cue_count": 0,
        }

    items.append(
        {
            "id": "subtitle_manifest_valid_json",
            "label": "Subtitle manifest valid JSON",
            "status": "pass",
            "detail": "",
            "path": manifest_path_str,
        }
    )

    cues, cue_src = _cue_list_from_manifest_doc(doc, mp)
    if not cues:
        items.append(
            {
                "id": "subtitle_cues_present",
                "label": "Subtitle cues present",
                "status": "fail",
                "detail": "no cues in manifest lists or empty/unreadable SRT",
                "path": cue_src or manifest_path_str,
            }
        )
        for rest_id, lab in (
            ("subtitle_cue_count_reasonable", "Subtitle cue count reasonable"),
            ("subtitle_cue_duration_valid", "Subtitle cue duration valid"),
            ("subtitle_cue_text_length_reasonable", "Subtitle cue text length reasonable"),
            ("subtitle_cue_word_count_reasonable", "Subtitle cue word count reasonable"),
            ("subtitle_cue_timing_order", "Subtitle cue timing order"),
        ):
            items.append(
                {"id": rest_id, "label": lab, "status": "fail", "detail": "no cues", "path": cue_src or manifest_path_str}
            )
        return {
            "status": "fail",
            "items": items,
            "warnings": ["subtitle_quality_no_cues"],
            "blocking_reasons": [],
            "summary": "no subtitle cues",
            "manifest_path": manifest_path_str,
            "cue_source": cue_src,
            "cue_count": 0,
        }

    items.append(
        {
            "id": "subtitle_cues_present",
            "label": "Subtitle cues present",
            "status": "pass",
            "detail": f"{len(cues)} cue(s)",
            "path": cue_src or manifest_path_str,
        }
    )

    n_cues = len(cues)
    if n_cues > _SUBTITLE_Q_HIGH_CUE_COUNT:
        items.append(
            {
                "id": "subtitle_cue_count_reasonable",
                "label": "Subtitle cue count reasonable",
                "status": "warning",
                "detail": f"{n_cues} cues (threshold {_SUBTITLE_Q_HIGH_CUE_COUNT})",
                "path": "",
            }
        )
    else:
        items.append(
            {
                "id": "subtitle_cue_count_reasonable",
                "label": "Subtitle cue count reasonable",
                "status": "pass",
                "detail": f"{n_cues} cues",
                "path": "",
            }
        )

    dur_fail = False
    dur_warn = False
    dur_notes: List[str] = []
    for i, c in enumerate(cues):
        st = float(c.get("start", 0.0))
        en = float(c.get("end", 0.0))
        dur = float(c.get("duration", max(en - st, 0.0)))
        if en <= st or dur < 0:
            dur_fail = True
            dur_notes.append(f"cue#{i + 1}: end<=start or negative duration")
        elif dur == 0.0:
            dur_fail = True
            dur_notes.append(f"cue#{i + 1}: zero duration")
        if dur < _SUBTITLE_Q_MIN_DUR and dur > 0 and en > st:
            dur_warn = True
            dur_notes.append(f"cue#{i + 1}: very short ({dur:.2f}s)")
        if dur > _SUBTITLE_Q_MAX_DUR:
            dur_warn = True
            dur_notes.append(f"cue#{i + 1}: very long ({dur:.2f}s)")

    if dur_fail:
        items.append(
            {
                "id": "subtitle_cue_duration_valid",
                "label": "Subtitle cue duration valid",
                "status": "fail",
                "detail": "; ".join(dur_notes[:3]) + ("…" if len(dur_notes) > 3 else ""),
                "path": "",
            }
        )
    elif dur_warn:
        items.append(
            {
                "id": "subtitle_cue_duration_valid",
                "label": "Subtitle cue duration valid",
                "status": "warning",
                "detail": "; ".join(dur_notes[:3]) + ("…" if len(dur_notes) > 3 else ""),
                "path": "",
            }
        )
    else:
        items.append(
            {
                "id": "subtitle_cue_duration_valid",
                "label": "Subtitle cue duration valid",
                "status": "pass",
                "detail": "durations in range",
                "path": "",
            }
        )

    long_chars = 0
    long_words = 0
    for c in cues:
        t = _s(c.get("text"))
        if len(t) > _SUBTITLE_Q_MAX_CHARS:
            long_chars += 1
        if len(t.split()) > _SUBTITLE_Q_MAX_WORDS:
            long_words += 1

    if long_chars:
        items.append(
            {
                "id": "subtitle_cue_text_length_reasonable",
                "label": "Subtitle cue text length reasonable",
                "status": "warning",
                "detail": f"{long_chars} cue(s) exceed {_SUBTITLE_Q_MAX_CHARS} chars",
                "path": "",
            }
        )
    else:
        items.append(
            {
                "id": "subtitle_cue_text_length_reasonable",
                "label": "Subtitle cue text length reasonable",
                "status": "pass",
                "detail": f"max {_SUBTITLE_Q_MAX_CHARS} chars ok",
                "path": "",
            }
        )

    if long_words:
        items.append(
            {
                "id": "subtitle_cue_word_count_reasonable",
                "label": "Subtitle cue word count reasonable",
                "status": "warning",
                "detail": f"{long_words} cue(s) exceed {_SUBTITLE_Q_MAX_WORDS} words",
                "path": "",
            }
        )
    else:
        items.append(
            {
                "id": "subtitle_cue_word_count_reasonable",
                "label": "Subtitle cue word count reasonable",
                "status": "pass",
                "detail": f"max {_SUBTITLE_Q_MAX_WORDS} words ok",
                "path": "",
            }
        )

    order_warn: List[str] = []
    for i in range(len(cues) - 1):
        if float(cues[i + 1].get("start", 0.0)) + 1e-6 < float(cues[i].get("start", 0.0)):
            order_warn.append("starts not monotonic in file order")
            break
    sorted_cues = sorted(cues, key=lambda x: float(x.get("start", 0.0)))
    for i in range(len(sorted_cues) - 1):
        a = sorted_cues[i]
        b = sorted_cues[i + 1]
        if float(a.get("end", 0.0)) > float(b.get("start", 0.0)) + 0.05:
            order_warn.append("overlapping cues")
            break
    if order_warn:
        items.append(
            {
                "id": "subtitle_cue_timing_order",
                "label": "Subtitle cue timing order",
                "status": "warning",
                "detail": "; ".join(dict.fromkeys(order_warn)),
                "path": "",
            }
        )
    else:
        items.append(
            {
                "id": "subtitle_cue_timing_order",
                "label": "Subtitle cue timing order",
                "status": "pass",
                "detail": "order ok",
                "path": "",
            }
        )

    has_fail = any(str(it.get("status", "")).lower() == "fail" for it in items)
    has_warn = any(str(it.get("status", "")).lower() == "warning" for it in items)
    if has_fail:
        st = "fail"
    elif has_warn:
        st = "warning"
    else:
        st = "pass"

    sw: List[str] = []
    if st == "fail":
        sw.append("subtitle_quality_fail")
    elif st == "warning":
        sw.append("subtitle_quality_warning")

    summary_parts = [f"{n_cues} cues", f"status={st}"]
    if long_words:
        summary_parts.append(f"{long_words} long-word cues")
    if long_chars:
        summary_parts.append(f"{long_chars} long-text cues")
    if order_warn:
        summary_parts.extend(list(dict.fromkeys(order_warn)))
    if dur_notes and st != "pass":
        summary_parts.append(dur_notes[0])
    summary = "; ".join(summary_parts)[:240]

    return {
        "status": st,
        "items": items,
        "warnings": sw,
        "blocking_reasons": [],
        "summary": summary,
        "manifest_path": manifest_path_str,
        "cue_source": cue_src,
        "cue_count": n_cues,
    }


def build_local_preview_quality_checklist(
    result: dict,
    *,
    _sync_guard_probe: Optional[Callable[[Path], Tuple[Optional[float], Optional[str]]]] = None,
) -> Dict[str, Any]:
    """BA 21.1 — Lokale Artefakt-/Bedienbarkeits-Checkliste (keine Video-Pixel-Analyse)."""
    r = result if isinstance(result, dict) else {}
    paths = r.get("paths")
    if not isinstance(paths, dict):
        paths = {}
    items: List[Dict[str, Any]] = []
    agg_warnings = _collect_local_preview_warnings(r)
    blocking_eff = sanitize_local_preview_blocking_reasons(r.get("blocking_reasons"))

    try:
        sq = build_local_preview_subtitle_quality_check(r)
    except Exception:
        sq = {
            "status": "fail",
            "items": [],
            "warnings": ["subtitle_quality_build_failed"],
            "blocking_reasons": [],
            "summary": "subtitle quality check error",
            "manifest_path": "",
            "cue_source": "",
            "cue_count": 0,
        }
    r["subtitle_quality_check"] = sq

    try:
        sg = build_local_preview_sync_guard(r, _probe=_sync_guard_probe)
    except Exception:
        sg = {
            "status": "fail",
            "items": [],
            "durations": {},
            "warnings": ["sync_guard_build_failed"],
            "blocking_reasons": [],
            "summary": "sync guard error",
        }
    r["sync_guard"] = sg

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

    items.append(
        {
            "id": "subtitle_quality",
            "label": "Subtitle quality",
            "status": str(sq.get("status", "fail")).lower(),
            "detail": (_s(sq.get("summary")) or "")[:220],
            "path": _s(sq.get("manifest_path") or ""),
        }
    )

    items.append(
        {
            "id": "sync_guard",
            "label": "Audio/video sync",
            "status": str(sg.get("status", "fail")).lower(),
            "detail": (_s(sg.get("summary")) or "")[:220],
            "path": "",
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
    ]
    fq = r.get("founder_quality_decision")
    if isinstance(fq, dict) and _s(fq.get("decision_code")):
        lines.extend(
            [
                "## Founder Decision (BA 21.5)",
                f"- **Entscheidung:** `{_s(fq.get('decision_code'))}` — {_s(fq.get('decision_label_de'))}",
                f"- **Top-Thema:** {_s(fq.get('top_issue'))}",
                f"- **Nächster Schritt:** {_s(fq.get('next_step'))}",
                "",
            ]
        )
    lines.extend(
        [
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
    )
    if tw:
        for w in tw:
            lines.append(f"- {w}")
    else:
        lines.append("- Keine")

    wc = r.get("warning_classification")
    if isinstance(wc, dict):
        hi = _s(wc.get("highest")) or "INFO"
        summ = _s(wc.get("summary")) or ""
        lines.extend(["", "## Warning Levels (BA 21.4)", f"Höchste Stufe: **{hi}**", summ, ""])

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

    sq = r.get("subtitle_quality_check")
    if isinstance(sq, dict) and sq.get("status"):
        lines.extend(["", "## Subtitle Quality"])
        lines.append(f"- Status: {str(sq.get('status')).upper()}")
        hint = _s(sq.get("summary"))
        if hint:
            lines.append(f"- Hinweis: {hint[:200]}")
        lines.append("")

    sg = r.get("sync_guard")
    if isinstance(sg, dict) and sg.get("status"):
        lines.extend(["", "## Sync Guard"])
        lines.append(f"- Status: {str(sg.get('status')).upper()}")
        dur = sg.get("durations") if isinstance(sg.get("durations"), dict) else {}
        aud = dur.get("audio_seconds")
        hint2 = _s(sg.get("summary"))
        if not isinstance(aud, (int, float)):
            lines.append("- Hinweis: Kein Audio vorhanden; Silent Render verwendet.")
        elif hint2:
            lines.append(f"- Hinweis: {hint2[:200]}")
        lines.append("")

    fq_ns = r.get("founder_quality_decision")
    nxt_line = (
        _s(fq_ns.get("next_step"))
        if isinstance(fq_ns, dict) and _s(fq_ns.get("next_step"))
        else local_preview_next_step_for_verdict(verdict)
    )
    lines.extend(["", "## Next Step", nxt_line, ""])
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
    ]
    fq = r.get("founder_quality_decision")
    if isinstance(fq, dict) and _s(fq.get("decision_code")):
        sig = fq.get("signals")
        sig_bits: List[str] = []
        if isinstance(sig, dict):
            for k, lab in (
                ("verdict", "Verdict"),
                ("quality_checklist", "Quality"),
                ("subtitle_quality", "Subtitle"),
                ("sync_guard", "Sync"),
                ("warning_level_highest", "Warnstufe"),
            ):
                v = _s(sig.get(k))
                if v:
                    sig_bits.append(f"{lab}={v}")
        lines.extend(
            [
                "## Founder Decision (BA 21.5)",
                f"- **Entscheidung:** `{_s(fq.get('decision_code'))}` — {_s(fq.get('decision_label_de'))}",
                f"- **Top-Thema:** {_s(fq.get('top_issue'))}",
                f"- **Nächster Schritt:** {_s(fq.get('next_step'))}",
            ]
        )
        fac = fq.get("factors_de")
        if isinstance(fac, list) and fac:
            lines.append("- **Faktoren:**")
            for bit in fac[:8]:
                b = _s(bit)
                if b:
                    lines.append(f"  - {b}")
        if sig_bits:
            lines.append(f"- **Signale:** {', '.join(sig_bits)}")
        lines.append("")
    lines.extend(
        [
        "## Preview",
        f"Preview erzeugt: **{'ja' if preview_yes else 'nein'}**",
        f"Datei öffnen: `{open_path}`",
        "",
        "## Run",
        f"Run ID: `{run_id}`",
        f"Pipeline Ordner: `{pipeline_dir}`",
        "",
        "## Steps",
        ],
    )
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

    wc = r.get("warning_classification")
    if isinstance(wc, dict):
        hi = _s(wc.get("highest")) or "INFO"
        summ = _s(wc.get("summary")) or ""
        lines.extend(
            [
                "",
                "## Warning Classification (BA 21.4)",
                f"Höchste Stufe: **{hi}**",
                f"Übersicht: {summ}",
                "",
            ]
        )
        witems = wc.get("items")
        if isinstance(witems, list) and witems:
            lines.append("Klassifizierte Codes:")
            for idx, it in enumerate(witems):
                if idx >= 40:
                    lines.append(f"- … ({len(witems) - 40} weitere)")
                    break
                if not isinstance(it, dict):
                    continue
                cod = _s(it.get("code"))
                lv = _s(it.get("level"))
                if cod:
                    lines.append(f"- [{lv}] `{cod}`")
            lines.append("")

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

    sq = r.get("subtitle_quality_check")
    if isinstance(sq, dict) and sq.get("status"):
        lines.extend(["", "## Subtitle Quality"])
        lines.append(f"- Status: **{str(sq.get('status')).upper()}**")
        ssum = _s(sq.get("summary"))
        if ssum:
            lines.append(f"- Summary: {ssum}")
        shown = 0
        for it in sq.get("items") or []:
            if shown >= 5:
                break
            if not isinstance(it, dict):
                continue
            if str(it.get("status", "")).lower() == "pass":
                continue
            tag = str(it.get("status", "fail")).upper()
            lab = _s(it.get("label")) or _s(it.get("id"))
            det = _s(it.get("detail"))
            lines.append(f"- [{tag}] {lab}" + (f" — {det}" if det else ""))
            shown += 1
        lines.append("")

    sg = r.get("sync_guard")
    if isinstance(sg, dict) and sg.get("status"):
        lines.extend(["", "## Sync Guard"])
        lines.append(f"Status: **{str(sg.get('status')).upper()}**")
        dur = sg.get("durations") if isinstance(sg.get("durations"), dict) else {}
        tl = dur.get("timeline_seconds")
        sub = dur.get("subtitle_seconds")
        aud = dur.get("audio_seconds")
        cl = dur.get("clean_video_seconds")
        pv = dur.get("preview_video_seconds")
        lines.append(f"- Timeline: {tl:.1f}s" if isinstance(tl, (int, float)) else "- Timeline: nicht verfügbar")
        lines.append(f"- Subtitle: {sub:.1f}s" if isinstance(sub, (int, float)) else "- Subtitle: nicht verfügbar")
        lines.append(f"- Audio: {aud:.1f}s" if isinstance(aud, (int, float)) else "- Audio: nicht verfügbar")
        lines.append(f"- Clean: {cl:.1f}s" if isinstance(cl, (int, float)) else "- Clean: nicht verfügbar")
        lines.append(f"- Preview: {pv:.1f}s" if isinstance(pv, (int, float)) else "- Preview: nicht verfügbar")
        ssum2 = _s(sg.get("summary"))
        if not isinstance(aud, (int, float)):
            lines.append("- Hinweis: Kein Audio vorhanden; Silent Render verwendet.")
        elif ssum2:
            lines.append(f"- Hinweis: {ssum2[:220]}")
        shown_g = 0
        for it in sg.get("items") or []:
            if shown_g >= 5:
                break
            if not isinstance(it, dict):
                continue
            if str(it.get("status", "")).lower() == "pass":
                continue
            tag = str(it.get("status", "fail")).upper()
            lab = _s(it.get("label")) or _s(it.get("id"))
            det = _s(it.get("detail"))
            lines.append(f"- [{tag}] {lab}" + (f" — {det}" if det else ""))
            shown_g += 1
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
    Founder Report (BA 20.10), OPEN_ME (BA 20.12), Quality Checklist (BA 21.1 / 21.2 / 21.3),
    Warn-Klassifikation (BA 21.4), Founder-Entscheidung (BA 21.5).

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
    try:
        out["warning_classification"] = build_local_preview_warning_classification(out)
    except Exception:
        w = _list_str(out.get("warnings"))
        w.append("warning_classification_build_failed")
        out["warnings"] = w
        out["warning_classification"] = {
            "highest": "WARNING",
            "counts": {"INFO": 0, "CHECK": 0, "WARNING": 1, "BLOCKING": 0},
            "items": [{"code": "warning_classification_build_failed", "level": "WARNING"}],
            "summary": "1 WARNING",
        }
    try:
        out["founder_quality_decision"] = build_founder_quality_decision(out)
    except Exception:
        w = _list_str(out.get("warnings"))
        w.append("founder_quality_decision_build_failed")
        out["warnings"] = w
        vd = compute_local_preview_verdict(out)
        out["founder_quality_decision"] = {
            "decision_code": "REVIEW_REQUIRED",
            "decision_label_de": "Founder-Entscheidungsschicht fehlgeschlagen — Rohdaten prüfen.",
            "top_issue": "founder_quality_decision_build_failed",
            "next_step": local_preview_next_step_for_verdict(vd),
            "signals": {},
            "factors_de": [f"Verdict: {vd}"],
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
    tl_path_resolved = str(Path(timeline_manifest).resolve())

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
                    "timeline_manifest": tl_path_resolved,
                    "audio_path": (
                        str(Path(audio_path).resolve())
                        if audio_path
                        else _s(step_build.get("audio_path"))
                    ),
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
                    "timeline_manifest": tl_path_resolved,
                    "audio_path": _s(step_build.get("audio_path")),
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
            "timeline_manifest": tl_path_resolved,
            "audio_path": _s(step_build.get("audio_path")),
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
