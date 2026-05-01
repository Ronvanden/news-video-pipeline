"""BA 10.4 — statische Template-Registry für Founder-Selector (kein LLM, keine DB)."""

from __future__ import annotations

from typing import List

from app.models import TemplateRegistryItem

TEMPLATE_REGISTRY: List[TemplateRegistryItem] = [
    TemplateRegistryItem(
        template_id="generic",
        label="Generic / Standard",
        style="Neutral, erklärend; flexibel für gemischte Themen.",
        ideal_use_case="Allgemeine News-Erklärer, Einstieg ohne starren Genre-Zwang.",
        hook_bias="Sachlich, kontextorientiert; weniger dramatischer Zwang.",
        pacing_bias="Mittlere Kapitelbreite; Hook darf kürzer sein.",
    ),
    TemplateRegistryItem(
        template_id="true_crime",
        label="True Crime",
        style="Dokumentarisch, Spannungsbogen mit Faktenanker.",
        ideal_use_case="Fallrekonstruktionen, Ermittlungsverläufe, serielle Muster.",
        hook_bias="Shock-Reveal oder Zeit/Ort-Anker; hohe Template-Konformität erwartet.",
        pacing_bias="Längere investigative Kapitel; klare Wendepunkte.",
    ),
    TemplateRegistryItem(
        template_id="mystery_explainer",
        label="Mystery Explainer",
        style="Rätsel–Auflösung; offene Fragen, dann strukturierte Antworten.",
        ideal_use_case="Ungelöste Phänomene, Theorien-Vergleich, Evidenz-Stufen.",
        hook_bias="Offene Frage oder Paradox; moderate Dramatisierung.",
        pacing_bias="Wechsel zwischen Hypothese und Faktenblock.",
    ),
    TemplateRegistryItem(
        template_id="history_deep_dive",
        label="History Deep Dive",
        style="Chronologie, Kontext, Primärquellen-Hinweise.",
        ideal_use_case="Epochen, Biografien, langfristige Kausalketten.",
        hook_bias="Kontrast damals/heute oder unbekannte Wendung.",
        pacing_bias="Tiefere Kapitel, weniger Hektik als Breaking News.",
    ),
    TemplateRegistryItem(
        template_id="breaking_news",
        label="Breaking News",
        style="Kurz, aktuell, Fokus auf Was-ist-los-jetzt.",
        ideal_use_case="Eilmeldungen, Live-Kontext, schnelle Updates.",
        hook_bias="Direktansprache, Dringlichkeit; Hook sehr knapp.",
        pacing_bias="Kürzere Segmente, häufigere Kapitelwechsel.",
    ),
    TemplateRegistryItem(
        template_id="philosophy",
        label="Philosophy / Big Ideas",
        style="Abstraktionsfähig, Argumentationsketten, Definitionen.",
        ideal_use_case="Ethik, Gesellschaftstheorie, Konzeptvergleiche.",
        hook_bias="Paradox oder Gegenintuition; weniger Sensationsdruck.",
        pacing_bias="Langsamere Eskalation, mehr Reflexionspausen.",
    ),
]


def list_templates() -> List[TemplateRegistryItem]:
    """Öffentliche Übersicht (Reihenfolge stabil für UI)."""
    return list(TEMPLATE_REGISTRY)
