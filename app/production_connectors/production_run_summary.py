"""BA 10.10 — Production Run Summary (read-only Aggregat)."""

from __future__ import annotations

from app.production_connectors.schema import ProductionLaunchRecommendation, ProductionRunSummaryResult
def build_production_run_summary(plan: object) -> ProductionRunSummaryResult:
    fr = plan.final_readiness_gate_result
    guard = plan.live_execution_guard_result
    pol = plan.execution_policy_result
    mock = plan.provider_job_runner_mock_result
    tracker = plan.asset_status_tracker_result
    cost = plan.cost_projection_result
    queue = plan.provider_execution_queue_result

    run_readiness = fr.summary if fr else "readiness_unknown"
    execution_safety = guard.live_execution_status if guard else "guard_unknown"

    projected_cost = float(cost.total_estimated_cost_eur) if cost else 0.0
    projected_jobs = int(queue.total_jobs) if queue else 0

    provider_summary = ""
    if mock:
        provider_summary = mock.summary
    asset_summary = ""
    if tracker:
        asset_summary = (
            f"expected={tracker.total_expected_assets} generated={tracker.generated_assets} "
            f"pending={tracker.pending_assets} failed={tracker.failed_assets}"
        )

    launch: ProductionLaunchRecommendation = "hold"
    if guard and guard.live_execution_status == "blocked":
        launch = "hold"
    elif pol and pol.global_execution_mode == "emergency_stop":
        launch = "hold"
    elif (
        pol
        and pol.global_execution_mode == "guarded_live"
        and not (pol.violations or [])
        and guard
        and guard.live_execution_status == "live_ready"
    ):
        launch = "guarded_live_candidate"
    elif mock and mock.runner_status in ("complete", "partial"):
        launch = "dry_run_execute"

    founder = (
        f"Safety={execution_safety}; Policy={pol.global_execution_mode if pol else 'n/a'}; "
        f"Mock={mock.runner_status if mock else 'n/a'}; Launch={launch}. V1 ohne Live-API."
    )

    return ProductionRunSummaryResult(
        run_readiness=run_readiness[:400],
        execution_safety=execution_safety,
        projected_cost=round(projected_cost, 4),
        projected_jobs=projected_jobs,
        provider_summary=provider_summary[:400],
        asset_summary=asset_summary[:400],
        launch_recommendation=launch,
        founder_summary=founder[:800],
    )
