"""BA 9.24 — Cost Projection V2 (heuristisch)."""

from app.prompt_engine.cost_projection import build_cost_projection
from app.prompt_engine.schema import (
    ChapterOutlineItem,
    ProductionExportContractResult,
    ProductionExportPayload,
    ProductionPromptPlan,
    ProductionTimelineResult,
)
from app.prompt_engine.timeline_builder import build_production_timeline


def _contract() -> ProductionExportContractResult:
    return ProductionExportContractResult(
        export_contract_version="9.19-v1",
        handoff_package_id="hid",
        export_ready=True,
        export_status="ready",
        summary="ok",
        export_payload=ProductionExportPayload(),
        warnings=[],
        blocking_reasons=[],
        checked_sources=[],
    )


def _base_plan() -> ProductionPromptPlan:
    return ProductionPromptPlan(
        template_type="true_crime",
        tone="ernst",
        hook="Hook für Kostenmodell.",
        chapter_outline=[
            ChapterOutlineItem(title="K1", summary="a"),
            ChapterOutlineItem(title="K2", summary="b"),
        ],
        scene_prompts=["s1", "s2"],
        voice_style="calm",
        thumbnail_angle="thumb",
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


def test_cost_projection_has_provider_lines_and_total():
    p = _base_plan()
    p = p.model_copy(update={"production_timeline_result": build_production_timeline(p)})
    cost = build_cost_projection(p)
    assert cost.cost_status == "estimated"
    assert cost.total_estimated_cost_eur > 0
    names = {x.provider_name for x in cost.provider_costs}
    assert "Leonardo (image)" in names
    assert "Kling (video)" in names
    assert "Voice (OpenAI/ElevenLabs stub)" in names
    assert "Thumbnail" in names
    assert "Render pipeline" in names
    assert cost.estimated_cost_per_minute >= 0


def test_cost_partial_when_timeline_partial():
    p = _base_plan().model_copy(
        update={
            "scene_prompts": ["s1"],
            "production_timeline_result": build_production_timeline(
                _base_plan().model_copy(update={"scene_prompts": ["s1"]})
            ),
        }
    )
    cost = build_cost_projection(p)
    assert cost.cost_status == "partial"


def test_cost_insufficient_when_timeline_blocked():
    p = _base_plan().model_copy(
        update={
            "production_timeline_result": ProductionTimelineResult(
                timeline_status="blocked",
                total_estimated_duration_seconds=0,
                target_video_length_category="short",
                scenes=[],
                warnings=["x"],
            ),
        }
    )
    cost = build_cost_projection(p)
    assert cost.cost_status == "insufficient_data"
    assert cost.provider_costs == []
