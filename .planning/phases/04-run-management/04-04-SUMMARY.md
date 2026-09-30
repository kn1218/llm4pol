---
phase: 04-run-management
plan: 04
subsystem: run-record
tags: [schema-inventory, examples, ledger, run-meta, problem-spec, selection-plan, a-5, d-39]

requires:
  - phase: 04-run-management
    provides: "problem-spec.json and ledger-event.json (04-01), selection-plan.json, run-meta.json, open_run, drive and the tracer run (04-02), run_support fixtures"
  - phase: 03-evaluator
    provides: "the committed-example pattern of test_evaluate_contract.py"
provides:
  - "eleven committed examples under protocol/examples: problem spec, selection plan, meta.json, ledger header, one ledger event of each of the seven kinds"
  - "four new [tool.llm4polcheck] entries; the gate prints `llm4polcheck inventory: 7 entries, 14 instances processed`"
  - "tests/test_run_examples.py: schema validity, validation, byte equality of the ledger examples with a fresh tracer run, meta equality, tracer inputs, the fixture-id scan"
affects: [04-05, 04-06, 04-07, 04-08, 04-09]

plan_head_before: 089440deec1d716301a71d572df25bb2cb99781e
actuals:
  tokens: 5000
  tasks: 1
  commits: 2

tech-stack:
  added: []
  patterns:
    - "an example of a written record is a line of the run that writes it, generated under an injected clock, token, code identity and an empty environment, and compared byte for byte by a test"
    - "the id scan reads quoted 16-hex JSON strings, never bare digit runs"

key-files:
  created:
    - protocol/examples/problem-spec.example.json
    - protocol/examples/selection-plan.example.json
    - protocol/examples/run-meta.example.json
    - protocol/examples/ledger-header.example.json
    - protocol/examples/ledger-event.run_opened.example.json
    - protocol/examples/ledger-event.iteration_opened.example.json
    - protocol/examples/ledger-event.selection.example.json
    - protocol/examples/ledger-event.evaluation.example.json
    - protocol/examples/ledger-event.no_match.example.json
    - protocol/examples/ledger-event.iteration_closed.example.json
    - protocol/examples/ledger-event.run_closed.example.json
    - tests/test_run_examples.py
  modified:
    - pyproject.toml
    - tests/test_check_inventory.py

key-decisions:
  - "The meta example is made with an empty mapping standing for the environment, injected by replacing resume.build_meta with functools.partial(build_meta, environ={}) in the test and the scratch generator; open_run has no environ parameter and the plan does not add one"
  - "The ledger examples are the first event of each kind of the tracer run, rendered with jsonio.pretty_bytes, so the evaluation example is the first of the three evaluation events (candidate 7ec8cb49ff317efc, three results)"

patterns-established:
  - "An inventory glob over generated instances is paired with a test that the file set equals header plus one file per event kind, so a stray file cannot join the glob unnoticed"

requirements-completed: [RUN-01, RUN-02, RUN-06]

coverage:
  - id: D1
    description: "The four schemas of the tracer are valid Draft 2020-12; the problem, plan, meta and eight ledger examples validate against them; the ledger files are one header and one event of each of the seven kinds"
    requirement: RUN-02
    verification:
      - kind: unit
        ref: "tests/test_run_examples.py#test_run_record_schemas_are_valid_draft_2020_12"
        status: pass
      - kind: unit
        ref: "tests/test_run_examples.py#test_committed_run_examples_validate_against_their_schemas"
        status: pass
    human_judgment: false
  - id: D2
    description: "The header and the first event of each kind of a fresh tracer run, rendered with pretty_bytes, equal the committed ledger examples byte for byte"
    requirement: RUN-02
    verification:
      - kind: integration
        ref: "tests/test_run_examples.py#test_committed_ledger_examples_equal_the_tracer_run_lines"
        status: pass
    human_judgment: false
  - id: D3
    description: "The problem and plan examples parse to charter_problem(1, 3, 2) and TRACER_PLAN and equal their pretty_bytes; the meta example equals the tracer meta in every key but snapshot_sha256 (platform line terminator of the synthetic CSV, F-28)"
    requirement: RUN-06
    verification:
      - kind: unit
        ref: "tests/test_run_examples.py#test_committed_problem_and_plan_examples_are_the_tracer_inputs"
        status: pass
      - kind: integration
        ref: "tests/test_run_examples.py#test_committed_meta_example_equals_the_tracer_meta"
        status: pass
    human_judgment: false
  - id: D4
    description: "Every quoted 16-hex id in the eleven examples is one of the six fixture ids"
    requirement: RUN-01
    verification:
      - kind: unit
        ref: "tests/test_run_examples.py#test_every_id_in_the_examples_is_a_fixture_id"
        status: pass
    human_judgment: false
  - id: D5
    description: "The gate inventory processes 14 instances in 7 entries and the whole gate passes; no file under protocol/schemas changed between the RED commit and the tip"
    verification:
      - kind: other
        ref: "pixi run --manifest-path env/pixi.toml check -> `llm4polcheck inventory: 7 entries, 14 instances processed`, `SUMMARY: 7/7 steps passed` (233 tests); git diff --stat bfc42bf^..HEAD -- protocol/schemas is empty"
        status: pass
    human_judgment: false

duration: 12min
completed: 2026-09-30
status: complete
---

# Phase 4 Plan 04: Committed Run-Record Examples in the Schema Inventory Summary

**Eleven example files (problem spec, selection plan, meta, ledger header, one event of each of the seven kinds) generated from the tracer run under an injected identity, validated by the gate on every run, and compared with a fresh run byte for byte by a test.**

## Performance

- **Duration:** 12 min
- **Tasks:** 1 (RED commit, then GREEN commit)
- **Files:** 14 (12 created, 2 modified)
- **Gate:** `SUMMARY: 7/7 steps passed`, 233 tests

The gate line: `llm4polcheck inventory: 7 entries, 14 instances processed` (3 existing instances plus 11).

## Accomplishments

- The four schemas the tracer uses (`problem-spec.json`, `selection-plan.json`, `run-meta.json`, `ledger-event.json`) each have a committed instance in the `[tool.llm4polcheck]` inventory, so a drift between schema and instance fails the gate.
- The ledger examples cannot drift from the writer: `test_committed_ledger_examples_equal_the_tracer_run_lines` opens and drives the tracer run on `synthetic_candidates` under `FIXED_NOW`, `FIXED_TOKEN`, a constant clock and `CodeIdentity(FIXED_CODE_SHA, False)` and compares eight byte strings.
- The meta example equals the meta of that run in fourteen of its fifteen keys; `snapshot_sha256` is excluded from the comparison with the reason stated in the test (pandas writes the CSV with the platform line terminator, F-28) and both values are checked to be 64 hex characters.
- No schema was edited and every example passed its schema at the first generation.

## Task Commits

1. **Task 1 RED** - `bfc42bf` (test): failing schema-example tests for the run record; five of the six new tests and the inventory count assertion fail on missing files (assertion or file errors), the schema-validity test passes at once
2. **Task 1 GREEN** - `3344f4b` (feat): the eleven examples, four inventory entries, and the quoted-id scan

**Plan metadata:** recorded by the closing docs commit.

## Decisions Made

- The empty environment for the meta example is injected by replacing `resume.build_meta` with `functools.partial(config.build_meta, environ={})` (`monkeypatch` in the test, a plain assignment in the throwaway generator). `open_run` takes no `environ` argument and the plan does not ask for one.
- The evaluation example is the first `evaluation` event of the tracer run, which carries three results and the cost of one candidate.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] The fixture-id scan matched the fractional digits of a float**
- **Found during:** Task 1 GREEN, first test run after the examples existed
- **Issue:** the pattern `\b[0-9a-f]{16}\b` of my own Test 6 read `2.6100000000000003` (a threshold percentile in `run_opened`) as the token `6100000000000003`, so the test failed on a value that is not an id.
- **Fix:** the pattern is now `"([0-9a-f]{16})"`; an id is always a JSON string, and the quotes keep a number out of the scan. The comment above it says why. The test still asserts that at least one id is found.
- **Files modified:** `tests/test_run_examples.py`
- **Verification:** the six tests pass; the found set is a subset of the six fixture ids.
- **Committed in:** `3344f4b`

---

**Total deviations:** 1 auto-fixed (Rule 1, in a test written by this plan).
**Impact on plan:** none on the examples or the schemas; the guard is stricter about shape, not weaker (ids are quoted strings by the schema).

## TDD Gate Compliance

`test(04-04)` (`bfc42bf`) precedes `feat(04-04)` (`3344f4b`). The RED state is behavioural: five tests failed on the absent example files and the inventory test failed on the count (`3 entries, 3 instances` against the expected `7 entries, 14 instances`); `test_run_record_schemas_are_valid_draft_2020_12` passed at once because the four schemas already exist. The plan sets `type: execute`, so the TDD mode gate was not active. No refactor commit was needed.

## Issues Encountered

None beyond the deviation above. No package was installed and the lock file is untouched. The generator script lives in the session scratch directory and is not committed (the plan forbids hand-written examples and asks for a script that is not kept).

## Known Stubs

None. The scan of `tests/test_run_examples.py` found no TODO, FIXME, placeholder or skipped test; the examples are complete records.

## Threat Flags

None. T-04-18 is mitigated by Tests 3 to 5 comparing bytes or keys with a fresh run, T-04-19 by the empty `git diff --stat bfc42bf^..HEAD -- protocol/schemas`, T-04-20 by Test 6 (only the six fixture ids) and T-04-21 by the empty environment mapping (`provider_key_configured` is `false` and no environment value appears in the file). No new network, auth or trust-boundary surface was added.

## Next Phase Readiness

Plans 04-07 and 04-08 add the `usage.json` and `run_summary.json` schemas with their writers and take the inventory to 9 entries and 16 instances; the count assertion in `tests/test_check_inventory.py` moves with them. Plan 04-05 must not change the bytes written for an uninterrupted run, and plan 04-06 must not move a byte of the meta example (a redaction rule inside `config.py` and a narrower `dirty`); the two byte-equality tests named above fail at the first drift of either.

## Self-Check: PASSED

- All twelve created files exist on disk; the commits `bfc42bf` and `3344f4b` are in `git log`.
- `git rev-list --count 089440d..HEAD` was 2 at the GREEN commit (the measured `commits`).
- Plan verification re-run: the two test files pass with no skip; `ls protocol/examples | grep -c "^ledger-.*\.example\.json$"` prints 8; the gate prints `llm4polcheck inventory: 7 entries, 14 instances processed` once and ends `SUMMARY: 7/7 steps passed` with no `FAIL` or `HIT` line; the diff of `protocol/schemas` from `bfc42bf^` to the tip is empty.
