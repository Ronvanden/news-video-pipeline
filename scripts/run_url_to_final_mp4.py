"""BA 26.5 — Founder-Run: URL oder script.json + vorhandene Assets → final_video.mp4 (ohne Provider-Pflicht).

BA 26.7 — ElevenLabs Voice Founder Integration: optional `--voice-mode`
(`none` | `existing` | `elevenlabs` | `dummy` | `openai`) erzeugt einen
Voiceover, übergibt ihn der bestehenden Timeline → Render-Kette und ergänzt
`run_summary.json` um Voice-Felder. **Kein** neuer Provider, **kein** neues
Voice-Portal. Wiederverwendung der vorhandenen
``scripts/build_full_voiceover.py``-Synthese-Funktionen.

BA 26.7b — Fit Video Duration to Voice: optional `--fit-video-to-voice` plus
`--voice-fit-padding-seconds` passt nach erfolgreicher Voice-Ermittlung die
Szenen-/Timeline-Dauer an ``voice_duration + padding`` an (Minimum gesichert),
damit `final_video.mp4` nicht deutlich länger als die Stimme läuft.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.real_video_build.script_input_adapter import (  # type: ignore
    _scenes_from_chapters_like,
    _scenes_from_full_script,
    _visual_prompt_from_text,
)
from app.utils import build_script_response_from_extracted_text, extract_text_from_url  # type: ignore

import importlib.util

_ASSET_RUNNER = ROOT / "scripts" / "run_asset_runner.py"
_TIMELINE = ROOT / "scripts" / "build_timeline_manifest.py"
_RENDER = ROOT / "scripts" / "render_final_story_video.py"
_VOICEOVER = ROOT / "scripts" / "build_full_voiceover.py"

_VOICE_MODES = ("none", "existing", "elevenlabs", "dummy", "openai")
_VOICE_AUDIO_SUFFIXES = {".mp3", ".wav", ".m4a"}
_DEFAULT_DUMMY_VOICE_SECONDS = 8
_DEFAULT_VOICE_FIT_PADDING_SECONDS = 0.75


def _load_submodule(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _tolerant_script(data: Any) -> Dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError("script must be a JSON object")
    ch = data.get("chapters")
    if ch is not None and not isinstance(ch, list):
        ch = []
    src = data.get("sources")
    if src is not None and not isinstance(src, list):
        src = [str(src)] if src else []
    wr = data.get("warnings")
    if wr is not None and not isinstance(wr, list):
        wr = [str(wr)] if wr else []
    return {
        "title": str(data.get("title") or "").strip(),
        "hook": str(data.get("hook") or "").strip(),
        "chapters": list(ch or []),
        "full_script": str(data.get("full_script") or "").strip(),
        "sources": [str(x).strip() for x in (src or []) if str(x).strip()],
        "warnings": [str(x).strip() for x in (wr or []) if str(x).strip()],
    }


def _collect_assets(asset_dir: Optional[Path]) -> Tuple[List[Path], List[Path]]:
    if asset_dir is None or not asset_dir.is_dir():
        return [], []
    v_ext = {".mp4", ".mov", ".webm"}
    i_ext = {".png", ".jpg", ".jpeg"}
    videos: List[Path] = []
    images: List[Path] = []
    for p in sorted(asset_dir.rglob("*")):
        if not p.is_file():
            continue
        suf = p.suffix.lower()
        if suf in v_ext:
            videos.append(p.resolve())
        elif suf in i_ext:
            images.append(p.resolve())
    return videos, images


def _rel_to_pack(abs_path: Path, pack_parent: Path) -> str:
    return Path(os.path.relpath(abs_path, pack_parent)).as_posix()


def _build_scene_rows_from_script(
    script: Dict[str, Any],
    *,
    max_scenes: int,
    total_duration_seconds: int,
) -> List[Dict[str, Any]]:
    """Hook + Kapitel → Liste von Szenen-Dicts (title, narration) max. max_scenes."""
    rows: List[Dict[str, Any]] = []
    hook = str(script.get("hook") or "").strip()
    if hook and max_scenes > 0:
        rows.append({"title": "Hook", "narration": hook})
    rows.extend(_scenes_from_chapters_like(script.get("chapters")))
    if not rows:
        rows = _scenes_from_full_script(script.get("full_script") or "")
    cleaned: List[Dict[str, str]] = []
    for r in rows:
        narration = str((r or {}).get("narration") or "").strip()
        if not narration:
            continue
        title = str((r or {}).get("title") or "").strip() or f"Szene {len(cleaned) + 1}"
        cleaned.append({"title": title, "narration": narration})
    if not cleaned:
        raise ValueError("no_scenes_from_script")
    cleaned = cleaned[:max_scenes]
    n = len(cleaned)
    total = max(n * 5, int(total_duration_seconds))
    base = total // n
    rem = total % n
    out: List[Dict[str, Any]] = []
    for i, r in enumerate(cleaned):
        dur = base + (1 if i < rem else 0)
        if dur < 5:
            dur = 5
        title = r["title"]
        narration = r["narration"]
        out.append(
            {
                "title": title,
                "narration": narration,
                "duration_seconds": dur,
                "visual_prompt": _visual_prompt_from_text(title, narration)[1],
            }
        )
    return out


def _assign_media(
    n_scenes: int,
    videos: Sequence[Path],
    images: Sequence[Path],
    pack_parent: Path,
) -> Tuple[List[Optional[str]], Dict[int, Path], List[str]]:
    """
    Pro Szene (1..n): optional runway_clip_path (rel.), optional Post-Runner-Bild.

    BA 26.6: Wenn weniger Videos als Szenen vorliegen, wird **dasselbe** Video
    für alle restlichen Szenen wiederverwendet (Reuse-Loop), damit der Founder-Run
    nicht in Standbild-Placeholder abrutscht. Kein neuer Provider-Call; ffmpeg
    übernimmt Loop/Trim per `-stream_loop` (Render-Logik unverändert).
    """
    warns: List[str] = []
    rel_videos: List[Optional[str]] = [None] * n_scenes
    img_ov: Dict[int, Path] = {}
    if videos:
        for i in range(n_scenes):
            src_idx = i if i < len(videos) else len(videos) - 1
            rel_videos[i] = _rel_to_pack(videos[src_idx], pack_parent)
        if len(videos) < n_scenes:
            warns.append("ba266_video_reuse_for_remaining_scenes")
    elif images:
        for i in range(n_scenes):
            sn = i + 1
            img_ov[sn] = images[i % len(images)]
    if not videos and not images:
        warns.append("no_assets_in_asset_dir_using_placeholder")
    elif videos or images:
        warns.append("existing_asset_used")
    if not videos:
        warns.append("no_existing_video_asset_found_using_fallback")
    return rel_videos, img_ov, warns


def _draw_cinematic_placeholder_png(out_path: Path, *, scene_number: int, total_scenes: int) -> None:
    """
    BA 26.6 — textfreie cinematic Placeholder (kein Szene-Label, kein Prompt-Snippet).

    Erzeugt ein 960×540 PNG mit weichem Vertikal-Verlauf, dezenter Vignette und
    ruhigen Akzentlinien — **ohne** Schrift, ohne Badges, ohne ``DRAFT``-Hinweis.
    Bewusst **deterministisch identisch** für alle Szenen: visuelle Variation
    entsteht im Render über `motion_mode=basic` (Ken-Burns-Zoompan), nicht über
    Standbild-Tönung. ``scene_number`` / ``total_scenes`` bleiben in der Signatur
    für künftige Erweiterungen, beeinflussen das Bild aktuell aber nicht.
    """
    del scene_number, total_scenes
    from PIL import Image, ImageDraw

    w, h = 960, 540
    base_top = (22, 28, 42)
    base_bot = (4, 6, 12)
    img = Image.new("RGB", (w, h), color=base_top)
    draw = ImageDraw.Draw(img)
    for y in range(h):
        ty = y / max(h - 1, 1)
        r = int(base_top[0] + (base_bot[0] - base_top[0]) * ty)
        g = int(base_top[1] + (base_bot[1] - base_top[1]) * ty)
        b = int(base_top[2] + (base_bot[2] - base_top[2]) * ty)
        draw.line([(0, y), (w, y)], fill=(r, g, b))
    cx, cy = w / 2.0, h / 2.0
    max_r2 = (cx * cx + cy * cy)
    vignette = Image.new("L", (w, h), 0)
    vd = ImageDraw.Draw(vignette)
    for y in range(h):
        for x in range(0, w, 2):
            dx = x - cx
            dy = y - cy
            r2 = (dx * dx + dy * dy) / max_r2
            v = int(min(120, max(0, r2 * 140)))
            vd.point((x, y), fill=v)
    black = Image.new("RGB", (w, h), (0, 0, 0))
    img = Image.composite(black, img, vignette)
    draw = ImageDraw.Draw(img)
    accent = (140, 110, 70)
    draw.rectangle([0, 0, w, 2], fill=accent)
    draw.rectangle([0, h - 2, w, h], fill=(accent[0] // 3, accent[1] // 3, accent[2] // 3))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="PNG")


def _apply_cinematic_placeholders(
    gen_dir: Path,
    manifest_path: Path,
    *,
    image_override_scenes: Sequence[int],
) -> List[str]:
    """
    BA 26.6 — Überschreibt nach dem Asset-Runner alle PNGs für **Bild**-Szenen
    (nur dort, wo kein Video gesetzt ist und kein expliziter Image-Override aus
    `--asset-dir` greift) durch eine textfreie cinematic Variante. Manifest
    bleibt strukturell unverändert.
    """
    warns: List[str] = []
    if not manifest_path.is_file():
        return warns
    try:
        man = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        warns.append("ba266_cinematic_manifest_unreadable")
        return warns
    assets = man.get("assets") or []
    skip = {int(s) for s in image_override_scenes if int(s) > 0}
    total = sum(1 for a in assets if isinstance(a, dict))
    overridden = 0
    for asset in assets:
        if not isinstance(asset, dict):
            continue
        sn = int(asset.get("scene_number") or 0)
        if sn <= 0 or sn in skip:
            continue
        img_name = str(asset.get("image_path") or "").strip()
        if not img_name:
            continue
        target = gen_dir / img_name
        try:
            _draw_cinematic_placeholder_png(target, scene_number=sn, total_scenes=max(1, total))
            overridden += 1
        except (OSError, ValueError) as exc:
            warns.append(f"ba266_cinematic_render_failed:{type(exc).__name__}:{sn}")
    if overridden > 0:
        warns.append(f"ba266_cinematic_placeholder_applied:{overridden}")
    return warns


def _build_scene_plan(
    scene_rows: List[Dict[str, Any]],
    *,
    script_title: str,
) -> Dict[str, Any]:
    scenes_out: List[Dict[str, Any]] = []
    for i, row in enumerate(scene_rows, start=1):
        scenes_out.append(
            {
                "scene_id": f"sc_{i:03d}",
                "title": row.get("title"),
                "voiceover_text": row.get("narration"),
                "duration_seconds": int(row.get("duration_seconds") or 6),
                "visual_prompt": row.get("visual_prompt") or "",
                "image_prompt": None,
                "video_prompt": None,
            }
        )
    return {"title": script_title, "scenes": scenes_out}


def _build_scene_asset_pack(
    scene_rows: List[Dict[str, Any]],
    *,
    script: Dict[str, Any],
    rel_videos: Sequence[Optional[str]],
    pack_parent: Path,
) -> Dict[str, Any]:
    expanded: List[Dict[str, Any]] = []
    for i, row in enumerate(scene_rows):
        sn = i + 1
        beat: Dict[str, Any] = {
            "chapter_index": 0,
            "beat_index": i,
            "visual_prompt": str(row.get("visual_prompt") or ""),
            "camera_motion_hint": "static",
            "duration_seconds": int(row.get("duration_seconds") or 6),
            "asset_type": "broll",
            "continuity_note": "",
            "safety_notes": [],
            "narration": str(row.get("narration") or ""),
            "voiceover_text": str(row.get("narration") or ""),
            "scene_title": str(row.get("title") or f"Szene {sn}"),
        }
        rv = rel_videos[i] if i < len(rel_videos) else None
        if rv:
            beat["runway_clip_path"] = rv
        expanded.append(beat)
    pack: Dict[str, Any] = {
        "export_version": "18.2-v1",
        "source_label": "ba265_url_to_final",
        "template_type": "documentary_news",
        "title": script.get("title") or "",
        "hook": script.get("hook") or "",
        "metadata": {
            "ba265": {
                "pipeline": "url_to_final_mp4",
                "script_sources": script.get("sources") or [],
                "script_warnings": script.get("warnings") or [],
            }
        },
        "scene_expansion": {"expanded_scene_assets": expanded},
    }
    return pack


def _apply_post_runner_images(gen_dir: Path, manifest_path: Path, overrides: Dict[int, Path]) -> None:
    if not overrides:
        return
    man = json.loads(manifest_path.read_text(encoding="utf-8"))
    assets = man.get("assets") or []
    for asset in assets:
        if not isinstance(asset, dict):
            continue
        sn = int(asset.get("scene_number") or 0)
        if sn not in overrides:
            continue
        if str(asset.get("video_path") or "").strip():
            continue
        src = overrides[sn]
        suf = src.suffix.lower() if src.suffix else ".png"
        dest = gen_dir / f"scene_{sn:03d}_ba265img{suf}"
        shutil.copy2(src, dest)
        asset["image_path"] = dest.name
    manifest_path.write_text(json.dumps(man, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# BA 26.7 — Voice helpers
# ---------------------------------------------------------------------------


def _collect_voiceover_text(scene_rows: Sequence[Dict[str, Any]]) -> str:
    """
    Bauspeisende Funktion für den ElevenLabs-Founder-Run: Verkettet die
    Narration-Texte aus den Szenen zu einem zusammenhängenden, vorlesbaren
    Block. Bewusst **ohne** ``Szene N``-Labels, ohne ``Chapter X``,
    ohne JSON-Strukturen, ohne technische IDs.
    """
    parts: List[str] = []
    for row in scene_rows or []:
        narration = str((row or {}).get("narration") or "").strip()
        if narration:
            parts.append(narration)
    return "\n\n".join(parts).strip()


def _validate_voice_file(p: Path) -> Tuple[bool, str]:
    if not p.is_file():
        return False, "voice_file_missing"
    suf = p.suffix.lower()
    if suf not in _VOICE_AUDIO_SUFFIXES:
        return False, f"voice_file_bad_extension:{suf or 'none'}"
    if p.stat().st_size <= 0:
        return False, "voice_file_empty"
    return True, ""


def _resolve_voice_output(out_dir: Path, voice_output: Optional[Path], *, suffix: str = ".mp3") -> Path:
    if voice_output is not None:
        target = Path(voice_output)
        if not target.is_absolute():
            target = (out_dir / target).resolve()
        return target
    return (out_dir / f"voiceover{suffix}").resolve()


def _probe_audio_duration_seconds(audio_path: Path) -> Optional[float]:
    """ffprobe-basierte Dauer (Sekunden) — robust None bei Fehler/missing."""
    ffprobe = shutil.which("ffprobe")
    if not ffprobe or not audio_path.is_file():
        return None
    try:
        import subprocess

        out = subprocess.run(
            [ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(audio_path)],
            capture_output=True,
            text=True,
            check=True,
        )
        s = (out.stdout or "").strip()
        return float(s) if s else None
    except (OSError, ValueError, subprocess.CalledProcessError):
        return None


def _synthesize_voice(
    voice_mode: str,
    voiceover_text: str,
    *,
    out_dir: Path,
    voice_file: Optional[Path],
    voice_output: Optional[Path],
    elevenlabs_voice_id: Optional[str],
    elevenlabs_model: Optional[str],
    tts_voice: Optional[str],
    elevenlabs_post_override: Optional[Callable[..., bytes]] = None,
    openai_post_override: Optional[Callable[..., bytes]] = None,
    dummy_seconds: int = _DEFAULT_DUMMY_VOICE_SECONDS,
) -> Dict[str, Any]:
    """
    Erzeugt (oder übernimmt) eine Audiodatei und gibt strukturierte Voice-Meta zurück.

    Rückgabewerte (immer alle Felder gesetzt — kein Crash bei Fehlern):
      ``voice_used`` (bool), ``voice_mode``, ``voice_file_path``,
      ``voice_duration_seconds`` (Optional[float]), ``voice_warnings`` (List[str]),
      ``voice_blocking_reasons`` (List[str]).

    **Secrets:** API-Key wird nie in Warnings/Blockers protokolliert.
    """
    mode = (voice_mode or "none").strip().lower()
    out: Dict[str, Any] = {
        "voice_used": False,
        "voice_mode": mode,
        "voice_file_path": None,
        "voice_duration_seconds": None,
        "voice_warnings": [],
        "voice_blocking_reasons": [],
    }

    if mode not in _VOICE_MODES:
        out["voice_warnings"].append(f"voice_mode_unknown_defaulting_none:{mode}")
        out["voice_mode"] = "none"
        return out

    if mode == "none":
        return out

    if mode == "existing":
        if voice_file is None:
            out["voice_blocking_reasons"].append("voice_file_required_for_existing_mode")
            return out
        ok, err = _validate_voice_file(Path(voice_file))
        if not ok:
            out["voice_blocking_reasons"].append(err)
            return out
        src = Path(voice_file).resolve()
        out["voice_used"] = True
        out["voice_file_path"] = str(src)
        out["voice_duration_seconds"] = _probe_audio_duration_seconds(src)
        return out

    text = (voiceover_text or "").strip()
    if mode != "dummy" and not text:
        out["voice_blocking_reasons"].append("voiceover_text_empty")
        return out

    target_mp3 = _resolve_voice_output(out_dir, voice_output, suffix=".mp3")
    target_mp3.parent.mkdir(parents=True, exist_ok=True)

    ffmpeg = shutil.which("ffmpeg")

    if mode == "dummy":
        if not ffmpeg:
            out["voice_blocking_reasons"].append("dummy_voice_requires_ffmpeg")
            return out
        try:
            voice_mod = _load_submodule("build_full_voiceover_ba267_dummy", _VOICEOVER)
            ok, br = voice_mod._write_smoke_mp3_ffmpeg(target_mp3, max(1, int(dummy_seconds)), ffmpeg)
        except (OSError, AttributeError) as exc:
            out["voice_blocking_reasons"].append(f"dummy_voice_module_failed:{type(exc).__name__}")
            return out
        if not ok:
            out["voice_blocking_reasons"].extend(br or ["dummy_voice_render_failed"])
            return out
        out["voice_used"] = True
        out["voice_file_path"] = str(target_mp3)
        out["voice_duration_seconds"] = float(max(1, int(dummy_seconds)))
        out["voice_warnings"].append("dummy_voice_used_not_real_tts")
        return out

    if mode == "elevenlabs":
        api_key_present = bool((os.environ.get("ELEVENLABS_API_KEY") or "").strip())
        if not api_key_present and elevenlabs_post_override is None:
            out["voice_blocking_reasons"].append("elevenlabs_missing_api_key")
            return out
        env_voice_id = (os.environ.get("ELEVENLABS_VOICE_ID") or "").strip()
        explicit_voice_id = (elevenlabs_voice_id or "").strip()
        if not env_voice_id and not explicit_voice_id:
            out["voice_warnings"].append("elevenlabs_voice_id_default_fallback")
        if not ffmpeg:
            out["voice_blocking_reasons"].append("elevenlabs_requires_ffmpeg_for_concat")
            return out
        prev_voice = os.environ.get("ELEVENLABS_VOICE_ID")
        prev_model = os.environ.get("ELEVENLABS_MODEL_ID")
        try:
            if explicit_voice_id:
                os.environ["ELEVENLABS_VOICE_ID"] = explicit_voice_id
            if (elevenlabs_model or "").strip():
                os.environ["ELEVENLABS_MODEL_ID"] = elevenlabs_model.strip()
            voice_mod = _load_submodule("build_full_voiceover_ba267_el", _VOICEOVER)
            work_dir = target_mp3.parent / "_voice_work"
            ok, _chunks, vw, vb = voice_mod.synthesize_elevenlabs_mp3(
                text,
                target_mp3,
                work_dir,
                ffmpeg,
                elevenlabs_post_override=elevenlabs_post_override,
            )
            try:
                if work_dir.is_dir() and not any(work_dir.iterdir()):
                    work_dir.rmdir()
            except OSError:
                pass
        finally:
            if prev_voice is None:
                os.environ.pop("ELEVENLABS_VOICE_ID", None)
            else:
                os.environ["ELEVENLABS_VOICE_ID"] = prev_voice
            if prev_model is None:
                os.environ.pop("ELEVENLABS_MODEL_ID", None)
            else:
                os.environ["ELEVENLABS_MODEL_ID"] = prev_model
        out["voice_warnings"].extend([_redact_secret(w) for w in (vw or [])])
        if not ok:
            out["voice_blocking_reasons"].extend([_redact_secret(b) for b in (vb or ["elevenlabs_synthesis_failed"])])
            return out
        out["voice_used"] = True
        out["voice_file_path"] = str(target_mp3)
        out["voice_duration_seconds"] = _probe_audio_duration_seconds(target_mp3)
        return out

    if mode == "openai":
        api_key_present = bool((os.environ.get("OPENAI_API_KEY") or "").strip())
        if not api_key_present and openai_post_override is None:
            out["voice_blocking_reasons"].append("openai_tts_missing_api_key")
            return out
        if not ffmpeg:
            out["voice_blocking_reasons"].append("openai_tts_requires_ffmpeg_for_concat")
            return out
        try:
            voice_mod = _load_submodule("build_full_voiceover_ba267_oa", _VOICEOVER)
            work_dir = target_mp3.parent / "_voice_work"
            ok, _chunks, vw, vb = voice_mod.synthesize_openai_mp3(
                text,
                target_mp3,
                work_dir,
                ffmpeg,
                openai_voice_override=(tts_voice or "").strip() or None,
                openai_post_override=openai_post_override,
            )
            try:
                if work_dir.is_dir() and not any(work_dir.iterdir()):
                    work_dir.rmdir()
            except OSError:
                pass
        except (OSError, AttributeError) as exc:
            out["voice_blocking_reasons"].append(f"openai_tts_module_failed:{type(exc).__name__}")
            return out
        out["voice_warnings"].extend([_redact_secret(w) for w in (vw or [])])
        if not ok:
            out["voice_blocking_reasons"].extend(
                [_redact_secret(b) for b in (vb or ["openai_tts_synthesis_failed"])]
            )
            return out
        out["voice_used"] = True
        out["voice_file_path"] = str(target_mp3)
        out["voice_duration_seconds"] = _probe_audio_duration_seconds(target_mp3)
        return out

    out["voice_warnings"].append(f"voice_mode_unhandled:{mode}")
    return out


def _distribute_durations(n: int, total_seconds: int, *, min_per_scene: int = 5) -> List[int]:
    """
    Verteilt ``total_seconds`` möglichst gleichmäßig auf ``n`` Szenen unter Wahrung
    von ``min_per_scene`` (Default 5). Reste landen vorne. Hebt ``total_seconds``
    auf ``n * min_per_scene`` an, falls ``total_seconds`` zu klein ist.
    """
    if n <= 0:
        return []
    floor_total = max(1, int(min_per_scene)) * n
    target = max(int(total_seconds or 0), floor_total)
    base = target // n
    rem = target % n
    out: List[int] = []
    for i in range(n):
        d = base + (1 if i < rem else 0)
        if d < int(min_per_scene):
            d = int(min_per_scene)
        out.append(int(d))
    return out


def _apply_fit_to_voice_durations(
    *,
    asset_manifest_path: Path,
    scene_plan_path: Optional[Path],
    scene_asset_pack_path: Optional[Path],
    voice_duration_seconds: float,
    voice_fit_padding_seconds: float,
    n_scenes: int,
    min_per_scene: int = 2,
) -> Tuple[List[str], Optional[int]]:
    """
    BA 26.7b ``--fit-video-to-voice``: Patcht **nach** Voice-Erzeugung die
    ``duration_seconds`` / ``estimated_duration_seconds`` pro Szene im
    ``asset_manifest.json`` so, dass Σ(Szenen) ≈
    ``voice_duration_seconds + voice_fit_padding_seconds`` (auf ganze Sekunden
    gerundet), mit Untergrenze ``max(3, n_scenes*2, n_scenes*min_per_scene)``.
    Optional werden ``scene_plan.json`` und ``scene_asset_pack.json`` mitgepatcht.
    Timeline-Build liest die Werte aus dem Asset-Manifest.

    Rückgabe: ``(warnings, total_seconds_after_fit)``.
    """
    warns: List[str] = []
    if n_scenes <= 0 or voice_duration_seconds is None or voice_duration_seconds <= 0:
        return warns, None
    padded = float(voice_duration_seconds) + float(voice_fit_padding_seconds)
    floor_total = max(3, n_scenes * 2, n_scenes * int(min_per_scene))
    target = max(int(round(padded)), floor_total)
    durs = _distribute_durations(n_scenes, target, min_per_scene=int(min_per_scene))
    total_after = sum(durs)

    try:
        man = json.loads(asset_manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        warns.append(f"fit_voice_asset_manifest_unreadable:{type(exc).__name__}")
        return warns, None
    assets = man.get("assets") or []
    patched = 0
    for asset in assets:
        if not isinstance(asset, dict):
            continue
        sn = int(asset.get("scene_number") or 0)
        if 1 <= sn <= n_scenes:
            d = durs[sn - 1]
            asset["duration_seconds"] = d
            asset["estimated_duration_seconds"] = d
            patched += 1
    try:
        asset_manifest_path.write_text(json.dumps(man, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as exc:
        warns.append(f"fit_voice_asset_manifest_write_failed:{type(exc).__name__}")
        return warns, None

    if scene_plan_path and scene_plan_path.is_file():
        try:
            plan = json.loads(scene_plan_path.read_text(encoding="utf-8"))
            scenes = plan.get("scenes") or []
            for i, sc in enumerate(scenes[:n_scenes]):
                if isinstance(sc, dict):
                    sc["duration_seconds"] = durs[i]
            scene_plan_path.write_text(
                json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except (OSError, json.JSONDecodeError) as exc:
            warns.append(f"fit_voice_scene_plan_patch_skipped:{type(exc).__name__}")

    if scene_asset_pack_path and scene_asset_pack_path.is_file():
        try:
            pack = json.loads(scene_asset_pack_path.read_text(encoding="utf-8"))
            beats = (pack.get("scene_expansion") or {}).get("expanded_scene_assets") or []
            for i, b in enumerate(beats[:n_scenes]):
                if isinstance(b, dict):
                    b["duration_seconds"] = durs[i]
            scene_asset_pack_path.write_text(
                json.dumps(pack, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except (OSError, json.JSONDecodeError) as exc:
            warns.append(f"fit_voice_scene_pack_patch_skipped:{type(exc).__name__}")

    warns.append(
        "ba267_video_fitted_to_voice:"
        f"voice_audio~{float(voice_duration_seconds):.2f}s"
        f"_padding={float(voice_fit_padding_seconds):.2f}s"
        f"_target_total={total_after}s_scenes={patched}"
    )
    return warns, int(total_after)


def _redact_secret(msg: Any) -> str:
    s = str(msg or "")
    api_key = (os.environ.get("ELEVENLABS_API_KEY") or "").strip()
    if api_key and api_key in s:
        s = s.replace(api_key, "***")
    oa_key = (os.environ.get("OPENAI_API_KEY") or "").strip()
    if oa_key and oa_key in s:
        s = s.replace(oa_key, "***")
    return s


def run_ba265_url_to_final(
    *,
    url: Optional[str],
    script_json_path: Optional[Path],
    out_dir: Path,
    max_scenes: int = 3,
    duration_seconds: int = 45,
    asset_dir: Optional[Path] = None,
    run_id: Optional[str] = None,
    motion_mode: str = "static",
    voice_mode: str = "none",
    voice_file: Optional[Path] = None,
    voice_output: Optional[Path] = None,
    elevenlabs_voice_id: Optional[str] = None,
    elevenlabs_model: Optional[str] = None,
    tts_voice: Optional[str] = None,
    elevenlabs_post_override: Optional[Callable[..., bytes]] = None,
    openai_post_override: Optional[Callable[..., bytes]] = None,
    dummy_voice_seconds: int = _DEFAULT_DUMMY_VOICE_SECONDS,
    fit_video_to_voice: bool = False,
    voice_fit_padding_seconds: float = _DEFAULT_VOICE_FIT_PADDING_SECONDS,
    fit_min_seconds_per_scene: int = 2,
) -> Dict[str, Any]:
    """Orchestrierung; gibt run_summary-Dict zurück."""
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    rid = (run_id or "").strip() or out_dir.name.replace(" ", "_") or f"ba265_{uuid.uuid4().hex[:8]}"
    original_requested_duration_seconds = max(5, int(duration_seconds))
    _pad = max(0.0, float(voice_fit_padding_seconds))
    fit_summary: Dict[str, Any] = {
        "fit_video_to_voice": bool(fit_video_to_voice),
        "voice_fit_padding_seconds": float(_pad) if fit_video_to_voice else None,
        "fitted_video_duration_seconds": None,
        "original_requested_duration_seconds": int(original_requested_duration_seconds),
    }
    warnings: List[str] = []
    blocking: List[str] = []
    input_mode = "url" if url else "script_json"
    script_path = out_dir / "script.json"
    scene_plan_path = out_dir / "scene_plan.json"
    pack_path = out_dir / "scene_asset_pack.json"
    summary_path = out_dir / "run_summary.json"
    final_video_path = out_dir / "final_video.mp4"
    render_result_path = out_dir / "render_result.json"
    voice_text_path = out_dir / "voiceover_text.txt"
    voice_meta: Dict[str, Any] = {
        "voice_used": False,
        "voice_mode": (voice_mode or "none").strip().lower(),
        "voice_file_path": None,
        "voice_duration_seconds": None,
        "voice_warnings": [],
        "voice_blocking_reasons": [],
    }
    voice_text_path_str: Optional[str] = None

    def _add_voice_fields(doc: Dict[str, Any]) -> Dict[str, Any]:
        doc["voice_used"] = bool(voice_meta.get("voice_used"))
        doc["voice_mode"] = voice_meta.get("voice_mode") or "none"
        doc["voice_text_path"] = voice_text_path_str
        doc["voice_file_path"] = voice_meta.get("voice_file_path")
        doc["voice_duration_seconds"] = voice_meta.get("voice_duration_seconds")
        doc["audio_stream_expected"] = bool(voice_meta.get("voice_used"))
        doc["voice_warnings"] = list(voice_meta.get("voice_warnings") or [])
        doc["voice_blocking_reasons"] = list(voice_meta.get("voice_blocking_reasons") or [])
        return doc

    def _finalize_summary(doc: Dict[str, Any]) -> Dict[str, Any]:
        _add_voice_fields(doc)
        doc.update(fit_summary)
        return doc

    asset_mod = _load_submodule("run_asset_runner_ba265", _ASSET_RUNNER)
    timeline_mod = _load_submodule("build_timeline_ba265", _TIMELINE)
    render_mod = _load_submodule("render_ba265", _RENDER)

    script: Dict[str, Any]
    if url:
        text, ext_warns = extract_text_from_url(url.strip())
        warnings.extend(ext_warns)
        if not (text or "").strip():
            blocking.append("url_extraction_empty_use_script_json")
            doc = {
                "ok": False,
                "input_mode": input_mode,
                "url": url.strip(),
                "script_json": None,
                "title": "",
                "output_dir": str(out_dir),
                "script_path": str(script_path),
                "scene_plan_path": str(scene_plan_path),
                "scene_asset_pack_path": str(pack_path),
                "asset_manifest_path": None,
                "timeline_manifest_path": None,
                "final_video_path": str(final_video_path),
                "used_existing_assets": False,
                "used_video_assets_count": 0,
                "used_image_assets_count": 0,
                "warnings": warnings,
                "blocking_reasons": blocking,
            }
            summary_path.write_text(json.dumps(_finalize_summary(doc), ensure_ascii=False, indent=2), encoding="utf-8")
            return doc
        dm = max(1, int(round(duration_seconds / 60.0)))
        title, hook, chapters, full_script, sources, gen_warns = build_script_response_from_extracted_text(
            extracted_text=text,
            source_url=url.strip(),
            target_language="de",
            duration_minutes=dm,
            extraction_warnings=[],
        )
        warnings.extend(gen_warns)
        script = {
            "title": title,
            "hook": hook,
            "chapters": chapters,
            "full_script": full_script,
            "sources": sources,
            "warnings": warnings,
        }
    else:
        raw = json.loads(Path(script_json_path or "").read_text(encoding="utf-8"))
        script = _tolerant_script(raw)

    script_path.write_text(
        json.dumps(script, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )

    videos, images = _collect_assets(asset_dir.resolve() if asset_dir else None)

    try:
        scene_rows = _build_scene_rows_from_script(
            script, max_scenes=max_scenes, total_duration_seconds=duration_seconds
        )
    except ValueError as e:
        blocking.append(f"scene_plan_failed:{e}")
        doc = {
            "ok": False,
            "input_mode": input_mode,
            "url": url.strip() if url else None,
            "script_json": str(script_json_path) if script_json_path else None,
            "title": script.get("title") or "",
            "output_dir": str(out_dir),
            "script_path": str(script_path),
            "scene_plan_path": str(scene_plan_path),
            "scene_asset_pack_path": str(pack_path),
            "asset_manifest_path": None,
            "timeline_manifest_path": None,
            "final_video_path": str(final_video_path),
            "used_existing_assets": bool(videos or images),
            "used_video_assets_count": 0,
            "used_image_assets_count": 0,
            "warnings": warnings,
            "blocking_reasons": blocking,
        }
        summary_path.write_text(json.dumps(_finalize_summary(doc), ensure_ascii=False, indent=2), encoding="utf-8")
        return doc

    n_scenes = len(scene_rows)
    rel_videos, img_overrides, assign_warns = _assign_media(n_scenes, videos, images, out_dir)
    warnings.extend(assign_warns)
    used_v = sum(1 for x in rel_videos if x)
    used_i = len(img_overrides)

    scene_plan = _build_scene_plan(scene_rows, script_title=script.get("title") or "")
    scene_plan_path.write_text(json.dumps(scene_plan, ensure_ascii=False, indent=2), encoding="utf-8")

    pack = _build_scene_asset_pack(scene_rows, script=script, rel_videos=rel_videos, pack_parent=out_dir)
    pack_path.write_text(json.dumps(pack, ensure_ascii=False, indent=2), encoding="utf-8")

    try:
        ameta = asset_mod.run_local_asset_runner(
            pack_path,
            out_dir,
            run_id=rid,
            mode="placeholder",
        )
    except (OSError, ValueError, FileNotFoundError, json.JSONDecodeError) as e:
        blocking.append(f"asset_runner_failed:{type(e).__name__}")
        doc = {
            "ok": False,
            "input_mode": input_mode,
            "url": url.strip() if url else None,
            "script_json": str(script_json_path) if script_json_path else None,
            "title": script.get("title") or "",
            "output_dir": str(out_dir),
            "script_path": str(script_path),
            "scene_plan_path": str(scene_plan_path),
            "scene_asset_pack_path": str(pack_path),
            "asset_manifest_path": None,
            "timeline_manifest_path": None,
            "final_video_path": str(final_video_path),
            "used_existing_assets": bool(videos or images),
            "used_video_assets_count": used_v,
            "used_image_assets_count": used_i,
            "warnings": warnings + [str(e)],
            "blocking_reasons": blocking,
        }
        summary_path.write_text(json.dumps(_finalize_summary(doc), ensure_ascii=False, indent=2), encoding="utf-8")
        return doc

    if not ameta.get("ok"):
        blocking.append("asset_runner_not_ok")
        doc = {
            "ok": False,
            "input_mode": input_mode,
            "url": url.strip() if url else None,
            "script_json": str(script_json_path) if script_json_path else None,
            "title": script.get("title") or "",
            "output_dir": str(out_dir),
            "script_path": str(script_path),
            "scene_plan_path": str(scene_plan_path),
            "scene_asset_pack_path": str(pack_path),
            "asset_manifest_path": ameta.get("manifest_path"),
            "timeline_manifest_path": None,
            "final_video_path": str(final_video_path),
            "used_existing_assets": bool(videos or images),
            "used_video_assets_count": used_v,
            "used_image_assets_count": used_i,
            "warnings": warnings + list(ameta.get("warnings") or []),
            "blocking_reasons": blocking,
        }
        summary_path.write_text(json.dumps(_finalize_summary(doc), ensure_ascii=False, indent=2), encoding="utf-8")
        return doc

    manifest_path = Path(str(ameta["manifest_path"]))
    gen_dir = manifest_path.parent
    warnings.extend(list(ameta.get("warnings") or []))
    _apply_post_runner_images(gen_dir, manifest_path, img_overrides)
    cin_warns = _apply_cinematic_placeholders(
        gen_dir,
        manifest_path,
        image_override_scenes=list(img_overrides.keys()),
    )
    warnings.extend(cin_warns)

    voiceover_text = _collect_voiceover_text(scene_rows)
    if voiceover_text:
        try:
            voice_text_path.write_text(voiceover_text + "\n", encoding="utf-8")
            voice_text_path_str = str(voice_text_path)
        except OSError as exc:
            warnings.append(f"voiceover_text_write_failed:{type(exc).__name__}")

    voice_meta = _synthesize_voice(
        voice_mode,
        voiceover_text,
        out_dir=out_dir,
        voice_file=voice_file,
        voice_output=voice_output,
        elevenlabs_voice_id=elevenlabs_voice_id,
        elevenlabs_model=elevenlabs_model,
        tts_voice=tts_voice,
        elevenlabs_post_override=elevenlabs_post_override,
        openai_post_override=openai_post_override,
        dummy_seconds=int(dummy_voice_seconds),
    )
    audio_for_timeline: Optional[Path] = None
    vfp = voice_meta.get("voice_file_path")
    if voice_meta.get("voice_used") and vfp:
        audio_for_timeline = Path(str(vfp))

    vd_raw = voice_meta.get("voice_duration_seconds")
    vd_ok = (
        voice_meta.get("voice_used")
        and vd_raw is not None
        and float(vd_raw) > 0
    )
    if fit_video_to_voice:
        if vd_ok:
            fit_warns, total_after = _apply_fit_to_voice_durations(
                asset_manifest_path=manifest_path,
                scene_plan_path=scene_plan_path,
                scene_asset_pack_path=pack_path,
                voice_duration_seconds=float(vd_raw),
                voice_fit_padding_seconds=float(_pad),
                n_scenes=n_scenes,
                min_per_scene=max(1, int(fit_min_seconds_per_scene)),
            )
            warnings.extend(fit_warns)
            if total_after is not None and total_after > 0:
                duration_seconds = int(total_after)
                fit_summary["fitted_video_duration_seconds"] = float(total_after)
        else:
            warnings.append("fit_video_to_voice_requested_but_no_voice_duration")

    scene_dur_default = max(5, min(12, duration_seconds // max(1, n_scenes)))
    try:
        tfile, _tbody = timeline_mod.write_timeline_manifest(
            timeline_mod.load_asset_manifest(manifest_path),
            asset_manifest_path=manifest_path,
            audio_path=audio_for_timeline,
            run_id=rid,
            scene_duration_seconds=scene_dur_default,
            out_root=out_dir,
        )
    except (OSError, ValueError, FileNotFoundError, json.JSONDecodeError) as e:
        blocking.append(f"timeline_failed:{type(e).__name__}")
        doc = {
            "ok": False,
            "input_mode": input_mode,
            "url": url.strip() if url else None,
            "script_json": str(script_json_path) if script_json_path else None,
            "title": script.get("title") or "",
            "output_dir": str(out_dir),
            "script_path": str(script_path),
            "scene_plan_path": str(scene_plan_path),
            "scene_asset_pack_path": str(pack_path),
            "asset_manifest_path": str(manifest_path),
            "timeline_manifest_path": None,
            "final_video_path": str(final_video_path),
            "used_existing_assets": bool(videos or images),
            "used_video_assets_count": used_v,
            "used_image_assets_count": used_i,
            "warnings": warnings + [str(e)],
            "blocking_reasons": blocking,
        }
        summary_path.write_text(json.dumps(_finalize_summary(doc), ensure_ascii=False, indent=2), encoding="utf-8")
        return doc

    rmeta = render_mod.render_final_story_video(
        tfile,
        output_video=final_video_path,
        motion_mode=motion_mode,
        subtitle_path=None,
        run_id=rid,
        write_output_manifest=True,
        manifest_root=out_dir,
    )
    render_result_path.write_text(json.dumps(rmeta, ensure_ascii=False, indent=2), encoding="utf-8")

    vid_ok = bool(rmeta.get("video_created"))
    warnings.extend(list(rmeta.get("warnings") or []))
    blocking.extend(list(rmeta.get("blocking_reasons") or []))

    used_existing = bool(videos or images)
    doc = {
        "ok": vid_ok,
        "input_mode": input_mode,
        "url": url.strip() if url else None,
        "script_json": str(script_json_path.resolve()) if script_json_path else None,
        "title": script.get("title") or "",
        "output_dir": str(out_dir),
        "script_path": str(script_path),
        "scene_plan_path": str(scene_plan_path),
        "scene_asset_pack_path": str(pack_path),
        "asset_manifest_path": str(manifest_path),
        "timeline_manifest_path": str(tfile),
        "final_video_path": str(final_video_path),
        "used_existing_assets": used_existing,
        "used_video_assets_count": used_v,
        "used_image_assets_count": used_i,
        "warnings": warnings,
        "blocking_reasons": blocking,
    }
    summary_path.write_text(json.dumps(_finalize_summary(doc), ensure_ascii=False, indent=2), encoding="utf-8")
    return doc


def main() -> int:
    p = argparse.ArgumentParser(description="BA 26.5 — URL oder script.json + Assets -> final_video.mp4")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--url", type=str, default=None)
    g.add_argument("--script-json", type=Path, default=None, dest="script_json")
    p.add_argument("--out-dir", type=Path, required=True, dest="out_dir")
    p.add_argument("--max-scenes", type=int, default=3, dest="max_scenes")
    p.add_argument("--duration-seconds", type=int, default=45, dest="duration_seconds")
    p.add_argument("--asset-dir", type=Path, default=None, dest="asset_dir")
    p.add_argument("--run-id", type=str, default=None, dest="run_id")
    p.add_argument(
        "--motion-mode",
        choices=("static", "basic"),
        default="basic",
        dest="motion_mode",
        help="BA 26.6: Default 'basic' (Ken-Burns / xfade); 'static' für strikten BA-26.5-Look.",
    )
    p.add_argument(
        "--voice-mode",
        choices=_VOICE_MODES,
        default="none",
        dest="voice_mode",
        help=(
            "BA 26.7: 'none' (Default, BA-26.5/26.6-Verhalten), 'existing' (--voice-file), "
            "'elevenlabs' (ENV ELEVENLABS_API_KEY), 'dummy' (stilles MP3 für Smoke), "
            "'openai' (ENV OPENAI_API_KEY, optional)."
        ),
    )
    p.add_argument("--voice-file", type=Path, default=None, dest="voice_file")
    p.add_argument("--voice-output", type=Path, default=None, dest="voice_output")
    p.add_argument("--elevenlabs-voice-id", type=str, default=None, dest="elevenlabs_voice_id")
    p.add_argument("--elevenlabs-model", type=str, default=None, dest="elevenlabs_model")
    p.add_argument("--tts-voice", type=str, default=None, dest="tts_voice")
    p.add_argument(
        "--fit-video-to-voice",
        action="store_true",
        dest="fit_video_to_voice",
        help=(
            "BA 26.7b: Nach ermittelter Voice-Dauer Szenen-/Timeline-Dauer auf "
            "voice_duration + padding ausrichten (kein großer Render-Refactor). "
            "Ohne nutzbare Voice-Dauer: Warning fit_video_to_voice_requested_but_no_voice_duration."
        ),
    )
    p.add_argument(
        "--voice-fit-padding-seconds",
        type=float,
        default=_DEFAULT_VOICE_FIT_PADDING_SECONDS,
        dest="voice_fit_padding_seconds",
        metavar="SEC",
        help=(
            "Zuschlag in Sekunden auf die gemessene Voice-Dauer bei --fit-video-to-voice "
            f"(Default {_DEFAULT_VOICE_FIT_PADDING_SECONDS})."
        ),
    )
    p.add_argument(
        "--fit-min-seconds-per-scene",
        type=int,
        default=2,
        dest="fit_min_seconds_per_scene",
        help="Mindestdauer pro Szene bei --fit-video-to-voice (Default 2).",
    )
    args = p.parse_args()

    try:
        doc = run_ba265_url_to_final(
            url=args.url,
            script_json_path=args.script_json,
            out_dir=args.out_dir,
            max_scenes=max(1, int(args.max_scenes)),
            duration_seconds=max(5, int(args.duration_seconds)),
            asset_dir=args.asset_dir,
            run_id=args.run_id,
            motion_mode=args.motion_mode,
            voice_mode=args.voice_mode,
            voice_file=args.voice_file,
            voice_output=args.voice_output,
            elevenlabs_voice_id=args.elevenlabs_voice_id,
            elevenlabs_model=args.elevenlabs_model,
            tts_voice=args.tts_voice,
            fit_video_to_voice=bool(args.fit_video_to_voice),
            voice_fit_padding_seconds=float(args.voice_fit_padding_seconds),
            fit_min_seconds_per_scene=max(1, int(args.fit_min_seconds_per_scene)),
        )
    except Exception as e:
        err = {"ok": False, "error": type(e).__name__, "message": str(e)}
        print(json.dumps(err, ensure_ascii=False, indent=2))
        return 2

    print(json.dumps(doc, ensure_ascii=False, indent=2))
    return 0 if doc.get("ok") else 3


if __name__ == "__main__":
    raise SystemExit(main())
