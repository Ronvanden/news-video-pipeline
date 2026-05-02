"""BA 15.5 — One-Command URL → Demo-Orchestrierung (PromptPlan + Kommando-Hooks, kein Auto-Publishing)."""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.prompt_engine.pipeline import build_production_prompt_plan
from app.prompt_engine.schema import PromptPlanRequest


def main() -> int:
    parser = argparse.ArgumentParser(description="Manual URL → Story → PromptPlan → Demo-Kommando-Hints.")
    parser.add_argument("url", help="Artikel- oder Seiten-URL")
    parser.add_argument(
        "--topic",
        default="URL Demo Run",
        help="Pflichtfeld topic für PromptPlanRequest (Platzhalter).",
    )
    parser.add_argument(
        "--rewrite-mode",
        default="",
        dest="rewrite_mode",
        help="Optional: documentary | emotional | mystery | viral",
    )
    parser.add_argument(
        "--duration-minutes",
        type=int,
        default=10,
        dest="duration_minutes",
    )
    args = parser.parse_args()

    req = PromptPlanRequest(
        topic=args.topic,
        title="",
        source_summary="",
        manual_source_url=args.url.strip(),
        manual_url_rewrite_mode=(args.rewrite_mode or "").strip(),
        manual_url_duration_minutes=args.duration_minutes,
    )
    plan = build_production_prompt_plan(req)

    mu = plan.manual_url_story_execution_result
    gate = plan.manual_url_quality_gate_result
    demo = plan.manual_url_demo_execution_result

    payload = {
        "local_run_id": str(uuid.uuid4()),
        "input_url": args.url.strip(),
        "rewritten_story": {
            "hook": plan.hook,
            "hook_type": plan.hook_type,
            "script_preview": mu.narrative_rewrite.full_script_preview if mu else "",
            "chapters": [
                {"title": c.title, "summary": (c.summary or "")[:280]}
                for c in plan.chapter_outline[:16]
            ],
        },
        "prompt_plan_summary": {
            "template_type": plan.template_type,
            "video_template": plan.video_template,
            "chapter_count": len(plan.chapter_outline),
            "scene_prompt_count": len(plan.scene_prompts),
            "warnings_head": plan.warnings[:12],
        },
        "url_quality_gate": gate.model_dump() if gate else None,
        "leonardo_asset_hook": list(demo.leonardo_command_hint) if demo else [],
        "voice_asset_hook": list(demo.voice_command_hint) if demo else [],
        "first_demo_video_command": list(demo.first_demo_video_command_hint) if demo else [],
        "local_output_summary": demo.local_run_summary if demo else "",
        "demo_execution": demo.model_dump() if demo else None,
    }

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
