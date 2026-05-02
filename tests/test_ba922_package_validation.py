"""BA 9.22 — Production Package Validation V1."""

from fastapi.testclient import TestClient

from app.main import app
from app.prompt_engine.package_validation import validate_provider_export_bundle
from app.prompt_engine.provider_export_bundle import build_provider_export_bundle
from app.prompt_engine.provider_packaging import build_provider_packages
from app.prompt_engine.schema import (
    ChapterOutlineItem,
    ProductionExportContractResult,
    ProductionExportPayload,
    ProductionPromptPlan,
)


def _contract(*, export_ready: bool = True, export_status: str = "ready") -> ProductionExportContractResult:
    return ProductionExportContractResult(
        export_contract_version="9.19-v1",
        handoff_package_id="hid",
        export_ready=export_ready,
        export_status=export_status,  # type: ignore[arg-type]
        summary="ok",
        export_payload=ProductionExportPayload(),
        warnings=[],
        blocking_reasons=[],
        checked_sources=[],
    )


def _plan(**kwargs) -> ProductionPromptPlan:
    defaults = dict(
        template_type="true_crime",
        tone="ernst",
        hook="Ein ausreichend langer Hook für Package-Validation.",
        chapter_outline=[
            ChapterOutlineItem(title="K1", summary="a"),
            ChapterOutlineItem(title="K2", summary="b"),
        ],
        scene_prompts=["s1", "s2"],
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
        production_export_contract_result=_contract(),
        provider_packaging_result=None,
        provider_export_bundle_result=None,
        package_validation_result=None,
    )
    defaults.update(kwargs)
    return ProductionPromptPlan(**defaults)


def _bundle_plan(base: ProductionPromptPlan) -> ProductionPromptPlan:
    pkg = build_provider_packages(base)
    b = build_provider_export_bundle(base.model_copy(update={"provider_packaging_result": pkg}))
    return base.model_copy(
        update={
            "provider_packaging_result": pkg,
            "provider_export_bundle_result": b,
        }
    )


def test_validation_pass_when_bundle_ready_and_consistent():
    p = _bundle_plan(_plan())
    v = validate_provider_export_bundle(p)
    assert v.validation_status == "pass"
    assert v.production_safety == "safe"
    assert not v.missing_components


def test_validation_detects_missing_components_when_partial():
    base = _plan(scene_prompts=[], production_export_contract_result=_contract())
    p = _bundle_plan(base)
    v = validate_provider_export_bundle(p)
    assert v.validation_status == "fail"
    assert v.production_safety == "unsafe"
    assert v.missing_components


def test_validation_blocked_bundle():
    base = _plan(production_export_contract_result=_contract(export_ready=False, export_status="blocked"))
    p = _bundle_plan(base)
    v = validate_provider_export_bundle(p)
    assert v.validation_status == "fail"
    assert "export_bundle_blocked" in v.missing_components


def test_validation_warning_when_bundle_partial_but_slots_ready():
    base = _plan(production_export_contract_result=_contract(export_ready=False, export_status="needs_review"))
    p = _bundle_plan(base)
    v = validate_provider_export_bundle(p)
    assert v.validation_status == "warning"
    assert v.production_safety == "review"
    assert not v.missing_components


def test_validation_no_bundle():
    p = _plan()
    v = validate_provider_export_bundle(p)
    assert v.validation_status == "fail"
    assert "provider_export_bundle" in v.missing_components


def test_prompt_plan_api_has_packaging_fields():
    client = TestClient(app)
    r = client.post("/story-engine/prompt-plan", json={"topic": "Polizei und Mord"})
    assert r.status_code == 200
    body = r.json()
    assert "provider_packaging_result" in body
    assert "provider_export_bundle_result" in body
    assert "package_validation_result" in body
    assert body["provider_export_bundle_result"]["bundle_version"] == "9.21-v1"
    assert "production_timeline_result" in body
    assert "cost_projection_result" in body
    assert "final_readiness_gate_result" in body
    assert "template_performance_comparison_result" in body
    assert "template_recommendation_result" in body
    assert "provider_strategy_optimizer_result" in body
    assert "production_os_dashboard_result" in body
    assert "master_orchestration_result" in body
    assert "production_connector_suite_result" in body
    assert "connector_auth_contracts_result" in body
    assert "provider_execution_queue_result" in body
    assert "live_provider_safety_result" in body
    assert "runtime_secret_check_result" in body
    assert "leonardo_live_result" in body
    assert "voice_live_result" in body
    assert "asset_persistence_result" in body
    assert "provider_error_recovery_result" in body
    assert "master_asset_manifest_result" in body
    assert "multi_asset_assembly_result" in body
    assert "final_timeline_result" in body
    assert "voice_scene_alignment_result" in body
    assert "render_instruction_package_result" in body
    assert "downloadable_production_bundle_result" in body
    assert "human_final_review_package_result" in body
    assert "metadata_master_package_result" in body
    assert "metadata_optimizer_result" in body
    assert "thumbnail_variant_pack_result" in body
    assert "upload_checklist_result" in body
    assert "schedule_plan_result" in body
    assert "publishing_readiness_gate_result" in body
    assert "founder_publishing_summary_result" in body
    assert "kpi_ingest_contract_result" in body
    assert "kpi_normalization_result" in body
    assert "hook_performance_result" in body
    assert "template_evolution_result" in body
    assert "cost_revenue_analysis_result" in body
    assert "auto_recommendation_upgrade_result" in body
    assert "founder_growth_intelligence_result" in body
    assert "master_feedback_orchestrator_result" in body
    assert "live_execution_guard_result" in body
    assert "api_activation_control_result" in body
    assert "execution_policy_result" in body
    assert "provider_job_runner_mock_result" in body
    assert "asset_status_tracker_result" in body
    assert "production_run_summary_result" in body
