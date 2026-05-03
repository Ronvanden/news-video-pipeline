"""BA 20.6 — Vorhandene subtitles.srt aus subtitle_manifest.json in ein Video brennen (Preview, classic SRT)."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_VALID_STYLES = frozenset({"classic", "word_by_word", "typewriter", "karaoke", "none"})

SUBTITLE_FORCE_STYLE = (
    "FontName=Arial,FontSize=22,"
    "PrimaryColour=&H00FFFFFF&,OutlineColour=&H000000&,"
    "Outline=2,Shadow=1,MarginV=64,Alignment=2"
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


def _subtitles_vf_fragment(srt: Path) -> str:
    pe = _ffmpeg_escape_subtitle_file_path(srt)
    st = SUBTITLE_FORCE_STYLE.replace(",", r"\,")
    return f"subtitles='{pe}':force_style={st}"


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

    def pack(
        *,
        ok: bool,
        skipped: bool,
        srt_path_str: str,
        out_video: str,
        style: str,
        fallback: bool,
    ) -> Dict[str, Any]:
        return {
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
            "warnings": list(warnings),
            "blocking_reasons": list(blocking),
        }

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
        )

    fallback_used = False
    if style_norm == "word_by_word":
        warnings.append("subtitle_style_word_by_word_rendered_as_srt")
        fallback_used = True
    elif style_norm == "typewriter":
        warnings.append("subtitle_style_typewriter_fallback_to_srt_burnin")
        fallback_used = True
    elif style_norm == "karaoke":
        warnings.append("subtitle_style_karaoke_fallback_to_srt_burnin")
        fallback_used = True

    out_dir.mkdir(parents=True, exist_ok=True)
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
        )

    vf = _subtitles_vf_fragment(srt_path)
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
        )

    return pack(
        ok=True,
        skipped=False,
        srt_path_str=str(srt_path),
        out_video=str(out_mp4),
        style=style_norm,
        fallback=fallback_used,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="BA 20.6 — subtitle_manifest.json + subtitles.srt → preview_with_subtitles.mp4"
    )
    parser.add_argument("--input-video", type=Path, required=True, dest="input_video")
    parser.add_argument("--subtitle-manifest", type=Path, required=True, dest="subtitle_manifest")
    parser.add_argument("--out-root", type=Path, default=ROOT / "output", dest="out_root")
    parser.add_argument("--run-id", default="", dest="run_id")
    parser.add_argument(
        "--force",
        action="store_true",
        dest="force",
        help="Vorhandenes preview_with_subtitles.mp4 überschreiben",
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
