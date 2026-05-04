"""BA 19.2 / BA 20.4 — timeline_manifest + Bilder + Audio → MP4 (ffmpeg)."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MOTION_FPS = 25
DEFAULT_XFADE_FADE_SEC = 0.35
CUT_XFADE_SEC = 0.06

# libass force_style (Kommas im Filter escaped)
SUBTITLE_FORCE_STYLE = (
    "FontName=Arial,FontSize=22,"
    "PrimaryColour=&H00FFFFFF&,OutlineColour=&H000000&,"
    "Outline=2,Shadow=1,MarginV=64,Alignment=2"
)


def _ffmpeg_escape_subtitle_file_path(p: Path) -> str:
    """Pfad für subtitles=… in -vf / filter_complex (Windows-tauglich)."""
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


def which_ffmpeg() -> Optional[str]:
    return shutil.which("ffmpeg")


def which_ffprobe() -> Optional[str]:
    return shutil.which("ffprobe")


def _ba207_write_render_output_manifest(
    manifest_path: Path,
    *,
    ok: bool,
    run_id: str,
    clean_video_path: str,
    clean_video_role: str,
    subtitle_burnin_video_path: str,
    subtitle_sidecar_srt_path: str,
    subtitle_sidecar_ass_path: str,
    subtitle_delivery_mode: str,
    subtitle_style: str,
    renderer_used: str,
    warnings: List[str],
    blocking_reasons: List[str],
) -> Optional[str]:
    """BA 20.7 — Contract-Datei unter output/render_<run_id>/ (V1, kein Orchestrierungs-Flow)."""
    doc: Dict[str, Any] = {
        "ok": ok,
        "run_id": run_id,
        "clean_video_path": clean_video_path,
        "clean_video_role": clean_video_role,
        "subtitle_burnin_video_path": subtitle_burnin_video_path,
        "subtitle_sidecar_srt_path": subtitle_sidecar_srt_path,
        "subtitle_sidecar_ass_path": subtitle_sidecar_ass_path,
        "subtitle_delivery_mode": subtitle_delivery_mode,
        "subtitle_style": subtitle_style,
        "renderer_used": renderer_used,
        "warnings": list(warnings),
        "blocking_reasons": list(blocking_reasons),
    }
    try:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
        return str(manifest_path.resolve())
    except OSError:
        return None


def load_timeline_manifest(path: Path) -> Dict[str, Any]:
    p = path.resolve()
    if not p.is_file():
        raise FileNotFoundError(f"timeline_manifest not found: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def _escape_concat_path(p: Path) -> str:
    s = p.resolve().as_posix()
    return s.replace("'", "'\\''")


def _timeline_video_duration_seconds(scenes: List[Dict[str, Any]]) -> float:
    """Summe der Szenenlängen (Plan-Länge für Audio-Trim, identisch zu BA 19.2 concat)."""
    return sum(float(sc.get("duration_seconds") or 6) for sc in scenes)


def _zoom_from_camera_hint(hint: str) -> str:
    h = (hint or "").lower()
    if "pull" in h or "zoom out" in h:
        return "slow_pull"
    if "push" in h or "zoom in" in h or "push-in" in h:
        return "slow_push"
    return "static"


def _scene_zoom_type(sc: Dict[str, Any]) -> str:
    zt = str(sc.get("zoom_type") or "").strip().lower()
    if zt in ("slow_push", "slow_pull", "static"):
        return zt
    return _zoom_from_camera_hint(str(sc.get("camera_motion_hint") or ""))


def _scene_pan_direction(sc: Dict[str, Any]) -> str:
    pd = str(sc.get("pan_direction") or "none").strip().lower()
    if pd in ("left", "right", "none"):
        return pd
    return "none"


def _boundary_fade_seconds(scene_after: Dict[str, Any]) -> float:
    """Übergang vor Szene scene_after (Eintritt): fade vs. harter Schnitt (kurzer xfade)."""
    tr = str(scene_after.get("transition") or "fade").strip().lower()
    if tr in ("fade", "crossfade", ""):
        return DEFAULT_XFADE_FADE_SEC
    return CUT_XFADE_SEC


def _xfade_offset_sequence(durs: List[float], fades: List[float]) -> List[float]:
    """Pro Kante fades[k]: offset im xfade-Filter."""
    if len(durs) < 2 or len(fades) != len(durs) - 1:
        return []
    offsets: List[float] = []
    acc_len = durs[0]
    for k in range(len(durs) - 1):
        fd = fades[k]
        offsets.append(acc_len - fd)
        acc_len = acc_len + durs[k + 1] - fd
    return offsets


def _segment_motion_filter(d_sec: float, zoom_type: str, pan_direction: str, fps: int) -> str:
    """Filterkette ohne Eingabe-Label: fps → Motion → setpts (einheitlich 1920×1080 yuv420p)."""
    frames = max(3, int(round(d_sec * float(fps))))
    zt = (zoom_type or "static").strip().lower()
    pd = (pan_direction or "none").strip().lower()
    d_str = f"{d_sec:.6f}"

    if zt in ("slow_push", "slow_zoom_in"):
        return (
            f"fps={fps},format=yuv420p,scale=iw*4:-1:flags=lanczos,"
            f"zoompan=z='if(eq(on,1),1,min(zoom+0.0010,1.14))':d={frames}:"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps={fps},"
            f"format=yuv420p,setpts=PTS-STARTPTS"
        )
    if zt in ("slow_pull", "slow_zoom_out"):
        return (
            f"fps={fps},format=yuv420p,scale=iw*4:-1:flags=lanczos,"
            f"zoompan=z='if(eq(on,1),1.14,max(zoom-0.0010,1))':d={frames}:"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps={fps},"
            f"format=yuv420p,setpts=PTS-STARTPTS"
        )

    if pd in ("left", "right"):
        dmax = max(frames - 1, 1)
        if pd == "left":
            xexpr = f"(iw-iw/zoom)*(1-on/{dmax})"
        else:
            xexpr = f"(iw-iw/zoom)*on/{dmax}"
        return (
            f"fps={fps},format=yuv420p,scale=iw*3:-1:flags=lanczos,"
            f"zoompan=z='1.1':d={frames}:x='{xexpr}':y='ih/2-(ih/zoom/2)':s=1920x1080:fps={fps},"
            f"format=yuv420p,setpts=PTS-STARTPTS"
        )

    return (
        f"fps={fps},format=yuv420p,scale=1920:1080:force_original_aspect_ratio=decrease,"
        f"pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black,"
        f"trim=duration={d_str},setpts=PTS-STARTPTS"
    )


def _write_concat_list(scenes: List[Dict[str, Any]], assets_dir: Path, tmp_list: Path) -> None:
    lines: List[str] = []
    for i, sc in enumerate(scenes):
        img = assets_dir / str(sc.get("image_path") or "")
        dur = float(sc.get("duration_seconds") or 6)
        lines.append(f"file '{_escape_concat_path(img)}'")
        lines.append(f"duration {dur}")
    if scenes:
        last = assets_dir / str(scenes[-1].get("image_path") or "")
        lines.append(f"file '{_escape_concat_path(last)}'")
        lines.append("duration 0.04")
    tmp_list.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _probe_audio_duration(audio: Path, ffprobe: str) -> Tuple[Optional[float], List[str]]:
    warns: List[str] = []
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
                str(audio),
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


def _probe_video_duration(video: Path, ffprobe: str) -> Tuple[Optional[float], List[str]]:
    warns: List[str] = []
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
                str(video),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        return float((cp.stdout or "").strip()), warns
    except Exception:
        warns.append("output_duration_probe_failed")
        return None, warns


def _normalize_motion_mode(raw: Optional[str]) -> Tuple[str, List[str]]:
    warns: List[str] = []
    m = (raw or "basic").strip().lower()
    if m not in ("static", "basic"):
        warns.append(f"motion_mode_unknown_defaulting_basic:{m}")
        m = "basic"
    return m, warns


def _build_basic_motion_filter_script(
    scenes: List[Dict[str, Any]],
    *,
    fps: int,
    timeline_seconds: float,
    has_audio: bool,
    audio_input_index: int,
) -> str:
    n = len(scenes)
    durs = [float(s.get("duration_seconds") or 6) for s in scenes]
    fades = [_boundary_fade_seconds(scenes[k + 1]) for k in range(n - 1)]
    offs = _xfade_offset_sequence(durs, fades)

    parts: List[str] = []
    for i, sc in enumerate(scenes):
        zt = _scene_zoom_type(sc)
        pd = _scene_pan_direction(sc)
        if zt in ("slow_push", "slow_pull"):
            pd_eff = "none"
        else:
            pd_eff = pd
        vf = _segment_motion_filter(durs[i], zt, pd_eff, fps)
        parts.append(f"[{i}:v]{vf}[b{i}]")

    if n == 1:
        parts.append("[b0]null[vcore]")
    else:
        cur = "b0"
        for k in range(n - 1):
            nxt = f"b{k + 1}"
            fd = fades[k]
            off = offs[k]
            out = f"xc{k}" if k < n - 2 else "vcore"
            parts.append(f"[{cur}][{nxt}]xfade=transition=fade:duration={fd:.4f}:offset={off:.4f}[{out}]")
            cur = out

    produced = durs[0]
    for k in range(1, n):
        produced += durs[k] - fades[k - 1]
    gap = max(0.0, float(timeline_seconds) - float(produced))
    if gap > 0.02:
        parts.append(f"[vcore]tpad=stop_mode=clone:stop_duration={gap:.4f}[vfin]")
    else:
        parts.append("[vcore]null[vfin]")

    if has_audio:
        td = max(float(timeline_seconds), 0.04)
        td_s = f"{td:.6f}"
        parts.append(f"[{audio_input_index}:a]atrim=duration={td_s},apad=whole_dur={td_s}[aout]")

    return ";".join(parts) + "\n"


def _run_ffmpeg_static_concat(
    scenes: List[Dict[str, Any]],
    assets_dir: Path,
    output_video: Path,
    ffmpeg: str,
    ffprobe: Optional[str],
    audio_file: Optional[Path],
    timeline_seconds: float,
    warnings: List[str],
    *,
    subtitle_path: Optional[Path] = None,
) -> Tuple[bool, List[str], List[str]]:
    """BA 19.2 Pfad: concat-Demuxer + globales scale/pad; optional BA 20.5 subtitles-Burn-in."""
    blocking: List[str] = []
    fd, tmp_name = tempfile.mkstemp(suffix="_concat.txt", text=True)
    os.close(fd)
    tmp_path = Path(tmp_name)
    try:
        _write_concat_list(scenes, assets_dir, tmp_path)
        vf = (
            "format=yuv420p,scale=1920:1080:force_original_aspect_ratio=decrease,"
            "pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black"
        )
        if subtitle_path is not None and subtitle_path.is_file() and subtitle_path.stat().st_size > 0:
            vf = f"{vf},{_subtitles_vf_fragment(subtitle_path)}"
        cmd: List[str] = [
            ffmpeg,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(tmp_path),
        ]
        if audio_file:
            cmd.extend(["-i", str(audio_file)])
            td = max(timeline_seconds, 0.04)
            td_s = f"{td:.6f}"
            audio_d: Optional[float] = None
            if ffprobe:
                audio_d, aw = _probe_audio_duration(audio_file, ffprobe)
                warnings.extend(aw)
            if audio_d is not None and audio_d + 0.1 < td:
                warnings.append("audio_shorter_than_timeline_padded_or_continued")
            cmd.extend(
                [
                    "-filter_complex",
                    f"[1:a]atrim=duration={td_s},apad=whole_dur={td_s}[aout]",
                    "-map",
                    "0:v",
                    "-map",
                    "[aout]",
                    "-c:a",
                    "aac",
                    "-b:a",
                    "192k",
                ]
            )
        else:
            cmd.extend(["-map", "0:v", "-an"])
        cmd.extend(
            [
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-vf",
                vf,
                str(output_video),
            ]
        )
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        err = (e.stderr or e.stdout or "")[:800]
        return False, warnings + [f"ffmpeg_failed:{err}"], ["ffmpeg_encode_failed"]
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass

    return True, warnings, blocking


def _run_ffmpeg_basic_motion(
    scenes: List[Dict[str, Any]],
    assets_dir: Path,
    output_video: Path,
    ffmpeg: str,
    ffprobe: Optional[str],
    audio_file: Optional[Path],
    timeline_seconds: float,
    warnings: List[str],
    *,
    subtitle_path: Optional[Path] = None,
) -> Tuple[bool, List[str], List[str]]:
    """BA 20.4: Ken-Burns-ähnlich + xfade; Audio wie BA 19.2; optional BA 20.5 subtitles."""
    blocking: List[str] = []
    n = len(scenes)
    fps = MOTION_FPS
    has_audio = audio_file is not None
    audio_idx = n if has_audio else -1

    fd, script_name = tempfile.mkstemp(suffix="_motion.fc", text=True)
    os.close(fd)
    script_path = Path(script_name)
    try:
        body = _build_basic_motion_filter_script(
            scenes,
            fps=fps,
            timeline_seconds=timeline_seconds,
            has_audio=has_audio,
            audio_input_index=audio_idx,
        )
        v_out = "vfin"
        if subtitle_path is not None and subtitle_path.is_file() and subtitle_path.stat().st_size > 0:
            frag = _subtitles_vf_fragment(subtitle_path)
            body = body.rstrip() + f";[vfin]{frag}[vsubout]\n"
            v_out = "vsubout"
        script_path.write_text(body, encoding="utf-8")

        cmd: List[str] = [ffmpeg, "-y"]
        for sc in scenes:
            img = assets_dir / str(sc.get("image_path") or "")
            d = float(sc.get("duration_seconds") or 6)
            cmd.extend(["-loop", "1", "-framerate", str(fps), "-t", f"{d:.6f}", "-i", str(img)])
        if audio_file:
            cmd.extend(["-i", str(audio_file)])

        cmd.extend(["-filter_complex_script", str(script_path)])
        if has_audio:
            td = max(timeline_seconds, 0.04)
            if ffprobe:
                audio_d, aw = _probe_audio_duration(audio_file, ffprobe)
                warnings.extend(aw)
                if audio_d is not None and audio_d + 0.1 < td:
                    warnings.append("audio_shorter_than_timeline_padded_or_continued")
            cmd.extend(
                [
                    "-map",
                    f"[{v_out}]",
                    "-map",
                    "[aout]",
                    "-c:v",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    "-c:a",
                    "aac",
                    "-b:a",
                    "192k",
                    str(output_video),
                ]
            )
        else:
            cmd.extend(
                [
                    "-map",
                    f"[{v_out}]",
                    "-an",
                    "-c:v",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    str(output_video),
                ]
            )
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        err = (e.stderr or e.stdout or "")[:800]
        return False, warnings + [f"ffmpeg_motion_failed:{err}"], ["ffmpeg_encode_failed"]
    except OSError as e:
        return False, warnings + [f"motion_filter_script_failed:{type(e).__name__}"], ["ffmpeg_encode_failed"]
    finally:
        try:
            script_path.unlink(missing_ok=True)
        except OSError:
            pass

    return True, warnings, blocking


def _ba207_render_manifest_payload(
    *,
    video_created: bool,
    output_path_str: str,
    burned: bool,
    sub_file: Optional[Path],
    use_sub: bool,
    warns: List[str],
    blocks: List[str],
) -> Dict[str, Any]:
    """Felder für render_output_manifest.json (BA 20.7)."""
    out_res = ""
    if output_path_str and video_created:
        try:
            out_res = str(Path(output_path_str).resolve())
        except OSError:
            out_res = output_path_str
    side_srt = str(sub_file.resolve()) if sub_file else ""
    if video_created and burned:
        return {
            "ok": True,
            "clean_video_path": "",
            "clean_video_role": "",
            "subtitle_burnin_video_path": out_res,
            "subtitle_sidecar_srt_path": side_srt,
            "subtitle_sidecar_ass_path": "",
            "subtitle_delivery_mode": "both" if side_srt else "burn_in",
            "subtitle_style": "classic",
            "renderer_used": "srt_burnin",
            "warnings": list(warns),
            "blocking_reasons": list(blocks),
        }
    if video_created:
        delivery = "none"
        if use_sub and side_srt and not burned:
            delivery = "sidecar_srt"
        return {
            "ok": True,
            "clean_video_path": out_res,
            "clean_video_role": "clean_video",
            "subtitle_burnin_video_path": "",
            "subtitle_sidecar_srt_path": side_srt,
            "subtitle_sidecar_ass_path": "",
            "subtitle_delivery_mode": delivery,
            "subtitle_style": "classic" if use_sub else "none",
            "renderer_used": "none",
            "warnings": list(warns),
            "blocking_reasons": list(blocks),
        }
    return {
        "ok": False,
        "clean_video_path": "",
        "clean_video_role": "",
        "subtitle_burnin_video_path": "",
        "subtitle_sidecar_srt_path": side_srt,
        "subtitle_sidecar_ass_path": "",
        "subtitle_delivery_mode": "none",
        "subtitle_style": "none",
        "renderer_used": "none",
        "warnings": list(warns),
        "blocking_reasons": list(blocks),
    }


def render_final_story_video(
    timeline_path: Path,
    *,
    output_video: Path,
    motion_mode: Optional[str] = None,
    subtitle_path: Optional[Path] = None,
    ffmpeg_bin: Optional[str] = None,
    ffprobe_bin: Optional[str] = None,
    run_id: Optional[str] = None,
    write_output_manifest: bool = False,
    manifest_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    concat demuxer (static) oder Motion+xfade (basic) → scale/pad 1920x1080 → H.264 + optional AAC.
    Ohne Audio: stumm (warnings audio_missing_silent_render).
    BA 20.5: optional Untertitel-Burn-in (--subtitle-path), bei Fehler erneuter Lauf ohne Untertitel.
    BA 20.7: Primärausgabe ist **clean** ohne --subtitle-path; --subtitle-path = Legacy-Inline-Burn-in
    (Warnung legacy_subtitle_path_burnin_used). Optional render_output_manifest.json bei write_output_manifest.
    """
    warnings: List[str] = []
    blocking: List[str] = []
    ffprobe = ffprobe_bin or which_ffprobe()
    sub_req = (str(subtitle_path).strip() if subtitle_path is not None else "") or ""
    rid = (str(run_id).strip() if run_id is not None else "") or str(uuid.uuid4())
    man_root = Path(manifest_root).resolve() if manifest_root is not None else (ROOT / "output")
    manifest_path = man_root / f"render_{rid}" / "render_output_manifest.json"
    sub_file: Optional[Path] = None
    use_sub = False

    motion_eff, mw = _normalize_motion_mode(motion_mode)
    warnings.extend(mw)
    if sub_req:
        warnings.append("legacy_subtitle_path_burnin_used")

    def _sub_meta() -> Dict[str, Any]:
        return {
            "subtitle_path_requested": sub_req or None,
            "subtitles_burned": False,
        }

    def _merge_207(r: Dict[str, Any], *, video_created: bool, burned: bool) -> Dict[str, Any]:
        r["run_id"] = rid
        if write_output_manifest:
            pay = _ba207_render_manifest_payload(
                video_created=video_created,
                output_path_str=str(r.get("output_path") or ""),
                burned=burned,
                sub_file=sub_file,
                use_sub=use_sub,
                warns=list(r.get("warnings") or []),
                blocks=list(r.get("blocking_reasons") or []),
            )
            mp = _ba207_write_render_output_manifest(
                manifest_path,
                ok=bool(pay["ok"]),
                run_id=rid,
                clean_video_path=str(pay["clean_video_path"]),
                clean_video_role=str(pay["clean_video_role"]),
                subtitle_burnin_video_path=str(pay["subtitle_burnin_video_path"]),
                subtitle_sidecar_srt_path=str(pay["subtitle_sidecar_srt_path"]),
                subtitle_sidecar_ass_path=str(pay["subtitle_sidecar_ass_path"]),
                subtitle_delivery_mode=str(pay["subtitle_delivery_mode"]),
                subtitle_style=str(pay["subtitle_style"]),
                renderer_used=str(pay["renderer_used"]),
                warnings=list(pay["warnings"]),
                blocking_reasons=list(pay["blocking_reasons"]),
            )
            if mp:
                r["render_output_manifest_path"] = mp
        return r

    try:
        tl = load_timeline_manifest(timeline_path)
    except (OSError, json.JSONDecodeError, FileNotFoundError) as e:
        r = {
            "video_created": False,
            "output_path": str(output_video),
            "duration_seconds": None,
            "scene_count": 0,
            "motion_mode": motion_eff,
            "warnings": warnings + [f"timeline_load_failed:{type(e).__name__}"],
            "blocking_reasons": ["timeline_manifest_invalid_or_missing"],
        }
        r.update(_sub_meta())
        return _merge_207(r, video_created=False, burned=False)

    scenes = tl.get("scenes") or []
    if not isinstance(scenes, list) or not scenes:
        r = {
            "video_created": False,
            "output_path": str(output_video),
            "duration_seconds": None,
            "scene_count": 0,
            "motion_mode": motion_eff,
            "warnings": warnings,
            "blocking_reasons": ["timeline_scenes_empty"],
        }
        r.update(_sub_meta())
        return _merge_207(r, video_created=False, burned=False)

    n_scenes = len(scenes)
    ffmpeg = ffmpeg_bin if ffmpeg_bin is not None else which_ffmpeg()
    if not ffmpeg:
        r = {
            "video_created": False,
            "output_path": str(output_video),
            "duration_seconds": None,
            "scene_count": n_scenes,
            "motion_mode": motion_eff,
            "warnings": warnings,
            "blocking_reasons": ["ffmpeg_missing"],
        }
        r.update(_sub_meta())
        return _merge_207(r, video_created=False, burned=False)

    assets_dir = Path(str(tl.get("assets_directory") or ""))
    if not assets_dir.is_dir():
        r = {
            "video_created": False,
            "output_path": str(output_video),
            "duration_seconds": None,
            "scene_count": n_scenes,
            "motion_mode": motion_eff,
            "warnings": warnings,
            "blocking_reasons": ["assets_directory_missing"],
        }
        r.update(_sub_meta())
        return _merge_207(r, video_created=False, burned=False)

    for sc in scenes:
        ip = assets_dir / str(sc.get("image_path") or "")
        if not ip.is_file():
            r = {
                "video_created": False,
                "output_path": str(output_video),
                "duration_seconds": None,
                "scene_count": n_scenes,
                "motion_mode": motion_eff,
                "warnings": warnings,
                "blocking_reasons": [f"missing_image:{sc.get('image_path')}"],
            }
            r.update(_sub_meta())
            return _merge_207(r, video_created=False, burned=False)

    audio_path = (tl.get("audio_path") or "").strip()
    audio_file: Optional[Path] = Path(audio_path) if audio_path else None
    if audio_file and not audio_file.is_file():
        warnings.append("audio_path_set_but_file_missing_silent_render")
        audio_file = None
    if not audio_file:
        warnings.append("audio_missing_silent_render")

    timeline_seconds = _timeline_video_duration_seconds(scenes)

    output_video.parent.mkdir(parents=True, exist_ok=True)

    sub_file = None
    if subtitle_path is not None and str(subtitle_path).strip():
        sp = Path(str(subtitle_path).strip())
        if not sp.is_file():
            warnings.append("subtitle_path_set_but_file_missing_skipped")
        elif sp.stat().st_size == 0:
            warnings.append("subtitle_file_empty_skipped")
        else:
            sub_file = sp.resolve()

    use_sub = sub_file is not None
    burned_subtitles = False
    used_motion = motion_eff == "basic"
    ok = False
    blocking: List[str] = []
    sub_tries = [True, False] if use_sub else [False]

    if motion_eff == "basic":
        for sub_on in sub_tries:
            ok, warnings, blocking = _run_ffmpeg_basic_motion(
                scenes,
                assets_dir,
                output_video,
                ffmpeg,
                ffprobe,
                audio_file,
                timeline_seconds,
                warnings,
                subtitle_path=sub_file if sub_on else None,
            )
            if ok:
                burned_subtitles = bool(sub_on)
                break
        if not ok:
            warnings.append("motion_render_failed_fallback_static")
            used_motion = False
            for sub_on in sub_tries:
                ok, warnings, blocking = _run_ffmpeg_static_concat(
                    scenes,
                    assets_dir,
                    output_video,
                    ffmpeg,
                    ffprobe,
                    audio_file,
                    timeline_seconds,
                    warnings,
                    subtitle_path=sub_file if sub_on else None,
                )
                if ok:
                    burned_subtitles = bool(sub_on)
                    break
    else:
        for sub_on in sub_tries:
            ok, warnings, blocking = _run_ffmpeg_static_concat(
                scenes,
                assets_dir,
                output_video,
                ffmpeg,
                ffprobe,
                audio_file,
                timeline_seconds,
                warnings,
                subtitle_path=sub_file if sub_on else None,
            )
            if ok:
                burned_subtitles = bool(sub_on)
                break

    if ok and use_sub and not burned_subtitles:
        warnings.append("subtitle_burn_failed_fallback_no_subtitles")

    if not ok:
        r = {
            "video_created": False,
            "output_path": str(output_video),
            "duration_seconds": None,
            "scene_count": n_scenes,
            "motion_mode": motion_eff,
            "motion_applied": used_motion,
            "warnings": warnings,
            "blocking_reasons": blocking or ["ffmpeg_encode_failed"],
            "subtitle_path_requested": sub_req or None,
            "subtitles_burned": False,
        }
        return _merge_207(r, video_created=False, burned=False)

    dur: Optional[float] = None
    if ffprobe:
        dur, pw = _probe_video_duration(output_video, ffprobe)
        warnings.extend(pw)
    r_ok: Dict[str, Any] = {
        "video_created": True,
        "output_path": str(output_video.resolve()),
        "duration_seconds": dur,
        "scene_count": n_scenes,
        "motion_mode": motion_eff,
        "motion_applied": used_motion,
        "warnings": warnings,
        "blocking_reasons": blocking,
        "subtitle_path_requested": sub_req or None,
        "subtitles_burned": burned_subtitles,
    }
    return _merge_207(r_ok, video_created=True, burned=burned_subtitles)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="BA 19.2 / BA 20.4 / BA 20.5 / BA 20.7 — timeline_manifest → MP4 (ffmpeg); "
        "Burn-in nur optional via --subtitle-path (Legacy); BA 20.7 Manifest unter output/render_<run_id>/"
    )
    parser.add_argument("--timeline-manifest", type=Path, required=True, dest="timeline_manifest")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "output" / "final_story_video.mp4",
        dest="output",
    )
    parser.add_argument(
        "--motion-mode",
        choices=("static", "basic"),
        default="basic",
        dest="motion_mode",
        help="BA 20.4: static = BA19.2 concat; basic = Zoom/Pan + xfade (Fallback bei ffmpeg-Fehler)",
    )
    parser.add_argument(
        "--subtitle-path",
        type=Path,
        default=None,
        dest="subtitle_path",
        help="BA 20.5 (Legacy): SRT ins **gleiche** Output-MP4 brennen — BA 20.7 empfiehlt clean render + "
        "separaten Schritt burn_in_subtitles_preview.py statt Default-Burn-in",
    )
    parser.add_argument(
        "--run-id",
        default="",
        dest="run_id",
        help="BA 20.7: Ordner output/render_<run_id>/ für render_output_manifest.json (Default: UUID)",
    )
    args = parser.parse_args()

    meta = render_final_story_video(
        args.timeline_manifest,
        output_video=args.output,
        motion_mode=args.motion_mode,
        subtitle_path=args.subtitle_path,
        run_id=(args.run_id or "").strip() or None,
        write_output_manifest=True,
    )
    print(json.dumps(meta, ensure_ascii=False, indent=2))
    return 0 if meta.get("video_created") else 4


if __name__ == "__main__":
    raise SystemExit(main())
