"""BA 32.69 — dry-run readiness helper for one manual live 2-clip smoke.

This helper never calls live providers and never reads .env files. It only checks
process environment variable *presence* and prints an operator checklist summary.
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict, List, Sequence

IMAGE_PROVIDER_ENV: Dict[str, List[str]] = {
    "placeholder": [],
    "leonardo": ["LEONARDO_API_KEY"],
    "openai_image": ["OPENAI_API_KEY"],
    "gemini_image": ["GEMINI_API_KEY", "GOOGLE_API_KEY"],
}

VOICE_PROVIDER_ENV: Dict[str, List[str]] = {
    "smoke": [],
    "elevenlabs": ["ELEVENLABS_API_KEY"],
    "openai": ["OPENAI_API_KEY"],
}

OPTIONAL_ENV_NAMES: Sequence[str] = (
    "ELEVENLABS_VOICE_ID",
    "ELEVENLABS_MODEL_ID",
    "OPENAI_TTS_VOICE",
    "OPENAI_TTS_MODEL",
    "GEMINI_IMAGE_MODEL",
    "GEMINI_IMAGE_TRANSPORT",
    "LEONARDO_MODEL_ID",
    "LEONARDO_API_ENDPOINT",
)


def _present(name: str) -> bool:
    return bool((os.environ.get(name) or "").strip())


def _provider_env_ready(names: Sequence[str]) -> bool:
    if not names:
        return True
    return any(_present(name) for name in names)


def build_readiness_summary(
    *,
    image_provider: str,
    voice_provider: str,
    duration_minutes: float,
    max_scenes: int,
    max_motion_clips: int,
    motion_clip_duration_seconds: int,
    confirm_provider_costs: bool,
    ack_live_provider_risk: bool,
    ack_not_ci: bool,
) -> Dict[str, Any]:
    """Return a secret-safe dry-run readiness summary for the manual smoke."""
    required_env_groups: Dict[str, List[str]] = {
        "runway_motion": ["RUNWAY_API_KEY"],
        "image_provider": list(IMAGE_PROVIDER_ENV[image_provider]),
        "voice_provider": list(VOICE_PROVIDER_ENV[voice_provider]),
    }
    env_presence = {
        name: _present(name)
        for group in required_env_groups.values()
        for name in group
    }
    env_presence.update({name: _present(name) for name in OPTIONAL_ENV_NAMES})

    blockers: List[str] = []
    warnings: List[str] = []

    if _present("CI"):
        blockers.append("ci_environment_detected_do_not_run_live_smoke")
    if not ack_not_ci:
        blockers.append("ack_not_ci_required")
    if not confirm_provider_costs:
        blockers.append("confirm_provider_costs_required")
    if not ack_live_provider_risk:
        blockers.append("ack_live_provider_risk_required")
    if not _present("RUNWAY_API_KEY"):
        blockers.append("runway_api_key_missing")
    if not _provider_env_ready(required_env_groups["image_provider"]):
        blockers.append(f"{image_provider}_env_missing")
    if not _provider_env_ready(required_env_groups["voice_provider"]):
        blockers.append(f"{voice_provider}_env_missing")

    if max_motion_clips != 2:
        blockers.append("max_motion_clips_must_equal_2_for_ba3269")
    if motion_clip_duration_seconds < 5 or motion_clip_duration_seconds > 10:
        warnings.append("motion_clip_duration_recommendation_5_to_10_seconds")
    if duration_minutes <= 0 or duration_minutes > 2:
        warnings.append("duration_recommendation_1_to_2_minutes_for_cost_control")
    if max_scenes <= 0 or max_scenes > 4:
        warnings.append("max_scenes_recommendation_2_to_4_for_first_live_smoke")
    if image_provider == "placeholder":
        warnings.append("placeholder_images_selected_not_a_full_live_visual_smoke")
    if voice_provider == "smoke":
        warnings.append("smoke_voice_selected_not_a_full_live_voice_smoke")

    checklist = [
        "Do not run this live smoke in CI or unattended automation.",
        "Confirm provider costs/billing before enabling live image, voice, and Runway motion.",
        "Use a short duration (1-2 minutes), small scene cap (2-4), max_motion_clips=2.",
        "Use 5-10 second motion clips; inspect that clips play only in their slot windows.",
        "After the run, inspect run_summary.json, asset_manifest.json, final_video.mp4, and OPEN_ME_VIDEO_RESULT.html.",
        "Abort safely with Ctrl+C before provider dispatch or stop the local server/job if unexpected costs, wrong URL, CI, or missing keys are detected.",
    ]

    return {
        "ba_id": "BA 32.69",
        "mode": "dry_run_readiness_only_no_external_api_calls",
        "ready": not blockers,
        "status": "ready" if not blockers else "blocked",
        "required_env_groups": required_env_groups,
        "env_presence": env_presence,
        "operator_confirmations": {
            "confirm_provider_costs": bool(confirm_provider_costs),
            "ack_live_provider_risk": bool(ack_live_provider_risk),
            "ack_not_ci": bool(ack_not_ci),
        },
        "recommended_bounds": {
            "duration_minutes": duration_minutes,
            "max_scenes": int(max_scenes),
            "max_motion_clips": int(max_motion_clips),
            "motion_clip_duration_seconds": int(motion_clip_duration_seconds),
        },
        "blockers": blockers,
        "warnings": warnings,
        "checklist": checklist,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="BA 32.69 — dry-run readiness checklist for one manual live two-clip smoke"
    )
    parser.add_argument("--image-provider", choices=sorted(IMAGE_PROVIDER_ENV), default="gemini_image")
    parser.add_argument("--voice-provider", choices=sorted(VOICE_PROVIDER_ENV), default="elevenlabs")
    parser.add_argument("--duration-minutes", type=float, default=1.0)
    parser.add_argument("--max-scenes", type=int, default=3)
    parser.add_argument("--max-motion-clips", type=int, default=2)
    parser.add_argument("--motion-clip-duration-seconds", type=int, default=10)
    parser.add_argument("--confirm-provider-costs", action="store_true")
    parser.add_argument("--ack-live-provider-risk", action="store_true")
    parser.add_argument("--ack-not-ci", action="store_true")
    args = parser.parse_args(argv)

    summary = build_readiness_summary(
        image_provider=args.image_provider,
        voice_provider=args.voice_provider,
        duration_minutes=args.duration_minutes,
        max_scenes=args.max_scenes,
        max_motion_clips=args.max_motion_clips,
        motion_clip_duration_seconds=args.motion_clip_duration_seconds,
        confirm_provider_costs=bool(args.confirm_provider_costs),
        ack_live_provider_risk=bool(args.ack_live_provider_risk),
        ack_not_ci=bool(args.ack_not_ci),
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary.get("ready") else 3


if __name__ == "__main__":
    raise SystemExit(main())
