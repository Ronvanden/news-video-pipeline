"""BA 9.20 — Provider-Packaging / Mapping (Stubs, keine echten Provider-Calls)."""

from __future__ import annotations

from typing import List

from app.prompt_engine.schema import (
    ProviderPackage,
    ProviderPackagingOverallStatus,
    ProviderPackagingResult,
    ProviderRoleType,
    ProductionPromptPlan,
)

WARN_CONTRACT_MISSING = "Production export contract missing."
WARN_CONTRACT_BLOCKED = "Export contract blocked; provider packaging halted."


def _blocked_slot(role: ProviderRoleType, name: str, reason: str) -> ProviderPackage:
    return ProviderPackage(
        provider_type=role,
        provider_name=name,
        package_status="blocked",
        payload={},
        warnings=[reason],
    )


def build_provider_packages(plan: ProductionPromptPlan) -> ProviderPackagingResult:
    checked_sources = ["production_prompt_plan", "provider_packaging_v1"]
    ex = plan.production_export_contract_result
    if ex is not None:
        checked_sources.append("production_export_contract_result")

    if ex is None:
        pkgs = [
            _blocked_slot("image", "Leonardo", WARN_CONTRACT_MISSING),
            _blocked_slot("video", "Kling", WARN_CONTRACT_MISSING),
            _blocked_slot("voice", "OpenAI / ElevenLabs (stub)", WARN_CONTRACT_MISSING),
            _blocked_slot("thumbnail", "Thumbnail (stub)", WARN_CONTRACT_MISSING),
            _blocked_slot("render", "Render timeline (stub)", WARN_CONTRACT_MISSING),
        ]
        return ProviderPackagingResult(
            packaging_status="blocked",
            packages=pkgs,
            checked_sources=checked_sources,
        )

    if ex.export_status == "blocked":
        reason = WARN_CONTRACT_BLOCKED
        pkgs = [
            _blocked_slot("image", "Leonardo", reason),
            _blocked_slot("video", "Kling", reason),
            _blocked_slot("voice", "OpenAI / ElevenLabs (stub)", reason),
            _blocked_slot("thumbnail", "Thumbnail (stub)", reason),
            _blocked_slot("render", "Render timeline (stub)", reason),
        ]
        return ProviderPackagingResult(
            packaging_status="blocked",
            packages=pkgs,
            checked_sources=checked_sources,
        )

    chapters = list(plan.chapter_outline or [])
    scenes = list(plan.scene_prompts or [])
    n_ch, n_sc = len(chapters), len(scenes)

    # A) IMAGE — Leonardo
    img_warn: List[str] = []
    if not scenes:
        img_warn.append("No scene_prompts for image generation.")
        img_st = "incomplete"
    else:
        img_st = "ready"
    img_pkg = ProviderPackage(
        provider_type="image",
        provider_name="Leonardo",
        package_status=img_st,
        payload={
            "provider_target": "Leonardo",
            "style_profile": plan.template_type,
            "prompts": scenes,
        },
        warnings=img_warn,
    )

    # B) VIDEO — Kling
    vid_warn: List[str] = []
    if not scenes:
        vid_warn.append("No scene_prompts for video motion prompts.")
        vid_st = "incomplete"
    elif n_ch != n_sc:
        vid_warn.append("Chapter/scene count mismatch for chapter progression.")
        vid_st = "incomplete"
    else:
        vid_st = "ready"
    motion: List[dict] = []
    for i, ch in enumerate(chapters):
        sc = scenes[i] if i < n_sc else ""
        motion.append(
            {
                "index": i,
                "chapter_title": ch.title,
                "motion_prompt": f"{sc} | progression: beat {i + 1}/{max(n_ch, 1)}",
            }
        )
    vid_pkg = ProviderPackage(
        provider_type="video",
        provider_name="Kling",
        package_status=vid_st,
        payload={"provider_target": "Kling", "motion_prompts": motion},
        warnings=vid_warn,
    )

    # C) VOICE — stub
    vo_warn: List[str] = []
    vs = (plan.voice_style or "").strip()
    if not vs:
        vo_warn.append("voice_style missing for voice provider stub.")
        vo_st = "incomplete"
    else:
        vo_st = "ready"
    blocks = [{"chapter_title": c.title, "summary": c.summary} for c in chapters]
    vo_pkg = ProviderPackage(
        provider_type="voice",
        provider_name="OpenAI / ElevenLabs (stub)",
        package_status=vo_st,
        payload={
            "provider_stub": "OpenAI / ElevenLabs",
            "voice_style": vs,
            "chapter_voice_blocks": blocks,
        },
        warnings=vo_warn,
    )

    # D) THUMBNAIL
    th_warn: List[str] = []
    hk = (plan.hook or "").strip()
    ta = (plan.thumbnail_angle or "").strip()
    th_st: str
    if not ta:
        th_warn.append("thumbnail_angle missing.")
        th_st = "incomplete"
    else:
        th_st = "ready"
    if not hk:
        th_warn.append("hook empty; thumbnail may lack narrative anchor.")
        th_st = "incomplete"
    th_pkg = ProviderPackage(
        provider_type="thumbnail",
        provider_name="Thumbnail (stub)",
        package_status=th_st,
        payload={
            "hook": plan.hook,
            "thumbnail_angle": plan.thumbnail_angle,
            "composite_prompt": f"{hk} — {ta}".strip(" —") if hk and ta else "",
        },
        warnings=th_warn,
    )

    # E) RENDER timeline
    ren_warn: List[str] = []
    if n_ch == 0 or n_sc == 0:
        ren_warn.append("Timeline requires chapters and scenes.")
        ren_st = "incomplete"
    elif n_ch != n_sc:
        ren_warn.append("Chapter/scene count mismatch for render timeline.")
        ren_st = "incomplete"
    else:
        ren_st = "ready"
    timeline = [
        {"order": i, "chapter_title": chapters[i].title, "scene_prompt": scenes[i]}
        for i in range(min(n_ch, n_sc))
    ]
    ren_pkg = ProviderPackage(
        provider_type="render",
        provider_name="Render timeline (stub)",
        package_status=ren_st,
        payload={"timeline_skeleton": timeline},
        warnings=ren_warn,
    )

    packages = [img_pkg, vid_pkg, vo_pkg, th_pkg, ren_pkg]
    local_ready = all(p.package_status == "ready" for p in packages)

    packaging_status: ProviderPackagingOverallStatus
    if local_ready and ex.export_ready:
        packaging_status = "ready"
    elif any(p.package_status == "blocked" for p in packages):
        packaging_status = "blocked"
    else:
        packaging_status = "partial"

    return ProviderPackagingResult(
        packaging_status=packaging_status,
        packages=packages,
        checked_sources=checked_sources,
    )
