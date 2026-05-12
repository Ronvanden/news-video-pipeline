"""Structured prompt anatomy for Visual Prompt Engine V1.

This module is deterministic and provider-neutral. It prepares structured
prompt parts that can later be formatted for different image or motion targets.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
import unicodedata
from typing import Any, Dict, List


@dataclass(frozen=True)
class VisualPromptAnatomy:
    subject_description: str = ""
    action: str = ""
    environment: str = ""
    camera: str = ""
    lighting: str = ""
    mood: str = ""
    composition: str = ""
    style_tags: List[str] = field(default_factory=list)
    continuity: str = ""
    text_safety: str = ""
    negative_constraints: List[str] = field(default_factory=list)
    sanitized_terms: List[str] = field(default_factory=list)
    source_summary: str = ""


@dataclass(frozen=True)
class MotionPromptAnatomy:
    motion_intent: str = ""
    camera_motion: str = ""
    subject_motion: str = ""
    background_motion: str = ""
    scene_evolution: str = ""
    pacing: str = ""
    transition_hint: str = ""
    duration_hint: str = ""
    stability_constraints: List[str] = field(default_factory=list)
    motion_negative_constraints: List[str] = field(default_factory=list)


def _norm_space(value: str) -> str:
    return " ".join(str(value or "").split())


def _dedupe(items: List[str]) -> List[str]:
    out: List[str] = []
    seen: set[str] = set()
    for item in items:
        value = _norm_space(item)
        if not value or value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def _split_negative_segments(value: str) -> List[str]:
    parts: List[str] = []
    for piece in re.split(r"[;,]", value or ""):
        part = _norm_space(piece)
        if part:
            parts.append(part)
    return parts


def _source_summary(narration: str, detail_level: str) -> str:
    text = _norm_space(narration)
    if not text:
        return ""
    cap = {"basic": 120, "enhanced": 260, "deep": 420}.get(detail_level, 260)
    if len(text) <= cap:
        return text
    return text[: max(1, cap - 3)].rsplit(" ", 1)[0].strip() + "..."


def _search_key(value: str) -> str:
    text = _norm_space(value).lower()
    replacements = {
        "\u00e4": "ae",
        "\u00f6": "oe",
        "\u00fc": "ue",
        "\u00df": "ss",
        "\u00c3\u00a4": "ae",
        "\u00c3\u00b6": "oe",
        "\u00c3\u00bc": "ue",
        "\u00c3\u009f": "ss",
    }
    for raw, repl in replacements.items():
        text = text.replace(raw, repl)
    return "".join(
        ch for ch in unicodedata.normalize("NFKD", text) if not unicodedata.combining(ch)
    )


def _contains_any(text: str, needles: List[str]) -> bool:
    haystack = _search_key(text)
    return any(_search_key(needle) in haystack for needle in needles)


def _looks_like_abstract_headline(title: str) -> bool:
    text = _search_key(title)
    if not text:
        return False
    if text == "cinematic opening beat":
        return False
    question_markers = ["?", "warum ", "wieso ", "weshalb ", "wie ", "why ", "how "]
    abstract_markers = [
        "vertrauen",
        "misstrauen",
        "experten",
        "gesellschaft",
        "bröckelt",
        "broeckelt",
        "plötzlich",
        "ploetzlich",
        "angst",
        "unsicherheit",
        "fakten",
        "krise",
        "health",
        "expert",
        "citizen",
        "society",
        "trust",
        "regierung",
        "bevoelkerung",
        "preise",
        "familien",
        "ermittlerin",
        "rekonstruiert",
        "verlassenes dorf",
        "vater",
        "tochter",
    ]
    if any(marker in text for marker in question_markers):
        return True
    return len(text.split()) >= 3 and _contains_any(text, abstract_markers)


def _should_derive_visual_subject(scene_title: str, narration: str, video_template: str, visual_preset: str) -> bool:
    title = _norm_space(scene_title)
    if not title:
        return True
    if _search_key(title) == "cinematic opening beat":
        return False
    combined = f"{title} {_norm_space(narration)} {_norm_space(video_template)} {_norm_space(visual_preset)}"
    domain_markers = [
        "vertrauen",
        "misstrauen",
        "experten",
        "gesundheit",
        "gesundheitsfall",
        "buerger",
        "gesellschaft",
        "health",
        "expert",
        "citizen",
        "society",
        "trust",
        "public",
        "regierung",
        "government",
        "presse",
        "press",
        "bevoelkerung",
        "preise",
        "price",
        "inflation",
        "familie",
        "familien",
        "ermittlerin",
        "ermittler",
        "investigator",
        "rekonstruiert",
        "hinweise",
        "verlassen",
        "dorf",
        "bergdorf",
        "berge",
        "mountain",
        "village",
        "vater",
        "tochter",
        "father",
        "daughter",
        "kuechentisch",
    ]
    return _looks_like_abstract_headline(title) or (len(title.split()) >= 3 and _contains_any(combined, domain_markers))


def derive_visual_subject(scene_title: str, narration: str, video_template: str, visual_preset: str) -> str:
    """Derive a concrete visual subject without inventing specific facts."""
    title = _norm_space(scene_title)
    if not _should_derive_visual_subject(title, narration, video_template, visual_preset):
        return title or "a grounded documentary subject representing the scene topic"

    combined = f"{title} {_norm_space(narration)} {_norm_space(video_template)} {_norm_space(visual_preset)}"
    if _contains_any(combined, ["vater", "tochter", "father", "daughter", "kuechentisch"]):
        return "a father and daughter seated at a modest kitchen table during a quiet crisis conversation"
    if _contains_any(combined, ["preise", "price", "inflation", "familie", "familien", "einkauf", "rechnungen", "kosten"]):
        return "a worried parent reviewing grocery receipts with family at a modest kitchen table"
    if _contains_any(combined, ["ermittlerin", "ermittler", "investigator", "rekonstruiert", "hinweise", "true crime"]):
        return "a focused investigator reconstructing an evening timeline in a quiet investigation office"
    if _contains_any(combined, ["verlassen", "dorf", "bergdorf", "berge", "mountain village", "abandoned village"]):
        return "an empty abandoned mountain village street with shuttered houses and no symbolic props"
    if _contains_any(combined, ["regierung", "government", "politik", "policy", "presse", "press", "bevoelkerung"]):
        return "a government spokesperson facing skeptical citizens in a real press briefing room"
    if _contains_any(
        combined,
        [
            "gesundheit",
            "health",
            "experten",
            "expert",
            "public health",
            "gesundheitsfall",
            "arzt",
            "ärzt",
            "doctor",
            "wissenschaft",
            "scientist",
        ],
    ):
        return "a calm public health expert in a realistic documentary setting"
    if _contains_any(
        combined,
        ["vertrauen", "misstrauen", "bürger", "buerger", "citizen", "gesellschaft", "public", "community"],
    ):
        return "concerned citizens in a quiet public information environment"
    if _contains_any(combined, ["politik", "policy", "regierung", "government", "news", "press"]):
        return "a grounded civic news subject in a realistic documentary setting"
    return "a grounded documentary subject representing the scene topic"


def derive_visual_environment(scene_title: str, narration: str, visual_preset: str) -> str:
    """Derive a concrete but conservative environment for prompt anatomy."""
    combined = f"{_norm_space(scene_title)} {_norm_space(narration)} {_norm_space(visual_preset)}"
    if _contains_any(combined, ["ermittlerin", "ermittler", "investigator", "rekonstruiert", "hinweise", "true crime"]):
        return "quiet investigation office with unlabelled evidence photos, a desk, and muted practical light"
    if _contains_any(combined, ["verlassen", "dorf", "bergdorf", "berge", "mountain village", "abandoned village"]):
        return "abandoned mountain village street with weathered houses and distant alpine slopes"
    if _contains_any(combined, ["vater", "tochter", "father", "daughter", "kuechentisch"]):
        return "modest family kitchen with a small table and everyday household details"
    if _contains_any(combined, ["preise", "price", "inflation", "familie", "familien", "einkauf", "rechnungen", "kosten"]):
        return "modest family kitchen or small apartment dining table with groceries and receipts"
    if _contains_any(combined, ["regierung", "government", "politik", "policy", "presse", "press", "bevoelkerung"]):
        return "real press briefing room or municipal hallway with citizens and reporters in the background"
    if _contains_any(
        combined,
        [
            "gesundheit",
            "health",
            "experten",
            "expert",
            "public health",
            "gesundheitsfall",
            "arzt",
            "ärzt",
            "doctor",
            "wissenschaft",
            "scientist",
            "bürger",
            "buerger",
            "citizen",
        ],
    ):
        return "modern public information room or municipal hallway"
    if _contains_any(combined, ["politik", "policy", "regierung", "government", "news", "press", "civic"]):
        return "realistic press or civic environment"
    if _contains_any(combined, ["mystery", "dark_mystery"]):
        return "restrained real-world interior with low-key documentary atmosphere"
    return "grounded documentary environment / editorial real-world setting"


def derive_visual_action(scene_title: str, narration: str, visual_preset: str) -> str:
    """Turn summary text into a short visual moment instead of copying it wholesale."""
    combined = f"{_norm_space(scene_title)} {_norm_space(narration)} {_norm_space(visual_preset)}"
    if _contains_any(combined, ["vater", "tochter", "father", "daughter", "kuechentisch"]):
        return "the father explains calmly while his daughter listens, both framed with restrained emotion"
    if _contains_any(combined, ["preise", "price", "inflation", "familie", "familien", "einkauf", "rechnungen", "kosten"]):
        return "a parent compares receipts and groceries while the family sits quietly nearby"
    if _contains_any(combined, ["ermittlerin", "ermittler", "investigator", "rekonstruiert", "hinweise", "true crime"]):
        return "the investigator studies unlabelled evidence photos and reconstructs the sequence of events"
    if _contains_any(combined, ["verlassen", "dorf", "bergdorf", "berge", "mountain village", "abandoned village"]):
        return "the empty street holds still, with weathered homes and mountain light creating quiet unease"
    if _contains_any(combined, ["regierung", "government", "politik", "policy", "presse", "press", "bevoelkerung"]):
        return "the spokesperson addresses the room while skeptical citizens and reporters listen in soft background"
    if _contains_any(combined, ["experten", "expert", "gesundheit", "health", "public health"]):
        return "the expert calmly explains while concerned citizens listen in the background"
    if _contains_any(combined, ["vertrauen", "misstrauen", "bürger", "buerger", "citizen", "gesellschaft"]):
        return "concerned citizens listen and exchange cautious looks in a public setting"
    if _contains_any(combined, ["politik", "policy", "regierung", "government", "press", "news"]):
        return "a civic briefing unfolds while people listen attentively"

    source = _norm_space(narration)
    if not source:
        return ""
    first_sentence = re.split(r"(?<=[.!?])\s+", source, maxsplit=1)[0]
    if len(first_sentence) > 150:
        first_sentence = first_sentence[:147].rsplit(" ", 1)[0].strip() + "..."
    return first_sentence


def _camera_for(preset_id: str, detail_level: str) -> str:
    if preset_id == "documentary_realism":
        if detail_level == "deep":
            return "35mm documentary lens feel, eye-level medium shot, shallow depth of field but realistic, deliberate focal hierarchy"
        return "35mm documentary lens feel, eye-level medium shot, shallow depth of field but realistic"
    if preset_id == "clean_news_explainer":
        return "clean editorial medium-wide frame"
    if preset_id == "dark_mystery":
        return "controlled cinematic frame with restrained slow tension"
    if preset_id == "minimal_symbolic":
        return "static minimal composition with one clear focal object"
    if detail_level == "basic":
        return "clear editorial frame"
    if detail_level == "deep":
        return "grounded documentary frame with deliberate focal hierarchy"
    return "natural editorial frame with clear focal subject"


def _lighting_for(preset_id: str) -> str:
    if preset_id == "documentary_realism":
        return "soft directional natural light, subtle cinematic contrast, no theatrical color cast"
    if preset_id == "dark_mystery":
        return "low-key muted lighting"
    if preset_id == "cinematic_story":
        return "cinematic naturalistic lighting with controlled contrast"
    if preset_id == "clean_news_explainer":
        return "bright neutral newsroom-style lighting"
    if preset_id == "emotional_human_story":
        return "soft natural light"
    if preset_id == "minimal_symbolic":
        return "simple soft studio-like light"
    return "natural light"


def _mood_for(preset_id: str, video_template: str, scene_title: str = "", narration: str = "") -> str:
    template = _norm_space(video_template).lower()
    combined = f"{_norm_space(scene_title)} {_norm_space(narration)} {template}"
    if preset_id == "documentary_realism":
        if _contains_any(combined, ["ermittlerin", "ermittler", "investigator", "rekonstruiert", "hinweise", "true crime"]):
            return "investigative, tense but grounded, restrained documentary realism"
        if _contains_any(combined, ["verlassen", "dorf", "bergdorf", "berge", "mountain village", "abandoned village"]):
            return "restrained mystery, quiet unease, grounded documentary realism"
        if _contains_any(combined, ["vater", "tochter", "father", "daughter", "kuechentisch"]):
            return "emotional restraint, protective family intimacy, grounded documentary realism"
        if _contains_any(combined, ["preise", "price", "inflation", "familie", "familien", "einkauf", "rechnungen", "kosten"]):
            return "quiet financial uncertainty, restrained family stress, grounded documentary realism"
        if _contains_any(combined, ["regierung", "government", "politik", "policy", "presse", "press", "bevoelkerung"]):
            return "public scrutiny, quiet civic tension, grounded documentary realism"
        return "observational documentary realism, quiet uncertainty, emotionally restrained"
    if preset_id == "dark_mystery" or "mystery" in template:
        return "restrained tension"
    if preset_id == "emotional_human_story":
        return "empathetic and grounded"
    if preset_id == "clean_news_explainer":
        return "clear and neutral"
    if preset_id == "minimal_symbolic":
        return "quiet and symbolic"
    return "grounded documentary realism"


def _composition_for(text_safety_mode: str, preset_id: str = "") -> str:
    is_doc_real = preset_id == "documentary_realism"
    if text_safety_mode == "overlay_friendly":
        if is_doc_real:
            return (
                "clear foreground subject, midground context, softly defocused background, subject slightly off-center, "
                "clean negative space for later title overlay"
            )
        return "concrete editorial image, clear focal subject, believable environment, clean negative space for later overlay"
    if text_safety_mode == "strict_no_text":
        if is_doc_real:
            return (
                "clear foreground subject, midground context, softly defocused background, subject slightly off-center, "
                "clean negative space for later title overlay, natural framing, no generated text"
            )
        return "concrete editorial image, clear focal subject, believable environment, natural framing, no generated text"
    if is_doc_real:
        return (
            "clear foreground subject, midground context, softly defocused background, subject slightly off-center, "
            "clean negative space for later title overlay, natural framing"
        )
    return "concrete editorial image, clear focal subject, believable environment, natural framing"


def _text_safety_for(text_safety_mode: str) -> str:
    if text_safety_mode == "overlay_friendly":
        return "leave clean empty space for later editorial text overlay"
    if text_safety_mode == "strict_no_text":
        return "no readable text, no letters, no fake UI, no logo, no typography"
    return "avoid readable generated text"


def _camera_motion_from_hint(motion_hint: str) -> str:
    hint = _norm_space(motion_hint).lower()
    if not hint:
        return "slow controlled push-in"
    if "static" in hint or "lock-off" in hint:
        return "static locked-off frame with minimal drift"
    if "pan" in hint:
        return "subtle controlled pan"
    if "handheld" in hint:
        return "gentle handheld documentary drift"
    if "push" in hint or "push-in" in hint:
        return "slow controlled push-in"
    return _norm_space(motion_hint)


def build_visual_prompt_anatomy(
    *,
    context: Any,
    normalized_controls: Dict[str, str],
    sanitized_title_or_label: str,
    sanitizer_guards: List[str],
    sanitizer_warnings: List[str] | None = None,
    preset: Dict[str, Any] | None = None,
) -> VisualPromptAnatomy:
    """Build structured prompt anatomy from context and normalized operator controls."""
    controls = dict(normalized_controls or {})
    preset_data = dict(preset or {})
    preset_id = controls.get("visual_preset", "")
    detail_level = controls.get("prompt_detail_level", "enhanced")
    text_safety_mode = controls.get("text_safety_mode", "strict_no_text")
    consistency_mode = controls.get("visual_consistency_mode", "one_style_per_video")

    title = _norm_space(sanitized_title_or_label)
    narration = _norm_space(getattr(context, "narration", "") or "")
    source = _source_summary(narration, detail_level)
    style_tags = [str(t) for t in (preset_data.get("style_tags") or []) if str(t).strip()]
    visual_subject = derive_visual_subject(
        title,
        narration,
        getattr(context, "video_template", "") or "",
        preset_id,
    )
    visual_environment = derive_visual_environment(title, narration, preset_id)
    visual_action = derive_visual_action(title, narration, preset_id) or source

    negative_constraints: List[str] = []
    negative_constraints.extend(str(t) for t in (preset_data.get("negative_tags") or []) if str(t).strip())
    negative_constraints.extend(sanitizer_guards or [])
    negative_constraints.extend(_split_negative_segments(getattr(context, "existing_negative_prompt", "") or ""))
    if text_safety_mode == "strict_no_text":
        negative_constraints.extend(["no readable text", "no letters", "no fake UI", "no logo", "no typography"])
    elif text_safety_mode == "overlay_friendly":
        negative_constraints.extend(["no rendered text", "no cluttered frame", "preserve clean negative space"])
    elif text_safety_mode == "normal":
        negative_constraints.append("avoid readable generated text")

    sanitized_terms = [w for w in (sanitizer_warnings or []) if str(w).strip()]

    return VisualPromptAnatomy(
        subject_description=visual_subject,
        action=visual_action,
        environment=visual_environment,
        camera=_camera_for(preset_id, detail_level),
        lighting=_lighting_for(preset_id),
        mood=_mood_for(
            preset_id,
            getattr(context, "video_template", "") or "",
            title,
            narration,
        ),
        composition=_composition_for(text_safety_mode, preset_id),
        style_tags=_dedupe(style_tags),
        continuity=(
            "use one consistent visual style across the video"
            if consistency_mode == "one_style_per_video"
            else ("allow scene-specific visual emphasis" if consistency_mode == "scene_specific" else "allow experimental variation")
        ),
        text_safety=_text_safety_for(text_safety_mode),
        negative_constraints=_dedupe(negative_constraints),
        sanitized_terms=_dedupe(sanitized_terms),
        source_summary=source,
    )


def build_motion_prompt_anatomy(
    visual_anatomy: VisualPromptAnatomy,
    context: Any = None,
    normalized_controls: Dict[str, str] | None = None,
    motion_hint: str = "",
    duration_seconds: int | None = None,
) -> MotionPromptAnatomy:
    """Build a deterministic motion anatomy for future provider-specific formatters."""
    controls = dict(normalized_controls or {})
    detail_level = controls.get("prompt_detail_level", "enhanced")
    duration_value = int(duration_seconds) if duration_seconds is not None else 0
    source_summary = _norm_space(getattr(visual_anatomy, "source_summary", "") or "")
    subject = _norm_space(getattr(visual_anatomy, "subject_description", "") or "")

    if source_summary:
        motion_intent = f"animate the provided image with grounded documentary motion based on: {source_summary}"
    elif subject:
        motion_intent = f"animate the provided image with grounded documentary motion around {subject}"
    else:
        motion_intent = "animate the provided image with grounded documentary motion"

    pacing = "calm documentary pacing"
    if detail_level == "deep":
        pacing = "calm deliberate documentary pacing"

    transition_hint = "maintain the same shot without a cut"
    if duration_value >= 10:
        transition_hint = "hold the same shot and evolve attention gently over the clip"

    return MotionPromptAnatomy(
        motion_intent=motion_intent,
        camera_motion=_camera_motion_from_hint(motion_hint),
        subject_motion="minimal natural subject movement",
        background_motion="subtle ambient background movement only",
        scene_evolution="no scene change, attention evolves within the provided image",
        pacing=pacing,
        transition_hint=transition_hint,
        duration_hint="10 seconds" if duration_value >= 10 else "5 seconds",
        stability_constraints=_dedupe(
            [
                "preserve subject identity",
                "preserve composition",
                "preserve lighting",
                "preserve spatial layout",
            ]
        ),
        motion_negative_constraints=_dedupe(
            [
                "no scene cut",
                "no new objects",
                "no text morphing",
                "no warped faces",
                "no object drift",
                "no sudden camera shake",
            ]
        ),
    )
