"""BA 20.0 — Founder Full Voiceover: PromptPlan → narration_script.txt + MP3 + voice_manifest.json."""

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
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.prompt_engine.pipeline import build_production_prompt_plan
from app.prompt_engine.schema import ProductionPromptPlan, PromptPlanRequest
from app.utils import count_words

# Heuristik 130–160 W/min — Mitte für geschätzte Sprechdauer
DEFAULT_WPM = 145.0
MIN_BODY_CHARS = 24
SMOKE_MP3_MAX_SECONDS = 3600
SMOKE_BASELINE_SECONDS = 5  # Referenz: kurzer Smoke-Clip ~2 s; Ziel deutlich darüber bei echtem Skript

_SMOKE_HEADER = (
    "# BA 20.0 — FULL VOICEOVER (SMOKE / PLACEHOLDER)\n"
    "# Die MP3 ist bewusst keine echte TTS-Stimme: Dauer orientiert sich an Wortzahl/WPM.\n"
    "# Für echte Stimme: voice_mode=provider + API (noch optional; siehe voice_manifest warnings).\n\n"
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
        f"anullsrc=r=44100:cl=stereo",
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
    full_script_json: str = "",
    ffmpeg_bin: Optional[str] = None,
) -> Dict[str, Any]:
    """Schreibt output/full_voice_<run_id>/ und gibt Metadaten zurück."""
    warnings: List[str] = []
    blocking: List[str] = []
    requested_voice_mode = (voice_mode or "smoke").strip().lower()
    if requested_voice_mode not in ("smoke", "provider"):
        warnings.append("voice_mode_unknown_defaulting_smoke")
        requested_voice_mode = "smoke"

    if requested_voice_mode == "provider":
        if not (os.environ.get("ELEVENLABS_API_KEY") or "").strip():
            warnings.append("provider_voice_env_missing_using_smoke_placeholder")
        # V1: keine Pflicht-Provider-HTTP — Audio bleibt Smoke (Stille/Länge-Näherung).

    narration, source_type, nw = extract_narration_text(plan, full_script_json=full_script_json)
    warnings.extend(nw)

    wc = count_words(narration) if narration else 0
    est_sec = estimate_speak_duration_seconds(wc)
    if wc > 0 and est_sec <= SMOKE_BASELINE_SECONDS:
        warnings.append("estimated_duration_very_short_check_source_text")

    out_dir = Path(out_root).resolve() / f"full_voice_{run_id}"
    out_dir.mkdir(parents=True, exist_ok=True)
    script_path = out_dir / "narration_script.txt"
    mp3_path = out_dir / "full_voiceover.mp3"
    manifest_path = out_dir / "voice_manifest.json"

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
        mp3_ok, br = _write_smoke_mp3_ffmpeg(mp3_path, est_sec, ffmpeg or "")
        blocking.extend(br)
        if not mp3_ok:
            warnings.append("smoke_placeholder_mp3_not_created_see_blocking")

    manifest: Dict[str, Any] = {
        "run_id": run_id,
        "source_type": source_type,
        "word_count": wc,
        "estimated_duration_seconds": est_sec,
        "voice_mode": requested_voice_mode,
        "warnings": warnings,
        "blocking_reasons": list(dict.fromkeys(blocking)),
        "output_dir": str(out_dir),
        "narration_script_path": str(script_path),
        "full_voiceover_path": str(mp3_path) if mp3_ok else "",
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "ok": bool(narration.strip()) and mp3_ok and "narration_text_empty" not in blocking,
        "run_id": run_id,
        "output_dir": str(out_dir),
        "voice_manifest_path": str(manifest_path),
        "narration_script_path": str(script_path),
        "full_voiceover_path": str(mp3_path) if mp3_ok else "",
        "word_count": wc,
        "estimated_duration_seconds": est_sec,
        "source_type": source_type,
        "voice_mode": manifest["voice_mode"],
        "warnings": warnings,
        "blocking_reasons": manifest["blocking_reasons"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="BA 20.0 — Full voiceover track from URL or PromptPlan JSON")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--url", default="", dest="url", help="Artikel-URL → build_production_prompt_plan")
    src.add_argument("--prompt-plan-json", type=Path, default=None, dest="prompt_plan_json")
    parser.add_argument("--out-root", type=Path, default=ROOT / "output", dest="out_root")
    parser.add_argument("--run-id", default="", dest="run_id")
    parser.add_argument(
        "--voice-mode",
        choices=("smoke", "provider"),
        default="smoke",
        dest="voice_mode",
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
                full_script_json="",
            )
    except (OSError, ValueError, json.JSONDecodeError) as e:
        print(json.dumps({"ok": False, "error": type(e).__name__, "message": str(e)}, ensure_ascii=False, indent=2))
        return 2

    print(json.dumps(meta, ensure_ascii=False, indent=2))
    return 0 if meta.get("ok") else 3


if __name__ == "__main__":
    raise SystemExit(main())
