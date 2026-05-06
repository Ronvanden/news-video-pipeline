"""BA 11.0 — Live-Provider-Safety vor optionalem HTTP."""

from __future__ import annotations

from typing import List

from app.production_connectors.schema import LiveProviderMode, LiveProviderSafetyResult


def evaluate_live_provider_safety(plan: object) -> LiveProviderSafetyResult:
    required_conditions = [
        "execution_policy_ok",
        "kill_switch_disabled_for_live",
        "api_activation_allows_provider",
        "auth_contracts_present",
        "human_approval_approved",
        "final_readiness_ready_for_production",
        "live_execution_guard_not_blocked",
        "allow_live_provider_execution_flag",
        "provider_payload_min_requirements",
    ]
    violations: List[str] = []
    warnings: List[str] = []
    blocked_providers: List[str] = []
    approved_providers: List[str] = []

    pol = plan.execution_policy_result
    act = plan.api_activation_control_result
    leg = plan.live_execution_guard_result
    ha = plan.human_approval_state
    fr = plan.final_readiness_gate_result
    bundle = plan.provider_export_bundle_result
    allow_live = bool(getattr(plan, "allow_live_provider_execution", False))

    img_name = bundle.providers.image_package.provider_name if bundle else "Leonardo"
    voice_name = bundle.providers.voice_package.provider_name if bundle else "OpenAI / ElevenLabs (stub)"

    if pol is None:
        violations.append("execution_policy_result_missing")
    else:
        violations.extend(list(pol.violations or []))
        if pol.global_execution_mode == "emergency_stop":
            violations.append("execution_policy_emergency_stop")

    kill_on = bool(pol.kill_switch_active) if pol else True

    if act is None:
        violations.append("api_activation_control_result_missing")
    elif act.activation_mode == "disabled":
        violations.append("api_activation_disabled")

    if leg is None:
        warnings.append("live_execution_guard_missing")
    elif leg.live_execution_status == "blocked":
        violations.append("live_execution_guard_blocked")

    if ha is None:
        violations.append("human_approval_state_missing")
    elif ha.status != "approved":
        violations.append(f"human_approval_not_approved:{ha.status}")

    if fr is None:
        violations.append("final_readiness_gate_missing")
    elif fr.readiness_decision != "ready_for_production":
        violations.append(f"final_readiness_not_production:{fr.readiness_decision}")

    if not allow_live:
        warnings.append("allow_live_provider_execution_false_default")

    if kill_on:
        warnings.append("kill_switch_active_blocks_live_providers")

    candidates: List[str] = []
    if act and act.activation_mode == "restricted_live":
        if act.provider_activation_matrix.leonardo:
            candidates.append(img_name)
        else:
            blocked_providers.append(img_name)
        if act.provider_activation_matrix.voice:
            candidates.append(voice_name)
        else:
            blocked_providers.append(voice_name)
    elif act and act.activation_mode == "dry_run":
        warnings.append("api_activation_dry_run_no_live")
        blocked_providers.extend([img_name, voice_name])

    blocked_providers = list(dict.fromkeys(blocked_providers))

    mode: LiveProviderMode = "dry_run_only"
    live_allowed = False

    if violations:
        mode = "blocked"
        live_allowed = False
        approved_providers = []
        blocked_providers = list(dict.fromkeys(blocked_providers + candidates))
    elif act and act.activation_mode == "dry_run":
        mode = "dry_run_only"
        live_allowed = False
        approved_providers = []
    elif act and act.activation_mode == "restricted_live":
        if not candidates:
            mode = "provider_restricted"
            live_allowed = False
            approved_providers = []
        elif kill_on or not allow_live:
            mode = "dry_run_only"
            live_allowed = False
            approved_providers = []
            warnings.append("restricted_live_gates_ok_but_kill_switch_or_live_flag_off")
        else:
            mode = "guarded_live_ready"
            live_allowed = True
            approved_providers = list(dict.fromkeys(candidates))
    else:
        mode = "dry_run_only"
        live_allowed = False
        approved_providers = []

    return LiveProviderSafetyResult(
        live_provider_mode=mode,
        live_provider_allowed=live_allowed,
        approved_providers=approved_providers,
        blocked_providers=blocked_providers,
        required_conditions=required_conditions,
        violations=list(dict.fromkeys(violations)),
        warnings=list(dict.fromkeys(warnings)),
    )
