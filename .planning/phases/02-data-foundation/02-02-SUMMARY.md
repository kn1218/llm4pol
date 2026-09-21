---
phase: 02-data-foundation
plan: 02
subsystem: protocol
tags: [jsonschema, draft-2020-12, pyyaml, property-registry, provenance, pytest]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: six-step gate (scripts/check.py) whose pytest step picks up tests/, protocol/ directory contract (protocol/README.md), tests/test_governance.py house style
  - phase: 02-data-foundation (plan 02-01)
    provides: pyyaml + types-pyyaml locked; SNAPSHOT_ID `polyomics:general_polymers@041e5834` that the registry's `snapshot` leaf must equal (asserted in plan 02-04)
provides:
  - "`protocol/schemas/property-registry.json` — draft 2020-12 schema; `propertyNames` enum of the nine charter keys + required + min/maxProperties 9 make A-7 structural; `additionalProperties: false` at root, `$defs.property`, `$defs.condition`, `filters`; condition consts 300 K / 1 atm / GAFF2_mod / RESP / isotropic_amorphous; `physical_range` prefixItems; `filters` limited to `check_tc` / `tg_rmse_ladder` / `tg_rmse_unit`; `unit_note` required when `unit_status` is `unverified`"
  - "`protocol/property-registry_v1.yaml` — the M1 freeze of charter §7: nine entries in charter order with column, unit, unit_status, condition, role, physical_range; `check_tc: true` on thermal_conductivity; `tg_rmse_ladder [0.05, 0.1, 0.2, 0.5, 1.0]` in `(g/cm^3)^2` on tg with no cut; r2 `nm^2` unverified with a unit_note"
  - "`protocol/property-registry_v1.provenance.yaml` — 62 entries, one per leaf; 37 paper_or_source (F-01, F-20..F-30), 24 protocol_decision, 1 unresolved (`properties.r2.unit`)"
  - "`tests/test_data_registry.py` — 14 tests inside the gate; imports only json / yaml / jsonschema / pathlib (no source-package import)"
affects: [02-04, 02-05, evaluate, loop]

# Actuals (#2632) — chars/4 over the realized diff (added lines of the four commits), never a harness token count.
actuals:
  tokens: 11600
  tasks: 2
  commits: 4
plan_head_before: 68e7cc5941551b84f5fef78fa80815c498168800

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Protocol triad: `<name>_v1.yaml` + `schemas/<name>.json` + `<name>_v1.provenance.yaml`; the instance header states the change route (a new file, never an edit once cited), the float rule (F-47) and what the ranges are NOT (D-16)"
    - "A-7 by construction: the schema's `propertyNames` enum is the closed key set; injecting any other key fails validation before any code sees it"
    - "Provenance leaf-set equality: `_leaf_paths(instance) == set(provenance['entries'])`, with a `condition` mapping counted as one leaf, so a value cannot move without its provenance"
    - "Barred-name fragment discipline: the test body builds the excluded column name from two fragments; only `def test_` lines carry the literal so INVARIANTS.md and evidence can cite the test by name"

key-files:
  created:
    - protocol/schemas/property-registry.json
    - protocol/property-registry_v1.yaml
    - protocol/property-registry_v1.provenance.yaml
    - tests/test_data_registry.py
  modified: []

key-decisions:
  - "`properties.tg.filters.tg_rmse_unit` is `paper_or_source` (RadonPy `sim/preset/tg.py`, F-23), not `protocol_decision`: the plan's `<action>` and `<acceptance_criteria>` say so and the unit of a column is a source fact, while the `<behavior>` line 'every filters.* leaf is protocol_decision' contradicted them. Test 13 pins the two filter *choices* (`check_tc`, `tg_rmse_ladder`) as decisions and `tg_rmse_unit` as sourced with `fact: F-23`."
  - "The registry instance's `condition` block is repeated verbatim in each of the nine entries (D-05 asks for a per-entry condition) rather than hoisted to the top level as the research skeleton sketched; the schema's `$defs.condition` consts make the nine copies unable to differ."
  - "The RED evidence for both TDD steps is a `FileNotFoundError` on the not-yet-written protocol file, exactly as the plan specifies; under #3770 that classifies INVALID_RED, recorded here as in plan 02-01 (plan `type: execute`, `tdd_mode` unset)."
  - "Commits made directly on `main`: the orchestrator ran this executor in sequential mode on the main working tree with `branching_strategy: none` (same as plans 01-01 and 02-01); the executor's protected-branch assertion was consciously overridden by that instruction."

patterns-established:
  - "Registry values are read from `protocol/property-registry_v1.yaml`; nothing downstream hardcodes a range, a unit or a filter (plans 02-04 and 02-05 consume it)"
  - "Every numeric protocol value is a YAML number with a decimal point; `test_registry_numbers_are_numbers_not_strings` walks every scalar"

requirements-completed: [DATA-03, DATA-09]

coverage:
  - id: D1
    description: "Schema at protocol/schemas/property-registry.json (draft 2020-12) admits exactly nine keys; the uncorrected static permittivity column cannot be registered (A-7 by construction)"
    requirement: DATA-03
    verification:
      - kind: unit
        ref: "tests/test_data_registry.py#test_registry_schema_is_a_valid_draft_2020_12_schema"
        status: pass
      - kind: unit
        ref: "tests/test_data_registry.py#test_a7_static_dielectric_const_is_rejected_by_the_registry_schema"
        status: pass
      - kind: unit
        ref: "tests/test_data_registry.py#test_schema_rejects_an_unknown_filter_key_and_a_bad_range"
        status: pass
      - kind: other
        ref: "grep -c static_dielectric_const protocol/property-registry_v1.yaml (0); grep -v 'def test_' tests/test_data_registry.py | grep -c static_dielectric_const (0)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Registry instance v1 declares the nine keys in charter order with column, unit, unit_status (R-4: eight verified, r2 unverified with a note), pinned condition, role and physical_range; validates against the schema"
    requirement: DATA-03
    verification:
      - kind: unit
        ref: "tests/test_data_registry.py#test_registry_instance_validates_against_its_schema"
        status: pass
      - kind: unit
        ref: "tests/test_data_registry.py#test_registry_declares_exactly_the_nine_keys_in_charter_order"
        status: pass
      - kind: unit
        ref: "tests/test_data_registry.py#test_registry_units_and_status_match_research_r4"
        status: pass
      - kind: unit
        ref: "tests/test_data_registry.py#test_registry_condition_matches_the_pinned_run_conditions"
        status: pass
      - kind: unit
        ref: "tests/test_data_registry.py#test_registry_roles_follow_charter_table"
        status: pass
      - kind: unit
        ref: "tests/test_data_registry.py#test_registry_header_names_snapshot_and_revision"
        status: pass
      - kind: other
        ref: "pixi run --manifest-path env/pixi.toml python -c '…jsonschema.validate(i, s); print(\"registry ok\", len(i[\"properties\"]))' -> registry ok 9"
        status: pass
    human_judgment: false
  - id: D3
    description: "Tg physical range [100, 900] K and the tg_rmse ladder [0.05, 0.1, 0.2, 0.5, 1.0] in (g/cm^3)^2 recorded with no cut applied; check_tc: true recorded as the TC quality filter (R-2, DATA-09)"
    requirement: DATA-09
    verification:
      - kind: unit
        ref: "tests/test_data_registry.py#test_registry_physical_ranges_and_filters_are_pinned"
        status: pass
      - kind: unit
        ref: "tests/test_data_registry.py#test_registry_numbers_are_numbers_not_strings"
        status: pass
      - kind: other
        ref: "grep -c tg_rmse_max protocol/property-registry_v1.yaml protocol/schemas/property-registry.json (0, 0)"
        status: pass
    human_judgment: false
  - id: D4
    description: "Provenance file with 62 entries equal to the instance's leaf set; classes complete; properties.r2.unit the only unresolved leaf; ranges named physical-range filters, never a D-16 decision"
    requirement: DATA-03
    verification:
      - kind: unit
        ref: "tests/test_data_registry.py#test_provenance_leaf_paths_equal_registry_leaf_paths"
        status: pass
      - kind: unit
        ref: "tests/test_data_registry.py#test_provenance_classes_are_valid_and_complete"
        status: pass
      - kind: unit
        ref: "tests/test_data_registry.py#test_provenance_never_calls_a_range_a_decision"
        status: pass
      - kind: other
        ref: "python -c '…print(len(e), sorted({…}), [unresolved])' -> 62 ['paper_or_source', 'protocol_decision', 'unresolved'] ['properties.r2.unit']"
        status: pass
    human_judgment: false
  - id: D5
    description: "Gate green with the new test module inside it"
    verification:
      - kind: other
        ref: "pixi run --manifest-path env/pixi.toml check -> SUMMARY: 6/6 steps passed; pytest 49 passed (35 pre-existing + 14 new)"
        status: pass
    human_judgment: false

# Metrics
duration: 7min
completed: 2026-09-22
status: complete
---

# Phase 2 Plan 02: Registry triad Summary

**The property registry is frozen as protocol: a draft 2020-12 schema whose `propertyNames` enum admits exactly the nine charter keys (so the uncorrected static permittivity column cannot be registered), a v1 instance for `polyomics:general_polymers@041e5834` carrying research-verified units with their status (r2 `nm^2` unverified), the validator's physical ranges, `check_tc: true` and the `tg_rmse` ladder with no cut, and a 62-leaf provenance file naming the origin of every value — pinned by 14 tests inside the gate.**

## Performance

- **Duration:** 7 min
- **Started:** 2026-09-21T18:46:46Z
- **Completed:** 2026-09-21T18:54:02Z
- **Tasks:** 2
- **Files modified:** 4 (4 created, 0 modified)

## Accomplishments

- `protocol/schemas/property-registry.json` is the charter §7 M1 freeze path: root `additionalProperties: false`; `properties.propertyNames.enum` of the nine keys with `required`, `minProperties: 9`, `maxProperties: 9`; `$defs.condition` with five consts; `$defs.property` with `unit_status` / `role` enums, `physical_range` `prefixItems` + `items: false`, `filters` restricted to `check_tc` / `tg_rmse_ladder` / `tg_rmse_unit`, and an `if`/`then` requiring `unit_note` for an `unverified` unit. Injecting the barred key into a copy of the instance raises `jsonschema.ValidationError` (A-7 by construction).
- `protocol/property-registry_v1.yaml` records R-4 exactly: `W/(m*K)`, `1`, `K`, `angstrom`, `1`, `MPa`, `g/cm^3`, `1` verified; `r2` `nm^2` unverified with the Table S3 vs data note. Ranges: ε_dc [1.0, 20.0] and Tg [100.0, 900.0] are the README's 43,561 filter (F-08); the others are A4 ranges. `tg.filters` holds the ladder and its unit only — no `tg_rmse_max`, no cut (R-2). The header describes the excluded column without naming it; `grep -c static_dielectric_const` on the instance prints 0.
- `protocol/property-registry_v1.provenance.yaml`: 62 leaves = 4 header + 9 × 6 + `check_tc` + `tg_rmse_ladder` + `tg_rmse_unit` + `r2.unit_note`; 37 `paper_or_source` citing F-01, F-20..F-30; 24 `protocol_decision`; `properties.r2.unit` the only `unresolved`, with `target_phase` and `pass_condition`. Every `physical_range` rationale contains `physical-range filter`; none contains `threshold =` or fixes D-16.
- `tests/test_data_registry.py` — 14 tests, `grep -c llm4pol` = 0, the barred literal only on the `def test_` line; the gate is `SUMMARY: 6/6 steps passed`, pytest `49 passed`.

## Task Commits

Each TDD task was committed as RED then GREEN:

1. **Task 1 RED** — `1b55b89` (test) — `test(02-02): add failing property-registry schema and instance tests (D-05, A-7, R-4)`; `git show --stat --format= 1b55b89` lists exactly `tests/test_data_registry.py`
2. **Task 1 GREEN** — `dedf34f` (feat) — `feat(02-02): freeze property registry v1 — schema with A-7 by construction, units with status, ranges, check_tc and the tg_rmse ladder (D-05, R-2, R-4, DATA-03)`
3. **Task 2 RED** — `e4ef455` (test) — `test(02-02): add failing provenance leaf-set and class tests (D-05 triad)`
4. **Task 2 GREEN** — `f5b4078` (feat) — `feat(02-02): add property-registry v1 provenance — 62 leaves, r2 unit unresolved (D-05, F-25)`

Full shas: `1b55b89`, `dedf34f`, `e4ef455`, `f5b4078` (measured: `git rev-list --count 68e7cc5..HEAD` = 4).

**Plan metadata:** the `docs(02-02): complete …` commit that follows this file.

## Recorded lines (per the plan's output spec)

- Task 1 RED: all 11 tests `FAILED` with `FileNotFoundError: [Errno 2] No such file or directory: '…\protocol\property-registry_v1.yaml'` (the schema test on the schema path). Task 2 RED: the 3 provenance tests `FAILED` with `FileNotFoundError … property-registry_v1.provenance.yaml`; the 11 Task 1 tests still passed.
- `registry ok 9`
- `62 ['paper_or_source', 'protocol_decision', 'unresolved'] ['properties.r2.unit']`
- `yaml.safe_load` types: every `physical_range` element `float`; ladder `['float', 'float', 'float', 'float', 'float']`
- Verify greps: instance non-comment barred name 0; instance any-line barred name 0; test body (non-`def test_`) barred name 0; `tg_rmse_max` 0 in both protocol files; `llm4pol` in the test module 0
- Gate after Task 1: `SUMMARY: 6/6 steps passed`, `46 passed`; after Task 2: `SUMMARY: 6/6 steps passed`, `49 passed in 21.52s`; `Steps: ruff check, ruff format --check, mypy, import-linter, history-secret-scan, pytest`
- Schema constraints relaxed from the plan: **none**. Every constraint the plan listed is in the file (`propertyNames`, `minProperties`/`maxProperties` 9, four `additionalProperties: false`, `prefixItems`, `if`/`then`).

## Files Created/Modified

- `protocol/schemas/property-registry.json` — the draft 2020-12 schema (M1 freeze path, charter §7)
- `protocol/property-registry_v1.yaml` — registry instance v1: header comment (level, change route, float rule, ranges ≠ D-16, filters and no cut, A-7, status rule), four header keys, nine entries
- `protocol/property-registry_v1.provenance.yaml` — 62 entries keyed by dotted leaf path
- `tests/test_data_registry.py` — `ROOT`, `REGISTRY`, `SCHEMA`, `PROVENANCE`, `NINE_KEYS`, `_load_yaml` (`safe_load` only), `_load_schema`, `_walk_scalars`, `_leaf_paths`, 14 tests

## Decisions Made

See `key-decisions` in the frontmatter: `tg_rmse_unit` sourced not decided (plan-internal conflict resolved toward the action/acceptance text), per-entry `condition` repeated as D-05 asks, RED evidence is the plan-specified `FileNotFoundError`, commits on `main` under the sequential instruction.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Plan-internal conflict on the class of `properties.tg.filters.tg_rmse_unit`**
- **Found during:** Task 2 (writing Test 13)
- **Issue:** `<behavior>` Test 13 says every `filters.*` leaf is `protocol_decision`; `<action>` STEP 2 and the acceptance criterion ("every `paper_or_source` entry carries a `fact` id from F-01, F-20..F-30 or F-23") make `tg_rmse_unit` `paper_or_source` with `fact: F-23`. Both cannot hold.
- **Fix:** Test 13 pins `check_tc` and `tg_rmse_ladder` (the filter choices) as `protocol_decision` and asserts `tg_rmse_unit` is `paper_or_source` with `fact: F-23` — the unit of a column is a source fact, which is the principle the whole plan applies to `unit` leaves.
- **Files modified:** `tests/test_data_registry.py`, `protocol/property-registry_v1.provenance.yaml`
- **Verification:** `test_provenance_classes_are_valid_and_complete` PASSED; the verify command's class listing is the expected `62 [...] ['properties.r2.unit']`.
- **Committed in:** `e4ef455` (test), `f5b4078` (provenance)

**2. [Rule 1 - Bug] Test-module docstring named the source package**
- **Found during:** Task 2 acceptance check (`grep -c "llm4pol" tests/test_data_registry.py` printed 1)
- **Issue:** The docstring sentence "does not depend on the ``llm4pol`` package" tripped the acceptance grep although nothing is imported.
- **Fix:** Reworded to "does not depend on the source package"; grep prints 0.
- **Files modified:** `tests/test_data_registry.py`
- **Verification:** `grep -c "llm4pol" tests/test_data_registry.py` = 0; ruff check/format clean.
- **Committed in:** `f5b4078` (with the GREEN provenance commit; the RED commit `1b55b89` still lists exactly the test file)

---

**Total deviations:** 2 auto-fixed (2 bugs in the plan text / test wording). **Impact on plan:** No value, unit, range or filter changed; no schema constraint relaxed.

## Issues Encountered

- `pytest` run directly needs `PYTHONPATH=src` (tests/conftest.py imports the data package); the gate sets it. Not a defect — recorded so the verify commands are reproducible outside the gate.
- The RED evidence for both steps is the plan-specified `FileNotFoundError` (no assertion failure is possible before the protocol files exist); `gsd_run check tdd-red-evidence` would classify it INVALID_RED under #3770. Recorded, not hidden; no test skipped or weakened.

## TDD Gate Compliance

RED `test(02-02)` `1b55b89` precedes GREEN `feat(02-02)` `dedf34f`; RED `test(02-02)` `e4ef455` precedes GREEN `feat(02-02)` `f5b4078`. No REFACTOR commit was needed (both GREENs passed on the first run and the gate was already clean).

## Known Stubs

None. The three protocol files carry real values with provenance; the test module has no skip, xfail or placeholder.

## Threat Flags

None beyond the plan's register. T-02-08 (YAML deserialisation): the tests use `yaml.safe_load` only; the instance uses no tags, anchors or flow-style objects. T-02-09, T-02-10, T-02-11, T-02-12: each mitigated by the named test.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 02-04 adds `llm4pol.data.registry` (loader reading this instance and schema), the `[tool.llm4polcheck]` inventory entry and the `schema-inventory` check step; its `snapshot == SNAPSHOT_ID` test closes the D-01 link stated in the provenance.
- Plan 02-05's ladders read `physical_range` and `filters` from the loaded registry; the `tg_rmse` rung counts and the `check_tc` count (42,733) are printed beside 43,561.
- Open for the owner (not blocking): which rung of the ladder, if any, and whether the Phase 3 hidden table applies `check_tc` (Open Question 2); `r2` unit resolution is deferred to M8 or the first phase making r2 a design variable.

---
*Phase: 02-data-foundation*
*Completed: 2026-09-22*

## Self-Check: PASSED

All 4 created files exist on disk; commits 1b55b89, dedf34f, e4ef455, f5b4078 are in `git log`; the final gate printed `SUMMARY: 6/6 steps passed` with 49 tests.
