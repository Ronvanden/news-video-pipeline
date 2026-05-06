"""Manual URL Story Execution V1 — Kernpfad auf PromptPlan."""

from unittest.mock import patch

from app.prompt_engine.pipeline import build_production_prompt_plan
from app.prompt_engine.schema import PromptPlanRequest


@patch("app.manual_url_story.engine.extract_text_from_url")
@patch("app.manual_url_story.engine.build_script_response_from_extracted_text")
def test_manual_url_story_execution_happy_path(mock_script, mock_extract):
    mock_extract.return_value = ("Article body text " * 80, [])
    mock_script.return_value = (
        "URL Story Title",
        "Hook aus Artikel.",
        [{"title": "A", "content": "ca"}, {"title": "B", "content": "cb"}],
        "Full script " * 50,
        ["https://example.com/news/1"],
        ["script_warning"],
    )

    plan = build_production_prompt_plan(
        PromptPlanRequest(
            topic="Fallback Topic",
            title="",
            source_summary="",
            manual_source_url="https://example.com/news/1?ref=x",
        )
    )

    assert plan.manual_url_story_execution_result is not None
    mu = plan.manual_url_story_execution_result
    assert mu.intake.status == "ok"
    assert "example.com" in mu.intake.source_url_display
    assert "?" not in mu.intake.source_url_display
    assert mu.extraction.status == "ok"
    assert mu.narrative_rewrite.status == "ok"
    assert mu.narrative_rewrite.script_title == "URL Story Title"
    assert len(plan.chapter_outline) == 2
    assert plan.chapter_outline[0].title == "A"
    assert plan.hook == "Hook aus Artikel."
    assert plan.hook_type == "manual_url_story_rewrite"
    assert mu.asset_prompt_build.scene_prompt_count == len(plan.scene_prompts)
    assert mu.demo_video_execution.status == "ready"
    assert "build_first_demo_video.py" in " ".join(mu.demo_video_execution.command_hint)
    assert any("[manual_url_story]" in w for w in plan.warnings)
    assert any("script_warning" in w for w in plan.warnings)
    assert plan.manual_url_quality_gate_result is not None
    assert plan.manual_url_quality_gate_result.url_quality_status in (
        "strong",
        "moderate",
        "weak",
        "blocked",
    )
    assert plan.manual_url_demo_execution_result is not None
    assert plan.manual_url_demo_execution_result.leonardo_command_hint
    assert plan.manual_url_demo_execution_result.voice_command_hint


@patch("app.manual_url_story.engine.extract_text_from_url")
def test_manual_url_extraction_blocked_falls_back_to_topic(mock_extract):
    mock_extract.return_value = ("", ["empty_extract"])

    plan = build_production_prompt_plan(
        PromptPlanRequest(
            topic="Polizei und Mord",
            title="",
            source_summary="",
            manual_source_url="https://example.com/empty",
        )
    )

    mu = plan.manual_url_story_execution_result
    assert mu is not None
    assert mu.extraction.status == "blocked"
    assert mu.narrative_rewrite.status == "skipped"
    assert mu.demo_video_execution.status == "blocked"
    assert plan.hook_type != "manual_url_story_rewrite"
    assert len(plan.chapter_outline) >= 1
    assert plan.manual_url_quality_gate_result is not None
    assert plan.manual_url_quality_gate_result.url_quality_status == "blocked"
    assert plan.manual_url_demo_execution_result is not None
    assert plan.manual_url_demo_execution_result.execution_status == "blocked"
