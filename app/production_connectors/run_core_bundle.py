"""BA 10.4–10.10 — Run-Core-Schicht in einem Schritt (keine Persistenz)."""

from __future__ import annotations

from app.production_connectors.api_activation_control import build_api_activation_control
from app.production_connectors.asset_status_tracker import build_asset_status_tracker
from app.production_connectors.execution_policy import build_execution_policy
from app.production_connectors.job_runner_mock import simulate_provider_job_run
from app.production_connectors.live_execution_guard import evaluate_live_execution_guard
from app.production_connectors.production_run_summary import build_production_run_summary


def apply_run_core_suite(plan: object) -> object:
    """Reihenfolge: Guard → API-Aktivierung → Policy → Mock-Runner → Asset-Tracker → Summary."""
    p = plan.model_copy(update={"live_execution_guard_result": evaluate_live_execution_guard(plan)})
    p = p.model_copy(update={"api_activation_control_result": build_api_activation_control(p)})
    p = p.model_copy(update={"execution_policy_result": build_execution_policy(p)})
    mock = simulate_provider_job_run(p)
    p = p.model_copy(update={"provider_job_runner_mock_result": mock})
    p = p.model_copy(update={"asset_status_tracker_result": build_asset_status_tracker(mock)})
    p = p.model_copy(update={"production_run_summary_result": build_production_run_summary(p)})
    return p
