"""BA 32.71c — Ein Bild (OpenAI Image 2 oder vorhandenes PNG) → kurzes MP4 über Timeline/Render."""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from app.production_connectors.openai_image_pipeline_smoke import (
    run_openai_image_pipeline_smoke_v1,
    write_builtin_minimal_scene_pack,
)
from app.production_connectors.openai_image_smoke import sanitize_openai_image_smoke_warnings

_REPO_ROOT = Path(__file__).resolve().parents[2]
_BUILD_TL_SCRIPT = _REPO_ROOT / "scripts" / "build_timeline_manifest.py"
_RENDER_SCRIPT = _REPO_ROOT / "scripts" / "render_final_story_video.py"

SMOKE_VERSION = "ba32_71c_v1"


def _load_build_timeline_module() -> Any:
    spec = importlib.util.spec_from_file_location("build_timeline_manifest_ba371c", _BUILD_TL_SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_render_module() -> Any:
    spec = importlib.util.spec_from_file_location("render_final_story_video_ba371c", _RENDER_SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _effective_model(cli_model: Optional[str]) -> str:
    c = (cli_model or "").strip()
    if c:
        return c
    return (os.environ.get("OPENAI_IMAGE_MODEL") or "").strip() or "gpt-image-2"


def _clamp_duration_sec(v: int) -> int:
    return max(3, min(600, int(v)))


def _write_single_scene_manifest(
    *,
    gen_dir: Path,
    run_id: str,
    duration_seconds: int,
    generation_mode: str = "openai_image_live",
) -> Path:
    gen_dir = Path(gen_dir).resolve()
    gen_dir.mkdir(parents=True, exist_ok=True)
    dur = _clamp_duration_sec(duration_seconds)
    doc: Dict[str, Any] = {
        "run_id": str(run_id),
        "source_pack": "ba32_71c_mini_video_smoke",
        "asset_count": 1,
        "generation_mode": generation_mode,
        "warnings": [],
        "assets": [
            {
                "scene_number": 1,
                "chapter_index": 0,
                "beat_index": 0,
                "asset_type": "scene",
                "generation_mode": generation_mode,
                "image_path": "scene_001.png",
                "camera_motion_hint": "static",
                "duration_seconds": dur,
            }
        ],
    }
    mp = gen_dir / "asset_manifest.json"
    mp.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    return mp


def _patch_first_asset_duration(manifest_path: Path, duration_seconds: int) -> None:
    p = Path(manifest_path)
    data = json.loads(p.read_text(encoding="utf-8"))
    assets = data.get("assets")
    dur = _clamp_duration_sec(duration_seconds)
    if isinstance(assets, list) and assets and isinstance(assets[0], dict):
        assets[0]["duration_seconds"] = dur
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def run_openai_image_mini_video_smoke_v1(
    *,
    run_id: str,
    out_root: Path,
    model: Optional[str],
    size: str,
    duration_seconds: int,
    image_path: Optional[Path],
    openai_image_timeout_seconds: float,
    motion_mode: str = "static",
    invoke_pipeline: Optional[Callable[..., Dict[str, Any]]] = None,
    invoke_render: Optional[Callable[..., Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Genau **eine** Szene / ein PNG → ``timeline_manifest`` → ``render_final_story_video``.

    ``invoke_pipeline`` / ``invoke_render`` nur für Tests (Mocks).
    """
    warnings: List[str] = []
    rid = str(run_id).strip()
    work_parent = Path(out_root).resolve() / f"openai_image_mini_video_smoke_{rid}"
    work_parent.mkdir(parents=True, exist_ok=True)
    gen_dir = work_parent / f"generated_assets_{rid}"
    video_out = work_parent / "mini_video.mp4"
    model_eff = _effective_model(model)
    size_eff = str(size).strip() or "1024x1024"
    dur_eff = _clamp_duration_sec(duration_seconds)

    manifest_path: Optional[Path] = None
    png_resolved: Optional[Path] = None

    if image_path is not None:
        src = Path(image_path).resolve()
        if not src.is_file():
            return {
                "ok": False,
                "run_id": rid,
                "model": model_eff,
                "image_path": "",
                "video_path": str(video_out),
                "duration_seconds": None,
                "bytes_written": 0,
                "warnings": warnings + ["mini_video_smoke_image_path_not_found"],
                "smoke_version": SMOKE_VERSION,
            }
        gen_dir.mkdir(parents=True, exist_ok=True)
        dst_png = gen_dir / "scene_001.png"
        shutil.copy2(src, dst_png)
        png_resolved = dst_png.resolve()
        manifest_path = _write_single_scene_manifest(
            gen_dir=gen_dir,
            run_id=rid,
            duration_seconds=dur_eff,
            generation_mode="external_image_ingest",
        )
    else:
        pack = write_builtin_minimal_scene_pack(work_parent / "builtin_scene_asset_pack.json", 1)
        pipe_fn = invoke_pipeline
        if pipe_fn is None:
            pipe_fn = run_openai_image_pipeline_smoke_v1
        saved_ip = os.environ.get("IMAGE_PROVIDER")
        try:
            os.environ["IMAGE_PROVIDER"] = "openai_image"
            body = pipe_fn(
                pack_path=pack,
                out_root=Path(out_root).resolve(),
                run_id=rid,
                max_scenes=1,
                openai_image_model=model_eff,
                openai_image_size=size_eff,
                openai_image_timeout_seconds=float(openai_image_timeout_seconds),
            )
        finally:
            if saved_ip is None:
                os.environ.pop("IMAGE_PROVIDER", None)
            else:
                os.environ["IMAGE_PROVIDER"] = saved_ip

        warns_p = sanitize_openai_image_smoke_warnings(list(body.get("warnings") or []))
        warnings.extend(warns_p)
        if not body.get("ok"):
            return {
                "ok": False,
                "run_id": rid,
                "model": str(body.get("model") or model_eff),
                "image_path": "",
                "video_path": str(video_out),
                "duration_seconds": None,
                "bytes_written": 0,
                "warnings": warnings,
                "smoke_version": SMOKE_VERSION,
            }
        model_eff = str(body.get("model") or model_eff)
        mp = Path(str(body.get("manifest_path") or ""))
        if not mp.is_file():
            return {
                "ok": False,
                "run_id": rid,
                "model": model_eff,
                "image_path": "",
                "video_path": str(video_out),
                "duration_seconds": None,
                "bytes_written": 0,
                "warnings": warnings + ["mini_video_smoke_manifest_missing_after_pipeline"],
                "smoke_version": SMOKE_VERSION,
            }
        manifest_path = mp
        _patch_first_asset_duration(manifest_path, dur_eff)
        paths = list(body.get("asset_paths") or [])
        if paths:
            png_resolved = Path(str(paths[0])).resolve()
        else:
            outd = Path(str(body.get("output_dir") or manifest_path.parent))
            cand = outd / "scene_001.png"
            png_resolved = cand.resolve() if cand.is_file() else None

    assert manifest_path is not None

    tl_mod = _load_build_timeline_module()
    manifest = tl_mod.load_asset_manifest(manifest_path)
    timeline_file, _tbody = tl_mod.write_timeline_manifest(
        manifest,
        asset_manifest_path=manifest_path,
        audio_path=None,
        run_id=rid,
        scene_duration_seconds=dur_eff,
        out_root=work_parent,
    )

    render_fn = invoke_render
    if render_fn is None:
        render_mod = _load_render_module()
        render_fn = render_mod.render_final_story_video

    rmeta = render_fn(
        timeline_file,
        output_video=video_out,
        motion_mode=(motion_mode or "static").strip().lower(),
        subtitle_path=None,
        run_id=rid,
        write_output_manifest=False,
        manifest_root=work_parent,
    )

    rw = list(rmeta.get("warnings") or [])
    warnings.extend(str(w) for w in rw if str(w).strip())
    vid_ok = bool(rmeta.get("video_created"))
    bytes_written = 0
    if video_out.is_file():
        try:
            bytes_written = int(video_out.stat().st_size)
        except OSError:
            bytes_written = 0

    dur_out = rmeta.get("duration_seconds")
    try:
        dur_out_f = float(dur_out) if dur_out is not None else None
    except (TypeError, ValueError):
        dur_out_f = None

    rb = list(rmeta.get("blocking_reasons") or [])
    if rb:
        warnings.extend(rb)

    ok = vid_ok and bytes_written > 0
    img_out = str(png_resolved) if png_resolved is not None else ""

    return {
        "ok": ok,
        "run_id": rid,
        "model": model_eff,
        "image_path": img_out,
        "video_path": str(video_out.resolve()),
        "duration_seconds": dur_out_f,
        "bytes_written": int(bytes_written),
        "warnings": sanitize_openai_image_smoke_warnings(warnings),
        "smoke_version": SMOKE_VERSION,
    }
