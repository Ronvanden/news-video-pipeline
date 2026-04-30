"""BA 9.3.3 — deterministischer Nebenkanal ``story_structure`` (nicht Teil von GenerateScriptResponse)."""

from __future__ import annotations

from typing import Any, Dict, List


def build_story_structure_v1(
    *,
    video_template: str,
    duration_minutes: int,
    chapters: List[Any],
    hook: str,
    word_count: int,
    template_definition_version: str,
    template_conformance_gate: str,
    rhythm_hints: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    chap = chapters or []
    roles: List[Dict[str, Any]] = []
    for i, ch in enumerate(chap):
        if isinstance(ch, dict):
            t = str(ch.get("title") or "")
        else:
            t = str(getattr(ch, "title", "") or "")
        if not (t or "").strip():
            t = f"Kapitel {i + 1}"
        roles.append(
            {
                "index": i,
                "chapter_title_hint": (t.strip())[:200],
                "role": _chapter_role(video_template, i, len(chap)),
            }
        )

    dm = max(1, int(duration_minutes))
    pacing = ""
    if roles:
        n = len(roles)
        secs = dm * 60 / n if n else 0
        lo = max(45, int(secs * 0.82))
        hi = max(lo + 1, int(secs * 1.22))
        pacing = (
            f"Orientierung: etwa {lo}–{hi} Sekunden verbaler Luft pro Hauptabschnitt "
            f"(~{dm} Min. Gesamtlaufzeit, keine harten Schnitt-Vorgaben)."
        )

    cta = (
        "CTA klar vor dem Schluss formulieren (letztes oder vorletztes Kapitel), "
        "nicht mittendrin im Twist."
        if len(chap) >= 4 or dm >= 10
        else "Kompaktes Format: kurze Einladung zur Diskussion/Recherche vor dem Schluss."
    )

    hook_words = len(((hook or "").strip()).split())

    payload: Dict[str, Any] = {
        "schema_version": "1",
        "video_template": video_template,
        "duration_minutes": dm,
        "hook_word_estimate": hook_words,
        "script_word_count": int(word_count),
        "chapter_roles": roles,
        "pacing_hints": pacing,
        "cta_placement_hint": cta,
        "meta": {
            "template_definition_version": template_definition_version or None,
            "template_conformance_gate": template_conformance_gate or None,
        },
    }
    if rhythm_hints:
        payload["rhythm"] = rhythm_hints
    return payload


def _chapter_role(tpl: str, index: int, total: int) -> str:
    tid = (tpl or "").strip().lower().replace("-", "_")
    if total <= 1:
        return "main_arc"
    if index == 0:
        mapping = {
            "true_crime": "cold_open_context",
            "mystery_explainer": "question_stake",
            "history_deep_dive": "chronological_anchor",
        }
        return mapping.get(tid, "intro_positioning")
    if index >= total - 1:
        return "resolution_outro"
    mids = {
        "true_crime": "timeline_evidence_cluster",
        "mystery_explainer": "claim_counterpoint_rotate",
        "history_deep_dive": "cause_consequence_deepening",
        "generic": "middle_development",
    }
    return mids.get(tid, "middle_development")
