# LLM4POL -- Project Governance

## What this project is, and what LLM4MOF is to it

LLM4MOF supplies **ideas** (a closed hypothesis-to-evidence loop, a stateful hypothesis agent
paired with a stateless constraint translator, controlled comparison arms that attribute a
gain to a design axis, a bounded factual memory) and a **development methodology** (exercise
everything on a cheap lookup oracle first, then layer expensive physics on an unchanged loop).

It does **not** supply an architecture to copy. The architecture is designed from the polymer
problem. `docs/research/PORTING-MAP.md` is a study of the parent system, not the plan; it is
superseded in framing and says so.

The problem is fixed by ADR-0004 and the charter: a thermally conductive electrical
insulator designed at the repeat-unit level on PolyOmics `general_polymers`. Do not take a
target, design space or scope from any other document.

## Source of truth and precedence

When guidance from different sources disagrees, the precedence order, highest first:

1. `docs/MASTER-PLAN.md` -- the charter and authoritative source of truth. **Approved
   2026-09-21, v1.0** (ADR-0005). Three parameters are gated, not open: objective form
   (D-16, fixed at M6), experimental source (D-17, M8), live scope (D-18, M9).
2. `.planning/REQUIREMENTS.md` -- the owner-reviewed implementation contract, a GSD artifact
   subordinate to the charter.
3. This hand-authored `CLAUDE.md`; it carries no GSD generator marker and is safe to edit by
   hand.
4. Machine-generated blocks of `.claude/CLAUDE.md`, between `GSD:{name}-start` and
   `GSD:{name}-end` markers, if and when GSD generates them.

A higher source wins. Flag the conflict to the human owner instead of resolving it silently.

Everything under `docs/audit/`, `docs/research/` and `docs/reference/` is an **input**: the
audit and research reports are verified facts, the July 2026 proposal is an unapproved concept
document. None of them is a plan.

## Before doing anything, read the state

- `docs/governance/DECISIONS-LOG.md` -- what the owner has decided, what is still open, and
  what was decided and then reopened. Never act on a reopened decision.
- `docs/governance/INVARIANTS.md` -- what must hold and what enforces it.
- `docs/ENGINEERING-OPERATING-MODEL.md` -- planes, tool roles, build order, the cheap-first
  ladder.

## Production code exists only under an approved charter

`src/llm4pol/` may hold production code only while `docs/MASTER-PLAN.md` declares
`Status: Approved`. `tests/test_governance.py::test_charter_status_gates_production_code`
enforces it. Build in the charter's order (§13: M0 → M9); a milestone is done when its
exit criterion is reproduced. GSD artifacts under `.planning/` are derived from the charter
and are diffed against it before implementation starts (ADR-0002).

## Data policy

- Two data layers. The hidden table is PolyOmics (CC BY 4.0, pinned Hugging Face revision,
  hashes in `data/MANIFEST-open.sha256` once M1 creates it). The transfer-validation layer is
  PoLyInfo-derived; the NIMS MatNavi terms forbid redistribution of that data and of derived
  data. **No data file of either layer is committed** -- PoLyInfo by licence, PolyOmics by
  size. `data/raw/`, `data/interim/` and `data/processed/` are git-ignored. See ADR-0001.
- `data/MANIFEST.sha256` lists the expected raw files with sha256 and byte size. Any file
  present in `data/raw/` must match it; `tests/test_manifest.py` checks this.
- Recorded but not yet an ADR (D-04): content sent to a hosted language-model API is limited
  to derived tags and noise-floor-binned values. No names, no SMILES, no identifiers.
- Never print or log the contents of `.env`, and never print a secret value.

## Where things go

| Directory | Holds | Rule |
|---|---|---|
| `protocol/prompts/` | Agent prompts exactly as sent, versioned | A prompt that produced a reported result is never edited in place; bump the version |
| `protocol/schemas/` | JSON Schema for every payload crossing a component boundary | A payload with no schema has no guard |
| `config/` | Committed machine configuration | Every file has a sibling `*.schema.json`; enforced by the test suite. No secrets |
| `experiments/` | Run outputs | Git-ignored except the README. Append-only; a rerun gets a new identifier |
| `docs/governance/ADR/` | Architecture decisions | `NNNN-kebab-case.md`, contiguous numbering, Status and Date lines; enforced by the test suite |

## Checks

```
pixi run --manifest-path env/pixi.toml check
```

Equivalent to `python scripts/check.py` at the repository root inside the pixi environment,
with `PYTHONPATH=src`. It must pass before anything is committed. CI runs the same invocation
on Windows and Linux.

## Working rules

- Authoring and review are separate passes. Do not approve your own work in the context that
  produced it. `docs/governance/REVIEW-CHECKLIST.md` is the checklist.
- A rule that matters becomes a test, a schema or a CI check as soon as it is stable.
  Documentation states the reason; the guard enforces the rule.
- A number is published in one place; elsewhere it is cited. An unverified transcription is
  labelled as unverified until a second source confirms it.
- A milestone is done when its measurable exit criterion is reproduced, not when its tasks are
  closed. Placeholder notes, skipped tests, stubs and unimplemented branches are blockers, not
  evidence.

## Tooling

- GSD Core is installed per-project under `.claude/`. `/gsd-new-project` is run with the
  approved charter as its input (ADR-0002); `.planning/` is subordinate to the charter.
- Whether oh-my-claudecode is disabled here is an owner decision at charter time; no setting
  disabling it has been written. The prior project disables it.
- Commit messages follow conventional commits (`feat:`, `fix:`, `docs:`, `test:`, `chore:`),
  scoped by GSD plan id once plans exist.
