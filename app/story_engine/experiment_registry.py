"""BA 9.6 — experimentelle Hook-/Template-Zuordnung (kein Pflichtteil der Live-Generate-API).

Varianten sind versionierte Konstanten für Persistenz/Nebenkanal; keine stillen Produktionsänderungen.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

_EXPERIMENT_ID_BASE = "exp_hook_ab_v1"

_REGISTRY: Tuple[Dict[str, Any], ...] = (
    {
        "id": "hv_doc_led_v1",
        "label": "Dokumentarischer Einstieg",
        "default_for_templates": frozenset({"history_deep_dive", "generic"}),
        "hook_type_tags": frozenset(
            {"authority_stat", "timeline_tease", "cold_open_facts"}
        ),
    },
    {
        "id": "hv_tension_arc_v1",
        "label": "Spannungsbogen ohne Sensationalismus",
        "default_for_templates": frozenset({"true_crime", "mystery_explainer"}),
        "hook_type_tags": frozenset({"shock_reveal", "mystery_hook", "case_frame"}),
    },
)


def public_experiment_registry() -> Dict[str, Any]:
    """Kompakte, exportierbare Meta-Liste (ohne Business-Secrets)."""
    return {
        "experiment_id": _EXPERIMENT_ID_BASE,
        "variants": [
            {
                "id": r["id"],
                "label": r["label"],
                "templates": sorted(r["default_for_templates"]),
            }
            for r in _REGISTRY
        ],
    }


def assign_hook_variant_and_experiment(
    *,
    video_template: str,
    hook_type: str,
) -> Tuple[str, str]:
    """Liefert (experiment_id, hook_variant_id)."""
    tid = (video_template or "").strip().lower().replace("-", "_")
    ht = (hook_type or "").strip().lower()

    picked = _REGISTRY[0]["id"]
    for row in _REGISTRY:
        if tid in row["default_for_templates"]:
            picked = row["id"]
            break
        if ht and ht in row["hook_type_tags"]:
            picked = row["id"]
            break
    return _EXPERIMENT_ID_BASE, picked
