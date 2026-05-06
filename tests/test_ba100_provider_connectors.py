"""BA 10.0 — Provider stub connectors."""

from app.production_connectors.kling_connector import KlingProductionConnector
from app.production_connectors.render_connector import RenderProductionConnector
from app.production_connectors.thumbnail_connector import ThumbnailProductionConnector
from app.production_connectors.voice_connector import VoiceProductionConnector


def test_kling_invalid_then_valid():
    k = KlingProductionConnector()
    bad = k.dry_run({})
    assert bad.execution_status == "invalid_payload"
    good = k.dry_run(
        {
            "motion_prompts": [
                {"index": 0, "chapter_title": "A", "motion_prompt": "move camera slowly"},
            ]
        }
    )
    assert good.execution_status == "dry_run_success"


def test_voice_thumbnail_render():
    v = VoiceProductionConnector()
    assert v.dry_run({"voice_style": "calm", "chapter_voice_blocks": [{"chapter_title": "K", "summary": "s"}]}).execution_status == "dry_run_success"

    t = ThumbnailProductionConnector()
    assert (
        t.dry_run({"hook": "Hallo Welt", "thumbnail_angle": "dramatic", "composite_prompt": "x"}).execution_status
        == "dry_run_success"
    )

    r = RenderProductionConnector()
    assert (
        r.dry_run(
            {"timeline_skeleton": [{"order": 0, "chapter_title": "K", "scene_prompt": "s"}]}
        ).execution_status
        == "dry_run_success"
    )
