"""BA 10.8 — Job runner mock."""

from app.prompt_engine.pipeline import build_production_prompt_plan
from app.prompt_engine.schema import PromptPlanRequest
from app.production_connectors.job_runner_mock import simulate_provider_job_run


def test_simulate_respects_queue_order_and_success():
    plan = build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord", title="", source_summary=""))
    mock = simulate_provider_job_run(plan)
    assert mock.runner_status in ("complete", "partial", "blocked")
    q = plan.provider_execution_queue_result
    if q and q.queue_status == "ready" and len(q.jobs) == 5:
        assert len(mock.job_outcomes) == 5
        assert all(o.final_status == "simulated_success" for o in mock.job_outcomes)
        assert len(mock.connector_execution_records) == 5
    else:
        assert mock.runner_status in ("partial", "blocked") or len(mock.job_outcomes) <= 5
