"""BA 15.5 — Manuelle Demo-Execution-Hooks (Kommando-Orchestrierung, kein Auto-Run)."""

from __future__ import annotations

from typing import List

from app.manual_url_story.engine import ManualUrlRewriteOutcome
from app.manual_url_story.schema import DemoExecutionStatus, ManualUrlDemoExecutionResult


def build_manual_url_demo_execution_result(
    outcome: ManualUrlRewriteOutcome | None,
    *,
    narrative_ok: bool,
    scene_prompt_count: int,
    first_demo_video_hint: List[str],
) -> ManualUrlDemoExecutionResult | None:
    if outcome is None:
        return None

    blocking: List[str] = []
    warnings: List[str] = []
    leonardo = ["python", "scripts/run_leonardo_smoke_test.py"]
    voice = ["python", "scripts/run_voice_smoke_test_and_save.py"]

    if not outcome.extraction_ok:
        blocking.append("extraction_failed")
    if not narrative_ok:
        blocking.append("narrative_not_available")
    if scene_prompt_count <= 0:
        blocking.append("no_scene_prompts")

    status: DemoExecutionStatus
    if blocking:
        status = "blocked"
    elif narrative_ok and scene_prompt_count > 0:
        status = "ready"
    else:
        status = "partial"

    notes = [
        "Leonardo-Smoke liefert nutzbares Bild; Voice-Smoke schreibt output/voice_smoke_test_output.mp3.",
        "Demo-Video: statisches Bild + MP3 → output/first_demo_video.mp4.",
    ]
    if status == "ready":
        warnings.append("url_to_demo_commands_ready_no_auto_publish")

    summary_parts = [
        f"extraction_ok={outcome.extraction_ok}",
        f"narrative_ok={narrative_ok}",
        f"scene_prompts={scene_prompt_count}",
        f"demo_video_hint={' '.join(first_demo_video_hint) if first_demo_video_hint else 'n/a'}",
    ]
    local_summary = "; ".join(summary_parts)

    return ManualUrlDemoExecutionResult(
        execution_version="15.5-v1",
        execution_status=status,
        local_run_summary=local_summary,
        leonardo_command_hint=leonardo,
        voice_command_hint=voice,
        first_demo_video_command_hint=list(first_demo_video_hint),
        asset_handoff_notes=notes,
        warnings=warnings,
        blocking_reasons=blocking,
    )
