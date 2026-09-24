---
phase: 02-data-foundation
plan: 06
scope: "Plan 02-06 (ADR-0006 tacticity resolution) + regression re-verification of the already-verified Phases 2 and 3"
verified: 2026-09-24T06:25:10Z
status: passed
score: 21/21 must-haves verified
covered_files:
  - ".planning/REQUIREMENTS.md"
  - ".planning/phases/02-data-foundation/02-06-PLAN.md"
  - ".planning/phases/02-data-foundation/02-06-SUMMARY.md"
  - ".planning/phases/02-data-foundation/02-CONTEXT.md"
  - ".planning/phases/02-data-foundation/02-VERIFICATION.md"
  - ".planning/phases/03-evaluator-table-backend/03-VERIFICATION.md"
  - "docs/audit/README.md"
  - "docs/audit/polyomics-041e5834-validation.md"
  - "docs/governance/ADR/0006-tacticity-resolution-in-candidate-identity.md"
  - "docs/governance/INVARIANTS.md"
  - "protocol/examples/eval-response.example.json"
  - "src/llm4pol/data/expectations.py"
  - "src/llm4pol/data/filters.py"
  - "src/llm4pol/data/identity.py"
  - "src/llm4pol/data/load.py"
  - "src/llm4pol/data/validate.py"
  - "tests/conftest.py"
  - "tests/test_data_cli.py"
  - "tests/test_data_identity.py"
  - "tests/test_data_invariants.py"
  - "tests/test_data_real_file.py"
  - "tests/test_data_schema.py"
  - "tests/test_evaluate_cli.py"
  - "tests/test_evaluate_contract.py"
  - "tests/test_evaluate_real_file.py"
  - "tests/test_evaluate_table.py"
covered_digest: "v1:sha256:0ca01d93e0c0200a67da2777d9a1b9619086abbf5ec0d8e725155e4b4ba617a1"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  kind: "scoped regression re-verification (no prior 02-06-VERIFICATION.md existed)"
  previous_artifacts:
    - "02-VERIFICATION.md — status passed, 26/26, verified 2026-09-21T20:26:40Z"
    - "03-VERIFICATION.md — status passed, 23/23, verified 2026-09-21T22:24:16Z"
  gaps_closed: []
  gaps_remaining: []
  regressions: []
  intentional_number_changes:
    - "unique_candidate_ids 78,676 -> 78,375 (ADR-0006, D-25). Every Phase-2/Phase-3 artifact that quoted the pre-ADR value was moved in the same commit; the historical SUMMARY/VERIFICATION records were correctly left unrewritten."
gaps: []
deferred: []
advisory:
  - finding: "`actuals.commits: 4` in 02-06-SUMMARY.md frontmatter undercounts. From `plan_head_before` d0d5588 there were 5 commits at the moment the summary was written (4 task commits + the summary commit itself) and 6 at HEAD (the post-summary ADR correction e8a9477)."
    category: other
    reason: "The executor's own explanation — measured before the metadata commit — is correct for the off-by-one at authoring time, but it is now off by two. Cosmetic planning metadata; no artifact, number or guard depends on it. Resolution: set `commits: 6` or leave it and note the post-summary commit."
    evidence_status: "reproduced: `git rev-list --count d0d5588..HEAD` -> 6; `git log --oneline d0d5588..HEAD` -> 51ac2cd, 35febb0, 5e7b296, 1277838, 9c62e89, e8a9477"
  - finding: "02-06-SUMMARY.md § Next Phase Readiness and § Deviations 1 both state that ADR-0006's Consequences wording slip was 'flagged for the owner; not edited here'. Commit e8a9477 (post-summary) did edit it, so the summary is stale on that point."
    category: other
    reason: "The ADR now reads correctly and the corrected text was independently re-derived in this verification (55 no-label canonicals behind all 60 unresolved rows; neither of the 2 multi-label canonicals carries an empty row). The staleness is in the narrative only, in the benign direction. Resolution: one sentence in the summary, or leave it as a record of what was true when written (consistent with the plan's own no-rewrite policy)."
    evidence_status: "reproduced: `git show e8a9477` is a 6-insertion/2-deletion prose edit to the ADR Context section; the summary text predates it"
  - finding: "STATE.md still reports `completed_phases: 1` and `Progress: [░░░░░░░░░░] 0%` while ROADMAP.md's table marks phases 1, 2 and 3 Complete."
    category: other
    reason: "Pre-existing before this plan and explicitly left alone by the executor, as claimed. The GSD-tooling regressions this run DID introduce (ROADMAP Phase 2 row -> 'In Progress' with an empty date; `completed_phases` -> 0) were restored by hand and the committed state is correct. Only the older counter/bar discrepancy remains. Resolution is a GSD state-tooling fix, not a code change."
    evidence_status: "reproduced: `git diff d0d5588..HEAD -- .planning/STATE.md` shows `completed_phases: 1` as an unchanged context line and the 0% bar untouched; the ROADMAP row reads `| 2. Data Foundation | 6/6 | Complete | 2026-09-24 |`"
  - finding: "HEAD (e8a9477) is one commit ahead of the CI-verified sha 1277838 on a non-.planning path: the ADR prose correction. The cited green two-platform run does not cover HEAD."
    category: other
    reason: "A fresh `workflow_dispatch` at HEAD is needed to keep the project's own convention (R-4: the gate green at the tip on both platforms). Risk is negligible: the edit is prose inside an ADR body, its Status/Date lines are unchanged, no gate step reads ADR prose, and the verifier ran the full seven-step gate at HEAD on this workstation (7/7, 189 passed). Not dispatched per instruction; not raised as a human-judgement item."
    evidence_status: "reproduced: `git diff --name-only 1277838..HEAD -- . ':(exclude).planning'` -> docs/governance/ADR/0006-tacticity-resolution-in-candidate-identity.md"
behavior_unverified_items: []
coincidental_reliance_items: []
human_verification: []
---

# Phase 2 Plan 06: ADR-0006 tacticity resolution — Verification Report

**Plan goal:** a missing `tacticity` is resolved from its labelled twin before the candidate
identity is taken; the committed validator report is republished; the D-11 guard is promoted; no
row-level finding moved detectably; every Phase 2 and Phase 3 truth still holds.

**Verified:** 2026-09-24T06:25:10Z at HEAD `e8a9477`, working tree clean, `main...origin/main` in sync.
**Status:** passed
**Re-verification:** Yes — scoped regression pass over the already-verified Phases 2 and 3. No prior
`02-06-VERIFICATION.md` existed.

Every claim below was reproduced by command in this verifier's own process. `02-06-SUMMARY.md` was
used only to locate what to check; nothing was accepted on its say-so. The ADR-0006 numbers were
additionally re-derived **outside** the `llm4pol` package, from the pinned CSV with plain pandas and
RDKit, so the loader cannot corroborate itself.

## Goal Achievement

### A. Plan 02-06 observable truths

| #  | Truth | Status | Evidence |
| -- | ----- | ------ | -------- |
| T1 | On the pinned snapshot, `load` writes 95,332 in-scope rows (unchanged) and **78,375** candidates — 301 fewer than 78,676 | ✓ VERIFIED | `python -m llm4pol.data load` → `read 95,335 rows x 259 columns; excluded 3 second-monomer rows, 0 parse failures; wrote 95,332 rows …; 78,375 candidates`. Independent re-derivation (plain pandas + RDKit, no `llm4pol` import): in-scope 95,332, unique canonical 78,373, **candidates POST-ADR 78,375, PRE-ADR 78,676, delta 301**. `test_real_load_writes_95332_rows_and_78375_candidates` PASSED by name |
| T2 | Of 554 in-scope empty-`tacticity` rows: 312 `none`, 182 `atactic`, 0 `isotactic`, 0 `syndiotactic`, 60 stay `unknown`; exactly 2 canonicals carry >1 distinct label; all seven published with their population | ✓ VERIFIED | Validator: `tacticity_empty_in_scope 554`, `…_resolved_none 312`, `…_resolved_atactic 182`, `…_resolved_isotactic 0`, `…_resolved_syndiotactic 0`, `tacticity_unresolved 60`, `tacticity_multi_label_canonical 2` — all `reproduce … reproduced`. Independent re-derivation returns the same seven. Report § `Tacticity resolution (ADR-0006)` carries all seven rows each with a `population` cell (`in-scope rows` / `in-scope rows with an empty tacticity`). `test_real_tacticity_resolution_counts_match_adr_0006` PASSED by name |
| T3 | No candidate carries a `tacticity` its own canonical was never observed with; two distinct labelled twins keep `unknown`; both guards named in the D-11 row of INVARIANTS.md | ✓ VERIFIED | Both named tests exist, are in the 189-test gate collection, and PASSED individually. Bodies are substantive (the first loads the synthetic root and rebuilds the label map from the raw source; the second is a 5-entry two-label case asserting `resolved[2] == unknown`). **Stronger, independent check:** my own pass over the pinned snapshot found **0** rows leaving with a label their canonical was not observed with. `sed -n '/^| D-11 /p' docs/governance/INVARIANTS.md` names `resolve_tacticity`, both `test_d11_*` tests and the report table |
| T4 | The committed report is republished, byte-identical to a fresh run, and every candidate-level number in it is the value the code now produces | ✓ VERIFIED | Fresh `python -m llm4pol.data validate` → `VALIDATION: 56 reproduced, 38 documented, 0 failed -> exit 0`; then `git diff --exit-code -- docs/audit/` exits 0 (byte-identical) and `git status --porcelain` is empty. `test_real_validate_exits_0_and_committed_report_is_byte_identical_to_a_fresh_run` PASSED by name. Two republished candidate-level values re-derived independently: multi-row candidates **13,014**, max rows in a candidate **22**, sizes summing to 95,332 — matching the summary's republished table and the validator |
| T5 | `identity.candidate_id` keeps its signature and its pure vectors; resolution happens over the whole frame in `load`, never per row | ✓ VERIFIED | `load.add_identity` calls `resolve_tacticity(kept_canonical, tacticity)` once, after `normalise_tacticity` and before the `candidate_id` comprehension (read in source). `candidate_id` is unchanged: my independent sha256 implementation returns `d220c5c57c4fae2e` for `("*CC*", "unknown")`. `identity.py` imports only `hashlib`, `math`, `collections.abc`, RDKit — still pandas-free |
| T6 | Every fixture-derived and real-file expectation that quoted a pre-ADR number is green in the same commit; the synthetic root yields 8 candidates with `*CC*`/`none` at n = 4; the protocol example is regenerated; the three `test_evaluate_table.py` counts stay exact equalities | ✓ VERIFIED | Independent synthetic build: **8 candidates**, 12 rows, `7ec8cb49ff317efc` (`*CC*`/`none`) `n_rows 4`, TC median 0.315, std 0.017078. Independent CLI drive `python -m llm4pol.evaluate --request protocol/examples/eval-request.example.json --root <fresh synthetic root>` → output **equals the committed example exactly**, and the file equals `json.dumps(…, indent=2, sort_keys=True) + "\n"` with no CR. Exact equalities confirmed by reading the file: `assert len(ids) == 9` (L272), `assert response.cost.evals == 8` (L289), `assert len(charged) == len(set(charged)) == 8` (L291), `assert response.cost == Cost(8, 0.0)` (L305) — none relaxed to a bound or subset |
| T7 | No row-level count moved detectably, established by a command | ✓ VERIFIED | The plan's row-level guard, run with the pre-flip sha substituted (`git diff -U0 35febb08…..HEAD -- src/llm4pol/data/expectations.py \| grep '^-' \| grep -cE '…'`) prints **0**. Independently: `in_scope_rows 95,332`, `unique_canonical 78,373`, `raw_string_merges 5`, `multi_tacticity_smiles_with_unknown 303 / without_unknown 2 / unknown_twins 301`, `tacticity_none 48,790 / atactic 45,032 / isotactic 951 / syndiotactic 8 / unknown 554` — all `reproduce … reproduced`; my own pandas run gives 95,332 and 78,373. The residual gap the summary states (a `documented` row-level finding drifting inside its own tolerance is invisible to both guard and validator) is correct and honestly scoped |
| T8 | `02-CONTEXT.md` D-03 states its NaN rule is superseded by ADR-0006 and points at it; no SUMMARY, VERIFICATION, RESEARCH or prior PLAN is rewritten | ✓ VERIFIED | D-03 now reads "…**the rule for when a missing value keeps that spelling is superseded by ADR-0006**…(see `docs/governance/ADR/0006-…md` and DECISIONS-LOG D-25)". `git diff --name-only d0d5588..HEAD` touches no prior SUMMARY/PLAN/RESEARCH; `02-VERIFICATION.md` still carries `78,676` 4× and `02-01-SUMMARY.md` 6× |
| T9 | The seven-step gate is green locally and in a `workflow_dispatch` CI run on both platforms with the real-file tests skipping by design | ✓ VERIFIED | Local at HEAD: `Steps: ruff check, ruff format --check, mypy, import-linter, schema-inventory, history-secret-scan, pytest`; `Contracts: 4 kept, 0 broken.`; `189 passed in 55.43s`; `SUMMARY: 7/7 steps passed`; exit 0. CI `gh run view 35962545625` → `conclusion success`, `event workflow_dispatch`, `headBranch main`, `headSha 1277838…`, both `check (windows-latest)` and `check (ubuntu-latest)` success; log grep → `SUMMARY: 7/7 steps passed` ×2, `Contracts: 4 kept, 0 broken.` ×2, `172 passed, 17 skipped` on each (172 + 17 = 189 = the local collection). See advisory 4 on the one-commit gap to HEAD |

### B. Phase 2 regression truths (from `02-VERIFICATION.md`)

The candidate-level numbers Phase 2 recorded moved **by design** under ADR-0006. The truths behind
them were re-checked in their post-ADR form; the historical record was correctly not rewritten.

| #  | Truth | Status | Evidence |
| -- | ----- | ------ | -------- |
| B1 | P1.2 — `load` writes both parquets with the declared shape and snapshot metadata | ✓ VERIFIED | `pq.read_metadata`: rows parquet **95,332 × 262** (unchanged), candidates parquet **78,375 × 49** (was 78,676); both carry `llm4pol.snapshot=polyomics:general_polymers@041e5834`, `llm4pol.revision`, `llm4pol.source_rows=95335`, `llm4pol.source_columns=259`, `excluded_second_monomer=3`, `excluded_parse_failure=0`, `source_sha256=71e955ac…` — identical to the values Phase 2 recorded |
| B2 | P3.5 / M1(2) — identity counts on the pinned file | ✓ VERIFIED | `in_scope_rows 95,332`, `unique_canonical 78,373` **unchanged**; `unique_candidate_ids 78,375` (was 78,676) — the one intended move. Candidate sizes sum to 95,332 (independently re-derived). `test_real_candidates_have_unique_ids_and_sizes_sum_to_in_scope_rows` in the green gate |
| B3 | M1(2)/(5)/DATA-06 — the committed report remains the number authority: every figure reproduced or documented | ✓ VERIFIED | `VALIDATION: 56 reproduced, 38 documented, 0 failed -> exit 0`. Row-level headline findings all still `reproduced` at their Phase-2 values (43,561 triple, 42,733, 38,693, 88.82, dc 0, Tg window 56,064 / 52,753 / 3,311, tg_rmse ladder) — none appears on a removed line of `expectations.py` since the pre-flip sha |
| B4 | M1(4)/R3/DATA-07 — replicate structure and per-property noise floor recorded with populations | ✓ VERIFIED | Republished from the validator: multi-row candidates 13,014 (was 12,983), max rows 22 (was 17) — both **independently re-derived** by this verifier. The `documented` noise-floor band was deliberately not reset (drift stayed inside tolerance), so the guard is not spent. `test_d9_report_states_noise_floor_per_property_with_population` in the green gate |
| B5 | M1(6)/DATA-10 — D-7..D-10 and A-7 guards still collected and green; D-11 added without renumbering or damaging them | ✓ VERIFIED | `git diff d0d5588..HEAD -- docs/governance/INVARIANTS.md` is a **pure addition**: one intro sentence plus the D-11 row. D-1..D-10 and A-1, A-2, A-3, A-7 cells byte-unchanged. All guard-named tests are in the 189-test collection and the gate is 7/7 |
| B6 | Data policy (ADR-0001, charter §10) | ✓ VERIFIED | `git ls-files data/` → exactly `data/MANIFEST-open.sha256`, `data/MANIFEST.sha256`, `data/README.md`. `git status --porcelain` empty after regenerating both parquets. Report scan: 16-hex tokens **0**, UUID-shaped tokens **0**, `*…*` repeat-unit SMILES **0**; the only `smiles` occurrences are column/finding names. 02-06-SUMMARY.md: 0 UUIDs, and its only 16-hex tokens are the synthetic `7ec8cb49ff317efc` and the pure vector `d220c5c57c4fae2e` |

### C. Phase 3 regression truths (from `03-VERIFICATION.md`)

| #  | Truth | Status | Evidence |
| -- | ----- | ------ | -------- |
| C1 | SC1 / T2 — the synthetic example yields the nine statuses in order with reasons and per-candidate charging | ✓ VERIFIED | My own CLI drive on a freshly built synthetic root: statuses `ok,ok,ok,missing,missing,ok,missing,unsupported,ok`; reasons `value_absent, value_absent, candidate_unknown`; per-result evals `[1,0,0,0,0,1,0,0,1]`; response cost `{evals 3, cpu_hours 0.0}` — **byte-for-byte the sequence `03-VERIFICATION.md` recorded** |
| C2 | SC3 / T4 — a 100-entry batch returns 300 results in request order; response cost is the sum of result costs | ✓ VERIFIED | `test_batch_of_100_synthetic_entries_returns_300_results_in_request_order` and `test_response_cost_is_the_sum_of_result_costs` PASSED individually after the count change (9 ids / 8 charged) |
| C3 | SC4 / T3 — every result carries `source`, `backend`, `provenance_tier`, cost `{evals, cpu_hours}` | ✓ VERIFIED | My CLI drive: tiers `{md_simulated}`, backends `{table}`, sources `{polyomics:general_polymers@041e5834}` on all 9 results; cost keys exactly the two |
| C4 | T5 — the committed response example equals the evaluator's own output on the synthetic root | ✓ VERIFIED | Independent CLI drive output `== committed example` → **True**; canonical formatting `json.dumps(indent=2, sort_keys=True) + "\n"` → True; no CR. `test_committed_response_example_equals_evaluator_output_on_the_synthetic_root` PASSED by name. The `7ec8cb49ff317efc` TC 0.315 / n 4 / spread 0.017078 in the example matches the candidate table I built independently |
| C5 | T4/SC3 evidence not weakened — the three candidate-count assertions stay exact equalities | ✓ VERIFIED | Read directly from `tests/test_evaluate_table.py`: `len(ids) == 9`, `response.cost.evals == 8`, `len(charged) == len(set(charged)) == 8`, `response.cost == Cost(8, 0.0)`. No `>=`, `<=`, `in`, `issubset` or `approx` on any of them. `_synthetic_ids()`'s pre-existing subset assertion is untouched and is the only subset test in the file |
| C6 | A-1/A-5 — the frozen schemas are untouched by this plan; only an instance was regenerated | ✓ VERIFIED | `git diff d0d5588..HEAD -- protocol/schemas/` is **empty**. `protocol/examples/eval-response.example.json` is the only protocol file in the plan's diff. `Contracts: 4 kept, 0 broken.` locally and on both CI platforms |

**Score:** 21/21 truths verified (0 present, behavior-unverified).

Behavior-dependent truths — T1/T5 (the ordering invariant: resolution must run *before* the hash),
T3 (the never-an-unobserved-label invariant), T4 (report republication is idempotent), C1/C4
(evaluator state after the table changed shape) — were each upgraded to VERIFIED by a named test run
individually in this session **plus** a direct out-of-package reproduction, not by symbol presence.
The ordering in particular is proven by consequence: my own script computes 78,676 candidates when
the identity is taken on the unresolved label and 78,375 when it is taken on the resolved one.

### Independent re-derivation of ADR-0006 (no `llm4pol` import)

Plain `pandas.read_csv` on the pinned CSV + RDKit `MolFromSmiles`/`MolToSmiles(isomericSmiles=True)`
+ a local sha256, scope filter and twin rule written from the ADR text:

| Quantity | ADR-0006 / validator | Independent re-derivation | Agrees |
| --- | --- | --- | --- |
| source rows × columns | 95,335 × 259 | 95,335 × 259 | ✓ |
| second-monomer rows excluded | 3 | 3 | ✓ |
| parse failures excluded | 0 | 0 | ✓ |
| in-scope rows | 95,332 | 95,332 | ✓ |
| unique canonical | 78,373 | 78,373 | ✓ |
| empty `tacticity`, in scope | 554 | 554 | ✓ |
| resolved → `none` | 312 | 312 | ✓ |
| resolved → `atactic` | 182 | 182 | ✓ |
| resolved → `isotactic` / `syndiotactic` | 0 / 0 | 0 / 0 | ✓ |
| left `"unknown"` | 60 | 60 | ✓ |
| canonicals with ≥2 distinct labels (in scope) | 2 | 2 | ✓ |
| **distinct canonicals behind the 60 unresolved rows** | 55 | **55, every one with NO label at all** | ✓ |
| **multi-label canonicals that also carry an empty row** | 0 (ADR as corrected) | **0** | ✓ |
| candidates, post-ADR | 78,375 | 78,375 | ✓ |
| candidates, pre-ADR (rule not applied) | 78,676 | 78,676 | ✓ |
| D-11 violations on the pinned snapshot | 0 (guard is synthetic-only) | **0 over all 95,332 rows** | ✓ |
| multi-row candidates (n ≥ 2) | 13,014 | 13,014 | ✓ |
| max rows in a candidate | 22 | 22 | ✓ |
| `candidate_id("*CC*", "unknown")` | `d220c5c57c4fae2e` | `d220c5c57c4fae2e` | ✓ |

**The ADR-0006 correction (commit `e8a9477`) is right.** The file now reads: the 60 unresolved rows
come from 55 canonical SMILES that carry an empty row and no label at all; separately 2 canonical
SMILES carry more than one distinct label, but neither of those two carries an empty row, so the
second guard admits no rows on this snapshot and is enforced prospectively by a synthetic test. Every
clause of that paragraph was reproduced independently above. The pre-correction wording ("Two
canonical SMILES … are therefore left `unknown` by the rule's own guard") was indeed wrong.

### Deferred Items

None.

### Advisory (New Scope, Unevidenced)

| # | Finding | Category | Why Advisory |
|---|---------|----------|--------------|
| 1 | `actuals.commits: 4` undercounts (5 at authoring time, 6 at HEAD) | other | Planning metadata only; no guard or number depends on it |
| 2 | 02-06-SUMMARY says the ADR slip was "not edited here"; `e8a9477` edited it | other | Narrative staleness in the benign direction; the corrected ADR was independently verified |
| 3 | STATE.md `completed_phases: 1` / 0 % bar vs three Complete phases in ROADMAP | other | Pre-existing, correctly left alone; a GSD state-tooling issue |
| 4 | HEAD is one non-`.planning` commit (ADR prose) ahead of the CI-verified sha | other | A fresh dispatch is needed by convention; local 7/7 at HEAD; not dispatched per instruction |

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `src/llm4pol/data/identity.py` | `observed_labels`, `resolve_tacticity`; `candidate_id` / `normalise_tacticity` unchanged | ✓ VERIFIED | Both present, typed, pure (plain sequences in/out); module still imports only `hashlib`, `math`, `collections.abc`, RDKit. `resolve_tacticity` resolves only when `len(labels) == 1`. Wired from `load` |
| `src/llm4pol/data/load.py` | `add_identity` resolves the whole frame before hashing | ✓ VERIFIED | One call after `normalise_tacticity`/`kept_canonical`, before the `candidate_id` comprehension; `LoadResult` fields and the printed `load:` format unchanged |
| `src/llm4pol/data/filters.py` | `TacticityResolution`, `tacticity_resolution_counts(source, rows)` keyed on `row_index` | ✓ VERIFIED | Present, pure, joins `source.iloc[rows["row_index"]]`; `RESOLVED_LABELS` fixes the four label rows so a 0 publishes rather than vanishing. Docstring records why `multi_label_canonical` drops the plan's extra conjunct |
| `src/llm4pol/data/validate.py` | `Tacticity resolution (ADR-0006)` table; rewritten `_IDENTITY_INTRO`; `row_index` requested | ✓ VERIFIED | Table rendered with seven population-bearing rows; superseded sentence gone (`grep -c "stays a separate candidate in M1"` → 0) |
| `src/llm4pol/data/expectations.py` | 78,375 + seven resolution findings registered in `POPULATIONS` | ✓ VERIFIED | All seven reproduce against `in-scope rows` / `in-scope rows with an empty tacticity`; none fell through `population_of`'s `tacticity_` prefix to "all source rows" |
| `tests/test_data_invariants.py` | Two D-11 guards + the resolution-sum invariant | ✓ VERIFIED | All three collected and PASSED by name; bodies substantive |
| `tests/test_data_identity.py` | Three-branch vectors for `resolve_tacticity`; existing `candidate_id` vectors untouched | ✓ VERIFIED | Five new tests collected; the seven original vectors still green in the 189-test gate |
| `docs/audit/polyomics-041e5834-validation.md` | Republished authority with the resolution table | ✓ VERIFIED | Byte-identical to a fresh run; aggregates only |
| `docs/governance/INVARIANTS.md` | One guarded D-11 row; intro notes it comes from ADR-0006 | ✓ VERIFIED | Exactly one `| D-11 ` row naming both tests; pure addition |
| `protocol/examples/eval-response.example.json` | Equals the evaluator's output on the synthetic root | ✓ VERIFIED | Reproduced by an independent CLI drive, including formatting and LF endings |
| `protocol/schemas/**` | MUST BE UNCHANGED by this plan | ✓ VERIFIED | `git diff d0d5588..HEAD -- protocol/schemas/` empty |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `identity.resolve_tacticity` | `load.add_identity` → `candidate_id` | whole-frame pass after `normalise_tacticity`, before the hash | ✓ WIRED | Read in source; proven by consequence (78,676 → 78,375 when and only when the pass runs) |
| `load.add_identity` | `candidates-041e5834.parquet` → `evaluate.backends.table` | the candidate table is Phase 3's only input | ✓ WIRED | The committed protocol example changed with the table and still equals a live evaluator drive |
| `rows.row_index` | `source.iloc[...]` in `tacticity_resolution_counts` | the join recovering originally-empty rows | ✓ WIRED | `row_index` present in `validate._read_processed`'s `wanted`; the seven counts reproduce |
| `expectations.POPULATIONS` | `population_of` | explicit registration of every `tacticity_*` id | ✓ WIRED | Report rows show the intended populations, not "all source rows" |

### Data-Flow Trace (Level 4)

| Artifact | Data variable | Source | Produces real data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| `load.load` parquets | `rows`, `candidates` | pinned CSV → RDKit → `resolve_tacticity` → `groupby(candidate_id)` | Yes — 95,332 / 78,375 on disk with snapshot metadata | ✓ FLOWING |
| `validate.run` findings | `observed[...]` | `read_source` + both parquets → `filters.*` / `replicates.*` | Yes — 94 findings, the headline ones reproduced by this verifier's own pandas run | ✓ FLOWING |
| report resolution table | seven counts | `filters.tacticity_resolution_counts` over the `row_index` join | Yes — matches the independent derivation exactly | ✓ FLOWING |
| `eval-response.example.json` | result values | candidate parquet → `TableBackend` → `Evaluator` | Yes — reproduced by a live CLI drive | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Seven-step gate at HEAD | `pixi run --manifest-path env/pixi.toml check` | `Contracts: 4 kept, 0 broken.`; `189 passed in 55.43s`; `SUMMARY: 7/7 steps passed`; exit 0 | ✓ PASS |
| Loader on the pinned snapshot | `python -m llm4pol.data load` | `95,332 rows … 78,375 candidates`, exit 0 | ✓ PASS |
| Validator | `python -m llm4pol.data validate` | seven resolution findings 554/312/182/0/0/60/2 reproduced; `56 reproduced, 38 documented, 0 failed -> exit 0` | ✓ PASS |
| Report idempotence | `git diff --exit-code -- docs/audit/` after a fresh validate | exit 0, byte-identical | ✓ PASS |
| Named guards | `pytest …::test_d11_resolution_never_assigns_an_unobserved_label …::test_d11_two_labelled_twins_keep_unknown …::test_real_tacticity_resolution_counts_match_adr_0006 …::test_real_load_writes_95332_rows_and_78375_candidates …::test_real_validate_exits_0_and_committed_report_is_byte_identical_to_a_fresh_run …::test_committed_response_example_equals_evaluator_output_on_the_synthetic_root` | 6 passed | ✓ PASS |
| Phase-3 count-sensitive tests | `pytest …::test_batch_of_100_… …::test_response_cost_is_the_sum_of_result_costs …::test_no_population_filter_is_applied …::test_cache_hit_leaves_evals_unchanged_after_jsonl_replay` | 4 passed | ✓ PASS |
| Evaluator CLI on a fresh synthetic root | `python -m llm4pol.evaluate --request protocol/examples/eval-request.example.json --root <tmp>` | output `==` the committed example; 9 results; evals `[1,0,0,0,0,1,0,0,1]`; cost `{evals 3}` | ✓ PASS |
| Row-level expectations guard | `git diff -U0 35febb08…..HEAD -- src/llm4pol/data/expectations.py \| grep '^-' \| grep -cE '…'` | `0` | ✓ PASS |
| Test collection | `PYTHONPATH=src pytest tests/ --collect-only -q -o addopts=""` | `189 tests collected` (= the gate's 189 passed = CI's 172 + 17 skipped) | ✓ PASS |
| CI | `gh run view 35962545625 --json conclusion,event,headBranch,headSha,jobs` | `success`, `workflow_dispatch`, `main`, `1277838…`, both jobs success; log: `SUMMARY: 7/7 steps passed` ×2 | ✓ PASS |

### Probe Execution

No `scripts/*/tests/probe-*.sh` exists in this repository and neither the PLAN nor the SUMMARY
declares a probe. The project's equivalent runnable authority is `scripts/check.py`, executed above.

### Requirements Coverage

| Requirement | Source plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| DATA-04 | 02-06 | `candidate_id = sha256(canonical_psmiles + "\|" + tacticity)[:16]`, stereo-aware | ✓ SATISFIED | Formula unchanged (T5); what changed is the `tacticity` it is given. `d220c5c57c4fae2e` re-derived |
| DATA-05 | 02-06 | Rows sharing a `candidate_id` grouped as replicates, median with count and spread | ✓ SATISFIED | 301 previously split repeat units now pool; multi-row candidates 13,014 / max 22 independently re-derived; sizes sum to 95,332 |
| DATA-06 | 02-06 | The validator report reproduces or documents every figure it carries | ✓ SATISFIED | `0 failed`; byte-identical republication; seven new findings with populations |
| DATA-10 | 02-06 | An invariant is promoted to a test in the same change that adds the code | ✓ SATISFIED | D-11 row and its two guards landed in `5e7b296`, the same commit as the call-site flip |

No orphaned requirement: `.planning/REQUIREMENTS.md` maps DATA-04..DATA-10 to Phase 2, and DATA-07,
DATA-08, DATA-09 were unaffected by this plan (their findings still reproduce/document, B3/B4).

### Anti-Patterns Found

None. Every file in the plan's diff was scanned for `TODO`, `FIXME`, `XXX`, `HACK`, `PLACEHOLDER`,
"not yet implemented" and "coming soon" — zero hits across all 15 source and test files. No
`@pytest.mark.skip` / `xfail` anywhere; the one `pytest.skip(` outside `conftest.py` is the
pre-existing absent-manifest skip in `tests/test_manifest.py`. The 17 CI skips are the real-file
tests, which run and pass locally.

### Housekeeping claims checked

1. **`commits: 4` is an off-by-one.** *Partly correct, and it does not matter.* At authoring time the
   count from `plan_head_before` `d0d5588` was **5** (four task commits plus the summary commit), so
   the executor's explanation of the cause is right. At HEAD it is **6**, because `e8a9477` — a real
   post-summary content change to a governance document — landed afterwards and is recorded nowhere
   in the SUMMARY. Nothing downstream reads `actuals.commits`. Advisory 1 and 2.
2. **GSD state tooling regressed ROADMAP and `completed_phases`; both restored by hand; a pre-existing
   0 % discrepancy left alone.** *Correct, and it does not matter for the goal.* The committed
   ROADMAP row reads `| 2. Data Foundation | 6/6 | Complete | 2026-09-24 |` and the wave-4 checkbox is
   ticked; `.planning/STATE.md`'s diff shows `completed_phases: 1` as an **unchanged context line**,
   i.e. the transient 0 never reached a commit. The older inconsistency — `completed_phases: 1` and a
   0 % bar while ROADMAP marks phases 1, 2 and 3 Complete — is untouched, exactly as claimed. It is
   display metadata; no artifact, gate or number depends on it. Advisory 3.

### Human Verification Required

None. The one procedural item — a `workflow_dispatch` at HEAD to cover the ADR prose commit — is
recorded as Advisory 4 rather than as a human-judgement item, per the verification brief.

### Gaps Summary

No gaps. The plan's goal is achieved and independently corroborated: the resolution runs over the
whole in-scope frame before the identity is taken, the pinned snapshot yields 78,375 candidates, the
seven resolution counts reproduce against registered populations, the committed report is a
byte-identical republication, D-11 is a guarded invariant whose two named tests exist and pass, no
row-level finding moved detectably (established by command, with the residual `documented`-tolerance
gap honestly stated), and every Phase 2 and Phase 3 truth still holds — with the Phase-2
candidate-level figures moving only where ADR-0006 required and the Phase-3 exact-equality
assertions preserved as equalities. The ADR's own corrected text about the 60 unresolved rows was
re-derived from the raw CSV and is right.

---

_Verified: 2026-09-24T06:25:10Z_
_Verifier: Claude (gsd-verifier)_
