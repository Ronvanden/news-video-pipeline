"""BA 25.1 — Real Video Build Orchestrator CLI.

Verbindet vorhandene Build-Scripts mit **einer** ``run_id`` zu einem lokalen
``output/real_build_<run_id>/``-Indexpaket. Kein URL-Input, kein
``GenerateScriptResponse``-Adapter (BA 25.2/25.3), kein Final Render
(bestehender BA 24.x-Flow).

Reihenfolge:

A. Asset Runner       (scene_asset_pack.json → asset_manifest.json)
B. Voiceover (smoke)  (Narration aus scene_expansion → narration_script.txt + smoke MP3)
C. Timeline Builder   (asset_manifest.json + audio_path → timeline_manifest.json)
D. Clean Render       (timeline_manifest.json → clean_video.mp4)
E. Subtitle Build     (narration_script.txt → subtitle_manifest.json + subtitles.srt)
F. Burn-in Preview    (clean_video.mp4 + subtitle_manifest → preview_with_subtitles.mp4)
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_ASSET_SCRIPT = ROOT / "scripts" / "run_asset_runner.py"
_TIMELINE_SCRIPT = ROOT / "scripts" / "build_timeline_manifest.py"
_VOICEOVER_SCRIPT = ROOT / "scripts" / "build_full_voiceover.py"
_RENDER_SCRIPT = ROOT / "scripts" / "render_final_story_video.py"
_SUBTITLE_SCRIPT = ROOT / "scripts" / "build_subtitle_file.py"
_BURN_SCRIPT = ROOT / "scripts" / "burn_in_subtitles_preview.py"

REAL_BUILD_RESULT_FILENAME = "real_video_build_result.json"
REAL_BUILD_RESULT_SCHEMA = "real_video_build_result_v1"

_RUN_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,80}$")

_REQUIRED_PATH_KEYS: Tuple[str, ...] = (
    "scene_asset_pack",
    "asset_manifest",
    "timeline_manifest",
    "voiceover_audio",
    "narration_script",
    "clean_video",
    "subtitle_manifest",
    "subtitle_file",
    "preview_with_subtitles",
    "local_preview_dir",
    "final_render_dir",
    "final_video",
)


def _validate_run_id(run_id: str) -> bool:
    s = (run_id or "").strip()
    if not s or ".." in s or "/" in s or "\\" in s:
        return False
    return bool(_RUN_ID_RE.fullmatch(s))


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _empty_paths() -> Dict[str, str]:
    return {k: "" for k in _REQUIRED_PATH_KEYS}


def _resolve_or_blank(p: Any) -> str:
    if not p:
        return ""
    try:
        return str(Path(str(p)).resolve())
    except OSError:
        return str(p)


def _list_str(x: Any) -> List[str]:
    if x is None:
        return []
    if isinstance(x, list):
        return [str(i) for i in x if i is not None and str(i).strip() != ""]
    if isinstance(x, (str, int, float, bool)):
        t = str(x).strip()
        return [t] if t else []
    return [str(x)]


def derive_narration_from_scene_pack(pack_data: Dict[str, Any]) -> str:
    """
    BA 25.1/25.2:
    - Prefer echte Narration-Felder, falls im scene_asset_pack vorhanden (BA 25.2 Adapter).
    - Fallback: minimal aus visual_prompts ableiten (BA 25.1 Fixture-Path).
    """
    se = pack_data.get("scene_expansion") if isinstance(pack_data, dict) else None
    if not isinstance(se, dict):
        return ""
    raw = se.get("expanded_scene_assets") or []
    if not isinstance(raw, list) or not raw:
        return ""
    sorted_beats = sorted(
        raw,
        key=lambda b: (int((b or {}).get("chapter_index", 0)), int((b or {}).get("beat_index", 0))),
    )
    parts: List[str] = []
    hook = str(pack_data.get("hook") or "").strip() if isinstance(pack_data, dict) else ""
    for i, b in enumerate(sorted_beats, start=1):
        if not isinstance(b, dict):
            continue
        preferred = ""
        for key in ("narration", "voiceover_text", "script_text", "text", "content"):
            preferred = str(b.get(key) or "").strip()
            if preferred:
                break
        if preferred:
            parts.append(preferred)
            continue

        vp = re.sub(r"\s+", " ", str(b.get("visual_prompt") or "")).strip()
        if vp:
            parts.append(f"Szene {i}. {vp}")
    # Hook nur ergänzen, wenn er nicht bereits als erster Preferred-Block enthalten ist.
    if hook:
        first = (parts[0] or "").strip() if parts else ""
        if not first or first != hook:
            parts = [hook] + parts
    return "\n\n".join(p for p in parts if p)


def _next_step_for_status(status: str) -> str:
    s = (status or "").strip().lower()
    if s == "completed":
        return (
            "Öffne preview_with_subtitles.mp4 im Indexpaket; "
            "Final Render bleibt BA 24.x-Flow (run_final_render.py)."
        )
    if s == "blocked":
        return (
            "Blocking Reasons im Manifest prüfen "
            "(z. B. ffmpeg_missing, scene_asset_pack ungültig)."
        )
    if s == "failed":
        return "Letzten Step im Manifest prüfen und ggf. mit --force erneut starten."
    return "Manifest-Pfad und Status prüfen."


def _step(name: str, *, ok: bool, output: str = "", warnings: Optional[List[str]] = None,
          blocking_reasons: Optional[List[str]] = None,
          extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    body: Dict[str, Any] = {
        "name": name,
        "ok": bool(ok),
        "output": _s(output),
        "warnings": list(warnings or []),
        "blocking_reasons": list(blocking_reasons or []),
    }
    if extra:
        body["extra"] = dict(extra)
    return body


def _s(v: Any) -> str:
    if v is None:
        return ""
    return str(v).strip()


def write_real_video_build_result(
    *,
    build_dir: Path,
    payload: Dict[str, Any],
) -> str:
    """Schreibt das ``real_video_build_result.json`` (V1, additiv erweiterbar)."""
    build_dir.mkdir(parents=True, exist_ok=True)
    target = build_dir / REAL_BUILD_RESULT_FILENAME
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return str(target.resolve())


def _build_voiceover_smoke(
    *,
    pack_data: Dict[str, Any],
    run_id: str,
    out_root: Path,
    voice_mode: str,
    voiceover_mod: Any,
    write_smoke_mp3_fn: Optional[Callable[[Path, int, str], Tuple[bool, List[str]]]] = None,
    which_ffmpeg_fn: Optional[Callable[[], Optional[str]]] = None,
) -> Tuple[Dict[str, Any], Dict[str, str]]:
    """
    BA 25.1: minimal lokal — Narration aus scene_pack ableiten, smoke MP3 via ffmpeg-anullsrc.
    Kein TTS-Live (auch wenn Keys gesetzt sind), das ist BA 25.2/25.3.
    """
    warnings: List[str] = []
    blocking: List[str] = []
    paths: Dict[str, str] = {"voiceover_audio": "", "narration_script": ""}

    requested = (voice_mode or "smoke").strip().lower()
    if requested != "smoke":
        warnings.append(f"voice_mode_forced_smoke_in_ba_25_1:{requested}")

    narration_text = derive_narration_from_scene_pack(pack_data)
    if not narration_text:
        warnings.append("voiceover_narration_empty_from_scene_pack")
        return _step(
            "voiceover_smoke",
            ok=False,
            output="",
            warnings=warnings,
            blocking_reasons=["narration_text_empty"],
        ), paths

    voice_dir = out_root.resolve() / f"full_voice_{run_id}"
    voice_dir.mkdir(parents=True, exist_ok=True)
    narration_path = voice_dir / "narration_script.txt"
    mp3_path = voice_dir / "full_voiceover.mp3"
    manifest_path = voice_dir / "voice_manifest.json"

    header = (
        "# BA 25.1 — REAL VIDEO BUILD VOICEOVER (smoke)\n"
        "# Narration aus scene_asset_pack abgeleitet; kein TTS-Live in BA 25.1.\n\n"
    )
    narration_path.write_text(header + narration_text.strip() + "\n", encoding="utf-8")
    paths["narration_script"] = str(narration_path.resolve())

    word_count = len(re.findall(r"\b\w+\b", narration_text))
    est_dur = voiceover_mod.estimate_speak_duration_seconds(word_count)

    which = which_ffmpeg_fn or voiceover_mod.which_ffmpeg
    ffmpeg_bin = which() or ""
    write_fn = write_smoke_mp3_fn or voiceover_mod._write_smoke_mp3_ffmpeg
    mp3_ok = False
    if not ffmpeg_bin:
        warnings.append("voiceover_smoke_skipped_ffmpeg_missing")
    elif est_dur < 1:
        warnings.append("voiceover_smoke_zero_duration")
    else:
        ok, br = write_fn(mp3_path, int(est_dur), ffmpeg_bin)
        if ok:
            mp3_ok = True
            paths["voiceover_audio"] = str(mp3_path.resolve())
        else:
            warnings.append("voiceover_smoke_mp3_write_failed")
            blocking.extend(list(br))

    voice_manifest = {
        "schema_version": "real_build_voice_manifest_v1",
        "run_id": run_id,
        "source_type": "scene_asset_pack_visual_prompts",
        "voice_mode_effective": "smoke",
        "word_count": int(word_count),
        "estimated_duration_seconds": int(est_dur),
        "narration_script_path": paths["narration_script"],
        "full_voiceover_path": paths["voiceover_audio"],
        "warnings": list(warnings),
    }
    try:
        manifest_path.write_text(
            json.dumps(voice_manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError:
        warnings.append("voiceover_manifest_write_failed")

    return _step(
        "voiceover_smoke",
        ok=mp3_ok or not blocking,  # narration ohne MP3 bleibt nutzbar (silent render)
        output=paths["voiceover_audio"] or paths["narration_script"],
        warnings=warnings,
        blocking_reasons=blocking,
        extra={
            "voice_manifest_path": str(manifest_path.resolve()),
            "estimated_duration_seconds": int(est_dur),
            "word_count": int(word_count),
            "real_tts_generated": False,
        },
    ), paths


def _load_pack(pack_path: Path) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    warns: List[str] = []
    p = pack_path.resolve()
    if not p.is_file():
        return None, ["scene_asset_pack_missing"]
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None, ["scene_asset_pack_invalid_json"]
    if not isinstance(data, dict):
        return None, ["scene_asset_pack_not_object"]
    se = data.get("scene_expansion")
    if not isinstance(se, dict):
        warns.append("scene_asset_pack_missing_scene_expansion")
    return data, warns


def run_real_video_build(
    *,
    run_id: str,
    scene_asset_pack: Path,
    out_root: Path,
    asset_mode: str = "placeholder",
    voice_mode: str = "smoke",
    motion_mode: str = "static",
    subtitle_style: str = "typewriter",
    subtitle_mode: str = "simple",
    force: bool = False,
    asset_runner_fn: Optional[Callable[..., Dict[str, Any]]] = None,
    timeline_writer_fn: Optional[Callable[..., Tuple[Path, Dict[str, Any]]]] = None,
    voiceover_smoke_fn: Optional[Callable[..., Tuple[Dict[str, Any], Dict[str, str]]]] = None,
    render_fn: Optional[Callable[..., Dict[str, Any]]] = None,
    subtitle_build_fn: Optional[Callable[..., Dict[str, Any]]] = None,
    burn_in_fn: Optional[Callable[..., Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Orchestriert die existierenden Build-Scripts.

    *_fn-Parameter sind nur für Tests gedacht. Default-Verhalten: Module
    dynamisch via ``importlib`` laden und die kanonischen Funktionen aufrufen.

    BA 25.1: kein URL-Input, keine echten Provider-Calls, kein Final Render.
    """
    rid = _s(run_id)
    if not _validate_run_id(rid):
        return _early_failure(
            run_id=rid,
            out_root=out_root,
            blocking_reasons=["invalid_run_id"],
            message="invalid run_id",
        )

    pack_path = Path(scene_asset_pack).resolve()
    out_root_p = Path(out_root).resolve()
    build_dir = out_root_p / f"real_build_{rid}"
    build_dir.mkdir(parents=True, exist_ok=True)

    pack_data, pack_warns = _load_pack(pack_path)
    if pack_data is None:
        return _finalize_and_write(
            build_dir=build_dir,
            run_id=rid,
            scene_asset_pack=pack_path,
            steps=[
                _step(
                    "load_scene_asset_pack",
                    ok=False,
                    output=str(pack_path),
                    warnings=pack_warns,
                    blocking_reasons=pack_warns or ["scene_asset_pack_invalid"],
                )
            ],
            paths={"scene_asset_pack": str(pack_path)},
            warnings=list(pack_warns),
            blocking_reasons=list(pack_warns or ["scene_asset_pack_invalid"]),
            status="blocked",
            metadata={"asset_mode": asset_mode, "voice_mode": voice_mode,
                      "motion_mode": motion_mode, "subtitle_style": subtitle_style,
                      "subtitle_mode": subtitle_mode, "force": bool(force)},
        )

    paths = _empty_paths()
    paths["scene_asset_pack"] = str(pack_path)
    paths["local_preview_dir"] = ""
    paths["final_render_dir"] = ""
    paths["final_video"] = ""

    warnings: List[str] = list(pack_warns)
    blocking: List[str] = []
    steps: List[Dict[str, Any]] = []

    asset_mod = _load_module("run_asset_runner_dyn", _ASSET_SCRIPT)
    timeline_mod = _load_module("build_timeline_manifest_dyn", _TIMELINE_SCRIPT)
    voice_mod = _load_module("build_full_voiceover_dyn", _VOICEOVER_SCRIPT)
    render_mod = _load_module("render_final_story_video_dyn", _RENDER_SCRIPT)
    subtitle_mod = _load_module("build_subtitle_file_dyn", _SUBTITLE_SCRIPT)
    burn_mod = _load_module("burn_in_subtitles_preview_dyn", _BURN_SCRIPT)

    a_fn = asset_runner_fn or asset_mod.run_local_asset_runner
    tl_fn = timeline_writer_fn or timeline_mod.write_timeline_manifest
    v_fn = voiceover_smoke_fn or _build_voiceover_smoke
    r_fn = render_fn or render_mod.render_final_story_video
    s_fn = subtitle_build_fn or subtitle_mod.build_subtitle_pack
    u_fn = burn_in_fn or burn_mod.burn_in_subtitles_preview

    metadata = {
        "asset_mode": asset_mode,
        "voice_mode": voice_mode,
        "motion_mode": motion_mode,
        "subtitle_style": subtitle_style,
        "subtitle_mode": subtitle_mode,
        "force": bool(force),
    }

    # A) Asset Runner
    try:
        asset_res = a_fn(
            pack_path,
            out_root_p,
            run_id=rid,
            mode=asset_mode,
        )
    except Exception as exc:
        steps.append(_step("asset_runner", ok=False, output=str(pack_path),
                           warnings=[f"asset_runner_exception:{type(exc).__name__}"],
                           blocking_reasons=["asset_runner_failed"]))
        blocking.append("asset_runner_failed")
        return _finalize_and_write(build_dir=build_dir, run_id=rid,
                                   scene_asset_pack=pack_path,
                                   steps=steps, paths=paths,
                                   warnings=warnings, blocking_reasons=blocking,
                                   status="failed", metadata=metadata)

    asset_warns = _list_str((asset_res or {}).get("warnings"))
    asset_manifest_path = _s((asset_res or {}).get("manifest_path"))
    paths["asset_manifest"] = asset_manifest_path
    asset_ok = bool((asset_res or {}).get("ok"))
    steps.append(_step(
        "asset_runner",
        ok=asset_ok,
        output=asset_manifest_path,
        warnings=asset_warns,
        blocking_reasons=[] if asset_ok else ["asset_runner_failed"],
        extra={"asset_count": (asset_res or {}).get("asset_count")},
    ))
    warnings.extend(asset_warns)
    if not asset_ok or not asset_manifest_path:
        blocking.append("asset_runner_failed")
        return _finalize_and_write(build_dir=build_dir, run_id=rid,
                                   scene_asset_pack=pack_path,
                                   steps=steps, paths=paths,
                                   warnings=warnings, blocking_reasons=blocking,
                                   status="failed", metadata=metadata)

    # B) Voiceover smoke (vor Timeline, damit audio_path direkt einfließt)
    try:
        voice_step, voice_paths = v_fn(
            pack_data=pack_data,
            run_id=rid,
            out_root=out_root_p,
            voice_mode=voice_mode,
            voiceover_mod=voice_mod,
        )
    except Exception as exc:
        voice_step = _step("voiceover_smoke", ok=False,
                           warnings=[f"voiceover_exception:{type(exc).__name__}"],
                           blocking_reasons=[])
        voice_paths = {"voiceover_audio": "", "narration_script": ""}
    steps.append(voice_step)
    warnings.extend(_list_str(voice_step.get("warnings")))
    paths["voiceover_audio"] = _resolve_or_blank(voice_paths.get("voiceover_audio"))
    paths["narration_script"] = _resolve_or_blank(voice_paths.get("narration_script"))

    if not paths["voiceover_audio"]:
        warnings.append("timeline_audio_path_not_wired")

    # C) Timeline Builder (audio_path optional)
    try:
        am_data = json.loads(Path(asset_manifest_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        steps.append(_step("timeline_builder", ok=False, output=asset_manifest_path,
                           warnings=[f"asset_manifest_load_failed:{type(exc).__name__}"],
                           blocking_reasons=["asset_manifest_invalid"]))
        blocking.append("asset_manifest_invalid")
        return _finalize_and_write(build_dir=build_dir, run_id=rid,
                                   scene_asset_pack=pack_path,
                                   steps=steps, paths=paths,
                                   warnings=warnings, blocking_reasons=blocking,
                                   status="failed", metadata=metadata)

    audio_arg: Optional[Path] = (
        Path(paths["voiceover_audio"]) if paths["voiceover_audio"] else None
    )
    try:
        tl_path, _tl_body = tl_fn(
            am_data,
            asset_manifest_path=Path(asset_manifest_path),
            audio_path=audio_arg,
            run_id=rid,
            scene_duration_seconds=4,
            out_root=out_root_p,
        )
        tl_path_str = str(Path(tl_path).resolve())
        paths["timeline_manifest"] = tl_path_str
        steps.append(_step("timeline_builder", ok=True, output=tl_path_str,
                           extra={"audio_path_set": bool(audio_arg)}))
    except Exception as exc:
        steps.append(_step("timeline_builder", ok=False,
                           warnings=[f"timeline_writer_exception:{type(exc).__name__}"],
                           blocking_reasons=["timeline_builder_failed"]))
        blocking.append("timeline_builder_failed")
        return _finalize_and_write(build_dir=build_dir, run_id=rid,
                                   scene_asset_pack=pack_path,
                                   steps=steps, paths=paths,
                                   warnings=warnings, blocking_reasons=blocking,
                                   status="failed", metadata=metadata)

    # D) Clean Render
    clean_video_path = build_dir / "clean_video.mp4"
    try:
        render_res = r_fn(
            Path(paths["timeline_manifest"]),
            output_video=clean_video_path,
            motion_mode=motion_mode,
            subtitle_path=None,
            run_id=rid,
            write_output_manifest=True,
            manifest_root=out_root_p,
        )
    except Exception as exc:
        steps.append(_step("clean_render", ok=False,
                           warnings=[f"render_exception:{type(exc).__name__}"],
                           blocking_reasons=["clean_render_failed"]))
        blocking.append("clean_render_failed")
        return _finalize_and_write(build_dir=build_dir, run_id=rid,
                                   scene_asset_pack=pack_path,
                                   steps=steps, paths=paths,
                                   warnings=warnings, blocking_reasons=blocking,
                                   status="failed", metadata=metadata)

    render_warns = _list_str((render_res or {}).get("warnings"))
    render_ok = bool((render_res or {}).get("video_created"))
    if render_ok:
        paths["clean_video"] = str(clean_video_path.resolve())
    steps.append(_step(
        "clean_render",
        ok=render_ok,
        output=paths["clean_video"] or str(clean_video_path),
        warnings=render_warns,
        blocking_reasons=_list_str((render_res or {}).get("blocking_reasons")) if not render_ok else [],
    ))
    warnings.extend(render_warns)
    if not render_ok:
        blocking.extend(_list_str((render_res or {}).get("blocking_reasons")) or ["clean_render_failed"])
        return _finalize_and_write(build_dir=build_dir, run_id=rid,
                                   scene_asset_pack=pack_path,
                                   steps=steps, paths=paths,
                                   warnings=warnings, blocking_reasons=blocking,
                                   status="failed", metadata=metadata)

    # E) Subtitle Build
    try:
        sub_res = s_fn(
            Path(paths["narration_script"]) if paths["narration_script"] else build_dir / "missing_narration.txt",
            timeline_manifest_path=Path(paths["timeline_manifest"]),
            out_root=out_root_p,
            run_id=rid,
            subtitle_mode=subtitle_mode,
            subtitle_source="narration",
            subtitle_style=subtitle_style,
            audio_path=Path(paths["voiceover_audio"]) if paths["voiceover_audio"] else None,
        )
    except Exception as exc:
        steps.append(_step("subtitle_build", ok=False,
                           warnings=[f"subtitle_build_exception:{type(exc).__name__}"],
                           blocking_reasons=["subtitle_build_failed"]))
        blocking.append("subtitle_build_failed")
        return _finalize_and_write(build_dir=build_dir, run_id=rid,
                                   scene_asset_pack=pack_path,
                                   steps=steps, paths=paths,
                                   warnings=warnings, blocking_reasons=blocking,
                                   status="failed", metadata=metadata)

    sub_warns = _list_str((sub_res or {}).get("warnings"))
    sub_ok = bool((sub_res or {}).get("ok"))
    sub_manifest = _s((sub_res or {}).get("subtitle_manifest_path"))
    sub_srt = _s((sub_res or {}).get("subtitles_srt_path"))
    paths["subtitle_manifest"] = sub_manifest
    paths["subtitle_file"] = sub_srt
    steps.append(_step(
        "subtitle_build",
        ok=sub_ok,
        output=sub_manifest,
        warnings=sub_warns,
        blocking_reasons=_list_str((sub_res or {}).get("blocking_reasons")) if not sub_ok else [],
    ))
    warnings.extend(sub_warns)
    if not sub_ok or not sub_manifest:
        blocking.extend(_list_str((sub_res or {}).get("blocking_reasons")) or ["subtitle_build_failed"])
        return _finalize_and_write(build_dir=build_dir, run_id=rid,
                                   scene_asset_pack=pack_path,
                                   steps=steps, paths=paths,
                                   warnings=warnings, blocking_reasons=blocking,
                                   status="failed", metadata=metadata)

    # F) Burn-in Preview
    try:
        burn_res = u_fn(
            Path(paths["clean_video"]),
            Path(sub_manifest),
            out_root=out_root_p,
            run_id=rid,
            force=bool(force),
        )
    except Exception as exc:
        steps.append(_step("burn_in_preview", ok=False,
                           warnings=[f"burn_exception:{type(exc).__name__}"],
                           blocking_reasons=["burn_in_failed"]))
        blocking.append("burn_in_failed")
        return _finalize_and_write(build_dir=build_dir, run_id=rid,
                                   scene_asset_pack=pack_path,
                                   steps=steps, paths=paths,
                                   warnings=warnings, blocking_reasons=blocking,
                                   status="failed", metadata=metadata)

    burn_warns = _list_str((burn_res or {}).get("warnings"))
    burn_ok = bool((burn_res or {}).get("ok"))
    burn_skipped = bool((burn_res or {}).get("skipped"))
    preview_path = _s((burn_res or {}).get("output_video_path"))
    if preview_path:
        paths["preview_with_subtitles"] = preview_path
    steps.append(_step(
        "burn_in_preview",
        ok=burn_ok,
        output=preview_path,
        warnings=burn_warns,
        blocking_reasons=_list_str((burn_res or {}).get("blocking_reasons")) if not burn_ok else [],
        extra={"skipped": burn_skipped},
    ))
    warnings.extend(burn_warns)
    if not burn_ok:
        blocking.extend(_list_str((burn_res or {}).get("blocking_reasons")) or ["burn_in_failed"])
        return _finalize_and_write(build_dir=build_dir, run_id=rid,
                                   scene_asset_pack=pack_path,
                                   steps=steps, paths=paths,
                                   warnings=warnings, blocking_reasons=blocking,
                                   status="failed", metadata=metadata)

    status = "completed" if (burn_ok and (burn_skipped or preview_path)) else "blocked"
    return _finalize_and_write(build_dir=build_dir, run_id=rid,
                               scene_asset_pack=pack_path,
                               steps=steps, paths=paths,
                               warnings=warnings, blocking_reasons=blocking,
                               status=status, metadata=metadata)


def _finalize_and_write(
    *,
    build_dir: Path,
    run_id: str,
    scene_asset_pack: Path,
    steps: List[Dict[str, Any]],
    paths: Dict[str, str],
    warnings: List[str],
    blocking_reasons: List[str],
    status: str,
    metadata: Dict[str, Any],
) -> Dict[str, Any]:
    norm_paths = _empty_paths()
    for k, v in (paths or {}).items():
        if k in norm_paths:
            norm_paths[k] = _s(v)
    seen_w: List[str] = []
    for w in warnings or []:
        if w and w not in seen_w:
            seen_w.append(w)
    seen_b: List[str] = []
    for b in blocking_reasons or []:
        if b and b not in seen_b:
            seen_b.append(b)
    overall_ok = (status == "completed") and not seen_b
    payload = {
        "schema_version": REAL_BUILD_RESULT_SCHEMA,
        "run_id": run_id,
        "ok": bool(overall_ok),
        "status": status,
        "build_dir": str(build_dir.resolve()),
        "scene_asset_pack": str(scene_asset_pack.resolve()) if scene_asset_pack else "",
        "metadata": dict(metadata or {}),
        "steps": list(steps or []),
        "paths": norm_paths,
        "warnings": seen_w,
        "blocking_reasons": seen_b,
        "next_step": _next_step_for_status(status),
        "created_at_epoch": time.time(),
    }
    try:
        result_path = write_real_video_build_result(build_dir=build_dir, payload=payload)
        payload["paths_self"] = result_path
    except OSError as exc:
        payload["warnings"].append(f"real_video_build_result_write_failed:{type(exc).__name__}")
    return payload


def _early_failure(
    *,
    run_id: str,
    out_root: Path,
    blocking_reasons: List[str],
    message: str,
) -> Dict[str, Any]:
    return {
        "schema_version": REAL_BUILD_RESULT_SCHEMA,
        "run_id": _s(run_id),
        "ok": False,
        "status": "blocked",
        "build_dir": "",
        "scene_asset_pack": "",
        "metadata": {},
        "steps": [],
        "paths": _empty_paths(),
        "warnings": [],
        "blocking_reasons": list(blocking_reasons or []),
        "next_step": message or "Eingabe prüfen.",
        "created_at_epoch": time.time(),
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "BA 25.1 — Real Video Build Orchestrator CLI: verbindet vorhandene "
            "Build-Scripts (Asset Runner / Timeline / Voiceover-Smoke / Render / "
            "Subtitles / Burn-in) zu einem real_build_<run_id>-Indexpaket. "
            "Kein URL-Input, kein Final Render."
        )
    )
    parser.add_argument("--run-id", required=True, dest="run_id")
    parser.add_argument(
        "--scene-asset-pack",
        type=Path,
        required=True,
        dest="scene_asset_pack",
        help="Pfad zu scene_asset_pack.json (BA 18.2 Export oder Fixture).",
    )
    parser.add_argument(
        "--out-root",
        type=Path,
        default=ROOT / "output",
        dest="out_root",
    )
    parser.add_argument(
        "--asset-mode",
        choices=("placeholder", "live"),
        default="placeholder",
        dest="asset_mode",
    )
    parser.add_argument(
        "--voice-mode",
        choices=("smoke",),
        default="smoke",
        dest="voice_mode",
        help="BA 25.1 nur smoke (TTS-Live folgt BA 25.2/25.3).",
    )
    parser.add_argument(
        "--motion-mode",
        choices=("static", "basic"),
        default="static",
        dest="motion_mode",
    )
    parser.add_argument(
        "--subtitle-style",
        choices=("classic", "word_by_word", "typewriter", "karaoke", "none"),
        default="typewriter",
        dest="subtitle_style",
    )
    parser.add_argument(
        "--subtitle-mode",
        choices=("none", "simple"),
        default="simple",
        dest="subtitle_mode",
    )
    parser.add_argument("--force", action="store_true", dest="force")
    parser.add_argument("--print-json", action="store_true", dest="print_json")
    args = parser.parse_args(argv)

    rid = _s(args.run_id)
    if not _validate_run_id(rid):
        err = _early_failure(
            run_id=rid,
            out_root=args.out_root,
            blocking_reasons=["invalid_run_id"],
            message="invalid run_id (A–Z, 0–9, _, -)",
        )
        if args.print_json:
            print(json.dumps(err, ensure_ascii=False, indent=2))
        return 3

    if not Path(args.scene_asset_pack).is_file():
        err = _early_failure(
            run_id=rid,
            out_root=args.out_root,
            blocking_reasons=["scene_asset_pack_missing"],
            message="scene_asset_pack file missing",
        )
        if args.print_json:
            print(json.dumps(err, ensure_ascii=False, indent=2))
        return 3

    try:
        result = run_real_video_build(
            run_id=rid,
            scene_asset_pack=Path(args.scene_asset_pack),
            out_root=Path(args.out_root),
            asset_mode=args.asset_mode,
            voice_mode=args.voice_mode,
            motion_mode=args.motion_mode,
            subtitle_style=args.subtitle_style,
            subtitle_mode=args.subtitle_mode,
            force=bool(args.force),
        )
    except Exception as exc:
        msg = str(exc)[:400]
        err = _early_failure(
            run_id=rid,
            out_root=args.out_root,
            blocking_reasons=["unexpected_exception"],
            message=msg or "unexpected error",
        )
        if args.print_json:
            print(json.dumps(err, ensure_ascii=False, indent=2))
        return 1

    if args.print_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))

    status = _s(result.get("status")).lower()
    if status == "completed":
        return 0
    if status == "blocked":
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
