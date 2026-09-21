---
phase: 02-data-foundation
plan: 04
subsystem: data
tags: [jsonschema, pyyaml, tomllib, pandas, pytest, tdd, noise-floor, replicates, check-gate]

# Dependency graph
requires:
  - phase: 02-data-foundation
    provides: "plan 02-01's candidate table (`load.build_candidates`: `<column>_median|_n|_min|_max|_std`, `n_rows`), report model and validator sections; plan 02-02's registry triad (instance, draft 2020-12 schema, provenance); plan 02-03's loader rules (`<column>_n` is the non-null count, ddof=1 std)"
provides:
  - "Seven-step gate: `schema-inventory` after `import-linter` validates every `[tool.llm4polcheck] validated` instance (YAML or JSON) against its JSON Schema; absent table, missing schema path, zero-match `required` glob and instance failure are each a failure (D-06)"
  - "`llm4pol.data.registry.load_registry()` -> frozen `Registry` of nine `PropertySpec`s (column, unit, unit_status, role, physical_range, check_tc, tg_rmse_ladder, tg_rmse_unit, unit_note) with `columns()`, `spec_for_column()`, `by_role()`; validated by jsonschema before any field is read; the barred key is refused with `RegistryError` (D-05, DATA-03, A-7)"
  - "`llm4pol.data.filters.readme_triple_mask(df, registry)` — TC non-null AND eps_dc AND tg inside their registry physical ranges; no numeric literal in the module (T-02-20)"
  - "`llm4pol.data.replicates`: `replicate_structure`, `noise_floor` (candidate table only; median over candidates with n >= 2 of std / |median|, plus absolute and p90), `noise_floor_on_rows` (filter then group, F-61), `same_version_split` over the present `VERSION_COLUMNS`, `replicate_section` (D-04, DATA-05, DATA-07)"
  - "Validator section `Replicate structure and noise floor` with three population-labelled tables and twelve findings pinned to F-50 / F-52 / F-55 / F-56; `run(..., registry=None)` loads the protocol registry (D-07)"
  - "D-9 promoted: `tests/test_data_invariants.py::test_d9_report_states_noise_floor_per_property_with_population` named in INVARIANTS.md; the D-7 test extended with the replicate structure, not duplicated (D-08, DATA-10)"
affects: [02-05, evaluate, loop, every plot (charter section 9 carries the noise floor)]

# Actuals (#2632) — chars/4 over the realized diff (44,343 bytes of added/removed lines), never a harness token count.
actuals:
  tokens: 11100
  tasks: 2
  commits: 4
plan_head_before: 2e9abdf311efdeddae7249841ee7a834579b010f

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Explicit schema inventory: `[tool.llm4polcheck] validated = [{name, instances, schema, required}]`; the gate step is `validate_inventory(ROOT)` and the test suite imports the same function through `tests/conftest.py`'s `sys.path` insertion"
    - "Registry-fed masks: a filter function takes the `Registry` object and reads `spec.column` / `spec.physical_range`; a test proves a changed registry changes the mask (`dataclasses.replace` on the frozen specs)"
    - "Noise floor on the candidate table only: `noise_floor` raises `ValueError` when `<column>_median|_n|_std` are absent, so raw rows cannot be passed by mistake; the only rows entry point is `noise_floor_on_rows`, which filters first and then calls `build_candidates`"
    - "Population labels live in `replicates.py` (`NOISE_POPULATION_ALL`, `NOISE_POPULATION_TRIPLE`, `MULTI_ROW_CANDIDATES`) and are imported by `validate.POPULATIONS`, so the finding line and the table row say the same words"

key-files:
  created:
    - src/llm4pol/data/registry.py
    - src/llm4pol/data/filters.py
    - src/llm4pol/data/replicates.py
    - tests/test_check_inventory.py
  modified:
    - scripts/check.py
    - pyproject.toml
    - src/llm4pol/data/validate.py
    - tests/test_data_registry.py
    - tests/test_data_invariants.py
    - docs/governance/INVARIANTS.md

key-decisions:
  - "`replicate_section` takes a keyword `rows_population` (default `in-scope rows`) so `validate.py` can pass its own `IN_SCOPE_ROWS` constant without `replicates.py` importing from `validate.py` (no cycle); the plan's positional signature `(rows, candidates, registry)` is unchanged"
  - "Candidates whose median is exactly zero are dropped from the relative series only (the absolute series keeps them); on the pinned file no property has such a candidate, so every F-55 / F-56 value reproduces to the printed digit"
  - "`same_version_split` counts NaN as a value (`nunique(dropna=False)`) and uses only the version columns present in the frame; on the pinned file it gives 1,887 same-version / 11,096 cross-version against F-52's 1,888 / 11,096 counted on `smiles_list` groups (one F-35 merge moved a group; tolerance 10, difference 1)"
  - "The RED evidence for Task 2 is a collection `ImportError` on the missing `filters` / `replicates` modules (one module-level `from llm4pol.data import ...` statement), which also keeps `test_d10_...` from running in the RED state; a function-level import that would have kept D-10 green was rejected as a code smell the reviewer would flag. Recorded, not hidden (plan `type: execute`, `tdd_mode: false`)"
  - "Commits made directly on `main` under the orchestrator's sequential instruction with `branching_strategy: none` (same as plans 02-01, 02-02 and 02-03)"

patterns-established:
  - "Finding ids for spreads: `noise_floor_rel_<key>` / `noise_floor_abs_<key>` on the in-scope population, `noise_floor_triple_rel_<key>` on the README-triple population; keys are registry keys, never columns, so the barred column can never appear as a property row"
  - "Report formatting for spreads: relative spreads four decimals (`format_float(x, 4)`), absolute spreads four significant digits (`f\"{x:.4g}\"`), NaN rendered as an em dash"

requirements-completed: [DATA-03, DATA-05, DATA-07, DATA-10]

coverage:
  - id: D1
    description: "`scripts/check.py` runs a seventh step `schema-inventory` after `import-linter` that validates every `[tool.llm4polcheck]` instance against its schema and fails on an absent table, a missing schema path or a zero-match required glob; the gate prints `SUMMARY: 7/7 steps passed`"
    requirement: DATA-03
    verification:
      - kind: unit
        ref: "tests/test_check_inventory.py#test_absent_llm4polcheck_table_fails"
        status: pass
      - kind: unit
        ref: "tests/test_check_inventory.py#test_required_entry_matching_zero_instances_fails"
        status: pass
      - kind: unit
        ref: "tests/test_check_inventory.py#test_yaml_instance_is_validated_not_skipped"
        status: pass
      - kind: unit
        ref: "tests/test_check_inventory.py#test_repository_inventory_validates"
        status: pass
      - kind: unit
        ref: "tests/test_check_inventory.py#test_check_steps_include_schema_inventory_after_import_linter"
        status: pass
      - kind: other
        ref: "pixi run --manifest-path env/pixi.toml check -> Steps: ruff check, ruff format --check, mypy, import-linter, schema-inventory, history-secret-scan, pytest; llm4polcheck inventory: 1 entries, 1 instances processed; SUMMARY: 7/7 steps passed"
        status: pass
    human_judgment: false
  - id: D2
    description: "`load_registry()` returns a typed `Registry` whose nine specs carry column, unit, unit_status, role, physical_range and the check_tc / tg_rmse_ladder filters; snapshot equals `SNAPSHOT_ID`, columns equal `schema.PROPERTY_COLUMNS`; the barred key and a missing file are refused with `RegistryError`"
    requirement: DATA-03
    verification:
      - kind: unit
        ref: "tests/test_data_registry.py#test_load_registry_returns_typed_specs_for_nine_keys"
        status: pass
      - kind: unit
        ref: "tests/test_data_registry.py#test_registry_snapshot_equals_snapshot_id_constant"
        status: pass
      - kind: unit
        ref: "tests/test_data_registry.py#test_registry_columns_equal_loader_property_columns"
        status: pass
      - kind: unit
        ref: "tests/test_data_registry.py#test_load_registry_rejects_an_instance_with_the_barred_key"
        status: pass
      - kind: unit
        ref: "tests/test_data_registry.py#test_load_registry_rejects_a_missing_file"
        status: pass
      - kind: other
        ref: "python -c one-liner -> `polyomics:general_polymers@041e5834 9 (100.0, 900.0) True`"
        status: pass
    human_judgment: false
  - id: D3
    description: "The noise floor is the median over candidates with n >= 2 of std / |median| computed on the candidate table (never on raw rows; mean never used), on the in-scope rows and on the README-triple rows (filter first, then group); the triple mask reads its bounds from the registry"
    requirement: DATA-05
    verification:
      - kind: unit
        ref: "tests/test_data_invariants.py#test_noise_floor_values_on_synthetic_are_medians_of_relative_std"
        status: pass
      - kind: unit
        ref: "tests/test_data_invariants.py#test_readme_triple_mask_uses_registry_ranges"
        status: pass
      - kind: unit
        ref: "tests/test_data_invariants.py#test_noise_floor_on_readme_triple_rows_filters_then_groups"
        status: pass
      - kind: unit
        ref: "tests/test_data_invariants.py#test_same_version_split_uses_only_present_version_columns"
        status: pass
      - kind: other
        ref: "grep -c \"mean()\" src/llm4pol/data/replicates.py (0); no digit in any code line of src/llm4pol/data/filters.py"
        status: pass
    human_judgment: false
  - id: D4
    description: "The report carries `## Replicate structure and noise floor` with rows per candidate, the size histogram, the same-version / cross-version split, and per-property median absolute, median relative and p90 relative spread on two named populations; on the pinned file 12,983 / 17 reproduced and the ten F-52 / F-55 / F-56 values documented within tolerance"
    requirement: DATA-07
    verification:
      - kind: unit
        ref: "tests/test_data_invariants.py#test_d9_report_states_noise_floor_per_property_with_population"
        status: pass
      - kind: integration
        ref: "tests/test_data_invariants.py#test_real_replicate_structure_and_noise_floor_match_research"
        status: pass
      - kind: other
        ref: "pixi run --manifest-path env/pixi.toml python -m llm4pol.data validate -> VALIDATION: 10 reproduced, 10 documented, 0 failed -> exit 0"
        status: pass
    human_judgment: false
  - id: D5
    description: "D-9 is a named test inside the gate and INVARIANTS.md's D-9 guard cell names it and the report section; the D-7 test from plan 02-01 is extended with the replicate structure (9 / 2 / 5 / 3, histogram {1: 7, 2: 1, 3: 1}) rather than duplicated; D-7 and D-10 cells untouched"
    requirement: DATA-10
    verification:
      - kind: unit
        ref: "tests/test_data_invariants.py#test_d7_candidate_table_dedups_replicates_before_any_metric"
        status: pass
      - kind: unit
        ref: "tests/test_data_invariants.py#test_d10_every_count_table_in_report_names_its_population"
        status: pass
      - kind: other
        ref: "sed on INVARIANTS.md: D-9 row names test_d9_... (1); D-7 row names test_d7_... (1); D-7/D-9/D-10 rows saying `| prose |` (0); `git show --format= --stat 10acb31 -- docs/governance/INVARIANTS.md` = 1 insertion, 1 deletion"
        status: pass
    human_judgment: false

# Metrics
duration: 11min
completed: 2026-09-22
status: complete
---

# Phase 2 Plan 04: Registry loader, schema-inventory gate step, replicate structure and noise floor Summary

**The frozen property registry is now enforced twice — by the gate's seventh step `schema-inventory` (`[tool.llm4polcheck]`, every listed protocol instance validated against its JSON Schema on every run) and by a typed `load_registry()` that refuses an invalid instance — and consumed by code that reads ranges from it instead of literals; the validator reports the replicate structure of the 78,676 candidates (12,983 multi-row, max 17) and the per-property noise floor over candidates with n >= 2 on two named populations, reproducing F-55 / F-56 to the printed digit (TC 3.69 %, eps_dc 0.84 %, Tg 5.77 % / 30.2 K; triple TC 4.31 %, eps_dc 1.12 %, Tg 5.40 %), and D-9 is a named test inside the gate.**

## Performance

- **Duration:** 11 min
- **Started:** 2026-09-21T19:11:58Z
- **Completed:** 2026-09-21T19:23:06Z
- **Tasks:** 2 (both TDD: RED then GREEN)
- **Files modified:** 10 (4 created, 6 modified)

## Accomplishments

- `scripts/check.py` gained `validate_inventory` (port of the CALF20 precedent, `calfcheck` -> `llm4polcheck`) and `step_schema_inventory`, registered immediately after `import-linter`; `pyproject.toml` carries `[tool.llm4polcheck]` with one required entry, the property registry v1 against `protocol/schemas/property-registry.json`. Seven tests prove the four failure classes, YAML validation, the repository inventory and the STEPS order.
- `llm4pol.data.registry` reads and validates the instance (`yaml.safe_load` + `jsonschema.validate`) before any field is read and returns frozen `Registry` / `PropertySpec` dataclasses; `columns()` equals `schema.PROPERTY_COLUMNS` in order, `snapshot` equals `SNAPSHOT_ID`, the barred key and a missing file each raise `RegistryError`.
- `llm4pol.data.filters.readme_triple_mask` and `llm4pol.data.replicates` compute the README-triple mask, the replicate structure, the per-property noise floor (candidate table only, median of std / |median|, absolute and p90), the filter-then-group triple floor and the same-version split — with no range literal and no `mean()`.
- The validator writes `## Replicate structure and noise floor` (three tables, each row naming its population) and evaluates twelve new findings; on the pinned file every one is `reproduced` or `documented` with a zero failed count.
- D-9 promoted to `test_d9_report_states_noise_floor_per_property_with_population` and named in INVARIANTS.md; the D-7 test now also pins the replicate structure.

## Task Commits

1. **Task 1 RED** — `1d6479c` (test) — `test(02-04): add failing schema-inventory step and registry-loader tests (D-05, D-06)`; touches only `tests/test_check_inventory.py`, `tests/test_data_registry.py`
2. **Task 1 GREEN** — `5b9b478` (feat) — `feat(02-04): add the schema-inventory check step with the property registry as its first entry, and the typed registry loader (D-05, D-06, DATA-03)`; touches only `scripts/check.py`, `pyproject.toml`, `src/llm4pol/data/registry.py`
3. **Task 2 RED** — `a65195f` (test) — `test(02-04): add failing D-9 invariant, replicate-structure and noise-floor tests; extend the D-7 test (D-08, DATA-05, DATA-07)`; touches only `tests/test_data_invariants.py`
4. **Task 2 GREEN** — `10acb31` (feat) — `feat(02-04): report replicate structure and noise floor per property; promote D-9 to a test (D-04, D-07, D-08, DATA-05, DATA-07, DATA-10)`; touches `filters.py`, `replicates.py`, `validate.py`, `docs/governance/INVARIANTS.md` (1 insertion, 1 deletion)

Full shas: `1d6479cc61449030096639094547870d06792ec6`, `5b9b4784577fc28e10aec48f5fc118aa6dcd7119`, `a65195f3e0201a3bb9dedec898320c7fe76dd507`, `10acb318f879a02bce34c0dd4390c408e5698da6` (from `git log 2e9abdf..HEAD`).

**Plan metadata:** see the `docs(02-04): complete …` commit that follows this file.

## Recorded lines (per the plan's output spec)

**Task 1 RED** (`pytest tests/test_check_inventory.py tests/test_data_registry.py`, 2 collection errors): `ImportError: cannot import name 'validate_inventory' from 'check'`; `ImportError: cannot import name 'registry' from 'llm4pol.data'`.

**Task 1 GREEN:** `26 passed`; gate `Steps: ruff check, ruff format --check, mypy, import-linter, schema-inventory, history-secret-scan, pytest`, `llm4polcheck inventory: 1 entries, 1 instances processed`, mypy `Success: no issues found in 11 source files`, `94 passed in 22.27s`, `SUMMARY: 7/7 steps passed`; one-liner `polyomics:general_polymers@041e5834 9 (100.0, 900.0) True`; `grep -c '"schema-inventory"' scripts/check.py` = 1; `grep -c "^\[tool.llm4polcheck\]" pyproject.toml` = 1.

**Task 2 RED** (`pytest tests/test_data_invariants.py`, 1 collection error): `ImportError: cannot import name 'filters' from 'llm4pol.data'` at the module-level import (see key-decisions on D-10 in the RED state).

**Task 2 GREEN:** `8 passed` (the real-file test included, first run); gate `100 passed in 26.53s`, mypy `Success: no issues found in 13 source files`, `SUMMARY: 7/7 steps passed`; `grep -c "mean()" src/llm4pol/data/replicates.py` = 0; INVARIANTS.md sed checks 1 / 1 / 0.

**`python -m llm4pol.data validate` on the pinned file** (exit 0; the twelve replicate / noise-floor finding lines):

- `finding replicate_multi_row_candidates: reproduce expected=12,983 observed=12,983 reproduced`
- `finding replicate_max_rows: reproduce expected=17 observed=17 reproduced`
- `finding same_version_replicate_candidates: documented expected=1,888 observed=1,887 documented`
- `finding cross_version_rerun_candidates: documented expected=11,096 observed=11,096 documented`
- `finding noise_floor_rel_thermal_conductivity: documented expected=0.0369 observed=0.0369 documented`
- `finding noise_floor_rel_dielectric_const_dc: documented expected=0.0084 observed=0.0084 documented`
- `finding noise_floor_rel_tg: documented expected=0.0577 observed=0.0577 documented`
- `finding noise_floor_rel_density: documented expected=0.0034 observed=0.0034 documented`
- `finding noise_floor_abs_tg: documented expected=30.2000 observed=30.2107 documented`
- `finding noise_floor_triple_rel_thermal_conductivity: documented expected=0.0431 observed=0.0431 documented`
- `finding noise_floor_triple_rel_dielectric_const_dc: documented expected=0.0112 observed=0.0112 documented`
- `finding noise_floor_triple_rel_tg: documented expected=0.0540 observed=0.0540 documented`
- `VALIDATION: 10 reproduced, 10 documented, 0 failed -> exit 0`

**Tolerances approached:** none within a factor of 5 of the bound. `noise_floor_abs_tg` 30.2107 vs 30.2 (tolerance 0.5; the research rounded to one decimal). `same_version_replicate_candidates` 1,887 vs 1,888 (tolerance 10): F-52 counted on (`smiles_list`, tacticity) groups (12,984 multi-row); the report counts by `candidate_id` (12,983 multi-row, one fewer after the F-35 merges), and the one merged group was same-version. Population definitions used: in-scope rows (95,332) -> candidate table (78,676; n_groups per property: TC 9,439, eps_dc 12,842, Tg 2,377, rg 12,983, r2 12,906, ffv 9,453, sp_ced 8,606, density 12,983, refractive_index 12,842 — F-55's counts, with rg / density 12,983 instead of 12,984 by `candidate_id`); README-triple rows (TC non-null AND eps_dc in [1, 20] AND Tg in [100, 900] from the registry) -> `build_candidates` -> 1,725 candidates with n >= 2 for each of the three (F-56 exactly).

**Histogram on the pinned file** (printed, not pinned; by `candidate_id`): 1: 65,693 / 2: 11,368 / 3: 577 / 4: 55 / 5: 962 / 6: 17 / 7: 2 / 9: 1 / 17: 1 — differs from F-50's smiles-group histogram by the F-35 merges (65,698 / 578 / 964 / 16 and no size-9 group there), as the plan anticipated. Rows in multi-row candidates 29,639 (F-50: 29,637 on smiles groups).

**Full-table values on all in-scope rows** (median_rel_std / p90): rg 0.0350 / 0.0971, r2 0.1631 / 0.4180, ffv 0.0239 / 0.0650, sp_ced 0.0223 / 0.0648, refractive_index 0.0014 / 0.0049 — each matches F-55's un-pinned values (0.035, 0.163, 0.024, 0.022, 0.0014).

## Files Created/Modified

- `scripts/check.py` — imports `json`, `tomllib`, `jsonschema`, `yaml`; `validate_inventory(root) -> list[str]`; `step_schema_inventory()`; `STEPS` seven entries; docstring lists the inventory
- `pyproject.toml` — comment header and `[tool.llm4polcheck] validated = [...]` with one required entry
- `src/llm4pol/data/registry.py` (121 lines) — `RegistryError`, `PropertySpec`, `Registry`, `REGISTRY_PATH`, `SCHEMA_PATH`, `load_registry`
- `src/llm4pol/data/filters.py` (39 lines) — `TRIPLE_KEYS`, `within_physical_range`, `readme_triple_mask`
- `src/llm4pol/data/replicates.py` (236 lines) — `MIN_REPLICATES`, `P90`, `VERSION_COLUMNS`, population labels, `NOISE_HEADER`, `ReplicateStructure`, `NoiseFloor`, `replicate_structure`, `noise_floor`, `noise_floor_on_rows`, `same_version_split`, `replicate_section`
- `src/llm4pol/data/validate.py` (310 lines) — twelve expectations and populations, `_replicates`, `_build_report(..., registry)`, `run(..., registry=None)`
- `tests/test_check_inventory.py` — 7 tests, `EXPECTED_STEPS`, `_write_pyproject`
- `tests/test_data_registry.py` — +5 loader tests (19 total); docstring's last paragraph updated because the module now imports the source package
- `tests/test_data_invariants.py` — D-7 test extended; +6 tests (8 total); `_loaded`, `_findings` helpers; `NOISE_HEADER`, `NOISE_ALL`, `NOISE_TRIPLE`, `TRIPLE`
- `docs/governance/INVARIANTS.md` — D-9 guard cell only

## Decisions Made

See `key-decisions` in the frontmatter. In brief: `replicate_section` takes a keyword `rows_population`; zero-median candidates are dropped from the relative series only; `same_version_split` treats NaN as a value; Task 2's RED is a module-level collection error; commits on `main` per the orchestrator.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] `noise_floor` and `replicate_structure` refuse a frame that is not the candidate table**
- **Found during:** Task 2 STEP 1 (behaviour 1 says `noise_floor` "accepts only the candidate table")
- **Issue:** The plan states the constraint but no mechanism; a raw-rows frame passed by mistake would raise an opaque `KeyError` on `<column>_n`, or worse, a frame that happened to carry such columns would be aggregated without dedup (D-7).
- **Fix:** `_require_candidate_columns` raises `ValueError("noise_floor takes the candidate table (build_candidates output); missing ...")`; `replicate_structure` raises on a missing `n_rows`. The extended D-7 test asserts `pytest.raises(ValueError, match="candidate")` on the rows parquet.
- **Files modified:** `src/llm4pol/data/replicates.py`, `tests/test_data_invariants.py`
- **Verification:** `test_d7_candidate_table_dedups_replicates_before_any_metric` PASSED
- **Committed in:** `a65195f`, `10acb31`

**2. [Rule 3 - Blocking] `tests/test_data_registry.py` docstring paragraph rewritten**
- **Found during:** Task 1 STEP 1
- **Issue:** The module docstring stated "this module does not depend on the source package (plan 02-04 adds the loader tests that do)"; after this plan's import of `llm4pol.data.registry` that sentence would be false.
- **Fix:** The paragraph now says the triad tests import only the four libraries and the loader tests at the end import `llm4pol.data.registry`.
- **Files modified:** `tests/test_data_registry.py`
- **Committed in:** `1d6479c`

---

**Total deviations:** 2 auto-fixed (1 Rule 2, 1 Rule 3). **Impact on plan:** both make the plan's own statements true in code; no scope change, no expected number or tolerance touched.

## Issues Encountered

- The plan's RED description for Task 2 says "the untouched `test_d10_…` stays green"; with one module-level `from llm4pol.data import filters, load, registry, replicates, report, validate` the whole module fails to collect in the RED state, so D-10 did not run until GREEN. Keeping it green would have required function-level imports of the not-yet-existing modules, which I judged a worse test file. D-10 is green in GREEN (`8 passed`) and the D-10 test body is byte-identical to plan 02-01's.
- `gsd_run check tdd-red-evidence` was not run: plans 02-01, 02-02 and 02-03 recorded that the checker parses node:test TAP output and returns `INVALID_RED (zero_tests_discovered)` for pytest runs, and this plan is `type: execute` with `tdd_mode: false`, so the plan-level gate does not apply. The RED evidence is the two verbatim collection errors quoted above; the plan itself specifies collection-error REDs for modules that do not exist before GREEN.
- A bash heredoc carrying the `scripts/check.py` edit script tripped the shell parser (triple-quoted Python strings inside a quoted heredoc); the edit scripts were written to the session scratchpad and run from there instead. No repository effect.
- `pixi run --manifest-path env/pixi.toml python -m pytest …` needs `PYTHONPATH=src` in the environment (only the `check` task sets it); the plan's verify commands were run with it exported.

## TDD Gate Compliance

Task 1: RED `1d6479c` (`test(02-04)`) precedes GREEN `5b9b478` (`feat(02-04)`). Task 2: RED `a65195f` precedes GREEN `10acb31`. No REFACTOR commit was needed (GREEN passed the gate on its first full run in both tasks, after one mypy variance fix in `replicates.py` before the commit). Each RED commit touches only test files; each GREEN commit touches only source modules plus, for Task 2, the single INVARIANTS.md row the plan assigns to it. Both REDs are collection errors by the plan's design (modules that do not exist before GREEN).

## Known Stubs

None. No placeholder, skipped test or unrun `<verify>`; every `<verify>` command of both tasks was run and its `fails_when` condition checked. The untracked `docs/audit/polyomics-041e5834-validation.md` (rewritten by the validate run above, now carrying the new section) remains plan 02-05's to commit.

## Threat Flags

None beyond the plan's register. T-02-18 (`test_absent_llm4polcheck_table_fails`, `test_required_entry_matching_zero_instances_fails`), T-02-19 (`yaml.safe_load` only, in `check.py` and `registry.py`), T-02-20 (`test_readme_triple_mask_uses_registry_ranges`), T-02-21 (two named populations on every table and finding), T-02-22 (`mean()` absent from `replicates.py`) each have their mitigation in place. No new network endpoint, auth path or schema boundary was introduced; the inventory step reads only `pyproject.toml` and the files it names.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 02-05 (ladders, Maxwell, the committed report, CI evidence) extends `filters.py` (the plan says so in its docstring) and `validate.EXPECTED_POLYOMICS` / `POPULATIONS`; the registry loader gives it `tg_rmse_ladder`, `check_tc` and every range without a literal; `docs/audit/polyomics-041e5834-validation.md` already carries the replicate section it will commit.
- D-8 and A-7 remain `prose` in INVARIANTS.md for plan 02-05; D-7, D-9 and D-10 are tests.
- The noise floor every later plot must carry (charter section 9) and the D-16 gate reads is now a reproducible number: TC 0.0369 (abs 0.0082 W/(m*K)), eps_dc 0.0084, Tg 0.0577 (30.2 K), density 0.0034 on candidates with n >= 2.

---
*Phase: 02-data-foundation*
*Completed: 2026-09-22*

## Self-Check: PASSED

All 10 changed files and the SUMMARY exist on disk; commits 1d6479c, 5b9b478, a65195f, 10acb31 are in `git log`; test counts 7 / 19 / 8 match the plan; the final gate printed `SUMMARY: 7/7 steps passed` (100 passed) with `llm4polcheck inventory: 1 entries, 1 instances processed`.
