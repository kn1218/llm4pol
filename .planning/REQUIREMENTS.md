# Requirements: LLM4POL

**Defined:** 2026-09-21
**Core Value:** The loop attributes a measured gain to a design axis under a matched evaluation budget.
**Source:** `docs/MASTER-PLAN.md` v1.0 §4, §6, §7, §13. Every requirement cites the charter
section it derives from; the charter's exit criteria are the acceptance tests. This file is
subordinate to the charter (ADR-0002).

## v1 Requirements

### Foundation (charter §13 M0)

- [x] **FOUND-01**: The check gate (`pixi run --manifest-path env/pixi.toml check`) passes on windows-latest and ubuntu-latest from a committed lock file
- [x] **FOUND-02**: `huggingface_hub` is available in the locked environment so the snapshot fetch runs identically on both platforms
- [x] **FOUND-03**: Secrets are read only from `.env`; no secret value is printed, logged or committed (R-3), and `.env` is never tracked

### Data foundation (charter §13 M1, §6, §10)

- [x] **DATA-01**: `llm4pol.data.fetch` acquires PolyOmics `general_polymers` at a pinned Hugging Face revision and verifies each file's sha256 and size against `data/MANIFEST-open.sha256`
- [x] **DATA-02**: `llm4pol.data.load` produces one parquet snapshot `data/processed/polyomics-<rev>.parquet` with a declared pyarrow schema and the snapshot identifier `polyomics:general_polymers@<rev>`
- [x] **DATA-03**: The property registry (`protocol/schemas/property-registry.json`) declares key, column, unit and condition for `thermal_conductivity`, `dielectric_const_dc`, `tg`, `rg`, `r2`, `ffv`, `sp_ced`, `density`, `refractive_index`; `static_dielectric_const` is absent (A-7)
- [x] **DATA-04**: `llm4pol.data.identity` computes `candidate_id = sha256(canonical_psmiles + "|" + tacticity)[:16]` with a stereo-aware canonical repeat-unit SMILES (D-6)
- [x] **DATA-05**: Rows sharing a `candidate_id` are grouped as replicates; the candidate value is the replicate median with count and spread preserved (D-7, D-9, D-10)
- [x] **DATA-06**: `llm4pol.data.validate` emits a validator report (`docs/audit/polyomics-<rev>-validation.md`) that reproduces or documents the difference for: row count, unique repeat units, filtered triple count 43,561, `static_dielectric_const` Maxwell violation 88.9 %, `dielectric_const_dc` violation 0, and resolves 95,335 vs 73,045
- [x] **DATA-07**: The validator report records the replicate structure and the replicate noise floor of `thermal_conductivity`, `dielectric_const_dc` and `tg`
- [x] **DATA-08**: The validator report states the feasible-set size under the development default thresholds (ε ≤ table Q25, Tg ≥ 400 K)
- [x] **DATA-09**: Tg rows are filtered by `tg_rmse` and to 100–900 K; the filter counts are recorded (ADR-0004 §2)
- [x] **DATA-10**: Invariants D-7..D-10 and A-7 are promoted from prose to tests in the same change that adds the loader

### Evaluator (charter §13 M2, §7, §4 A-1..A-3)

- [ ] **EVAL-01**: Evaluator request and response payloads validate against `protocol/schemas/eval-request.json` and `eval-response.json`, and the test suite loads those schemas
- [ ] **EVAL-02**: Each (candidate, property) response carries exactly one status in `{ok, unsupported, missing, error}`; `unsupported` (not in registry) and `missing` (row present, value absent) consume no budget; `error` is retryable
- [ ] **EVAL-03**: Every response carries `backend`, `source`, `provenance_tier`, `n_replicates`, `spread`, `unit` and `cost {evals, cpu_hours}`
- [ ] **EVAL-04**: The cache is keyed by `(candidate_id, property, backend, source)`; a cache hit leaves `evals` unchanged
- [ ] **EVAL-05**: A batch request of 100 entries returns responses in request order with matching count
- [ ] **EVAL-06**: import-linter contracts forbid `llm4pol.loop` → `llm4pol.evaluate.backends.radonpy`, `llm4pol.evaluate` → `llm4pol.loop`/`llm4pol.llm`, and restrict `llm4pol.llm` to `llm4pol.loop.agents` (A-1, A-2)

### Run management (charter §13 M3, §7, §4 A-3, A-6)

- [ ] **RUN-01**: A run has id `<UTC timestamp>-<8 hex>`; `experiments/<run-id>/meta.json` records problem spec, code git sha, prompt versions, provider/model, seed and snapshot hash
- [ ] **RUN-02**: `ledger.jsonl` is append-only; one event per selection, evaluation, feedback and iteration-close; a rerun gets a new id
- [ ] **RUN-03**: `resume` continues from the last closed iteration and never records the same `(run_id, iteration, beam)` event twice
- [ ] **RUN-04**: `replay` regenerates `results.csv` from the ledger alone, byte-identical to the original
- [ ] **RUN-05**: `usage.json` totals for `evals` and `cpu_hours` equal the ledger sums; tokens and USD are reported separately
- [ ] **RUN-06**: Problem specs validate against `protocol/schemas/problem-spec.json`

### Deterministic end-to-end (charter §13 M4, §7)

- [ ] **LOOP-01**: Hypotheses and queries validate against `protocol/schemas/hypothesis.json` and `query.json`; the tag vocabulary is frozen in `protocol/schemas/tag-vocabulary.json`
- [ ] **LOOP-02**: Tags on the A2 (chemistry) and A3 (backbone) axes are computed deterministically with RDKit SMARTS; no LLM-written field is used as a filter
- [ ] **LOOP-03**: Four beams `full`, `chem`, `primary`, `random` are built from one query with the same seeded, target-blind stratified sampling rule; `n` per beam is recorded in `results.csv`
- [ ] **LOOP-04**: A zero-match iteration consumes no budget and is recorded as a `no_match` event
- [ ] **LOOP-05**: `llm4pol run --selector deterministic` completes a 10-iteration campaign on the laptop in under 5 minutes, and two runs with the same seed produce identical `ledger.jsonl` and `results.csv`
- [ ] **LOOP-06**: `results.csv` reports per iteration and beam: `n`, `median_tc`, `feasible_frac`, `pct_of_table`, `hits_top10`, `hits_top1`

### LLM loop (charter §13 M5, §4 A-4, A-5) — gated on D-14

- [ ] **LLM-01**: One provider adapter (`llm4pol.llm.provider`) configured by `config/llm.json` with a sibling schema; keys come only from `.env`
- [ ] **LLM-02**: A stateful hypothesis agent and a stateless translator agent run from versioned prompts `protocol/prompts/hypothesis_v1.md` and `translator_v1.md`; a prompt that produced a reported result is never edited in place
- [ ] **LLM-03**: Feedback to the agent contains the ledger's facts-only memory and the four beam tables, and a test proves the payload carries no row ids, table size, percentiles, thresholds or global statistics
- [ ] **LLM-04**: A 10-iteration LLM campaign completes; the schema pass rate of agent responses and tokens/USD per campaign are recorded in `usage.json`
- [ ] **LLM-05**: Observation response is demonstrated: two runs with the same seed, feedback on versus off, produce a documented query diff from iteration 2 onward (success layer L3)

### Variance, controls, pre-registration (charter §13 M6) — fixes D-16

- [ ] **VAR-01**: A replicate battery runs 10 replicates of each of the deterministic, LLM and zero-feedback arms and reports σ of the final-iteration percentile
- [ ] **VAR-02**: The zero-feedback arm's memorisation share is reported
- [ ] **VAR-03**: `experiments/PREREG-<date>.md` fixes objective form, thresholds, metrics, comparison arms and replicate count, and its sha256 is committed before any comparison is claimed

### Comparison arms (charter §13 M7)

- [ ] **CMP-01**: Random, GA and BO arms run against the same evaluator with realised `evals` within ±5 % of the LLM arm
- [ ] **CMP-02**: Every reported comparison states population, `n` per beam and both budget currencies

## v2 Requirements

Gated follow-ons; tracked, not in the current roadmap until their gate opens.

### Sim-to-real (charter §13 M8) — gated on D-17

- **S2R-01**: An experimental thermal-conductivity table backend uses the same evaluator contract with a different `source`
- **S2R-02**: The PoLyInfo loader promotes invariants D-1..D-6 to tests when it is first written
- **S2R-03**: Overlapping repeat units are counted and the rank correlation with CI between PolyOmics and experimental TC is reported

### Live mode (charter §13 M9) — gated on D-18

- **LIVE-01**: `llm4pol.evaluate.backends.radonpy` implements the evaluator contract with `provenance_tier` distinct from `table`
- **LIVE-02**: `config/hpc.json` and `scripts/submit.py` exist per the hpc-submit skill; one candidate round-trips
- **LIVE-03**: The difference between `table` and `radonpy` values is reported for every finalist

## Out of Scope

| Feature | Reason |
|---------|--------|
| Molecular-weight / dispersity design | Not in the data; Mw/Mn = 1.0 on every row (ADR-0004) |
| Copolymer composition axis | `general_polymers` is homopolymer (D-10) |
| In-loop MD oracle | Allocation is small; MD is a spot check (D-06, ADR-0003) |
| Surrogate model in the loop | Would optimise another model's biases (ADR-0003); needs a scaffold-grouped split ADR first |
| Regime concept from the July proposal | Unapproved input; revisit after M5 |
| Physical DB split for LLM blindness | Blindness is guaranteed by the payload test (A-4), not by storage |
| Multi-agent / service architecture for the two agents | Roles are prompts and state, not processes (charter §5) |

## Traceability

Which phases cover which requirements. Phase N is charter milestone M(N-1); see `ROADMAP.md`. Filled during roadmap creation on 2026-09-21.

| Requirement | Phase | Status |
|-------------|-------|--------|
| FOUND-01 | Phase 1 (Foundation) | Complete |
| FOUND-02 | Phase 1 (Foundation) | Complete |
| FOUND-03 | Phase 1 (Foundation) | Complete |
| DATA-01 | Phase 2 (Data Foundation) | Complete |
| DATA-02 | Phase 2 (Data Foundation) | Complete |
| DATA-03 | Phase 2 (Data Foundation) | Complete |
| DATA-04 | Phase 2 (Data Foundation) | Complete |
| DATA-05 | Phase 2 (Data Foundation) | Complete |
| DATA-06 | Phase 2 (Data Foundation) | Complete |
| DATA-07 | Phase 2 (Data Foundation) | Complete |
| DATA-08 | Phase 2 (Data Foundation) | Complete |
| DATA-09 | Phase 2 (Data Foundation) | Complete |
| DATA-10 | Phase 2 (Data Foundation) | Complete |
| EVAL-01 | Phase 3 (Evaluator (table backend)) | Pending |
| EVAL-02 | Phase 3 (Evaluator (table backend)) | Pending |
| EVAL-03 | Phase 3 (Evaluator (table backend)) | Pending |
| EVAL-04 | Phase 3 (Evaluator (table backend)) | Pending |
| EVAL-05 | Phase 3 (Evaluator (table backend)) | Pending |
| EVAL-06 | Phase 3 (Evaluator (table backend)) | Pending |
| RUN-01 | Phase 4 (Run Management) | Pending |
| RUN-02 | Phase 4 (Run Management) | Pending |
| RUN-03 | Phase 4 (Run Management) | Pending |
| RUN-04 | Phase 4 (Run Management) | Pending |
| RUN-05 | Phase 4 (Run Management) | Pending |
| RUN-06 | Phase 4 (Run Management) | Pending |
| LOOP-01 | Phase 5 (Deterministic End-to-End) | Pending |
| LOOP-02 | Phase 5 (Deterministic End-to-End) | Pending |
| LOOP-03 | Phase 5 (Deterministic End-to-End) | Pending |
| LOOP-04 | Phase 5 (Deterministic End-to-End) | Pending |
| LOOP-05 | Phase 5 (Deterministic End-to-End) | Pending |
| LOOP-06 | Phase 5 (Deterministic End-to-End) | Pending |
| LLM-01 | Phase 6 (LLM Loop) | Pending |
| LLM-02 | Phase 6 (LLM Loop) | Pending |
| LLM-03 | Phase 6 (LLM Loop) | Pending |
| LLM-04 | Phase 6 (LLM Loop) | Pending |
| LLM-05 | Phase 6 (LLM Loop) | Pending |
| VAR-01 | Phase 7 (Variance, Controls, Pre-registration) | Pending |
| VAR-02 | Phase 7 (Variance, Controls, Pre-registration) | Pending |
| VAR-03 | Phase 7 (Variance, Controls, Pre-registration) | Pending |
| CMP-01 | Phase 8 (Comparison Arms) | Pending |
| CMP-02 | Phase 8 (Comparison Arms) | Pending |

**Coverage:**

- v1 requirements: 41 total (3 FOUND + 10 DATA + 6 EVAL + 6 RUN + 6 LOOP + 5 LLM + 3 VAR + 2 CMP)
- Mapped to phases: 41
- Unmapped: 0 ✓
- v2 (gated, not in roadmap): 6 (S2R-01..03 gated D-17, LIVE-01..03 gated D-18)

---
*Requirements defined: 2026-09-21*
*Last updated: 2026-09-21 after roadmap creation (traceability filled, count corrected 40 → 41)*
