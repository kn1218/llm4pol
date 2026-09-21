# Progress tracking

## Where progress lives

Milestone and task state live in GSD's `.planning/` artifacts once GSD is initialised. This
file records only what exists before that, and the rule for what counts as done.

## Definition of done

A milestone is done when its **measurable exit criterion** is reproduced, not when its tasks
are closed. An exit criterion is a number or a check that another person can re-run.

These are never evidence of completion: placeholder notes, skipped or focused tests, stubbed
functions, unimplemented branches, or a passing gate on code that nothing calls.

## Current state — 2026-09-21

| Item | State |
|---|---|
| Data foundation audit | Done, independently verified |
| LLM4MOF method and code study | Done, independently verified, two numbers corrected |
| Polymer landscape survey | Done, citations independently re-checked |
| Polymer database survey | Done; PolyOmics verified directly, one broken column found |
| Repository, environment, gate, CI, GSD install | Done, gate green, zero commits |
| Problem definition | **Decided** (ADR-0004): thermally conductive electrical insulator on PolyOmics |
| PROJECT FOUNDATION PROPOSAL | Approved 2026-09-21, promoted to the charter (ADR-0005) |
| Charter, `MASTER-PLAN.md` | **Approved v1.0.** D-16/D-17/D-18 gated at M6/M8/M9 |
| M0 reproducible base | In progress: first commit, `huggingface_hub` in the environment |
| GSD initialisation | Next, with the charter as input; drift review follows |
| Production code | None yet; permitted under the approved charter, built in the §13 order |
