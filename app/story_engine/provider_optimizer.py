"""BA 10.5 — Provider-Prompt-Optimierung und Shotlists (lokal, deterministisch)."""

from __future__ import annotations

import re
from typing import List, Tuple

from app.models import (
    CSVShotlistRow,
    CapCutShotlistRow,
    ExportPackageRequest,
    KlingMotionScenePrompt,
    OptimizedProviderScenePrompt,
    ProviderOptimizedPromptsBundle,
    ProviderPromptOptimizeResponse,
    SceneExpandedPrompt,
)
from app.story_engine.export_package import _dedupe_warnings, build_export_package_v1
from app.story_engine.thumbnail_ctr import build_thumbnail_variants

_LEO_REALISM = (
    "cinematic photoreal still, volumetric atmosphere, natural skin micro-detail, "
    "filmic contrast, editorial composition density"
)
_LEO_CONT = (
    "facial continuity hint: match anchor identity across scenes; wardrobe and "
    "environment palette carryover from scene_1 mood"
)
_LEO_STYLE = "depth haze controlled, practical-light realism, no on-image legible text"

_OPENAI_SAFE_PREFIX = (
    "Platform-safe editorial photograph: primary subject dominant foreground, "
    "readable hierarchy, neutral documentary tone"
)
_OPENAI_HIERARCHY = (
    "midground supporting context soft, background minimal clutter, single clear focal story"
)

_CAMERA_PATHS = (
    "dolly_in_slow",
    "static_hold_then_push_in",
    "lateral_pan_left_to_subject",
    "orbital_arc_clockwise_tight",
    "crane_down_reveal",
)

_MOTION_VERBS = (
    "measured cinematic energy",
    "controlled kinetic emphasis",
    "scene-forward momentum",
    "tension-building drift",
    "clarity-first motion cadence",
)


def _norm_space(s: str) -> str:
    return " ".join((s or "").split())


def _truncate(s: str, cap: int) -> str:
    t = _norm_space(s)
    if len(t) <= cap:
        return t
    return t[: cap - 1].rsplit(" ", 1)[0].strip() + "…"


_OAI_REPLACE = (
    (re.compile(r"\bgore\b", re.I), "stylised abstract tension"),
    (re.compile(r"\bblood\b", re.I), "muted documentary red accent"),
    (re.compile(r"\bnude\b", re.I), "fully_clothed_subject"),
    (re.compile(r"\bnudity\b", re.I), "non_explicit_styling"),
    (re.compile(r"\bkill\b", re.I), "conflict_event_reference"),
    (re.compile(r"\bmurder\b", re.I), "investigation_topic_reference"),
)


def _optimize_leonardo_scene(sp: SceneExpandedPrompt) -> OptimizedProviderScenePrompt:
    base = _norm_space(sp.positive_expanded or "")
    cont = _norm_space(sp.continuity_token or "")
    extra = f" {_LEO_CONT}: {cont}." if cont else f" {_LEO_CONT}."
    merged = _norm_space(f"{_LEO_REALISM}. {base} {extra} {_LEO_STYLE}")
    return OptimizedProviderScenePrompt(
        scene_number=int(sp.scene_number),
        positive_optimized=_truncate(merged, 920),
        negative_prompt=sp.negative_prompt or "",
        continuity_token=cont,
    )


def _optimize_openai_scene(sp: SceneExpandedPrompt) -> OptimizedProviderScenePrompt:
    text = _norm_space(sp.positive_expanded or "")
    for rx, rep in _OAI_REPLACE:
        text = rx.sub(rep, text)
    cont = _norm_space(sp.continuity_token or "")
    cont_chunk = f" continuity_anchor: {cont}." if cont else ""
    merged = _norm_space(
        f"{_OPENAI_SAFE_PREFIX}. {text} {_OPENAI_HIERARCHY}.{cont_chunk}"
    )
    return OptimizedProviderScenePrompt(
        scene_number=int(sp.scene_number),
        positive_optimized=_truncate(merged, 920),
        negative_prompt=sp.negative_prompt or "",
        continuity_token=cont,
    )


def _kling_motion_for_scene(
    idx: int,
    sp: SceneExpandedPrompt,
    transition_style: str,
    beat_label: str,
) -> KlingMotionScenePrompt:
    sn = int(sp.scene_number)
    path = _CAMERA_PATHS[idx % len(_CAMERA_PATHS)]
    verb = _MOTION_VERBS[idx % len(_MOTION_VERBS)]
    pos = _norm_space(sp.positive_expanded or "")
    motion = _norm_space(
        f"{verb}; camera {path}; subject readable; motion-safe cuts; beat:{beat_label or 'n/a'}"
    )
    th = _truncate(
        _norm_space(
            f"Pacing: hold {2 + (idx % 3)}s entrance, ease {1 + (idx % 2)}s exit. "
            f"Template rhythm: {transition_style or 'default_bridge'}"
        ),
        220,
    )
    return KlingMotionScenePrompt(
        scene_number=sn,
        motion_prompt=_truncate(motion, 420),
        camera_path=path,
        transition_hint=th,
        keyframe_positive=_truncate(pos, 480),
    )


def _beat_label_for_index(rhythm: dict, i: int) -> str:
    beats = (rhythm or {}).get("beats") if isinstance(rhythm, dict) else None
    if not isinstance(beats, list):
        return ""
    for b in beats:
        if isinstance(b, dict) and int(b.get("index", -10)) == i:
            return str(b.get("label") or "").strip()
    return ""


def _build_shotlists(
    leo_scenes: List[OptimizedProviderScenePrompt],
    kling_scenes: List[KlingMotionScenePrompt],
    chapter_titles: List[str],
) -> Tuple[List[CapCutShotlistRow], List[CSVShotlistRow]]:
    cap_rows: List[CapCutShotlistRow] = []
    csv_rows: List[CSVShotlistRow] = []
    n = max(len(leo_scenes), len(kling_scenes))
    for i in range(n):
        le = leo_scenes[i] if i < len(leo_scenes) else None
        km = kling_scenes[i] if i < len(kling_scenes) else None
        sn = int(le.scene_number if le else (km.scene_number if km else i + 1))
        label = ""
        if 0 <= i < len(chapter_titles):
            label = chapter_titles[i]
        if not label:
            label = f"Szene {sn}"
        vis = _truncate((le.positive_optimized if le else "") or "", 280)
        mot = _truncate((km.motion_prompt if km else ""), 200)
        note = _truncate((km.transition_hint if km else ""), 160)
        cap_rows.append(
            CapCutShotlistRow(
                scene_number=sn,
                scene_label=label,
                visual_prompt_excerpt=vis,
                motion_summary=mot,
                editor_note=note,
            )
        )
        csv_rows.append(
            CSVShotlistRow(
                scene_number=sn,
                scene_label=label,
                visual_prompt_excerpt=vis,
                motion_summary=mot,
                editor_note=note,
            )
        )
    return cap_rows, csv_rows


def optimize_provider_prompts(req: ExportPackageRequest) -> ProviderPromptOptimizeResponse:
    pkg = build_export_package_v1(req)
    warns = list(pkg.warnings or [])
    warns.append(
        "[provider_optimizer] BA 10.5 V1 — lokale String-Optimierung, keine Provider-API."
    )

    bundle = pkg.provider_prompts
    rhythm = pkg.rhythm if isinstance(pkg.rhythm, dict) else {}
    trans_style = str(rhythm.get("transition_style_hint") or "").strip()

    leo_opt = [_optimize_leonardo_scene(x) for x in (bundle.leonardo or [])]
    oai_opt = [_optimize_openai_scene(x) for x in (bundle.openai or [])]

    kling_out: List[KlingMotionScenePrompt] = []
    for i, sp in enumerate(bundle.kling or []):
        kling_out.append(
            _kling_motion_for_scene(
                i,
                sp,
                trans_style,
                _beat_label_for_index(rhythm, i),
            )
        )

    chapter_titles = [(c.title or "").strip() for c in (req.chapters or [])]
    capcut_rows, csv_rows = _build_shotlists(leo_opt, kling_out, chapter_titles)

    prof = (req.provider_profile or "openai").strip() or "openai"
    thumbs = build_thumbnail_variants(
        title=req.title,
        hook=(req.hook or "").strip() or pkg.hook.hook_text,
        video_template=req.video_template,
    )

    merged = _dedupe_warnings(warns)
    return ProviderPromptOptimizeResponse(
        provider_profile=prof,
        optimized_prompts=ProviderOptimizedPromptsBundle(
            leonardo=leo_opt,
            kling=kling_out,
            openai=oai_opt,
        ),
        thumbnail_variants=thumbs,
        capcut_shotlist=capcut_rows,
        csv_shotlist=csv_rows,
        warnings=merged,
    )
