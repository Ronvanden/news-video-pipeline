"""BA 10.6 — globale Execution-Policy / Kill-Switch (ohne Persistenz)."""

from __future__ import annotations

from typing import List

from app.production_connectors.schema import ExecutionPolicyResult, GlobalExecutionMode
DEFAULT_MAX_COST_EUR = 500.0
DEFAULT_MAX_JOBS = 50


def build_execution_policy(plan: object) -> ExecutionPolicyResult:
    flags: List[str] = ["kill_switch_default_on", "no_persisted_policy_source_v1"]
    violations: List[str] = []

    cost = plan.cost_projection_result
    queue = plan.provider_execution_queue_result
    guard = plan.live_execution_guard_result

    total_cost = float(cost.total_estimated_cost_eur) if cost else 0.0
    jobs = int(queue.total_jobs) if queue else 0

    if total_cost > DEFAULT_MAX_COST_EUR:
        violations.append(f"estimated_cost_{total_cost}_exceeds_cap_{DEFAULT_MAX_COST_EUR}")
    if jobs > DEFAULT_MAX_JOBS:
        violations.append(f"job_count_{jobs}_exceeds_cap_{DEFAULT_MAX_JOBS}")

    mode: GlobalExecutionMode = "dry_run_only"
    if violations:
        mode = "emergency_stop"
        flags.append("auto_emergency_stop_due_to_violations")
    elif guard and guard.live_execution_status == "live_ready" and guard.live_execution_allowed:
        mode = "guarded_live"
        flags.append("guard_would_allow_guarded_live")

    return ExecutionPolicyResult(
        global_execution_mode=mode,
        kill_switch_active=True,
        max_estimated_cost_eur=DEFAULT_MAX_COST_EUR,
        max_jobs_per_run=DEFAULT_MAX_JOBS,
        policy_flags=list(dict.fromkeys(flags)),
        violations=list(dict.fromkeys(violations)),
    )
