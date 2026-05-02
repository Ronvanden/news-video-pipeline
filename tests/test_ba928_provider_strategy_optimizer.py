"""BA 9.28 — Provider Strategy Optimizer V1."""

from app.prompt_engine.provider_strategy_optimizer import optimize_provider_strategy
from app.prompt_engine.schema import (
    ChapterOutlineItem,
    CostProjectionResult,
    ProductionExportContractResult,
    ProductionExportPayload,
    ProductionPromptPlan,
    ProductionTimelineResult,
    ProviderExportBundleResult,
    ProviderExportProviders,
    ProviderPackage,
    ProviderPackagingResult,
)


def _ready_pkg(role: str, name: str) -> ProviderPackage:
    return ProviderPackage(provider_type=role, provider_name=name, package_status="ready", payload={})


def _plan_with_cost(*, total: float, per_min: float) -> ProductionPromptPlan:
    providers = ProviderExportProviders(
        image_package=_ready_pkg("image", "L"),
        video_package=_ready_pkg("video", "K"),
        voice_package=_ready_pkg("voice", "V"),
        thumbnail_package=_ready_pkg("thumbnail", "T"),
        render_package=_ready_pkg("render", "R"),
    )
    return ProductionPromptPlan(
        template_type="true_crime",
        tone="ernst",
        hook="Hook lang genug für Tests.",
        chapter_outline=[ChapterOutlineItem(title="K1", summary="a")],
        scene_prompts=["s1"],
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
        human_approval_state=None,
        production_handoff_result=None,
        production_export_contract_result=ProductionExportContractResult(
            export_contract_version="9.19-v1",
            handoff_package_id="h",
            export_ready=True,
            export_status="ready",
            summary="",
            export_payload=ProductionExportPayload(),
            warnings=[],
            blocking_reasons=[],
            checked_sources=[],
        ),
        provider_packaging_result=ProviderPackagingResult(
            packaging_status="ready",
            packages=[],
            checked_sources=[],
        ),
        provider_export_bundle_result=ProviderExportBundleResult(
            bundle_version="9.21-v1",
            bundle_status="ready",
            bundle_id="b",
            providers=providers,
            export_summary="",
            warnings=[],
        ),
        package_validation_result=None,
        production_timeline_result=ProductionTimelineResult(
            timeline_status="ready",
            total_estimated_duration_seconds=600,
            target_video_length_category="medium",
            scenes=[],
            warnings=[],
        ),
        cost_projection_result=CostProjectionResult(
            cost_status="estimated",
            total_estimated_cost_eur=total,
            estimated_cost_per_minute=per_min,
            provider_costs=[],
            assumptions=[],
            warnings=[],
        ),
        final_readiness_gate_result=None,
    )


def test_strategy_premium_when_high_cost_per_minute():
    p = _plan_with_cost(total=50.0, per_min=30.0)
    r = optimize_provider_strategy(p)
    assert r.cost_priority == "premium"
    assert r.optimization_status == "ready"


def test_strategy_low_cost_when_cheap():
    p = _plan_with_cost(total=10.0, per_min=5.0)
    r = optimize_provider_strategy(p)
    assert r.cost_priority == "low_cost"


def test_strategy_blocked_without_bundle():
    base = _plan_with_cost(total=10.0, per_min=5.0)
    p = base.model_copy(update={"provider_export_bundle_result": None})
    r = optimize_provider_strategy(p)
    assert r.optimization_status == "blocked"
