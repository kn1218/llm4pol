---
phase: 04-run-management
plan: 05
subsystem: run-record
tags: [resume, ledger-integrity, event-keys, budget-refusal, byte-identity, a-6, m3-exit-1]

requires:
  - phase: 04-run-management
    provides: "ledger (header, fsynced appends, strict reader) and schemas (04-01); open_run, drive, reducer, populations, run/replay verbs (04-02); committed run-record examples that a fresh tracer run reproduces byte for byte (04-04)"
  - phase: 03-evaluator
    provides: "Evaluator with a prepared cache and meter, BudgetExceeded raised before commit, key_for, JsonlCache.put_many, EvalResult.from_json"
provides:
  - "ledger.read refuses every defect of a line or of the sequence: torn tail, repeated key, second header, seq gap, foreign run id, duplicate event key, event after run_closed, evaluation without its selection, lifecycle disorder, unequal population arrays"
  - "resume.rebuild_state and resume.resume: the cache, the meter and the recorded keys come from the recorded evaluation events and nothing else; drive continues any valid prefix inside the open iteration"
  - "python -m llm4pol.run resume (no problem option) and the recorded budget refusal run_closed(budget_exhausted) with exit 3"
  - "selector.verify_replay and SequenceMismatch: a recorded selection the selector does not give is refused before anything is appended"
  - "charter section 13 M3 exit criterion (1) reproduced on the synthetic table: 18 of 18 event boundaries resume to the bytes of the uninterrupted run"
affects: [04-06, 04-07, 04-08, 04-09, phase-05, phase-06]

plan_head_before: 5ffe57bb149fe86d6750e1c3a33aa1bbb829b927
actuals:
  tokens: 14700
  tasks: 2
  commits: 4

tech-stack:
  added: []
  patterns:
    - "one code path for a fresh and a resumed run: state derived from the ledger, every event whose key is recorded is skipped"
    - "the replay-sequence check compares each recorded iteration with a prefix of the events the selector implies, before any append"
    - "a refusal is an exception that leaves the ledger bytes as found; the only writers are exclusive create and append"

key-files:
  created:
    - tests/test_run_resume.py
  modified:
    - src/llm4pol/run/ledger.py
    - src/llm4pol/run/resume.py
    - src/llm4pol/run/selector.py
    - src/llm4pol/run/reduce.py
    - src/llm4pol/run/__main__.py
    - src/llm4pol/run/__init__.py
    - docs/governance/INVARIANTS.md
    - tests/run_support.py
    - tests/test_run_ledger.py
    - tests/test_run_cli.py

key-decisions:
  - "Exit codes fixed within CONTEXT D-07 and R-9 (owner: a choice made here for review): 2 the record cannot be read as a ledger (torn final line, a line that does not parse or validate) and other input defects; 3 budget refusal recorded by this call; 4 a readable ledger that cannot be trusted or continued (seq gap, duplicate key, lifecycle order, header naming other snapshot, registry version, code sha or selector, a recorded selection the selector does not give, results.csv that is not what the ledger reduces to)"
  - "resume on a run that is already closed returns 0 and appends nothing, also when the recorded close is budget_exhausted; exit 3 is reserved for the call that records the refusal (Outcome.appended tells them apart)"
  - "RunRefused and SequenceMismatch subclass LedgerIntegrityError, so the existing handler maps them to exit 4 with the integrity line and the CLI does not import resume for the mapping"
  - "The sequence check compares whole iterations, not only selections: recorded events must be a prefix of iteration_opened, per beam selection or no_match then one evaluation per candidate in order, iteration_closed; this also refuses a doctored evaluation order or an iteration closed early"
  - "run_closed is accepted inside an open iteration (a budget refusal ends the run there); a completed close is not required to follow an iteration_closed"

patterns-established:
  - "State is never carried across a restart: Evaluator gets JsonlCache() and a BudgetMeter built from the ledger"
  - "A hand-derived campaign (reference: 17 events, 5 evals, 453-byte results.csv; budget: 6 events, 244 bytes) is a fixture with its bytes and sha256 in run_support"

requirements-completed: [RUN-02, RUN-03]

coverage:
  - id: D1
    description: "ledger.read refuses a torn tail at each byte of the last line (offset of the last LF and trailing byte count), a duplicate event key (seven cases), lifecycle disorder (eight cases), a second header, a foreign run id, unequal population arrays, and twelve schema defects; the tracer ledger is still accepted"
    requirement: RUN-02
    verification:
      - kind: unit
        ref: "tests/test_run_ledger.py#test_truncation_at_every_byte_of_the_last_line_is_refused"
        status: pass
      - kind: unit
        ref: "tests/test_run_ledger.py#test_duplicate_event_keys_are_refused"
        status: pass
      - kind: unit
        ref: "tests/test_run_ledger.py#test_lifecycle_order_is_enforced"
        status: pass
      - kind: unit
        ref: "tests/test_run_ledger.py#test_population_arrays_must_be_parallel"
        status: pass
    human_judgment: false
  - id: D2
    description: "reference campaign: 17 events in the stated order, evaluation events charged 1,1,1,1,0,0,1 (5 evals), POM charged through its dielectric constant, results.csv 453 bytes sha256 0e31cfc3..."
    requirement: RUN-02
    verification:
      - kind: unit
        ref: "tests/test_run_resume.py#test_reference_campaign_records_seventeen_events_and_five_evals"
        status: pass
    human_judgment: false
  - id: D3
    description: "a run cut at each of the 18 event boundaries and resumed gives ledger.jsonl and results.csv equal byte for byte to the uninterrupted run with no repeated event key; the rebuilt meter and cache equal the recorded spend at every boundary; a closed run is left untouched"
    requirement: RUN-03
    verification:
      - kind: unit
        ref: "tests/test_run_resume.py#test_resume_at_every_event_boundary_is_byte_identical"
        status: pass
      - kind: unit
        ref: "tests/test_run_resume.py#test_rebuilt_state_equals_the_recorded_spend"
        status: pass
      - kind: unit
        ref: "tests/test_run_resume.py#test_resume_appends_nothing_to_a_closed_run"
        status: pass
    human_judgment: false
  - id: D4
    description: "resume refuses, appends nothing and repairs nothing for a torn final line (exit 2, offset and trailing bytes on stderr), a different snapshot, registry version, code sha or selector, and a recorded selection the selector does not give (exit 4)"
    requirement: RUN-03
    verification:
      - kind: integration
        ref: "tests/test_run_resume.py#test_resume_refuses_a_torn_final_line"
        status: pass
      - kind: integration
        ref: "tests/test_run_resume.py#test_resume_refuses_a_different_snapshot_registry_version_or_code"
        status: pass
      - kind: integration
        ref: "tests/test_run_resume.py#test_resume_refuses_another_plan_or_a_doctored_selection"
        status: pass
    human_judgment: false
  - id: D5
    description: "a budget refusal ends the run with run_closed reason budget_exhausted, requested 1, remaining 0, limit 2; the CLI exits 3 with BUDGET: evaluation budget exhausted; results.csv is 244 bytes sha256 23f046d9...; a cut run resumes to the same bytes; resume on the closed run exits 0"
    requirement: RUN-03
    verification:
      - kind: integration
        ref: "tests/test_run_resume.py#test_budget_refusal_closes_the_run_and_exits_3"
        status: pass
    human_judgment: false
  - id: D6
    description: "the resume verb has no problem option, takes the problem from the header and completes a CLI-made run cut after event 7 with 17 events and no repeated key; no code path shortens or rewrites a ledger; resume has no argument that relaxes a check"
    requirement: RUN-03
    verification:
      - kind: integration
        ref: "tests/test_run_resume.py#test_cli_resume_reads_the_problem_from_the_header"
        status: pass
      - kind: unit
        ref: "tests/test_run_resume.py#test_the_prohibitions_of_the_plan_hold_in_the_source"
        status: pass
      - kind: other
        ref: "pixi run --manifest-path env/pixi.toml check -> SUMMARY: 7/7 steps passed, 310 tests, Contracts: 5 kept, 0 broken."
        status: pass
    human_judgment: false

duration: 20min
completed: 2026-09-30
status: complete
---

# Phase 4 Plan 05: Resume From The Ledger Alone Summary

**The ledger is the only state: `resume` rebuilds the cache and the budget meter from the recorded `evaluation` events, refuses what it cannot trust, and continues at the first unrecorded key, so a run cut at any of 18 event boundaries ends in the bytes of the uninterrupted run; a budget refusal is a recorded `run_closed` with exit 3.**

## Performance

- **Duration:** 20 min (07:57Z to 08:17Z)
- **Tasks:** 2 (each RED then GREEN)
- **Files:** 11 (1 created, 10 modified)
- **Gate:** `SUMMARY: 7/7 steps passed`, `Contracts: 5 kept, 0 broken.`, 310 tests, at both feature commits (264 at `d190b0b`, 310 at `8d2bbd9`)

## Accomplishments

- Charter section 13 M3 exit criterion (1) reproduced on the synthetic table. The byte-identity test reports **`18 passed`**: the header alone (k = 0) through the complete ledger without its outputs (k = 17), every one giving a `ledger.jsonl` and a `results.csv` equal to the uninterrupted run, 18 lines, and no repeated event key.
- The hand arithmetic of the plan agreed with the code on the first run. Reference campaign: 17 events in the stated order, evaluation events charged `1, 1, 1, 1, 0, 0, 1` (five `evals`), `results.csv` **453 bytes**, sha256 `0e31cfc380aaaf9f86a68b5e83986ad34ce57cd3c4704634ea2de840f0512fc6`. Budget scenario: six events ending in `run_closed(budget_exhausted, requested 1, remaining 0, limit 2)`, `results.csv` **244 bytes**, sha256 `23f046d9a90fcfad19ff5963610210885ef4d7e558c8acaaec9bec9dc0c73062`.
- Ledger sizes (fixed identity, constant clock): reference **10,308 bytes** (18 LF-terminated lines), budget scenario **3,842 bytes** (7 lines). The tracer ledger of 04-02 is unchanged (5,187 bytes, 10 lines), and `tests/test_run_examples.py` stays green without regenerating a committed example.
- `ledger.read` now refuses every defect a line or the sequence can have (Task 1); it reads the truncation sweep of 100+ cut points, each refused with `last_lf_offset` and `trailing_bytes`, and the one clean cut as a shorter ledger.
- `rebuild_state` reproduces the evaluator's own bookkeeping: at k = 12 the meter reads 4, the cache holds the PE results, and an evaluator built from it answers PE with `cached` true and cost 0 (the F-62 failure, a fresh evaluator overcharging, cannot occur).

## Task Commits

1. **Task 1 RED** - `61aaaef` (test): failing ledger integrity tests (duplicate keys, lifecycle, population arrays); the truncation sweep, header and schema tests already passed and stay as guards
2. **Task 1 GREEN** - `d190b0b` (feat): `event_key`, the integrity pass, second-header refusal, A-6 row extended
3. **Task 2 RED** - `1d3aefe` (test): failing resume tests, reference and budget campaigns in `run_support`
4. **Task 2 GREEN** - `8d2bbd9` (feat): `rebuild_state`, `resume`, the continuing `drive`, `verify_replay`, the `resume` verb, exit 3, A-6 row extended

**Plan metadata:** recorded by the closing docs commit.

## Exit Codes (a choice made within CONTEXT D-07 and R-9; flagged for the owner)

| Code | Meaning | Stdout |
|---|---|---|
| 0 | success; also `resume` on a run that is already closed (nothing appended) | cost lines |
| 2 | the record cannot be read as a ledger (torn final line, a line that does not parse or validate), or another input defect (invalid problem or plan, unknown run id, missing table) | `ERROR: input refused` |
| 3 | the evaluation budget refused a request and this call recorded `run_closed(budget_exhausted)` | `BUDGET: evaluation budget exhausted` |
| 4 | a readable ledger that cannot be trusted or continued: `seq` gap, duplicate key, lifecycle order, header naming another snapshot, registry version, code sha or selector, a recorded selection the selector does not give, a `results.csv` that is not what the ledger reduces to | `ERROR: ledger integrity check failed` |

The detail line on stderr names what differs (field with both values, or the offset of the last LF and the number of trailing bytes).

## Decisions Made

See `key-decisions`. The two the owner may want to overrule: `resume` on an already closed budget-exhausted run returns 0 rather than 3, as the plan states; and a `RunRefused` (header versus running code) shares exit 4 with ledger integrity defects.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug/conflict] A foreign `run_id` stays `LedgerIntegrityError`, not `LedgerFormatError`**
- **Found during:** Task 1 (Test 4)
- **Issue:** the plan's Test 4 says an event whose `run_id` differs from the header raises `LedgerFormatError`, while the 04-01 test `test_read_refuses_a_missing_header_a_second_header_and_a_foreign_run` (which the plan says stays as it is) pins `LedgerIntegrityError`, and the objective maps integrity defects to exit 4.
- **Fix:** kept the class the earlier plan fixed. The second header is `LedgerFormatError` (a defect of form); Test 4 asserts `LedgerIntegrityError` for the foreign run id.
- **Files modified:** `tests/test_run_ledger.py`
- **Commit:** `61aaaef`

**2. [Rule 1 - Bug] A 04-01 test appended `run_closed` as the first event of a ledger**
- **Found during:** Task 1 GREEN, first full run
- **Issue:** `test_ledger_schema_closes_the_envelope_and_the_payload_rules` read back a ledger whose only event was `run_closed`, which the new "first event is `run_opened`" rule (Task 1 Test 3) refuses.
- **Fix:** the test appends a `run_opened` first and numbers the close 2; its assertions are otherwise unchanged.
- **Files modified:** `tests/test_run_ledger.py`
- **Commit:** `d190b0b`

**3. [Rule 1 - Bug] Two 04-02 expectations that this plan changes by design**
- **Found during:** Task 2 GREEN
- **Issue:** (a) `test_a_request_beyond_the_evals_limit_exits_3_and_leaves_a_valid_prefix` pinned the interim behaviour (an unclosed prefix, stdout `BUDGET: evaluation budget exceeded`) that 04-02 explicitly left to this plan; (b) `test_reduce_is_a_pure_function_of_the_ledger` expected `FileExistsError` from `write_outputs` on a present `results.csv`, which the plan replaces with compare-and-never-overwrite.
- **Fix:** (a) renamed to `..._exits_3_and_records_the_refusal`, now asserts the ledger ends `selection, evaluation, run_closed` with reason `budget_exhausted` and the line `BUDGET: evaluation budget exhausted`; (b) asserts a present equal file is returned as its sha256 and left as found, and a differing file raises `LedgerIntegrityError` and is left as found. No expected results bytes changed.
- **Files modified:** `tests/test_run_cli.py`
- **Commit:** `8d2bbd9`

**4. [Rule 3 - Blocking] `verify_replay` and `SequenceMismatch` live in `selector.py`**
- **Found during:** Task 2 GREEN
- **Issue:** with the replay check inside `resume.py` the file reached 415 lines, over the 400-line limit the plan and `test_the_static_prohibitions_of_the_plan_hold` set; adding a module would change that test's fixed module list.
- **Fix:** the check (about 60 lines, a function of the selector protocol and a ledger) sits in `selector.py`; `resume.py` imports and lists `SequenceMismatch` in `__all__`, so `resume.SequenceMismatch` resolves as the plan names it. `resume.py` is 376 lines, `ledger.py` 399.
- **Files modified:** `src/llm4pol/run/selector.py`, `src/llm4pol/run/resume.py`
- **Commit:** `8d2bbd9`

**5. [Rule 2 - Missing critical functionality] Names, checks and tests beyond the interface table**
- `ledger.EventKey` (type) and `ledger.event_key` exported from the package root (the root still does not import `resume`); `Outcome` gained `status`, `appended` and `closing`; a `_check_populations` also refuses a repeated population name.
- `TornTail`'s message now carries `last LF at byte offset N, M trailing bytes`, so the stderr detail of the CLI names both without special-casing the exception.
- `BudgetExceeded` is no longer caught in `main` (the driver records it and the handler returns 3); the import was removed.
- Extra tests: `test_a_valid_lifecycle_is_accepted_with_a_budget_close_in_an_open_iteration` (a budget close inside an open iteration is valid; a selection and a no_match share one key space), `test_the_prohibitions_of_the_plan_hold_in_the_source` (ledger writers use only `xb` and `ab`, no truncate/unlink/replace anywhere in the package, `resume` has exactly `run_dir, root, selector, code, clock`, memory-only cache), and a doctored `results.csv` case inside `test_resume_appends_nothing_to_a_closed_run`.
- **Commits:** `d190b0b`, `8d2bbd9`

**6. Note on the RED state of Task 1**
The plan expected Tests 2, 3, 4 and 5 to fail at RED. Tests 2, 3, 5 and the new lifecycle test failed; Test 4 (second header, foreign run) and Tests 1 and 6 already passed because the 04-01 reader had those checks. They stay as guards, as the plan allows for Tests 1 and 6. The RED of Task 2 is an `AttributeError` or an argparse usage error on the missing names, except the reference-campaign test, which passed at once and confirmed the hand arithmetic.

---

**Total deviations:** 3 auto-fixed bugs or conflicts (Rule 1), 1 blocking (Rule 3), 1 set of additive hardening items (Rule 2), plus one note on RED states.
**Impact on plan:** additive inside the plan's own area, plus one file (`selector.py`) not in `files_modified`; three earlier tests edited at the points where this plan changes their contract, none in a way that changes an expected byte of a committed example or of the tracer results.

## TDD Gate Compliance

Both tasks have a `test(04-05)` commit (`61aaaef`, `1d3aefe`) before the `feat(04-05)` commit (`d190b0b`, `8d2bbd9`). The plan sets `type: execute`, so the TDD mode gate was not active. No refactor commit was needed.

## Issues Encountered

- Ruff's `--fix` removed an unused re-export (`SequenceMismatch` in `resume.py`) and the test caught it at once; the name is now in `__all__`.
- `ledger.py` ended at 399 lines, one under the limit; the section banners were dropped to make room. A later plan that adds to `ledger.py` must move something out first.

## Known Stubs

None. The scan of `src/llm4pol/run/`, `tests/test_run_resume.py`, `tests/test_run_ledger.py` and `tests/run_support.py` found no TODO, FIXME, placeholder or skipped test.

## Threat Flags

None new. The mitigations of the plan's register are in place: T-04-22 (LF rule, schema, `seq`, event keys and lifecycle in `ledger.read`, read before anything is built), T-04-23 (state rebuilt from recorded results, 18 boundaries), T-04-24 (four header comparisons, no override argument), T-04-25 (only exclusive create and append write the ledger; refusals leave the bytes as found, asserted in the refusal tests), T-04-26 (the refusal is recorded as `run_closed`). T-04-27 is accepted: stderr details name snapshot ids, a registry version, git shas and a plan hash, and no environment value is read.

## Next Phase Readiness

Plans 04-06..04-09 do not depend on a name this plan changed except through `resume.drive` and `reduce.write_outputs`. Notes: `drive` no longer refuses a ledger that holds events; it continues any valid prefix and refuses through `verify_replay`. A selector that reads results (Phase 5) receives, for every iteration, the events recorded before that iteration opened, identically in a fresh and in a resumed run. `ledger.py` has no headroom under the 400-line limit.

## Self-Check: PASSED

- Created and modified files exist on disk (`tests/test_run_resume.py`, `src/llm4pol/run/resume.py`, `src/llm4pol/run/selector.py`, `tests/run_support.py`); the four commits `61aaaef`, `d190b0b`, `1d3aefe`, `8d2bbd9` are in `git log`, newest first with the subjects the plan names.
- `git rev-list --count 5ffe57b..HEAD` was 4 (the measured `commits`).
- Plan verification re-run: `tests/test_run_resume.py` 46 passed with no skip; the byte-identity test reports `18 passed`; the three named tests report `3 passed`; `campaign resume --help` lists `--run` and `--plan` and no `--problem`; the A-6 row names `test_truncation_at_every_byte_of_the_last_line_is_refused` and `test_resume_at_every_event_boundary_is_byte_identical` (one match each); `resume.py` 376 lines, `ledger.py` 399, no function over 50 lines in the files this plan touched except the pre-existing `reduce._row` (49).
- Full gate at the final feature commit: `SUMMARY: 7/7 steps passed`, 310 tests, `Contracts: 5 kept, 0 broken.`
