"""BA 9.21 — Multi-Provider Export Bundle (ein Maschinenpaket für Connectoren)."""

from __future__ import annotations

import hashlib
from typing import List

from app.prompt_engine.provider_packaging import build_provider_packages
from app.prompt_engine.schema import (
    ProviderExportBundleResult,
    ProviderExportProviders,
    ProviderPackage,
    ProviderPackagingOverallStatus,
    ProviderPackagingResult,
    ProviderRoleType,
    ProductionPromptPlan,
)

BUNDLE_VERSION = "9.21-v1"


def _pick(
    packaging: ProviderPackagingResult,
    role: ProviderRoleType,
    fallback_name: str,
) -> ProviderPackage:
    for p in packaging.packages:
        if p.provider_type == role:
            return p
    return ProviderPackage(
        provider_type=role,
        provider_name=fallback_name,
        package_status="blocked",
        payload={},
        warnings=["Package missing from provider_packaging_result."],
    )


def build_bundle_id(plan: ProductionPromptPlan, packaging_status: str) -> str:
    seed = "|".join(
        [
            plan.template_type,
            plan.video_template,
            packaging_status,
            str(len(plan.scene_prompts or [])),
        ]
    )
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:14]
    return f"bundle_{plan.template_type}_{digest}"


def build_provider_export_bundle(plan: ProductionPromptPlan) -> ProviderExportBundleResult:
    pkg_res = plan.provider_packaging_result
    if pkg_res is None:
        pkg_res = build_provider_packages(plan)

    providers = ProviderExportProviders(
        image_package=_pick(pkg_res, "image", "Leonardo"),
        video_package=_pick(pkg_res, "video", "Kling"),
        voice_package=_pick(pkg_res, "voice", "OpenAI / ElevenLabs (stub)"),
        thumbnail_package=_pick(pkg_res, "thumbnail", "Thumbnail (stub)"),
        render_package=_pick(pkg_res, "render", "Render timeline (stub)"),
    )

    bundle_status: ProviderPackagingOverallStatus = pkg_res.packaging_status
    bundle_id = build_bundle_id(plan, bundle_status)

    flat_warnings: List[str] = []
    for p in pkg_res.packages:
        flat_warnings.extend(p.warnings or [])
    flat_warnings = list(dict.fromkeys(flat_warnings))

    if bundle_status == "ready":
        summary = "Multi-provider export bundle is ready for downstream connectors."
    elif bundle_status == "blocked":
        summary = "Export bundle blocked (see export contract or packaging)."
    else:
        summary = "Export bundle is partial; some provider payloads are incomplete."

    return ProviderExportBundleResult(
        bundle_version=BUNDLE_VERSION,
        bundle_status=bundle_status,
        bundle_id=bundle_id,
        providers=providers,
        export_summary=summary,
        warnings=flat_warnings,
    )
