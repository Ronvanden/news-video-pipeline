"""BA 26.8 — Real Visual Assets Founder Smoke.

Script → Leonardo-Bilder + Runway-Clips → ElevenLabs Voice → final_video.mp4.

Nutzt bestehende Module (run_asset_runner, runway_image_to_video_smoke,
run_url_to_final_mp4) und fügt nur die Orchestrierung hinzu.
Kein neuer Provider, kein Dashboard, kein Publishing.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import sys
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from app.real_video_build.production_pack import build_production_pack

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_URL_TO_FINAL = ROOT / "scripts" / "run_url_to_final_mp4.py"
_ASSET_RUNNER = ROOT / "scripts" / "run_asset_runner.py"
_RUNWAY_SMOKE = ROOT / "scripts" / "runway_image_to_video_smoke.py"

_LEONARDO_ENV = "LEONARDO_API_KEY"
_RUNWAY_ENV = "RUNWAY_API_KEY"
_ELEVENLABS_ENV = "ELEVENLABS_API_KEY"


def _load_mod(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _env_present(key: str) -> bool:
    return bool((os.environ.get(key) or "").strip())


def _detect_providers() -> Dict[str, bool]:
    return {
        "leonardo": _env_present(_LEONARDO_ENV),
        "runway": _env_present(_RUNWAY_ENV),
        "elevenlabs": _env_present(_ELEVENLABS_ENV),
    }


def _provider_env_detected(providers: Dict[str, bool]) -> Dict[str, str]:
    return {k: ("set" if v else "not_set") for k, v in providers.items()}


# ---------------------------------------------------------------------------
# Phase 1: Leonardo Images via run_asset_runner (live mode)
# ---------------------------------------------------------------------------

def _run_leonardo_images(
    pack_path: Path,
    out_dir: Path,
    run_id: str,
    *,
    max_scenes: int,
    leonardo_beat_fn: Optional[Callable] = None,
) -> Tuple[int, Path, List[str], List[str]]:
    """Returns (count_ok, gen_dir, warnings, blocking_reasons)."""
    warns: List[str] = []
    blocking: List[str] = []

    if not _env_present(_LEONARDO_ENV):
        blocking.append("leonardo_missing_api_key")
        return 0, out_dir, warns, blocking

    asset_mod = _load_mod("asset_runner_ba268", _ASSET_RUNNER)
    ameta = asset_mod.run_local_asset_runner(
        pack_path,
        out_dir,
        run_id=run_id,
        mode="live",
        max_assets_live=max_scenes,
        leonardo_beat_fn=leonardo_beat_fn,
    )
    warns.extend(ameta.get("warnings") or [])
    manifest_path = Path(str(ameta.get("manifest_path") or ""))
    gen_dir = manifest_path.parent if manifest_path.is_file() else out_dir

    count = 0
    if manifest_path.is_file():
        try:
            man = json.loads(manifest_path.read_text(encoding="utf-8"))
            for a in man.get("assets") or []:
                if isinstance(a, dict) and str(a.get("generation_mode") or "") == "leonardo_live":
                    count += 1
        except (OSError, json.JSONDecodeError):
            warns.append("ba268_leonardo_manifest_parse_error")

    return count, gen_dir, warns, blocking


# ---------------------------------------------------------------------------
# Phase 2: Runway Videos for selected scenes
# ---------------------------------------------------------------------------

def _run_runway_clips(
    gen_dir: Path,
    out_dir: Path,
    scene_plan: Dict[str, Any],
    run_id: str,
    *,
    max_runway_scenes: int = 3,
    runway_run_fn: Optional[Callable] = None,
) -> Tuple[int, Dict[int, Path], List[str], List[str]]:
    """Returns (count_ok, {scene_num: clip_path}, warnings, blocking)."""
    warns: List[str] = []
    blocking: List[str] = []
    clips: Dict[int, Path] = {}

    if not _env_present(_RUNWAY_ENV):
        blocking.append("runway_missing_api_key")
        return 0, clips, warns, blocking

    scenes = (scene_plan.get("scenes") or [])[:max_runway_scenes]
    if not scenes:
        warns.append("ba268_runway_no_scenes")
        return 0, clips, warns, blocking

    rw_mod = _load_mod("runway_smoke_ba268", _RUNWAY_SMOKE)
    run_fn = runway_run_fn or rw_mod.run_runway_image_to_video_smoke

    runway_out = out_dir / "visual_assets" / "runway"
    runway_out.mkdir(parents=True, exist_ok=True)

    for idx, sc in enumerate(scenes):
        sn = idx + 1
        img_path = gen_dir / f"scene_{sn:03d}.png"
        if not img_path.is_file():
            warns.append(f"ba268_runway_scene_image_missing:{sn}")
            continue

        vprompt = str(sc.get("visual_prompt") or sc.get("video_prompt") or "cinematic slow motion")
        sub_id = f"{run_id}_rw_sc{sn:03d}"

        try:
            res = run_fn(
                image_path=img_path,
                prompt=vprompt,
                run_id=sub_id,
                out_root=out_dir / "_runway_work",
                duration_seconds=5,
            )
        except Exception as exc:
            warns.append(f"ba268_runway_exception:{sn}:{type(exc).__name__}")
            continue

        if res.get("ok") and (res.get("output_video_path") or "").strip():
            src = Path(str(res["output_video_path"]))
            dest = runway_out / f"scene_{sn:03d}.mp4"
            try:
                shutil.copy2(src, dest)
                clips[sn] = dest
            except OSError as exc:
                warns.append(f"ba268_runway_copy_failed:{sn}:{type(exc).__name__}")
        else:
            sw = res.get("warnings") or []
            sb = res.get("blocking_reasons") or []
            warns.extend([str(w) for w in sw])
            warns.extend([str(b) for b in sb])

    return len(clips), clips, warns, blocking


# ---------------------------------------------------------------------------
# Phase 3: Build asset-dir with priority: Runway > Leonardo > Fallback
# ---------------------------------------------------------------------------

def _build_asset_dir(
    gen_dir: Path,
    runway_clips: Dict[int, Path],
    out_dir: Path,
    n_scenes: int,
    *,
    fallback_clip: Optional[Path] = None,
) -> Tuple[Path, List[Dict[str, Any]], List[str]]:
    """Build a merged asset directory for run_url_to_final_mp4."""
    asset_dir = out_dir / "visual_assets" / "merged"
    asset_dir.mkdir(parents=True, exist_ok=True)
    warns: List[str] = []
    scene_details: List[Dict[str, Any]] = []

    for sn in range(1, n_scenes + 1):
        detail: Dict[str, Any] = {"scene_number": sn, "source": "none", "path": None}

        if sn in runway_clips and runway_clips[sn].is_file():
            dest = asset_dir / f"scene_{sn:03d}.mp4"
            shutil.copy2(runway_clips[sn], dest)
            detail["source"] = "runway_live"
            detail["path"] = str(dest)
            scene_details.append(detail)
            continue

        leo_img = gen_dir / f"scene_{sn:03d}.png"
        if leo_img.is_file() and leo_img.stat().st_size > 1000:
            dest = asset_dir / f"scene_{sn:03d}.png"
            shutil.copy2(leo_img, dest)
            detail["source"] = "leonardo_image"
            detail["path"] = str(dest)
            scene_details.append(detail)
            continue

        if fallback_clip and fallback_clip.is_file():
            dest = asset_dir / f"scene_{sn:03d}_fallback.mp4"
            shutil.copy2(fallback_clip, dest)
            detail["source"] = "fallback_existing_clip"
            detail["path"] = str(dest)
            warns.append(f"fallback_existing_runway_clip_used:{sn}")
            scene_details.append(detail)
            continue

        detail["source"] = "cinematic_placeholder"
        scene_details.append(detail)

    return asset_dir, scene_details, warns


# ---------------------------------------------------------------------------
# Phase 4: Visual Summary
# ---------------------------------------------------------------------------

def _write_visual_summary(
    out_dir: Path,
    *,
    leonardo_count: int,
    runway_count: int,
    scene_details: List[Dict[str, Any]],
    warnings: List[str],
    blocking: List[str],
    providers: Dict[str, bool],
    output_paths: Dict[str, str],
) -> Path:
    fallback_count = sum(1 for s in scene_details if s.get("source") in ("fallback_existing_clip", "cinematic_placeholder"))
    doc = {
        "ok": not blocking,
        "used_leonardo_images_count": leonardo_count,
        "used_runway_videos_count": runway_count,
        "fallback_assets_used": fallback_count,
        "scenes": scene_details,
        "warnings": warnings,
        "blocking_reasons": blocking,
        "provider_env_detected": _provider_env_detected(providers),
        "output_paths": output_paths,
    }
    p = out_dir / "visual_summary.json"
    p.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------

def run_real_visual_founder_smoke(
    *,
    script_json_path: Path,
    out_dir: Path,
    max_scenes: int = 5,
    duration_seconds: int = 60,
    use_leonardo: bool = True,
    use_runway: bool = True,
    max_runway_scenes: int = 3,
    voice_mode: str = "elevenlabs",
    fit_video_to_voice: bool = True,
    fallback_clip: Optional[Path] = None,
    run_id: Optional[str] = None,
    leonardo_beat_fn: Optional[Callable] = None,
    runway_run_fn: Optional[Callable] = None,
    elevenlabs_post_override: Optional[Callable] = None,
) -> Dict[str, Any]:
    """Full BA 26.8 orchestration. Returns combined summary dict."""
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    rid = (run_id or "").strip() or f"ba268_{uuid.uuid4().hex[:8]}"

    providers = _detect_providers()
    all_warns: List[str] = []
    all_blocking: List[str] = []

    script_json_path = Path(script_json_path).resolve()
    if not script_json_path.is_file():
        all_blocking.append("script_json_missing")
        summary = {
            "ok": False, "run_id": rid,
            "warnings": all_warns, "blocking_reasons": all_blocking,
        }
        (out_dir / "run_summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return summary

    try:
        script_data = json.loads(script_json_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        all_blocking.append(f"script_json_parse_error:{type(exc).__name__}")
        summary = {
            "ok": False, "run_id": rid,
            "warnings": all_warns, "blocking_reasons": all_blocking,
        }
        (out_dir / "run_summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return summary

    url_to_final_mod = _load_mod("url_to_final_ba268", _URL_TO_FINAL)

    scene_rows = url_to_final_mod._build_scene_rows_from_script(
        url_to_final_mod._tolerant_script(script_data),
        max_scenes=max_scenes,
        total_duration_seconds=duration_seconds,
    )
    n_scenes = len(scene_rows)
    scene_plan = url_to_final_mod._build_scene_plan(
        scene_rows,
        script_title=str(script_data.get("title") or ""),
    )
    script_clean = url_to_final_mod._tolerant_script(script_data)
    pack = url_to_final_mod._build_scene_asset_pack(
        scene_rows,
        script=script_clean,
        rel_videos=[None] * n_scenes,
        pack_parent=out_dir,
    )

    scene_plan_path = out_dir / "scene_plan.json"
    scene_plan_path.write_text(json.dumps(scene_plan, ensure_ascii=False, indent=2), encoding="utf-8")
    pack_path = out_dir / "scene_asset_pack.json"
    pack_path.write_text(json.dumps(pack, ensure_ascii=False, indent=2), encoding="utf-8")

    # --- Leonardo Images ---
    leonardo_count = 0
    gen_dir = out_dir
    if use_leonardo:
        leonardo_count, gen_dir, leo_w, leo_b = _run_leonardo_images(
            pack_path, out_dir, rid,
            max_scenes=max_scenes,
            leonardo_beat_fn=leonardo_beat_fn,
        )
        all_warns.extend(leo_w)
        all_blocking.extend(leo_b)
    else:
        all_warns.append("ba268_leonardo_skipped_by_flag")

    # --- Runway Videos ---
    runway_count = 0
    runway_clips: Dict[int, Path] = {}
    if use_runway:
        runway_count, runway_clips, rw_w, rw_b = _run_runway_clips(
            gen_dir, out_dir, scene_plan, rid,
            max_runway_scenes=min(max_runway_scenes, n_scenes),
            runway_run_fn=runway_run_fn,
        )
        all_warns.extend(rw_w)
        all_blocking.extend(rw_b)
    else:
        all_warns.append("ba268_runway_skipped_by_flag")

    # --- Build merged asset dir ---
    asset_dir, scene_details, merge_warns = _build_asset_dir(
        gen_dir, runway_clips, out_dir, n_scenes,
        fallback_clip=fallback_clip,
    )
    all_warns.extend(merge_warns)

    # --- Visual Summary ---
    output_paths: Dict[str, str] = {
        "scene_plan": str(scene_plan_path),
        "scene_asset_pack": str(pack_path),
        "asset_dir": str(asset_dir),
    }
    vs_path = _write_visual_summary(
        out_dir,
        leonardo_count=leonardo_count,
        runway_count=runway_count,
        scene_details=scene_details,
        warnings=list(all_warns),
        blocking=[b for b in all_blocking if "missing_api_key" in b],
        providers=providers,
        output_paths=output_paths,
    )
    output_paths["visual_summary"] = str(vs_path)

    # --- run_url_to_final_mp4 with generated assets ---
    final_doc = url_to_final_mod.run_ba265_url_to_final(
        url=None,
        script_json_path=script_json_path,
        out_dir=out_dir,
        max_scenes=max_scenes,
        duration_seconds=duration_seconds,
        asset_dir=asset_dir,
        run_id=rid,
        motion_mode="basic",
        voice_mode=voice_mode,
        fit_video_to_voice=fit_video_to_voice,
        elevenlabs_post_override=elevenlabs_post_override,
    )

    final_doc["ba268_visual"] = {
        "used_leonardo_images_count": leonardo_count,
        "used_runway_videos_count": runway_count,
        "fallback_assets_used": sum(
            1 for s in scene_details
            if s.get("source") in ("fallback_existing_clip", "cinematic_placeholder")
        ),
        "visual_summary_path": str(vs_path),
        "provider_env_detected": _provider_env_detected(providers),
    }
    final_doc["warnings"] = list(set(final_doc.get("warnings") or []) | set(all_warns))

    # BA 27.0b — Production Pack reference wiring (no render, no live calls)
    try:
        pack_dir = out_dir / f"production_pack_{rid}"
        src_paths = {
            "asset_manifest": Path(str(final_doc.get("asset_manifest_path") or "")) if final_doc.get("asset_manifest_path") else None,
            "scene_asset_pack": Path(str(final_doc.get("scene_asset_pack_path") or "")) if final_doc.get("scene_asset_pack_path") else None,
            "script_json": Path(str(final_doc.get("script_path") or "")) if final_doc.get("script_path") else None,
        }
        pack_res = build_production_pack(
            run_id=rid,
            output_root=out_dir,
            source_paths=src_paths,
            pack_dir=pack_dir,
            copy_assets=True,
            dry_run=False,
        )
        final_doc["production_pack_summary"] = pack_res.get("production_pack_summary") or None
        final_doc["production_pack_reference_path"] = str((Path(str(pack_res.get("pack_dir") or "")).resolve() / "production_pack_reference.json"))
    except Exception as exc:
        final_doc.setdefault("warnings", [])
        final_doc["warnings"].append(f"production_pack_build_failed:{type(exc).__name__}")

    run_summary_path = out_dir / "run_summary.json"
    run_summary_path.write_text(
        json.dumps(final_doc, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return final_doc


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    p = argparse.ArgumentParser(
        description="BA 26.8 — Real Visual Assets Founder Smoke: Leonardo + Runway + Voice → final_video.mp4"
    )
    p.add_argument("--script-json", type=Path, required=True, dest="script_json")
    p.add_argument("--out-dir", type=Path, required=True, dest="out_dir")
    p.add_argument("--max-scenes", type=int, default=5, dest="max_scenes")
    p.add_argument("--duration-seconds", type=int, default=60, dest="duration_seconds")
    p.add_argument("--use-leonardo", action="store_true", dest="use_leonardo")
    p.add_argument("--use-runway", action="store_true", dest="use_runway")
    p.add_argument("--max-runway-scenes", type=int, default=3, dest="max_runway_scenes")
    p.add_argument(
        "--voice-mode", default="elevenlabs", dest="voice_mode",
        choices=("none", "existing", "elevenlabs", "dummy", "openai"),
    )
    p.add_argument("--fit-video-to-voice", action="store_true", dest="fit_video_to_voice")
    p.add_argument(
        "--fallback-clip", type=Path, default=None, dest="fallback_clip",
        help="Optional: existing MP4 clip as visual fallback for scenes without Leonardo/Runway.",
    )
    p.add_argument("--run-id", type=str, default=None, dest="run_id")
    args = p.parse_args()

    try:
        doc = run_real_visual_founder_smoke(
            script_json_path=args.script_json,
            out_dir=args.out_dir,
            max_scenes=max(1, int(args.max_scenes)),
            duration_seconds=max(5, int(args.duration_seconds)),
            use_leonardo=bool(args.use_leonardo),
            use_runway=bool(args.use_runway),
            max_runway_scenes=max(1, int(args.max_runway_scenes)),
            voice_mode=args.voice_mode,
            fit_video_to_voice=bool(args.fit_video_to_voice),
            fallback_clip=args.fallback_clip,
            run_id=args.run_id,
        )
    except Exception as exc:
        err = {"ok": False, "error": type(exc).__name__, "message": str(exc)}
        print(json.dumps(err, ensure_ascii=False, indent=2))
        return 2

    print(json.dumps(doc, ensure_ascii=False, indent=2))
    return 0 if doc.get("ok") else 3


if __name__ == "__main__":
    raise SystemExit(main())
