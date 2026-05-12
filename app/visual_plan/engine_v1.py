"""Visual Prompt Engine V1 skeleton.

Provider-neutral prompt preparation only: no API calls, no rendering, no
dashboard wiring. Existing production flows can adopt this module later.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Tuple
import unicodedata

from app.visual_plan.presets import get_visual_prompt_control_options, normalize_visual_prompt_controls
from app.visual_plan.prompt_formatters import anatomy_to_generic_prompt, anatomy_to_openai_image_prompt
from app.visual_plan.prompt_anatomy import (
    VisualPromptAnatomy,
    build_visual_prompt_anatomy,
    derive_visual_action,
    derive_visual_subject,
)
from app.visual_plan.visual_no_text import append_no_text_guard


_HOOK_VISUAL_LABEL = "cinematic opening beat"
_HOOK_NEGATIVE_GUARDS = (
    "no fishing hook",
    "no metal hook",
    "no literal hook object",
    "no hook-shaped object",
)


@dataclass(frozen=True)
class VisualPromptEngineContext:
    scene_title: str
    narration: str = ""
    video_template: str = ""
    beat_role: str = ""
    visual_preset: str | None = None
    prompt_detail_level: str | None = None
    provider_target: str | None = None
    text_safety_mode: str | None = None
    visual_consistency_mode: str | None = None
    existing_negative_prompt: str = ""


@dataclass(frozen=True)
class VisualPromptEngineResult:
    visual_prompt_raw: str
    visual_prompt_effective: str
    negative_prompt: str
    visual_policy_warnings: List[str] = field(default_factory=list)
    visual_style_profile: str = ""
    prompt_quality_score: int = 0
    prompt_risk_flags: List[str] = field(default_factory=list)
    normalized_controls: Dict[str, str] = field(default_factory=dict)
    visual_prompt_anatomy: Dict[str, Any] = field(default_factory=dict)


def _norm_space(s: str) -> str:
    return " ".join((s or "").split())


def _dedupe(items: List[str]) -> List[str]:
    out: List[str] = []
    seen: set[str] = set()
    for item in items:
        v = _norm_space(str(item or ""))
        if not v or v in seen:
            continue
        seen.add(v)
        out.append(v)
    return out


def _looks_like_internal_hook_title(title: str) -> bool:
    t = _norm_space(title).lower()
    if not t:
        return False
    t_ascii = "".join(
        ch for ch in unicodedata.normalize("NFKD", t) if not unicodedata.combining(ch)
    )
    t_ascii = (
        t_ascii.replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("ß", "ss")
        .replace("Ã¤", "ae")
        .replace("Ã¶", "oe")
        .replace("Ã¼", "ue")
        .replace("ÃŸ", "ss")
    )
    return t_ascii in {
        "hook",
        "the hook",
        "opening hook",
        "intro hook",
        "viral hook",
        "aufhanger",
        "aufhaenger",
        "auftakt-hook",
        "intro-hook",
    }


def _visual_title_and_guards(title: str, beat_role: str) -> Tuple[str, List[str], List[str]]:
    title_clean = _norm_space(title)
    role_clean = _norm_space(beat_role).lower()
    if _looks_like_internal_hook_title(title_clean) or _looks_like_internal_hook_title(role_clean):
        return _HOOK_VISUAL_LABEL, list(_HOOK_NEGATIVE_GUARDS), ["internal_term_sanitized:hook"]
    return title_clean, [], []


def _preset_by_id(preset_id: str) -> Dict[str, Any]:
    controls = get_visual_prompt_control_options()["controls"]
    for preset in controls["visual_presets"]:
        if preset.get("id") == preset_id:
            return dict(preset)
    return {}


def _control_payload(ctx: VisualPromptEngineContext) -> Dict[str, Any]:
    return {
        "visual_preset": ctx.visual_preset,
        "prompt_detail_level": ctx.prompt_detail_level,
        "provider_target": ctx.provider_target,
        "text_safety_mode": ctx.text_safety_mode,
        "visual_consistency_mode": ctx.visual_consistency_mode,
    }


def _negative_prompt_from_anatomy(anatomy: VisualPromptAnatomy) -> str:
    return "; ".join(_dedupe(list(anatomy.negative_constraints or [])))


def _raw_prompt_from_anatomy(
    *,
    anatomy: VisualPromptAnatomy,
    preset: Dict[str, Any],
    ctx: VisualPromptEngineContext,
    controls: Dict[str, str],
) -> Tuple[str, List[str]]:
    risk_flags: List[str] = []
    role_raw = _norm_space(ctx.beat_role)
    role = _HOOK_VISUAL_LABEL if _looks_like_internal_hook_title(role_raw) else (role_raw or "scene")

    if not anatomy.source_summary:
        risk_flags.append("sparse_narration")

    if not anatomy.subject_description and not anatomy.source_summary:
        risk_flags.append("generic_visual_fallback")

    formatter_controls: Dict[str, Any] = dict(controls)
    formatter_controls["visual_preset_label"] = str(preset.get("label") or "")
    formatter_controls["video_template"] = _norm_space(ctx.video_template) or "generic video"
    formatter_controls["beat_role"] = role
    if controls.get("provider_target") == "openai_image":
        return anatomy_to_openai_image_prompt(anatomy, formatter_controls), risk_flags
    return anatomy_to_generic_prompt(anatomy, formatter_controls), risk_flags


def _anatomy_risk_flags(anatomy: VisualPromptAnatomy) -> List[str]:
    flags: List[str] = []
    if not _norm_space(anatomy.subject_description):
        flags.append("subject_missing")
    if not _norm_space(anatomy.environment):
        flags.append("environment_missing")
    if not anatomy.negative_constraints:
        flags.append("negative_constraints_missing")
    if not _norm_space(anatomy.text_safety):
        flags.append("text_safety_missing")
    return flags


def _anatomy_enrichment_flags(
    ctx: VisualPromptEngineContext,
    visual_title: str,
    anatomy: VisualPromptAnatomy,
    controls: Dict[str, str],
) -> List[str]:
    flags: List[str] = []
    narration = _norm_space(ctx.narration)
    preset_id = controls.get("visual_preset", "")
    derived_subject = derive_visual_subject(
        visual_title,
        narration,
        ctx.video_template,
        preset_id,
    )
    if _norm_space(derived_subject) and _norm_space(derived_subject) != _norm_space(visual_title):
        flags.extend(["subject_was_headline", "visual_subject_derived"])
    if _norm_space(anatomy.environment) == "grounded documentary environment / editorial real-world setting":
        flags.append("environment_generic")
    derived_action = derive_visual_action(visual_title, narration, preset_id)
    if derived_action and _norm_space(derived_action) != _norm_space(anatomy.source_summary):
        flags.append("action_from_summary")
    elif anatomy.source_summary:
        flags.append("action_from_summary")
    return flags


def _quality_score(raw_prompt: str, negative_prompt: str, risk_flags: List[str], warnings: List[str]) -> int:
    score = 82
    if len(raw_prompt) < 140:
        score -= 12
    if len(raw_prompt) > 260:
        score += 5
    if negative_prompt:
        score += 5
    weight_by_flag = {
        "subject_was_headline": 0,
        "visual_subject_derived": 0,
        "action_from_summary": 0,
        "environment_generic": 4,
    }
    for flag in set(risk_flags):
        score -= weight_by_flag.get(flag, 10)
    score -= 4 * len(set(warnings))
    return max(0, min(100, score))


def build_visual_prompt_v1(context: VisualPromptEngineContext) -> VisualPromptEngineResult:
    """Build a deterministic V1 visual prompt skeleton result."""
    normalized_payload = normalize_visual_prompt_controls(_control_payload(context))
    controls = dict(normalized_payload.get("normalized") or {})
    warnings = list(normalized_payload.get("warnings") or [])

    visual_title, sanitizer_guards, sanitizer_warnings = _visual_title_and_guards(
        context.scene_title,
        context.beat_role,
    )
    warnings.extend(sanitizer_warnings)

    preset = _preset_by_id(controls.get("visual_preset", ""))
    style_profile = controls.get("visual_preset", "")
    anatomy = build_visual_prompt_anatomy(
        context=context,
        normalized_controls=controls,
        sanitized_title_or_label=visual_title,
        sanitizer_guards=sanitizer_guards,
        sanitizer_warnings=sanitizer_warnings,
        preset=preset,
    )
    raw_prompt, risk_flags = _raw_prompt_from_anatomy(
        anatomy=anatomy,
        preset=preset,
        ctx=context,
        controls=controls,
    )
    risk_flags.extend(_anatomy_risk_flags(anatomy))
    risk_flags.extend(_anatomy_enrichment_flags(context, visual_title, anatomy, controls))

    if "symbolic" in raw_prompt.lower() and not anatomy.source_summary:
        risk_flags.append("generic_visual_fallback")

    negative = _negative_prompt_from_anatomy(anatomy)
    effective = append_no_text_guard(raw_prompt)
    risk_flags = _dedupe(risk_flags)
    warnings = _dedupe(warnings)
    score = _quality_score(raw_prompt, negative, risk_flags, warnings)

    return VisualPromptEngineResult(
        visual_prompt_raw=raw_prompt,
        visual_prompt_effective=effective,
        negative_prompt=negative,
        visual_policy_warnings=warnings,
        visual_style_profile=style_profile,
        prompt_quality_score=score,
        prompt_risk_flags=risk_flags,
        normalized_controls=controls,
        visual_prompt_anatomy=asdict(anatomy),
    )
