---
name: ba-check
description: >-
  Checks proposed build phases (BA) and roadmap ideas against PIPELINE_PLAN.md
  governance for news-to-video-pipeline: canonical BA numbering, intact Phase
  numbering, BA/Phase separation, repo naming, minimal-invasive scope, docs
  needs. Use when the user invokes /ba-check, ba-check, or asks for a BA/Phase
  governance gate before planning or merging roadmap changes.
disable-model-invocation: true
---

# BA Check (Build-Phase Governance Gate)

Purpose: Analyze the **requested build phase or roadmap proposal** for the **news-to-video-pipeline** project against repository canon.

## Mandatory process

1. Check PIPELINE_PLAN.md
2. Check README.md
3. Check ISSUES_LOG.md
4. Check AGENTS.md

Use the **current** contents of these files (and any diff under review). Do not rely on memory for numbering, status, or terminology.

## Evaluation (answer each)

- **A)** Is BA numbering canonical?
- **B)** Is Phase numbering untouched?
- **C)** Does this conflict with the existing BA roadmap?
- **D)** Is BA/Phase separation preserved?
- **E)** Are repo naming conventions preserved?
- **F)** Is this minimal-invasive?
- **G)** Are documentation changes required?

## Important

- Never allow **BA 10** if **BA 9.x** maturity is incomplete (treat roadmap through **BA 9.9** as the Story Engine line; do not approve a new top-level BA that skips or collapses that sequence).
- Never merge **Story Engine BA 9.x** with **Packaging/Publishing** macro phases (**Phase 9** Video Packaging, **Phase 10** Publishing).
- Preserve the **BA 9.5a** and **BA 9.5b** distinction (9.5a Observability before 9.5b Story-Pack / Beat-Sheet per PIPELINE_PLAN).
- Preserve **repo terminology** (e.g. documented collection and field names such as **`review_results`** — do not invent parallel persistence names).

Additional hard rules (align with AGENTS.md / PIPELINE_PLAN):

- **BA** = modular build phases; **Phase** = macro product roadmap — never conflate **BA 9.x** with **Phase 9** or **Phase 10**.
- Do **not** change **`GenerateScriptResponse`** / `/generate-script` contract unless the user explicitly requests it.
- Do **not** read or modify `.env`. Do **not** modify `.cursor/plans` unless the user explicitly requests it.

## Output (strict)

Respond **only** with the following sections and headings, in this order. Use the exact heading text. Lists may use `-` bullets; if empty, write `(none)`.

## Governance Verdict

(pass / warning / fail)

## Canonical Alignment

(fully aligned / partial drift / conflicting)

## Risks

(list)

## Required Corrections

(list)

## Safe Next Step

(single recommended path)

## Verdict guidance

- **pass**: A–G satisfied; no canon conflict; optional doc touch-ups only.
- **warning**: Minor drift, naming slip, or doc lag fixable without roadmap conflict; call out what to fix.
- **fail**: BA/Phase mix-up, non-canonical BA numbering, collision with BA 9.x sequence, unauthorized contract change risk, or **BA 10** while **9.x** incomplete — require corrections before implementation.

Base evidence on **quoted or cited** sections from the four mandatory files when asserting alignment or conflict.
