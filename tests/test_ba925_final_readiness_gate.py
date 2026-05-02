"""BA 9.25 — Final Production Readiness Gate V1."""

from app.prompt_engine.cost_projection import build_cost_projection
from app.prompt_engine.final_readiness_gate import evaluate_final_production_readiness
from app.prompt_engine.human_approval import build_human_approval_state
from app.prompt_engine.package_validation import validate_provider_export_bundle
from app.prompt_engine.pipeline import build_production_prompt_plan
from app.prompt_engine.production_export_contract import build_production_export_contract
from app.prompt_engine.production_handoff import build_production_handoff
from app.prompt_engine.provider_export_bundle import build_provider_export_bundle
from app.prompt_engine.provider_packaging import build_provider_packages
from app.prompt_engine.schema import (
    ChapterOutlineItem,
    CostProjectionResult,
    HumanApprovalState,
    PackageValidationResult,
    ProductionExportContractResult,
    ProductionExportPayload,
    ProductionPromptPlan,
    ProviderCostEstimate,
    ProviderExportBundleResult,
    ProviderExportProviders,
    ProviderPackage,
    PromptPlanRequest,
    PromptPlanReviewGateResult,
)
from app.prompt_engine.timeline_builder import build_production_timeline


def _rerun_handoff_through_readiness(plan):
    """Spiegelt Pipeline-Schritte ab Human-Approval (Testszenario)."""
    ho = build_production_handoff(plan)
    p = plan.model_copy(update={"production_handoff_result": ho})
    co = build_production_export_contract(p)
    p = p.model_copy(update={"production_export_contract_result": co})
    pkg = build_provider_packages(p)
    p = p.model_copy(update={"provider_packaging_result": pkg})
    bu = build_provider_export_bundle(p)
    p = p.model_copy(update={"provider_export_bundle_result": bu})
    val = validate_provider_export_bundle(p)
    p = p.model_copy(update={"package_validation_result": val})
    tl = build_production_timeline(p)
    p = p.model_copy(update={"production_timeline_result": tl})
    cost = build_cost_projection(p)
    p = p.model_copy(update={"cost_projection_result": cost})
    gate = evaluate_final_production_readiness(p)
    return p.model_copy(update={"final_readiness_gate_result": gate})


def _pkg_ready() -> ProviderExportProviders:
    stub = ProviderPackage(
        provider_type="image",
        provider_name="Leonardo",
        package_status="ready",
        payload={},
        warnings=[],
    )
    return ProviderExportProviders(
        image_package=stub.model_copy(update={"provider_type": "image"}),
        video_package=stub.model_copy(update={"provider_type": "video", "provider_name": "Kling"}),
        voice_package=stub.model_copy(update={"provider_type": "voice", "provider_name": "Voice"}),
        thumbnail_package=stub.model_copy(
            update={"provider_type": "thumbnail", "provider_name": "Thumb"}
        ),
        render_package=stub.model_copy(update={"provider_type": "render", "provider_name": "Render"}),
    )


def _green_plan() -> ProductionPromptPlan:
    return ProductionPromptPlan(
        template_type="true_crime",
        tone="ernst",
        hook="Solider Hook für Readiness-Gate-Tests.",
        chapter_outline=[ChapterOutlineItem(title="K1", summary="a")],
        scene_prompts=["Szene eins mit Substanz."],
        voice_style="calm",
        thumbnail_angle="dramatic",
        warnings=[],
        video_template="true_crime",
        narrative_archetype_id="arc",
        hook_type="x",
        hook_score=7.0,
        quality_result=None,
        narrative_score_result=None,
        performance_record=None,
        review_gate_result=None,
        repair_suggestions_result=None,
        repair_preview_result=None,
        human_approval_state=HumanApprovalState(
            status="approved",
            recommended_action="approve",
            approval_required=True,
            reasons=[],
            checklist=[],
            approved_by="test",
            approved_at="2026-01-01T00:00:00Z",
            rejected_reason=None,
        ),
        production_handoff_result=None,
        production_export_contract_result=ProductionExportContractResult(
            export_contract_version="9.19-v1",
            handoff_package_id="hid",
            export_ready=True,
            export_status="ready",
            summary="ok",
            export_payload=ProductionExportPayload(),
            warnings=[],
            blocking_reasons=[],
            checked_sources=[],
        ),
        provider_packaging_result=None,
        provider_export_bundle_result=ProviderExportBundleResult(
            bundle_version="9.21-v1",
            bundle_status="ready",
            bundle_id="bid",
            providers=_pkg_ready(),
            export_summary="ok",
            warnings=[],
        ),
        package_validation_result=PackageValidationResult(
            validation_status="pass",
            production_safety="safe",
            missing_components=[],
            warnings=[],
            recommendations=[],
        ),
    )


def test_validation_fail_not_ready():
    p = _green_plan().model_copy(
        update={
            "package_validation_result": PackageValidationResult(
                validation_status="fail",
                production_safety="unsafe",
                missing_components=["x"],
                warnings=[],
                recommendations=[],
            ),
        }
    )
    p = p.model_copy(update={"production_timeline_result": build_production_timeline(p)})
    p = p.model_copy(
        update={
            "cost_projection_result": CostProjectionResult(
                cost_status="estimated",
                total_estimated_cost_eur=10.0,
                estimated_cost_per_minute=2.0,
                provider_costs=[
                    ProviderCostEstimate(provider_name="Leonardo (image)", estimated_units=1, estimated_cost_eur=1.0)
                ],
                assumptions=[],
                warnings=[],
            ),
        }
    )
    r = evaluate_final_production_readiness(p)
    assert r.readiness_decision == "not_ready"
    assert r.production_blockers


def test_full_manual_plan_ready_for_production():
    p = _green_plan()
    p = p.model_copy(update={"production_timeline_result": build_production_timeline(p)})
    p = p.model_copy(
        update={
            "cost_projection_result": CostProjectionResult(
                cost_status="estimated",
                total_estimated_cost_eur=22.0,
                estimated_cost_per_minute=5.0,
                provider_costs=[
                    ProviderCostEstimate(provider_name="Leonardo (image)", estimated_units=2, estimated_cost_eur=1.0)
                ],
                assumptions=[],
                warnings=[],
            ),
        }
    )
    r = evaluate_final_production_readiness(p)
    assert r.readiness_decision == "ready_for_production"
    assert r.readiness_score >= 88


def test_pipeline_with_go_gate_recomputed_downstream_ready_for_review():
    base = build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord", title="", source_summary=""))
    go_gate = PromptPlanReviewGateResult(decision="go", confidence=92, reasons=[], required_actions=[], checked_signals=[])
    patched = base.model_copy(update={"review_gate_result": go_gate})
    patched = patched.model_copy(update={"human_approval_state": build_human_approval_state(patched)})
    plan = _rerun_handoff_through_readiness(patched)
    assert plan.package_validation_result.validation_status == "warning"
    assert plan.final_readiness_gate_result.readiness_decision == "ready_for_review"
