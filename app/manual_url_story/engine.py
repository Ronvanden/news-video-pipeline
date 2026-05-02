"""Manual URL → Extraktion → Narrativ-Rewrite — Eingriffspunkt für build_production_prompt_plan."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple
from urllib.parse import urlparse

from app.manual_url_story.quality_gate import build_url_quality_gate_result
from app.manual_url_story.rewrite_mode import (
    resolve_video_template_for_manual_url_script,
    tune_hook_for_rewrite_mode,
)
from app.manual_url_story.schema import (
    DemoStepStatus,
    ManualUrlAssetPromptStep,
    ManualUrlDemoVideoStep,
    ManualUrlExtractionStep,
    ManualUrlIntakeStep,
    ManualUrlNarrativeRewriteStep,
    ManualUrlStoryExecutionResult,
    StepStatus,
    UrlQualityGateResult,
)
from app.prompt_engine.schema import ChapterOutlineItem, PromptPlanRequest
from app.utils import build_script_response_from_extracted_text, extract_text_from_url


def _safe_source_url_display(url: str) -> str:
    raw = (url or "").strip()
    if not raw:
        return ""
    p = urlparse(raw.split("#", 1)[0])
    if not p.netloc:
        return ""
    path = p.path or ""
    return f"{p.scheme}://{p.netloc}{path}"[:480]


@dataclass
class ManualUrlRewriteOutcome:
    effective_topic: str
    effective_title: str
    effective_source_summary: str
    chapter_outline_override: Optional[List[ChapterOutlineItem]]
    hook_override: Optional[str]
    hook_extra_warnings: List[str]
    intake_display_url: str
    extraction_ok: bool
    narrative_ok: bool
    extraction_warnings: List[str]
    narrative_warnings: List[str]
    extracted_char_count: int
    script_title: str
    chapter_count: int
    full_script_preview: str


def run_manual_url_rewrite_phase(
    req: PromptPlanRequest,
) -> Tuple[Optional[ManualUrlRewriteOutcome], Optional[UrlQualityGateResult]]:
    """Liest optional manual_source_url; bei Fehlen (None, None) — klassischer Topic-Pfad."""
    url = (req.manual_source_url or "").strip()
    if not url:
        return None, None

    display = _safe_source_url_display(url)
    hook_extra: List[str] = []
    hook_extra.append("[manual_url_story] Kernpfad aktiv — Topic/Titel/Zusammenfassung aus URL-Pipeline gespeist.")

    extracted_text, extraction_warnings = extract_text_from_url(url)
    ext_ok = bool((extracted_text or "").strip())
    ext_chars = len(extracted_text or "")

    if not ext_ok:
        outcome = ManualUrlRewriteOutcome(
            effective_topic=req.topic,
            effective_title=req.title,
            effective_source_summary=req.source_summary,
            chapter_outline_override=None,
            hook_override=None,
            hook_extra_warnings=hook_extra,
            intake_display_url=display,
            extraction_ok=False,
            narrative_ok=False,
            extraction_warnings=list(extraction_warnings),
            narrative_warnings=[],
            extracted_char_count=0,
            script_title="",
            chapter_count=0,
            full_script_preview="",
        )
        gate = build_url_quality_gate_result(
            extraction_ok=False,
            extracted_text="",
            narrative_ok=False,
            script_title="",
            full_script="",
            chapter_count=0,
        )
        return outcome, gate

    tpl = resolve_video_template_for_manual_url_script(req)
    tc = (req.manual_url_template_conformance_level or "warn").strip() or "warn"

    title, hook, chapters_raw, full_script, _sources, script_warnings = (
        build_script_response_from_extracted_text(
            extracted_text=extracted_text,
            source_url=url,
            target_language=req.manual_url_target_language or "de",
            duration_minutes=int(req.manual_url_duration_minutes),
            extraction_warnings=extraction_warnings,
            extra_warnings=None,
            video_template=tpl,
            template_conformance_level=tc,
        )
    )

    narrative_ok = bool(full_script and full_script.strip())
    eff_title = (title or "").strip() or req.title
    eff_topic = (title or "").strip() or req.topic
    summary_cap = 12000
    eff_summary = (full_script or "").strip()[:summary_cap] if narrative_ok else req.source_summary

    ch_outline: Optional[List[ChapterOutlineItem]] = None
    if chapters_raw:
        ch_outline = [
            ChapterOutlineItem(
                title=str(c.get("title") or f"Kapitel {i}"),
                summary=str(c.get("content") or "")[:4000],
            )
            for i, c in enumerate(chapters_raw, start=1)
        ]

    raw_hook = (hook or "").strip() if narrative_ok else ""
    hook_override = (
        tune_hook_for_rewrite_mode(raw_hook, getattr(req, "manual_url_rewrite_mode", "") or "")
        if raw_hook
        else None
    )

    outcome = ManualUrlRewriteOutcome(
        effective_topic=eff_topic,
        effective_title=eff_title,
        effective_source_summary=eff_summary,
        chapter_outline_override=ch_outline,
        hook_override=hook_override,
        hook_extra_warnings=hook_extra,
        intake_display_url=display,
        extraction_ok=True,
        narrative_ok=narrative_ok,
        extraction_warnings=list(extraction_warnings),
        narrative_warnings=list(script_warnings),
        extracted_char_count=ext_chars,
        script_title=(title or "").strip(),
        chapter_count=len(chapters_raw or []),
        full_script_preview=(full_script or "")[:480],
    )
    gate = build_url_quality_gate_result(
        extraction_ok=True,
        extracted_text=extracted_text,
        narrative_ok=narrative_ok,
        script_title=(title or "").strip(),
        full_script=full_script or "",
        chapter_count=len(chapters_raw or []),
    )
    return outcome, gate


def finalize_manual_url_story_execution_result(
    outcome: ManualUrlRewriteOutcome,
    *,
    scene_prompt_count: int,
) -> ManualUrlStoryExecutionResult:
    """Erzeugt die additive API-Spur (15.0–15.4)."""
    intake_status: StepStatus = "ok" if outcome.intake_display_url else "blocked"
    ext_status: StepStatus = "ok" if outcome.extraction_ok else "blocked"
    nar_status: StepStatus
    if outcome.narrative_ok:
        nar_status = "ok"
    elif outcome.extraction_ok:
        nar_status = "blocked"
    else:
        nar_status = "skipped"

    asset_status: StepStatus = "ok" if scene_prompt_count > 0 else "blocked"
    demo_status: DemoStepStatus = "skipped"
    demo_notes: List[str] = []
    cmd: List[str] = []

    if nar_status == "ok" and asset_status == "ok":
        demo_status = "ready"
        cmd = ["python", "scripts/build_first_demo_video.py", "<image_url_or_path>"]
        demo_notes.append(
            "Benötigt Bild aus Manifest oder Leonardo-Live; Audio z. B. output/voice_smoke_test_output.mp3 "
            "(wie BA 15.0 Demo Video Automation)."
        )
    elif nar_status != "ok":
        demo_status = "blocked"
        demo_notes.append("Demo gesperrt — Narrativ aus URL nicht verfügbar.")

    return ManualUrlStoryExecutionResult(
        intake=ManualUrlIntakeStep(
            status=intake_status,
            source_url_display=outcome.intake_display_url,
        ),
        extraction=ManualUrlExtractionStep(
            status=ext_status,
            extracted_char_count=outcome.extracted_char_count,
            warnings=list(outcome.extraction_warnings),
        ),
        narrative_rewrite=ManualUrlNarrativeRewriteStep(
            status=nar_status,
            script_title=outcome.script_title,
            chapter_count=outcome.chapter_count,
            full_script_preview=outcome.full_script_preview,
            warnings=list(outcome.narrative_warnings),
        ),
        asset_prompt_build=ManualUrlAssetPromptStep(
            status=asset_status,
            scene_prompt_count=scene_prompt_count,
            notes=(
                ["scene_prompts aus Template × URL-Kapitel"]
                if asset_status == "ok"
                else ["Keine Szenen-Prompts erzeugt."]
            ),
        ),
        demo_video_execution=ManualUrlDemoVideoStep(
            status=demo_status,
            command_hint=cmd,
            notes=demo_notes,
        ),
    )
