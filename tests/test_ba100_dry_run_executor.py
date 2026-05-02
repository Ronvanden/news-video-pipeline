"""BA 10.0 — Dry-run executor over bundle."""

from app.prompt_engine.provider_export_bundle import build_provider_export_bundle
from app.prompt_engine.provider_packaging import build_provider_packages
from app.prompt_engine.schema import ChapterOutlineItem, ProductionPromptPlan
from app.production_connectors.dry_run_executor import dry_run_provider_bundle


def _minimal_plan(**kwargs) -> ProductionPromptPlan:
    defaults = dict(
        template_type="true_crime",
        tone="ernst",
        hook="Ein Hook mit genug Text für Thumbnail.",
        chapter_outline=[ChapterOutlineItem(title="K1", summary="s")],
        scene_prompts=["Szene eins mit Inhalt."],
        voice_style="calm",
        thumbnail_angle="dramatic",
        warnings=[],
        video_template="true_crime",
        narrative_archetype_id="cold_case_arc",
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
        production_export_contract_result=None,
        provider_packaging_result=None,
        provider_export_bundle_result=None,
        package_validation_result=None,
    )
    defaults.update(kwargs)
    return ProductionPromptPlan(**defaults)


def test_suite_blocked_when_bundle_missing():
    p = _minimal_plan()
    suite = dry_run_provider_bundle(p)
    assert suite.suite_status == "blocked"
    assert suite.connector_results == []
    assert "missing_provider_export_bundle" in suite.blocking_reasons


def test_suite_blocked_when_bundle_status_blocked():
    from app.prompt_engine.schema import (
        ProductionExportContractResult,
        ProductionExportPayload,
    )

    contract = ProductionExportContractResult(
        export_contract_version="9.19-v1",
        handoff_package_id="h",
        export_ready=False,
        export_status="blocked",
        summary="",
        export_payload=ProductionExportPayload(),
        warnings=[],
        blocking_reasons=[],
        checked_sources=[],
    )
    base = _minimal_plan(production_export_contract_result=contract)
    pkg = build_provider_packages(base)
    bplan = base.model_copy(update={"provider_packaging_result": pkg})
    bundle = build_provider_export_bundle(bplan)
    plan = bplan.model_copy(update={"provider_export_bundle_result": bundle})
    suite = dry_run_provider_bundle(plan)
    assert suite.suite_status == "blocked"
    assert len(suite.connector_results) == 5
    assert all(r.execution_status == "blocked" for r in suite.connector_results)


def test_suite_dry_run_success_when_bundle_ready_payloads_valid():
    from app.prompt_engine.schema import (
        ProductionExportContractResult,
        ProductionExportPayload,
    )

    contract = ProductionExportContractResult(
        export_contract_version="9.19-v1",
        handoff_package_id="h",
        export_ready=True,
        export_status="ready",
        summary="",
        export_payload=ProductionExportPayload(),
        warnings=[],
        blocking_reasons=[],
        checked_sources=[],
    )
    base = _minimal_plan(production_export_contract_result=contract)
    pkg = build_provider_packages(base)
    bplan = base.model_copy(update={"provider_packaging_result": pkg})
    bundle = build_provider_export_bundle(bplan)
    plan = bplan.model_copy(update={"provider_export_bundle_result": bundle})
    suite = dry_run_provider_bundle(plan)
    assert suite.suite_status in ("dry_run_complete", "dry_run_partial")
    assert len(suite.connector_results) == 5
    assert any(r.normalized_request for r in suite.connector_results)
