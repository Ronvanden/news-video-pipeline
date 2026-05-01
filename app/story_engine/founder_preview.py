"""BA 10.4 — Founder-Preview aus Export-Paket (lokal, deterministisch)."""

from __future__ import annotations

from app.models import (
    ExportPackagePreviewResponse,
    ExportPackageRequest,
    PromptQualityReport,
    ProviderProfileFlags,
    ThumbnailStrengthLiteral,
)
from app.story_engine.export_package import _dedupe_warnings, build_export_package_v1
from app.story_engine.provider_readiness import analyze_provider_readiness
from app.story_engine.templates import normalize_story_template_id


def _thumbnail_strength(thumbnail_prompt: str) -> ThumbnailStrengthLiteral:
    n = len((thumbnail_prompt or "").strip())
    if n >= 180:
        return "high"
    if n >= 90:
        return "medium"
    return "low"


def _prompt_quality_score(pq: PromptQualityReport | None) -> int:
    if not pq:
        return 0
    score = 100
    score -= 14 * len(pq.global_checks or [])
    for e in pq.scenes or []:
        score -= 5 * len(e.checks or [])
    return max(0, min(100, int(score)))


def _provider_stub_warning_count(pq: PromptQualityReport | None) -> int:
    """Summe der Szenen-Qualitätscodes (proxy für Stub-/Prompt-Risiken)."""
    if not pq:
        return 0
    return sum(len(e.checks or []) for e in (pq.scenes or []))


def build_export_preview(req: ExportPackageRequest) -> ExportPackagePreviewResponse:
    tid, _ = normalize_story_template_id(req.video_template)
    pkg = build_export_package_v1(req)
    readiness = analyze_provider_readiness(pkg)
    pq = pkg.prompt_quality or pkg.scene_prompts.prompt_quality
    scene_count = len(pkg.scene_plan.scenes or [])
    top = _dedupe_warnings(list(pkg.warnings or []))[:8]
    export_ready = (
        readiness.overall_status in ("ready", "partial_ready")
        and pkg.scene_plan.status != "failed"
        and scene_count > 0
    )
    return ExportPackagePreviewResponse(
        template_id=tid,
        hook_score=float(pkg.hook.hook_score),
        hook_type=pkg.hook.hook_type,
        thumbnail_strength=_thumbnail_strength(pkg.thumbnail_prompt),
        prompt_quality_score=_prompt_quality_score(pq),
        scene_count=scene_count,
        provider_profiles=ProviderProfileFlags(
            openai=readiness.scores.openai >= 70,
            leonardo=readiness.scores.leonardo >= 70,
            kling=readiness.scores.kling >= 70,
        ),
        provider_stub_warnings=_provider_stub_warning_count(pq),
        readiness_status=readiness.overall_status,
        top_warnings=top,
        export_ready=export_ready,
    )
