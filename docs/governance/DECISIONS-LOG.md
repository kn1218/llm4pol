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
| `docs/governance/ADR/` | live, 0001 to 0008 | decisions with context, alternatives and consequences |
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
| D-25 | A missing `tacticity` splits a repeat unit into two candidates. Resolve it, and how? | **Resolve from the labelled twin**: an empty value takes the label when the same canonical SMILES carries exactly one non-empty label elsewhere. Of the 554 empty rows, **312 resolve to `none`, 182 to `atactic`, 60 stay `unknown`** (canonical basis, the rule's own output; the raw-string pairing 176/125 was the motivating measurement). Candidates 78,676 to 78,375. Evidence: `none` is 98.2 % zero-stereocentre, the empty class 52.5 % | 2026-09-24 | Accepted (ADR-0006) |
| D-26 | Which population the loop searches: README triple 43,561 or `check_tc`-passing 42,733 | **the `check_tc`-passing population: 39,454 candidates** (42,733 is the row count the question quoted; corrected 2026-09-29 after the Phase 4 research, the filter chosen is unchanged; README triple 40,212 candidates). The flag explains 108 of the 109 TC > 1 W/(m K) outliers, so leaving them in would let the search optimise unconverged NEMD runs. The report prints percentiles against both populations | 2026-09-24 | Recorded (fixed for Phase 5; final form at the D-16 gate) |
| D-27 | `experiments/` git policy, now that ADR-0001's licence reason no longer covers the PolyOmics layer | **Commit the summaries, ignore the ledger**: `meta.json`, `usage.json`, `results.csv` are tracked (and `run_summary.json`, added by D-37); `ledger.jsonl` stays ignored. ADR-0001's wording is corrected in the same change | 2026-09-24 | Accepted |
| D-28 | REQUIREMENTS DATA-09 says Tg rows are filtered by `tg_rmse`, but `tg_rmse` is a density-residual sum of squares, not kelvin, and plays no part in reproducing 43,561 | **Correct the wording**: apply the 100-900 K window, record the `tg_rmse` ladder at every rung, apply no cut; the threshold is fixed at the Phase 7 pre-registration with D-16 | 2026-09-24 | Accepted |
| D-29 | REQUIREMENTS EVAL-06's third clause (only `llm4pol.loop.agents` may import `llm4pol.llm`) was applied in Phase 3 over the phase context's proposal to defer it to Phase 6. Keep or revert? | **Keep.** The contract is KEPT today and proven to go BROKEN on a violating import; REQUIREMENTS outranks a phase context, and a boundary that exists before the package it guards cannot be forgotten when the package arrives | 2026-09-29 | Accepted (owner delegated the choice to the agent) |
| D-30 | Commits land directly on `main` (`branching_strategy: none`). Keep, or move to branches and PRs? | **Direct commits through Phase 6, then phase branches with a PR and CI-required merge from Phase 7.** Through Phase 6 the repository is single-author infrastructure and the seven-step gate plus a two-platform CI run at every phase tip is the control. From Phase 7 results are claimed, so the pre-registration and every comparison land through a reviewable PR. `git.allow_default_branch_commits` is set to true until then | 2026-09-29 | Accepted (owner delegated the choice to the agent) |
| D-31 | How the ledger carries the population so `replay` needs no parquet | The `run_opened` event holds each population as parallel arrays (objective and every constraint value), sorted by objective, without candidate ids | 2026-09-29 | Accepted (decided by the agent under the owner's delegation of 2026-09-29; ADR-0008) |
| D-32 | `results.csv` column names and shape | Long format, one row per iteration, beam and population; columns `n_selected, n_ok, median_objective, feasible_frac, n_population, pct_of_population, hits_top10, hits_top1`; it reports the paid (sampled) layer only | 2026-09-29 | Accepted (decided by the agent under the owner's delegation of 2026-09-29; ADR-0008) |
| D-33 | Definitions of `feasible_frac`, `hits_top10`, `hits_top1` | A missing constraint value is not feasible; a hit must be feasible and at least as good as the top 10 % / 1 % threshold of the **feasible** members of the population. Development default until the D-16 gate | 2026-09-29 | Accepted (decided by the agent under the owner's delegation of 2026-09-29; ADR-0008) |
| D-34 | Value basis of a percentile | Membership by the population filter, values as the evaluator serves them. Serving medians over `check_tc`-passing rows only is recorded as an option for the D-16 gate (two of 39,454 members affected) | 2026-09-29 | Accepted (decided by the agent under the owner's delegation of 2026-09-29; ADR-0008) |
| D-35 | Does `resume` accept a different code version | No. It refuses a different snapshot, registry version or `code_git_sha`, and a torn final line; `replay` and `usage` do not compare code | 2026-09-29 | Accepted (decided by the agent under the owner's delegation of 2026-09-29; ADR-0008) |
| D-36 | Granularity of `evaluation` events | One per candidate | 2026-09-29 | Accepted (decided by the agent under the owner's delegation of 2026-09-29; ADR-0008) |
| D-37 | Is there a `run_summary.json` | Yes, tracked, written at `run_closed` and regenerated by `replay`; carries the sha256 of the ledger and of `results.csv` | 2026-09-29 | Accepted (decided by the agent under the owner's delegation of 2026-09-29; ADR-0008); ADR-0007 |
| D-38 | Where the selector protocol lives | In `llm4pol.run`; Phase 4 ships a plan-file selector, Phase 5 adds the deterministic one in `llm4pol.loop` | 2026-09-29 | Accepted (decided by the agent under the owner's delegation of 2026-09-29; ADR-0008) |
| D-39 | Do `meta.json`, `usage.json` and `run_summary.json` need JSON Schemas, or do key-set tests suffice? | **Schemas**: `protocol/schemas/run-meta.json`, `run-usage.json`, `run-summary.json`, each with `schema_version` and a committed example in the gate inventory. The files are tracked, frozen at M3 and read by Phases 7 and 8; a key-set test pins names, not types | 2026-09-29 | Accepted (decided by the agent under the owner's delegation of 2026-09-29) |
| D-40 | The Phase 4 code review (CR-01, IN-02) added two exit codes to the `campaign` CLI beyond Phase 4 CONTEXT D-07 (`0` / `2` schema, IO / `4`, with `3` for the recorded budget refusal). Keep them? | **Keep, as an amendment of CONTEXT D-07**: `2` stays for input that cannot be read or validated (operator files, a ledger that is not a ledger); `5` is a failure while *writing* the run record (disk full, permission), whose message names the byte offset a torn line may follow; `6` is a run held by another process (the ledger lock). A write failure and a locked run call for different operator actions than bad input, so they get their own codes. `3` and `4` are unchanged | 2026-09-30 | Accepted (decided by the agent under the owner's delegation; flagged for owner review) |

## Open

| # | Question | Why it blocks |
|---|---|---|
| D-12 | Synthesis or measurement collaborator for even one polymer | Sets the realistic venue; blocks nothing before M7 |
| D-15 | Replicate budget and multiplicity-correction plan | Blocks M6 only. Measured there: 10 replicates, MDE, Holm |
| D-14 | LLM provider, API key and budget | Blocks M5 only. No API key is set on this machine |
