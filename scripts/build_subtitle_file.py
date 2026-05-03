"""BA 20.5 — Narration → SRT + subtitle_manifest.json (Founder-lokal)."""

from __future__ import annotations

import argparse
import json
import re
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.utils import count_words

DEFAULT_WPM = 145.0
MAX_CUE_CHARS = 76
MAX_LINE_LEN = 38


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


def _strip_narration_header(raw: str) -> str:
    lines = (raw or "").splitlines()
    out: List[str] = []
    for ln in lines:
        if ln.strip().startswith("#"):
            continue
        out.append(ln)
    return "\n".join(out).strip()


def _split_sentences(text: str) -> List[str]:
    t = re.sub(r"\s+", " ", (text or "").strip())
    if not t:
        return []
    parts = re.split(r"(?<=[.!?])\s+", t)
    return [p.strip() for p in parts if p.strip()]


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
    sentences = _split_sentences(text)
    if not sentences:
        blob = re.sub(r"\s+", " ", (text or "").strip())
        if not blob:
            return []
        sentences = [blob]
    chunks: List[str] = []
    buf = ""
    for s in sentences:
        cand = f"{buf} {s}".strip() if buf else s
        if len(cand) <= MAX_CUE_CHARS:
            buf = cand
            continue
        if buf:
            chunks.append(_hard_wrap_chunk(buf, MAX_LINE_LEN, MAX_CUE_CHARS))
            buf = ""
        rest = s
        while len(rest) > MAX_CUE_CHARS:
            cut = rest[:MAX_CUE_CHARS].rsplit(" ", 1)[0]
            if len(cut) < 12:
                cut = rest[:MAX_CUE_CHARS]
            chunks.append(_hard_wrap_chunk(cut.strip(), MAX_LINE_LEN, MAX_CUE_CHARS))
            rest = rest[len(cut) :].strip()
        buf = rest
    if buf:
        chunks.append(_hard_wrap_chunk(buf, MAX_LINE_LEN, MAX_CUE_CHARS))
    return [c for c in chunks if c.strip()]


def _distribute_times(chunks: List[str], total_seconds: float) -> List[Tuple[float, float, str]]:
    total_seconds = max(0.5, float(total_seconds))
    weights = [max(1, len(c)) for c in chunks]
    s = float(sum(weights))
    out: List[Tuple[float, float, str]] = []
    t = 0.0
    for i, ch in enumerate(chunks):
        w = weights[i]
        dur = total_seconds * (w / s) if s > 0 else total_seconds / len(chunks)
        if i == len(chunks) - 1:
            end = total_seconds
        else:
            end = min(total_seconds, t + dur)
        if end <= t:
            end = min(total_seconds, t + 0.3)
        out.append((t, end, ch))
        t = end
    if out and out[-1][1] < total_seconds - 0.05:
        a, b, txt = out[-1]
        out[-1] = (a, total_seconds, txt)
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

    if tl:
        td = _timeline_duration_seconds(tl)
        if td <= 0:
            td = _estimate_duration_from_text(body)
            warnings.append("timeline_duration_zero_using_word_estimate")
    else:
        td = _estimate_duration_from_text(body)
        if not timeline_manifest_path:
            warnings.append("timeline_manifest_missing_using_word_estimate")

    if mode == "none":
        timed = []
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
    parser = argparse.ArgumentParser(description="BA 20.5 — narration_script → subtitles.srt + manifest")
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
