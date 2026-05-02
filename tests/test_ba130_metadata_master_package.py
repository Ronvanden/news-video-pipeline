"""BA 13.0 — Metadata Master Package."""

from app.prompt_engine.pipeline import build_production_prompt_plan
from app.prompt_engine.schema import PromptPlanRequest
from app.publishing.metadata_master_package import build_metadata_master_package


def test_metadata_package_present_with_youtube_default():
    plan = build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord", title="", source_summary=""))
    meta = plan.metadata_master_package_result
    assert meta is not None
    assert meta.platform_target == "youtube"
    assert meta.canonical_title
    assert meta.canonical_description
    assert meta.canonical_tags
    assert meta.metadata_status in ("complete", "partial")


def test_metadata_package_blocks_without_title_and_tags():
    plan = build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord", title="", source_summary=""))
    stripped = plan.model_copy(update={"hook": "", "template_type": "", "video_template": "", "narrative_archetype_id": ""})
    meta = build_metadata_master_package(stripped)
    assert meta.metadata_status in ("partial", "blocked")
    assert meta.compliance_warnings
