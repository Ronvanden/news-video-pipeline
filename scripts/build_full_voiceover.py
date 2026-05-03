"""BA 20.0 / BA 20.1 — Founder Full Voiceover: PromptPlan → narration + MP3 + voice_manifest.json."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import httpx

from app.founder_calibration.ba203_presets import resolve_voice_preset
from app.prompt_engine.pipeline import build_production_prompt_plan
from app.prompt_engine.schema import ProductionPromptPlan, PromptPlanRequest
from app.utils import count_words

# Heuristik 130–160 W/min — Mitte für geschätzte Sprechdauer
DEFAULT_WPM = 145.0
MIN_BODY_CHARS = 24
SMOKE_MP3_MAX_SECONDS = 3600
SMOKE_BASELINE_SECONDS = 5

ELEVENLABS_CHUNK_MAX_CHARS = 4500
OPENAI_CHUNK_MAX_CHARS = 3800
ELEVENLABS_DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"
OPENAI_SPEECH_URL = "https://api.openai.com/v1/audio/speech"

_SMOKE_HEADER = (
    "# BA 20.0 / BA 20.1 — FULL VOICEOVER\n"
    "# Smoke: Stille/Länge-Näherung; elevenlabs|openai: echte TTS (siehe voice_manifest).\n\n"
)


def which_ffmpeg() -> Optional[str]:
    return shutil.which("ffmpeg")


def estimate_speak_duration_seconds(word_count: int, wpm: float = DEFAULT_WPM) -> int:
    if word_count <= 0:
        return 0
    wpm = max(wpm, 60.0)
    sec = int(round((word_count / wpm) * 60.0))
    return max(1, min(sec, SMOKE_MP3_MAX_SECONDS))


def _collapse_ws(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def _join_chapter_summaries(plan: ProductionPromptPlan) -> str:
    parts: List[str] = []
    for c in plan.chapter_outline or []:
        title = (c.title or "").strip()
        summary = (c.summary or "").strip()
        if summary:
            if title:
                parts.append(f"{title}\n\n{summary}")
            else:
                parts.append(summary)
        elif title:
            parts.append(title)
    return "\n\n---\n\n".join(parts)


def extract_narration_text(
    plan: ProductionPromptPlan,
    *,
    full_script_json: str = "",
) -> Tuple[str, str, List[str]]:
    """
    Priorität: full_script (JSON-Zusatzfeld) → Kapitel-Summaries → Hook + Kapitel-Summaries.
    Rückgabe: (text, source_type, warnings).
    """
    warns: List[str] = []
    fs = (full_script_json or "").strip()
    if fs:
        return fs, "full_script", warns

    joined = _join_chapter_summaries(plan).strip()
    if len(joined) >= MIN_BODY_CHARS:
        return joined, "chapter_summaries", warns

    hook = (plan.hook or "").strip()
    combo = f"{hook}\n\n{joined}".strip() if joined else hook
    if len(combo) >= MIN_BODY_CHARS:
        warns.append("narration_fallback_hook_plus_chapters")
        return combo, "hook_plus_chapter_summaries", warns

    if hook:
        warns.append("narration_fallback_hook_only")
        return hook, "hook_only", warns

    warns.append("narration_text_empty")
    return "", "empty", warns


def chunk_narration_for_tts(text: str, max_chars: int) -> List[str]:
    """Teilt Fließtext in API-sichere Blöcke (Absätze, dann Sätze, dann hart)."""
    t = (text or "").strip()
    if not t:
        return []
    if max_chars < 200:
        max_chars = 200
    if len(t) <= max_chars:
        return [t]

    paragraphs = re.split(r"\n\s*\n+", t)
    chunks: List[str] = []
    buf = ""

    def flush_buf() -> None:
        nonlocal buf
        if buf.strip():
            chunks.append(buf.strip())
        buf = ""

    for para in paragraphs:
        p = para.strip()
        if not p:
            continue
        if len(p) > max_chars:
            flush_buf()
            chunks.extend(_split_oversized_block(p, max_chars))
            continue
        candidate = f"{buf}\n\n{p}" if buf else p
        if len(candidate) <= max_chars:
            buf = candidate
        else:
            flush_buf()
            buf = p
    flush_buf()
    return [c for c in chunks if c]


def _split_oversized_block(block: str, max_chars: int) -> List[str]:
    out: List[str] = []
    sentences = re.split(r"(?<=[.!?])\s+", block)
    buf = ""
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        if len(s) > max_chars:
            if buf:
                out.append(buf.strip())
                buf = ""
            for i in range(0, len(s), max_chars):
                out.append(s[i : i + max_chars].strip())
            continue
        cand = f"{buf} {s}".strip() if buf else s
        if len(cand) <= max_chars:
            buf = cand
        else:
            if buf:
                out.append(buf.strip())
            buf = s
    if buf.strip():
        out.append(buf.strip())
    return out


def _escape_concat_path(p: Path) -> str:
    return p.resolve().as_posix().replace("'", "'\\''")


def _write_smoke_mp3_ffmpeg(out_mp3: Path, duration_seconds: int, ffmpeg: str) -> Tuple[bool, List[str]]:
    blocking: List[str] = []
    if not ffmpeg:
        return False, ["ffmpeg_missing"]
    dur = max(1, min(int(duration_seconds), SMOKE_MP3_MAX_SECONDS))
    cmd = [
        ffmpeg,
        "-y",
        "-f",
        "lavfi",
        "-i",
        "anullsrc=r=44100:cl=stereo",
        "-t",
        str(dur),
        "-c:a",
        "libmp3lame",
        "-b:a",
        "128k",
        str(out_mp3),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return True, []
    except FileNotFoundError:
        return False, ["ffmpeg_missing"]
    except subprocess.CalledProcessError:
        return False, ["ffmpeg_encode_failed"]


def _merge_mp3_segments_ffmpeg(segment_paths: List[Path], out_mp3: Path, ffmpeg: str) -> Tuple[bool, List[str]]:
    if not segment_paths:
        return False, ["tts_segments_empty"]
    if len(segment_paths) == 1:
        try:
            shutil.copyfile(segment_paths[0], out_mp3)
            return True, []
        except OSError:
            return False, ["tts_segment_copy_failed"]
    if not ffmpeg:
        return False, ["ffmpeg_missing"]
    lines = [f"file '{_escape_concat_path(p)}'" for p in segment_paths]
    list_txt = out_mp3.parent / f"_concat_{out_mp3.stem}.txt"
    try:
        list_txt.write_text("\n".join(lines) + "\n", encoding="utf-8")
        cmd = [
            ffmpeg,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_txt),
            "-c",
            "copy",
            str(out_mp3),
        ]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return True, []
    except (FileNotFoundError, subprocess.CalledProcessError, OSError):
        return False, ["ffmpeg_concat_failed"]
    finally:
        try:
            list_txt.unlink(missing_ok=True)
        except OSError:
            pass


def _elevenlabs_api_key() -> str:
    return (os.environ.get("ELEVENLABS_API_KEY") or "").strip()


def _elevenlabs_voice_id() -> str:
    return (os.environ.get("ELEVENLABS_VOICE_ID") or ELEVENLABS_DEFAULT_VOICE_ID).strip() or ELEVENLABS_DEFAULT_VOICE_ID


def _elevenlabs_model_id() -> str:
    return (os.environ.get("ELEVENLABS_MODEL_ID") or "eleven_multilingual_v2").strip() or "eleven_multilingual_v2"


def _openai_api_key() -> str:
    return (os.environ.get("OPENAI_API_KEY") or "").strip()


def _openai_tts_voice() -> str:
    return (os.environ.get("OPENAI_TTS_VOICE") or "alloy").strip() or "alloy"


def _openai_tts_model() -> str:
    return (os.environ.get("OPENAI_TTS_MODEL") or "tts-1").strip() or "tts-1"


def _post_elevenlabs_tts(
    text: str,
    *,
    api_key: str,
    voice_id: str,
    voice_settings: Optional[Dict[str, Any]] = None,
    timeout_seconds: float = 120.0,
    post_override: Optional[Callable[[str, str, str, str], bytes]] = None,
) -> Tuple[bytes, Optional[int], str]:
    """POST einen Chunk; Rückgabe (bytes, http_status, error_tag). error_tag leer bei Erfolg."""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    body: Dict[str, Any] = {"text": text, "model_id": _elevenlabs_model_id()}
    if voice_settings:
        body["voice_settings"] = dict(voice_settings)
    if post_override:
        try:
            return post_override(text, api_key, voice_id, json.dumps(body)), 200, ""
        except Exception as exc:
            return b"", None, f"elevenlabs_post_exception:{type(exc).__name__}"
    try:
        with httpx.Client(timeout=timeout_seconds) as client:
            r = client.post(
                url,
                headers={"xi-api-key": api_key, "Content-Type": "application/json"},
                json=body,
            )
        if r.status_code != 200:
            return b"", r.status_code, f"elevenlabs_http_{r.status_code}"
        return r.content or b"", r.status_code, ""
    except httpx.HTTPError as exc:
        return b"", None, f"elevenlabs_transport:{type(exc).__name__}"


def _post_openai_tts(
    text: str,
    *,
    api_key: str,
    voice: str,
    model: str,
    timeout_seconds: float = 120.0,
    post_override: Optional[Callable[[str, str, str, str], bytes]] = None,
) -> Tuple[bytes, Optional[int], str]:
    payload = {"model": model, "voice": voice, "input": text, "response_format": "mp3"}
    if post_override:
        try:
            return post_override(text, api_key, voice, model), 200, ""
        except Exception as exc:
            return b"", None, f"openai_post_exception:{type(exc).__name__}"
    try:
        with httpx.Client(timeout=timeout_seconds) as client:
            r = client.post(
                OPENAI_SPEECH_URL,
                headers={"Authorization": f"Bearer {api_key}"},
                json=payload,
            )
        if r.status_code != 200:
            return b"", r.status_code, f"openai_http_{r.status_code}"
        return r.content or b"", r.status_code, ""
    except httpx.HTTPError as exc:
        return b"", None, f"openai_transport:{type(exc).__name__}"


def synthesize_elevenlabs_mp3(
    narration: str,
    out_mp3: Path,
    work_dir: Path,
    ffmpeg: str,
    *,
    max_retries: int = 2,
    elevenlabs_voice_settings: Optional[Dict[str, Any]] = None,
    elevenlabs_post_override: Optional[Callable[[str, str, str, str], bytes]] = None,
) -> Tuple[bool, int, List[str], List[str]]:
    """
    Chunk → ElevenLabs → Segment-MP3s → ffmpeg concat.
    Rückgabe: (ok, chunk_count, warnings, blocking_on_fatal).
    """
    warns: List[str] = []
    block: List[str] = []
    api_key = _elevenlabs_api_key()
    voice_id = _elevenlabs_voice_id()
    if not api_key:
        warns.append("elevenlabs_env_missing_fallback_smoke")
        return False, 0, warns, block

    chunks = chunk_narration_for_tts(narration, ELEVENLABS_CHUNK_MAX_CHARS)
    if not chunks:
        return False, 0, warns + ["elevenlabs_chunks_empty"], block

    work_dir.mkdir(parents=True, exist_ok=True)
    segment_paths: List[Path] = []
    for i, chunk in enumerate(chunks):
        seg = work_dir / f"tts_elevenlabs_{i:03d}.mp3"
        audio = b""
        err = ""
        status: Optional[int] = None
        for attempt in range(max(1, max_retries)):
            audio, status, err = _post_elevenlabs_tts(
                chunk,
                api_key=api_key,
                voice_id=voice_id,
                voice_settings=elevenlabs_voice_settings,
                post_override=elevenlabs_post_override,
            )
            if audio:
                break
            warns.append(f"elevenlabs_chunk_{i}_retry_{attempt}:{err or 'empty'}")
        if not audio:
            warns.append(f"elevenlabs_chunk_failed:{i}:{err or 'empty_body'}")
            for p in segment_paths:
                try:
                    p.unlink(missing_ok=True)
                except OSError:
                    pass
            return False, 0, warns, ["elevenlabs_mid_run_failed"]
        seg.write_bytes(audio)
        segment_paths.append(seg)

    ok, br = _merge_mp3_segments_ffmpeg(segment_paths, out_mp3, ffmpeg)
    for p in segment_paths:
        try:
            p.unlink(missing_ok=True)
        except OSError:
            pass
    if not ok:
        warns.append("elevenlabs_merge_failed_fallback_smoke")
        return False, 0, warns, br
    return True, len(chunks), warns, []


def synthesize_openai_mp3(
    narration: str,
    out_mp3: Path,
    work_dir: Path,
    ffmpeg: str,
    *,
    max_retries: int = 2,
    openai_voice_override: Optional[str] = None,
    openai_post_override: Optional[Callable[[str, str, str, str], bytes]] = None,
) -> Tuple[bool, int, List[str], List[str]]:
    api_key = _openai_api_key()
    warns: List[str] = []
    if not api_key:
        warns.append("openai_tts_env_missing_fallback_smoke")
        return False, 0, warns, []

    voice = (openai_voice_override or "").strip() or _openai_tts_voice()
    model = _openai_tts_model()
    chunks = chunk_narration_for_tts(narration, OPENAI_CHUNK_MAX_CHARS)
    if not chunks:
        return False, 0, warns + ["openai_chunks_empty"], []

    work_dir.mkdir(parents=True, exist_ok=True)
    segment_paths: List[Path] = []
    for i, chunk in enumerate(chunks):
        seg = work_dir / f"tts_openai_{i:03d}.mp3"
        audio = b""
        err = ""
        for attempt in range(max(1, max_retries)):
            audio, _st, err = _post_openai_tts(
                chunk,
                api_key=api_key,
                voice=voice,
                model=model,
                post_override=openai_post_override,
            )
            if audio:
                break
            warns.append(f"openai_chunk_{i}_retry_{attempt}:{err or 'empty'}")
        if not audio:
            warns.append(f"openai_chunk_failed:{i}:{err or 'empty_body'}")
            for p in segment_paths:
                try:
                    p.unlink(missing_ok=True)
                except OSError:
                    pass
            return False, 0, warns, ["openai_mid_run_failed"]
        seg.write_bytes(audio)
        segment_paths.append(seg)

    ok, br = _merge_mp3_segments_ffmpeg(segment_paths, out_mp3, ffmpeg)
    for p in segment_paths:
        try:
            p.unlink(missing_ok=True)
        except OSError:
            pass
    if not ok:
        warns.append("openai_merge_failed_fallback_smoke")
        return False, 0, warns, br
    return True, len(chunks), warns, []


def load_plan_from_json_file(path: Path) -> Tuple[ProductionPromptPlan, str]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("prompt-plan-json must contain a JSON object")
    data = dict(raw)
    full_script_extra = (data.pop("full_script", None) or "")
    if not isinstance(full_script_extra, str):
        full_script_extra = str(full_script_extra)
    plan = ProductionPromptPlan.model_validate(data)
    return plan, full_script_extra.strip()


def load_plan_from_url(url: str, *, topic: str, duration_minutes: int) -> Tuple[ProductionPromptPlan, str]:
    req = PromptPlanRequest(
        topic=topic,
        title="",
        source_summary="",
        manual_source_url=url.strip(),
        manual_url_duration_minutes=duration_minutes,
    )
    plan = build_production_prompt_plan(req)
    return plan, ""


def build_full_voiceover(
    plan: ProductionPromptPlan,
    *,
    run_id: str,
    out_root: Path,
    voice_mode: str,
    voice_preset: Optional[str] = None,
    full_script_json: str = "",
    ffmpeg_bin: Optional[str] = None,
    elevenlabs_post_override: Optional[Callable[[str, str, str, str], bytes]] = None,
    openai_post_override: Optional[Callable[[str, str, str, str], bytes]] = None,
) -> Dict[str, Any]:
    """Schreibt output/full_voice_<run_id>/ und gibt Metadaten zurück."""
    warnings: List[str] = []
    blocking: List[str] = []
    requested = (voice_mode or "smoke").strip().lower()
    allowed = ("smoke", "elevenlabs", "openai")
    if requested not in allowed:
        warnings.append("voice_mode_unknown_defaulting_smoke")
        requested = "smoke"

    narration, source_type, nw = extract_narration_text(plan, full_script_json=full_script_json)
    warnings.extend(nw)

    voice_preset_requested = (voice_preset or "").strip()
    voice_preset_effective, openai_voice_override, elevenlabs_voice_settings, vp_w = resolve_voice_preset(
        voice_preset_requested or None
    )
    warnings.extend(vp_w)

    wc = count_words(narration) if narration else 0
    est_sec = estimate_speak_duration_seconds(wc)
    if wc > 0 and est_sec <= SMOKE_BASELINE_SECONDS:
        warnings.append("estimated_duration_very_short_check_source_text")

    out_dir = Path(out_root).resolve() / f"full_voice_{run_id}"
    out_dir.mkdir(parents=True, exist_ok=True)
    script_path = out_dir / "narration_script.txt"
    mp3_path = out_dir / "full_voiceover.mp3"
    manifest_path = out_dir / "voice_manifest.json"
    work_tts = out_dir / "_tts_work"
    if work_tts.exists():
        try:
            shutil.rmtree(work_tts)
        except OSError:
            pass

    provider_used = "none"
    chunk_count = 0
    real_tts_generated = False
    fallback_used = False

    if not narration.strip():
        blocking.append("narration_text_empty")
        script_body = _SMOKE_HEADER + "(Kein Sprechertext aus Plan ableitbar.)\n"
        script_path.write_text(script_body, encoding="utf-8")
        est_sec = 0
    else:
        script_path.write_text(_SMOKE_HEADER + narration.strip() + "\n", encoding="utf-8")

    ffmpeg = which_ffmpeg() if ffmpeg_bin is None else ffmpeg_bin
    mp3_ok = False

    if "narration_text_empty" in blocking:
        warnings.append("smoke_mp3_skipped_no_narration_text")
    elif est_sec < 1:
        warnings.append("smoke_mp3_skipped_zero_duration")
    else:
        if requested == "elevenlabs":
            ok_tts, n_chunks, tw, br = synthesize_elevenlabs_mp3(
                narration,
                mp3_path,
                work_tts,
                ffmpeg or "",
                elevenlabs_voice_settings=elevenlabs_voice_settings,
                elevenlabs_post_override=elevenlabs_post_override,
            )
            warnings.extend(tw)
            if ok_tts:
                mp3_ok = True
                provider_used = "elevenlabs"
                chunk_count = n_chunks
                real_tts_generated = True
            else:
                blocking.extend(br)
                fallback_used = True
                if _elevenlabs_api_key():
                    warnings.append("elevenlabs_failed_using_smoke_fallback")
                mp3_ok, br_smoke = _write_smoke_mp3_ffmpeg(mp3_path, est_sec, ffmpeg or "")
                blocking = [b for b in blocking if b not in ("elevenlabs_mid_run_failed",)]
                blocking.extend(br_smoke)
                provider_used = "smoke"
                chunk_count = 0
                real_tts_generated = False
                if not mp3_ok:
                    warnings.append("smoke_placeholder_mp3_not_created_see_blocking")
        elif requested == "openai":
            ok_tts, n_chunks, tw, br = synthesize_openai_mp3(
                narration,
                mp3_path,
                work_tts,
                ffmpeg or "",
                openai_voice_override=openai_voice_override,
                openai_post_override=openai_post_override,
            )
            warnings.extend(tw)
            if ok_tts:
                mp3_ok = True
                provider_used = "openai"
                chunk_count = n_chunks
                real_tts_generated = True
            else:
                blocking.extend(br)
                fallback_used = True
                if _openai_api_key():
                    warnings.append("openai_failed_using_smoke_fallback")
                mp3_ok, br_smoke = _write_smoke_mp3_ffmpeg(mp3_path, est_sec, ffmpeg or "")
                blocking = [b for b in blocking if b not in ("openai_mid_run_failed",)]
                blocking.extend(br_smoke)
                provider_used = "smoke"
                chunk_count = 0
                real_tts_generated = False
                if not mp3_ok:
                    warnings.append("smoke_placeholder_mp3_not_created_see_blocking")
        else:
            provider_used = "smoke"
            mp3_ok, br = _write_smoke_mp3_ffmpeg(mp3_path, est_sec, ffmpeg or "")
            blocking.extend(br)
            if not mp3_ok:
                warnings.append("smoke_placeholder_mp3_not_created_see_blocking")

    try:
        if work_tts.exists():
            shutil.rmtree(work_tts, ignore_errors=True)
    except OSError:
        pass

    manifest: Dict[str, Any] = {
        "run_id": run_id,
        "source_type": source_type,
        "word_count": wc,
        "estimated_duration_seconds": est_sec,
        "voice_mode": requested,
        "voice_preset_requested": voice_preset_requested or None,
        "voice_preset_effective": voice_preset_effective,
        "elevenlabs_voice_settings_from_preset": bool(elevenlabs_voice_settings),
        "provider_used": provider_used,
        "chunk_count": chunk_count,
        "real_tts_generated": real_tts_generated,
        "fallback_used": fallback_used,
        "warnings": warnings,
        "blocking_reasons": list(dict.fromkeys(blocking)),
        "output_dir": str(out_dir),
        "narration_script_path": str(script_path),
        "full_voiceover_path": str(mp3_path) if mp3_ok else "",
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    ok_out = bool(narration.strip()) and mp3_ok and "narration_text_empty" not in blocking
    return {
        "ok": ok_out,
        "run_id": run_id,
        "output_dir": str(out_dir),
        "voice_manifest_path": str(manifest_path),
        "narration_script_path": str(script_path),
        "full_voiceover_path": str(mp3_path) if mp3_ok else "",
        "word_count": wc,
        "estimated_duration_seconds": est_sec,
        "source_type": source_type,
        "voice_mode": manifest["voice_mode"],
        "voice_preset_effective": voice_preset_effective,
        "voice_preset_requested": voice_preset_requested or None,
        "provider_used": provider_used,
        "chunk_count": chunk_count,
        "real_tts_generated": real_tts_generated,
        "fallback_used": fallback_used,
        "warnings": warnings,
        "blocking_reasons": manifest["blocking_reasons"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="BA 20.0/20.1 — Full voiceover from URL or PromptPlan JSON")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--url", default="", dest="url", help="Artikel-URL → build_production_prompt_plan")
    src.add_argument("--prompt-plan-json", type=Path, default=None, dest="prompt_plan_json")
    parser.add_argument("--out-root", type=Path, default=ROOT / "output", dest="out_root")
    parser.add_argument("--run-id", default="", dest="run_id")
    parser.add_argument(
        "--voice-mode",
        choices=("smoke", "elevenlabs", "openai"),
        default="smoke",
        dest="voice_mode",
    )
    parser.add_argument(
        "--voice-preset",
        default="",
        dest="voice_preset",
        help="BA 20.3 optional: documentary_de | dramatic_documentary_de | calm_explainer_de",
    )
    parser.add_argument("--topic", default="Full Voiceover Run", dest="topic")
    parser.add_argument("--duration-minutes", type=int, default=10, dest="duration_minutes")
    args = parser.parse_args()

    run_id = (args.run_id or "").strip() or str(uuid.uuid4())
    try:
        if args.prompt_plan_json:
            plan, fs_extra = load_plan_from_json_file(args.prompt_plan_json)
            meta = build_full_voiceover(
                plan,
                run_id=run_id,
                out_root=args.out_root,
                voice_mode=args.voice_mode,
                voice_preset=(args.voice_preset or "").strip() or None,
                full_script_json=fs_extra,
            )
        else:
            url = (args.url or "").strip()
            if not url:
                raise ValueError("--url must be non-empty")
            plan, _ = load_plan_from_url(url, topic=args.topic, duration_minutes=args.duration_minutes)
            meta = build_full_voiceover(
                plan,
                run_id=run_id,
                out_root=args.out_root,
                voice_mode=args.voice_mode,
                voice_preset=(args.voice_preset or "").strip() or None,
                full_script_json="",
            )
    except (OSError, ValueError, json.JSONDecodeError) as e:
        print(json.dumps({"ok": False, "error": type(e).__name__, "message": str(e)}, ensure_ascii=False, indent=2))
        return 2

    print(json.dumps(meta, ensure_ascii=False, indent=2))
    return 0 if meta.get("ok") else 3


if __name__ == "__main__":
    raise SystemExit(main())
