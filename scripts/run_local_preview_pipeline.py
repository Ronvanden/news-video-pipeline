"""BA 20.9 — Ein Kommando: Untertitel bauen → Clean-Video rendern → Burn-in-Preview (lokal, Founder)."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

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
        return {
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
            "blocking_reasons": blocking or ["build_subtitles_failed"],
        }

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
        return {
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
            "blocking_reasons": blocking or ["render_clean_failed"],
        }

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

    preview_path = str(step_burn.get("output_video_path") or "")
    burn_ok = bool(step_burn.get("ok"))
    skipped = bool(step_burn.get("skipped"))
    overall_ok = burn_ok and (skipped or bool(preview_path))

    return {
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


def main() -> int:
    parser = argparse.ArgumentParser(
        description="BA 20.9 — Lokale Preview-Pipeline: Untertitel → clean MP4 → Burn-in-Preview (ein Aufruf)."
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
    print(json.dumps(meta, ensure_ascii=False, indent=2))
    return 0 if meta.get("ok") else 3


if __name__ == "__main__":
    raise SystemExit(main())
