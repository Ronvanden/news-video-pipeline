## BA 27.3 — Continuity Display (V1)

### Ziel
Continuity-Daten aus BA 27.2 werden **operator-freundlich** sichtbar gemacht:
- Prompt Cards (pro Szene/Asset)
- Production Pack README / Textausgaben (Counts)

Keine Live-Uploads, keine Provider-API-Änderung.

### Implementierung
- Helper: `app/visual_plan/continuity_display.py`
- Dashboard: `app/founder_dashboard/html.py` zeigt eine Continuity-Zeile in Prompt Cards, falls Felder vorhanden
- Production Pack: `README_PRODUCTION_PACK.md` enthält Abschnitt „Continuity“, wenn `continuity_wiring_summary` vorhanden ist

