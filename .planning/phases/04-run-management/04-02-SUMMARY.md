---
phase: 04-run-management
plan: 02
subsystem: run-record
tags: [tracer, run-verb, replay-verb, plan-selector, populations, results-csv, run-meta, d-39]

requires:
  - phase: 04-run-management
    provides: "ids, jsonio, config (problem spec, run dir), ledger (header, fsynced appends, strict reader) and the two schemas of plan 04-01"
  - phase: 03-evaluator
    provides: "Evaluator, EvalRequest/EvalResponse, JsonlCache (memory-only), BudgetMeter, TableBackend, PropertyTable"
  - phase: 02-data
    provides: "filters.readme_triple_mask, check_tc_mask, build_candidates, the rows and candidate parquets with their llm4pol.* metadata"
provides:
  - "python -m llm4pol.run run|replay and the pixi task campaign; exit constants 0/2/3/4"
  - "the selector protocol (owned by llm4pol.run) and a complete plan-file selector with protocol/schemas/selection-plan.json"
  - "population capture: run_opened carries check_tc then readme_triple as sorted parallel arrays without ids"
  - "the one campaign code path (open_run, drive) writing one evaluation event per candidate"
  - "the pure reducer and the eleven-column long results.csv, byte-identical from the ledger alone (301 bytes, sha256 bbd59e21...)"
  - "meta.json with protocol/schemas/run-meta.json: fifteen keys, validated before it is written, written once"
affects: [04-03, 04-04, 04-05, 04-06, 04-07, 04-08, 04-09, phase-05, phase-06]

plan_head_before: e5a4b4ade2ec2f1e2feeeb69374215d1a858eb9f
actuals:
  tokens: 20000
  tasks: 1
  commits: 2

tech-stack:
  added: []
  patterns:
    - "one run code path: open_run writes meta and header, drive appends every event through one recorder"
    - "the reducer reads thresholds, direction, operators and populations from the ledger only; the direction and operator vocabularies are dictionaries keyed by the schema tokens"
    - "deferred imports: the run handler imports population and resume, replay imports neither, and a child interpreter proves numpy, pandas, pyarrow stay unloaded"
    - "schema-patterns ending in dollar are matched again with fullmatch in Python where a trailing LF would matter"

key-files:
  created:
    - src/llm4pol/run/__main__.py
    - src/llm4pol/run/selector.py
    - src/llm4pol/run/population.py
    - src/llm4pol/run/resume.py
    - src/llm4pol/run/reduce.py
    - protocol/schemas/selection-plan.json
    - protocol/schemas/run-meta.json
    - tests/test_run_cli.py
  modified:
    - src/llm4pol/run/__init__.py
    - src/llm4pol/run/config.py
    - env/pixi.toml
    - tests/run_support.py

key-decisions:
  - "Owner note 1: the driver enforces the budget in evals only, with limit iterations x candidates_per_beam x beams (charter M4: 10 x 10 x 4 = 400); it does not police candidates_per_beam or beams, and an overspending selection is stopped by the evaluator's meter"
  - "Owner note 2: dirty is any output of git status --porcelain until plan 04-06 narrows it to the paths that define behaviour (Pitfall 9)"
  - "The package root does not export the function reduce: `from llm4pol.run import reduce` must keep returning the submodule"
  - "A BudgetExceeded from the evaluator propagates out of drive and exits 3 with the generic BUDGET line; recording run_closed(budget_exhausted) stays with plan 04-05 (R-9)"

patterns-established:
  - "validate_meta is public so open_run refuses a bad mapping before the run directory exists"
  - "the CLI prints run_id right after open_run, so a run that fails while driving names its directory"

requirements-completed: [RUN-01, RUN-02, RUN-04]

coverage:
  - id: D1
    description: "run then replay through the module entry point: 10-line ledger (LF only, seq 1..9, nine event kinds in order), results.csv 301 bytes sha256 bbd59e21275bb7357f83d679ae67ce339dd30c83a126019e833ccff77941be14, replay reproduces the bytes and leaves the run directory unchanged"
    requirement: RUN-04
    verification:
      - kind: integration
        ref: "tests/test_run_cli.py#test_tracer_run_then_replay_through_the_module_entry_point"
        status: pass
    human_judgment: false
  - id: D2
    description: "meta.json validated against run-meta.json before it is written, written once, exactly fifteen keys, a provider key recorded as a boolean by name membership and never as a value"
    requirement: RUN-01
    verification:
      - kind: unit
        ref: "tests/test_run_cli.py#test_meta_is_validated_written_once_and_holds_no_key_value"
        status: pass
    human_judgment: false
  - id: D3
    description: "run_opened carries check_tc then readme_triple, objective [0.155, 0.18, 0.2, 0.315] on both, constraints as served, no quoted 16-hex token in the line; the header selector equals the plan identity"
    requirement: RUN-02
    verification:
      - kind: integration
        ref: "tests/test_run_cli.py#test_run_opened_carries_both_populations_sorted_and_without_ids"
        status: pass
    human_judgment: false
  - id: D4
    description: "replay loads none of numpy, pandas, pyarrow and names no data root"
    requirement: RUN-04
    verification:
      - kind: integration
        ref: "tests/test_run_cli.py#test_replay_loads_no_dataframe_library"
        status: pass
    human_judgment: false
  - id: D5
    description: "an invalid problem or plan exits 2 with ERROR: input refused on stdout, detail on stderr, and creates no run directory; a malformed or unknown run id is refused before a path is built"
    requirement: RUN-01
    verification:
      - kind: unit
        ref: "tests/test_run_cli.py#test_run_refuses_an_invalid_problem_or_plan_with_exit_2_and_creates_nothing"
        status: pass
      - kind: unit
        ref: "tests/test_run_cli.py#test_replay_refuses_a_malformed_or_unknown_run_id"
        status: pass
    human_judgment: false
  - id: D6
    description: "static prohibitions: ten modules, none over 400 lines, no loop or llm package, reduce imports no dataframe stack and names no property or threshold, the package root imports neither population nor resume, the cache is memory-only"
    verification:
      - kind: unit
        ref: "tests/test_run_cli.py#test_the_static_prohibitions_of_the_plan_hold"
        status: pass
      - kind: other
        ref: "pixi run --manifest-path env/pixi.toml check -> SUMMARY: 7/7 steps passed, Contracts: 5 kept, 0 broken."
        status: pass
    human_judgment: false

duration: 12min
completed: 2026-09-30
status: complete
---

# Phase 4 Plan 02: The Tracer, Problem Spec to results.csv Summary

**`python -m llm4pol.run run` drives a plan-file selector through the real evaluator on the synthetic table, appends one fsynced event per candidate behind populations captured in `run_opened`, writes a schema-valid `meta.json`, and `replay` re-derives the 301-byte `results.csv` from the ledger alone without loading a dataframe library.**

## Performance

- **Duration:** 12 min (07:28Z to 07:40Z)
- **Tasks:** 1 (a tracer task: RED commit, then GREEN commit)
- **Files:** 12 (8 created, 4 modified)
- **Gate:** `SUMMARY: 7/7 steps passed`, `Contracts: 5 kept, 0 broken.`, 225 tests

## Accomplishments

- The shape the M3 freeze needs is proven end to end: header, envelope, nine events in the tracer order, populations in `run_opened`, one `evaluation` event per candidate, the long `results.csv`, the closed `meta.json`.
- The tracer ledger is **5,187 bytes** (10 LF-terminated canonical lines, 0 CR; `meta.json` 1,109 bytes on the fixed-constant run). `evals` 3, `cpu_hours` 0.0, equal by results and by event cost.
- `results.csv` written by `run` and the bytes produced by `replay` are the hand-derived 301 bytes, sha256 `bbd59e21275bb7357f83d679ae67ce339dd30c83a126019e833ccff77941be14`. The plan's hand arithmetic (medians, feasibility, thresholds, `pct_of_population` 50.0) agreed with the code on the first run.
- `meta.json` holds exactly fifteen keys: `schema_version, run_id, created_at, problem, code_git_sha, dirty, prompt_versions, provider, model, seed, snapshot, snapshot_sha256, registry_version, selector, provider_key_configured`.
- Tracer feedback gate (auto mode): the tracer's `<verify>` commands were re-run after the GREEN commit and all passed (4 named tests, `campaign --help`, `Contracts: 5 kept, 0 broken.` once, both schemas pass `check_schema`, no `loop` or `llm` package, ten modules); expansion is not part of this plan.

## Task Commits

1. **Task 1 RED** - `f2f2635` (test): failing run-to-replay tracer; the RED state is a collection error by design (the modules do not exist), as in plan 04-01
2. **Task 1 GREEN** - `3eb7985` (feat): tracer - plan selector, populations, evaluation events, meta.json, reducer, run/replay CLI

**Plan metadata:** recorded by the closing docs commit.

## Decisions Made

- **Owner note 1 (budget):** the driver enforces the budget in `evals` only, limit `iterations * candidates_per_beam * beams` (charter M4: 10 x 10 x 4, "max 400 evals"). It does not police `candidates_per_beam` or `beams`; how many candidates a selector puts in a beam is the selector's business, and an overspending selection is stopped by the evaluator's meter.
- **Owner note 2 (`dirty`):** `dirty` is any output of `git status --porcelain` in this plan; plan 04-06 narrows it to the paths that define behaviour (Pitfall 9). It is `true` on almost every checkout today.
- The plan selector's identity is `plan:sha256:` plus the sha256 of `canonical_bytes` of the plan payload (so it includes the trailing LF of the canonical form, as the plan states); two plans differing in one candidate have different identities.
- The direction and operator vocabularies live in small dictionaries in `reduce.py` keyed by the schema tokens (`max`, `min`, `<=`, `>=`); the value compared against always comes from the ledger header.
- `CodeIdentityError` (git cannot name the code) exits 2, the nearest of the four fixed exit codes.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Package root exported the function `reduce`, shadowing the submodule**
- **Found during:** Task 1 GREEN, first test run
- **Issue:** `from llm4pol.run.reduce import reduce` in `__init__` made `from llm4pol.run import reduce` return the function, so `reduce.ReduceError` failed with `'function' object has no attribute 'ReduceError'`.
- **Fix:** the root re-exports `COLUMNS`, `RESULTS_NAME`, `Reduced`, `ReduceError`, `Row`, `render_csv` and not the function; it is reached as `llm4pol.run.reduce.reduce`. The `__init__` docstring says why.
- **Files modified:** `src/llm4pol/run/__init__.py`
- **Committed in:** `3eb7985`

**2. [Rule 1 - Bug] mypy refused `except (*_INPUT_ERRORS, _Refused)`**
- **Found during:** the first full gate run (6/7, `FAIL mypy`)
- **Fix:** `_Refused` is defined before the tuple and belongs to it; the handler is `except _INPUT_ERRORS`.
- **Files modified:** `src/llm4pol/run/__main__.py`
- **Committed in:** `3eb7985`

**3. [Rule 2 - Missing critical functionality] Beam names and candidate ids matched again with `fullmatch`**
- **Found during:** Task 1 (`selector.py`)
- **Issue:** the schema patterns end in `$`, which Python's `re.search` lets match before a final LF, so `full\n` would pass the schema (the same note as the run id in plan 04-01).
- **Fix:** `PlanSelector` checks both patterns with `fullmatch` after the schema; the test covers `ABC`, `full\n` and the empty name.
- **Files modified:** `src/llm4pol/run/selector.py`, `tests/test_run_cli.py`
- **Committed in:** `3eb7985`

**4. [Rule 2 - Missing critical functionality] Names and checks beyond the interface table**
- `config.validate_meta` and `config.MetaError` (public) so `open_run` refuses a mapping the schema refuses before the run directory exists, and `write_meta` validates through the same function; `population.candidate_metadata` (snapshot and source sha256 from the candidate parquet, used by `open_run` before anything is created); `reduce.ReduceError` (selections in a ledger without a `run_opened` population); `resume.DriveError` (a ledger that already holds events, or a selector whose identity is not the header's).
- **Committed in:** `3eb7985`

**5. Behaviour the plan left open**
- `run` prints `run_id:` right after `open_run`, before driving, so a run that fails while driving names its directory; every refusal that occurs before `open_run` returns leaves stdout as exactly `ERROR: input refused`.
- A `BudgetExceeded` from the evaluator exits 3 with stdout `BUDGET: evaluation budget exceeded` and leaves a valid unclosed ledger prefix (a test pins this). Recording `run_closed(budget_exhausted)` and resuming are plan 04-05 (R-9); nothing here pretends to do them.
- `replay --out` is a directory (`<out>/results.csv`); it is refused when it is the run directory itself, the copy is written before the comparison, and a differing recorded `results.csv` returns 4 with `ERROR: ledger integrity check failed`.

**6. Extra tests beyond the five of the behavior list**
`test_the_fixture_ids_are_the_candidates_of_the_synthetic_table` (pins the six ids), `test_replay_refuses_a_malformed_or_unknown_run_id` (T-04-08), `test_replay_returns_4_when_results_csv_holds_other_bytes`, `test_a_request_beyond_the_evals_limit_exits_3_and_leaves_a_valid_prefix`, `test_reduce_is_a_pure_function_of_the_ledger`, `test_plan_selector_refuses_a_plan_that_its_schema_or_the_budget_refuses`, `test_the_new_schemas_are_valid_and_the_meta_problem_is_the_problem_spec_body`, `test_the_static_prohibitions_of_the_plan_hold`.

---

**Total deviations:** 2 auto-fixed bugs (Rule 1), 2 additive hardening items (Rule 2), plus notes on open behaviour and extra tests.
**Impact on plan:** additive inside the plan's own files; no file outside `files_modified`; the two Rule 1 items were found and fixed before the GREEN commit.

## TDD Gate Compliance

`test(04-02)` (`f2f2635`) precedes `feat(04-02)` (`3eb7985`). The RED state is a collection error by the plan's design (`llm4pol.run.__main__`, `selector`, `population`, `resume`, `reduce` did not exist), not an assertion failure; `check tdd-red-evidence` would classify it INVALID_RED, as recorded for plans 02-01 and 04-01. The plan sets `type: execute`, so the TDD mode gate was not active. No refactor commit was needed.

## Issues Encountered

None beyond the two gate findings above. No package was installed and the lock file is untouched.

## Known Stubs

None. The scan of `src/llm4pol/run/`, `tests/test_run_cli.py` and `tests/run_support.py` found no TODO, FIXME, placeholder or skipped test. The paths this plan leaves to later plans (resume, refusals on a recorded prefix, the redaction rule, `usage.json`, `run_summary.json`) are absent, not stubbed.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: subprocess | src/llm4pol/run/config.py | `code_identity` runs `git rev-parse HEAD` and `git status --porcelain` with a fixed argument list, no shell, in the code checkout; a failure is `CodeIdentityError`. It reads no environment value. |

The threats T-04-07..T-04-13 of the plan's register are mitigated as planned (strict plan reader and closed plan schema, `require_run_id` before a path is joined, key presence by name membership, `write_meta` validating before it opens the file, population arrays only in `run_opened` and without ids, membership from the masks and values as served, reduce reading everything from the header).

## Next Phase Readiness

Plan 04-03 is independent of this plan. Plans 04-05..04-08 extend the shape proven here. Notes for them: `drive` starts from a header-only ledger and refuses anything else (`DriveError`), so `resume` belongs in `resume.py` beside it; `reduce.write_outputs` opens `results.csv` exclusively, so a resumed run must write it once at the close; `ids.utc_now()` drops microseconds, so `ts` and run id agree to the second; the example instances for `run-meta.json` and `selection-plan.json` and their inventory entries arrive in plan 04-04.

## Self-Check: PASSED

- All eight created files exist on disk (`__main__.py`, `selector.py`, `population.py`, `resume.py`, `reduce.py`, `selection-plan.json`, `run-meta.json`, `test_run_cli.py`); the two commits `f2f2635` and `3eb7985` are in `git log`, newest first with the subjects the plan names.
- `git rev-list --count e5a4b4a..HEAD` is 2 (the measured `commits`).
- Plan verification re-run: the 4 named tests pass, `campaign --help` lists `run` and `replay`, `lint-imports` prints `Contracts: 5 kept, 0 broken.` once, both schemas pass `check_schema`, `ls src/llm4pol | grep -cE "^(loop|llm)$"` prints 0, `src/llm4pol/run/` holds ten modules (largest 349 lines).
- Full gate at the final feature commit: `SUMMARY: 7/7 steps passed`.
