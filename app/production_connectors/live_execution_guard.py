"""BA 10.4 — Live-Execution-Gate (Default: Dry-Run only)."""

from __future__ import annotations

from typing import List

from app.production_connectors.schema import LiveExecutionGuardResult, LiveExecutionGuardStatus

DEFAULT_KILL_SWITCH_ACTIVE = True


def evaluate_live_execution_guard(plan: object) -> LiveExecutionGuardResult:
    blockers: List[str] = []
    warnings: List[str] = []
    required: List[str] = [
        "human_approval_approved",
        "final_readiness_ready_for_production",
        "export_contract_export_ready",
        "package_validation_pass",
        "connector_suite_dry_run_complete",
        "execution_queue_ready",
        "cost_projection_estimated",
        "auth_contracts_no_missing_api_keys",
        "kill_switch_inactive_for_live",
    ]

    ha = plan.human_approval_state
    fr = plan.final_readiness_gate_result
    ex = plan.production_export_contract_result
    val = plan.package_validation_result
    suite = plan.production_connector_suite_result
    queue = plan.provider_execution_queue_result
    auth = plan.connector_auth_contracts_result
    cost = plan.cost_projection_result

    if ha is None:
        blockers.append("human_approval_state_missing")
    elif ha.status != "approved":
        warnings.append(f"human_approval_status:{ha.status}")

    if fr is None:
        blockers.append("final_readiness_gate_result_missing")
    elif fr.readiness_decision == "not_ready":
        blockers.append("final_readiness_not_ready")
    elif fr.readiness_decision == "ready_for_review":
        warnings.append("final_readiness_pending_review")

    if ex is None:
        blockers.append("export_contract_missing")
    elif not ex.export_ready:
        blockers.append("export_contract_not_export_ready")

    if val is None:
        blockers.append("package_validation_missing")
    elif val.validation_status == "fail":
        blockers.append("package_validation_failed")
    elif val.validation_status == "warning":
        warnings.append("package_validation_warning")

    if suite is None:
        blockers.append("connector_suite_missing")
    elif suite.suite_status == "blocked":
        blockers.append("connector_suite_blocked")
    elif suite.suite_status != "dry_run_complete":
        warnings.append(f"connector_suite_status:{suite.suite_status}")

    if queue is None:
        blockers.append("execution_queue_missing")
    elif queue.queue_status == "blocked":
        blockers.append("execution_queue_blocked")
    elif queue.queue_status != "ready":
        warnings.append(f"execution_queue_status:{queue.queue_status}")

    if cost is None:
        blockers.append("cost_projection_missing")
    elif cost.cost_status == "insufficient_data":
        blockers.append("cost_projection_insufficient_data")
    elif cost.cost_status == "partial":
        warnings.append("cost_projection_partial")

    if auth is None:
        warnings.append("auth_contracts_missing")
    else:
        for c in auth.contracts:
            if c.auth_status == "auth_missing" and c.required_env_vars:
                warnings.append(f"auth_missing:{c.connector_name}")

    if DEFAULT_KILL_SWITCH_ACTIVE:
        warnings.append("kill_switch_active_default_true")

    status: LiveExecutionGuardStatus
    allowed = False

    if blockers:
        status = "blocked"
    elif fr and fr.readiness_decision == "ready_for_review":
        status = "policy_review"
    elif val and val.validation_status == "warning" and not blockers:
        status = "policy_review"
    elif (
        not blockers
        and ha
        and ha.status == "approved"
        and fr
        and fr.readiness_decision == "ready_for_production"
        and ex
        and ex.export_ready
        and val
        and val.validation_status == "pass"
        and suite
        and suite.suite_status == "dry_run_complete"
        and queue
        and queue.queue_status == "ready"
        and cost
        and cost.cost_status == "estimated"
        and not DEFAULT_KILL_SWITCH_ACTIVE
        and not any(w.startswith("auth_missing:") for w in warnings)
    ):
        status = "live_ready"
        allowed = True
    else:
        status = "dry_run_only"

    if DEFAULT_KILL_SWITCH_ACTIVE and status == "live_ready":
        status = "dry_run_only"
        allowed = False
        warnings.append("live_downgraded_to_dry_run_kill_switch")

    return LiveExecutionGuardResult(
        live_execution_status=status,
        live_execution_allowed=allowed,
        blockers=list(dict.fromkeys(blockers)),
        warnings=list(dict.fromkeys(warnings)),
        required_conditions=required,
    )
