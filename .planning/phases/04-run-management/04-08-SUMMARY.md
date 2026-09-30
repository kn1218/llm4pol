---
phase: 04-run-management
plan: 08
subsystem: run-record
tags: [run-summary, replay, result-sha256, pinned-fixture, schema-inventory, adr-0008, adr-0007, d-39, m3-exit-2]

requires:
  - phase: 04-run-management
    provides: "ledger.read/parse_bytes and the closed ledger schema (04-01, 04-05); reducer, results.csv and usage.json with write_outputs settling two files (04-02, 04-07); byte-identical resume at 18 boundaries (04-05); the reference campaign and its hand-derived bytes (04-05, 04-06)"
provides:
  - "protocol/schemas/run-summary.json (Draft 2020-12, closed, eight required keys, schema_version 1) and protocol/examples/run-summary.example.json (2,279 bytes, the summary of the committed fixture ledger), in the schema inventory"
  - "summary.summary_of (pure) and reduce.render_outputs(ledger_bytes) -> Outputs, reduce.result_sha256, reduce.SUMMARY_NAME; write_outputs settles three files and validates every mapping against its schema before a file is opened"
  - "python -m llm4pol.run replay in full: writes an absent file of a closed run, refuses a differing one with exit 4 and nothing written, writes nothing into an open run, --out writes the three files, prints ledger_sha256, results_sha256 and last result_sha256"
  - "tests/fixtures/run/reference-ledger.jsonl: 18 LF lines, 10,308 bytes, fixture ids and invented values only, equal to a fresh reference run and pinned by four sha256 values"
  - "charter section 13 M3 exit criterion (2) reproduced on the synthetic table: replay is byte-identical for results.csv, usage.json and run_summary.json"
affects: [04-09, phase-05, phase-06]

plan_head_before: be39159ca95c0ed78f5dd2cdf94a6d4fe20a1439
actuals:
  tokens: 10500
  tasks: 1
  commits: 2

tech-stack:
  added: []
  patterns:
    - "one rendering for every caller: render_outputs(ledger_bytes) returns the bytes and hashes of all three reduced files, and write_outputs, replay and the tests all go through it"
    - "a pinned fixture reduced with a constant: two hashes hand-derived (results.csv, usage.json), two recorded at generation (ledger, summary), and the summary bytes rebuilt in run_support from the plan's hand table with no import of llm4pol.run"
    - "a leaf module (summary.py) holds the pure mapping builder and imports the row type for type checking only, so reduce.py can import it without a cycle"

key-files:
  created:
    - src/llm4pol/run/summary.py
    - protocol/schemas/run-summary.json
    - protocol/examples/run-summary.example.json
    - tests/test_run_replay.py
    - tests/fixtures/run/reference-ledger.jsonl
  modified:
    - src/llm4pol/run/reduce.py
    - src/llm4pol/run/__main__.py
    - src/llm4pol/run/__init__.py
    - pyproject.toml
    - experiments/README.md
    - tests/run_support.py
    - tests/test_run_resume.py
    - tests/test_run_cli.py
    - tests/test_run_reduce.py
    - tests/test_check_inventory.py

key-decisions:
  - "Placement under the line limits (owner asked for it to be recorded): summary_of, SUMMARY_SCHEMA_VERSION and the trend building are in the new src/llm4pol/run/summary.py (67 lines); Outputs, render_outputs, result_sha256, SUMMARY_NAME, SUMMARY_SCHEMA_PATH and the three-file write_outputs are in reduce.py, which is 397 lines after compaction; ledger.py is untouched at 399; reduce imports summary_of, so reduce.summary_of resolves as the interface names it and a test can monkeypatch it there"
  - "result_sha256 is the sha256 of results.csv, usage.json and run_summary.json laid end to end (owner note 1, CONTEXT D-03); printed by replay, never stored"
  - "A ledger that holds a header and no event cannot be summarised (no run_opened, so no primary population): render_outputs raises ReduceError and replay exits 2; usage on such a ledger still works because it does not go through render_outputs"
  - "replay compares before it writes anywhere: a differing file returns 4 before the run directory or --out is touched"

patterns-established:
  - "Outputs carries closed (a bool), so a caller decides between write-into-the-run-directory and write-nothing without parsing twice; write_outputs takes an optional precomputed Outputs"

requirements-completed: [RUN-04]

coverage:
  - id: D1
    description: "run_summary.json of the reference run validates against run-summary.json, has exactly the eight keys, the six trend entries in first-appearance order (full, random, chem, each for check_tc then readme_triple), points with iteration and value, a null percentile and count 0 for the empty chem beam, the sha256 of the ledger bytes and results_sha256 0e31cfc3..., and bytes equal to pretty_bytes of the parsed object"
    requirement: RUN-04
    verification:
      - kind: unit
        ref: "tests/test_run_replay.py#test_run_summary_holds_what_adr_0008_names"
        status: pass
    human_judgment: false
  - id: D2
    description: "the schema refuses fifteen defects (removed key, extra key, status done, float or negative counts, iteration 0, string percentile, 63-character and upper-case hashes, schema_version 2, empty primary population, malformed run id); write_outputs raises ReduceError before any file exists when the mapping is refused"
    requirement: RUN-04
    verification:
      - kind: unit
        ref: "tests/test_run_replay.py#test_summary_schema_pins_names_and_types"
        status: pass
    human_judgment: false
  - id: D3
    description: "a closed run directory holds exactly meta.json, ledger.jsonl, usage.json, results.csv and run_summary.json, for the reference run and for the budget run (status budget_exhausted, completed_iterations 0)"
    requirement: RUN-04
    verification:
      - kind: unit
        ref: "tests/test_run_replay.py#test_a_closed_run_directory_holds_five_files"
        status: pass
    human_judgment: false
  - id: D4
    description: "replay --out writes three files equal to the run directory's, returns 0, and prints ledger_sha256, results_sha256 and last result_sha256 equal to the sha256 of the three files end to end; a byte changed in any of the three files makes replay return 4 with the integrity line and write nothing (not even --out)"
    requirement: RUN-04
    verification:
      - kind: integration
        ref: "tests/test_run_replay.py#test_replay_regenerates_the_three_files_byte_identical"
        status: pass
      - kind: integration
        ref: "tests/test_run_replay.py#test_replay_refuses_a_file_that_differs"
        status: pass
    human_judgment: false
  - id: D5
    description: "replay writes the three files of a closed run that lacks them (also the one missing file of a partial run), writes nothing into a run cut after event 9, and with --out gives a summary of status open and completed_iterations 0"
    requirement: RUN-04
    verification:
      - kind: integration
        ref: "tests/test_run_replay.py#test_replay_writes_what_is_absent_on_a_closed_run_and_nothing_into_an_open_one"
        status: pass
    human_judgment: false
  - id: D6
    description: "the committed fixture ledger (10,308 bytes, sha256 bc2370c0...) reduces with no table present to results.csv sha256 0e31cfc3... and usage.json sha256 bb11fcba..., a run_summary.json of 2,279 bytes sha256 8190025e... equal to the committed example; it equals a fresh reference run byte for byte; it has 18 LF lines, no CR, only the six fixture ids and the unknown id, forty zeros as code sha, the fixed run id, and every result value equals what TableBackend serves for that id"
    requirement: RUN-04
    verification:
      - kind: unit
        ref: "tests/test_run_replay.py#test_committed_fixture_ledger_reduces_to_the_pinned_bytes"
        status: pass
      - kind: unit
        ref: "tests/test_run_replay.py#test_committed_fixture_ledger_equals_a_fresh_reference_run"
        status: pass
      - kind: unit
        ref: "tests/test_run_replay.py#test_committed_fixture_holds_fixture_ids_and_invented_values_only"
        status: pass
    human_judgment: false
  - id: D7
    description: "replay and usage in a child interpreter started in an empty directory, on a run directory holding only the fixture ledger, return 0 and load none of numpy, pandas, pyarrow; reduce.py, ledger.py, jsonio.py and summary.py import none of them and __init__.py imports neither population nor resume; no file of the reference run or the tracer run matches a scanner class"
    requirement: RUN-04
    verification:
      - kind: integration
        ref: "tests/test_run_replay.py#test_replay_and_usage_need_no_table_and_no_dataframe_library"
        status: pass
      - kind: unit
        ref: "tests/test_run_replay.py#test_reduced_modules_import_no_dataframe_library"
        status: pass
      - kind: unit
        ref: "tests/test_run_replay.py#test_no_written_file_matches_a_scanner_class"
        status: pass
    human_judgment: false
  - id: D8
    description: "the resume test still reports 18 passed and now compares usage.json and run_summary.json as well as the ledger and results.csv at every boundary; the gate prints llm4polcheck inventory: 9 entries, 16 instances processed and SUMMARY: 7/7 steps passed, 387 tests"
    requirement: RUN-04
    verification:
      - kind: unit
        ref: "tests/test_run_resume.py#test_resume_at_every_event_boundary_is_byte_identical"
        status: pass
      - kind: unit
        ref: "tests/test_check_inventory.py#test_repository_inventory_validates"
        status: pass
      - kind: other
        ref: "pixi run --manifest-path env/pixi.toml check -> SUMMARY: 7/7 steps passed, 387 tests, llm4polcheck inventory: 9 entries, 16 instances processed"
        status: pass
    human_judgment: false
  - id: D9
    description: "the two-platform reading of the pinned bytes (windows-latest and ubuntu-latest) is not reproduced by this plan: only the local Windows run exists; the Linux leg is settled by the CI run of plan 04-09"
    requirement: RUN-04
    human_judgment: true
    rationale: "Cross-platform byte identity (RESEARCH F-33, assumptions A1 and A2) cannot be observed on this machine; the test that settles it is committed and runs on both CI legs"

duration: 11min
completed: 2026-09-30
status: complete
---

# Phase 4 Plan 08: run_summary.json, The Full replay, And The Pinned Fixture Ledger Summary

**`run_summary.json` (closed schema, per-beam percentile and count trends with iteration numbers, the sha256 of the ledger and of `results.csv`) is written at close and rebuilt by `replay`, which now regenerates all three reduced files byte for byte, refuses a differing one with exit 4, writes nothing into an open run and ends with `result_sha256`; a committed 10,308-byte fixture ledger pins the reducer with four sha256 values.**

## Performance

- **Duration:** 11 min (08:48Z to 08:59Z)
- **Tasks:** 1 (RED then GREEN)
- **Files:** 5 created, 10 modified
- **Gate:** `SUMMARY: 7/7 steps passed`, 387 tests, `llm4polcheck inventory: 9 entries, 16 instances processed`, no `FAIL` or `HIT` line, on the tree of the GREEN commit

## Accomplishments

- **The hand table and the code agree.** The `run_summary.json` derived by hand from the plan objective (six trend entries, the empty `chem` beam with a null percentile and count 0) was typed into `run_support` before any code existed, with its sha256 computed by an independent `json.dumps`; the writer reproduced it on the first run: 2,279 bytes, sha256 `8190025ee895b71c9961d25a817015437f91285dbbff6b51413d70b20b9d20a9`.
- **Charter section 13 M3 exit criterion (2) on the synthetic table.** `replay --out` gives three files equal to the run directory's; a byte flipped in any of the three gives exit 4, the integrity line and no write; a closed run without outputs gets its three files; a run cut after event 9 gets nothing, and its `--out` summary says `open` with 0 completed iterations.
- **The fixture pins the reducer.** `tests/fixtures/run/reference-ledger.jsonl` was generated by a scratch script (never hand-written) from the reference campaign under the fixed identity, and Test 8 confirms a fresh run still writes the same bytes. Reduced with no table present it gives `results.csv` sha256 `0e31cfc3...` and `usage.json` sha256 `bb11fcba...`.
- **Byte identity at every boundary now covers four files.** The resume test compares `usage.json` and `run_summary.json` as well; 18 of 18 boundaries still pass.

## Record for the owner

| Item | Value |
|---|---|
| Commit, RED | `5a0ade0` test(04-08): add failing run_summary, replay and pinned-fixture tests |
| Commit, GREEN | `28dc5ab` feat(04-08): run_summary.json with its schema and both hashes, replay over the three reduced files, the pinned fixture ledger |
| Fixture | `tests/fixtures/run/reference-ledger.jsonl`, 10,308 bytes (under 20 kB), 18 lines, `i/lf w/lf` |
| Pinned, hand-derived | `results.csv` (453 bytes) `0e31cfc380aaaf9f86a68b5e83986ad34ce57cd3c4704634ea2de840f0512fc6`; `usage.json` (89 bytes) `bb11fcba3db73cf823941bb629dd5827a614f908f7a40ba2f9284e0817787caa` |
| Pinned, recorded at generation | fixture ledger `bc2370c0eff10b2904a325c597d070d1ee63384ba92fc786d29da7ec3839c457`; `run_summary.json` (2,279 bytes) `8190025ee895b71c9961d25a817015437f91285dbbff6b51413d70b20b9d20a9` (also equal to the hand-derived bytes) |
| Inventory line | `llm4polcheck inventory: 9 entries, 16 instances processed` |
| Line counts | `reduce.py` 397, `summary.py` 67 (new), `ledger.py` 399 (untouched), `resume.py` 376, `__main__.py` 266 |
| Gate | `SUMMARY: 7/7 steps passed`, 387 tests |

**Owner notes of the objective, as executed.**
1. `result_sha256` is the sha256 of `results.csv`, then `usage.json`, then `run_summary.json`, printed last by `replay` and stored nowhere (`Outputs` and `reduce.result_sha256`).
2. `status` takes `open`, `completed`, `budget_exhausted`; the schema enumerates them and `summary_of` reads the `run_closed` reason (a run without that event is `open`).
3. The fixture guard is "fixture ids and invented values only": Test 9 admits the six fixture ids and the unknown id as quoted 16-hex strings, checks every result value against what `TableBackend` serves for that id, and does not claim that no id of the pinned table appears.

**Placement under the line limits (as requested).** `summary_of` lives in a new leaf module `summary.py`; everything that needs `reduce()` (`Outputs`, `render_outputs`, `result_sha256`, the three-file `write_outputs`) is in `reduce.py`, which needed about 30 new lines with 19 free and was compacted to 397 without changing a byte of output (`Row.cells` is `dataclasses.astuple`, the operator tables are one line each, `_better_first` is inlined, the `_ByCandidate` alias, two docstrings shortened). `ledger.py` was not touched. The static module list in `tests/test_run_cli.py` gains `summary.py`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `summary_of` is in `summary.py`, not `reduce.py`**
- **Found during:** Task 1 GREEN
- **Issue:** the plan places `summary_of` in `reduce.py` (artifact `contains: "def summary_of("`), but `reduce.py` was at 381 of 400 lines and the summary, `Outputs`, `render_outputs` and `result_sha256` need about 70. The objective of this run asked that the placement be recorded.
- **Fix:** a leaf module `summary.py` holds `summary_of`; `reduce.py` imports it, so `reduce.summary_of` resolves as 04-09 names it (`reduce.render_outputs`, also in `reduce.py`). The module has no run-time import of `reduce` (the `Row` type is imported under `TYPE_CHECKING`).
- **Files modified:** `src/llm4pol/run/summary.py` (new), `src/llm4pol/run/reduce.py`, `src/llm4pol/run/__init__.py`, `tests/test_run_cli.py` (module list), `tests/test_run_replay.py` (Test 12 scans it too)
- **Commit:** `28dc5ab`

**2. [Rule 1 - Bug] Two earlier expectations that this plan changes by design**
- **Found during:** Task 1 GREEN
- **Issue:** `tests/test_run_reduce.py::test_usage_is_written_beside_the_results_and_never_overwritten` (04-07) expected `write_outputs` to return two hashes; it settles three files now. The equivalent expectation in `tests/test_run_cli.py` and the five-file directory listing were changed in the RED commit as the plan lists.
- **Fix:** the 04-07 test expects the third hash, `REFERENCE_SUMMARY_SHA256`. No byte of any earlier pinned output changed.
- **Files modified:** `tests/test_run_reduce.py`
- **Commit:** `28dc5ab`

**3. [Rule 1 - Bug] Test 9 read decimal digits as ids**
- **Found during:** Task 1 GREEN, first run
- **Issue:** the plan says "every 16-hex token is one of the six fixture ids"; a 16-digit fractional part of a float (`0.5355339059327378`, `2.6100000000000003`) is also a 16-hex token.
- **Fix:** the test looks for quoted 16-hex strings, which is how an id appears in the ledger; the ledger holds nothing else in quotes at that length.
- **Files modified:** `tests/test_run_replay.py`
- **Commit:** `28dc5ab`

**4. [Rule 2 - Missing critical functionality] Additions beyond the interface list**
- `Outputs.closed` and `Outputs.files()`, and an optional `outputs` argument of `write_outputs`, so `replay` renders once and settles the run directory from that rendering.
- `render_outputs` refuses a ledger with a header and no event (no `run_opened`, hence no primary population) with `ReduceError`, exit 2, instead of a `StopIteration`.
- `replay` compares before it writes anywhere; the earlier `replay` wrote `--out` before comparing, and the plan's Test 5 says a differing file writes nothing.
- `reduce._render_checked` and `_validator(schema_path)` replace the usage-only validator, so usage and summary share one refusal message form (`usage mapping refused by run-usage.json`, `summary mapping refused by run-summary.json`).
- `protocol/schemas/run-summary.json` refuses an empty beam or population name (`minLength` 1) in addition to what the plan lists.
- `experiments/README.md` (not in `files_modified`): the sentence that said the `run_summary.json` schema arrives in plan 04-08 now describes the file and the full `replay`, as the objective of this run asked; the `replay` rule is updated in the same place.
- **Commit:** `28dc5ab`

### Notes, no change

- **The `usage` verb still uses `render_usage`, not `render_outputs`**, although the plan's key link names `render_outputs` for both verbs. `usage` must keep working on an open run and on a header-only ledger, and `render_outputs` refuses the latter; `usage` imports neither `population` nor `resume` either way.
- **The RED commit does not pass the gate**, as in plans 04-05 to 04-07: `5a0ade0` fails at collection (`reduce.SUMMARY_NAME` does not exist) by design. The GREEN commit was gated at 7/7 before it was made.
- **Test 12 does not scan `__main__.py`** for `population` or `resume` imports: the `run` and `resume` handlers import them inside the function on purpose, so that `replay` never loads them; that property is what Test 10 proves in a child interpreter.
- **Line endings.** My first Python edits of three test files wrote CRLF on this Windows shell; they were normalised to LF before the RED commit (`git ls-files --eol` shows `i/lf w/lf` for every touched file).

**Total deviations:** 1 blocking (Rule 3), 2 auto-fixed bugs (Rule 1), 1 set of additive items (Rule 2). **Impact on plan:** one new module not in `files_modified` (`summary.py`) and one earlier test edited at the point where this plan changes its contract; no pinned byte of plans 04-02 to 04-07 changed.

## TDD Gate Compliance

The task has a `test(04-08)` commit (`5a0ade0`) before the `feat(04-08)` commit (`28dc5ab`). The plan sets `type: execute`, so the TDD mode gate was not active. No refactor commit was needed.

## Known Stubs

None. The scan of `src/llm4pol/run/summary.py`, `src/llm4pol/run/reduce.py`, `src/llm4pol/run/__main__.py`, `tests/test_run_replay.py` and `protocol/schemas/run-summary.json` found no TODO, FIXME, placeholder, skipped or xfail test.

## Threat Flags

None new. Register mitigations in place: T-04-38 (`replay` regenerates and compares all three files, exit 4; Test 5, three parametrised cases), T-04-39 (the closed schema is applied before writing; Test 2), T-04-40 (bytes written without text mode, `repr` floats, fixed separators; Test 7 is the test the ubuntu-latest leg runs, settled by 04-09), T-04-41 (Test 8 regenerates the ledger, Test 7 compares the example with the rendered summary), T-04-42 (Test 11: no class of `history_secret_scan.PATTERNS` matches any of the ten files), T-04-43 (Test 9), T-04-44 (write what is absent, compare what is present; Tests 5 and 6). T-04-SC: nothing installed.

## Next Phase Readiness

Ready for 04-09 (the CI reading and the pinned table). `reduce.render_outputs(ledger_bytes)` exists with the signature 04-09 lists, returning `Outputs` (`results`, `usage`, `summary`, `ledger_sha256`, `results_sha256`, `closed`). The one open fact is the ubuntu-latest reading of the four pinned hashes, which only the CI run can give.

## Self-Check: PASSED

- Created files exist: `src/llm4pol/run/summary.py`, `protocol/schemas/run-summary.json`, `protocol/examples/run-summary.example.json`, `tests/test_run_replay.py`, `tests/fixtures/run/reference-ledger.jsonl`; modified files listed above exist.
- Commits `5a0ade0` and `28dc5ab` are in `git log`; `git rev-list --count be39159..HEAD` gave 2 (the measured `commits`).
- Plan verification re-run: `tests/test_run_replay.py`, `test_run_resume.py`, `test_run_cli.py`, `test_check_inventory.py`, `test_run_examples.py`, `test_run_reduce.py`, `test_run_ledger.py`, `test_run_population.py`, `test_run_config.py` green with no skip (60 passed in the replay and resume files together); the four named tests report `4 passed`; `git ls-files --eol` prints `i/lf w/lf` for the fixture; `grep -c ""` prints 18; `git ls-files experiments` prints `experiments/README.md` only; the gate prints the 9/16 inventory line once and `SUMMARY: 7/7 steps passed`.
