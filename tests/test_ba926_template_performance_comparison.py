"""BA 9.26 — Template Performance Comparison V1."""

from app.prompt_engine.schema import PerformanceRecord
from app.prompt_engine.template_performance_comparison import compare_template_performance


def test_comparison_insufficient_without_records():
    r = compare_template_performance([])
    assert r.comparison_status == "insufficient_data"
    assert r.best_template_type is None
    assert r.templates == []


def test_comparison_ranks_templates_by_overall_score():
    recs = [
        PerformanceRecord(
            id="a",
            template_type="true_crime",
            quality_score=60,
            narrative_score=55,
            created_at="",
            updated_at="",
        ),
        PerformanceRecord(
            id="b",
            template_type="true_crime",
            quality_score=62,
            narrative_score=58,
            created_at="",
            updated_at="",
        ),
        PerformanceRecord(
            id="c",
            template_type="mystery_history",
            quality_score=88,
            narrative_score=90,
            created_at="",
            updated_at="",
        ),
    ]
    r = compare_template_performance(recs)
    assert r.comparison_status == "ready"
    assert r.best_template_type == "mystery_history"
    assert len(r.templates) == 2
    assert r.templates[0].template_type == "mystery_history"
    assert r.templates[0].overall_template_score >= r.templates[1].overall_template_score
