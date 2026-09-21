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
| M0 reproducible base (Phase 1) | **Done 2026-09-22.** Exit criteria reproduced in `.planning/phases/01-foundation/01-VERIFICATION.md`: six-step gate green on windows-latest and ubuntu-latest (CI run 35627403598), history secret scan as the R-3 guard, `huggingface_hub` import proof. Remote: github.com/kn1218/llm4pol (public; private-repo Actions were blocked by account billing) |
| M1 data foundation (Phase 2) | **Done 2026-09-22.** `.planning/phases/02-data-foundation/02-VERIFICATION.md` 26/26; validator report `docs/audit/polyomics-041e5834-validation.md` is the number authority (49 reproduced, 38 documented, 0 failed); CI 7/7 on both platforms (runs 35648565974, 35651579337). Owner questions recorded there: DATA-09 `tg_rmse` wording vs R-2, 303 unknown-tacticity twins, 43,561 vs 42,733 population, 88.82 % rounding |
| GSD initialisation | Done 2026-09-21: `.planning/{PROJECT,REQUIREMENTS,ROADMAP,STATE}.md`, 8 phases = M0..M7, 41/41 requirements mapped; drift review against charter §13 passed |
| Production code | None yet; permitted under the approved charter, built in the §13 order |
