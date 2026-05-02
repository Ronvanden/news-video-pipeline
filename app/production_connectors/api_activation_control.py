"""BA 10.5 — API-Aktivierung (theoretisch, ohne echte Keys)."""

from __future__ import annotations

from typing import List

from app.production_connectors.schema import (
    APIActivationControlResult,
    APIActivationMode,
    ProviderActivationMatrix,
)
def build_api_activation_control(plan: object) -> APIActivationControlResult:
    warns: List[str] = []
    g = plan.live_execution_guard_result
    matrix = ProviderActivationMatrix()

    if g is None:
        return APIActivationControlResult(
            activation_mode="dry_run",
            activation_allowed=False,
            activation_reason="live_execution_guard_result_missing",
            provider_activation_matrix=matrix,
            warnings=["guard_not_evaluated"],
        )

    if g.live_execution_status == "blocked":
        # V1-Standard: immer dry_run als Modus; Live bleibt aus, Blocker in warnings.
        return APIActivationControlResult(
            activation_mode="dry_run",
            activation_allowed=False,
            activation_reason="live_execution_blocked_dry_run_only",
            provider_activation_matrix=matrix,
            warnings=list(g.blockers) + list(g.warnings),
        )

    if g.live_execution_status == "live_ready" and g.live_execution_allowed:
        matrix = ProviderActivationMatrix(
            leonardo=True,
            kling=True,
            voice=True,
            thumbnail=True,
            render=True,
        )
        return APIActivationControlResult(
            activation_mode="restricted_live",
            activation_allowed=True,
            activation_reason="guard_green_and_kill_switch_off_theoretical_only",
            provider_activation_matrix=matrix,
            warnings=warns + ["V1: restricted_live ist Planungsmodus ohne HTTP."],
        )

    if g.live_execution_status == "policy_review":
        warns.append("policy_review_path_activation_stays_dry_run")
        return APIActivationControlResult(
            activation_mode="dry_run",
            activation_allowed=False,
            activation_reason="policy_review_requires_human_followup",
            provider_activation_matrix=matrix,
            warnings=warns + g.warnings,
        )

    return APIActivationControlResult(
        activation_mode="dry_run",
        activation_allowed=False,
        activation_reason="default_dry_run_only_guard_not_live_ready",
        provider_activation_matrix=matrix,
        warnings=warns + g.warnings,
    )
