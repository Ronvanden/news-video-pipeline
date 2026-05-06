"""BA 9.22 — Validierung des Provider-Export-Bundles (ohne Produktionsstart)."""

from __future__ import annotations

from typing import List

from app.prompt_engine.schema import (
    PackageValidationResult,
    ProductionPromptPlan,
)

REC_ALIGN_CHAPTERS_SCENES = (
    "Align chapter_outline and scene_prompts counts before production handoff."
)
REC_VOICE_THUMB = "Fill voice_style and thumbnail_angle for voice and thumbnail providers."
REC_EXPORT_GATE = "Resolve export contract / handoff gate before treating bundle as production-safe."


def validate_provider_export_bundle(plan: ProductionPromptPlan) -> PackageValidationResult:
    missing: List[str] = []
    warnings: List[str] = []
    recommendations: List[str] = []

    bundle = plan.provider_export_bundle_result
    if bundle is None:
        recommendations.append(REC_EXPORT_GATE)
        return PackageValidationResult(
            validation_status="fail",
            production_safety="unsafe",
            missing_components=["provider_export_bundle"],
            warnings=["provider_export_bundle_result missing."],
            recommendations=recommendations,
        )

    if bundle.bundle_status == "blocked":
        missing.append("export_bundle_blocked")
        recommendations.append(REC_EXPORT_GATE)
        return PackageValidationResult(
            validation_status="fail",
            production_safety="unsafe",
            missing_components=missing,
            warnings=list(dict.fromkeys(bundle.warnings or [])),
            recommendations=recommendations,
        )

    prov = bundle.providers
    slots = [
        ("image", prov.image_package),
        ("video", prov.video_package),
        ("voice", prov.voice_package),
        ("thumbnail", prov.thumbnail_package),
        ("render", prov.render_package),
    ]
    for key, pkg in slots:
        if pkg.package_status != "ready":
            missing.append(key)

    ch = len(plan.chapter_outline or [])
    sc = len(plan.scene_prompts or [])
    if ch != sc:
        warnings.append("Hook/chapter/scene consistency: chapter count != scene count.")
        recommendations.append(REC_ALIGN_CHAPTERS_SCENES)
        if "render" not in missing:
            missing.append("timeline_consistency")

    if not (plan.hook or "").strip():
        warnings.append("Hook is empty.")
        if "thumbnail" not in missing:
            missing.append("hook_present")

    if not (plan.voice_style or "").strip():
        warnings.append("voice_style is empty.")
        if "voice" not in missing:
            missing.append("voice_style_present")

    if not (plan.thumbnail_angle or "").strip():
        warnings.append("thumbnail_angle is empty.")
        recommendations.append(REC_VOICE_THUMB)

    missing = list(dict.fromkeys(missing))

    core_ok = (
        prov.image_package.package_status == "ready"
        and prov.video_package.package_status == "ready"
        and prov.voice_package.package_status == "ready"
        and prov.thumbnail_package.package_status == "ready"
        and prov.render_package.package_status == "ready"
        and bundle.bundle_status == "ready"
        and ch == sc
        and ch > 0
    )

    if core_ok and not warnings:
        return PackageValidationResult(
            validation_status="pass",
            production_safety="safe",
            missing_components=[],
            warnings=[],
            recommendations=[],
        )

    if core_ok and warnings:
        recommendations.append(REC_VOICE_THUMB)
        return PackageValidationResult(
            validation_status="warning",
            production_safety="review",
            missing_components=[],
            warnings=warnings,
            recommendations=list(dict.fromkeys(recommendations)),
        )

    slots_all_ready = all(pkg.package_status == "ready" for _, pkg in slots)
    if (
        not missing
        and slots_all_ready
        and ch == sc
        and ch > 0
        and bundle.bundle_status == "partial"
    ):
        merge_warn = list(warnings)
        merge_warn.append(
            "Bundle status partial while export_handoff is not export_ready (expected until human approval)."
        )
        recommendations.append(REC_EXPORT_GATE)
        return PackageValidationResult(
            validation_status="warning",
            production_safety="review",
            missing_components=[],
            warnings=list(dict.fromkeys(merge_warn + (bundle.warnings or []))),
            recommendations=list(dict.fromkeys(recommendations)),
        )

    recommendations.append(REC_EXPORT_GATE)
    return PackageValidationResult(
        validation_status="fail",
        production_safety="unsafe",
        missing_components=missing,
        warnings=warnings + (bundle.warnings or []),
        recommendations=list(dict.fromkeys(recommendations)),
    )
