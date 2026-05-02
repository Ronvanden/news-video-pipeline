"""BA 10.5 — API activation control."""

from app.prompt_engine.pipeline import build_production_prompt_plan
from app.prompt_engine.schema import PromptPlanRequest


def test_default_activation_is_dry_run():
    plan = build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord", title="", source_summary=""))
    a = plan.api_activation_control_result
    assert a is not None
    assert a.activation_mode == "dry_run"
    assert a.activation_allowed is False
    assert not a.provider_activation_matrix.leonardo
