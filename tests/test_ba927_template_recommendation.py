"""BA 9.27 — Auto Template Recommendation V1."""

import app.prompt_engine.loader as pe_loader
from app.prompt_engine.loader import load_all_prompt_templates
from app.prompt_engine.schema import PerformanceRecord
from app.prompt_engine.template_recommendation import recommend_best_template


def test_recommendation_follows_topic_keywords():
    pe_loader.list_prompt_template_keys.cache_clear()
    pe_loader.load_prompt_template.cache_clear()
    templates = load_all_prompt_templates()
    keys = sorted(templates.keys())
    r = recommend_best_template(
        "Mordfall Polizei und Gerichtsverhandlung",
        keys,
        None,
        template_docs=templates,
        current_narrative_archetype_id="",
    )
    assert r.recommended_template == "true_crime"
    assert r.recommendation_basis == "topic_match"
    assert r.confidence >= 40


def test_recommendation_prefers_historical_performance_when_data_favors_other_template():
    pe_loader.list_prompt_template_keys.cache_clear()
    pe_loader.load_prompt_template.cache_clear()
    templates = load_all_prompt_templates()
    keys = sorted(templates.keys())
    perf = [
        PerformanceRecord(
            id="1",
            template_type="true_crime",
            quality_score=55,
            narrative_score=50,
            created_at="",
            updated_at="",
        ),
        PerformanceRecord(
            id="2",
            template_type="mystery_history",
            quality_score=92,
            narrative_score=91,
            created_at="",
            updated_at="",
        ),
    ]
    r = recommend_best_template(
        "Polizei und Mord",
        keys,
        perf,
        template_docs=templates,
        current_narrative_archetype_id="",
    )
    assert r.recommended_template == "mystery_history"
    assert r.recommendation_basis == "historical_performance"
    assert "true_crime" in r.alternatives
