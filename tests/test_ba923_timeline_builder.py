"""BA 9.23 — Production Timeline Builder V1."""

from app.prompt_engine.schema import (
    ChapterOutlineItem,
    ProductionExportContractResult,
    ProductionExportPayload,
    ProductionPromptPlan,
)
from app.prompt_engine.timeline_builder import build_production_timeline


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
        hook="Starker Eröffnungs-Hook für die Timeline.",
        chapter_outline=[
            ChapterOutlineItem(title="Kapitel A", summary="a"),
            ChapterOutlineItem(title="Kapitel B", summary="b"),
        ],
        scene_prompts=["Szene A Text genügend lang.", "Szene B Text genügend lang."],
        voice_style="calm",
        thumbnail_angle="dramatic",
        warnings=[],
        video_template="true_crime",
        narrative_archetype_id="arc",
        hook_type="cold_open",
        hook_score=8.0,
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


def test_timeline_hook_first_then_one_scene_per_chapter():
    tl = build_production_timeline(_plan())
    assert tl.timeline_status == "ready"
    assert len(tl.scenes) == 3
    assert tl.scenes[0].timeline_role == "hook"
    assert tl.scenes[0].chapter_title == "Hook"
    assert tl.scenes[1].chapter_title == "Kapitel A"
    assert tl.scenes[2].chapter_title == "Kapitel B"
    assert tl.scenes[0].provider_targets == ["Leonardo", "Kling"]


def test_duration_length_categories():
    short_plan = _plan(
        chapter_outline=[ChapterOutlineItem(title="K", summary="x")],
        scene_prompts=["nur eine Szene"],
    )
    tl_s = build_production_timeline(short_plan)
    assert tl_s.target_video_length_category == "short"
    assert tl_s.total_estimated_duration_seconds < 90

    medium_ch = [ChapterOutlineItem(title=f"K{i}", summary="s") for i in range(4)]
    medium_sc = [f"Szenario {i}" for i in range(4)]
    tl_m = build_production_timeline(_plan(chapter_outline=medium_ch, scene_prompts=medium_sc))
    assert tl_m.target_video_length_category == "medium"
    assert 90 <= tl_m.total_estimated_duration_seconds <= 480

    many = [ChapterOutlineItem(title=f"K{i}", summary="s") for i in range(18)]
    prompts = [f"Szenentext Nummer {i} mit etwas Inhalt." for i in range(18)]
    long_plan = _plan(chapter_outline=many, scene_prompts=prompts)
    tl_l = build_production_timeline(long_plan)
    assert tl_l.target_video_length_category == "long"
    assert tl_l.total_estimated_duration_seconds > 480


def test_mismatch_chapters_scenes_partial():
    tl = build_production_timeline(
        _plan(
            scene_prompts=["nur eins"],
        )
    )
    assert tl.timeline_status == "partial"
    assert any("mismatch" in w.lower() for w in tl.warnings)


def test_blocked_export_contract_blocks_timeline():
    tl = build_production_timeline(
        _plan(
            production_export_contract_result=_contract(export_ready=False, export_status="blocked"),
        )
    )
    assert tl.timeline_status == "blocked"
    assert tl.scenes == []


def test_hook_only_timeline_partial():
    tl = build_production_timeline(
        _plan(
            chapter_outline=[],
            scene_prompts=[],
        )
    )
    assert len(tl.scenes) == 1
    assert tl.scenes[0].timeline_role == "hook"
    assert tl.timeline_status == "partial"
