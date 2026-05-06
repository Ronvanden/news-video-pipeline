"""BA 9.20 — Provider Packaging / Provider Mapping V1."""

from app.prompt_engine.provider_packaging import WARN_CONTRACT_BLOCKED, build_provider_packages
from app.prompt_engine.schema import (
    ChapterOutlineItem,
    ProductionExportContractResult,
    ProductionExportPayload,
    ProductionPromptPlan,
)


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
        hook="Ein ausreichend langer Hook für Provider-Packaging.",
        chapter_outline=[
            ChapterOutlineItem(title="K1", summary="a"),
            ChapterOutlineItem(title="K2", summary="b"),
        ],
        scene_prompts=["scene one", "scene two"],
        voice_style="documentary calm",
        thumbnail_angle="high contrast silhouette",
        warnings=[],
        video_template="true_crime",
        narrative_archetype_id="arc",
        hook_type="cold_open",
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
    defaults.update(kwargs)
    return ProductionPromptPlan(**defaults)


def test_full_plan_all_core_packages_ready():
    r = build_provider_packages(_plan())
    assert r.packaging_status == "ready"
    assert len(r.packages) == 5
    assert all(p.package_status == "ready" for p in r.packages)
    types = {p.provider_type for p in r.packages}
    assert types == {"image", "video", "voice", "thumbnail", "render"}
    leo = next(p for p in r.packages if p.provider_type == "image")
    assert leo.provider_name == "Leonardo"
    assert leo.payload.get("style_profile") == "true_crime"
    assert len(leo.payload.get("prompts", [])) == 2


def test_missing_scenes_image_video_partial():
    p = _plan(
        scene_prompts=[],
        production_export_contract_result=_contract(),
    )
    r = build_provider_packages(p)
    assert r.packaging_status == "partial"
    img = next(x for x in r.packages if x.provider_type == "image")
    vid = next(x for x in r.packages if x.provider_type == "video")
    assert img.package_status == "incomplete"
    assert vid.package_status == "incomplete"


def test_missing_voice_incomplete_with_warning():
    p = _plan(voice_style="", production_export_contract_result=_contract())
    r = build_provider_packages(p)
    vo = next(x for x in r.packages if x.provider_type == "voice")
    assert vo.package_status == "incomplete"
    assert any("voice_style" in w.lower() for w in vo.warnings)


def test_missing_thumbnail_incomplete():
    p = _plan(thumbnail_angle="", production_export_contract_result=_contract())
    r = build_provider_packages(p)
    th = next(x for x in r.packages if x.provider_type == "thumbnail")
    assert th.package_status == "incomplete"


def test_blocked_export_contract_all_blocked():
    p = _plan(production_export_contract_result=_contract(export_ready=False, export_status="blocked"))
    r = build_provider_packages(p)
    assert r.packaging_status == "blocked"
    assert all(p.package_status == "blocked" for p in r.packages)
    assert WARN_CONTRACT_BLOCKED in r.packages[0].warnings[0] or "blocked" in r.packages[0].warnings[0].lower()


def test_missing_contract_all_blocked():
    p = _plan(production_export_contract_result=None)
    r = build_provider_packages(p)
    assert r.packaging_status == "blocked"
