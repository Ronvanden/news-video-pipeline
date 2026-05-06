"""BA 9.29 — Production OS Dashboard Summary V1."""

from app.prompt_engine.pipeline import build_production_prompt_plan
from app.prompt_engine.production_os_dashboard import build_production_os_dashboard
from app.prompt_engine.schema import PromptPlanRequest


def test_dashboard_contains_core_metrics():
    plan = build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord", title="", source_summary=""))
    d = build_production_os_dashboard(plan)
    assert d.prompt_health_score >= 0
    assert d.production_readiness_score >= 0
    assert d.estimated_cost >= 0
    assert d.recommended_template
    assert "Leonardo" in d.recommended_provider_strategy or d.recommended_provider_strategy == ""
    assert isinstance(d.top_risks, list)
    assert isinstance(d.top_strengths, list)
    assert d.executive_summary
