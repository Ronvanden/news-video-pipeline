"""BA 13.4 — Schedule Plan."""

from app.prompt_engine.pipeline import build_production_prompt_plan
from app.prompt_engine.schema import PromptPlanRequest
from app.publishing.schedule_plan import build_schedule_plan


def test_schedule_plan_has_publish_windows_when_checklist_not_blocked():
    plan = build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord", title="", source_summary=""))
    schedule = plan.schedule_plan_result
    assert schedule is not None
    assert schedule.suggested_publish_mode in ("scheduled", "immediate")
    assert schedule.recommended_publish_windows
    assert schedule.timezone_notes


def test_schedule_plan_holds_on_blocked_checklist():
    plan = build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord", title="", source_summary=""))
    blocked_checklist = plan.upload_checklist_result.model_copy(update={"checklist_status": "blocked"})
    schedule = build_schedule_plan(plan.model_copy(update={"upload_checklist_result": blocked_checklist}))
    assert schedule.suggested_publish_mode == "hold"
    assert not schedule.recommended_publish_windows
