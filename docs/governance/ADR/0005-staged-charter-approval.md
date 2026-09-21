# ADR-0005: The charter is approved with gated parameters; objective form, experimental source and live scope are fixed at milestone gates

- **Status:** Accepted
- **Date:** 2026-09-21
- **Deciders:** owner ("진행해", approving `PROJECT-FOUNDATION-PROPOSAL.md` v0.1 §10), on analysis presented by the agent
- **Relates to:** ADR-0002, ADR-0003, ADR-0004, `MASTER-PLAN.md` §13, DECISIONS-LOG D-16, D-17, D-18, D-19, D-20

## Context

ADR-0002 fixes the order proposal → charter → GSD → code, and invariant R-5 forbids production
code before the charter is approved. On 2026-09-11 the progress tracker recorded the proposal
as "blocked only on D-16 (objective form) and D-17 (experimental source)".

The dependency analysis in the proposal (§3) showed that neither decision blocks the four
infrastructure milestones. The evaluator returns all three properties regardless of the
objective form; the run ledger records all three; the experimental source only enters at the
sim-to-real milestone as a second `source` value under the same evaluator contract; live mode
only needs the `backend` field and the compute-hours currency that ADR-0003 already requires.
Holding the charter for these answers would hold every line of code hostage to research
decisions that have no infrastructure consequence.

## Decision

The charter (`docs/MASTER-PLAN.md`) is approved now with three parameters declared **gated**,
each fixed at the entry of the milestone that first needs it:

| Parameter | Decision | Development default until fixed | Fixed at |
|---|---|---|---|
| Objective form and thresholds | D-16 | constrained single objective: maximise `thermal_conductivity` subject to `dielectric_const_dc` ≤ table Q25 and `tg` ≥ 400 K | M6 pre-registration |
| Experimental thermal-conductivity source | D-17 | OpenPoly as the default anchor; PoLyInfo re-export requested in parallel | M8 entry |
| Live-mode scope | D-18 | not in the first paper; gated follow-on | M9 entry |

Two further decisions are taken with this ADR:

- **D-19.** PolyOmics-derived content (repeat-unit SMILES, deterministic tags, sampled property
  values) may be sent to a hosted LLM API. PolyOmics is CC BY 4.0. The methodological blind
  rule applies: row identifiers, table size, percentiles, thresholds and any global statistic
  are never sent. D-04 continues to govern PoLyInfo-derived content unchanged.
- **D-20.** The staged approval itself.

## Alternatives considered

| Option | Why not |
|---|---|
| Answer D-16 and D-17 first, then approve | Delays M0–M4 for decisions with zero infrastructure consequence; the thresholds cannot be chosen well before M1 reports the feasible-set size anyway |
| Approve the charter without naming gates | Leaves the parameters implicit; a later change could not be distinguished from drift |
| Freeze the development default as the final objective form | Pre-empts the M6 pre-registration, which is where the replicate noise and feasible-set size that justify the thresholds are first measured |

## Consequences

- `MASTER-PLAN.md` §13 names each gated parameter, its development default and its gate. A
  milestone that fixes a parameter records the value in `AMENDMENTS.md` if it differs from the
  default.
- Invariant R-5 changes direction: production code may exist only while the charter declares
  `Status: Approved`. **Guard:** `tests/test_governance.py::test_charter_status_gates_production_code`.
- The feedback payload test required by M5 (no row ids, percentiles or thresholds in anything
  sent to a provider) is the guard for D-19. Prose until M5.
- ADR-0002's drift review after `/gsd-new-project` remains required and now also checks that
  GSD artifacts do not silently fix a gated parameter.
