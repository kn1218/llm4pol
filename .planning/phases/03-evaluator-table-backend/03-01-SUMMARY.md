---
phase: 03-evaluator-table-backend
plan: 01
subsystem: evaluate
tags: [jsonschema, draft-2020-12, dataclasses, protocol, pyarrow, pandas, pytest, tdd, tracer, cli]

# Dependency graph
requires:
  - phase: 02-data-foundation
    provides: "`llm4pol.data.registry.load_registry()` / `Registry` / `PropertySpec` (keys, columns, units, snapshot id); `snapshot.candidates_parquet(snapshot.processed_dir(root))`; `load.load` writing the 49-column candidate parquet with `llm4pol.snapshot` metadata; `identity.candidate_id`; `conftest.SYNTHETIC_ROWS` / `synthetic_root`; the seven-step gate with `[tool.llm4polcheck]`"
provides:
  - "`llm4pol.evaluate.contract`: `Status`, `STATUSES`, `MissingReason`, `MISSING_REASONS`, `parse_status`, `Cost`, `Lookup`, `Backend` (runtime-checkable Protocol), `BatchEntry`, `EvalRequest`, `EvalResult` (`to_json` / `from_json` / `from_lookup`), `EvalResponse`, `RequestError`, `SCHEMA_DIR`, `REQUEST_SCHEMA_PATH`, `RESPONSE_SCHEMA_PATH`, `load_schema`, `request_validator`, `response_validator`, `parse_request` (Draft 2020-12 validation before any dataclass; JSON pointer in the message)"
  - "`llm4pol.evaluate.registry.PropertyTable`: the only `load_registry` call site under `evaluate` (`load`, `snapshot`, `supported`, `spec`, `columns`)"
  - "`llm4pol.evaluate.backends.table.TableBackend` (`name` `table`, `provenance_tier` `md_simulated`, `source` = registry snapshot; pyarrow -> pandas indexed by `candidate_id`, loaded once per instance, `SnapshotMismatch` when the parquet metadata differs; NaN -> None; spread None when n < 2; no population filter)"
  - "`llm4pol.evaluate.evaluator.Evaluator(backend, properties).evaluate(request)`: decision order unsupported -> candidate_unknown -> error -> value_absent -> ok; results in request order; `evals` charged once per distinct candidate per request on its first `ok`; `cpu_hours` 0.0; response cost is the sum"
  - "`python -m llm4pol.evaluate --request <json> [--root <repo>]` (exit 0 / 2) and the `evaluate` pixi task"
  - "`protocol/schemas/eval-request.json`, `protocol/schemas/eval-response.json` (M2 freeze, charter section 7) and their committed instances `protocol/examples/eval-request.example.json`, `eval-response.example.json` registered in `[tool.llm4polcheck]` (gate prints `llm4polcheck inventory: 3 entries, 3 instances processed`)"
  - "Fixtures: `conftest.make_synthetic_root`, `synthetic_candidates` (9-candidate parquet), `real_candidates` (read-only, skips when absent), `SYNTHETIC_EXAMPLE_REQUEST`, `UNKNOWN_CANDIDATE_ID`"
  - "Tests: `tests/test_evaluate_cli.py` (3), `tests/test_evaluate_contract.py` (20), `tests/test_evaluate_table.py` (11); `test_check_inventory.py` updated to 3 entries"
affects: [03-02 (cache, budget meter, error path extend Evaluator and TableBackend), 03-03 (import-linter contracts, real-file batch, evidence), 05-loop (consumes EvalRequest/EvalResponse; applies population masks itself), 08-comparison-arms (same evaluator contract)]

# Actuals (#2632) — chars/4 over the realized diff (70,707 bytes of added/removed lines), never a harness token count.
actuals:
  tokens: 17700
  tasks: 3
  commits: 5
plan_head_before: 03190d33e4ef9fdd95181edb1369f94fa5bca41d

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Contract-first evaluator: `parse_request` validates the caller's JSON against the Draft 2020-12 schema before any dataclass exists; the response is validated in tests, and the committed example is the evaluator's own output so it can never go stale"
    - "Status decided in the orchestrator, facts from the backend: `Evaluator._lookup` answers `unsupported` from `PropertyTable` before the backend is consulted; `TableBackend.lookup` distinguishes `candidate_unknown` from `value_absent`; any backend exception becomes `error` with the class name"
    - "Backend as a runtime-checkable Protocol with `@property` members satisfied by plain class attributes (`name = \"table\"`); `TableBackend.source` is read from `PropertyTable.snapshot`, never a literal"
    - "Per-request charging set: `evals` counts distinct candidates on their first `ok` result; `unsupported` / `missing` / `error` cost `Cost(0, 0.0)`"
    - "`from_json` readers reject `bool` where `int` / `float` is expected and raise one exception class (`ValueError`) at the boundary through `_wrong_type`, so the 03-02 cache replay handles every malformed record the same way"
    - "Ruff isort `known-first-party = [\"llm4pol\"]`: submodule imports are classified by declaration, so a RED test importing a not-yet-existing module keeps a stable import order through GREEN"

key-files:
  created:
    - src/llm4pol/evaluate/__init__.py
    - src/llm4pol/evaluate/contract.py
    - src/llm4pol/evaluate/registry.py
    - src/llm4pol/evaluate/evaluator.py
    - src/llm4pol/evaluate/__main__.py
    - src/llm4pol/evaluate/backends/__init__.py
    - src/llm4pol/evaluate/backends/table.py
    - protocol/schemas/eval-request.json
    - protocol/schemas/eval-response.json
    - protocol/examples/eval-request.example.json
    - protocol/examples/eval-response.example.json
    - tests/test_evaluate_cli.py
    - tests/test_evaluate_contract.py
    - tests/test_evaluate_table.py
  modified:
    - tests/conftest.py
    - tests/test_check_inventory.py
    - pyproject.toml
    - env/pixi.toml
    - protocol/README.md

key-decisions:
  - "`from_json` keeps `ValueError` (the plan's contract, relied on by the 03-02 cache replay) although ruff 0.16 enables TRY004 (prefer TypeError): the wrong-type rejection is centralised in `_wrong_type`, whose docstring states why a malformed payload is a value problem, instead of seven `noqa` lines"
  - "Ruff isort `known-first-party = [\"llm4pol\"]` added to pyproject.toml in the RED commit (Rule 3): without it ruff classified the not-yet-existing `llm4pol.evaluate` as third-party and would have re-sorted the test imports after GREEN, the instability plan 02-01 recorded"
  - "The `__init__.py` docstring was reworded so no line begins with `from`: the verify grep `^(from|import) .*backends` counts lines, not import statements, and a docstring line tripped it"
  - "`EvalResult.from_json` reads `reason` only when the key is present (absent and `null` both map to `None`), matching `to_json`, which drops the key when `None`"
  - "Commits made directly on `main` under the orchestrator's sequential instruction with `branching_strategy: none` (same as plans 01-01 and 02-01..02-05); `git.base-branch --is-protected main` answers true and no `allow_default_branch_commits` override is set — recorded, not resolved"

patterns-established:
  - "Test-file convention for the evaluator: `_evaluator(root)` builds `Evaluator(TableBackend(candidates_parquet(processed_dir(root)), properties=PropertyTable.load()), PropertyTable.load())`; `_request(pairs)` goes through `parse_request` on a dict; the fixture parquet is read back with `pd.read_parquet(...).set_index(\"candidate_id\")` for cross-checks"
  - "The barred column's name is built from fragments (`\"static_\" + \"dielectric_const\"`) in test bodies; `grep -v \"def test_\" | grep -c static_dielectric_const` prints 0"
  - "RED commits carry the lint/format steps clean and the pytest count of the RED state in the message; the full 7/7 gate is run before every GREEN / feat commit"

requirements-completed: [EVAL-01, EVAL-02, EVAL-03, EVAL-05]

coverage:
  - id: D1
    description: "`python -m llm4pol.evaluate --request <json> --root <root>` validates the request against `eval-request.json`, answers every (candidate, property) pair through the `Backend` contract implemented by `TableBackend`, prints a response that validates against `eval-response.json`; exit 0 on success, 2 on a request-schema failure (malformed id, duplicate properties)"
    requirement: EVAL-01
    verification:
      - kind: integration
        ref: "tests/test_evaluate_cli.py#test_tracer_request_json_to_response_json_on_the_synthetic_root"
        status: pass
      - kind: unit
        ref: "tests/test_evaluate_cli.py#test_cli_exit_2_on_a_request_schema_failure"
        status: pass
      - kind: other
        ref: "PYTHONPATH=src python -m llm4pol.evaluate --request protocol/examples/eval-request.example.json --root <synthetic root> -> exit 0, statuses ok, ok, ok, missing, missing, ok, missing, unsupported, ok, cost {evals 3, cpu_hours 0.0}, JSON-equal to the committed response example"
        status: pass
    human_judgment: false
  - id: D2
    description: "Both schemas are valid Draft 2020-12 documents; the committed examples validate, carry synthetic ids only, and the response example equals the evaluator's output; ten response-shape and six request negative cases are rejected with the validator's message; the gate's schema-inventory step prints `llm4polcheck inventory: 3 entries, 3 instances processed`"
    requirement: EVAL-01
    verification:
      - kind: unit
        ref: "tests/test_evaluate_contract.py#test_both_schemas_are_valid_draft_2020_12"
        status: pass
      - kind: unit
        ref: "tests/test_evaluate_contract.py#test_committed_examples_validate_against_their_schemas"
        status: pass
      - kind: unit
        ref: "tests/test_evaluate_contract.py#test_committed_response_example_equals_evaluator_output_on_the_synthetic_root"
        status: pass
      - kind: unit
        ref: "tests/test_evaluate_contract.py#test_response_schema_rejects_each_status_shape_violation"
        status: pass
      - kind: unit
        ref: "tests/test_evaluate_contract.py#test_request_schema_rejects_dup_props_empty_batch_1001_batch_bool_iteration_and_malformed_id"
        status: pass
      - kind: unit
        ref: "tests/test_check_inventory.py#test_repository_inventory_validates"
        status: pass
      - kind: other
        ref: "pixi run --manifest-path env/pixi.toml check -> llm4polcheck inventory: 3 entries, 3 instances processed; SUMMARY: 7/7 steps passed"
        status: pass
    human_judgment: false
  - id: D3
    description: "Each of `ok` (n >= 2 with spread, n 1 with null spread), `missing/value_absent` (exactly where `_n == 0`), `missing/candidate_unknown` and `unsupported` (unregistered key and the barred key, even on an unknown candidate, backend never consulted) has a passing test; `unsupported` and `missing` cost `Cost(0, 0.0)`; no population filter is applied"
    requirement: EVAL-02
    verification:
      - kind: unit
        ref: "tests/test_evaluate_table.py#test_ok_with_spread_when_n_ge_2"
        status: pass
      - kind: unit
        ref: "tests/test_evaluate_table.py#test_ok_with_null_spread_when_n_is_1"
        status: pass
      - kind: unit
        ref: "tests/test_evaluate_table.py#test_missing_value_absent_when_median_is_null"
        status: pass
      - kind: unit
        ref: "tests/test_evaluate_table.py#test_missing_candidate_unknown_for_a_well_formed_absent_id"
        status: pass
      - kind: unit
        ref: "tests/test_evaluate_table.py#test_unsupported_for_an_unregistered_key_and_the_barred_key_even_on_an_unknown_candidate"
        status: pass
      - kind: unit
        ref: "tests/test_evaluate_table.py#test_unsupported_and_missing_consume_no_evals"
        status: pass
      - kind: unit
        ref: "tests/test_evaluate_table.py#test_no_population_filter_is_applied"
        status: pass
    human_judgment: false
  - id: D4
    description: "Every result carries `backend` `table`, `source` = `PropertyTable.load().snapshot` (`polyomics:general_polymers@041e5834`), `provenance_tier` `md_simulated`, `cached` false, the two-field `cost`, and `unit` / `n_replicates` / `spread` equal to the registry unit and the fixture parquet's `_n` / `_std` for every candidate x key"
    requirement: EVAL-03
    verification:
      - kind: unit
        ref: "tests/test_evaluate_table.py#test_every_result_carries_backend_source_and_provenance_tier"
        status: pass
      - kind: unit
        ref: "tests/test_evaluate_table.py#test_unit_n_replicates_and_spread_come_from_the_registry_and_the_candidate_table"
        status: pass
      - kind: other
        ref: "grep -rnE \"= *[\\\"']polyomics:|= *[\\\"']W/\\(m\" src/llm4pol/evaluate/ | wc -l -> 0; grep for a filters import -> 0; grep for property-registry_v1 under evaluate -> 0"
        status: pass
    human_judgment: false
  - id: D5
    description: "A 100-entry synthetic batch with three properties each returns exactly 300 results whose (candidate_id, property) sequence equals the flattened request, `cost.evals` 9 (nine distinct synthetic candidates, duplicates charged 0), schema-valid, and the response cost is the sum of the result costs"
    requirement: EVAL-05
    verification:
      - kind: unit
        ref: "tests/test_evaluate_table.py#test_batch_of_100_synthetic_entries_returns_300_results_in_request_order"
        status: pass
      - kind: unit
        ref: "tests/test_evaluate_table.py#test_response_cost_is_the_sum_of_result_costs"
        status: pass
    human_judgment: false
  - id: D6
    description: "Dataclasses round-trip through JSON (`EvalResponse.from_json(r.to_json()) == r`), `from_json` raises `ValueError` on a wrong-typed field (`cached: \"yes\"`, `n_replicates: true`) and on an unknown status, `to_json` of an `ok` result has no `reason` key, every contract dataclass is frozen"
    requirement: EVAL-01
    verification:
      - kind: unit
        ref: "tests/test_evaluate_contract.py#test_dataclasses_round_trip_through_json"
        status: pass
    human_judgment: false

# Metrics
duration: 16min
completed: 2026-09-22
status: complete
---

# Phase 3 Plan 01: Evaluator tracer (contract, schemas, TableBackend, Evaluator, CLI) Summary

**One schema-validated request now travels `parse_request` -> `Evaluator` -> `TableBackend` over the candidate parquet -> schema-valid response JSON on stdout, with `ok` / `missing` (both reasons) / `unsupported` in request order, per-candidate charging and provenance on every result; the M2 request/response schemas are frozen with committed examples validated inside the gate.**

## Performance

- **Duration:** 16 min
- **Started:** 2026-09-21T21:26:50Z
- **Completed:** 2026-09-21T21:43:00Z (UTC; 2026-09-22 local)
- **Tasks:** 3
- **Files modified:** 19 (14 created, 5 modified)

## Accomplishments

- `python -m llm4pol.evaluate --request protocol/examples/eval-request.example.json --root <synthetic root>` exits 0 and prints nine results with statuses `ok, ok, ok, missing, missing, ok, missing, unsupported, ok`, per-result `evals` `1, 0, 0, 0, 0, 1, 0, 0, 1`, response `cost {"evals": 3, "cpu_hours": 0.0}`; the output is JSON-equal (and LF-text-equal) to the committed `eval-response.example.json`. A malformed `candidate_id` (`ZZZZ`) and duplicate properties exit 2 with `ERROR:` on stderr (R-3, F-29).
- `protocol/schemas/eval-request.json` and `eval-response.json` are valid Draft 2020-12 documents (RESEARCH Code Example 1; per-status conditional null-ness, `reason` enum on `missing`, `cost.evals` `const 0` on non-ok / cached, `provenance_tier` `["md_simulated"]`), and the gate's `schema-inventory` step prints `llm4polcheck inventory: 3 entries, 3 instances processed` (charter section 13 M2 (5)).
- Charter section 13 M2 (1) for `ok` / `unsupported` / `missing`, (3) and (4) are reproducible by command on the synthetic table: eleven named tests in `tests/test_evaluate_table.py`, all green on their first run (the tracer needed no fix).
- The gate is green: `SUMMARY: 7/7 steps passed`, mypy strict `Success: no issues found in 22 source files`, `Contracts: 1 kept, 0 broken.`, **150 tests** (116 baseline + 3 + 20 + 11; the inventory test updated in place).

## Task Commits

Each task was committed atomically (RED then GREEN for the TDD tasks):

1. **Task 1: tracer** — `6bfa5c5` (test, RED) -> `1a06127` (feat, GREEN)
2. **Task 2: examples, inventory, negative cases, round trip, protocol index** — `db50d35` (test, RED) -> `6eb02ad` (feat, GREEN)
3. **Task 3: status taxonomy, provenance, no-population-filter, 100-batch order** — `c0b06a7` (test; green on first run, no `fix(03-01)` commit needed)

**Plan metadata:** see the final `docs(03-01): complete …` commit.

**RED evidence.** Task 1: collection error `ModuleNotFoundError: No module named 'llm4pol.evaluate'` (exit 2), by the plan's design as plan 02-01 recorded; `gsd_run check tdd-red-evidence` would classify that INVALID_RED under #3770 — the plan is `type: execute`, `tdd_mode: false`, so the plan-level gate does not apply; recorded, not hidden. Task 2: `3 failed, 24 passed` (both example files absent — `FileNotFoundError` — and the inventory still printing `1 entries, 1 instances`). Task 3: the plan itself expected most tests green immediately; all eleven were.

## Files Created/Modified

- `src/llm4pol/evaluate/contract.py` (351 lines) — the contract dataclasses, `Backend` Protocol, schema paths, cached validators, `parse_request`, `_wrong_type` boundary readers.
- `src/llm4pol/evaluate/registry.py` — `PropertyTable` over `load_registry()`.
- `src/llm4pol/evaluate/backends/table.py` — `TableBackend`, `SnapshotMismatch`; `backends/__init__.py` docstring only.
- `src/llm4pol/evaluate/evaluator.py` — `Evaluator` with the decision order and per-candidate charging (docstring states the D-04 / R-2 reading).
- `src/llm4pol/evaluate/__main__.py` — argparse `--request` / `--root`, UTF-8 streams, exit 0 / 2; `__init__.py` re-exports the contract, `Evaluator`, `PropertyTable` and imports no backend (F-49).
- `protocol/schemas/eval-request.json`, `eval-response.json`; `protocol/examples/eval-request.example.json`, `eval-response.example.json` (generated by a one-off scratchpad script from `conftest.SYNTHETIC_ROWS`, not committed); `protocol/README.md` (`examples/` row, `## Current contents`, the A-5 sentence).
- `pyproject.toml` — two `[tool.llm4polcheck]` entries and the comment line; `[tool.ruff.lint.isort] known-first-party`.
- `env/pixi.toml` — `evaluate` task (no dependency change; lock untouched).
- `tests/conftest.py` — `make_synthetic_root`, `synthetic_candidates`, `real_candidates`, `SYNTHETIC_EXAMPLE_REQUEST`, `UNKNOWN_CANDIDATE_ID`; `tests/test_check_inventory.py` — `3 entries, 3 instances`.
- `tests/test_evaluate_cli.py`, `tests/test_evaluate_contract.py`, `tests/test_evaluate_table.py`.

## Decisions Made

- **`ValueError` at the boundary, TRY004 answered structurally.** Ruff 0.16 flags `raise ValueError` inside `isinstance` branches; the contract (and the 03-02 cache replay) needs one exception class for every malformed payload, so the seven raises became one `_wrong_type` helper with the rationale in its docstring — no `noqa`.
- **`known-first-party = ["llm4pol"]`** in the RED commit: ruff's isort classifies by disk lookup, so a test importing a submodule that GREEN creates was re-sorted across the two commits (02-01 worked around it per-file). Declaring the package fixes the cause.
- **`__init__.py` docstring reworded** so no line starts with `from` — the plan's grep counts lines, and the sentence "backends are imported / from `llm4pol.evaluate.backends.<name>`" had tripped it (printed 1, now 0).
- **Commits on `main`** under the orchestrator's sequential instruction with `branching_strategy: none`, as every prior plan; the executor's protected-branch probe answers true for `main` and no override key exists in config — flagged for the owner, not acted on.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Ruff re-sorted the not-yet-existing `llm4pol.evaluate` import as third-party**
- **Found during:** Task 1 STEP 1 (RED) — `I001` on `tests/test_evaluate_cli.py`; `ruff check --fix` moved the import into the third-party block, which would have flipped back after GREEN
- **Fix:** `[tool.ruff.lint.isort] known-first-party = ["llm4pol"]` in `pyproject.toml` with a comment naming the cause; the plan's import order is now stable in both states
- **Files modified:** `pyproject.toml`
- **Verification:** `ruff check` and `ruff format --check` clean before the RED commit and in the GREEN gate
- **Committed in:** `6bfa5c5`

**2. [Rule 3 - Blocking] Ruff TRY004 on the seven `raise ValueError` wrong-type rejections**
- **Found during:** Task 1 STEP 6 (gate: `FAIL ruff check`, 7 x TRY004 in `contract.py`)
- **Fix:** one `_wrong_type(key, expected, value) -> ValueError` helper; the raises use it; the contract semantics (`ValueError`, Test 6 of Task 2) are unchanged
- **Files modified:** `src/llm4pol/evaluate/contract.py`
- **Verification:** gate `PASS ruff check`; `test_dataclasses_round_trip_through_json` pins `ValueError` on `cached: "yes"`, `n_replicates: true` and an unknown status
- **Committed in:** `1a06127`

**3. [Rule 1 - Bug] The `__init__.py` docstring tripped the plan's backend-import grep**
- **Found during:** Task 1 verify (`grep -cE "^(from|import) .*backends" src/llm4pol/evaluate/__init__.py` printed 1)
- **Fix:** the sentence reworded so no docstring line begins with `from`; the module still imports nothing from `backends`
- **Files modified:** `src/llm4pol/evaluate/__init__.py`
- **Verification:** the grep prints 0
- **Committed in:** `1a06127`

---

**Total deviations:** 3 auto-fixed (2 blocking, 1 bug). **Impact on plan:** none on scope; two are lint-configuration consequences of ruff 0.16's wider default rule set, one a grep-vs-docstring artefact. No test was weakened; no source behaviour changed to satisfy a check.

### Test-authoring corrections before the RED commits (not deviations)

- `tests/test_evaluate_contract.py::_non_ok` passed `value` twice (helper bug, `TypeError` at collection) — fixed before RED.
- jsonschema 4.26 words `minLength` violations as `'' should be non-empty` (not `is too short`); the `empty-run-id` fragment was corrected before RED. The `1001-batch` case uses `is too long`, `bool` iteration `is not of type 'integer'`, `malformed-id` `does not match`.

## Issues Encountered

- The full gate cannot pass on a designed collection-error RED (pytest fails by construction); as in 02-01, RED commits carry the lint / format steps clean and record the RED pytest line, and the 7/7 gate precedes every feat commit.
- `pytest -v` with the project's `addopts = "-q"` prints no per-test lines; `-o addopts=""` was used to list the PASSED names for the verify blocks.
- A first probe of "byte-identical CLI output" appended a second newline to stdout and printed False; the corrected check confirms JSON equality and LF-text equality (no `\r` in stdout).

## Notes for plan 03-02

- `Evaluator(backend, properties)` is the constructor to extend with `cache`, `meter` and `evals_limit` keyword arguments; `evaluate` already builds the full result list before summing (Pattern 4's phase 1), so the budget check and the cache commit slot in after the loop.
- `TableBackend._frame` keeps nothing on a failed load (`pq.read_table` or `SnapshotMismatch` raise before `self._table` is assigned), so the next lookup retries by design — the `error` path is retryable without further change. `EvalResult.from_json` raises `ValueError` on any wrong-typed field for the JSONL replay.
- `EvalResult.to_json` drops `reason` when `None`; `from_json` accepts both an absent and a `null` `reason`.

## Known Stubs

None. No placeholder, skipped test, xfail or unimplemented branch was introduced; `backends/radonpy.py`, `cache.py`, `budget.py`, `llm4pol.loop` / `run` / `llm` do not exist (prohibition honoured).

## Threat Flags

None beyond the plan's register. T-03-01 (`maxItems 1000`, `uniqueItems`, `additionalProperties: false`, validation before any lookup), T-03-03 (NaN -> None in the backend; `allow_nan=False` on stdout), T-03-04 (examples generated from `SYNTHETIC_ROWS`; `static_` grep on `protocol/examples/` prints 0; every id a synthetic id or `0123456789abcdef`) and T-03-05 (`parse_status` narrowing; typed `from_json`) landed here; T-03-02 (`SnapshotMismatch`) is implemented and is pinned by a test in 03-02 as the plan assigns. Data policy: `git ls-files data/` lists only the two manifests and the README; no parquet or CSV is tracked.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Ready for 03-02 (cache, budget meter, `error` path, `--cache` / `--evals-limit`) and 03-03 (import-linter contracts, real-file batch, evidence, CI). The owner questions inherited from Phase 2 (which triple the evaluator's *caller* serves; the 303 unknown-tacticity twins) are untouched by this plan: the evaluator applies no population filter (D-03), so the choice remains a Phase 5 caller decision.

## Self-Check: PASSED

All 14 created files exist on disk; commits `6bfa5c5`, `1a06127`, `db50d35`, `6eb02ad`, `c0b06a7` are in `git log`; `git rev-list --count 03190d3..HEAD` = 5 matches `commits: 5`; the final gate printed `SUMMARY: 7/7 steps passed` with 150 tests.

---
*Phase: 03-evaluator-table-backend*
*Completed: 2026-09-22*
