---
phase: 02-data-foundation
plan: 03
subsystem: data
tags: [huggingface-hub, sha256, rdkit, pyarrow, pandas, pytest, tdd]

# Dependency graph
requires:
  - phase: 02-data-foundation
    provides: "plan 02-01's tracer modules (fetch, identity, schema, load), the synthetic root fixture and the real_load session fixture"
provides:
  - "`fetch.fetch` as a complete contract: revision guard before any file, every entry hashed and sized, every MISMATCH printed before the return value, downloader called only for absent files, exit 0 / 1 / 2 each proven by a named test (D-01, D-10, DATA-01)"
  - "One manifest parser: `tests/test_manifest.py` imports `parse_manifest` and `sha256_of` from `llm4pol.data.fetch` (RESEARCH Don't Hand-Roll)"
  - "Identity vectors from F-32..F-35 pinned by test: merges, stereo kept, both `*` kept, `\"\"` / `*C(` / comma-joined -> None, idempotence, `candidate_id('*CC*', None) == d220c5c57c4fae2e` (D-03, D-6, DATA-04)"
  - "Declared schema asserted field by field after the large_string cast; `n_atom` / `mol_weight` never numeric; `smiles_search` never an identity column (D-02, F-36, F-41, F-42)"
  - "Loader rules as tests: second-monomer exclusion before parsing, parse failures after, NaN tacticity -> unknown, sorted `missing required columns: a, b`, `missing source file: <path>`, candidate `_n` as non-null count and ddof=1 std (D-03, D-04)"
  - "Real-file identity counts: 78,373 canonical, 78,676 ids, 95,332 x 262, n_rows sum 95,332 / max 17 / 12,983 multi-row (F-07, F-37, F-50)"
affects: [02-04, 02-05, evaluate, loop]

# Actuals (#2632) — chars/4 over the realized diff (38,614 bytes), never a harness token count.
actuals:
  tokens: 9700
  tasks: 2
  commits: 4
plan_head_before: 1c53e90908e587873625c48bf8e6e4eb3a121f63

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Recording fake downloader: `_recording_downloader(bytes_by_name)` returns `(callable, calls)`; the callable takes exactly `repo_id, repo_type, filename, revision, local_dir` and writes into `local_dir / filename` like `hf_hub_download`"
    - "Fetch reports, never repairs: a present file that mismatches is a MISMATCH line and exit 1; only an absent file reaches the downloader (the library's local fast path would hand a corrupted file back unchanged, Q5)"
    - "Downloader boundary catches `Exception` once (`# noqa: BLE001`) because the huggingface_hub error tree is open-ended; `KeyboardInterrupt` propagates (T-02-17)"
    - "Barred column name built from fragments in tests (`\"static_\" + \"dielectric_const\"`) so a literal grep never matches a test"

key-files:
  created:
    - tests/test_data_fetch.py
    - tests/test_data_identity.py
    - tests/test_data_schema.py
  modified:
    - tests/test_manifest.py
    - tests/test_data_real_file.py
    - src/llm4pol/data/fetch.py
    - src/llm4pol/data/identity.py
    - src/llm4pol/data/load.py

key-decisions:
  - "A present-but-mismatched file is never re-downloaded (plan must-have: downloader only for absent files); 02-01's `absent or mismatched` behaviour is narrowed and `test_fetch_returns_1_on_sha256_mismatch_and_names_the_file` asserts the downloader was not called"
  - "`canonical_psmiles(\"\")` returns None by an explicit guard plus `canonical or None` — RDKit parses the empty string as an empty molecule and would otherwise yield an empty canonical key"
  - "`schema.py` was not touched: every assertion of Tests 8–10 already held (`do_TC` boolean, no `n_atom` / `mol_weight` entry, DECLARED_FIELDS complete, IDENTITY_COLUMNS exact)"
  - "The `fetch` verified/downloaded line drops the `(existing)` suffix: `verified <name> size=N sha256=<12 hex>…` and `downloaded <name> size=N sha256=<12 hex>…`; every consumer (CLI test, real-file test) matches on `verified <name>` only"
  - "Commits made directly on `main` under the orchestrator's sequential instruction with `branching_strategy: none` (same as plans 02-01 and 02-02)"

patterns-established:
  - "Manifest ValueError messages are `<path>:<lineno>: <reason>`; tests match `r\":2:\"` on the 1-based line"
  - "Real-file tests read only the columns they need (`pd.read_parquet(..., columns=[...])`) so the three new tests add no measurable time to the 17 s session fixture"

requirements-completed: [DATA-01, DATA-02, DATA-04]

coverage:
  - id: D1
    description: "`fetch` returns 1 and prints `MISMATCH <name> expected sha256=… size=… observed sha256=… size=…` for every bad file, checks every entry before returning, refuses a drifted `# revision:` before touching a file, returns 2 on a missing manifest or a raising downloader, and calls the downloader only for absent files with the exact `hf_hub_download` kwargs"
    requirement: DATA-01
    verification:
      - kind: unit
        ref: "tests/test_data_fetch.py#test_fetch_downloads_a_missing_file_then_verifies_it"
        status: pass
      - kind: unit
        ref: "tests/test_data_fetch.py#test_fetch_checks_every_file_before_returning"
        status: pass
      - kind: unit
        ref: "tests/test_data_fetch.py#test_fetch_returns_2_when_downloader_raises"
        status: pass
      - kind: other
        ref: "pixi run --manifest-path env/pixi.toml python -m llm4pol.data fetch (exit 0, two `verified` lines, snapshot line)"
        status: pass
    human_judgment: false
  - id: D2
    description: "One manifest parser serves both manifests; `tests/test_manifest.py` imports it and the committed MANIFEST-open content is pinned to F-02 / F-03"
    requirement: DATA-01
    verification:
      - kind: unit
        ref: "tests/test_data_fetch.py#test_committed_manifest_open_lists_the_two_pinned_files_with_research_hashes"
        status: pass
      - kind: unit
        ref: "tests/test_manifest.py#test_raw_files_match_manifest"
        status: pass
    human_judgment: false
  - id: D3
    description: "Identity vectors: equivalent raw strings merge, stereo and both `*` kept, `*C(` / comma-joined / empty -> None, idempotent, `candidate_id('*CC*', None)` is `d220c5c57c4fae2e`, unknown tacticity total"
    requirement: DATA-04
    verification:
      - kind: unit
        ref: "tests/test_data_identity.py#test_canonical_psmiles_merges_equivalent_raw_strings"
        status: pass
      - kind: unit
        ref: "tests/test_data_identity.py#test_candidate_id_maps_missing_tacticity_to_unknown"
        status: pass
      - kind: other
        ref: "python -c one-liner -> `d220c5c57c4fae2e *CC(*)(C)C(=O)OC None`"
        status: pass
    human_judgment: false
  - id: D4
    description: "Declared parquet schema asserted field by field after the cast (`smiles_list` is `string`, not `large_string`), pass-through of undeclared columns, metadata counts, exclusion and error rules of the loader, candidate statistics on the fixture"
    requirement: DATA-02
    verification:
      - kind: unit
        ref: "tests/test_data_schema.py#test_loaded_parquet_schema_has_declared_types_after_cast"
        status: pass
      - kind: unit
        ref: "tests/test_data_schema.py#test_candidate_table_has_median_n_min_max_std_per_property"
        status: pass
      - kind: unit
        ref: "tests/test_data_schema.py#test_loader_raises_loader_error_naming_missing_required_columns"
        status: pass
    human_judgment: false
  - id: D5
    description: "On the pinned file: 78,373 unique canonical, 78,676 unique ids, 95,332 x 262 with declared types, candidate `n_rows` sums to 95,332 with max 17 and 12,983 multi-row candidates"
    requirement: DATA-04
    verification:
      - kind: integration
        ref: "tests/test_data_real_file.py#test_real_identity_counts_match_research"
        status: pass
      - kind: integration
        ref: "tests/test_data_real_file.py#test_real_parquet_schema_round_trips_with_declared_types"
        status: pass
      - kind: integration
        ref: "tests/test_data_real_file.py#test_real_candidates_have_unique_ids_and_sizes_sum_to_in_scope_rows"
        status: pass
    human_judgment: false

# Metrics
duration: 10min
completed: 2026-09-22
status: complete
---

# Phase 2 Plan 03: Fetch failure paths, identity vectors, declared schema, loader rules Summary

**DATA-01, DATA-02 and DATA-04 are now complete contracts rather than happy paths: every fetch failure (wrong byte, wrong size, drifted revision, missing manifest, raising downloader) produces its documented line and exit code; the RDKit identity rule reproduces the F-32..F-35 vectors and `d220c5c57c4fae2e`; the parquet schema is the declared one field by field; and the pinned file reproduces 78,373 canonical repeat units, 78,676 candidates and replicate sizes summing to the 95,332 in-scope rows.**

## Performance

- **Duration:** 10 min
- **Started:** 2026-09-21T18:57:31Z
- **Completed:** 2026-09-21T19:07:32Z
- **Tasks:** 2 (both TDD: RED then GREEN)
- **Files modified:** 8 (3 created, 5 modified)

## Accomplishments

- `fetch` checks the manifest revision before any file, hashes and sizes every entry, prints every `MISMATCH` before deciding the return value, calls the downloader only for absent files with exactly `repo_id`, `repo_type="dataset"`, `filename`, `revision`, `local_dir`, and maps any downloader exception to `ERROR: download failed for <name>: <exc>` / exit 2. The download-metadata sidecar (F-05) is never read (`grep -c "\.cache"` = 0).
- The PoLyInfo manifest test and the PolyOmics fetch share one parser: `tests/test_manifest.py` lost its `_parse_manifest` / `_sha256` copies and imports `parse_manifest` / `sha256_of`.
- Seven identity tests pin the charter §6 rule with research vectors; the empty-string edge case was a real defect (RDKit returns an empty molecule for `""`, giving an empty canonical key instead of `None`).
- Twelve schema tests assert `DECLARED_FIELDS` against `pq.read_schema` of the written parquet, the pass-through of `extra_note`, the metadata counts, the exclusion order, unknown tacticity, the u07/u08 merge and the `*CC*`/none statistics (median 0.32, min 0.30, max 0.34, std 0.02; `*CO*`/none `_n` 0, std NaN).
- Three real-file tests reproduce F-07, F-37, F-44 and F-50 on the pinned bytes; every expected number is as the plan stated, none was edited.

## Task Commits

1. **Task 1 RED** — `6c4c9c9` (test) — `test(02-03): add failing fetch-contract tests and share the manifest parser with test_manifest.py (D-01, DATA-01)`; touches only `tests/test_data_fetch.py`, `tests/test_manifest.py`
2. **Task 1 GREEN** — `f458082` (feat) — `feat(02-03): complete the fetch contract — revision guard, every-file check, exit codes (D-01, D-10)`; touches only `src/llm4pol/data/fetch.py`
3. **Task 2 RED** — `3b78d41` (test) — `test(02-03): add failing identity, declared-schema and loader tests (D-02, D-03, D-04)`; touches only the three test files
4. **Task 2 GREEN** — `ba59947` (feat) — `feat(02-03): pin identity vectors, declared schema and loader exclusion rules; prove identity counts on the pinned file (D-02, D-03, D-04, DATA-02, DATA-04)`; touches only `identity.py`, `load.py`

Full shas: `6c4c9c9`, `f458082`, `3b78d41`, `ba59947` (from `git log 1c53e90..HEAD`).

**Plan metadata:** see the `docs(02-03): complete …` commit that follows this file.

## Recorded lines (per the plan's output spec)

**Task 1 RED** (`pytest tests/test_data_fetch.py tests/test_manifest.py -v` → `2 failed, 13 passed`):
- `FAILED tests/test_data_fetch.py::test_fetch_downloads_a_missing_file_then_verifies_it` — `AssertionError: assert 'downloaded README.md' in 'verified … README.md size=130 sha256=d3b8876de667… (downloaded)\n…'`
- `FAILED tests/test_data_fetch.py::test_fetch_returns_1_on_sha256_mismatch_and_names_the_file` — the full 64-hex sha was printed where the test expects the 12-hex prefix followed by `…`
- Tests 1, 2, 3, 6, 7, 8, 9, 10, 11 and the four manifest tests were already green on the tracer (the plan anticipated "RED on whichever behaviours the tracer did not implement").

**Task 1 GREEN:** `15 passed in 0.38s`; greps: `def _parse_manifest\|def _sha256` = 0, `from llm4pol.data.fetch import` = 1, `\.cache` in fetch.py = 0; `python -m llm4pol.data fetch` on this repository (exit 0):
- `verified general_polymers_with_sp_abbe_dynamic-dielectric.csv size=196910783 sha256=71e955ac1e90…`
- `verified README.md size=15532 sha256=c2340252a720…`
- `snapshot: polyomics:general_polymers@041e5834`
- gate: `SUMMARY: 6/6 steps passed` (`60 passed in 22.31s`)

**Task 2 RED** (`pytest tests/test_data_identity.py tests/test_data_schema.py tests/test_data_real_file.py -v` → `2 failed, 23 passed in 20.31s`):
- `FAILED tests/test_data_identity.py::test_canonical_psmiles_returns_none_for_unparseable_and_comma_joined_lists` — `AssertionError: assert '' is None` (line 49, the `canonical_psmiles("")` clause)
- `FAILED tests/test_data_schema.py::test_loader_raises_loader_error_naming_missing_required_columns` — message was `…short.csv: missing required columns: ['check_tc', 'tg_rmse']`, the test expects the sorted `check_tc, tg_rmse`
- The three new real-file tests PASSED on their first run: the loader already produced the research counts. Tests 9, 18 and the `_n == 0` clause of Test 16 (the plan's other likely REDs) were already green.

**Task 2 GREEN:** `19 passed in 0.54s` on the fixture files; one-liner prints `d220c5c57c4fae2e *CC(*)(C)C(=O)OC None`; `grep -c smiles_search` = 0 in both `identity.py` and `load.py`; gate `SUMMARY: 6/6 steps passed` — `Steps: ruff check, ruff format --check, mypy, import-linter, history-secret-scan, pytest`; mypy `Success: no issues found in 10 source files`; `Contracts: 1 kept, 0 broken.`; `82 passed in 22.63s`.

**Real-file suite** (`pytest tests/test_data_real_file.py -vv -rA --durations=3`, exit 0):
- `PASSED tests/test_data_real_file.py::test_real_fetch_verifies_pinned_files_without_downloading`
- `PASSED tests/test_data_real_file.py::test_real_load_writes_95332_rows_and_78676_candidates`
- `PASSED tests/test_data_real_file.py::test_real_validate_reproduces_source_shape`
- `PASSED tests/test_data_real_file.py::test_real_identity_counts_match_research`
- `PASSED tests/test_data_real_file.py::test_real_parquet_schema_round_trips_with_declared_types`
- `PASSED tests/test_data_real_file.py::test_real_candidates_have_unique_ids_and_sizes_sum_to_in_scope_rows`
- durations: `16.96s setup tests/test_data_real_file.py::test_real_load_writes_95332_rows_and_78676_candidates` / `2.41s call tests/test_data_real_file.py::test_real_validate_reproduces_source_shape` / `0.15s call tests/test_data_real_file.py::test_real_fetch_verifies_pinned_files_without_downloading` / `6 passed in 19.80s`

**Expected values a defect forced me to investigate:** none. Every real-file number (3 / 0 / 78,373 / 78,676 / 95,332 / 262 / 17 / 12,983) held on the first run.

## Files Created/Modified

- `tests/test_data_fetch.py` — 11 tests; helpers `_recording_downloader`, `_raise`, `_rewrite_manifest`; `CSV_SHA` / `README_SHA` constants (F-02, F-03)
- `tests/test_data_identity.py` — 7 tests; `ID_PATTERN`
- `tests/test_data_schema.py` — 12 tests; `BARRED_COLUMN` from fragments; `_declared_types`, `_rows_frame`
- `tests/test_manifest.py` — imports `parse_manifest`, `sha256_of`; local helpers deleted; docstring states the shared-parser proof; test names and skip reason unchanged
- `tests/test_data_real_file.py` — +3 tests, `pandas` / `pyarrow.parquet` / `DECLARED_FIELDS` imports, docstring extended
- `src/llm4pol/data/fetch.py` (191 lines) — `_short`, `_report`, `_download` extracted; `fetch` rewritten to the contract; `EntryNotFoundError` import dropped (subsumed by the boundary catch)
- `src/llm4pol/data/identity.py` — empty-string guard, docstring
- `src/llm4pol/data/load.py` — `LoaderError` messages, `build_candidates` docstring

## Decisions Made

See `key-decisions` in the frontmatter. In brief: mismatched present files are reported, not re-downloaded; `canonical_psmiles("")` is `None` by guard; `schema.py` needed no change; the `(existing)` suffix on the verified line was dropped; commits on `main` per the orchestrator.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] Test 5 also asserts the downloader is not called for a present-but-mismatched file**
- **Found during:** Task 1 (writing behaviour 5)
- **Issue:** The plan's must-have says the downloader is called "only for absent files", but the tracer re-downloaded any mismatched file; behaviour 5's text ("fake that returns the existing path without writing") tolerated either.
- **Fix:** `test_fetch_returns_1_on_sha256_mismatch_and_names_the_file` asserts `calls == []`; `fetch` downloads only when `path.is_file()` is false.
- **Files modified:** `tests/test_data_fetch.py`, `src/llm4pol/data/fetch.py`
- **Verification:** the test PASSED; `test_cli_fetch_exits_1_on_a_sha256_mismatch` (02-01) still PASSED (its fake copies the file onto itself, so it is indifferent).
- **Committed in:** `6c4c9c9`, `f458082`

**2. [Rule 1 - Bug] `test_loader_raises_loader_error_naming_missing_required_columns` asserts the exact sorted `a, b` format**
- **Found during:** Task 2 STEP 1
- **Issue:** The plan's Test 17 prose ("message contains both names") was already green on the tracer's list-repr message, which would have left STEP 2's specified format (`missing required columns: a, b`, sorted) unproven.
- **Fix:** The test asserts `"missing required columns: check_tc, tg_rmse" in message`; `read_source` sorts and joins with `, `.
- **Files modified:** `tests/test_data_schema.py`, `src/llm4pol/data/load.py`
- **Committed in:** `3b78d41`, `ba59947`

---

**Total deviations:** 2 auto-fixed (1 Rule 2, 1 Rule 1). **Impact on plan:** both tighten a test to the contract the plan itself states; no scope change, no expected number touched.

## Issues Encountered

- `gsd_run check tdd-red-evidence` returns `INVALID_RED (zero_tests_discovered)` for both RED records: the checker parses node:test TAP summaries (`# tests`, `# pass`, `# fail`, `not ok`) and cannot read pytest output. The RED evidence is the verbatim pytest runs quoted above (target tests failing on assertions for the planned behaviour, everything else green). The plan is `type: execute` with `tdd_mode: false`, so the plan-level gate does not apply; recorded, not hidden — same limitation 02-01 noted.
- Running `ruff check` directly on `src/llm4pol/data/` (outside `scripts/check.py`) reports `BLE001`, `RUF046` and `ISC004` from a rule set the project's `[tool.ruff]` does not enable; the gate's ruff step passes. The one such finding inside this plan's edit (`except Exception` at the downloader boundary) carries `# noqa: BLE001` with its reason; the `RUF046` / `ISC004` sites are in `report.py`, `validate.py` (plan 02-04's files) and pre-existing lines of `load.py`, left alone per the scope boundary.
- `pytest -v` prints dots under this project's configuration; `-vv -rA` was needed to capture the per-test PASSED lines quoted above.

## TDD Gate Compliance

Task 1: RED `6c4c9c9` (`test(02-03)`) precedes GREEN `f458082` (`feat(02-03)`). Task 2: RED `3b78d41` precedes GREEN `ba59947`. No REFACTOR commit was needed. Each RED commit touches only test files; each GREEN commit touches only source modules. The RED evidence is a genuine assertion failure of the named target tests (see Recorded lines), not a collection error.

## Known Stubs

None. No placeholder, skipped test or unrun `<verify>`; the untracked `docs/audit/polyomics-041e5834-validation.md` remains plan 02-05's to commit.

## Threat Flags

None beyond the plan's register. T-02-13, T-02-14, T-02-15, T-02-16 and T-02-17 each have their named mitigating test in place. No new network endpoint, auth path or schema boundary was introduced.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 02-04 (registry loader, replicates, noise floor) can build on a loader whose exclusion, pass-through, error and candidate-statistics rules are fixed by tests; it owns `validate.py`, `report.py`, `__main__.py`, `test_data_invariants.py`, `INVARIANTS.md` and `pyproject.toml`, none of which this plan touched.
- Plan 02-05 (ladders, Maxwell, the committed report, CI evidence) inherits `fetch`'s exit-code contract and the real-file identity counts as reproduced facts.
- `fetch`'s stdout line format changed (`(existing)` suffix dropped, `downloaded <name>` for a fetched file); the only consumers are the tests, all green.

---
*Phase: 02-data-foundation*
*Completed: 2026-09-22*

## Self-Check: PASSED

All 8 changed files and the SUMMARY exist on disk; commits 6c4c9c9, f458082, 3b78d41, ba59947 are in `git log`; test counts 11 / 7 / 12 / 4 / 6 match the plan; the final gate printed `SUMMARY: 6/6 steps passed` (82 passed).
