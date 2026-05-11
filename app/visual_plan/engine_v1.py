"""Visual Prompt Engine V1 skeleton.

Provider-neutral prompt preparation only: no API calls, no rendering, no
dashboard wiring. Existing production flows can adopt this module later.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Dict, List, Tuple

from app.visual_plan.presets import get_visual_prompt_control_options, normalize_visual_prompt_controls
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
    t_ascii = t.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    return t_ascii in {
        "hook",
        "the hook",
        "opening hook",
        "intro hook",
        "viral hook",
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


def _narration_excerpt(narration: str, detail_level: str) -> str:
    text = _norm_space(narration)
    if not text:
        return ""
    cap = {"basic": 120, "enhanced": 260, "deep": 420}.get(detail_level, 260)
    if len(text) <= cap:
        return text
    return text[: max(1, cap - 3)].rsplit(" ", 1)[0].strip() + "..."


def _style_phrase(preset: Dict[str, Any], controls: Dict[str, str]) -> str:
    preset_label = str(preset.get("label") or controls.get("visual_preset") or "Visual Preset")
    tags = [str(t) for t in (preset.get("style_tags") or []) if str(t).strip()]
    if tags:
        return f"{preset_label}; style tags: {', '.join(tags[:5])}"
    return preset_label


def _negative_prompt(existing: str, preset: Dict[str, Any], guards: List[str]) -> str:
    parts: List[str] = []
    for source in [existing, "; ".join(str(t) for t in (preset.get("negative_tags") or [])), "; ".join(guards)]:
        for piece in re.split(r"[;,]", source or ""):
            p = _norm_space(piece)
            if p:
                parts.append(p)
    return "; ".join(_dedupe(parts))


def _raw_prompt(
    *,
    visual_title: str,
    narration_excerpt: str,
    style_phrase: str,
    ctx: VisualPromptEngineContext,
    controls: Dict[str, str],
) -> Tuple[str, List[str]]:
    risk_flags: List[str] = []
    title = visual_title or "untitled scene"
    template = _norm_space(ctx.video_template) or "generic video"
    role_raw = _norm_space(ctx.beat_role)
    role = _HOOK_VISUAL_LABEL if _looks_like_internal_hook_title(role_raw) else (role_raw or "scene")
    provider_target = controls.get("provider_target", "generic")
    consistency = controls.get("visual_consistency_mode", "one_style_per_video")

    if narration_excerpt:
        subject = narration_excerpt
    else:
        subject = "grounded editorial scene based on the scene title"
        risk_flags.append("sparse_narration")

    if not visual_title and not narration_excerpt:
        risk_flags.append("generic_visual_fallback")

    prompt = (
        f"{style_phrase}. Visual scene: {title}. Story context: {subject}. "
        f"Template: {template}. Beat role: {role}. "
        f"Composition: concrete editorial image, clear focal subject, believable environment, natural framing. "
        f"Provider target: {provider_target}. Consistency mode: {consistency}."
    )
    return _norm_space(prompt), risk_flags


def _quality_score(raw_prompt: str, negative_prompt: str, risk_flags: List[str], warnings: List[str]) -> int:
    score = 82
    if len(raw_prompt) < 140:
        score -= 12
    if len(raw_prompt) > 260:
        score += 5
    if negative_prompt:
        score += 5
    score -= 10 * len(set(risk_flags))
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
    style_phrase = _style_phrase(preset, controls)
    narration_excerpt = _narration_excerpt(context.narration, controls.get("prompt_detail_level", "enhanced"))
    raw_prompt, risk_flags = _raw_prompt(
        visual_title=visual_title,
        narration_excerpt=narration_excerpt,
        style_phrase=style_phrase,
        ctx=context,
        controls=controls,
    )

    if "symbolic" in raw_prompt.lower() and not narration_excerpt:
        risk_flags.append("generic_visual_fallback")

    negative = _negative_prompt(context.existing_negative_prompt, preset, sanitizer_guards)
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
    )
