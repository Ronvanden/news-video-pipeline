"""BA 13.0 — Metadata Master Package."""

from __future__ import annotations

import re
from typing import List

from app.publishing.schema import MetadataMasterPackageResult


def _clean_text(value: str, *, max_len: int) -> str:
    cleaned = re.sub(r"\s+", " ", (value or "").strip())
    return cleaned[:max_len].rstrip()


def _tags_from_plan(plan: object) -> List[str]:
    raw_terms = [
        getattr(plan, "template_type", ""),
        getattr(plan, "video_template", ""),
        getattr(plan, "narrative_archetype_id", ""),
        "news",
        "story",
    ]
    hook = getattr(plan, "hook", "") or ""
    for token in re.findall(r"[A-Za-zÄÖÜäöüß0-9]{4,}", hook):
        raw_terms.append(token.lower())
    out: List[str] = []
    for term in raw_terms:
        tag = re.sub(r"[^A-Za-zÄÖÜäöüß0-9_-]+", "_", (term or "").strip().lower()).strip("_")
        if tag and tag not in out:
            out.append(tag)
    return out[:15]


def build_metadata_master_package(plan: object) -> MetadataMasterPackageResult:
    warnings: List[str] = []
    hook = _clean_text(getattr(plan, "hook", "") or "", max_len=95)
    title_base = hook or _clean_text(getattr(plan, "template_type", "") or "Production Story", max_len=95)
    canonical_title = title_base if len(title_base) <= 95 else title_base[:92].rstrip() + "..."

    chapters = getattr(plan, "chapter_outline", []) or []
    chapter_lines = []
    for idx, chapter in enumerate(chapters[:6], start=1):
        title = getattr(chapter, "title", "") or f"Kapitel {idx}"
        summary = getattr(chapter, "summary", "") or ""
        chapter_lines.append(f"{idx}. {title}: {summary}".strip())

    description_parts = [
        canonical_title,
        "",
        "In diesem Video:",
        *chapter_lines,
        "",
        "Hinweis: Publishing-Paket V1, kein automatischer Upload.",
    ]
    canonical_description = _clean_text("\n".join(description_parts), max_len=4500)
    tags = _tags_from_plan(plan)

    if not canonical_title:
        warnings.append("canonical_title_missing")
    if not chapter_lines:
        warnings.append("chapter_outline_missing_for_description")
    if len(tags) < 5:
        warnings.append("canonical_tags_sparse")

    audience_flags = ["human_review_required", "no_auto_publish"]
    if "crime" in (getattr(plan, "template_type", "") or "").lower() or "mord" in canonical_title.lower():
        audience_flags.append("sensitive_topic_review")
        warnings.append("sensitive_topic_requires_manual_review")

    status = "complete"
    if not canonical_title or not canonical_description or not tags:
        status = "blocked"
    elif warnings:
        status = "partial"

    return MetadataMasterPackageResult(
        metadata_status=status,
        platform_target="youtube",
        canonical_title=canonical_title,
        canonical_description=canonical_description,
        canonical_tags=tags,
        category="News & Politics",
        audience_flags=list(dict.fromkeys(audience_flags)),
        compliance_warnings=list(dict.fromkeys(warnings)),
    )
