"""BA 9.10 — Prompt Planning System V1 (deterministisch, Hook-Engine-Anbindung)."""

import pytest

import app.prompt_engine.loader as pe_loader
from app.prompt_engine.pipeline import build_production_prompt_plan
from app.prompt_engine.schema import PromptPlanRequest


@pytest.fixture(autouse=True)
def _clear_pe_loader_cache():
    pe_loader.list_prompt_template_keys.cache_clear()
    pe_loader.load_prompt_template.cache_clear()
    yield
    pe_loader.list_prompt_template_keys.cache_clear()
    pe_loader.load_prompt_template.cache_clear()


def test_classify_true_crime_keywords():
    plan = build_production_prompt_plan(
        PromptPlanRequest(topic="Der Mordfall — Polizei und Ermittlung", title="", source_summary="")
    )
    assert plan.template_type == "true_crime"
    assert plan.video_template == "true_crime"
    assert plan.hook
    assert len(plan.chapter_outline) >= 1
    assert len(plan.scene_prompts) == len(plan.chapter_outline)


def test_classify_mystery_history_keywords():
    plan = build_production_prompt_plan(
        PromptPlanRequest(topic="Ein historisches Mysterium aus dem Mittelalter", title="", source_summary="")
    )
    assert plan.template_type == "mystery_history"
    assert plan.video_template == "mystery_explainer"


def test_default_documentary_when_no_keyword_hit():
    plan = build_production_prompt_plan(
        PromptPlanRequest(topic="Allgemeines Video ohne Treffer", title="", source_summary="")
    )
    assert plan.template_type == "documentary"
    assert plan.video_template == "generic"


def test_template_override():
    plan = build_production_prompt_plan(
        PromptPlanRequest(
            topic="Polizei und Gericht",
            template_override="mystery_history",
        )
    )
    assert plan.template_type == "mystery_history"


def test_hook_engine_fields_present():
    plan = build_production_prompt_plan(
        PromptPlanRequest(topic="Ein Fall für die Forensik", title="Titel", source_summary="Kurz")
    )
    assert plan.hook_type
    assert 0 <= plan.hook_score <= 10


def test_unknown_override_raises():
    with pytest.raises(ValueError, match="Unbekanntes"):
        build_production_prompt_plan(PromptPlanRequest(topic="x", template_override="nosuch"))