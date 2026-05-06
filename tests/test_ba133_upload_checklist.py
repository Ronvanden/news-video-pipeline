"""BA 13.3 — Upload Checklist."""

from app.prompt_engine.pipeline import build_production_prompt_plan
from app.prompt_engine.schema import PromptPlanRequest
from app.publishing.upload_checklist import build_upload_checklist


def test_upload_checklist_complete_for_default_package():
    plan = build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord", title="", source_summary=""))
    checklist = plan.upload_checklist_result
    assert checklist is not None
    assert checklist.checklist_status == "complete"
    assert "metadata_complete" in checklist.completed_items
    assert "thumbnail_ready" in checklist.completed_items
    assert not checklist.blockers


def test_upload_checklist_detects_missing_items():
    plan = build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord", title="", source_summary=""))
    broken = plan.model_copy(update={"thumbnail_variant_pack_result": None, "downloadable_production_bundle_result": None})
    checklist = build_upload_checklist(broken)
    assert checklist.checklist_status == "blocked"
    assert "thumbnail_variants_missing" in checklist.blockers
    assert "download_bundle_missing_or_blocked" in checklist.blockers
