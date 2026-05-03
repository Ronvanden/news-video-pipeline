"""BA 20.5 / BA 20.5b — Narration → SRT + subtitle_manifest.json (Founder-lokal)."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.utils import count_words

DEFAULT_WPM = 145.0
# BA 20.5b: kürzere Cues (~6–10 Wörter, lesbar begrenzt)
MAX_CUE_CHARS = 48
MAX_LINE_LEN = 24
MAX_WORDS_PER_CUE = 10


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
            # audio_path gesetzt aber nicht nutzbar → Timeline
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

    # Kein gültiges Timeline-Objekt (fehlt oder Parse-Fehler war schon separat gemeldet)
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
    """Bis zwei Zeilen, Umbruch bevorzugt an Leerzeichen."""
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
    """
    Wortbasierte kurze Cues (BA 20.5b): typisch 6–10 Wörter, harte Zeichengrenze.
    """
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


def _distribute_times(
    chunks: List[str],
    total_seconds: float,
) -> List[Tuple[float, float, str]]:
    """
    Wortgewichtete Anteile, Clamp pro Cue (BA 20.5b), Summe = total, letzter Cue endet exakt bei total.
    """
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


def build_subtitle_pack(
    narration_script_path: Path,
    *,
    timeline_manifest_path: Optional[Path],
    out_root: Path,
    run_id: str,
    subtitle_mode: str,
) -> Dict[str, Any]:
    warnings: List[str] = []
    blocking: List[str] = []
    rid = (run_id or "").strip() or str(uuid.uuid4())
    mode = (subtitle_mode or "simple").strip().lower()
    if mode not in ("none", "simple"):
        warnings.append(f"subtitle_mode_unknown_defaulting_simple:{mode}")
        mode = "simple"

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

    td, dur_warns = _resolve_total_duration_seconds(tl, body)
    warnings.extend(dur_warns)

    if mode == "none":
        timed: List[Tuple[float, float, str]] = []
        warnings.append("subtitle_mode_none_no_cues")
    else:
        chunks = _split_into_caption_chunks(body)
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

    manifest: Dict[str, Any] = {
        "run_id": rid,
        "source_narration_script": str(src),
        "timeline_manifest": tl_path_str,
        "subtitle_count": len(timed),
        "estimated_duration_seconds": round(td, 3),
        "subtitle_mode": mode,
        "warnings": warnings,
        "blocking_reasons": blocking,
        "subtitles_srt_path": str(srt_path),
        "output_dir": str(out_dir),
    }
    man_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "ok": True,
        "run_id": rid,
        "output_dir": str(out_dir),
        "subtitles_srt_path": str(srt_path),
        "subtitle_manifest_path": str(man_path),
        "subtitle_count": len(timed),
        "estimated_duration_seconds": round(td, 3),
        "warnings": warnings,
        "blocking_reasons": blocking,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="BA 20.5 / BA 20.5b — narration_script → subtitles.srt + manifest")
    parser.add_argument("--narration-script", type=Path, required=True, dest="narration_script")
    parser.add_argument("--timeline-manifest", type=Path, default=None, dest="timeline_manifest")
    parser.add_argument("--out-root", type=Path, default=ROOT / "output", dest="out_root")
    parser.add_argument("--run-id", default="", dest="run_id")
    parser.add_argument(
        "--subtitle-mode",
        choices=("none", "simple"),
        default="simple",
        dest="subtitle_mode",
    )
    args = parser.parse_args()

    meta = build_subtitle_pack(
        args.narration_script,
        timeline_manifest_path=args.timeline_manifest,
        out_root=args.out_root,
        run_id=(args.run_id or "").strip() or str(uuid.uuid4()),
        subtitle_mode=args.subtitle_mode,
    )
    print(json.dumps(meta, ensure_ascii=False, indent=2))
    return 0 if meta.get("ok") else 3


if __name__ == "__main__":
    raise SystemExit(main())
