"""BA 10.2 — Provider execution queue."""

from app.prompt_engine.provider_export_bundle import build_provider_export_bundle
from app.prompt_engine.provider_packaging import build_provider_packages
from app.prompt_engine.schema import (
    ChapterOutlineItem,
    ProductionExportContractResult,
    ProductionExportPayload,
    ProductionPromptPlan,
)
from app.production_connectors.execution_queue import build_provider_execution_queue


def _plan_bundle(*, export_ready: bool):
    contract = ProductionExportContractResult(
        export_contract_version="9.19-v1",
        handoff_package_id="h",
        export_ready=export_ready,
        export_status="ready" if export_ready else "blocked",
        summary="",
        export_payload=ProductionExportPayload(),
        warnings=[],
        blocking_reasons=[],
        checked_sources=[],
    )
    base = ProductionPromptPlan(
        template_type="true_crime",
        tone="ernst",
        hook="Ausreichend langer Hook für Thumbnail.",
        chapter_outline=[ChapterOutlineItem(title="K1", summary="s")],
        scene_prompts=["Szene mit Substanz."],
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
        production_export_contract_result=contract,
        provider_packaging_result=None,
        provider_export_bundle_result=None,
        package_validation_result=None,
    )
    pkg = build_provider_packages(base)
    b = build_provider_export_bundle(base.model_copy(update={"provider_packaging_result": pkg}))
    return base.model_copy(update={"provider_packaging_result": pkg, "provider_export_bundle_result": b})


def test_queue_blocked_when_bundle_blocked():
    p = _plan_bundle(export_ready=False)
    q = build_provider_execution_queue(p)
    assert q.queue_status == "blocked"
    assert q.total_jobs == 5
    assert all(j.queue_status == "blocked" for j in q.jobs)


def test_queue_order_thumbnail_first_render_last():
    p = _plan_bundle(export_ready=True)
    q = build_provider_execution_queue(p)
    by_type = {j.provider_type: j for j in q.jobs}
    assert by_type["thumbnail"].dependency_order < by_type["image"].dependency_order
    assert by_type["image"].dependency_order == by_type["voice"].dependency_order
    assert by_type["render"].dependency_order > by_type["video"].dependency_order
