# BA 9.8 — Story Intelligence Layer

Steckbrief für die umgesetzte Schicht (**read-only Hinweise**) — konsistent zu [MODULE_TEMPLATE.md](../../MODULE_TEMPLATE.md). Kanon: [PIPELINE_PLAN.md](../../PIPELINE_PLAN.md).

## Modulname

BA 9.8 Story Intelligence Layer

## Ziel

Aus bereits vorhandenen Stichprobe- und Aggregationssignalen **erklärbare operative Hinweise** liefern (Template-Verteilung, relative Gesundheit, keine Closed-Loop-Automatisierung).

## Scope

- Funktion **`build_story_engine_intelligence_summary`** (`story_intelligence_layer.py`).
- JSON-Felder unter **`ControlPanelStoryEngineSummary.story_intelligence`** und parallel unter **`StoryEngineTemplateHealthHttpResponse`** (`GET /story-engine/template-health`).

## Nicht-Ziele

- Kein automatisches Ändern von `generated_scripts` / Produktionsstatus.
- Kein echtes ML; **Self-Learning Readiness** nur als dokumentierte Aussagen.
- **`GenerateScriptResponse`** unberührt.

## Dateien

| Pfad | Rolle |
|------|--------|
| `app/story_engine/story_intelligence_layer.py` | Regeln/Komposition Hinweistexte |
| `app/watchlist/control_panel.py` | Einblendung Aggregat |
| `app/watchlist/service.py` | `get_story_engine_template_health_service` |
| `app/watchlist/models.py` | `StoryEngineIntelligenceSummary` |
| `tests/test_ba98_story_intelligence.py` | Regressions-Schutz |

## Akzeptanzkriterien

- Deterministische Tests auf Fixture-Stichprobe.
- Alle Prefixe konsistent **`[story_intelligence:…]`** oder Verweise darauf.

## Verknüpfung Pipeline-Plan

**BA 9.8** — Abschnitt in [PIPELINE_PLAN.md](../../PIPELINE_PLAN.md); Governance **BA 9 ≠ Phase 9/10**.
