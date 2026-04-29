# Modul-Template

Kopiere diesen Abschnitt für ein **neues Pipeline-Modul** (Datei z. B. `docs/modules/<name>.md` oder als Issue/PR-Beschreibung) und fülle alle Felder aus, bevor Code geschrieben wird.

---

## Modulname

*(Kurzname, z. B. „Script Review API“)*

---

## Ziel

*(Ein Satz: Welches Nutzer- oder Pipeline-Problem löst das Modul?)*

---

## Scope

*(Was soll in der ersten Lieferung enthalten sein?)*

---

## Nicht-Ziele

*(Was bewusst ausgeschlossen ist — verhindert Scope-Creep.)*

---

## Dateien

| Pfad | Rolle |
|------|--------|
| *(z. B. `app/...`)* | *(neu / geändert)* |

---

## Endpoints

| Methode | Pfad | Request | Response | Vertrag stabil? |
|---------|------|---------|----------|-----------------|
| | | | | ja/nein |

*(Wenn bestehende Verträge wie `GenerateScriptResponse` berührt werden: explizite Abstimmung und Update von README/AGENTS.)*

---

## Datenmodell

*(Pydantic-Modelle, DB-Tabellen, Storage-Pfade — ohne Secrets.)*

---

## Akzeptanzkriterien

- [ ] *(messbar, z. B. „HTTP 200 + valides JSON bei …“)*  
- [ ] *(Fehlerpfad: keine 500 bei erwarteten Client-/Upstream-Fehlern)*  
- [ ] *(`warnings` oder gleichwertige Transparenz, falls zutreffend)*  

---

## Tests

| Test | Art (manuell / automatisch) | Befehl / Ablauf |
|------|-----------------------------|-----------------|
| | | |

**Minimum laut Projektregeln:** `python -m compileall app`; für API-Änderungen `GET /health` und relevante `POST`-Routes.

---

## Deployment

*(Cloud Run: neue Env-Vars? Secret Manager? Größeres Image? Keine Secrets hier dokumentieren — nur Namen der Variablen.)*

---

## Risiken

| Risiko | Mitigation |
|--------|------------|
| | |

---

## Abnahme

| Rolle | Name / Datum | OK |
|-------|----------------|-----|
| Technisch | | |
| Redaktion / Produkt | | |

---

## Verknüpfung Pipeline-Plan

**Phase:** *(Nummer und Name aus [PIPELINE_PLAN.md](PIPELINE_PLAN.md))*  

**Status nach Merge:** Phase-Status in `PIPELINE_PLAN.md` aktualisieren.
