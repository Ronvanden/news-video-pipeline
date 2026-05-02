"""BA 10.9 — Asset status tracker."""

from app.prompt_engine.pipeline import build_production_prompt_plan
from app.prompt_engine.schema import PromptPlanRequest


def test_asset_counts_match_five_slots():
    plan = build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord", title="", source_summary=""))
    t = plan.asset_status_tracker_result
    assert t is not None
    assert t.total_expected_assets == 5
    assert len(t.asset_matrix) == 5
    m = plan.provider_job_runner_mock_result
    if m and m.runner_status == "complete" and len(m.job_outcomes) == 5:
        assert t.generated_assets == 5
        assert t.pending_assets == 0
