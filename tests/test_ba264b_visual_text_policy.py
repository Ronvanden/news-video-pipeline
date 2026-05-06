"""BA 26.4b — Visual Provider Router, No-Text Guard, Overlay-Zerlegung."""

from __future__ import annotations

from app.models import (
    SceneBlueprintContract,
    SceneBlueprintPlanResponse,
    SceneBlueprintPromptPack,
)
from app.visual_plan.provider_formatter import build_all_provider_prompts
from app.visual_plan.visual_no_text import append_no_text_guard, partition_visual_overlay_text
from app.visual_plan.visual_provider_router import route_visual_provider


def test_partition_checklist_moves_overlay_items():
    raw = (
        "Eine dunkle Checkliste mit drei Punkten: Akte prüfen, Zeugen finden, Wahrheit suchen"
    )
    vis, overlay, ts = partition_visual_overlay_text(raw)
    assert ts is True
    assert "Akte prüfen" in overlay
    assert "Zeugen finden" in overlay
    assert "Wahrheit suchen" in overlay
    assert "Akte prüfen" not in vis
    assert "Checkboxen" in vis or "Text-Overlays" in vis


def test_route_text_sensitive_to_openai_images():
    r = route_visual_provider("cinematic_broll", text_sensitive=True)
    assert r["provider"] == "openai_images"
    assert r["image_provider"] == ""


def test_route_cinematic_broll_default_leonardo():
    assert route_visual_provider("cinematic_broll")["provider"] == "leonardo"


def test_route_atmosphere_still_leonardo():
    assert route_visual_provider("atmosphere_still")["provider"] == "leonardo"


def test_route_motion_runway():
    assert route_visual_provider("motion_clip")["provider"] == "runway"


def test_route_thumbnail_openai():
    assert route_visual_provider("thumbnail_base")["provider"] == "openai_images"


def test_route_overlay_render_layer():
    r = route_visual_provider("lower_third", text_sensitive=False)
    assert r["provider"] == "render_layer"
    assert r["image_provider"] == "leonardo"
    r2 = route_visual_provider("title_card", text_sensitive=True)
    assert r2["provider"] == "render_layer"
    assert r2["image_provider"] == "openai_images"


def test_append_no_text_guard_idempotent():
    a = append_no_text_guard("cinematic push-in")
    b = append_no_text_guard(a)
    assert a == b
    assert "No readable text" in a
    assert "Keine lesbare Schrift" in a


def test_blueprint_checklist_not_in_leonardo_positive_expanded():
    bp = SceneBlueprintPlanResponse(
        policy_profile="visual_policy_test",
        scenes=[
            SceneBlueprintContract(
                scene_number=1,
                prompt_pack=SceneBlueprintPromptPack(
                    image_primary=(
                        "Eine dunkle Checkliste mit drei Punkten: "
                        "Akte prüfen, Zeugen finden, Wahrheit suchen"
                    ),
                ),
            ),
        ],
        warnings=[],
    )
    bundle = build_all_provider_prompts(bp, continuity_lock=False, safety_segments=tuple())
    leo = bundle.leonardo[0]
    assert "Akte prüfen" not in leo.positive_expanded
    assert "[visual_no_text_guard_v26_4]" in leo.positive_expanded
    assert leo.overlay_intent
    assert leo.text_sensitive is True
    assert leo.routed_visual_provider == "openai_images"


def test_runway_motion_prompt_no_fake_ui_readable_wording():
    from app.models import ExportPackageRequest, Chapter
    from app.story_engine.provider_optimizer import optimize_provider_prompts

    req = ExportPackageRequest(
        video_template="generic",
        duration_minutes=10,
        title="T",
        hook="H",
        chapters=[
            Chapter(title="Eins", content=("Inhalt genug für eine Szene. " * 12)),
        ],
        provider_profile="openai",
        continuity_lock=False,
    )
    out = optimize_provider_prompts(req)
    km = out.optimized_prompts.kling[0]
    assert "fake UI" not in km.motion_prompt.lower()
    assert "subject readable" not in km.motion_prompt.lower()
    assert "[visual_no_text_guard_v26_4]" in km.motion_prompt
    assert km.routed_visual_provider == "runway"
