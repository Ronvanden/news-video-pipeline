"""BA 9.2 — Hook-Typen und Satzschablonen (regelbasiert, kein LLM)."""

from __future__ import annotations

from typing import Dict, FrozenSet

# Pro Template erlaubte Hook-Typen (V1)
ALLOWED_HOOK_TYPES: Dict[str, FrozenSet[str]] = {
    "generic": frozenset({"generic_curiosity"}),
    "true_crime": frozenset({"shock_reveal", "hidden_truth"}),
    "mystery_explainer": frozenset({"unexplained_event", "question_gap"}),
    "history_deep_dive": frozenset({"forgotten_power", "timeline_twist"}),
    "documentary": frozenset({"forgotten_power", "timeline_twist"}),
}

HOOK_TEMPLATES_DE: Dict[str, str] = {
    "shock_reveal": (
        "Niemand rechnete mit dieser Wendung — doch bei {focus} rückt ein Detail "
        "in den Mittelpunkt, das alles neu einordnet."
    ),
    "hidden_truth": (
        "Was später ans Licht kam, stellte vieles auf den Kopf — "
        "vor allem rund um {focus}."
    ),
    "unexplained_event": (
        "Bis heute bleibt unklar, was sich hinter {focus} wirklich abgespielt hat — "
        "die Fakten ziehen einen Riss durch jede einfache Erklärung."
    ),
    "question_gap": (
        "Warum ausgerechnet {focus} — und welche Fragen blieben offen, "
        "obwohl alle danach suchten?"
    ),
    "forgotten_power": (
        "Dieses Gebäude an {focus} entschied einst über weit mehr "
        "als nur Stein und Farbe — seine Rolle geriet in Vergessenheit."
    ),
    "timeline_twist": (
        "Die Chronik kennt eine naheliegende Version — "
        "doch die Spuren um {focus} erzählen eine andere Geschichte."
    ),
    "generic_curiosity": (
        "Worauf es wirklich ankommt bei {focus} — "
        "ein Einstieg, der Kontext, Spannung und offene Punkte verbindet."
    ),
}


def opening_style_label(hook_type: str) -> str:
    """Kurzbeschreibung für Persistenz (`opening_style`)."""
    labels = {
        "shock_reveal": "Einstieg: Wendung / Enthüllung",
        "hidden_truth": "Einstieg: spätere Wahrheit",
        "unexplained_event": "Einstieg: ungeklärtes Ereignis",
        "question_gap": "Einstieg: Frage / Lücke",
        "forgotten_power": "Einstieg: vergessene Bedeutung (Ort)",
        "timeline_twist": "Einstieg: Chronik vs. Realität",
        "generic_curiosity": "Einstieg: Neugier / Kontext",
    }
    return labels.get(hook_type, f"Einstieg: {hook_type}")
