"""BA 26.4e — Provider Routing Acceptance Smoke (dry-run, keine Provider-Calls).

Ziel: Vor BA 26.5 trocken beweisen, dass Routing + No-Text-Guard + Overlay-Auslagerung +
Manifest/Policy-Felder konsistent zusammenspielen.
"""

from __future__ import annotations

from typing import Any, Dict, List

from app.visual_plan.visual_no_text import append_no_text_guard, partition_visual_overlay_text
from app.visual_plan.visual_policy_report import build_visual_policy_fields, ensure_effective_prompt
from app.visual_plan.visual_provider_router import route_visual_provider


def _scene(
    *,
    asset_kind: str,
    prompt: str,
    force_overlay: bool = False,
) -> Dict[str, Any]:
    # partition: overlay_intent + text_sensitive + textfreier core prompt
    cleaned, overlay, text_sensitive = partition_visual_overlay_text(prompt)
    if force_overlay and not overlay:
        overlay = ["(overlay missing)"]
    route = route_visual_provider(asset_kind, text_sensitive=bool(text_sensitive))

    routed_visual_provider = str(route.get("provider") or "")
    routed_image_provider = str(route.get("image_provider") or "")

    eff = append_no_text_guard(cleaned or prompt)
    eff2, _ = ensure_effective_prompt(eff)

    fields = build_visual_policy_fields(
        visual_prompt_raw=prompt,
        visual_prompt_effective=eff2,
        overlay_intent=overlay,
        text_sensitive=bool(text_sensitive),
        visual_asset_kind=asset_kind,
        routed_visual_provider=routed_visual_provider,
        routed_image_provider=routed_image_provider,
    )
    # Spiegelung der für Dashboard/Manifeste relevanten Keys
    fields["overlay_intent"] = overlay
    fields["text_sensitive"] = bool(text_sensitive)
    fields["visual_asset_kind"] = asset_kind
    fields["routed_visual_provider"] = routed_visual_provider
    fields["routed_image_provider"] = routed_image_provider
    return fields


def test_ba264e_provider_routing_acceptance_smoke():
    scenes: List[Dict[str, Any]] = []

    # A) cinematic_broll
    scenes.append(
        _scene(
            asset_kind="cinematic_broll",
            prompt="Cinematic night street, documentary mood, no text focus",
        )
    )

    # B) text_sensitive checklist → overlay_intent + openai_images
    scenes.append(
        _scene(
            asset_kind="cinematic_broll",
            prompt="Dark checklist with text: Akte prüfen, Zeugen finden, Wahrheit suchen",
        )
    )

    # C) motion_clip → runway
    scenes.append(
        _scene(
            asset_kind="motion_clip",
            prompt="Slow cinematic camera push through abandoned hallway",
        )
    )

    # D) thumbnail_base → openai_images
    scenes.append(
        _scene(
            asset_kind="thumbnail_base",
            prompt="High impact mystery thumbnail base with clean negative space reserved for later editorial overlay",
        )
    )

    # E) title_card / final_text_overlay → render_layer + overlay
    scenes.append(
        _scene(
            asset_kind="title_card",
            prompt='Title card text: "Die Wahrheit kam zu spät"',
        )
    )

    # --- Assertions per Szene ---
    assert len(scenes) == 5
    for s in scenes:
        # Contract-nah: BA 26.4c Feldnamen vorhanden
        for k in (
            "visual_prompt_raw",
            "visual_prompt_effective",
            "visual_text_guard_applied",
            "visual_policy_status",
            "visual_policy_warnings",
            "provider_routing_reason",
        ):
            assert k in s
        assert "[visual_no_text_guard_v26_4]" in str(s.get("visual_prompt_effective") or "")
        assert s.get("visual_text_guard_applied") is True
        assert s.get("visual_policy_status") in ("safe", "text_extracted", "needs_review")

    # A expectations
    assert scenes[0]["routed_visual_provider"] == "leonardo"
    assert scenes[0]["visual_policy_status"] in ("safe", "text_extracted")

    # B expectations (checklist)
    assert scenes[1]["text_sensitive"] is True
    assert scenes[1]["routed_visual_provider"] == "openai_images"
    ov = scenes[1].get("overlay_intent") or []
    assert "Akte prüfen" in ov
    assert "Zeugen finden" in ov
    assert "Wahrheit suchen" in ov
    assert scenes[1]["visual_policy_status"] == "text_extracted"

    # C expectations (motion)
    assert scenes[2]["routed_visual_provider"] == "runway"
    # keine positiven Text-/UI-Aufträge; Guard ist nur negativ
    eff_motion = str(scenes[2]["visual_prompt_effective"] or "").lower()
    assert "add subtitles" not in eff_motion
    assert "render text" not in eff_motion

    # D expectations (thumbnail)
    assert scenes[3]["routed_visual_provider"] == "openai_images"
    assert scenes[3]["visual_policy_status"] != "needs_review"

    # E expectations (title_card)
    assert scenes[4]["routed_visual_provider"] == "render_layer"
    ov2 = scenes[4].get("overlay_intent") or []
    assert "Die Wahrheit kam zu spät" in ov2
    assert scenes[4]["visual_policy_status"] == "text_extracted"

    # --- Acceptance report ---
    providers = {"leonardo": 0, "openai_images": 0, "runway": 0, "render_layer": 0}
    guard_applied_count = 0
    overlay_intent_count = 0
    needs_review_count = 0
    warnings: List[str] = []

    for s in scenes:
        rp = str(s.get("routed_visual_provider") or "")
        if rp in providers:
            providers[rp] += 1
        if s.get("visual_text_guard_applied"):
            guard_applied_count += 1
        overlay_intent_count += len((s.get("overlay_intent") or []))
        if s.get("visual_policy_status") == "needs_review":
            needs_review_count += 1

    report = {
        "ok": True,
        "acceptance": "passed",
        "scenes_checked": len(scenes),
        "guard_applied_count": guard_applied_count,
        "overlay_intent_count": overlay_intent_count,
        "providers": providers,
        "needs_review_count": needs_review_count,
        "warnings": warnings,
    }

    assert report["scenes_checked"] == 5
    assert report["guard_applied_count"] == 5
    assert report["needs_review_count"] == 0
    assert report["providers"]["leonardo"] >= 1
    assert report["providers"]["openai_images"] >= 1
    assert report["providers"]["runway"] >= 1
    assert report["providers"]["render_layer"] >= 1
    assert report["ok"] is True

