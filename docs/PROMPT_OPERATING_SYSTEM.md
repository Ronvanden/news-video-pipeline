# Prompt Operating System (PPOS) V1

**BA 0.0 — Meta-Governance-Layer.** Dieses Dokument standardisiert zukünftige Bauphasen-Prompts. Es verändert keine Runtime, keine API-Verträge und keine Produktionspipeline.

## Zweck

PPOS V1 reduziert Wiederholung in Masterplan-Prompts. Statt jede Bauphase vollständig neu zu beschreiben, sollen zukünftige Anfragen aus **PPOS-Makros + Pattern + Delta** bestehen.

Beispiel:

```text
Use PPOS_GLOBAL_V1 + PPOS_ASSEMBLY + PPOS_FULL_SUITE.
Implement BA 13.0–13.3.
Focus: metadata + title + schedule + readiness.
```

## Global Prompt Ruleset V1

Diese Regeln gelten für alle zukünftigen Bauphasen, sofern der Nutzer sie nicht ausdrücklich überschreibt:

- **Additive only:** Neue Felder, Module und Tests bevorzugt additiv ergänzen.
- **No breaking changes unless explicit:** Keine Vertrags- oder Strukturbrüche ohne ausdrückliche Freigabe.
- **`GenerateScriptResponse` unchanged unless explicit:** Der feste Skript-Endpoint-Vertrag bleibt unverändert.
- **`python -m compileall app` mandatory:** Nach Änderungen ausführen.
- **`python -m pytest` mandatory:** Relevante Tests und am Ende die Suite ausführen.
- **`PIPELINE_PLAN.md` update mandatory:** Roadmap-Status und BA-Abgrenzung dokumentieren.
- **Docs updates mandatory:** Nutzerrelevante Governance-/Architekturänderungen dokumentieren.
- **Minimal-invasive:** Nur betroffene Module anfassen.
- **No external dependency unless explicit:** Keine neuen Packages ohne klare Anforderung.
- **No live API unless explicit:** Keine echten Provider-/HTTP-Calls ohne ausdrückliche Live-Freigabe.
- **No Firestore unless explicit:** Keine neuen Persistenz-Writes ohne Auftrag.
- **No frontend unless explicit:** Kein UI-Ausbau, wenn nicht verlangt.
- **Architecture-first:** Erst Contract, Flow, Safety, Tests; dann Implementierung.
- **Deterministic naming:** Bestehende Benennungen, Präfixe und Repo-Konventionen beibehalten.
- **Backward compatibility preferred:** Bestehende Tests und public Contracts bleiben grün.

## Prompt Execution Hierarchy

Bei Zielkonflikten gilt diese Reihenfolge:

1. **Global Rules** — PPOS, AGENTS, Nutzerregeln, Secret-Regeln, Vertragsgrenzen.
2. **Pattern** — z. B. Connector, Assembly, Publishing.
3. **Phase Delta** — konkrete BA-Nummern, neue Module, Felder und Ausnahmen.
4. **Tests** — Pflichtfälle, Regressionen, API-Felder.
5. **Docs** — `PIPELINE_PLAN.md`, README-Verweise, Runbooks oder Pattern-Dokumente.

## Prompt Compression Model

PPOS nutzt Makros als kanonische Kurzformen. Ein Makro ersetzt wiederkehrende Architektur- und Qualitätsanforderungen.

### `PPOS_GLOBAL_V1`

Aktiviert das **Global Prompt Ruleset V1** inklusive additivem Vorgehen, Compile-/Pytest-Pflicht, Plan-/Docs-Update, Secret-Disziplin und unverändertem `GenerateScriptResponse`.

### `PPOS_STANDARD_BA`

Aktiviert den Standard-Bausteinvertrag: Modul, Kernfunktion, Schema, Integration, Tests, Doku, Checks.

### `PPOS_FULL_SUITE`

Aktiviert den Multi-BA-Suite-Vertrag: mehrere Module, gemeinsamer Pipeline-Flow, API-Erweiterung, Test-Suite, `PIPELINE_PLAN.md`-Update.

### `PPOS_CONNECTOR`

Aktiviert Connector-Regeln: Safety-Gates, Dry-Run Default, Provider einzeln, Secrets nur Presence/Runtime-safe, keine echten Live-Calls ohne Flag.

### `PPOS_ASSEMBLY`

Aktiviert Assembly-Regeln: Asset-Manifest, Gruppierung, Timeline-Finalisierung, Voice/Scene-Alignment, Render-Instructions, Bundle, Human Review.

### `PPOS_PUBLISHING`

Aktiviert Publishing-Preparation-Regeln: keine Auto-Veröffentlichung, Upload-Readiness statt Upload, Metadaten-QA, Scheduling-Checks, Human Gate.

## Praktische Beispiele

### Alt

Ein vollständiger BA-Prompt beschreibt Regeln, Module, Flow, Tests und Doku erneut in mehreren tausend Tokens.

### Neu

```text
Use PPOS_GLOBAL_V1 + PPOS_FULL_SUITE + PPOS_PUBLISHING.
Implement BA 13.0–13.3.
Focus:
- metadata readiness
- title/description package
- scheduling contract
- publishing readiness gate
No upload, no frontend, no Firestore writes.
```

## Geltungsbereich

PPOS V1 ist ein **Bauwerkzeug**, kein Produktfeature. Es darf:

- neue Dokumentations- und Governance-Dateien definieren,
- Pattern und Makros standardisieren,
- zukünftige Masterplan-Prompts verkürzen.

PPOS V1 darf nicht:

- Runtime-Logik ändern,
- `ProductionPromptPlan` erweitern,
- API-Felder hinzufügen,
- Firestore, Frontend, Provider oder Publishing aktivieren.
