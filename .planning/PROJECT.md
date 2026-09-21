# LLM4POL

> Derived from `docs/MASTER-PLAN.md` v1.0 (approved 2026-09-21, ADR-0005). The charter is the
> source of truth; this file references it and may not redefine the project's purpose
> (ADR-0002). Where this file and the charter disagree, the charter wins and the disagreement
> is reported as drift.

## What This Is

A closed hypothesis-to-evidence loop for polymer design: an LLM proposes chemistry hypotheses,
a deterministic evaluator scores them against a hidden simulated-property table (PolyOmics
`general_polymers`), and controlled comparison arms attribute any gain to a design axis. The
first target is a thermally conductive electrical insulator designed at the repeat-unit level
(charter §1). Built for the owner as a research instrument whose results become a paper.

## Core Value

The loop must attribute a measured gain to a design axis under a matched evaluation budget —
if that attribution is not reproducible, nothing else the system produces is a result
(charter §1, success layers L1–L5).

## Requirements

### Validated

(None yet — ship to validate)

### Active

Derived from charter §13 milestones M0–M9; detailed in `REQUIREMENTS.md`.

- [ ] Reproducible development base with one check gate on two platforms (M0)
- [ ] PolyOmics snapshot pinned, loaded, validated, with a numbers-of-record validator report (M1)
- [ ] Evaluator behind one contract with `table` backend, status taxonomy, cache, two-currency budget, provenance (M2)
- [ ] Append-only run records with resume and byte-identical replay (M3)
- [ ] Minimal deterministic end-to-end campaign with four beams (M4)
- [ ] LLM hypothesis/translator loop with blind feedback and bounded memory (M5)
- [ ] Replicate variance, zero-feedback control, pre-registration (M6)
- [ ] Budget-matched random / GA / BO comparison arms (M7)
- [ ] Sim-to-real check against an experimental thermal-conductivity source (M8, gated D-17)
- [ ] Live RadonPy backend behind the same evaluator contract (M9, gated D-18)

### Out of Scope

Charter §2 non-goals for the first paper:

- Molecular-weight or dispersity design — not present in the data (Mw/Mn = 1.0 everywhere, ADR-0004)
- Copolymer composition axis — PolyOmics `general_polymers` is homopolymer (D-07 superseded by D-10)
- Real-time MD oracle inside the loop — allocation is small, MD is a spot check (D-06, ADR-0003)
- Synthesis validation — no collaborator (D-12 open)
- The July proposal's "regime" concept — unapproved input, revisit after M5 results
- Training a surrogate model — would optimise another model's biases (ADR-0003)

## Context

- Governance and precedence: `CLAUDE.md`, `docs/governance/` (ADR-0001..0005, DECISIONS-LOG,
  INVARIANTS, CHANGE-POLICY, REVIEW-CHECKLIST).
- Verified inputs: `docs/audit/DATA-FOUNDATION-REPORT.md`, `docs/research/databases/README.md`
  (PolyOmics direct analysis), `docs/research/LLM4MOF-ANATOMY.md` (parent method),
  `docs/research/POLYMER-LANDSCAPE.md` (oracle costs).
- Environment: pixi (`env/pixi.toml`), Python 3.13, single gate `scripts/check.py`, CI on
  windows-latest + ubuntu-latest. `src/llm4pol/` is a scaffold; production code is permitted
  under the approved charter and built in §13 order.
- Data: PolyOmics is CC BY 4.0 (hidden table); PoLyInfo files are contract-bound and never
  committed (ADR-0001). No PolyOmics local copy exists yet — M1 re-acquires it at a pinned
  Hugging Face revision.
- Parent project LLM4MOF supplies ideas and methodology, not an architecture to copy
  (`CLAUDE.md`, charter §5).

## Constraints

- **Precedence**: charter > REQUIREMENTS.md > CLAUDE.md > generated blocks — conflicts are flagged, never silently resolved (ADR-0002)
- **Data**: no data file of either layer is committed; PoLyInfo by licence, PolyOmics by size (ADR-0001, charter §10)
- **Gate**: `pixi run --manifest-path env/pixi.toml check` passes before any commit (R-4)
- **Interfaces**: every cross-component payload has a JSON Schema in `protocol/schemas/`; prompts that produced a result are never edited in place (A-5)
- **Blindness**: nothing sent to a hosted LLM carries row ids, table size, percentiles, thresholds or global statistics (A-4, D-19)
- **Budget**: evaluation count and compute hours are separate currencies (A-3)
- **Review**: authoring and review are separate passes (`REVIEW-CHECKLIST.md`)
- **Completion**: a milestone is done when its charter §13 exit criterion is reproduced, not when tasks close

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Cheap lookup oracle first, simulation behind the same interface (ADR-0003) | Prompt revisions cost seconds, not CPU-weeks | — Pending |
| Problem: thermally conductive insulator on PolyOmics, repeat-unit design layer (ADR-0004) | Industrial spec, jointly available on 43,561 rows, mechanistic signature in intermediate variables | — Pending |
| Staged charter approval; D-16/D-17/D-18 gated at M6/M8/M9 (ADR-0005) | None of them blocks infrastructure; thresholds need M1's feasible-set size | — Pending |
| Development default objective: constrained single (max TC s.t. ε ≤ Q25, Tg ≥ 400 K) | Scalar hit definition keeps percentile/enrichment/GA/BO simple; ledger keeps all three values for post-hoc Pareto | — Pending |
| Agents are API calls, not subagents or services | Reproducibility and cost tracking | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-09-21 after initialization from charter v1.0*
