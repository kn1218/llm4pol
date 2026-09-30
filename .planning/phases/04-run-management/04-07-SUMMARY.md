---
phase: 04-run-management
plan: 07
subsystem: run-record
tags: [results-csv, column-definitions, usage-json, two-currencies, a-3, d-39, adr-0008, m3-exit-3]

requires:
  - phase: 04-run-management
    provides: "reducer, populations, run/replay verbs (04-02); committed run-record examples and the inventory of 7 entries (04-04); reference campaign with 453-byte results.csv and byte-identical resume (04-05); extended fixture and populations (04-06)"
provides:
  - "reduce.usage_of, render_usage, USAGE_NAME: usage.json summed from the recorded result costs, evals as an integer and cpu_hours by math.fsum, never combined; tokens 0 and usd 0.0 until Phase 6"
  - "protocol/schemas/run-usage.json (Draft 2020-12, closed, five required keys) and protocol/examples/run-usage.example.json (89 bytes, the reference campaign's usage.json)"
  - "reduce.write_outputs settles results.csv and usage.json together: both rendered and the usage mapping schema-checked before a file is opened; a present file must equal its rendering (checked for both before either is written)"
  - "python -m llm4pol.run usage --run <id>: prints the ledger sums, exit 4 when a usage.json differs; imports neither population nor resume, compares no code version"
  - "every column of results.csv proven by ADR-0008 definition on hand-derived tables: the reference campaign, the same 17 events under three other headers, the integer ceiling at m = 10, 11, 100, 101, ties, missing and null values"
affects: [04-08, 04-09, phase-05, phase-06]

plan_head_before: 4180b4251b0ee9e879b7b31c9ce3a71edd5cbaa0
actuals:
  tokens: 12500
  tasks: 1
  commits: 2

tech-stack:
  added: []
  patterns:
    - "a metric test that swaps the header, not the events: the same recorded event lines under a header of another problem give the hand-derived rows of the other problem, so no threshold or direction can be a literal"
    - "the schema is applied to the mapping before any output file is opened, and the compare-what-is-present pass runs for every output before the write-what-is-absent pass"
    - "an AST guard in the test suite: no arithmetic, comparison or boolean expression of reduce.py mentions two of evals, cpu_hours, tokens, usd"

key-files:
  created:
    - protocol/schemas/run-usage.json
    - protocol/examples/run-usage.example.json
    - tests/test_run_reduce.py
  modified:
    - src/llm4pol/run/reduce.py
    - src/llm4pol/run/__main__.py
    - src/llm4pol/run/__init__.py
    - pyproject.toml
    - docs/governance/INVARIANTS.md
    - experiments/README.md
    - tests/run_support.py
    - tests/test_run_cli.py
    - tests/test_check_inventory.py

key-decisions:
  - "An event cost is compared with the sum of its result costs exactly for evals and to a relative 1e-12 for cpu_hours: the evaluator adds the hours as a running float sum and usage_of uses fsum, so a bit-for-bit comparison could refuse an honest ledger once a physics backend records non-zero hours"
  - "On a usage.json that differs from the ledger sums the verb prints only the generic integrity line (stdout) and exits 4, so stdout is valid JSON exactly when the exit code is 0"
  - "render_csv refuses a non-finite float with ReduceError instead of writing nan or inf (RESEARCH F-27); the reducer cannot produce one from a schema-valid ledger, so this closes a hole rather than changing a byte"

patterns-established:
  - "run_support builders that import nothing of llm4pol.run: canonical_line, problem_variant, ledger_under, population_payload, feasible_population, hand_ledger"

requirements-completed: [RUN-04, RUN-05]

coverage:
  - id: D1
    description: "the reference campaign reduces to the eight hand-derived rows, 453 bytes, sha256 0e31cfc3...; the same 17 events under the headers eps <= 2.4 / Tg >= 250.0, direction min, and eps <= 1.0 / Tg >= 400.0 give the rows of the plan table on both populations (no feasible member: empty hit cells, an empty beam: empty ratio cells)"
    requirement: RUN-04
    verification:
      - kind: unit
        ref: "tests/test_run_reduce.py#test_reference_rows_match_the_hand_derivation"
        status: pass
      - kind: unit
        ref: "tests/test_run_reduce.py#test_thresholds_direction_and_constraints_come_from_the_header"
        status: pass
    human_judgment: false
  - id: D2
    description: "top indices are (m + 9) // 10 and (m + 99) // 100 in integer arithmetic (m = 10, 11, 100, 101 give hit counts 1/1, 2/1, 3/1, 3/2); a tie is not worse under max and min; a missing objective adds nothing to n_ok though its event is charged 1; a missing constraint is not feasible; a selected candidate with no evaluation event is neither; a null member is out of n_population and the percentile and a null constraint makes a member infeasible"
    requirement: RUN-04
    verification:
      - kind: unit
        ref: "tests/test_run_reduce.py#test_top_indices_use_integer_ceiling"
        status: pass
      - kind: unit
        ref: "tests/test_run_reduce.py#test_ties_are_not_worse"
        status: pass
      - kind: unit
        ref: "tests/test_run_reduce.py#test_missing_values_are_neither_ok_nor_feasible"
        status: pass
      - kind: unit
        ref: "tests/test_run_reduce.py#test_null_population_values"
        status: pass
    human_judgment: false
  - id: D3
    description: "render_csv is LF only, no BOM, empty field for no value, floats as repr (1e-07, 0.30000000000000004, 75.0), the header equals COLUMNS, and a non-finite number is refused"
    requirement: RUN-04
    verification:
      - kind: unit
        ref: "tests/test_run_reduce.py#test_render_csv_bytes"
        status: pass
    human_judgment: false
  - id: D4
    description: "usage_of returns the five keys 1, 5, 0.0, 0, 0.0 on the reference run; evals equals the sum over results and over event costs; ten events of 0.1 hours give exactly 1.0 while evals stays the integer 10; usage.json is the 89 pinned bytes, sha256 bb11fcba...; an event cost that is not the sum of its results raises LedgerIntegrityError; no expression of reduce.py combines two currencies"
    requirement: RUN-05
    verification:
      - kind: unit
        ref: "tests/test_run_reduce.py#test_usage_equals_the_ledger_sums_in_two_currencies"
        status: pass
      - kind: unit
        ref: "tests/test_run_reduce.py#test_usage_refuses_an_event_cost_that_is_not_the_sum_of_its_results"
        status: pass
      - kind: unit
        ref: "tests/test_run_reduce.py#test_the_reducer_never_combines_the_currencies"
        status: pass
    human_judgment: false
  - id: D5
    description: "run-usage.json is closed and pins names and types: a fifth currency key, a missing cpu_hours, evals as a float or a bool, a negative tokens, usd or cpu_hours, tokens as a float, schema_version 2 and one number for both currencies are all refused; the reference usage.json and the committed example validate; write_outputs raises before a file exists when the mapping is refused; a present usage.json is never overwritten"
    requirement: RUN-05
    verification:
      - kind: unit
        ref: "tests/test_run_reduce.py#test_usage_schema_pins_names_and_types"
        status: pass
      - kind: unit
        ref: "tests/test_run_reduce.py#test_usage_is_written_beside_the_results_and_never_overwritten"
        status: pass
    human_judgment: false
  - id: D6
    description: "the usage verb prints the pretty rendering and returns 0; returns 4 with the integrity line on a usage.json with another evals and changes nothing; on an open run (cut after event 7) prints evals 3 and writes no file; the committed example equals the reference usage.json; the inventory reads 8 entries, 15 instances processed"
    requirement: RUN-05
    verification:
      - kind: integration
        ref: "tests/test_run_reduce.py#test_usage_verb_prints_the_sums_and_compares_the_file"
        status: pass
      - kind: unit
        ref: "tests/test_run_reduce.py#test_committed_usage_example_is_the_reference_usage"
        status: pass
      - kind: unit
        ref: "tests/test_check_inventory.py#test_repository_inventory_validates"
        status: pass
      - kind: other
        ref: "pixi run --manifest-path env/pixi.toml check -> SUMMARY: 7/7 steps passed, 373 tests, llm4polcheck inventory: 8 entries, 15 instances processed"
        status: pass
    human_judgment: false

duration: 12min
completed: 2026-09-30
status: complete
---

# Phase 4 Plan 07: Column Definitions Proven By Hand, And usage.json In Two Currencies That Never Meet Summary

**Every column of `results.csv` is checked against its ADR-0008 definition on tables derived by hand (the reference campaign, the same 17 events under three other headers, the integer ceiling at four population sizes), and `usage.json` sums `evals` (integer) and `cpu_hours` (`math.fsum`) apart, validates against a closed `run-usage.json` before it is written, and is the 89 pinned bytes on the reference campaign.**

## Performance

- **Duration:** 12 min (about 08:34Z to 08:46Z)
- **Tasks:** 1 (RED then GREEN)
- **Files:** 3 created, 9 modified
- **Gate:** `SUMMARY: 7/7 steps passed`, 373 tests, `llm4polcheck inventory: 8 entries, 15 instances processed`, no `FAIL` or `HIT` line, on the tree of the GREEN commit

## Accomplishments

- **The tracer definitions were right.** Tests 1 to 6 (rows, three headers, integer ceiling, ties, missing values, null population values) passed on the first run against the code of plans 04-02 and 04-05, so the hand tables and the code agree; the only change to a definition is that `render_csv` now refuses a non-finite number. The tests stay as guards: reducing the same events under `eps <= 2.4 / Tg >= 250.0`, direction `min` and `eps <= 1.0 / Tg >= 400.0` gives the plan's row sets, which no literal could.
- **Two currencies.** `usage_of` walks the `evaluation` events once. On the reference campaign it returns `schema_version 1, evals 5, cpu_hours 0.0, tokens 0, usd 0.0`; `evals` equals the sum over results and over event costs (charter section 13 M3 exit criterion (3)); ten events of 0.1 hours sum to exactly `1.0` by `fsum` while `evals` stays the integer 10.
- **`usage.json` is 89 bytes, sha256 `bb11fcba3db73cf823941bb629dd5827a614f908f7a40ba2f9284e0817787caa`,** typed from the plan's derivation into `run_support.REFERENCE_USAGE_JSON` before any code existed, and the writer reproduced it; the committed `protocol/examples/run-usage.example.json` is those bytes.
- **The verb `usage`** prints the pretty rendering, returns 4 on a differing file and leaves it as found, and on an open run prints the recorded sums (3 evals after event 7) and writes nothing.

## Record for the owner

| Item | Value |
|---|---|
| Commit, RED | `43d6af3` test(04-07): add the column definitions on hand-derived tables and failing two-currency tests |
| Commit, GREEN | `53779f2` feat(04-07): column definitions of ADR-0008 proven on hand-derived tables; usage.json with its schema and the usage verb sum two currencies apart |
| `usage.json` of the reference campaign | 89 bytes, sha256 `bb11fcba3db73cf823941bb629dd5827a614f908f7a40ba2f9284e0817787caa` |
| `results.csv` of the reference campaign | 453 bytes, sha256 `0e31cfc380aaaf9f86a68b5e83986ad34ce57cd3c4704634ea2de840f0512fc6` (unchanged) |
| Inventory line | `llm4polcheck inventory: 8 entries, 15 instances processed` |
| Gate | `SUMMARY: 7/7 steps passed`, 373 tests |

**Owner notes of the objective, as executed.**
1. D-39 adds `schema_version` to `usage.json`; CONTEXT D-04's "no fifth field" is read as being about currencies. The four currency keys are unchanged, the schema is closed, and a merged or extra currency is refused (`test_usage_schema_pins_names_and_types` tries a fifth key and one number under a merged key).
2. `usage` on an open run prints the sums of what is recorded and returns 0; it writes nothing (asserted on a run cut after event 7).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] The plan's claim that a running sum of ten 0.1 gives 0.9999999999999999 does not hold for the built-in `sum` on Python 3.12+**
- **Found during:** Task 1 GREEN, first run of Test 8
- **Issue:** the test asserted `sum([0.1] * 10) == 0.9999999999999999`; from Python 3.12 the built-in `sum` of floats is compensated and returns `1.0`.
- **Fix:** the test demonstrates the failure of a running sum with an explicit `+=` loop (which does give 0.9999999999999999), while `usage_of` still uses `math.fsum`. No assertion about the code changed.
- **Files modified:** `tests/test_run_reduce.py`
- **Commit:** `53779f2`

**2. [Rule 1 - Bug] Plan Test 5 misstated feasibility for a candidate with a missing objective**
- **Found during:** Task 1 RED, first run
- **Issue:** the plan says a candidate whose objective is `missing` and whose constraints are `ok` adds nothing to `n_ok`; my first expected `feasible_frac` (0.25) treated that candidate as infeasible. ADR-0008 defines feasibility by constraint values only, so it is feasible (its objective is absent, so it cannot be a hit).
- **Fix:** the test expects 0.5 (the missing-objective candidate and the fully ok one), with a comment; `n_ok` is 2 and the hits count only the candidate that has an objective. The code was already right.
- **Files modified:** `tests/test_run_reduce.py`
- **Commit:** `43d6af3`

**3. [Rule 1 - Bug] One 04-02 expectation that this plan changes by design**
- **Found during:** Task 1 GREEN
- **Issue:** `test_reduce_is_a_pure_function_of_the_ledger` expected `write_outputs` to return exactly `{"results.csv": ...}`; the function now settles two files, as the plan's STEP 4 says.
- **Fix:** it asserts the keys are `results.csv` and `usage.json` and that the `results.csv` hash is the pinned tracer hash; the never-rewrite assertions are unchanged.
- **Files modified:** `tests/test_run_cli.py`
- **Commit:** `53779f2`

**4. [Rule 2 - Missing critical functionality] Additions beyond the interface list**
- `reduce.render_usage` (usage rendered and schema-checked in one place, used by `write_outputs` and the verb) and `reduce.USAGE_SCHEMA_PATH`; `render_usage`, `usage_of` and `USAGE_NAME` are re-exported from the package root.
- `write_outputs` compares every present output before it writes any absent one, so a differing `usage.json` cannot leave a freshly written `results.csv` beside it.
- `test_the_reducer_never_combines_the_currencies` (an AST scan for the A-3 prohibition), `test_usage_refuses_an_event_cost_that_is_not_the_sum_of_its_results`, `test_usage_is_written_beside_the_results_and_never_overwritten`, and a non-finite case in Test 7.
- `experiments/README.md` (not in `files_modified`): the sentence that said the `usage.json` schema arrives in a later plan now says `run-usage.json` exists, as the objective of this run asked.
- **Commit:** `53779f2`

### Notes, no change

- **The RED commit does not pass the gate**, as in plans 04-05 and 04-06: `43d6af3` holds seven failing tests by design. The GREEN commit was gated at 7/7 before it was made.
- **`evals` as a float in the schema test uses 5.5**, not 5.0: JSON Schema counts a number with a zero fraction as an integer, so 5.0 would validate. `usage_of` only ever produces an `int`, and the test asserts its type.
- `ledger.py` is untouched (399 lines); `reduce.py` is 381 lines.

**Total deviations:** 3 auto-fixed (Rule 1), 1 set of additive items (Rule 2). **Impact on plan:** none on scope or on any pinned byte; every byte string of plans 04-02, 04-05 and 04-06 is unchanged.

## TDD Gate Compliance

The task has a `test(04-07)` commit (`43d6af3`) before the `feat(04-07)` commit (`53779f2`). The plan sets `type: execute`, so the TDD mode gate was not active. No refactor commit was needed. At RED, Tests 1 to 6 passed on the existing definitions (kept as guards, as the plan allows) and Tests 7 to 11 failed on the missing behaviour and files.

## Known Stubs

None. The scan of `src/llm4pol/run/reduce.py`, `src/llm4pol/run/__main__.py`, `tests/test_run_reduce.py` and `tests/run_support.py` found no TODO, FIXME, placeholder or skipped test. `tokens` 0 and `usd` 0.0 are the specified values until Phase 6 (the schema description says so), not stubs.

## Threat Flags

None new. Register mitigations in place: T-04-34 (Test 2 reduces the same events under three other headers), T-04-35 (`usage_of` never combines two keys, the closed schema is applied before writing, the AST guard, the A-3 row), T-04-36 (`usage` and `write_outputs` compare with the ledger sums and return 4 or raise on a difference), T-04-37 (no value is the empty field; Tests 1 and 7). T-04-SC: nothing installed.

## Next Phase Readiness

Ready for 04-08 (`run_summary.json`, the full `replay`, the pinned fixture ledger). `write_outputs` now returns two hashes and settles two files; adding a third output there is the same pattern (render, check present, write absent). `usage.json` is written at every close and by `resume` on a closed run that lacks it.

## Self-Check: PASSED

- Created files exist: `protocol/schemas/run-usage.json`, `protocol/examples/run-usage.example.json`, `tests/test_run_reduce.py`; modified files listed above exist.
- Commits `43d6af3` and `53779f2` are in `git log`; `git rev-list --count 4180b42..HEAD` gave 2 (the measured `commits`).
- Plan verification re-run: `tests/test_run_reduce.py` and `tests/test_check_inventory.py` green with no skip; the four named tests pass; the seven parametrised tests pass; `test_run_cli.py`, `test_run_resume.py`, `test_run_population.py` and `test_run_examples.py` green; the example prints `89 bb11fcba3db73cf823941bb629dd5827a614f908f7a40ba2f9284e0817787caa`; `campaign usage --help` lists `--run`; the A-3 row names the usage test (one match); the gate prints the 8/15 inventory line once and `SUMMARY: 7/7 steps passed`.
