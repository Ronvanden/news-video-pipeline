"""Deterministischer Scene‑Blueprint‑Builder (read-only aus Skript-/Kapitelstruktur)."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from app.models import StorySceneBlueprintRequest
from app.story_engine.templates import normalize_story_template_id
from app.visual_plan import warning_codes as vw
from app.visual_plan import policy as vp


_INTENT_CAP = 280
_SUBJECTS_CAP = 200
_PRIMARY_CAP = 512
_CHUNK_WORD_ALERT = 50


def _dedupe_warnings(ws: List[str]) -> List[str]:
    out: List[str] = []
    seen: set[str] = set()
    for w in ws:
        key = (w or "").strip()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(w)
    return out


def _norm_space(s: str) -> str:
    return " ".join((s or "").split())


def _word_count(text: str) -> int:
    if not (text or "").strip():
        return 0
    return len(re.findall(r"\w+", text, flags=re.UNICODE))


def _truncate(s: str, cap: int) -> Tuple[str, bool]:
    t = _norm_space(s)
    if len(t) <= cap:
        return t, False
    return t[: cap - 3].rsplit(" ", 1)[0].strip() + " …", True


def _tags_for_template(tmpl: str) -> List[str]:
    """Deterministische, sortierte Stil-Tags ohne externe Daten."""
    tid = normalize_story_template_id(tmpl)[0]
    bucket: Dict[str, List[str]] = {
        "generic": ["layout_clean", "neutral_tone"],
        "true_crime": ["documentary_visual", "muted_palette"],
        "mystery_explainer": ["clarity_first", "soft_contrast"],
        "history_deep_dive": ["archival_visual", "warm_grade"],
        "default": ["layout_clean"],
    }
    tags = bucket.get(tid, bucket["default"])
    return sorted(set(tags))


def _rhythm_label_for_scene(
    rhythm_hints: Dict[str, Any], scene_idx: int
) -> str:
    if not rhythm_hints:
        return ""
    beats = rhythm_hints.get("beats")
    if not isinstance(beats, list):
        return ""
    for b in beats:
        if not isinstance(b, dict):
            continue
        if int(b.get("index", -1)) == scene_idx:
            return str(b.get("label") or "").strip()
    return ""


def build_scene_blueprint_plan(req: StorySceneBlueprintRequest):
    """Baut Liste von Szene-Verträgen; keine Persistenz, keine Bild-API."""
    # Import unten cyclic-safe (response models in app.models)
    from app.models import (
        SceneBlueprintContract,
        SceneBlueprintPlanResponse,
        SceneBlueprintPromptPack,
    )

    warns_acc: List[str] = []

    tmpl_id, tmpl_warns = normalize_story_template_id(req.video_template or "generic")
    warns_acc.extend(tmpl_warns)


    chapters = list(req.chapters or [])
    if req.story_structure:
        warns_acc.append(
            f"{vw.W_STORY_META_READ} story_structure‑Schlüssel wurden nur registriert, "
            "nicht zur inhaltlichen Erweiterung des Blueprints verwendet."
        )

    rhythm = dict(req.rhythm_hints or {})
    if rhythm:
        warns_acc.append(
            f"{vw.W_RHYTHM_META_READ} rhythm_hints‑Metadaten nur lesend eingebunden."
        )

    if not chapters:
        warns_acc.append(f"{vw.W_NO_CHAPTERS} Keine Kapitel übergeben.")
        return SceneBlueprintPlanResponse(
            policy_profile=vp.VISUAL_POLICY_PROFILE_V1,
            plan_version=1,
            status="draft",
            scenes=[],
            warnings=_dedupe_warnings(warns_acc),
        )

    total_words = sum(
        max(1, _word_count(_norm_space(ch.title)) + _word_count(_norm_space(ch.content)))
        for ch in chapters
    )
    hook_w = _word_count(req.hook or "")

    if (req.full_script or "").strip():
        fw = _word_count(req.full_script or "")
        if fw > 0 and abs(fw - (total_words + hook_w)) > max(120, fw // 10):
            warns_acc.append(
                f"{vw.W_FULLSCRIPT_DRIFT} "
                "Volltext-Wortzahl weicht stark von Summe der Kapitel ab — "
                "Blueprint nur aus chapters abgeleitet."
            )

    scenes_out: List[SceneBlueprintContract] = []

    for i, ch in enumerate(chapters):
        sn = i + 1
        title = _norm_space(ch.title or "") or f"Kapitel {sn}"
        body = _norm_space(ch.content or "")

        intent_src = f"{title}. {body}"
        pacing = _rhythm_label_for_scene(rhythm, i)
        pacing_suffix = f" (pacing_hint:{pacing})" if pacing else ""
        intent_cap = max(32, _INTENT_CAP - len(pacing_suffix))
        intent, truncated_i = _truncate(intent_src, intent_cap)
        if pacing_suffix:
            intent = intent + pacing_suffix
        if truncated_i:
            warns_acc.append(
                f"{vw.W_TRUNCATED} Szene {sn}: intent gekürzt (Cap {_INTENT_CAP})."
            )

        subjects_src = f"{title} — {body[:300]}"
        subjects, truncated_s = _truncate(subjects_src, _SUBJECTS_CAP)
        if truncated_s:
            warns_acc.append(
                f"{vw.W_TRUNCATED} Szene {sn}: subjects_safe gekürzt (Cap {_SUBJECTS_CAP})."
            )

        wc_scene = _word_count(body)
        risk: List[str] = []
        if wc_scene < _CHUNK_WORD_ALERT:
            risk.append("sparse_chapter")
            warns_acc.append(
                f"{vw.W_SPARSE_CHAPTER} Szene {sn}: wenig VO-Text unterhalb Schwellwert {_CHUNK_WORD_ALERT}."
            )

        prefix = (
            f"Establishing illustrative frame aligned to template `{tmpl_id}`, "
            f"emphasising chapter semantics without inventing factual detail: "
        )
        primary_body = _norm_space(f"{title}. Focus: {_truncate(body, 380)[0]}")
        image_primary_full = prefix + primary_body
        img_primary, tr_p = _truncate(image_primary_full, _PRIMARY_CAP)
        if tr_p:
            warns_acc.append(
                f"{vw.W_TRUNCATED} Szene {sn}: image_primary gekürzt (Cap {_PRIMARY_CAP})."
            )

        licensing = vp.LICENSING_NOTE_V1
        licensing_l, tr_l = _truncate(licensing, 420)
        if tr_l:
            warns_acc.append(
                f"{vw.W_TRUNCATED} Szene {sn}: licensing_notes gekürzt."
            )

        redaction: List[str] = []
        if not body:
            redaction.append("chapter_content_empty_visual_placeholder_only")

        scenes_out.append(
            SceneBlueprintContract(
                scene_number=sn,
                intent=intent,
                subjects_safe=subjects,
                style_tags=_tags_for_template(tmpl_id),
                source_class="synthetic_placeholder",
                risk_flags=risk,
                prompt_pack=SceneBlueprintPromptPack(
                    image_primary=img_primary,
                    negative_hints=vp.NEGATIVE_HINTS_DEFAULT_V1,
                ),
                licensing_notes=licensing_l,
                redaction_warnings=redaction,
            )
        )

    warns_acc.append(f"{vw.W_NO_LEGAL_CLAIM} Keine automatischen Stock-/Urheber-Freistellungen.")
    merged = _dedupe_warnings(warns_acc)

    return SceneBlueprintPlanResponse(
        policy_profile=vp.VISUAL_POLICY_PROFILE_V1,
        plan_version=1,
        status="ready",
        scenes=scenes_out,
        warnings=merged,
    )
