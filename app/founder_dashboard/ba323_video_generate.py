"""BA 32.3 — Founder Dashboard: URL → ``run_ba265_url_to_final`` (ohne Shell-Subprocess)."""

from __future__ import annotations

import importlib.util
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_run_url_to_final_mod():
    p = _REPO_ROOT / "scripts" / "run_url_to_final_mp4.py"
    name = "run_url_to_final_mp4_ba323"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, p)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def runway_live_configured() -> bool:
    """Nur Präsenzsignal — niemals Key-Werte loggen oder zurückgeben."""
    return bool((os.environ.get("RUNWAY_API_KEY") or "").strip())


def resolve_voice_mode_dashboard(requested: str) -> Tuple[str, List[str]]:
    """Mappt Dashboard-Strings auf ``run_ba265_url_to_final``-Voice-Modi."""
    warns: List[str] = []
    r = (requested or "").strip().lower()
    if r in ("elevenlabs_or_safe_default", ""):
        if (os.environ.get("ELEVENLABS_API_KEY") or "").strip():
            return "elevenlabs", warns
        warns.append("ba323_voice_mode_fallback_dummy_no_elevenlabs_key")
        return "dummy", warns
    allowed = frozenset({"none", "elevenlabs", "dummy", "openai", "existing"})
    if r not in allowed:
        warns.append("ba323_voice_mode_unknown_fallback_dummy")
        return "dummy", warns
    if r == "elevenlabs" and not (os.environ.get("ELEVENLABS_API_KEY") or "").strip():
        warns.append("ba323_voice_elevenlabs_requested_fallback_dummy")
        return "dummy", warns
    if r == "openai" and not (os.environ.get("OPENAI_API_KEY") or "").strip():
        warns.append("ba323_voice_openai_requested_fallback_dummy")
        return "dummy", warns
    return r, warns


def new_video_gen_run_id() -> str:
    return f"video_gen_10m_{int(time.time() * 1000)}"


def video_generate_output_dir(out_root: Path, run_id: str) -> Path:
    base = Path(out_root).resolve()
    return (base / "video_generate" / str(run_id).strip()).resolve()


def execute_dashboard_video_generate(
    *,
    url: str,
    output_dir: Path,
    run_id: str,
    duration_target_seconds: int,
    max_scenes: int,
    max_live_assets: int,
    motion_clip_every_seconds: int,
    motion_clip_duration_seconds: int,
    max_motion_clips: int,
    allow_live_assets: bool,
    allow_live_motion: bool,
    voice_mode: str,
    motion_mode: str,
) -> Dict[str, Any]:
    """
    Ruft ``run_ba265_url_to_final`` auf. Live-Motion erzeugt keine Runway-Clips
    in dieser Pipeline — nur Metadaten + ggf. Warnungen.
    """
    mod = _load_run_url_to_final_mod()
    vm, vm_warns = resolve_voice_mode_dashboard(voice_mode)
    live_motion_available = runway_live_configured()
    warnings_extra: List[str] = list(vm_warns)

    if allow_live_motion and live_motion_available:
        warnings_extra.append(
            "ba323_live_motion_runway_configured_but_url_to_final_does_not_ingest_runway_clips"
        )

    mm = (motion_mode or "basic").strip().lower()
    if mm not in ("static", "basic"):
        mm = "basic"
        warnings_extra.append("ba323_motion_mode_invalid_fallback_basic")

    doc = mod.run_ba265_url_to_final(
        url=(url or "").strip(),
        script_json_path=None,
        out_dir=Path(output_dir).resolve(),
        max_scenes=int(max_scenes),
        duration_seconds=int(duration_target_seconds),
        asset_dir=None,
        run_id=str(run_id).strip(),
        motion_mode=mm,
        voice_mode=vm,
        asset_runner_mode="live" if allow_live_assets else "placeholder",
        max_live_assets=int(max_live_assets) if allow_live_assets else None,
        motion_clip_every_seconds=int(motion_clip_every_seconds),
        motion_clip_duration_seconds=int(motion_clip_duration_seconds),
        max_motion_clips=int(max_motion_clips),
    )

    warnings = list(doc.get("warnings") or []) + warnings_extra
    blocking = list(doc.get("blocking_reasons") or [])
    ok = bool(doc.get("ok"))

    motion_strategy = {
        "motion_clip_every_seconds": int(motion_clip_every_seconds),
        "motion_clip_duration_seconds": int(motion_clip_duration_seconds),
        "max_motion_clips": int(max_motion_clips),
        "live_motion_available": bool(live_motion_available),
        "allow_live_motion_requested": bool(allow_live_motion),
    }

    next_action = "Final Video prüfen" if ok else "Fehler prüfen und Parameter anpassen"

    return {
        "ok": ok,
        "run_id": str(run_id).strip(),
        "output_dir": str(doc.get("output_dir") or ""),
        "final_video_path": str(doc.get("final_video_path") or ""),
        "script_path": str(doc.get("script_path") or ""),
        "scene_asset_pack_path": str(doc.get("scene_asset_pack_path") or ""),
        "asset_manifest_path": str(doc.get("asset_manifest_path") or ""),
        "duration_target_seconds": int(duration_target_seconds),
        "max_scenes": int(max_scenes),
        "max_live_assets": int(max_live_assets),
        "motion_strategy": motion_strategy,
        "warnings": warnings,
        "blocking_reasons": blocking,
        "next_action": next_action,
    }
