"""BA 11.5 — Provider Error Recovery."""

from app.production_connectors.error_recovery import build_provider_error_recovery
from app.production_connectors.schema import LiveConnectorExecutionResult
from app.prompt_engine.schema import ChapterOutlineItem, ProductionPromptPlan


def _minimal_plan(**kwargs):
    defaults = dict(
        template_type="true_crime",
        tone="ernst",
        hook="Ein ausreichend langer Hook für Tests.",
        chapter_outline=[ChapterOutlineItem(title="K1", summary="a")],
        scene_prompts=["s1"],
        voice_style="calm",
        thumbnail_angle="dramatic",
        warnings=[],
    )
    defaults.update(kwargs)
    return ProductionPromptPlan(**defaults)


def test_payload_error_blocked_recovery():
    plan = _minimal_plan(
        leonardo_live_result=LiveConnectorExecutionResult(
            provider_name="Leonardo",
            provider_type="image",
            execution_mode="blocked",
            blocking_reasons=["leonardo_payload_invalid"],
        ),
        voice_live_result=None,
    )
    r = build_provider_error_recovery(plan)
    assert r.recovery_status == "blocked"
    assert r.error_classification == "payload"


def test_timeout_retry_recovery():
    plan = _minimal_plan(
        leonardo_live_result=LiveConnectorExecutionResult(
            provider_name="Leonardo",
            provider_type="image",
            execution_mode="live_attempt",
            http_attempted=True,
            warnings=["leonardo_url_error:timed out"],
        ),
    )
    r = build_provider_error_recovery(plan)
    assert r.recovery_status == "retry_available"
    assert r.retry_recommended is True
    assert r.error_classification == "timeout"


def test_all_dry_run_no_action():
    plan = _minimal_plan(
        leonardo_live_result=LiveConnectorExecutionResult(
            provider_name="Leonardo",
            provider_type="image",
            execution_mode="dry_run",
        ),
        voice_live_result=LiveConnectorExecutionResult(
            provider_name="Voice",
            provider_type="voice",
            execution_mode="dry_run",
        ),
    )
    r = build_provider_error_recovery(plan)
    assert r.recovery_status == "no_action"
