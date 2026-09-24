# Decisions log

Owner decisions, recorded as they are made. A decision here is **not** binding architecture
until it appears in `MASTER-PLAN.md` or an accepted ADR. Status values:

- **Accepted** — stated by the owner and carried into an ADR or the charter
- **Recorded** — stated by the owner, not yet reflected in an ADR; may be revisited
- **Open** — asked, not yet answered
- **Reopened** — previously answered, then invalidated by a later instruction
- **Deferred** — the owner chose to leave it open for now

## Where the plan lives

| Artifact | Status | Holds |
|---|---|---|
| This log | live | every owner decision with its status |
| `docs/governance/ADR/` | live, 0001 to 0005 | decisions with context, alternatives and consequences |
| `docs/PROJECT-FOUNDATION-PROPOSAL.md` | superseded 2026-09-21 | stub; content promoted to the charter |
| `docs/MASTER-PLAN.md` | **Approved v1.0, 2026-09-21** | the charter; §13 holds milestones and gated parameters |
| `.planning/` (GSD) | initialising | milestones and tasks, generated from the charter, drift-checked against it |

## Recorded

| # | Question | Answer | Date | Status |
|---|---|---|---|---|
| D-01 | Repository location | Desktop, outside Dropbox | 2026-09-11 | Accepted (ADR-0001) |
| D-02 | Planning system and precedence | GSD per-project, subordinate to the charter | 2026-09-11 | Accepted (ADR-0002) |
| D-03 | Development methodology | Cheap lookup mode first, simulation layered on top | 2026-09-11 | Accepted (ADR-0003) |
| D-04 | May PoLyInfo-derived content be sent to a hosted LLM API? | Derived tags and noise-floor-binned values only. No names, no SMILES, no identifiers | 2026-09-11 | Recorded |
| D-05 | Venue and relationship to the LLM4MOF authors | Independent submission | 2026-09-11 | Recorded |
| D-06 | dirac HPC allocation | Small scale only. MD is a spot check, never an in-loop oracle | 2026-09-11 | Recorded |
| D-07 | Homopolymer only, or copolymer too? | Superseded by D-10: repeat unit is the design layer; PolyOmics `general_polymers` is homopolymer | 2026-09-11 | Superseded |
| D-08 | **What polymer problem is being solved?** | Thermally conductive electrical insulator: thermal conductivity up, dielectric constant down, Tg adequate. Framed for electronics packaging | 2026-09-11 | Accepted (ADR-0004) |
| D-09 | What plays pore geometry's role: hypothesisable, cheaply estimable, oracle-recomputed, not the target | Chain dimension (`Rg`, `r2`), cohesive energy density, fractional free volume — all in PolyOmics, computed by the same MD | 2026-09-11 | Accepted (ADR-0004) |
| D-10 | Which design layer | Repeat unit, tacticity controlled. Molecular weight and dispersity are simulation settings in PolyOmics (Mw/Mn = 1.0 everywhere) and out of scope | 2026-09-11 | Accepted (ADR-0004) |
| D-11 | Which table is the hidden table | PolyOmics `general_polymers`; PoLyInfo is the experimental transfer-validation layer | 2026-09-11 | Accepted (ADR-0004) |
| D-13 | Contribution: measured attribution, candidate discovery, or sim-to-real transfer | Owner keeps all three open. Agent's proposal for the proposal document: attribution as the headline claim, discovery as the output, sim-to-real as the validation chapter | 2026-09-11 | Deferred |
| D-16 | Objective form | **Development default: constrained single objective** (max `thermal_conductivity` s.t. `dielectric_const_dc` ≤ table Q25, `tg` ≥ 400 K). Final form and thresholds fixed at the M6 pre-registration gate | 2026-09-21 | Recorded, gated (ADR-0005) |
| D-17 | Experimental thermal-conductivity source | Development default: OpenPoly as anchor, PoLyInfo re-export requested in parallel. Fixed at M8 entry | 2026-09-21 | Recorded, gated (ADR-0005) |
| D-18 | Live-mode scope | Not in the first paper; gated follow-on. Fixed at M9 entry | 2026-09-21 | Recorded, gated (ADR-0005) |
| D-19 | May PolyOmics-derived content (repeat-unit SMILES, tags, sampled values) be sent to a hosted LLM API? | Yes, under the blind rule: never row ids, table size, percentiles, thresholds or global statistics. D-04 still governs PoLyInfo content | 2026-09-21 | Accepted (ADR-0005) |
| D-20 | Staged charter approval with D-16/D-17/D-18 as milestone-gated parameters | Yes | 2026-09-21 | Accepted (ADR-0005) |
| D-21 | Run ledger storage: JSONL or SQLite (the sibling port LLM4MO uses SQLite with a header row) | **JSONL with a header line** -- the first line carries `problem` + `provenance` so a resumed run cannot silently change its own problem (LLM4MO's property), while the record stays human-readable and diffable. Charter section 7 unchanged | 2026-09-23 | Accepted |
| D-22 | Data partitions: development / validation / test, as in LLM4MO | **No partitions.** Charter section 8 stands: DB mode trains nothing, so there is no model to overfit. A scaffold-grouped split is added by ADR when a surrogate first enters the loop | 2026-09-23 | Accepted |
| D-23 | Contract types: frozen dataclasses + JSON Schema (LLM4POL) or pydantic BaseModel (LLM4MO) | **Keep frozen dataclasses + JSON Schema.** Built and green in Phase 3; the schemas validate the contract from outside the language and are enforced by the `schema-inventory` gate step | 2026-09-23 | Accepted |
| D-24 | Physical public/private data split, as in LLM4MO | **No physical split.** Blindness is guaranteed by testing the payload that leaves for the provider (A-4), not by storage layout. Revisit if the Phase 6 payload test proves insufficient | 2026-09-23 | Accepted |

## Open

| # | Question | Why it blocks |
|---|---|---|
| D-12 | Synthesis or measurement collaborator for even one polymer | Sets the realistic venue; blocks nothing before M7 |
| D-15 | Replicate budget and multiplicity-correction plan | Blocks M6 only. Measured there: 10 replicates, MDE, Holm |
| D-14 | LLM provider, API key and budget | Blocks M5 only. No API key is set on this machine |
