"""BA 9.21 — Multi-Provider Export Bundle V1."""

from app.prompt_engine.provider_export_bundle import BUNDLE_VERSION, build_provider_export_bundle
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
        hook="Ein ausreichend langer Hook für Export-Bundle.",
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
        production_export_contract_result=_contract(),
        provider_packaging_result=None,
        provider_export_bundle_result=None,
        package_validation_result=None,
    )
    defaults.update(kwargs)
    return ProductionPromptPlan(**defaults)


def test_bundle_version_and_providers_structure():
    p = _plan()
    p2 = p.model_copy(update={"provider_packaging_result": build_provider_packages(p)})
    b = build_provider_export_bundle(p2)
    assert b.bundle_version == BUNDLE_VERSION == "9.21-v1"
    assert b.bundle_id.startswith("bundle_true_crime_")
    assert b.providers.image_package.provider_type == "image"
    assert b.providers.video_package.provider_type == "video"


def test_blocked_contract_bundle_blocked():
    p = _plan(
        production_export_contract_result=_contract(export_ready=False, export_status="blocked"),
    )
    p2 = p.model_copy(update={"provider_packaging_result": build_provider_packages(p)})
    b = build_provider_export_bundle(p2)
    assert b.bundle_status == "blocked"
