"""BA 10.4 — Provider-Produktions-Readiness aus lokalem Export-Paket (keine APIs)."""

from __future__ import annotations

from typing import List, Tuple

from app.models import (
    ExportPackageResponse,
    ProviderPromptsBundle,
    ProviderReadinessResponse,
    ProviderReadinessScores,
    SceneExpandedPrompt,
)
from app.story_engine.export_package import _dedupe_warnings
from app.visual_plan.policy import SAFETY_NEGATIVE_SEGMENTS_V1


def _dedupe_str_list(items: List[str]) -> List[str]:
    return _dedupe_warnings(items)


def _neg_segments(neg: str) -> int:
    if not (neg or "").strip():
        return 0
    return len([x for x in neg.split(";") if x.strip()])


def _safety_coverage(neg: str) -> int:
    """Wie viele Safety-Segmente sind (substring) im Negativ vertreten."""
    low = (neg or "").lower()
    hit = 0
    for seg in SAFETY_NEGATIVE_SEGMENTS_V1:
        s = (seg or "").lower()
        if not s:
            continue
        if s in low or s.replace("_", " ") in low:
            hit += 1
    return hit


def _continuity_ok_for_bundle(
    scenes: List[SceneExpandedPrompt], continuity_lock: bool
) -> Tuple[bool, List[str]]:
    issues: List[str] = []
    if not continuity_lock or not scenes:
        return True, issues
    for ep in scenes:
        if int(ep.scene_number) > 1 and "Continuity_lock:" not in (ep.positive_expanded or ""):
            issues.append(f"continuity_gap_scene_{ep.scene_number}")
    return (len(issues) == 0), issues


def _score_bundle_openai(scenes: List[SceneExpandedPrompt], continuity_lock: bool) -> Tuple[int, List[str], List[str]]:
    blocking: List[str] = []
    warns: List[str] = []
    if not scenes:
        return 0, ["openai:no_scenes"], []
    base = 100
    for ep in scenes:
        pos = (ep.positive_expanded or "").strip()
        neg = (ep.negative_prompt or "").strip()
        if len(pos) < 120:
            base -= 12
            warns.append("openai:short_positive")
        if _neg_segments(neg) < 3:
            base -= 8
            warns.append("openai:sparse_negative")
        cov = _safety_coverage(neg)
        if cov < 2:
            base -= 10
            warns.append("openai:policy_negative_thin")
    ok, cissues = _continuity_ok_for_bundle(scenes, continuity_lock)
    if not ok:
        base -= 8 * len(cissues)
        warns.extend(cissues)
    if base < 50:
        blocking.append("openai:low_composite_score")
    return max(0, min(100, base)), _dedupe_str_list(blocking), _dedupe_str_list(warns)


def _score_bundle_leonardo(
    scenes: List[SceneExpandedPrompt], continuity_lock: bool
) -> Tuple[int, List[str], List[str]]:
    blocking: List[str] = []
    warns: List[str] = []
    if not scenes:
        return 0, ["leonardo:no_scenes"], []
    base = 100
    ok, cissues = _continuity_ok_for_bundle(scenes, continuity_lock)
    if not ok:
        base -= 10 * len(cissues)
        warns.extend(["leonardo:continuity"] + cissues)
    for ep in scenes:
        pos = (ep.positive_expanded or "").strip()
        neg = (ep.negative_prompt or "").strip()
        wc = len(pos.split())
        if len(pos) < 120:
            base -= 10
            warns.append("leonardo:placeholder_or_short_positive")
        if wc < 22:
            base -= 4
            warns.append("leonardo:low_visual_density")
        if _neg_segments(neg) < 4:
            base -= 5
            warns.append("leonardo:negative_visual_density_low")
    if base < 50:
        blocking.append("leonardo:low_composite_score")
    return max(0, min(100, base)), _dedupe_str_list(blocking), _dedupe_str_list(warns)


def _score_bundle_kling(
    scenes: List[SceneExpandedPrompt], continuity_lock: bool
) -> Tuple[int, List[str], List[str]]:
    blocking: List[str] = []
    warns: List[str] = []
    if not scenes:
        return 0, ["kling:no_scenes"], []
    base = 100
    ok, cissues = _continuity_ok_for_bundle(scenes, continuity_lock)
    if not ok:
        base -= 12 * len(cissues)
        warns.extend(["kling:scene_transition_continuity"] + cissues)
    for ep in scenes:
        pos = (ep.positive_expanded or "").strip()
        neg = (ep.negative_prompt or "").strip()
        low = pos.lower()
        if len(pos) < 130:
            base -= 14
            warns.append("kling:motion_prompt_short")
        if "cinematic" not in low and "video" not in low:
            base -= 6
            warns.append("kling:cinematic_hint_weak")
        if _neg_segments(neg) < 3:
            base -= 6
            warns.append("kling:negative_sparse")
    if base < 50:
        blocking.append("kling:low_composite_score")
    return max(0, min(100, base)), _dedupe_str_list(blocking), _dedupe_str_list(warns)


def _pick_recommended_step(scores: dict[str, int]) -> str:
    if not scores:
        return "review_export_warnings"
    if min(scores.values()) >= 80:
        return "ready_to_export"
    order = sorted(scores.items(), key=lambda kv: (kv[1], kv[0]))
    low_key = order[0][0]
    if low_key == "kling":
        return "upgrade_kling_motion_prompts"
    if low_key == "leonardo":
        return "upgrade_leonardo_visual_density"
    if low_key == "openai":
        return "upgrade_openai_prompt_completeness"
    return "review_export_warnings"


def analyze_provider_readiness(pkg: ExportPackageResponse) -> ProviderReadinessResponse:
    """Heuristische Produktions-Readiness für Leonardo, Kling, OpenAI (deterministisch)."""
    blueprint = pkg.scene_plan
    continuity_lock = bool(pkg.scene_prompts.continuity_lock_enabled)
    bundle: ProviderPromptsBundle = pkg.provider_prompts

    blocking_all: List[str] = []
    warns_all: List[str] = []

    if blueprint.status == "failed":
        blocking_all.append("blueprint:failed")
    if not blueprint.scenes:
        blocking_all.append("blueprint:no_scenes")

    s_leo, b_leo, w_leo = _score_bundle_leonardo(list(bundle.leonardo), continuity_lock)
    s_kli, b_kli, w_kli = _score_bundle_kling(list(bundle.kling), continuity_lock)
    s_oai, b_oai, w_oai = _score_bundle_openai(list(bundle.openai), continuity_lock)

    blocking_all.extend(b_leo + b_kli + b_oai)
    warns_all.extend(w_leo + w_kli + w_oai)

    for w in pkg.warnings or []:
        t = (w or "").strip()
        if t:
            warns_all.append(t)

    scores_model = ProviderReadinessScores(leonardo=s_leo, kling=s_kli, openai=s_oai)
    scores_map = scores_model.model_dump()
    blocking_all = _dedupe_str_list(blocking_all)
    warns_all = _dedupe_str_list(warns_all)

    min_score = min(scores_map.values()) if scores_map else 0
    if blocking_all and ("blueprint:failed" in blocking_all or "blueprint:no_scenes" in blocking_all):
        overall = "not_ready"
    elif min_score < 45:
        overall = "not_ready"
    elif min_score >= 80 and not blocking_all:
        overall = "ready"
    else:
        overall = "partial_ready"

    rec = _pick_recommended_step(scores_map)

    return ProviderReadinessResponse(
        overall_status=overall,
        scores=scores_model,
        blocking_issues=blocking_all,
        warnings=warns_all,
        recommended_next_step=rec,
    )
