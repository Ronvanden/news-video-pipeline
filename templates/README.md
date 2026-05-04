# Video Pipeline Templates

Diese Template-Bibliothek enthält wiederverwendbare Story- und Produktionsvorlagen für die Video-Pipeline.

Ziel:
Aus Themen, Artikeln, YouTube-Inputs oder Rohtexten sollen konsistente Videoformate entstehen – mit passender Erzählstruktur, Hook-Stil, Voice-Stil, Szenenstil, Thumbnail-Winkel und Sicherheitsregeln.

## Aktuelle Templates

### `true_crime.json`
Für True-Crime-ähnliche Geschichten mit dunkler, investigativer Spannung.

Geeignet für:
- Kriminalfälle
- mysteriöse Vorfälle
- ungelöste Fragen
- investigative Storys

Wichtig:
- Keine unbewiesenen Anschuldigungen
- Keine erfundenen Fakten
- Keine explizite Gewalt / kein Gore

---

### `mystery_history.json`
Für historische Rätsel, vergessene Orte und geheimnisvolle Ereignisse.

Geeignet für:
- verlassene Orte
- alte Gebäude
- regionale Geschichte
- historische Rätsel
- Straßen oder Orte mit ungewöhnlicher Vergangenheit

Wichtig:
- Fakten und Interpretation trennen
- Unsichere Details vorsichtig formulieren
- Keine erfundenen historischen Daten

---

### `emotional_story.json`
Für emotionale, menschliche Geschichten mit Wendepunkt und Lernmoment.

Geeignet für:
- Lebensgeschichten
- persönliche Veränderungen
- Rückschläge und Comebacks
- Motivation
- gesellschaftliche Geschichten

Wichtig:
- Nicht künstlich dramatisieren
- Kein Fake-Zeugnis erfinden
- Respektvoller Ton

---

### `documentary.json`
Neutraler Allrounder für sachliche, dokumentarische Erklärvideos.

Geeignet für:
- Erklärvideos
- Gesellschaft
- Technik
- Wirtschaft
- Geschichte
- Immobilien
- allgemeine Dokus

Wichtig:
- Neutral bleiben
- Fakten nicht überziehen
- Interpretation klar von Fakten trennen

---

### `real_estate_story.json`
Für Immobiliengeschichten mit Markt-, Wert-, Sanierungs- oder Transformationswinkel.

Geeignet für:
- Immobilienverkäufe
- Sanierungen
- Denkmalobjekte
- Luxusumbauten
- leerstehende Gebäude
- Marktveränderungen

Wichtig:
- Keine erfundenen Preise
- Keine erfundenen Eigentümerangaben
- Privatsphäre beachten

---

### `news_explainer.json`
Für Nachrichten-Erklärformate, nicht für hektische Breaking-News-Produktion.

Geeignet für:
- Artikel-News
- Verbraucher-Themen
- Politik-/Gesellschaftserklärungen mit Vorsicht
- Business-News
- Technologie-News
- Immobilien-News

Wichtig:
- Keine Spekulation als Fakt darstellen
- Quellenbasiert formulieren
- Unsicherheit klar nennen
- Kein Clickbait ohne Substanz

---

## Grundregel

Diese Templates sind keine fertigen Videos, sondern Produktionslogik.

Ein Template definiert:

- Erzählstil
- Hook-Stil
- Kapitelstruktur
- Voice-Stil
- Szenenstil
- Thumbnail-Winkel
- Sicherheitsregeln
- Negative Prompts

## Ziel für spätere Integration

Diese Dateien können später von Cursor/Codex in die echte Pipeline-Struktur übernommen werden, z. B.:

```txt
app/templates/prompt_planning/