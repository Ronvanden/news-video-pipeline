"""BA 13.4 — Schedule Plan."""

from __future__ import annotations

from app.publishing.schema import SchedulePlanResult


def build_schedule_plan(plan: object) -> SchedulePlanResult:
    checklist = getattr(plan, "upload_checklist_result", None)
    readiness_hint = getattr(plan, "human_final_review_package_result", None)

    windows = [
        "Europe/Berlin weekday 18:00-20:00",
        "Europe/Berlin Sunday 10:00-12:00",
    ]
    notes = ["Timezone default: Europe/Berlin", "V1 heuristic only; no live channel analytics."]
    strategic = ["Publish after final human review.", "Use scheduled mode for sensitive or investigative topics."]

    if checklist is None or checklist.checklist_status == "blocked":
        mode = "hold"
        strategic.append("Hold until upload checklist blockers are resolved.")
    elif readiness_hint and readiness_hint.release_recommendation == "approve_for_render":
        mode = "scheduled"
    else:
        mode = "scheduled"
        strategic.append("Schedule after revision items are acknowledged.")

    return SchedulePlanResult(
        suggested_publish_mode=mode,
        recommended_publish_windows=windows if mode != "hold" else [],
        timezone_notes=notes,
        strategic_notes=strategic,
    )
