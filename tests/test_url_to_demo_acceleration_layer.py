"""BA 15.5–15.7 — URL To Demo Acceleration: Quality Gate, Rewrite-Preset, Demo-Hooks."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.manual_url_story.quality_gate import build_url_quality_gate_result
from app.manual_url_story.rewrite_mode import (
    prompt_template_for_rewrite_mode,
    resolve_video_template_for_manual_url_script,
)
from app.prompt_engine.loader import load_all_prompt_templates
from app.prompt_engine.pipeline import build_production_prompt_plan
from app.prompt_engine.schema import PromptPlanRequest


def test_url_quality_gate_strong_extract():
    text = " ".join(["Dies ist ein Satz mit Substanz und der Zahl 2020."] * 90)
    r = build_url_quality_gate_result(
        extraction_ok=True,
        extracted_text=text,
        narrative_ok=True,
        script_title="Ein Titel",
        full_script="Wort " * 900,
        chapter_count=5,
    )
    assert r.url_quality_status in ("strong", "moderate")
    assert r.hook_potential_score >= 35
    assert r.recommended_mode in ("documentary", "emotional", "mystery", "viral")


def test_url_quality_gate_weak_but_not_blocked():
    line = (
        "Erster Satz mit genug Wörtern für Dichte. Zweiter Satz mit Fakten und 1999. "
        "Dritter Satz mit einem offenen Warum und etwas Rätselcharakter?"
    )
    text = " ".join([line] * 25)
    r = build_url_quality_gate_result(
        extraction_ok=True,
        extracted_text=text,
        narrative_ok=True,
        script_title="",
        full_script="x",
        chapter_count=2,
    )
    assert r.url_quality_status in ("weak", "moderate")
    assert r.url_quality_status != "blocked"


def test_url_quality_gate_blocked_short():
    r = build_url_quality_gate_result(
        extraction_ok=True,
        extracted_text="nur drei worte hier",
        narrative_ok=False,
        script_title="",
        full_script="",
        chapter_count=0,
    )
    assert r.url_quality_status == "blocked"
    assert r.blocking_reasons


def test_rewrite_mode_prompt_template_mapping():
    templates = load_all_prompt_templates()
    assert prompt_template_for_rewrite_mode("mystery", templates) == "mystery_history"
    assert prompt_template_for_rewrite_mode("documentary", templates) == "mystery_history"
    assert prompt_template_for_rewrite_mode("emotional", templates) == "true_crime"


def test_resolve_video_template_priority():
    class _Req:
        template_override = "mystery_history"
        manual_url_rewrite_mode = "viral"
        manual_url_video_template = "generic"

    assert resolve_video_template_for_manual_url_script(_Req()) == "mystery_explainer"

    class _Req2:
        template_override = None
        manual_url_rewrite_mode = "mystery"
        manual_url_video_template = "generic"

    assert resolve_video_template_for_manual_url_script(_Req2()) == "mystery_explainer"


@patch("app.manual_url_story.engine.extract_text_from_url")
@patch("app.manual_url_story.engine.build_script_response_from_extracted_text")
def test_manual_url_rewrite_mode_api_fields(mock_script, mock_extract):
    mock_extract.return_value = ("Body " * 200, [])
    mock_script.return_value = (
        "T",
        "Hook.",
        [{"title": "K1", "content": "a"}],
        "Script " * 120,
        ["https://ex.example/news/x"],
        [],
    )

    plan = build_production_prompt_plan(
        PromptPlanRequest(
            topic="Fallback",
            manual_source_url="https://ex.example/news/x",
            manual_url_rewrite_mode="mystery",
        )
    )
    assert plan.template_type == "mystery_history"
    assert plan.manual_url_demo_execution_result is not None
    assert plan.manual_url_demo_execution_result.execution_status == "ready"


@patch("app.manual_url_story.engine.extract_text_from_url")
@patch("app.manual_url_story.engine.build_script_response_from_extracted_text")
def test_story_engine_prompt_plan_api_manual_url_fields(mock_script, mock_extract):
    mock_extract.return_value = ("Wort " * 220, [])
    mock_script.return_value = (
        "API Titel",
        "Hook?",
        [{"title": "K1", "content": "Inhalt."}],
        "Script " * 120,
        ["https://example.com/page"],
        [],
    )
    client = TestClient(app)
    res = client.post(
        "/story-engine/prompt-plan",
        json={"topic": "Demo", "manual_source_url": "https://example.com/page"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body.get("manual_url_quality_gate_result") is not None
    assert body.get("manual_url_demo_execution_result") is not None
    assert body.get("manual_url_story_execution_result") is not None
    assert body.get("cash_optimization_layer_result") is not None
    assert body["cash_optimization_layer_result"]["roi"]["candidate_roi_score"] >= 0
