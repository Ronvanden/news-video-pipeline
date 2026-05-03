"""BA 20.5 / BA 20.5b / BA 20.5c — Narration oder Audio-Transkription → SRT + subtitle_manifest.json."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import httpx

from app.utils import count_words

DEFAULT_WPM = 145.0
OPENAI_TRANSCRIPTIONS_URL = "https://api.openai.com/v1/audio/transcriptions"

# BA 20.5b: Narration-Cues
MAX_CUE_CHARS = 48
MAX_LINE_LEN = 24
MAX_WORDS_PER_CUE = 10

# BA 20.5c: aus Transkription — kürzer
MAX_CUE_CHARS_AUDIO = 42
MAX_LINE_LEN_AUDIO = 21
MAX_WORDS_AUDIO_CUE = 8

_VALID_SUBTITLE_STYLES = frozenset({"classic", "word_by_word", "typewriter", "karaoke", "none"})


def _normalize_subtitle_style(value: str) -> str:
    """CLI-Wert → kanonischen Style (ungültig → classic)."""
    v = (value or "classic").strip().lower().replace("-", "_")
    return v if v in _VALID_SUBTITLE_STYLES else "classic"


def _chunk_body_for_subtitle_style(style_norm: str, body: str) -> List[str]:
    """SRT-Chunking abhängig vom Style-Vertrag (V1: weiterhin SRT ohne Wort-Timestamps)."""
    if style_norm in ("word_by_word", "typewriter"):
        return _split_into_caption_chunks_audio(body)
    if style_norm in ("none",):
        return []
    return _split_into_caption_chunks(body)


def _build_subtitle_render_contract(
    style_norm: str,
    *,
    transcription_used: bool,
    subtitle_source_effective: str,
    fallback_from_audio: bool,
) -> Dict[str, Any]:
    """BA 20.5d — Vertrag für künftige Renderer; kein echtes Karaoke/Typewriter-Rendering in V1."""
    short_cue_profile = transcription_used or (
        subtitle_source_effective == "audio" and not fallback_from_audio
    )
    cw: List[str] = []

    if style_norm == "classic":
        mwp = 8 if short_cue_profile else 10
        return {
            "style": "classic",
            "recommended_renderer": "libass_srt",
            "requires_word_timing": False,
            "requires_character_timing": False,
            "max_words_per_cue": mwp,
            "fallback_style": "classic",
            "warnings": list(cw),
        }
    if style_norm == "word_by_word":
        cw.append("word_by_word_requires_word_level_timing_not_in_srt_v1")
        return {
            "style": "word_by_word",
            "recommended_renderer": "future_word_timed_renderer",
            "requires_word_timing": True,
            "requires_character_timing": False,
            "max_words_per_cue": 8,
            "fallback_style": "classic",
            "warnings": list(cw),
        }
    if style_norm == "typewriter":
        cw.append("typewriter_v1_contract_only_srt_has_line_timing_only")
        return {
            "style": "typewriter",
            "recommended_renderer": "future_typewriter_renderer",
            "requires_word_timing": False,
            "requires_character_timing": True,
            "max_words_per_cue": 6,
            "fallback_style": "word_by_word",
            "warnings": list(cw),
        }
    if style_norm == "karaoke":
        cw.append("karaoke_requires_word_timing_srt_v1_line_timing_only")
        return {
            "style": "karaoke",
            "recommended_renderer": "libass_or_future_karaoke",
            "requires_word_timing": True,
            "requires_character_timing": False,
            "max_words_per_cue": 8,
            "fallback_style": "classic",
            "warnings": list(cw),
        }
    # none
    cw.append("subtitle_style_none_contract_only")
    return {
        "style": "none",
        "recommended_renderer": "none",
        "requires_word_timing": False,
        "requires_character_timing": False,
        "max_words_per_cue": 0,
        "fallback_style": "classic",
        "warnings": list(cw),
    }


def load_timeline_manifest_optional(path: Optional[Path]) -> Optional[Dict[str, Any]]:
    if not path:
        return None
    p = path.resolve()
    if not p.is_file():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def _timeline_duration_seconds(tl: Dict[str, Any]) -> float:
    scenes = tl.get("scenes") or []
    if isinstance(scenes, list) and scenes:
        return float(sum(float(sc.get("duration_seconds") or 6) for sc in scenes))
    ed = tl.get("estimated_duration_seconds")
    if ed is not None:
        return max(0.04, float(ed))
    return 0.0


def _estimate_duration_from_text(text: str) -> float:
    wc = count_words(text)
    if wc <= 0:
        return 4.0
    wpm = max(60.0, DEFAULT_WPM)
    sec = (wc / wpm) * 60.0
    return max(4.0, min(float(sec), 3600.0))


def _probe_audio_file_duration(audio_path: Path) -> Tuple[Optional[float], List[str]]:
    """Liest Dauer per ffprobe (wie Render-Pipeline), ohne Secrets."""
    warns: List[str] = []
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        warns.append("ffprobe_missing_cannot_probe_audio")
        return None, warns
    if not audio_path.is_file():
        return None, warns
    try:
        cp = subprocess.run(
            [
                ffprobe,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(audio_path.resolve()),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        raw = (cp.stdout or "").strip()
        if not raw or raw == "N/A":
            warns.append("audio_duration_probe_empty")
            return None, warns
        return float(raw), warns
    except Exception:
        warns.append("audio_duration_probe_failed")
        return None, warns


def _resolve_total_duration_seconds(
    tl: Optional[Dict[str, Any]],
    body: str,
) -> Tuple[float, List[str]]:
    """
    Priorität (BA 20.5b):
    1) ffprobe auf timeline.audio_path (existierende Datei)
    2) Timeline-Szenensumme / estimated_duration_seconds
    3) Wort-Schätzung
    """
    warns: List[str] = []

    if tl is not None:
        ap = (tl.get("audio_path") or "").strip()
        if ap:
            apath = Path(ap)
            if apath.is_file():
                ad, aw = _probe_audio_file_duration(apath)
                warns.extend(aw)
                if ad is not None and ad > 0.05:
                    warns.append("subtitle_audio_duration_used")
                    return float(ad), warns
            td_tl = _timeline_duration_seconds(tl)
            if td_tl > 0.05:
                warns.append("subtitle_timeline_duration_used")
                return float(td_tl), warns
            td_est = _estimate_duration_from_text(body)
            warns.append("subtitle_duration_estimate_used")
            return float(td_est), warns

        td_tl = _timeline_duration_seconds(tl)
        if td_tl > 0.05:
            warns.append("subtitle_timeline_duration_used")
            return float(td_tl), warns
        td_est = _estimate_duration_from_text(body)
        warns.append("subtitle_duration_estimate_used")
        return float(td_est), warns

    td_est = _estimate_duration_from_text(body)
    warns.append("subtitle_duration_estimate_used")
    return float(td_est), warns


def _strip_narration_header(raw: str) -> str:
    lines = (raw or "").splitlines()
    out: List[str] = []
    for ln in lines:
        if ln.strip().startswith("#"):
            continue
        out.append(ln)
    return "\n".join(out).strip()


def _hard_wrap_chunk(chunk: str, max_line: int, max_chars: int) -> str:
    c = (chunk or "").strip()
    if len(c) <= max_chars:
        return c
    words = c.split()
    lines: List[str] = []
    cur: List[str] = []
    for w in words:
        cand = " ".join(cur + [w]) if cur else w
        if len(cand) <= max_line:
            cur.append(w)
        else:
            if cur:
                lines.append(" ".join(cur))
            cur = [w]
            if len(lines) >= 2:
                tail = " ".join(cur)
                merged = (lines[0] + " " + tail).strip()
                return merged[:max_chars].rsplit(" ", 1)[0] + ("…" if len(merged) > max_chars else "")
    if cur:
        lines.append(" ".join(cur))
    joined = "\n".join(lines[:2])
    if len(joined) > max_chars:
        return joined[: max_chars - 1].rsplit(" ", 1)[0] + "…"
    return joined


def _split_into_caption_chunks(text: str) -> List[str]:
    """Narration: typisch bis 10 Wörter."""
    blob = re.sub(r"\s+", " ", (text or "").strip())
    if not blob:
        return []
    words = blob.split()
    if not words:
        return []

    chunks: List[str] = []
    buf: List[str] = []

    def flush() -> None:
        nonlocal buf
        if buf:
            chunks.append(_hard_wrap_chunk(" ".join(buf), MAX_LINE_LEN, MAX_CUE_CHARS))
            buf = []

    for w in words:
        if len(w) > MAX_CUE_CHARS and not buf:
            chunks.append(_hard_wrap_chunk(w[:MAX_CUE_CHARS], MAX_LINE_LEN, MAX_CUE_CHARS))
            continue

        tentative = buf + [w]
        joined = " ".join(tentative)
        ow = len(tentative) > MAX_WORDS_PER_CUE
        oc = len(joined) > MAX_CUE_CHARS

        if buf and (ow or oc):
            flush()
            if len(w) > MAX_CUE_CHARS:
                chunks.append(_hard_wrap_chunk(w[:MAX_CUE_CHARS], MAX_LINE_LEN, MAX_CUE_CHARS))
                continue
            buf = [w]
        else:
            buf = tentative

        if len(buf) >= MAX_WORDS_PER_CUE:
            flush()

    flush()

    if len(chunks) >= 2:
        a, b = chunks[-2], chunks[-1]
        if count_words(b) < 4 and count_words(a) + count_words(b) <= MAX_WORDS_PER_CUE:
            merged = _hard_wrap_chunk(f"{a} {b}".replace("\n", " "), MAX_LINE_LEN, MAX_CUE_CHARS)
            chunks = chunks[:-2] + [merged]

    return [c for c in chunks if c.strip()]


def _split_into_caption_chunks_audio(text: str) -> List[str]:
    """BA 20.5c: Transkript-Text in kurze Cues (ca. 4–8 Wörter)."""
    blob = re.sub(r"\s+", " ", (text or "").strip())
    if not blob:
        return []
    words = blob.split()
    if not words:
        return []

    chunks: List[str] = []
    buf: List[str] = []

    def flush() -> None:
        nonlocal buf
        if buf:
            chunks.append(_hard_wrap_chunk(" ".join(buf), MAX_LINE_LEN_AUDIO, MAX_CUE_CHARS_AUDIO))
            buf = []

    for w in words:
        if len(w) > MAX_CUE_CHARS_AUDIO and not buf:
            chunks.append(_hard_wrap_chunk(w[:MAX_CUE_CHARS_AUDIO], MAX_LINE_LEN_AUDIO, MAX_CUE_CHARS_AUDIO))
            continue

        tentative = buf + [w]
        joined = " ".join(tentative)
        ow = len(tentative) > MAX_WORDS_AUDIO_CUE
        oc = len(joined) > MAX_CUE_CHARS_AUDIO

        if buf and (ow or oc):
            flush()
            if len(w) > MAX_CUE_CHARS_AUDIO:
                chunks.append(_hard_wrap_chunk(w[:MAX_CUE_CHARS_AUDIO], MAX_LINE_LEN_AUDIO, MAX_CUE_CHARS_AUDIO))
                continue
            buf = [w]
        else:
            buf = tentative

        if len(buf) >= MAX_WORDS_AUDIO_CUE:
            flush()

    flush()

    if len(chunks) >= 2:
        a, b = chunks[-2], chunks[-1]
        if count_words(b) < 3 and count_words(a) + count_words(b) <= MAX_WORDS_AUDIO_CUE:
            merged = _hard_wrap_chunk(f"{a} {b}".replace("\n", " "), MAX_LINE_LEN_AUDIO, MAX_CUE_CHARS_AUDIO)
            chunks = chunks[:-2] + [merged]

    return [c for c in chunks if c.strip()]


def _distribute_times(
    chunks: List[str],
    total_seconds: float,
) -> List[Tuple[float, float, str]]:
    total_seconds = max(0.5, float(total_seconds))
    n = len(chunks)
    weights = [max(1, count_words(c)) for c in chunks]
    s = float(sum(weights))
    raw = [total_seconds * (wi / s) for wi in weights] if s > 0 else [total_seconds / n] * n

    d_lo = max(0.35, min(2.0, total_seconds / max(n, 1)))
    d_hi = min(5.0, max(d_lo, total_seconds))
    d = [max(d_lo, min(d_hi, r)) for r in raw]

    for _ in range(12):
        sm = sum(d)
        if abs(sm - total_seconds) < 0.04:
            break
        fac = total_seconds / sm if sm > 0 else 1.0
        d = [max(d_lo, min(d_hi, di * fac)) for di in d]

    out: List[Tuple[float, float, str]] = []
    t = 0.0
    for i, (di, ch) in enumerate(zip(d, chunks)):
        if i == n - 1:
            out.append((t, total_seconds, ch))
            break
        end = min(total_seconds, t + di)
        if end <= t:
            end = min(total_seconds, t + d_lo)
        out.append((t, end, ch))
        t = end

    if out and out[-1][1] < total_seconds - 0.02:
        a, _b, tx = out[-1]
        out[-1] = (a, total_seconds, tx)

    for i in range(len(out) - 1):
        if out[i][1] > out[i + 1][0] + 0.001:
            a, b, tx = out[i]
            out[i] = (a, out[i + 1][0], tx)

    return out


def _format_srt_ts(sec: float) -> str:
    if sec < 0:
        sec = 0.0
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec % 60.0
    whole = int(s)
    ms = int(round((s - whole) * 1000))
    if ms >= 1000:
        whole += 1
        ms = 0
    return f"{h:02d}:{m:02d}:{whole:02d},{ms:03d}"


def build_srt_content(timed: List[Tuple[float, float, str]]) -> str:
    blocks: List[str] = []
    for i, (a, b, txt) in enumerate(timed, start=1):
        if b < a:
            b = a + 0.04
        blocks.append(f"{i}\n{_format_srt_ts(a)} --> {_format_srt_ts(b)}\n{txt}\n")
    return "\n".join(blocks).rstrip() + "\n"


def _openai_api_key() -> str:
    return (os.environ.get("OPENAI_API_KEY") or "").strip()


def _post_openai_transcription_verbose_json(
    audio_path: Path,
    *,
    api_key: str,
    timeout_seconds: float = 180.0,
) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    """POST /v1/audio/transcriptions (verbose_json). Keine Secrets in Warnungen."""
    warns: List[str] = []
    if not api_key:
        return None, warns
    try:
        with open(audio_path, "rb") as f:
            file_bytes = f.read()
    except OSError as e:
        warns.append(f"subtitle_transcription_audio_read_failed:{type(e).__name__}")
        return None, warns

    mime = "audio/mpeg"
    suf = audio_path.suffix.lower()
    if suf == ".wav":
        mime = "audio/wav"
    elif suf in (".m4a", ".mp4"):
        mime = "audio/mp4"
    elif suf == ".webm":
        mime = "audio/webm"

    data = {
        "model": "whisper-1",
        "response_format": "verbose_json",
    }
    files = {"file": (audio_path.name, file_bytes, mime)}

    try:
        with httpx.Client(timeout=timeout_seconds) as client:
            r = client.post(
                OPENAI_TRANSCRIPTIONS_URL,
                headers={"Authorization": f"Bearer {api_key}"},
                data=data,
                files=files,
            )
        if r.status_code != 200:
            warns.append(f"subtitle_transcription_http_{r.status_code}")
            return None, warns
        parsed = r.json()
        if not isinstance(parsed, dict):
            warns.append("subtitle_transcription_response_not_object")
            return None, warns
        return parsed, warns
    except httpx.HTTPError as e:
        warns.append(f"subtitle_transcription_transport:{type(e).__name__}")
        return None, warns


def _float_seg(x: Any) -> float:
    try:
        return float(x or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _normalize_transcription_segments(
    parsed: Dict[str, Any],
    audio_duration: float,
) -> List[Tuple[float, float, str]]:
    """Aus verbose_json Segmente; Zeiten clampen auf [0, audio_duration]."""
    segs = parsed.get("segments")
    out: List[Tuple[float, float, str]] = []
    if not isinstance(segs, list) or not segs:
        return out
    end_cap = max(0.1, float(audio_duration))
    for seg in segs:
        if not isinstance(seg, dict):
            continue
        t0 = max(0.0, _float_seg(seg.get("start")))
        t1 = max(t0 + 0.04, _float_seg(seg.get("end")))
        txt = re.sub(r"\s+", " ", str(seg.get("text") or "")).strip()
        if not txt:
            continue
        t1 = min(t1, end_cap)
        t0 = min(t0, t1 - 0.04)
        out.append((t0, t1, txt))
    return out


def _expand_segment_to_short_cues(
    start: float,
    end: float,
    text: str,
) -> List[Tuple[float, float, str]]:
    """Ein API-Segment ggf. in 4–8-Wort-Teile mit Unterzeitaufteilung."""
    chunks = _split_into_caption_chunks_audio(text)
    if not chunks:
        return []
    if len(chunks) == 1:
        return [(start, end, chunks[0])]
    dur = max(0.08, end - start)
    weights = [max(1, count_words(c)) for c in chunks]
    sw = float(sum(weights))
    out: List[Tuple[float, float, str]] = []
    t = start
    for i, (w, ch) in enumerate(zip(weights, chunks)):
        frac = w / sw if sw > 0 else 1.0 / len(chunks)
        if i == len(chunks) - 1:
            out.append((t, end, ch))
        else:
            t2 = min(end, t + dur * frac)
            if t2 <= t:
                t2 = min(end, t + 0.12)
            out.append((t, t2, ch))
            t = t2
    return out


def _timed_cues_from_transcription_segments(
    segments: List[Tuple[float, float, str]],
    audio_duration: float,
) -> List[Tuple[float, float, str]]:
    """Segmente zu SRT-Cues; lange Texte splitten."""
    timed: List[Tuple[float, float, str]] = []
    cap = max(0.2, float(audio_duration))
    for t0, t1, txt in segments:
        if count_words(txt) <= MAX_WORDS_AUDIO_CUE and len(txt) <= MAX_CUE_CHARS_AUDIO:
            e = min(t1, cap)
            s = min(max(0.0, t0), e - 0.04)
            timed.append((s, e, _hard_wrap_chunk(txt, MAX_LINE_LEN_AUDIO, MAX_CUE_CHARS_AUDIO)))
        else:
            timed.extend(_expand_segment_to_short_cues(t0, min(t1, cap), txt))
    if timed and timed[-1][1] > cap + 0.02:
        a, _b, tx = timed[-1]
        timed[-1] = (a, cap, tx)
    return timed


def _timed_from_plain_transcript_text(text: str, audio_duration: float) -> List[Tuple[float, float, str]]:
    chunks = _split_into_caption_chunks_audio(text)
    if not chunks:
        return []
    return _distribute_times(chunks, max(0.5, float(audio_duration)))


def build_subtitle_pack(
    narration_script_path: Path,
    *,
    timeline_manifest_path: Optional[Path],
    out_root: Path,
    run_id: str,
    subtitle_mode: str,
    subtitle_source: str = "narration",
    subtitle_style: str = "classic",
    audio_path: Optional[Path] = None,
    transcribe_fn: Optional[Callable[[Path, str], Tuple[Optional[Dict[str, Any]], List[str]]]] = None,
) -> Dict[str, Any]:
    warnings: List[str] = []
    blocking: List[str] = []
    rid = (run_id or "").strip() or str(uuid.uuid4())
    mode = (subtitle_mode or "simple").strip().lower()
    if mode not in ("none", "simple"):
        warnings.append(f"subtitle_mode_unknown_defaulting_simple:{mode}")
        mode = "simple"

    src_eff = (subtitle_source or "narration").strip().lower()
    if src_eff not in ("narration", "audio"):
        warnings.append(f"subtitle_source_unknown_defaulting_narration:{src_eff}")
        src_eff = "narration"

    style_raw = (subtitle_style or "classic").strip().lower().replace("-", "_")
    style_norm = _normalize_subtitle_style(subtitle_style or "classic")
    if style_raw not in _VALID_SUBTITLE_STYLES:
        warnings.append(f"subtitle_style_unknown_defaulting_classic:{(subtitle_style or '').strip()!r}")

    transcription_provider = ""
    transcription_used = False
    fallback_used = False
    audio_path_manifest: Optional[str] = None

    src = narration_script_path.resolve()
    if not src.is_file():
        blocking.append("narration_script_missing")
        return {
            "ok": False,
            "run_id": rid,
            "output_dir": "",
            "subtitles_srt_path": "",
            "subtitle_manifest_path": "",
            "subtitle_count": 0,
            "warnings": warnings,
            "blocking_reasons": blocking,
            "subtitle_source": src_eff,
            "subtitle_style": style_norm,
            "subtitle_render_contract": _build_subtitle_render_contract(
                style_norm,
                transcription_used=False,
                subtitle_source_effective=src_eff,
                fallback_from_audio=False,
            ),
            "transcription_provider": transcription_provider,
            "transcription_used": transcription_used,
            "fallback_used": fallback_used,
            "audio_path": audio_path_manifest,
        }

    raw = src.read_text(encoding="utf-8", errors="replace")
    body = _strip_narration_header(raw)
    tl = None
    tl_path_str: Optional[str] = None
    if timeline_manifest_path:
        tl_path_str = str(timeline_manifest_path.resolve())
        try:
            tl = load_timeline_manifest_optional(timeline_manifest_path)
        except (OSError, json.JSONDecodeError):
            tl = None
            warnings.append("timeline_manifest_invalid_ignored_for_duration")

    ap_input: Optional[Path] = None
    if audio_path is not None and str(audio_path).strip():
        ap_input = Path(str(audio_path).strip()).resolve()
        audio_path_manifest = str(ap_input)

    use_audio_source = src_eff == "audio"
    if use_audio_source:
        if ap_input is None or not ap_input.is_file():
            blocking.append("subtitle_audio_path_missing_or_invalid")
            return {
                "ok": False,
                "run_id": rid,
                "output_dir": "",
                "subtitles_srt_path": "",
                "subtitle_manifest_path": "",
                "subtitle_count": 0,
                "warnings": warnings,
                "blocking_reasons": blocking,
                "subtitle_source": "audio",
                "subtitle_style": style_norm,
                "subtitle_render_contract": _build_subtitle_render_contract(
                    style_norm,
                    transcription_used=False,
                    subtitle_source_effective="audio",
                    fallback_from_audio=False,
                ),
                "transcription_provider": transcription_provider,
                "transcription_used": transcription_used,
                "fallback_used": fallback_used,
                "audio_path": str(ap_input) if ap_input else None,
            }

    td, dur_warns = _resolve_total_duration_seconds(tl, body)
    warnings.extend(dur_warns)

    if use_audio_source and ap_input is not None:
        ad_probe, awp = _probe_audio_file_duration(ap_input)
        warnings.extend(awp)
        if ad_probe is not None and ad_probe > 0.05:
            td = float(ad_probe)
            if "subtitle_audio_duration_used" not in warnings:
                warnings.append("subtitle_audio_duration_used")

    timed: List[Tuple[float, float, str]] = []

    if style_norm == "none":
        warnings.append("subtitle_style_none_visual_suppressed")
        timed = []
    elif mode == "none":
        warnings.append("subtitle_mode_none_no_cues")
    elif use_audio_source and ap_input is not None:
        key = _openai_api_key()
        if not key:
            warnings.append("subtitle_audio_transcription_env_missing_fallback_narration")
            fallback_used = True
            chunks = _chunk_body_for_subtitle_style(style_norm, body)
            if not chunks:
                blocking.append("narration_body_empty")
                return {
                    "ok": False,
                    "run_id": rid,
                    "output_dir": "",
                    "subtitles_srt_path": "",
                    "subtitle_manifest_path": "",
                    "subtitle_count": 0,
                    "warnings": warnings + ["narration_body_empty_after_header_strip"],
                    "blocking_reasons": blocking,
                    "subtitle_source": "audio",
                    "subtitle_style": style_norm,
                    "subtitle_render_contract": _build_subtitle_render_contract(
                        style_norm,
                        transcription_used=False,
                        subtitle_source_effective="audio",
                        fallback_from_audio=True,
                    ),
                    "transcription_provider": transcription_provider,
                    "transcription_used": transcription_used,
                    "fallback_used": fallback_used,
                    "audio_path": audio_path_manifest,
                }
            timed = _distribute_times(chunks, td)
        else:
            t_fn = transcribe_fn or (lambda p, k: _post_openai_transcription_verbose_json(p, api_key=k))
            parsed, tw = t_fn(ap_input, key)
            warnings.extend(tw)
            if not parsed:
                warnings.append("subtitle_transcription_failed_fallback_narration")
                fallback_used = True
                chunks = _chunk_body_for_subtitle_style(style_norm, body)
                if not chunks:
                    blocking.append("narration_body_empty")
                    return {
                        "ok": False,
                        "run_id": rid,
                        "output_dir": "",
                        "subtitles_srt_path": "",
                        "subtitle_manifest_path": "",
                        "subtitle_count": 0,
                        "warnings": warnings,
                        "blocking_reasons": blocking,
                        "subtitle_source": "audio",
                        "subtitle_style": style_norm,
                        "subtitle_render_contract": _build_subtitle_render_contract(
                            style_norm,
                            transcription_used=False,
                            subtitle_source_effective="audio",
                            fallback_from_audio=True,
                        ),
                        "transcription_provider": "openai",
                        "transcription_used": False,
                        "fallback_used": fallback_used,
                        "audio_path": audio_path_manifest,
                    }
                timed = _distribute_times(chunks, td)
            else:
                transcription_provider = "openai"
                segs = _normalize_transcription_segments(parsed, td)
                if segs:
                    timed = _timed_cues_from_transcription_segments(segs, td)
                    if timed:
                        transcription_used = True
                if not timed:
                    full_text = re.sub(r"\s+", " ", str(parsed.get("text") or "")).strip()
                    if full_text:
                        timed = _timed_from_plain_transcript_text(full_text, td)
                        if timed:
                            transcription_used = True
                if not timed:
                    warnings.append("subtitle_transcription_no_cues_fallback_narration")
                    transcription_used = False
                    fallback_used = True
                    chunks = _chunk_body_for_subtitle_style(style_norm, body)
                    if not chunks:
                        blocking.append("narration_body_empty")
                        return {
                            "ok": False,
                            "run_id": rid,
                            "output_dir": "",
                            "subtitles_srt_path": "",
                            "subtitle_manifest_path": "",
                            "subtitle_count": 0,
                            "warnings": warnings,
                            "blocking_reasons": blocking,
                            "subtitle_source": "audio",
                            "subtitle_style": style_norm,
                            "subtitle_render_contract": _build_subtitle_render_contract(
                                style_norm,
                                transcription_used=False,
                                subtitle_source_effective="audio",
                                fallback_from_audio=True,
                            ),
                            "transcription_provider": transcription_provider,
                            "transcription_used": False,
                            "fallback_used": fallback_used,
                            "audio_path": audio_path_manifest,
                        }
                    timed = _distribute_times(chunks, td)
    else:
        if mode != "none":
            chunks = _chunk_body_for_subtitle_style(style_norm, body)
            if not chunks:
                blocking.append("narration_body_empty")
                return {
                    "ok": False,
                    "run_id": rid,
                    "output_dir": "",
                    "subtitles_srt_path": "",
                    "subtitle_manifest_path": "",
                    "subtitle_count": 0,
                    "warnings": warnings + ["narration_body_empty_after_header_strip"],
                    "blocking_reasons": blocking,
                    "subtitle_source": "narration",
                    "subtitle_style": style_norm,
                    "subtitle_render_contract": _build_subtitle_render_contract(
                        style_norm,
                        transcription_used=False,
                        subtitle_source_effective="narration",
                        fallback_from_audio=False,
                    ),
                    "transcription_provider": transcription_provider,
                    "transcription_used": transcription_used,
                    "fallback_used": fallback_used,
                    "audio_path": audio_path_manifest,
                }
            timed = _distribute_times(chunks, td)

    out_dir = Path(out_root).resolve() / f"subtitles_{rid}"
    out_dir.mkdir(parents=True, exist_ok=True)
    srt_path = out_dir / "subtitles.srt"
    man_path = out_dir / "subtitle_manifest.json"

    if timed:
        srt_body = build_srt_content(timed)
    else:
        srt_body = ""
    srt_path.write_text(srt_body, encoding="utf-8")

    eff_source = "narration" if fallback_used and use_audio_source else src_eff
    render_contract = _build_subtitle_render_contract(
        style_norm,
        transcription_used=transcription_used,
        subtitle_source_effective=eff_source,
        fallback_from_audio=bool(fallback_used and use_audio_source),
    )

    manifest: Dict[str, Any] = {
        "run_id": rid,
        "source_narration_script": str(src),
        "timeline_manifest": tl_path_str,
        "subtitle_count": len(timed),
        "estimated_duration_seconds": round(td, 3),
        "subtitle_mode": mode,
        "subtitle_source": eff_source,
        "subtitle_style": style_norm,
        "subtitle_render_contract": render_contract,
        "transcription_provider": transcription_provider,
        "transcription_used": transcription_used,
        "fallback_used": fallback_used,
        "audio_path": audio_path_manifest,
        "warnings": warnings,
        "blocking_reasons": blocking,
        "subtitles_srt_path": str(srt_path),
        "output_dir": str(out_dir),
    }
    man_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    ret = {
        "ok": True,
        "run_id": rid,
        "output_dir": str(out_dir),
        "subtitles_srt_path": str(srt_path),
        "subtitle_manifest_path": str(man_path),
        "subtitle_count": len(timed),
        "estimated_duration_seconds": round(td, 3),
        "warnings": warnings,
        "blocking_reasons": blocking,
        "subtitle_source": eff_source,
        "subtitle_style": style_norm,
        "subtitle_render_contract": render_contract,
        "transcription_provider": transcription_provider,
        "transcription_used": transcription_used,
        "fallback_used": fallback_used,
        "audio_path": audio_path_manifest,
    }
    return ret


def main() -> int:
    parser = argparse.ArgumentParser(
        description="BA 20.5 / BA 20.5b / BA 20.5c — narration oder Audio-Transkription → subtitles.srt + manifest"
    )
    parser.add_argument("--narration-script", type=Path, required=True, dest="narration_script")
    parser.add_argument("--timeline-manifest", type=Path, default=None, dest="timeline_manifest")
    parser.add_argument("--audio-path", type=Path, default=None, dest="audio_path", help="BA 20.5c: MP3/WAV für --subtitle-source audio")
    parser.add_argument("--out-root", type=Path, default=ROOT / "output", dest="out_root")
    parser.add_argument("--run-id", default="", dest="run_id")
    parser.add_argument(
        "--subtitle-mode",
        choices=("none", "simple"),
        default="simple",
        dest="subtitle_mode",
    )
    parser.add_argument(
        "--subtitle-source",
        choices=("narration", "audio"),
        default="narration",
        dest="subtitle_source",
        help="BA 20.5c: narration (Default) oder audio (OpenAI-Transkription wenn OPENAI_API_KEY)",
    )
    parser.add_argument(
        "--subtitle-style",
        choices=("classic", "word_by_word", "typewriter", "karaoke", "none"),
        default="classic",
        dest="subtitle_style",
        help="BA 20.5d: Render-Stil-Vertrag (SRT bleibt V1 line-basiert)",
    )
    args = parser.parse_args()

    meta = build_subtitle_pack(
        args.narration_script,
        timeline_manifest_path=args.timeline_manifest,
        out_root=args.out_root,
        run_id=(args.run_id or "").strip() or str(uuid.uuid4()),
        subtitle_mode=args.subtitle_mode,
        subtitle_source=args.subtitle_source,
        subtitle_style=args.subtitle_style,
        audio_path=args.audio_path,
    )
    print(json.dumps(meta, ensure_ascii=False, indent=2))
    return 0 if meta.get("ok") else 3


if __name__ == "__main__":
    raise SystemExit(main())
