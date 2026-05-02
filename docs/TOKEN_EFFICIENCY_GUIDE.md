# Token Efficiency Guide

Dieses Dokument beschreibt, wie PPOS V1 zukünftige Masterplan-Prompts verkürzt, ohne Architektur- oder Testdisziplin zu verlieren.

## Difference-Only Prompting

Beschreibe künftig nur noch die Abweichung vom kanonischen Pattern.

Statt:

```text
Baue Module, Schemas, Pipeline, Tests, Doku, keine Dependencies, keine Secrets...
```

Nutze:

```text
Use PPOS_GLOBAL_V1 + PPOS_FULL_SUITE + PPOS_ASSEMBLY.
Delta: BA 12.7 adds editorial QA manifest.
```

## Macro Prompting

Makros ersetzen wiederkehrende Regelblöcke:

- `PPOS_GLOBAL_V1`
- `PPOS_STANDARD_BA`
- `PPOS_FULL_SUITE`
- `PPOS_CONNECTOR`
- `PPOS_ASSEMBLY`
- `PPOS_PUBLISHING`

## Header Reuse

Nutze kurze, feste Header:

```text
Context:
Pattern:
Delta:
Integration:
Tests:
Docs:
Out of scope:
```

## Canon Referencing

Verweise auf kanonische Dokumente statt Regeln zu wiederholen:

- `docs/PROMPT_OPERATING_SYSTEM.md`
- `docs/PROMPT_PATTERNS.md`
- `PIPELINE_PLAN.md`
- `AGENTS.md`

## Pattern Shorthand

Beispiele:

```text
Use PPOS_CONNECTOR. Add one provider with dry_run default and guarded live optional.
```

```text
Use PPOS_PUBLISHING. Prepare metadata readiness only. No upload.
```

```text
Use PPOS_ASSEMBLY. Add one post-render package check. No render execution.
```

## Typische Tokenersparnis

Grobe Zielwerte:

- Einzel-BA: ca. **40 %** weniger Prompt-Text.
- Full Suite: ca. **50–70 %** weniger Wiederholung.
- Folge-BA auf bestehendem Pattern: oft nur **Delta + Tests + Out-of-scope** nötig.

## Sicherer Kurzprompt

```text
Use PPOS_GLOBAL_V1 + PPOS_FULL_SUITE + PPOS_PUBLISHING.
Implement BA 13.0–13.3.
Focus:
- metadata package
- title/description QA
- schedule readiness
- human publish gate
Out of scope:
- no upload
- no frontend
- no Firestore writes unless already existing read-only contract supports it
Checks:
- compileall
- pytest
- PIPELINE_PLAN update
```
