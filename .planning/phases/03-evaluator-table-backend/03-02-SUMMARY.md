---
phase: 03-evaluator-table-backend
plan: 02
subsystem: evaluate
tags: [jsonl, cache, budget, dataclasses, frozen, argparse, pytest, tdd, invariants]

# Dependency graph
requires:
  - phase: 03-evaluator-table-backend
    provides: "03-01: `Evaluator(backend, properties)` building the full result list before summing; `EvalResult.to_json` / `from_json` (typed, `ValueError` at the boundary); `TableBackend._frame` keeping nothing on a failed load; `SnapshotMismatch`; the CLI `--request` / `--root` with exit 0 / 2; `conftest.synthetic_candidates`, `SYNTHETIC_EXAMPLE_REQUEST`"
provides:
  - "`llm4pol.evaluate.budget`: frozen `BudgetMeter(evals=0, cpu_hours=0.0)` with `charge(cost) -> BudgetMeter` (a new meter), `remaining(evals_limit)`, `exhausted(evals_limit)` reading `evals` only; `BudgetExceeded(requested, remaining, limit)` with the message `requested N evals, M remaining of limit L`"
  - "`llm4pol.evaluate.cache`: `CacheKey = tuple[str, str, str, str]`, `key_for(candidate_id, property_key, backend)`, `CacheError`, `canonical_line(key, result)` (sorted keys, compact separators, `ensure_ascii=False`, `allow_nan=False`, LF), `JsonlCache(path=None)` with replay on construction through `EvalResult.from_json`, `get`, `put_many` (one flushed append per request, parent `mkdir`), `__len__`, `path`"
  - "`Evaluator(backend, properties, *, cache=None, meter=None, evals_limit=None)` with the two-phase `evaluate`: unsupported -> cache hit (`dataclasses.replace(hit, cached=True, cost=Cost(0, 0.0))`) -> lookup; only `ok` / `missing` queued; budget check before `put_many` and `charge`; public `backend`, `properties`, `cache`, `meter`, `evals_limit`"
  - "`python -m llm4pol.evaluate --request R [--root T] [--cache C] [--evals-limit N]`: exit 0 / 2 (`ERROR:`; unreadable or invalid request, bad registry, unreadable or malformed cache) / 3 (`BUDGET:`; nothing written)"
  - "`docs/governance/INVARIANTS.md` A-3 row (architecture table now holds A-3 and A-7)"
  - "Tests: `tests/test_evaluate_cache_budget.py` (11), `tests/test_evaluate_table.py` (+3 `error` tests), `tests/test_evaluate_cli.py` (+3 tests, one parametrised x5)"
affects: [03-03 (A-1 / A-2 rows are inserted before A-3 in the INVARIANTS architecture table; real-file batch may use --cache), 04-ledger (the durable record the cache defers to; the A-3 ledger-schema guard), 05-loop (BudgetMeter / BudgetExceeded / evals_limit are the 400-eval budget's primitives)]

# Actuals (#2632) — chars/4 over the realized diff (39,856 bytes of added/removed lines), never a harness token count.
actuals:
  tokens: 9964
  tasks: 2
  commits: 4
plan_head_before: fee8a9dadd6e6d80b383a8e372217cf29c32b779

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Two-phase evaluate (RESEARCH Pattern 4): every result is computed and the new ones queued, the budget is checked against `meter.remaining(evals_limit)`, and only then does the cache `put_many` and the meter `charge` -- a refusal leaves no partial state"
    - "Cache policy in the orchestrator, not the cache (Pattern 5): `JsonlCache` stores whatever it is given; the `Evaluator` decides that `error` and `unsupported` never reach it and that a hit is re-labelled on return, so stored records always carry `cached: false`"
    - "Frozen meter replaced, never mutated (Pattern 6, coding-style immutability): `self.meter = self.meter.charge(total)`; `FrozenInstanceError` on assignment is part of the A-3 guard test"
    - "Canonical JSONL line: `json.dumps(record, sort_keys=True, separators=(\",\", \":\"), ensure_ascii=False, allow_nan=False) + \"\\n\"` with `newline=\"\\n\"` on open, LF-only on Windows (F-33); every replayed line re-enters through the same typed `from_json` the contract tests pin, and every defect is one `CacheError(f\"{path}:{lineno}: {message}\")`"
    - "Guard-by-source-grep: the A-3 test reads `inspect.getsource(llm4pol.evaluate.budget)` for `__float__` / `__add__` / `total`, so the module's docstring is written without the combining words"

key-files:
  created:
    - src/llm4pol/evaluate/budget.py
    - src/llm4pol/evaluate/cache.py
    - tests/test_evaluate_cache_budget.py
  modified:
    - src/llm4pol/evaluate/evaluator.py
    - src/llm4pol/evaluate/__init__.py
    - src/llm4pol/evaluate/__main__.py
    - tests/test_evaluate_table.py
    - tests/test_evaluate_cli.py
    - docs/governance/INVARIANTS.md
    - env/pixi.toml

key-decisions:
  - "`Evaluator.backend` / `properties` became plain public attributes (the plan lists all five as public); the `unsupported` decision moved out of `_lookup` into the loop so it precedes the cache probe -- an unregistered key can never build a cache key (prohibition: `unsupported` never reaches the cache)"
  - "The CLI's `--cache` round-trip test asserts every *cacheable* result is `cached: true` on the second run and exactly one (`melting_point`, `unsupported`) stays `false`: the plan's phrase 'every `cached` true' cannot hold literally for a status the same plan forbids from the cache; the reading that honours the prohibition was taken"
  - "The CLI starts from `BudgetMeter()` on every invocation (a per-run limit): no meter persistence exists at M2 -- the Phase 4 ledger is where spend across runs is recorded"
  - "`JsonlCache.put_many` rebuilds the dict (`{**self._records, **dict(new)}`) rather than updating in place -- the immutability rule at the cost of O(n) per request, acceptable at F-48's 1,200-entry scale"
  - "Commits made directly on `main` under the orchestrator's sequential instruction with `branching_strategy: none`, as every prior plan; the protected-branch probe answers true for `main` and no override key exists in config -- recorded, not resolved"

patterns-established:
  - "Test helper convention extended: `_evaluator(root, *, cache=None, meter=None, evals_limit=None)` in `tests/test_evaluate_cache_budget.py`; `_error_evaluator(parquet, cache_path)` in `tests/test_evaluate_table.py` for backends pointed at a chosen parquet; `_run(args, capsys) -> (code, out, err)` in `tests/test_evaluate_cli.py`"
  - "RED commits carry ruff check / format clean and the RED pytest line in the message; the 7/7 gate precedes every feat commit (unchanged from 03-01)"

requirements-completed: [EVAL-02, EVAL-04]

coverage:
  - id: D1
    description: "A repeated request is fully cached with `evals` 0 and the meter unchanged, both in memory and after a fresh `JsonlCache(path)` replays the JSONL of the first request; the cache key includes backend and source"
    requirement: EVAL-04
    verification:
      - kind: unit
        ref: "tests/test_evaluate_cache_budget.py#test_cache_hit_leaves_evals_unchanged_in_memory"
        status: pass
      - kind: unit
        ref: "tests/test_evaluate_cache_budget.py#test_cache_hit_leaves_evals_unchanged_after_jsonl_replay"
        status: pass
      - kind: unit
        ref: "tests/test_evaluate_cache_budget.py#test_cache_key_includes_backend_and_source"
        status: pass
      - kind: unit
        ref: "tests/test_evaluate_cache_budget.py#test_stored_records_keep_cached_false"
        status: pass
      - kind: integration
        ref: "tests/test_evaluate_cli.py#test_cli_cache_round_trip_marks_second_run_cached_with_zero_evals"
        status: pass
      - kind: other
        ref: "python -m llm4pol.evaluate --request protocol/examples/eval-request.example.json --root <synthetic root> --cache c.jsonl twice: run 1 cost {evals 3}, 8 lines; run 2 cost {evals 0}, cached [T,T,T,T,T,T,T,F,T], still 8 lines; 0 CR bytes, ends with LF, no NaN, 3,250 bytes"
        status: pass
    human_judgment: false
  - id: D2
    description: "`evals` is charged once per distinct candidate per request on its first non-cached `ok`: three properties charge 1 (`[1, 0, 0]`), a duplicate entry charges 0, two `ok` candidates charge 2, an all-`missing` candidate charges 0 (and is cached), a new property of a cached candidate charges 1 again"
    requirement: EVAL-04
    verification:
      - kind: unit
        ref: "tests/test_evaluate_cache_budget.py#test_evals_charged_once_per_distinct_candidate_per_request"
        status: pass
      - kind: unit
        ref: "tests/test_evaluate_cache_budget.py#test_all_missing_candidate_charges_zero"
        status: pass
      - kind: unit
        ref: "tests/test_evaluate_cache_budget.py#test_new_property_of_a_cached_candidate_charges_one_eval"
        status: pass
    human_judgment: false
  - id: D3
    description: "A-3 promoted: `BudgetMeter` and `Cost` carry exactly `evals` and `cpu_hours`, the budget module's source contains no combining name, the schema `cost` definition is closed on the two fields, the meter is frozen; the INVARIANTS.md A-3 row names the meter, the schema definition and the test"
    requirement: EVAL-04
    verification:
      - kind: unit
        ref: "tests/test_evaluate_cache_budget.py#test_a3_budget_meter_keeps_evals_and_cpu_hours_as_separate_currencies"
        status: pass
      - kind: other
        ref: "grep -cE '__float__|__add__|total' src/llm4pol/evaluate/budget.py -> 0; sed -n '/^| A-3 /p' docs/governance/INVARIANTS.md | grep -c test_a3_... -> 1"
        status: pass
    human_judgment: false
  - id: D4
    description: "`BudgetExceeded(requested, remaining, limit)` is raised before anything is committed: afterwards the cache is empty, no JSONL file exists and the meter equals `BudgetMeter()`; the CLI exits 3 with `BUDGET:` and no cache file"
    requirement: EVAL-04
    verification:
      - kind: unit
        ref: "tests/test_evaluate_cache_budget.py#test_budget_exceeded_leaves_cache_and_meter_untouched"
        status: pass
      - kind: integration
        ref: "tests/test_evaluate_cli.py#test_cli_exit_3_when_evals_limit_would_be_exceeded_and_nothing_is_committed"
        status: pass
      - kind: other
        ref: "python -m llm4pol.evaluate ... --evals-limit 2 on the example request (3 ok candidates) -> exit 3, stderr `BUDGET: requested 3 evals, 2 remaining of limit 2`"
        status: pass
    human_judgment: false
  - id: D5
    description: "The JSONL is LF-only, one canonical line per stored `ok` / `missing` result, NaN-free with `spread` stored as `null`; a malformed third line raises `CacheError` naming `:3:` and the path; a record with `cached: \"yes\"` is refused on replay"
    requirement: EVAL-04
    verification:
      - kind: unit
        ref: "tests/test_evaluate_cache_budget.py#test_jsonl_lines_are_lf_only_canonical_and_nan_free"
        status: pass
      - kind: unit
        ref: "tests/test_evaluate_cache_budget.py#test_malformed_cache_line_raises_cache_error_with_line_number"
        status: pass
      - kind: other
        ref: "grep -c fsync src/llm4pol/evaluate/cache.py -> 0; grep -c 'allow_nan=False' src/llm4pol/evaluate/cache.py -> 1"
        status: pass
    human_judgment: false
  - id: D6
    description: "The fourth status: an absent parquet answers `error` / `FileNotFoundError` on every backend-reaching result with `evals` 0, nothing cached, meter untouched, schema-valid; the same evaluator answers the tracer statuses once the parquet appears (8 results cached, `evals` 3); a wrong `llm4pol.snapshot` answers `error` / `SnapshotMismatch`"
    requirement: EVAL-02
    verification:
      - kind: unit
        ref: "tests/test_evaluate_table.py#test_error_when_the_parquet_is_absent_consumes_no_evals_and_is_not_cached"
        status: pass
      - kind: unit
        ref: "tests/test_evaluate_table.py#test_error_is_retried_once_the_parquet_appears"
        status: pass
      - kind: unit
        ref: "tests/test_evaluate_table.py#test_error_on_snapshot_mismatch_names_the_exception_class"
        status: pass
    human_judgment: false
  - id: D7
    description: "CLI exit 2 for an absent request, invalid JSON, a schema failure, a directory `--cache` and a cache file with a malformed line (`ERROR:` on stderr, empty stdout); `--help` lists both flags"
    requirement: EVAL-02
    verification:
      - kind: integration
        ref: "tests/test_evaluate_cli.py#test_cli_exit_2_on_missing_request_bad_json_and_schema_failure"
        status: pass
      - kind: other
        ref: "pixi run --manifest-path env/pixi.toml evaluate --help | grep -c -- '--evals-limit\\|--cache' -> 8"
        status: pass
    human_judgment: false

# Metrics
duration: 9min
completed: 2026-09-22
status: complete
---

# Phase 3 Plan 02: JsonlCache, BudgetMeter, two-phase evaluate, the `error` path and the CLI flags Summary

**A cache hit on `(candidate_id, property, backend, source)` now leaves `evals` unchanged in memory and across an append-only JSONL replay, `evals` is charged once per distinct candidate per request, a frozen two-currency `BudgetMeter` refuses over-budget requests with `BudgetExceeded` before anything is committed, `error` from an absent or mismatched parquet is pinned as budget-free, uncached and retryable, and the CLI exposes `--cache` / `--evals-limit` with exit codes 0 / 2 / 3.**

## Performance

- **Duration:** 9 min
- **Started:** 2026-09-21T21:49:03Z
- **Completed:** 2026-09-21T21:57:56Z (UTC; 2026-09-22 local)
- **Tasks:** 2
- **Files modified:** 10 (3 created, 7 modified)

## Accomplishments

- Charter section 13 M2 (2) is reproducible by command: two runs of the example request with the same `--cache` give run 1 `cost {"evals": 3}` and 8 stored lines, run 2 `cost {"evals": 0}` with every cacheable result `cached: true` and the file still 8 lines. The file has 0 CR bytes, ends with LF, contains no `NaN`, and is 3,250 bytes for the eight records (Test 9 in the suite: 5 lines for `7ec8cb49ff317efc` x 3 + `d24805b4ce4c381c` / TC + `81b997b85ccd2069` / TC, each equal to `canonical_line(key, result)`, the n = 1 record storing `"spread": null`).
- Charter section 13 M2 (1) is complete for all four statuses: an absent parquet answers `error` / `FileNotFoundError` on the 8 backend-reaching results of the example request (the `unsupported` one is decided first), `cost {0, 0.0}`, nothing cached, `BudgetMeter()` untouched; the same evaluator answers `ok, ok, ok, missing, missing, ok, missing, unsupported, ok` with `evals` 3 and 8 cached results once the file is copied into place; a parquet re-written with `llm4pol.snapshot = polyomics:general_polymers@deadbeef` answers `error` / `SnapshotMismatch`.
- `BudgetExceeded` message format: `requested {requested} evals, {remaining} remaining of limit {limit}`, e.g. `BUDGET: requested 3 evals, 2 remaining of limit 2` on stderr with exit 3 and no cache file written; `exc.requested`, `exc.remaining`, `exc.limit` are attributes.
- A-3 promoted. The INVARIANTS.md row reads: `| A-3 | The budget keeps `evals` and `cpu_hours` as two separately counted currencies; no combined score exists | `llm4pol.evaluate.budget.BudgetMeter` (exactly the two fields; `charge` returns a new meter; `remaining` / `exhausted` read `evals` only); `protocol/schemas/eval-response.json` `$defs/cost` (exactly `evals` and `cpu_hours`, `additionalProperties: false`); `tests/test_evaluate_cache_budget.py::test_a3_budget_meter_keeps_evals_and_cpu_hours_as_separate_currencies`. The ledger-schema guard the charter names lands at M3 (Phase 4) |`.
- The gate is green: `SUMMARY: 7/7 steps passed`, mypy strict `Success: no issues found in 24 source files`, `Contracts: 1 kept, 0 broken.`, **171 tests** (150 after 03-01 + 11 + 3 + 7; the plan's floor was 152).

## Task Commits

Each task was committed atomically (RED then GREEN):

1. **Task 1: JsonlCache, BudgetMeter, two-phase evaluate, A-3** — `0c934bc` (test, RED: collection `ImportError` on `BudgetExceeded`) -> `4a319c1` (feat, GREEN; 161 tests)
2. **Task 2: `error` status pinned; CLI `--cache` / `--evals-limit`** — `904a355` (test, RED: 4 failed on `unrecognized arguments: --cache`; the three `error` tests passed through the tracer's conversion as the plan anticipated) -> `6b183ca` (feat, GREEN; 171 tests)

**Plan metadata:** see the final `docs(03-02): complete …` commit.

**Tracer defect revealed by Tests 1–3 of Task 2:** none. `TableBackend._frame` keeps nothing on a failed load (03-01's note held) and `_lookup` catches `Exception`, so `FileNotFoundError` from `pq.read_table` and `SnapshotMismatch` both surface as `error` with the class name; no `fix(03-02)` commit was needed.

## Files Created/Modified

- `src/llm4pol/evaluate/budget.py` (new, 53 lines) — `BudgetMeter` (frozen, slots, `evals` / `cpu_hours`, `charge` / `remaining` / `exhausted`), `BudgetExceeded`. The docstring is written without `total`, `__add__` or `__float__` because the A-3 test greps the source.
- `src/llm4pol/evaluate/cache.py` (new, 109 lines) — `CacheKey`, `CacheError`, `key_for`, `canonical_line`, `JsonlCache` (replay on construction, `get`, `put_many` with one flushed append, `__len__`, `path`), `_replay`, `_parse_record`.
- `src/llm4pol/evaluate/evaluator.py` — constructor keyword arguments; the loop decides `unsupported` first, probes the cache, then looks up; `ok` / `missing` queued; budget check, `put_many`, `charge`; class docstring states the charging edges (duplicate entry in one request charged 0 by the set, not a hit; new property of a cached candidate charged again).
- `src/llm4pol/evaluate/__init__.py` — exports `BudgetExceeded`, `BudgetMeter`, `CacheError`, `JsonlCache`; still imports no backend (`grep -cE "^(from|import) .*backends"` prints 0).
- `src/llm4pol/evaluate/__main__.py` — `--cache`, `--evals-limit` (non-negative), `EXIT_OK` / `EXIT_INPUT` / `EXIT_BUDGET`, the docstring exit-code table; replay errors and append errors are exit 2, `BudgetExceeded` exit 3.
- `env/pixi.toml` — the `evaluate` task comment names the flags and exit codes (no dependency change; lock untouched).
- `docs/governance/INVARIANTS.md` — the A-3 row before A-7.
- `tests/test_evaluate_cache_budget.py` (new, 11 tests); `tests/test_evaluate_table.py` (+3, `shutil` / `pyarrow.parquet` imports, `BudgetMeter` / `JsonlCache` / `SYNTHETIC_EXAMPLE_REQUEST`); `tests/test_evaluate_cli.py` (+3 tests, `_run` / `_line_count` helpers, `_TWO_OK` request).

## Decisions Made

- **`unsupported` decided before the cache key exists.** 03-01 answered `unsupported` inside `_lookup`; the two-phase loop now checks `properties.supported(key)` first and `continue`s, so `key_for` is never called for an unregistered key — the prohibition "no `unsupported` key ever reaches the cache" holds by construction, not by filtering.
- **Round-trip test reads "every `cached` true" as "every cacheable result".** The example request contains `melting_point` (`unsupported`), which the same plan forbids from the cache; the test asserts eight `true` and exactly one `false` rather than weaken the prohibition.
- **Per-invocation meter in the CLI.** No meter is persisted at M2; `--evals-limit` bounds one request. Cross-run spend is the Phase 4 ledger's job (the A-3 row says so).
- **Public attributes on `Evaluator`** (`backend`, `properties`, `cache`, `meter`, `evals_limit`) as the plan lists; the 03-01 `backend` property became a plain attribute.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `ruff format --check` failed on `cache.py` after the first GREEN run**
- **Found during:** Task 1 STEP 6 (gate 6/7: `FAIL ruff format --check`)
- **Issue:** two hand-wrapped expressions (`json.dumps(...)` in `canonical_line`, the `if` in `_parse_record`) were not in ruff's canonical layout
- **Fix:** `ruff format` on the package; no logic change
- **Files modified:** `src/llm4pol/evaluate/cache.py`
- **Verification:** gate `PASS ruff format --check`, 7/7
- **Committed in:** `4a319c1`

---

**Total deviations:** 1 auto-fixed (formatting). **Impact on plan:** none. No test was weakened; no source behaviour changed to satisfy a check.

### Test-authoring notes (not deviations)

- The plan's Test 4 lists the same candidate twice in one batch; the request schema has `uniqueItems` on `properties` only, so two entries for `7ec8cb49ff317efc` with different property lists validate, and the second entry's result is charged 0 by the per-request set (not a hit).
- The malformed-cache CLI case first runs the CLI once with `--cache` to produce a valid file, then appends `{not json`; the replay of the next run fails at `:9:` (8 stored lines + 1) and exits 2.

## Issues Encountered

- The full gate cannot pass on a designed collection-error RED; as in 02-01 and 03-01, RED commits carry the lint / format steps clean and record the RED pytest line, and the 7/7 gate precedes every feat commit.
- `mypy` run directly on `tests/test_evaluate_table.py` reports a pre-existing `unused-ignore` / `call-overload` pair on a 03-01 line (`set(result.to_json()["cost"])`); the gate's mypy step checks `src/` (24 files) and is green. Out of this plan's scope; logged here rather than fixed silently.

## Notes for plan 03-03

- The INVARIANTS.md architecture table now has A-3 and A-7; A-1 and A-2 are inserted before A-3 (rows in ID order).
- `llm4pol.evaluate.__init__` imports `budget`, `cache`, `contract`, `evaluator`, `registry` — none of them imports a backend; the import-linter layers contract of 03-03 should see the same graph as 03-01 plus these two leaf modules.
- The CLI's `--cache` can persist a real-file batch's results for the evidence run; the JSONL is a derived artifact (never committed — `experiments/` is git-ignored).

## Known Stubs

None. No placeholder, skipped test, xfail or unimplemented branch was introduced; `backends/radonpy.py`, `llm4pol.loop` / `run` / `llm` and a combined budget score do not exist (prohibitions honoured: `grep -c fsync cache.py` 0, `grep -cE "__float__|__add__|total" budget.py` 0, no `cached=True` is ever written to a stored record).

## Threat Flags

None beyond the plan's register. T-03-07 (typed replay, `CacheError` with path and line, `source` in the key), T-03-08 (`SnapshotMismatch` pinned by test), T-03-09 (`error` never queued; retry test), T-03-11 (`allow_nan=False`; Test 9), T-03-12 (two-phase commit; Test 8) landed here; T-03-10 and T-03-13 accepted as the plan states (`len(cache)` exposed; `--cache` path opened as given, documented in the module docstring). Data policy: `git ls-files data/` is unchanged; no parquet, CSV or cache file is tracked.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Ready for 03-03 (import-linter contracts A-1 / A-2, real-file batch proof, evidence, CI). Phase 5's budget primitives (`BudgetMeter`, `BudgetExceeded`, `evals_limit`) and Phase 4's cache-vs-ledger boundary are in place as the charter describes them.

## Self-Check: PASSED

All 3 created files exist on disk; commits `0c934bc`, `4a319c1`, `904a355`, `6b183ca` are in `git log`; `git rev-list --count fee8a9d..HEAD` = 4 matches `commits: 4`; the final gate printed `SUMMARY: 7/7 steps passed` with 171 tests.

---
*Phase: 03-evaluator-table-backend*
*Completed: 2026-09-22*
