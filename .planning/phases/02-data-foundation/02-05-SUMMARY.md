---
phase: 02-data-foundation
plan: 05
subsystem: data
tags: [pandas, pytest, tdd, validator, readme-numbers, maxwell-identity, feasible-set, ci, evidence]

# Dependency graph
requires:
  - phase: 02-data-foundation
    provides: "plan 02-01's report model (`CountTable`, `Expected`, `evaluate_finding`) and validator skeleton; plan 02-02's registry triad; plan 02-03's loader (`build_candidates`, declared schema); plan 02-04's `Registry` loader, `readme_triple_mask`, `replicates.replicate_section` and the seven-step gate"
provides:
  - "`llm4pol.data.filters`: readme_triple_ladder, alternative_eps_filters, check_tc_mask, check_tc_counts, candidate_level_triple (filter then median; median then filter as the printed alternative), MultiTacticity counts by smiles_list and by canonical, raw_string_merges, card_count_candidates, coverage, physical_range_counts, tacticity_counts, with_n_squared, dielectric_identity_residual, static_minimum, static_maxwell_violation_share, dc_maxwell_violations, spearman_table, readme_window, tg_window_counts, tg_rmse_ladder_counts, tg_rmse_descriptives, FeasibleSet / feasible_set / feasible_rows, DEV_DEFAULT_TG_MIN_K = 400.0 and DEV_DEFAULT_EPS_QUANTILE = 0.25 cited from charter section 13 (every bound from the registry; pandas only)"
  - "`llm4pol.data.expectations` (new): EXPECTED_POLYOMICS complete (49 reproduce + 38 documented findings on the pinned file) with per-finding class, value, tolerance, note and print digits; POPULATIONS and `population_of` (D-10)"
  - "`llm4pol.data.sections` (new): the coverage, physical-range, dielectric and README-ladder section builders; `validate.py` keeps orchestration, the Tg and feasible sections and run()"
  - "The eleven-section report: Fetch identity, Source shape (73,045 paragraph + candidate-count table), Scope exclusions and identity (twins, raw-string merges), Coverage per registry property, Physical-range filter counts, Dielectric columns: identity and Maxwell check, README triple ladder, Tg window and tg_rmse ladder (with the DATA-09-vs-R-2 flag), Replicate structure and noise floor, Feasible set under the development defaults (input to the D-16 gate), Findings (+ Finding notes)"
  - "`docs/audit/polyomics-041e5834-validation.md` committed: the number authority, byte-identical to a fresh `python -m llm4pol.data validate`, aggregates only (three greps at 0, no table cell over 80 characters)"
  - "D-8 and A-7 promoted to tests inside the gate (`test_d8_no_row_level_split_code_under_llm4pol_data`, `test_a7_validator_and_loader_never_serve_static_dielectric_const`), the D-10 test extended to the committed report, INVARIANTS.md D-8 cell and a new A-7 table"
  - "`docs/research/databases/README.md` dated correction note (2026-09-22) pointing at the report; `docs/audit/README.md` index row"
  - "`02-EVIDENCE.md`: charter section 13 M1 exit criteria (1)-(6) paired with commands and verbatim outputs; workflow_dispatch CI run 35648565974 green on windows-latest and ubuntu-latest (104 passed, 12 skipped by design each)"
affects: [03-evaluate (which population the evaluator serves: 43,561 vs 42,733; the 303 unknown twins), 07-preregistration (D-16 defaults are inputs here), every later citation of a PolyOmics number]

# Actuals (#2632) — chars/4 over the realized diff (148,786 bytes of added/removed lines), never a harness token count.
actuals:
  tokens: 37200
  tasks: 4
  commits: 8
plan_head_before: 162813b6fd45dd766bb41cda6397100c9fbcd479

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ladder of named populations: each rung is a finding id; the ladder table is rendered after the findings are evaluated so every step prints its expected value and status"
    - "`documented` findings pin the observed research value with a tolerance and carry the README's figure in the note; a `reproduce` finding pins the underlying count (38,693 / 43,561) so the percentage can never drift silently"
    - "Per-finding print digits (`Expected.digits`) so a share prints `88.82`, a Spearman `0.170`, a residual `5.7e-07`, and the 02-04 spreads keep four decimals"
    - "Report tables are titled with level-3 headings, never bold, and registry units render `*` as `·`, so the aggregates-only grep for `*` followed by a letter (charter section 10) stays at zero by construction"
    - "The barred column enters `filters.py` as `STATIC_COLUMN`, data the F-14 identity needs; it is never a registry column and appears in the report only inside the dielectric section"

key-files:
  created:
    - src/llm4pol/data/expectations.py
    - src/llm4pol/data/sections.py
    - docs/audit/polyomics-041e5834-validation.md
    - .planning/phases/02-data-foundation/02-EVIDENCE.md
  modified:
    - src/llm4pol/data/filters.py
    - src/llm4pol/data/validate.py
    - src/llm4pol/data/report.py
    - tests/test_data_invariants.py
    - tests/test_data_real_file.py
    - docs/governance/INVARIANTS.md
    - docs/audit/README.md
    - docs/research/databases/README.md

key-decisions:
  - "The static Maxwell share is pinned at 88.82 %, not the 88.83 % RESEARCH F-13 prints: F-13's own fraction 38,693 / 43,561 = 88.8249 % rounds to 88.82. The fraction is a `reproduce` finding (exact), the share a `documented` one (tolerance 0.05) whose note records both the README's 88.9 % and F-13's rounding slip; the correction note and the evidence say 88.82 % (38,693 / 43,561). The charter and REQUIREMENTS.md name only the README's 88.9 % as 'reproduced or documented', which this satisfies."
  - "`feasible_rows_dev_defaults` = 7,317 is the row-level count under the row-level Q25 (2.6427), which is the population F-62 used; the count under the candidate Q25 (7,582) is printed beside it and not pinned"
  - "Coverage finding ids use the column name (`coverage_Rg`, `coverage_fractional_free_volume`) as the plan lists them; the table's `property` cell uses the registry key so the barred column can never be a property row"
  - "`Finding notes` table added after `Findings` so the README's figures and the F-facts behind each `documented` finding are in the report, not only in source; notes are kept at or under 80 characters (the plan's cell rule)"
  - "`report.py` was edited in Task 1 (digits, scientific notation, heading titles, notes table) and left untouched in Task 2, as the plan's Task 2 acceptance requires"
  - "Commits made directly on `main` under the orchestrator's sequential instruction with `branching_strategy: none` (same as plans 02-01..02-04)"

patterns-established:
  - "Finding ids: `coverage_<column>`, `tacticity_<label>`, `check_tc_<true|false|none>`, `eps_alternative_<rung>`, `spearman_<a>_<b>`, `tg_rmse_le_<rung>`, `feasible_*_dev_defaults`, `eps_q25_<population>`"
  - "Population labels for the README numbers live in `expectations.py` (`TRIPLE_ALL_ROWS`, `TRIPLE_IN_SCOPE`, `DIELECTRIC_ROWS`, `CANDIDATE_TRIPLE`, `CANDIDATE_TRIPLE_ALT`, `TC_TG_ROWS`, `TG_RMSE_ROWS`) and are imported by both `sections.py` and `validate.py`"

requirements-completed: [DATA-06, DATA-08, DATA-09, DATA-10]

coverage:
  - id: D1
    description: "The README triple 43,561 is reproduced under exactly TC non-null ∧ eps_dc ∈ [1, 20] ∧ tg ∈ [100, 900] K on all source rows (ladder 95,335 → 81,405 → 79,929 → 76,168 → 43,561), with 43,560 in scope, 42,733 under check_tc, 40,212 candidates (filter then median; 40,426 printed as the alternative); the naive eps filters 45,821 / 42,186 / 45,134 / 45,704 printed and not used"
    requirement: DATA-06
    verification:
      - kind: unit
        ref: "tests/test_data_invariants.py#test_readme_ladder_counts_on_synthetic"
        status: pass
      - kind: unit
        ref: "tests/test_data_invariants.py#test_alternative_eps_filters_are_printed_not_used"
        status: pass
      - kind: integration
        ref: "tests/test_data_real_file.py#test_real_readme_numbers_reproduce_or_are_documented"
        status: pass
      - kind: other
        ref: "python -m llm4pol.data validate -> finding readme_triple_all_rows: reproduce expected=43,561 observed=43,561 reproduced; VALIDATION: 49 reproduced, 38 documented, 0 failed -> exit 0"
        status: pass
    human_judgment: false
  - id: D2
    description: "The two dielectric claims are documented: static Maxwell violation 38,693 / 43,561 = 88.82 % on the triple rows (README 88.9 %; F-13 printed 88.83) and 84.30 % on all rows with both columns; eps_dc violation 0 as the identity eps_dc = static − 1 + n² (max residual 5.7e-7, static minimum 1.00016) with the R-3 narrative (`corrected static dielectric constant`; the registry serves dielectric_const_dc only); 73,045 resolved as the card's description text with every candidate count printed"
    requirement: DATA-06
    verification:
      - kind: unit
        ref: "tests/test_data_invariants.py#test_maxwell_identity_holds_on_dielectric_rows"
        status: pass
      - kind: unit
        ref: "tests/test_data_invariants.py#test_card_count_73045_matches_no_column_on_synthetic"
        status: pass
      - kind: unit
        ref: "tests/test_data_invariants.py#test_findings_documented_class_uses_tolerance_and_reproduce_is_exact"
        status: pass
      - kind: other
        ref: "python -m llm4pol.data validate -> finding static_maxwell_violations_triple: reproduce expected=38,693 observed=38,693 reproduced; finding static_maxwell_violation_pct_triple: documented expected=88.82 observed=88.82 documented; finding dc_maxwell_violations: reproduce expected=0 observed=0 reproduced"
        status: pass
    human_judgment: false
  - id: D3
    description: "The feasible set under the development defaults is stated as an input to the D-16 gate: Q25 of candidate eps_dc medians 2.6524, Tg ≥ 400 K → 6,793 of 40,212 candidates (16.89 %); row-level 7,317 of 43,560 under the row Q25 2.6427; `threshold =` appears nowhere"
    requirement: DATA-08
    verification:
      - kind: unit
        ref: "tests/test_data_invariants.py#test_feasible_set_on_synthetic_is_labelled_as_d16_input"
        status: pass
      - kind: integration
        ref: "tests/test_data_real_file.py#test_real_tg_window_ladder_and_feasible_set"
        status: pass
      - kind: other
        ref: "grep -c \"threshold =\" src/llm4pol/data/validate.py src/llm4pol/data/filters.py src/llm4pol/data/sections.py docs/audit/polyomics-041e5834-validation.md -> 0 each"
        status: pass
    human_judgment: false
  - id: D4
    description: "Tg window 56,064 non-null / 52,753 inside / 3,311 outside and the tg_rmse ladder 36,592 / 42,232 / 43,316 / 43,521 / 43,545 on the in-scope triple rows with no cut applied; the DATA-09-vs-R-2 wording discrepancy flagged verbatim in the report's Tg section for the owner"
    requirement: DATA-09
    verification:
      - kind: unit
        ref: "tests/test_data_invariants.py#test_tg_window_and_tg_rmse_ladder_on_synthetic"
        status: pass
      - kind: integration
        ref: "tests/test_data_real_file.py#test_real_tg_window_ladder_and_feasible_set"
        status: pass
      - kind: other
        ref: "grep -c \"Wording discrepancy raised for the owner: REQUIREMENTS.md DATA-09\" src/llm4pol/data/validate.py -> 1"
        status: pass
    human_judgment: false
  - id: D5
    description: "D-8 and A-7 are named tests inside the gate, the D-10 test covers the committed report, INVARIANTS.md's D-8 cell names the AST test and the import-linter contract and a new `Architecture (charter §4) — guards landed` table carries A-7; the D-7, D-9 and D-10 cells are untouched"
    requirement: DATA-10
    verification:
      - kind: unit
        ref: "tests/test_data_invariants.py#test_d8_no_row_level_split_code_under_llm4pol_data"
        status: pass
      - kind: unit
        ref: "tests/test_data_invariants.py#test_a7_validator_and_loader_never_serve_static_dielectric_const"
        status: pass
      - kind: unit
        ref: "tests/test_data_invariants.py#test_d10_every_count_table_in_report_names_its_population"
        status: pass
      - kind: other
        ref: "git show --format= e355015 -- docs/governance/INVARIANTS.md: one changed row (D-8) plus the appended A-7 section; report.py absent from that commit's stat"
        status: pass
    human_judgment: false
  - id: D6
    description: "The number authority is committed, byte-identical to a fresh run, aggregates only; the research README carries its dated correction; CI is green on both platforms by workflow_dispatch and 02-EVIDENCE.md maps M1 (1)-(6) to commands and outputs"
    requirement: DATA-06
    verification:
      - kind: integration
        ref: "tests/test_data_real_file.py#test_real_validate_exits_0_and_committed_report_is_byte_identical_to_a_fresh_run"
        status: pass
      - kind: unit
        ref: "tests/test_data_invariants.py#test_committed_validator_report_exists_and_names_revision_and_sections"
        status: pass
      - kind: other
        ref: "gh run view 35648565974 --json event,headBranch,conclusion,jobs -> workflow_dispatch main success check (ubuntu-latest)=success,check (windows-latest)=success; both job logs: SUMMARY: 7/7 steps passed, llm4polcheck inventory: 1 entries, 1 instances processed, 104 passed, 12 skipped"
        status: pass
    human_judgment: false

# Metrics
duration: 45min
completed: 2026-09-22
status: complete
---

# Phase 2 Plan 05: README-number reproduction, feasible set, guards and evidence Summary

**Every PolyOmics README number is now a command: 43,561 / 42,733 / 40,212 reproduce exactly, the 88.9 % is documented as 38,693 / 43,561 = 88.82 %, the "0 Maxwell violations" is shown to be the identity eps_dc = static − 1 + n², 73,045 is the card's text, the feasible set 6,793 of 40,212 (16.89 %) is stated as a D-16 input, D-8 and A-7 run as tests, the report is committed byte-reproducibly and CI is green on both platforms with the M1 evidence recorded.**

## Performance

- **Duration:** 45 min
- **Started:** 2026-09-21T19:28:54Z
- **Completed:** 2026-09-21T20:13:19Z (UTC; 2026-09-22 local)
- **Tasks:** 4
- **Files modified:** 12 (4 created)

## Accomplishments

- `python -m llm4pol.data validate` exits 0 with `49 reproduced, 38 documented, 0 failed`; the committed `docs/audit/polyomics-041e5834-validation.md` is the number authority (charter §10), byte-identical to a fresh run and free of row-level values (three greps at 0; no table cell over 80 characters).
- Charter §13 M1 exit criteria (2), (3), (5), (6) are reproducible by command and (1)–(6) are paired with verbatim outputs in `02-EVIDENCE.md`; workflow_dispatch run 35648565974 on tip `39c5345` is green on windows-latest and ubuntu-latest (`SUMMARY: 7/7 steps passed` on both; the real-file tests skip by design).
- The DATA-09-vs-R-2 wording discrepancy is flagged for the owner in the report, the evidence and here — not resolved (see Owner questions).
- `docs/research/databases/README.md` carries its dated correction; the 2026-09-11 text is untouched (added lines only).

## Task Commits

Each task was committed atomically (RED then GREEN for the TDD tasks):

1. **Task 1: README numbers** — `bd2aab0` (test, RED) → `511732b` (feat, GREEN)
2. **Task 2: Tg ladder, feasible set, D-8 / D-10 / A-7 guards** — `3ff0474` (test, RED) → `e355015` (feat, GREEN)
3. **Task 3: number authority + correction note** — `df0e0ae` (docs) → `39c5345` (docs)
4. **Task 4: push, CI, evidence** — `aaef76a` (docs; pushed; post-dates the cited CI run, whose headSha is `39c5345`)
5. Post-plan file-size refactor — `a161ebf` (refactor: `sections.py` split; report byte-identical; pushed)

**Plan metadata:** see the final `docs(02-05): complete …` commit.

## Files Created/Modified

- `src/llm4pol/data/filters.py` — every ladder, share, window, twin count, Tg/tg_rmse count and the feasible set as pure registry-fed functions; `DEV_DEFAULT_*` cited from charter §13.
- `src/llm4pol/data/expectations.py` (new) — `EXPECTED_POLYOMICS`, `POPULATIONS`, `population_of`, population labels and finding notes.
- `src/llm4pol/data/sections.py` (new) — coverage, physical-range, dielectric and README-ladder section builders.
- `src/llm4pol/data/validate.py` — orchestration, source-shape / identity extensions, the Tg and feasible sections (flag paragraph and D-16 sentence), `run()`.
- `src/llm4pol/data/report.py` — `Expected.digits` / `Finding.digits`, `format_finding_values`, scientific notation below 1e-3, `###` table titles, `Finding notes` table.
- `tests/test_data_invariants.py` — +13 tests (README ladder, alternatives, Maxwell identity ×2, twins, 73,045, finding classes, Tg ladder, feasible set, D-8, A-7, section order, committed report) and the extended D-10 test.
- `tests/test_data_real_file.py` — +3 real-file tests (README numbers, Tg/feasible, byte-identical report).
- `docs/audit/polyomics-041e5834-validation.md` (new, committed) and `docs/audit/README.md` (index row).
- `docs/governance/INVARIANTS.md` — D-8 guard cell; new A-7 table.
- `docs/research/databases/README.md` — `#### Correction (2026-09-22, Phase 2 validator)`.
- `.planning/phases/02-data-foundation/02-EVIDENCE.md` (new).

## Decisions Made

- **88.82 %, not 88.83 %.** RESEARCH F-13 states "88.83 % (38,693 / 43,561)"; the fraction is exact on the pinned file and equals 88.8249 %, which rounds to 88.82. The plan forbids changing an expected value without the supporting F-fact; the supporting fact is F-13's own fraction, now pinned as a `reproduce` finding. The `documented` share pins 88.82 with tolerance 0.05 and notes the README's 88.9 % and F-13's rounding slip. The plan's verify string `expected=88.83 observed=88.83` is therefore intentionally not met; forcing it would have meant misrounding.
- **Row-level feasible count** pinned under the row-level Q25 (7,317, F-62's population); the candidate-Q25 count (7,582) is printed beside it.
- **`Finding notes` table** appended after `Findings` so the README figures behind each `documented` finding are in the report itself.
- **File-size split** (`expectations.py` in Task 1, `sections.py` after Task 4) to keep every module under the 800-line ceiling; the plan's greps on `validate.py` (`Wording discrepancy…`, `input to the D-16 gate`, no `threshold =`) still hold.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Bold table titles matched the aggregates-only grep**
- **Found during:** Task 1 (the plan's `\*[A-Za-z]` grep printed 8 on the 02-04 report because of `**Title**` lines)
- **Fix:** `report.py` renders table titles as `### Title`; registry units render `*` as `·` in the physical-range table (`W/(m·K)`); the grep prints 0 on the synthetic and the committed report.
- **Files modified:** `src/llm4pol/data/report.py`, `src/llm4pol/data/sections.py`
- **Commit:** `511732b`

**2. [Rule 1 - Bug] The validator's row frame lacked `tg_rmse`**
- **Found during:** Task 2 GREEN (`KeyError: 'tg_rmse'` in the new Tg section)
- **Fix:** `TG_RMSE_COLUMN` added to the columns read from the rows parquet.
- **Commit:** `e355015`

**3. [Rule 2 - Correctness] F-13's 88.83 % is a rounding slip**
- **Found during:** Task 1 GREEN (observed 88.82 on the pinned file; 38,693 / 43,561 = 88.8249 %)
- **Fix:** the counts 38,693 and 78,807 are `reproduce` findings; the share is pinned at its true rounding 88.82 (see Decisions). The test expectation and the correction note say 88.82 % (38,693 / 43,561).
- **Commit:** `511732b`

**4. [Rule 3 - Blocking] Finding notes exceeded the 80-character cell rule**
- **Found during:** Task 3 (the committed-report test found eight note cells over 80 characters, two of them 02-04's `_F52_NOTE`)
- **Fix:** notes shortened (wording only; no number changed); `expectations.py` therefore appears in the Task 3 report commit beside the four planned files.
- **Commit:** `df0e0ae`

### Scope additions

- `src/llm4pol/data/expectations.py` and `src/llm4pol/data/sections.py` were created (file-size ceiling); the plan listed no new modules. The commit `a161ebf` post-dates the cited CI run; the local gate passed 7/7 before its push and the committed report regenerated byte-identical.

## Owner questions (flagged, not resolved)

1. **DATA-09 wording vs R-2.** REQUIREMENTS.md DATA-09 reads "Tg rows are filtered by `tg_rmse` and to 100–900 K"; CONTEXT R-2 applies no `tg_rmse` cut in M1 and records the ladder. The report prints the count at every rung (36,592 / 42,232 / 43,316 / 43,521 / 43,545) so either reading is satisfied; which holds is an owner decision (precedence charter > REQUIREMENTS.md > phase context, ADR-0002).
2. **The 303 `unknown`-tacticity twins (R-1, F-39)** stay separate candidates in M1; both counts (303 with unknown, 2 without) are in the report. To be decided before Phase 3 freezes the hidden table.
3. **Which triple the evaluator serves (R-2, F-59):** 43,561 (README) vs 42,733 (`check_tc == True`); both are printed. Phase 3 decision.
4. **RESEARCH F-13 prints 88.83 %** for a fraction that rounds to 88.82 %; the report and correction note use 88.82. If the owner prefers the RESEARCH wording corrected, that is a one-line edit to 02-RESEARCH.md (not done here — research files are inputs).

## Issues Encountered

- `pixi run … ruff check --fix <path>` run as a bare pixi task uses `env/` as cwd and therefore a different ruff config than the gate (`python -m ruff check .` from the repository root); it rewrote `load.py` and `replicates.py` with unrelated fixes, which were reverted with `git checkout -- <file>` before any commit. Lint is run exactly as the gate does from then on.
- The verify string `expected=88.83 observed=88.83` in the plan's Task 1 block is not met by design (see Decisions).

## Known Stubs

None. No placeholder, skipped test, xfail or unimplemented branch was introduced.

## Threat Flags

None. No new network endpoint, auth path, file-access pattern or schema change; T-02-23..T-02-28 mitigations landed as planned (byte-identical test, three aggregates-only greps + the cell rule, pinned `documented` values, `threshold =` absent, run id / head sha / event / branch in the evidence, history scan at 0 hits before both pushes).

## Next Phase Readiness

Phase 2 is complete: all five plans have summaries, the seven-step gate is green locally (116 passed) and in CI on both platforms, and `02-EVIDENCE.md` covers charter §13 M1 (1)–(6). Phase 3 inherits the four owner questions above.

## Self-Check: PASSED

All 5 created files found; all 8 plan commits (bd2aab0, 511732b, 3ff0474, e355015, df0e0ae, 39c5345, aaef76a, a161ebf) found in history; `git rev-list --count 162813b..HEAD` = 8 matches `commits: 8`.
