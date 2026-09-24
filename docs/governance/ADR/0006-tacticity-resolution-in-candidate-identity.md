# ADR-0006: A missing tacticity is resolved from its labelled twin before the candidate identity is taken

- **Status:** Accepted
- **Date:** 2026-09-24
- **Deciders:** owner, on a measurement presented by the agent
- **Relates to:** ADR-0004, charter §6 and §7 (candidate definition, frozen at M1),
  `.planning/phases/02-data-foundation/02-CONTEXT.md` D-03, DECISIONS-LOG D-25

## Context

`candidate_id = sha256(canonical_psmiles + "|" + tacticity)[:16]` (charter §6). PolyOmics
`general_polymers` leaves `tacticity` empty on 554 of 95,335 rows. Phase 2 mapped an empty value to
the literal `"unknown"` so that every row receives an identity (02-CONTEXT D-03). The consequence was
that a repeat unit recorded once with a label and once without became **two** candidates.

Measured on the pinned revision `041e5834` on 2026-09-24, over the unique SMILES of each class
(RDKit `FindMolChiralCenters`, unassigned included; up to 400 sampled per class):

| `tacticity` | rows | unique SMILES | mean stereocentres | share with zero |
|---|---|---|---|---|
| `none` | 48,790 | 43,004 | 0.04 | **98.2 %** |
| `atactic` | 45,032 | 34,480 | 1.68 | 2.2 % |
| `isotactic` | 951 | 832 | 1.33 | 0.0 % |
| `syndiotactic` | 8 | 8 | 1.25 | 0.0 % |
| empty | 554 | 358 | 0.98 | **52.5 %** |

`none` therefore means *no stereocentre exists*, not *not recorded*: tacticity is inapplicable to
those repeat units. The empty class is a mixture — about half have no stereocentre and belong with
`none`, about half carry stereocentres and are simply unlabelled.

301 **raw** SMILES strings appear both with an empty value and with exactly one label — 176 pairing
with `none`, 125 with `atactic`. In each case the same repeat unit was simulated more than once under
the same cell settings and the label was recorded on one run and not the other.

The rule below keys on `canonical_psmiles`, not on the raw string, so it resolves more than that
motivating count: RDKit canonicalisation merges raw variants of one repeat unit. Measured on the
in-scope rows (95,332 after the homopolymer scope filter), of the **554 rows** with an empty
`tacticity`:

| Outcome | Rows |
|---|---|
| resolved to `none` | **312** |
| resolved to `atactic` | **182** |
| left `"unknown"` (no labelled twin, or more than one distinct label) | **60** |

Two canonical SMILES carry more than one distinct label and are therefore left `"unknown"` by the
rule's own guard. No empty row resolves to `isotactic` or `syndiotactic`.

## Decision

Before the identity is taken, an empty `tacticity` is resolved to the label of its twin when the same
`canonical_psmiles` carries **exactly one** non-empty label elsewhere in the table. Rows with no
labelled twin, or with more than one distinct labelled twin, keep `"unknown"`.

The rule is a lookup inside one snapshot, not an inference from chemistry: it never assigns a label a
row's own repeat unit was not observed to carry.

## Alternatives considered

| Option | Why not |
|---|---|
| Keep every empty value as `"unknown"` (the Phase 2 rule) | 301 materials stay split, so their replicates are never pooled, their replicate noise floor is not measured, and one beam can present the same repeat unit twice as two candidates |
| Merge only the 176 `none` twins (zero stereocentres is a fact, not an inference) | Leaves the 125 `atactic` twins split for a weaker reason: their twin states the label explicitly and the cell settings are identical |
| Assign by stereocentre count (zero → `none`, otherwise `"unknown"`) | Covers the 57 unique SMILES with no twin, but discards the twin evidence where it exists and substitutes a chemistry inference for an observation |
| Fold every empty value into `none` | Contradicted by the measurement: 47.5 % of the empty rows carry stereocentres |

## Consequences

- `llm4pol.data.identity` gains a resolution pass over the snapshot before hashing; the rule needs the
  whole table, so it runs in `load`, not per row.
- **`candidate_id` changes for the affected rows**, and the candidate count falls from **78,676 to
  78,375** (−301). The candidate-level triple counts move by a smaller amount and are republished from
  the validator itself rather than quoted here, since they depend on the filter-then-median order the
  report defines. The candidate definition is frozen at M1 (charter §7), so this ADR is the instrument
  that changes it;
  `data/processed/candidates-041e5834.parquet` is regenerated and
  `docs/audit/polyomics-041e5834-validation.md` is republished with the new counts. Phase 2 and Phase 3
  test expectations that quote the old counts are updated in the same change.
- The validator report states the resolution counts (176, 125, 57 unresolved) and the population each
  is drawn from, so the change is visible in the number authority rather than only here.
- **Guard:** `tests/test_data_invariants.py` gains a test that no candidate resolves to a label its own
  repeat unit was never observed with, and that a SMILES with two distinct labelled twins stays
  `"unknown"`.
