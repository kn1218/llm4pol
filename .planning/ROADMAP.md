# Roadmap: LLM4POL

> Derived from `docs/MASTER-PLAN.md` v1.0 §8 (build order) and §13 (milestones, exit criteria,
> decision gates). Per charter §14 this file **references** §13 and does not copy it. Each phase
> is one charter milestone in charter order; a phase is complete when its charter §13 exit
> criterion is reproduced and cited in that phase's `VERIFICATION.md` (charter §9). Gated
> parameters (D-14, D-15, D-16, D-17, D-18) are decided by the owner at the gates named in
> charter §13; nothing in this file fixes them (ADR-0005).

## Overview

The build runs in dependency-first order, not runtime order (charter §8): a reproducible base,
then the pinned PolyOmics snapshot and property registry, then the evaluator contract with its
`table` backend, then append-only run records with resume and replay, then a deterministic
four-beam end-to-end campaign that proves the pipeline alive without any LLM, then the LLM
hypothesis/translator loop behind one provider adapter, then replicate variance, a
zero-feedback control and a committed pre-registration, and finally the budget-matched
random / GA / BO comparison arms. Success layers L1–L4 (charter §1) are earned in that order;
L5 belongs to the gated follow-ons M8/M9 and is not in this roadmap.

| Phase | Charter milestone | Success layer (charter §1) |
|-------|-------------------|----------------------------|
| 1 | M0 Foundation | — |
| 2 | M1 Data foundation | — |
| 3 | M2 Evaluator (table) | L2 |
| 4 | M3 Run management | L2 |
| 5 | M4 Deterministic e2e | L1 |
| 6 | M5 LLM loop | L3 |
| 7 | M6 Variance, controls, pre-registration | (prerequisite of L4) |
| 8 | M7 Comparison arms | L4 |

## Phases

**Phase Numbering:**

- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation** - Reproducible development base; one check gate green on both CI platforms (charter M0) (completed 2026-09-22)
- [x] **Phase 2: Data Foundation** - PolyOmics snapshot pinned, loaded, identified and validated with a numbers-of-record report (charter M1) (completed 2026-09-22)
- [ ] **Phase 3: Evaluator (table backend)** - One evaluator contract with status taxonomy, cache, two-currency budget and provenance (charter M2)
- [ ] **Phase 4: Run Management** - Append-only run records with resume and byte-identical replay (charter M3)
- [ ] **Phase 5: Deterministic End-to-End** - Seed-reproducible 10-iteration four-beam campaign with no LLM (charter M4)
- [ ] **Phase 6: LLM Loop** - Hypothesis and translator agents through one provider adapter with blind feedback (charter M5, gated D-14)
- [ ] **Phase 7: Variance, Controls, Pre-registration** - Replicate σ, zero-feedback control, committed pre-registration (charter M6, depends D-15, fixes D-16)
- [ ] **Phase 8: Comparison Arms** - Budget-matched random / GA / BO against the same evaluator (charter M7)

## Phase Details

### Phase 1: Foundation

**Goal**: The repository is a reproducible development base whose single check gate is green on both CI platforms with the snapshot-fetch dependency locked in — see charter §13 M0.
**Charter milestone**: M0
**Depends on**: Nothing (first phase; charter approved under ADR-0005)
**Requirements**: FOUND-01, FOUND-02, FOUND-03
**Success Criteria** (what must be TRUE) — charter §13 M0:

  1. `pixi run --manifest-path env/pixi.toml check` is green on windows-latest and ubuntu-latest from the committed lock file, and `huggingface_hub` resolves in that lock on both platforms (charter §13 M0)
  2. A first commit of the approved-charter era exists on `main` (charter §13 M0)
  3. `.env` is untracked (`git ls-files .env` is empty), `.env.example` is committed, and no secret value appears in output, logs or history (charter §13 M0, R-3)

**Freezes**: nothing (explicit in charter §13 M0)
**Plans**: TBD

- [x] 01-01-PLAN.md

### Phase 2: Data Foundation

**Goal**: PolyOmics `general_polymers` is pinned at one Hugging Face revision, loaded into one parquet snapshot, identified per candidate, and validated by a report that is the authority for every number cited later — see charter §13 M1.
**Charter milestone**: M1
**Depends on**: Phase 1
**Requirements**: DATA-01, DATA-02, DATA-03, DATA-04, DATA-05, DATA-06, DATA-07, DATA-08, DATA-09, DATA-10
**Success Criteria** (what must be TRUE) — charter §13 M1:

  1. Every file of the pinned Hugging Face revision matches `data/MANIFEST-open.sha256` by sha256 and byte size (charter §13 M1 (1))
  2. The validator report `docs/audit/polyomics-<rev>-validation.md` reproduces — or documents the difference for — the row count, the unique repeat-unit count, the filtered triple count 43,561 (with the `tg_rmse` / 100–900 K filter counts that produce it), the `static_dielectric_const` Maxwell violation 88.9 % and the `dielectric_const_dc` violation 0, and resolves 95,335 vs 73,045 (charter §13 M1 (2)–(3))
  3. The validator report records the replicate structure (rows per `candidate_id`, replicate vs tacticity) and the replicate noise floor of `thermal_conductivity`, `dielectric_const_dc` and `tg` (charter §13 M1 (4))
  4. The validator report states the feasible-set size under the development default thresholds (ε ≤ table Q25, Tg ≥ 400 K) as an input to the D-16 gate, without fixing D-16 (charter §13 M1 (5))
  5. Invariants D-7..D-10 and A-7 run as tests inside the check gate, added in the same change as the loader (charter §13 M1 (6))

**Freezes**: candidate definition (`candidate_id = sha256(canonical_psmiles + "|" + tacticity)[:16]`), property registry (`protocol/schemas/property-registry.json`), snapshot identifier `polyomics:general_polymers@<hf_revision>` (charter §7, §13 M1)
**Plans**: 5/5 plans executed

Plans:
**Wave 1**

- [x] 02-01-PLAN.md — Tracer: environment + import contract, MANIFEST-open, fetch → load → identity → parquet → first validator sections through `python -m llm4pol.data` (wave 1)
- [x] 02-02-PLAN.md — Property registry triad: schema with A-7 by construction, instance with unit status, provenance (wave 1)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 02-03-PLAN.md — Fetch contract, identity vectors, declared schema and loader rules; real-file identity counts (wave 2)
- [x] 02-04-PLAN.md — Registry loader, `schema-inventory` check step, replicate structure and noise floor; D-7, D-9 promoted (wave 2)

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 02-05-PLAN.md — README numbers, Tg ladder, feasible set as D-16 input, D-8/D-10/A-7 promoted, committed report, README correction, CI evidence (wave 3)

Charter §8 permits fetch/identity ∥ validate inside this phase.

### Phase 3: Evaluator (table backend)

**Goal**: Every property lookup goes through one evaluator contract backed by `table`, with a four-value status taxonomy, a cache that never double-charges, and a two-currency budget — see charter §13 M2.
**Charter milestone**: M2
**Depends on**: Phase 2
**Requirements**: EVAL-01, EVAL-02, EVAL-03, EVAL-04, EVAL-05, EVAL-06
**Success Criteria** (what must be TRUE) — charter §13 M2:

  1. Each of `ok`, `unsupported`, `missing` and `error` has a passing test; `unsupported` and `missing` consume no `evals`; `error` is retried (charter §13 M2)
  2. A cache hit on `(candidate_id, property, backend, source)` leaves `evals` unchanged (charter §13 M2)
  3. A batch request of 100 entries returns 100 responses in request order (charter §13 M2)
  4. Every response carries `source`, `backend` and `provenance_tier`, together with `n_replicates`, `spread`, `unit` and `cost {evals, cpu_hours}` (charter §13 M2)
  5. Schema validation of `eval-request.json` / `eval-response.json` and the first import-linter contract run inside the check gate (charter §13 M2)

**Freezes**: evaluator request/response (`protocol/schemas/eval-request.json`, `eval-response.json`), import boundary in `pyproject.toml [tool.importlinter]` enforcing A-1 and A-2 (charter §7, §13 M2)
**Plans**: TBD

### Phase 4: Run Management

**Goal**: A campaign leaves an append-only run record under `experiments/<run-id>/` that can be resumed without duplicate events and replayed to a byte-identical `results.csv` — see charter §13 M3.
**Charter milestone**: M3
**Depends on**: Phase 3 (charter §8: M3 needs only the evaluator response format, so M2 ∥ M3 is permitted)
**Requirements**: RUN-01, RUN-02, RUN-03, RUN-04, RUN-05, RUN-06
**Success Criteria** (what must be TRUE) — charter §13 M3:

  1. A run interrupted mid-campaign and resumed continues from the last closed iteration and records zero duplicate `(run_id, iteration, beam)` events (charter §13 M3)
  2. `replay` regenerates `results.csv` from `ledger.jsonl` alone, byte-identical to the original (charter §13 M3)
  3. `usage.json` totals for `evals` and `cpu_hours` equal the ledger sums and are kept as two separate currencies (charter §13 M3, A-3)

**Freezes**: run record format (`protocol/schemas/ledger-event.json`, `experiments/<run-id>/{meta.json, ledger.jsonl, usage.json, results.csv}`), problem spec (`protocol/schemas/problem-spec.json`), A-3 (two budget currencies) and A-6 (append-only run directory, rerun gets a new id) as ledger tests (charter §7, §13 M3)
**Plans**: TBD

### Phase 5: Deterministic End-to-End

**Goal**: `llm4pol run --selector deterministic` completes a seed-reproducible 10-iteration, four-beam campaign on the hidden table with no LLM involved, proving the pipeline alive — see charter §13 M4.
**Charter milestone**: M4
**Depends on**: Phase 4
**Requirements**: LOOP-01, LOOP-02, LOOP-03, LOOP-04, LOOP-05, LOOP-06
**Success Criteria** (what must be TRUE) — charter §13 M4:

  1. Two runs with the same seed produce identical `ledger.jsonl` and `results.csv` (charter §13 M4)
  2. All four beams `full`, `chem`, `primary`, `random` record `n ≥ 1` in `results.csv`, with `n`, `median_tc`, `feasible_frac`, `pct_of_table`, `hits_top10`, `hits_top1` per iteration and beam (charter §13 M4, §7)
  3. A 10-iteration campaign finishes in under 5 minutes on the laptop (charter §13 M4)
  4. A zero-match iteration consumes no budget and is recorded as a `no_match` event (charter §13 M4)

**Freezes**: hypothesis, query and tag vocabulary (`protocol/schemas/hypothesis.json`, `query.json`, `tag-vocabulary.json`) (charter §7, §13 M4)
**Plans**: TBD

The input (problem spec at seed 0, Phase 2 snapshot, the deterministic selector rule, max 400 evals) and expected output (`meta.json`, ≈10×(1+1+4+≤40+1) ledger events, `usage.json {evals ≤ 400, cpu_hours 0, tokens 0}`, `results.csv`) are specified in charter §13 "첫 e2e (M4)". The resulting curve is a liveness check, not a research result.

### Phase 6: LLM Loop

**Goal**: A stateful hypothesis agent and a stateless translator drive the unchanged loop through one provider adapter, with blind feedback and facts-only memory, and the loop demonstrably changes its next query in response to observations — see charter §13 M5.
**Charter milestone**: M5
**Depends on**: Phase 5; gate D-14 (see Gate note)
**Requirements**: LLM-01, LLM-02, LLM-03, LLM-04, LLM-05
**Success Criteria** (what must be TRUE) — charter §13 M5:

  1. A 10-iteration LLM campaign completes end to end (charter §13 M5)
  2. The schema pass rate of agent responses is recorded for the campaign (charter §13 M5)
  3. Two same-seed runs, feedback on versus off, show a documented query diff from iteration 2 onward — success layer L3 (charter §13 M5)
  4. Tokens and USD are recorded in `usage.json` alongside `evals` and `cpu_hours` (charter §13 M5)
  5. The A-4 payload test — nothing sent to the provider carries row ids, table size, percentiles, thresholds or global statistics — runs inside the check gate (charter §13 M5, A-4, D-19)

**Freezes**: prompts v1 (`protocol/prompts/hypothesis_v1.md`, `translator_v1.md`), feedback format (`protocol/schemas/feedback.json`) (charter §7, §13 M5)
**Gate**: D-14 (LLM provider, API key, budget) is undecided and is fixed by the owner at M5 entry. Transition M4→M5 requires the Phase 5 exit criteria, a D-14 key present in `.env`, and `config/llm.json` passing its schema (charter §13 transition conditions). This roadmap does not choose a provider; `llm4pol.llm.provider` is written against the adapter contract, and the concrete provider enters via `config/llm.json` once D-14 is recorded.
**Plans**: TBD

### Phase 7: Variance, Controls, Pre-registration

**Goal**: Replicate variance and a zero-feedback control are measured, and the comparison protocol is pre-registered with a committed hash before any comparison number is claimed — see charter §13 M6.
**Charter milestone**: M6
**Depends on**: Phase 6; gate D-15 (see Gate note)
**Requirements**: VAR-01, VAR-02, VAR-03
**Success Criteria** (what must be TRUE) — charter §13 M6:

  1. Ten replicates each of the deterministic, LLM and zero-feedback arms have run, and σ of the final-iteration percentile is reported per arm (charter §13 M6)
  2. The zero-feedback arm's memorisation share is reported (charter §13 M6)
  3. `experiments/PREREG-<date>.md` fixing objective form, thresholds, metrics, comparison arms and replicate count exists and its sha256 is committed (charter §13 M6)

**Freezes**: D-16 — objective form, thresholds, metrics and replicate count, via `experiments/PREREG-<date>.md` with committed sha256 (charter §7, §13 M6)
**Gate**: D-15 (replicate count and multiplicity correction; development default 10 replicates, decided by MDE, Holm) is measured in this phase, and D-16 (objective form and thresholds; development default constrained single, ε ≤ table Q25, Tg ≥ 400 K) is fixed by the owner at pre-registration. Both remain gated until the owner records them; a value that differs from the development default is recorded in `governance/AMENDMENTS.md` (ADR-0005). This roadmap fixes neither. Transition M6→M7 = σ and memorisation share reported + pre-registration sha256 committed; no comparison figure is claimed before that (charter §13).
**Plans**: TBD

### Phase 8: Comparison Arms

**Goal**: Random, GA and BO arms run against the same evaluator at a matched budget so the pre-registered comparison can be reported with its population and n — see charter §13 M7.
**Charter milestone**: M7
**Depends on**: Phase 7 (transition M6→M7 satisfied: σ and memorisation share reported, pre-registration sha256 committed)
**Requirements**: CMP-01, CMP-02
**Success Criteria** (what must be TRUE) — charter §13 M7:

  1. Realised `evals` of each of the random, GA and BO arms are within ±5 % of the LLM arm (charter §13 M7)
  2. Both budget currencies (`evals`, `cpu_hours`) are reported for every arm (charter §13 M7)
  3. The results table states the population and `n` per beam for every comparison (charter §13 M7)

**Freezes**: nothing (charter §13 M7)
**Plans**: TBD

## Gated follow-ons (M8, M9 — tracked as REQUIREMENTS.md follow-ons, not phases in this roadmap)

- **M8 sim-to-real** (charter §13 M8, gated **D-17** experimental TC source; requirements S2R-01..03 in REQUIREMENTS.md v2). Depends on M6 and D-17; charter §8 permits M7 ∥ M8 once D-17 is fixed. First appearance of the PoLyInfo loader; D-1..D-6 are promoted to tests when it is written.
- **M9 live mode** (charter §13 M9, gated **D-18** live scope; requirements LIVE-01..03). Depends on M8 and D-18 plus `config/hpc.json`.

Both enter the roadmap through `/gsd-new-milestone` when the owner records the gate decision; until then they are tracked, not planned.

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 (charter §8 build order).

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 1/1 | Complete    | 2026-09-22 |
| 2. Data Foundation | 5/5 | Complete    | 2026-09-22 |
| 3. Evaluator (table backend) | 0/? | Not started | - |
| 4. Run Management | 0/? | Not started | - |
| 5. Deterministic End-to-End | 0/? | Not started | - |
| 6. LLM Loop | 0/? | Not started | - |
| 7. Variance, Controls, Pre-registration | 0/? | Not started | - |
| 8. Comparison Arms | 0/? | Not started | - |

---
*Roadmap created: 2026-09-21 from charter v1.0 §8/§13; drift review against the charter required before implementation starts (ADR-0002, charter §14)*
