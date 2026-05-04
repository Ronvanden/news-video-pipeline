"""BA 20.6 / BA 20.6a / BA 20.6b / BA 20.6c — subtitles.srt + Manifest → Preview-MP4 (Render-Contract, SRT/ASS)."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, NamedTuple, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_VALID_STYLES = frozenset({"classic", "word_by_word", "typewriter", "karaoke", "none"})

# BA 20.6c — heuristische Kennzeichnung bereits gebrannter Preview-Quellen (kein Pixel-Check)
_INPUT_SUSPECT_BURNIN_SUBSTRINGS = (
    "preview_with_subtitles",
    "subtitle_burnin",
    "with_subtitles",
    "burned",
)


def _write_burnin_output_manifest_json(out_dir: Path, meta: Dict[str, Any]) -> Optional[str]:
    """BA 20.7 — burnin_output_manifest.json nach erfolgreichem Lauf (ok True)."""
    p = out_dir / "burnin_output_manifest.json"
    body = {
        "ok": True,
        "clean_input_video_path": meta.get("input_video") or "",
        "subtitle_burnin_video_path": meta.get("output_video_path") or "",
        "subtitle_delivery_mode": meta.get("subtitle_delivery_mode") or "none",
        "subtitle_style": meta.get("subtitle_style") or "none",
        "renderer_used": meta.get("renderer_used") or "none",
        "ass_subtitle_path": meta.get("ass_subtitle_path") or "",
        "subtitles_srt_path": meta.get("subtitles_srt_path") or "",
        "input_video_role": meta.get("input_video_role") or "clean_candidate",
        "clean_video_required": bool(meta.get("clean_video_required")),
        "warnings": list(meta.get("warnings") or []),
    }
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(body, ensure_ascii=False, indent=2), encoding="utf-8")
        return str(p.resolve())
    except OSError:
        return None


def _classify_input_video_role(path: Path) -> Tuple[str, List[str]]:
    """Pfad/Dateiname → clean_candidate oder possibly_burned + ggf. Warnung."""
    warns: List[str] = []
    try:
        s = path.resolve().as_posix().lower()
    except OSError:
        s = path.as_posix().lower()
    if any(tok in s for tok in _INPUT_SUSPECT_BURNIN_SUBSTRINGS):
        warns.append("input_video_may_already_have_burned_subtitles")
        return "possibly_burned", warns
    return "clean_candidate", warns


# BA 20.6a — libass force_style (Kommas im Filter als \, escapen)
_SUBTITLE_BURNIN_FORCE_STYLE_RAW = (
    "FontName=Arial,FontSize=22,"
    "PrimaryColour=&H00FFFFFF&,OutlineColour=&H00000000&,"
    "BorderStyle=1,Outline=2,Shadow=1,"
    "Alignment=2,MarginV=45,MarginL=40,MarginR=40"
)


def _ffmpeg_escape_subtitle_file_path(p: Path) -> str:
    s = p.resolve().as_posix()
    s = s.replace("\\", "/")
    s = s.replace(":", r"\:")
    s = s.replace("'", r"\'")
    s = s.replace(",", r"\,")
    s = s.replace("[", r"\[")
    s = s.replace("]", r"\]")
    return s


def _build_ffmpeg_subtitle_filter(srt_path: Path) -> str:
    """Voller subtitles=…-Ausdruck inkl. force_style (BA 20.6a Safe Style)."""
    pe = _ffmpeg_escape_subtitle_file_path(srt_path)
    st = _SUBTITLE_BURNIN_FORCE_STYLE_RAW.replace(",", r"\,")
    return f"subtitles='{pe}':force_style={st}"


def _build_ffmpeg_ass_filter(ass_path: Path) -> str:
    """BA 20.6b — libass ass= mit escapetem Pfad (Windows-kompatibel)."""
    pe = _ffmpeg_escape_subtitle_file_path(ass_path)
    return f"ass='{pe}'"


class SubtitleCue(NamedTuple):
    index: int
    start_seconds: float
    end_seconds: float
    text: str


_SRT_TS_LINE = re.compile(
    r"^\s*(\d{1,2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{1,2}):(\d{2}):(\d{2})[,.](\d{3})\s*$"
)


def _srt_hmsf_to_seconds(h: str, m: str, s: str, f: str) -> float:
    return int(h) * 3600 + int(m) * 60 + int(s) + int(f) / 1000.0


def _parse_srt_cues(srt_path: Path) -> List[SubtitleCue]:
    """SRT → Cues (Index, Start/End in Sekunden, Fließtext)."""
    raw = srt_path.read_text(encoding="utf-8", errors="replace")
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    stripped = raw.strip()
    if not stripped:
        return []
    blocks = re.split(r"\n\s*\n", stripped)
    cues: List[SubtitleCue] = []
    for block in blocks:
        lines = [ln for ln in block.split("\n") if ln is not None]
        if not lines:
            continue
        idx_line = 0
        if lines[0].strip().isdigit():
            try:
                idx = int(lines[0].strip())
            except ValueError:
                idx = len(cues) + 1
            time_line_idx = 1
        else:
            idx = len(cues) + 1
            time_line_idx = 0
        if time_line_idx >= len(lines):
            continue
        m = _SRT_TS_LINE.match(lines[time_line_idx].strip() or "")
        if not m:
            continue
        t0 = _srt_hmsf_to_seconds(m.group(1), m.group(2), m.group(3), m.group(4))
        t1 = _srt_hmsf_to_seconds(m.group(5), m.group(6), m.group(7), m.group(8))
        text_lines = lines[time_line_idx + 1 :]
        text = " ".join(t.strip() for t in text_lines if t.strip())
        cues.append(SubtitleCue(index=idx, start_seconds=t0, end_seconds=max(t1, t0 + 0.04), text=text))
    return cues


def _format_ass_timestamp(seconds: float) -> str:
    """ASS-Zeit H:MM:SS.cc (Hundertstelsekunden)."""
    total_cs = int(max(0.0, seconds) * 100.0 + 0.5)
    h = total_cs // 360000
    rem = total_cs % 360000
    m = rem // 6000
    rem %= 6000
    s = rem // 100
    cs = rem % 100
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _escape_ass_text(text: str) -> str:
    """Dialog-Text für ASS: Backslash, geschweifte Klammern, Zeilenumbrüche."""
    t = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    t = t.replace("\\", r"\\")
    t = t.replace("{", r"\{").replace("}", r"\}")
    t = t.replace("\n", r"\N")
    return t


def _wrap_typewriter_visible_text(text: str, max_chars: int = 34) -> str:
    """Nur sichtbaren Prefix auf max. zwei Zeilen umbrechen (ohne vorausliegende Restzeile)."""
    if not text:
        return ""
    if len(text) <= max_chars:
        return text
    cut = max_chars
    sp = text.rfind(" ", 0, cut + 1)
    if sp > max_chars // 3:
        first, rest = text[:sp].rstrip(), text[sp + 1 :].lstrip()
    else:
        first, rest = text[:cut], text[cut:]
    if len(rest) <= max_chars:
        return first + r"\N" + rest
    return first + r"\N" + rest[:max_chars]


def _build_typewriter_ass_file(
    cues: List[SubtitleCue],
    ass_path: Path,
    *,
    font_size: int = 22,
    margin_v: int = 45,
    max_chars_per_line: int = 34,
    min_frame_duration: float = 0.035,
) -> Dict[str, Any]:
    """Schreibt preview_typewriter.ass mit progressiven Dialogue-Zeilen pro Cue."""
    warns: List[str] = []
    if not cues:
        return {"ok": False, "error": "no_cues", "warnings": warns, "dialogue_count": 0}

    header = (
        "[Script Info]\n"
        "Title: preview_typewriter\n"
        "ScriptType: v4.00+\n"
        "WrapStyle: 0\n"
        "ScaledBorderAndShadow: yes\n"
        "\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
        "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Default,Arial,{font_size},"
        "&H00FFFFFF,&H00000000,&H00000000,&H80000000,"
        "0,0,0,0,100,100,0,0,1,2,1,2,40,40,{margin_v},1\n"
        "\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )

    events: List[str] = []
    for cue in cues:
        full = (cue.text or "").strip()
        if not full:
            continue
        t0, t1 = float(cue.start_seconds), float(cue.end_seconds)
        duration = max(t1 - t0, min_frame_duration * 2.0)
        chars = list(full)
        n = len(chars)
        if n == 0:
            continue
        for i in range(n):
            prefix = "".join(chars[: i + 1])
            vis = _wrap_typewriter_visible_text(prefix, max_chars_per_line)
            txt = _escape_ass_text(vis)
            start = t0 + duration * (i / max(n, 1))
            end = t0 + duration * ((i + 1) / max(n, 1))
            if i == n - 1:
                end = t1
            start = max(t0, min(start, t1 - min_frame_duration))
            end = max(start + min_frame_duration, min(end, t1))
            if end <= start:
                end = min(t1, start + min_frame_duration)
            events.append(
                "Dialogue: 0,"
                + _format_ass_timestamp(start)
                + ","
                + _format_ass_timestamp(end)
                + ",Default,,0,0,0,,{\\an2}"
                + txt
                + "\n"
            )

    if not events:
        return {"ok": False, "error": "no_events", "warnings": warns, "dialogue_count": 0}

    body = header + "".join(events)
    try:
        ass_path.parent.mkdir(parents=True, exist_ok=True)
        ass_path.write_text(body, encoding="utf-8")
    except OSError as e:
        return {
            "ok": False,
            "error": f"write_failed:{type(e).__name__}",
            "warnings": warns,
            "dialogue_count": 0,
        }

    return {
        "ok": True,
        "warnings": warns,
        "dialogue_count": len(events),
        "path": str(ass_path.resolve()),
    }


def _wrap_words_to_max_line_len(text: str, max_len: int) -> List[str]:
    """Wortweise umbrechen; einzelne Tokens länger als max_len hart umbrechen."""
    words = (text or "").replace("\n", " ").split()
    if not words:
        return []
    lines: List[str] = []
    cur: List[str] = []
    cur_len = 0
    for w in words:
        if len(w) > max_len:
            if cur:
                lines.append(" ".join(cur))
                cur = []
                cur_len = 0
            for i in range(0, len(w), max_len):
                chunk = w[i : i + max_len]
                lines.append(chunk)
            continue
        add = len(w) + (1 if cur else 0)
        if cur_len + add <= max_len:
            cur.append(w)
            cur_len += add
        else:
            lines.append(" ".join(cur))
            cur = [w]
            cur_len = len(w)
    if cur:
        lines.append(" ".join(cur))
    return lines


def _srt_wrap_cues_for_burnin(content: str, max_line_len: int = 42) -> Tuple[str, bool]:
    """Nur Textzeilen innerhalb von Cues umbrechen; Index- und Zeitzeilen unverändert."""
    raw = content.replace("\r\n", "\n").replace("\r", "\n")
    stripped = raw.strip()
    if not stripped:
        return raw, False
    blocks = re.split(r"\n\s*\n", stripped)
    changed = False
    out_blocks: List[str] = []
    time_re = re.compile(
        r"^\s*\d{1,2}:\d{2}:\d{2}[,.]\d{3}\s*-->\s*\d{1,2}:\d{2}:\d{2}[,.]\d{3}\s*$"
    )

    for block in blocks:
        lines = block.split("\n")
        if not lines:
            continue
        if len(lines) >= 2 and lines[0].strip().isdigit() and time_re.match(lines[1].strip() or ""):
            header, text_lines = lines[:2], lines[2:]
        elif len(lines) >= 1 and time_re.match(lines[0].strip() or ""):
            header, text_lines = lines[:1], lines[1:]
        else:
            out_blocks.append(block)
            continue

        parts = [t.strip() for t in text_lines if t.strip()]
        if not parts:
            out_blocks.append("\n".join(header))
            continue

        joined = " ".join(parts)
        max_incoming = max(len(t) for t in parts)
        if len(joined) <= max_line_len and max_incoming <= max_line_len:
            out_blocks.append("\n".join(header + text_lines))
            continue

        wrapped = _wrap_words_to_max_line_len(joined, max_line_len)
        old_text = "\n".join(text_lines).strip()
        new_text = "\n".join(wrapped).strip()
        if new_text != old_text:
            changed = True
        out_blocks.append("\n".join(header + wrapped))

    out = "\n\n".join(out_blocks)
    if not out.endswith("\n"):
        out += "\n"
    return out, changed


def _normalize_manifest_style(raw: Any) -> Tuple[str, List[str]]:
    warns: List[str] = []
    v = str(raw or "classic").strip().lower().replace("-", "_")
    if v not in _VALID_STYLES:
        warns.append(f"subtitle_style_unknown_defaulting_classic:{(raw or '')!r}")
        return "classic", warns
    return v, warns


def _resolve_srt_path(manifest: Dict[str, Any], manifest_path: Path) -> Optional[Path]:
    p = manifest.get("subtitles_srt_path")
    if p:
        cand = Path(str(p)).resolve()
        if cand.is_file() and cand.stat().st_size > 0:
            return cand
    sib = (manifest_path.parent / "subtitles.srt").resolve()
    if sib.is_file() and sib.stat().st_size > 0:
        return sib
    return None


def _video_has_audio_stream(video: Path, ffprobe: Optional[str]) -> bool:
    if not ffprobe:
        return True
    try:
        r = subprocess.run(
            [
                ffprobe,
                "-v",
                "error",
                "-select_streams",
                "a:0",
                "-show_entries",
                "stream=index",
                "-of",
                "csv=p=0",
                str(video),
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        return r.returncode == 0 and (r.stdout or "").strip() != ""
    except (OSError, subprocess.TimeoutExpired):
        return True


def burn_in_subtitles_preview(
    input_video: Path,
    subtitle_manifest: Path,
    *,
    out_root: Path,
    run_id: str,
    force: bool,
    ffmpeg_bin: Optional[str] = None,
    subprocess_run: Optional[Callable[..., Any]] = None,
    shutil_which: Optional[Callable[[str], Optional[str]]] = None,
) -> Dict[str, Any]:
    """Manifest → ffmpeg-Burn-in; `subprocess_run` / `shutil_which` für Tests injizierbar."""
    run_fn = subprocess_run or subprocess.run
    which_fn = shutil_which or shutil.which

    warnings: List[str] = []
    blocking: List[str] = []
    rid = (run_id or "").strip() or str(uuid.uuid4())
    out_root_p = Path(out_root).resolve()
    man_path = Path(subtitle_manifest).resolve()
    invid = Path(input_video).resolve()
    out_dir = out_root_p / f"subtitle_burnin_{rid}"
    out_mp4 = out_dir / "preview_with_subtitles.mp4"

    input_video_role, burnin_path_warns = _classify_input_video_role(invid)
    warnings.extend(burnin_path_warns)

    def _render_contract(sty: str, skipped: bool, ok_output_written: bool) -> Dict[str, Any]:
        """BA 20.6c — Rollen und Liefermodus (Clean-Video-Contract)."""
        if sty == "none" and skipped:
            return {
                "input_video_role": input_video_role,
                "output_video_role": "",
                "subtitle_delivery_mode": "none",
                "clean_video_required": False,
            }
        return {
            "input_video_role": input_video_role,
            "output_video_role": ("subtitle_burnin_preview" if ok_output_written else ""),
            "subtitle_delivery_mode": "burn_in",
            "clean_video_required": True,
        }

    def pack(
        *,
        ok: bool,
        skipped: bool,
        srt_path_str: str,
        out_video: str,
        style: str,
        fallback: bool,
        ass_subtitle_path: str = "",
        renderer_used: str = "srt_burnin",
        contract_style: str = "classic",
        contract_skipped: bool = False,
        contract_ok_output: bool = False,
    ) -> Dict[str, Any]:
        base: Dict[str, Any] = {
            "ok": ok,
            "skipped": skipped,
            "run_id": rid,
            "output_dir": str(out_dir),
            "input_video": str(invid),
            "subtitle_manifest_path": str(man_path),
            "subtitles_srt_path": srt_path_str,
            "output_video_path": out_video,
            "subtitle_style": style,
            "fallback_used": fallback,
            "ass_subtitle_path": ass_subtitle_path,
            "renderer_used": renderer_used,
            "warnings": list(warnings),
            "blocking_reasons": list(blocking),
        }
        base.update(_render_contract(contract_style, contract_skipped, contract_ok_output))
        if base.get("ok") is True:
            mp = _write_burnin_output_manifest_json(out_dir, base)
            if mp:
                base["burnin_output_manifest_path"] = mp
        return base

    try:
        raw = man_path.read_text(encoding="utf-8", errors="replace")
        manifest = json.loads(raw)
        if not isinstance(manifest, dict):
            raise ValueError("manifest_not_object")
    except (OSError, json.JSONDecodeError, ValueError):
        warnings.append("subtitle_manifest_parse_failed")
        blocking.append("subtitle_manifest_parse_failed")
        return pack(
            ok=False,
            skipped=False,
            srt_path_str="",
            out_video=str(out_mp4),
            style="classic",
            fallback=False,
            ass_subtitle_path="",
            renderer_used="srt_burnin",
            contract_style="classic",
            contract_skipped=False,
            contract_ok_output=False,
        )

    style_norm, sw = _normalize_manifest_style(manifest.get("subtitle_style"))
    warnings.extend(sw)

    ffmpeg = ffmpeg_bin if ffmpeg_bin is not None else which_fn("ffmpeg")
    if not ffmpeg:
        warnings.append("ffmpeg_missing")
        blocking.append("ffmpeg_missing")
        return pack(
            ok=False,
            skipped=False,
            srt_path_str="",
            out_video=str(out_mp4),
            style=style_norm,
            fallback=False,
            ass_subtitle_path="",
            renderer_used="srt_burnin",
            contract_style=style_norm,
            contract_skipped=False,
            contract_ok_output=False,
        )

    if not invid.is_file():
        warnings.append("input_video_missing")
        blocking.append("input_video_missing")
        return pack(
            ok=False,
            skipped=False,
            srt_path_str="",
            out_video=str(out_mp4),
            style=style_norm,
            fallback=False,
            ass_subtitle_path="",
            renderer_used="srt_burnin",
            contract_style=style_norm,
            contract_skipped=False,
            contract_ok_output=False,
        )

    srt_path = _resolve_srt_path(manifest, man_path)
    srt_str = str(srt_path) if srt_path else ""

    if style_norm == "none":
        warnings.append("subtitle_style_none_skipped")
        return pack(
            ok=True,
            skipped=True,
            srt_path_str=srt_str,
            out_video="",
            style=style_norm,
            fallback=False,
            ass_subtitle_path="",
            renderer_used="none",
            contract_style=style_norm,
            contract_skipped=True,
            contract_ok_output=False,
        )

    if srt_path is None or not srt_path.is_file() or srt_path.stat().st_size == 0:
        warnings.append("subtitles_srt_missing")
        blocking.append("subtitles_srt_missing")
        return pack(
            ok=False,
            skipped=False,
            srt_path_str=srt_str,
            out_video=str(out_mp4),
            style=style_norm,
            fallback=False,
            ass_subtitle_path="",
            renderer_used="srt_burnin",
            contract_style=style_norm,
            contract_skipped=False,
            contract_ok_output=False,
        )

    if input_video_role == "possibly_burned" and not force:
        blocking.append("input_video_possibly_burned_subtitles_use_clean_or_force")
        return pack(
            ok=False,
            skipped=False,
            srt_path_str=str(srt_path),
            out_video=str(out_mp4),
            style=style_norm,
            fallback=False,
            ass_subtitle_path="",
            renderer_used="srt_burnin",
            contract_style=style_norm,
            contract_skipped=False,
            contract_ok_output=False,
        )

    fallback_used = False
    if style_norm == "word_by_word":
        warnings.append("subtitle_style_word_by_word_rendered_as_srt")
        fallback_used = True
    elif style_norm == "karaoke":
        warnings.append("subtitle_style_karaoke_fallback_to_srt_burnin")
        fallback_used = True

    out_dir.mkdir(parents=True, exist_ok=True)

    ass_subtitle_path = ""
    renderer_used = "srt_burnin"
    typewriter_ass_ok = False

    if style_norm == "typewriter":
        try:
            cues = _parse_srt_cues(srt_path)
            ass_p = out_dir / "preview_typewriter.ass"
            tw = _build_typewriter_ass_file(
                cues,
                ass_p,
                font_size=22,
                margin_v=45,
                max_chars_per_line=34,
                min_frame_duration=0.035,
            )
            if tw.get("ok"):
                typewriter_ass_ok = True
                ass_subtitle_path = str(ass_p.resolve())
                renderer_used = "ass_typewriter"
                warnings.extend(tw.get("warnings") or [])
                warnings.append("subtitle_typewriter_ass_renderer_used")
            else:
                warnings.append("subtitle_typewriter_ass_failed_fallback_srt")
                fallback_used = True
        except (OSError, ValueError, TypeError):
            warnings.append("subtitle_typewriter_ass_failed_fallback_srt")
            fallback_used = True

    if out_mp4.is_file() and not force:
        blocking.append("preview_with_subtitles_already_exists")
        warnings.append("preview_with_subtitles_already_exists")
        return pack(
            ok=False,
            skipped=False,
            srt_path_str=str(srt_path),
            out_video=str(out_mp4),
            style=style_norm,
            fallback=fallback_used,
            ass_subtitle_path=ass_subtitle_path,
            renderer_used=renderer_used,
            contract_style=style_norm,
            contract_skipped=False,
            contract_ok_output=False,
        )

    srt_for_ffmpeg = srt_path
    vf: str
    if typewriter_ass_ok and ass_subtitle_path:
        vf = _build_ffmpeg_ass_filter(Path(ass_subtitle_path))
    else:
        warnings.append("subtitle_burnin_safe_style_applied")
        try:
            srt_raw = srt_path.read_text(encoding="utf-8", errors="replace")
            wrapped_body, wrap_changed = _srt_wrap_cues_for_burnin(srt_raw)
            if wrap_changed:
                wrapped_path = out_dir / "preview_subtitles_wrapped.srt"
                wrapped_path.write_text(wrapped_body, encoding="utf-8")
                srt_for_ffmpeg = wrapped_path
                warnings.append("subtitle_srt_wrapped_for_burnin")
        except OSError:
            pass
        vf = _build_ffmpeg_subtitle_filter(srt_for_ffmpeg)
    ffprobe = which_fn("ffprobe")
    cmd: List[str] = [
        ffmpeg,
        "-y",
        "-i",
        str(invid),
        "-vf",
        vf,
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-preset",
        "fast",
        "-crf",
        "23",
    ]
    if _video_has_audio_stream(invid, ffprobe):
        cmd.extend(["-c:a", "aac", "-b:a", "192k"])
    else:
        cmd.append("-an")
    cmd.append(str(out_mp4))

    try:
        run_fn(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        err = (e.stderr or e.stdout or "")[:500]
        warnings.append(f"ffmpeg_burnin_failed:{err}")
        blocking.append("ffmpeg_encode_failed")
        return pack(
            ok=False,
            skipped=False,
            srt_path_str=str(srt_path),
            out_video=str(out_mp4),
            style=style_norm,
            fallback=fallback_used,
            ass_subtitle_path=ass_subtitle_path,
            renderer_used=renderer_used,
            contract_style=style_norm,
            contract_skipped=False,
            contract_ok_output=False,
        )

    return pack(
        ok=True,
        skipped=False,
        srt_path_str=str(srt_path),
        out_video=str(out_mp4),
        style=style_norm,
        fallback=fallback_used,
        ass_subtitle_path=ass_subtitle_path,
        renderer_used=renderer_used,
        contract_style=style_norm,
        contract_skipped=False,
        contract_ok_output=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="BA 20.6 / BA 20.6a / BA 20.6b — subtitle_manifest → preview_with_subtitles.mp4 (SRT safe style, typewriter: ASS)"
    )
    parser.add_argument("--input-video", type=Path, required=True, dest="input_video")
    parser.add_argument("--subtitle-manifest", type=Path, required=True, dest="subtitle_manifest")
    parser.add_argument("--out-root", type=Path, default=ROOT / "output", dest="out_root")
    parser.add_argument("--run-id", default="", dest="run_id")
    parser.add_argument(
        "--force",
        action="store_true",
        dest="force",
        help="Vorhandenes preview_with_subtitles.mp4 überschreiben; umgeht Block bei Verdacht auf bereits eingebrannte Untertitel in der Quelle (BA 20.6c)",
    )
    args = parser.parse_args()

    meta = burn_in_subtitles_preview(
        args.input_video,
        args.subtitle_manifest,
        out_root=args.out_root,
        run_id=(args.run_id or "").strip() or str(uuid.uuid4()),
        force=bool(args.force),
    )
    print(json.dumps(meta, ensure_ascii=False, indent=2))
    return 0 if meta.get("ok") else 3


if __name__ == "__main__":
    raise SystemExit(main())
