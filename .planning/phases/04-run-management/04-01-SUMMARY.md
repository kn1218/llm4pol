---
phase: 04-run-management
plan: 01
subsystem: run-record
tags: [jsonl-ledger, json-schema, import-linter, run-id, problem-spec, a-3, a-6]

requires:
  - phase: 03-evaluator
    provides: "eval-response.json $defs/cost and $defs/result (copied verbatim into the ledger schema), the canonical JSON form of cache.py, the parse-then-type pattern of parse_request"
  - phase: 01-foundation
    provides: "the import-linter step, the schema-inventory step and the pixi check gate"
provides:
  - "llm4pol.run package (ids, jsonio, config, ledger) under a fifth import contract that landed with it"
  - "protocol/schemas/problem-spec.json and protocol/schemas/ledger-event.json (the two schemas of the charter M3 freeze)"
  - "A-6 guarded by four test_a6_* tests; the ledger half of A-3 guarded by test_a3_ledger_schema_keeps_the_two_currencies_apart"
  - "tests/run_support.py fixtures for every later Phase 4 plan"
affects: [04-02, 04-03, 04-04, 04-05, 04-06, 04-07, 04-08, 04-09, phase-05, phase-06]

plan_head_before: eba293e21310ad2f745ad716636d7c4ba4d2dd03
actuals:
  tokens: 19500
  tasks: 2
  commits: 4

tech-stack:
  added: []
  patterns:
    - "validate against a closed JSON Schema first, then build the frozen dataclass (problem spec, header, event)"
    - "ledger bytes: one canonical line per append, binary exclusive create, fsync, LF rule on read"
    - "self-contained schema (no cross-file $ref) with embedded $defs compared to their sources by a test"
    - "injected clock and random token for every id and timestamp"

key-files:
  created:
    - src/llm4pol/run/__init__.py
    - src/llm4pol/run/ids.py
    - src/llm4pol/run/jsonio.py
    - src/llm4pol/run/config.py
    - src/llm4pol/run/ledger.py
    - protocol/schemas/problem-spec.json
    - protocol/schemas/ledger-event.json
    - tests/run_support.py
    - tests/test_run_config.py
    - tests/test_run_ledger.py
  modified:
    - pyproject.toml
    - scripts/check.py
    - docs/governance/INVARIANTS.md
    - tests/test_import_boundary.py

key-decisions:
  - "Run-scoped events (run_opened and run_closed, both reasons) are pinned to iteration 0 in the ledger schema, following RESEARCH assumption A4; iteration-scoped kinds accept any iteration of at least 0 as the plan states"
  - "ledger.create and ledger.append take record mappings; header_record and event_record build them; the typed Header, Event and Ledger are read-side results with to_json round trips"
  - "TornTail.last_lf_offset is the byte offset of the last LF (-1 when the file has none) and trailing_bytes the count after it"
  - "ledger.append refuses a missing ledger and a ledger whose last byte is not LF (Pitfall 2) after reading one byte, not the whole file"

patterns-established:
  - "Schema copies inside another schema are generated once and pinned by an equality test, so the two copies cannot drift"
  - "A promotion lands in the commit that adds the code it guards: A-6 with create_run_dir, A-3 ledger half and A-6 extension with the ledger"

requirements-completed: [RUN-01, RUN-02, RUN-06]

coverage:
  - id: D1
    description: "Run id <UTC timestamp>-<8 hex> with injected time and token; a path-like id is refused before a path is built; an existing run directory is refused with `run exists; use replay`"
    requirement: RUN-01
    verification:
      - kind: unit
        ref: "tests/test_run_config.py#test_a6_a_rerun_gets_a_new_run_id"
        status: pass
      - kind: unit
        ref: "tests/test_run_config.py#test_a6_run_directory_refuses_to_be_created_twice"
        status: pass
    human_judgment: false
  - id: D2
    description: "Problem spec validated against a closed schema before it is typed; missing schema_version, form pareto, an extra key, a non-finite threshold, a repeated or shared property are refused"
    requirement: RUN-06
    verification:
      - kind: unit
        ref: "tests/test_run_config.py#test_problem_spec_is_validated_before_it_is_typed"
        status: pass
      - kind: unit
        ref: "tests/test_run_config.py#test_problem_spec_refuses_a_repeated_or_shared_property"
        status: pass
      - kind: unit
        ref: "tests/test_run_config.py#test_problem_spec_property_enum_equals_the_registry_schema_enum"
        status: pass
    human_judgment: false
  - id: D3
    description: "canonical_bytes and pretty_bytes fixed by their separators; loads_strict refuses repeated keys and non-finite constants"
    requirement: RUN-02
    verification:
      - kind: unit
        ref: "tests/test_run_config.py#test_canonical_and_pretty_bytes"
        status: pass
      - kind: unit
        ref: "tests/test_run_config.py#test_strict_json_refuses_repeated_keys_and_non_finite_constants"
        status: pass
    human_judgment: false
  - id: D4
    description: "Append-only ledger: exclusive create, one fsynced canonical line per append with the previous bytes a strict prefix, strict byte-level reader with the LF rule, per-line schema and contiguous seq"
    requirement: RUN-02
    verification:
      - kind: unit
        ref: "tests/test_run_ledger.py#test_a6_ledger_refuses_to_be_created_twice"
        status: pass
      - kind: unit
        ref: "tests/test_run_ledger.py#test_a6_every_append_keeps_the_previous_bytes_as_a_prefix"
        status: pass
      - kind: unit
        ref: "tests/test_run_ledger.py#test_read_returns_the_header_and_events_and_requires_the_final_lf"
        status: pass
    human_judgment: false
  - id: D5
    description: "Ledger schema: header and seven event kinds, closed objects, population arrays admitted in run_opened only, a cost of exactly evals and cpu_hours, embedded defs equal their sources"
    requirement: RUN-02
    verification:
      - kind: unit
        ref: "tests/test_run_ledger.py#test_a3_ledger_schema_keeps_the_two_currencies_apart"
        status: pass
      - kind: unit
        ref: "tests/test_run_ledger.py#test_ledger_schema_accepts_one_event_of_each_kind_and_confines_the_populations"
        status: pass
      - kind: unit
        ref: "tests/test_run_ledger.py#test_embedded_definitions_equal_their_sources"
        status: pass
    human_judgment: false
  - id: D6
    description: "Fifth import contract (llm4pol.run never imports llm4pol.loop or llm4pol.llm) declared with the package and kept: Contracts: 5 kept, 0 broken."
    verification:
      - kind: integration
        ref: "tests/test_import_boundary.py#test_a1_contracts_are_declared_and_kept_by_the_gate_argv"
        status: pass
      - kind: other
        ref: "pixi run --manifest-path env/pixi.toml check -> SUMMARY: 7/7 steps passed"
        status: pass
    human_judgment: false

duration: 25min
completed: 2026-09-30
status: complete
---

# Phase 4 Plan 01: The Run Record Library Summary

**Append-only JSONL ledger with fsynced canonical lines, a strict byte-level reader, a self-contained ledger schema and a closed problem-spec schema, under a fifth import contract that landed with the `llm4pol.run` package; A-6 and the ledger half of A-3 are now named tests.**

## Performance

- **Duration:** 25 min
- **Started:** 2026-09-30T07:10:00Z (first commit 16:14 +0900)
- **Completed:** 2026-09-30T07:26:00Z
- **Tasks:** 2 (each RED then GREEN)
- **Files modified:** 14 (10 created, 4 modified)

## Accomplishments

- `llm4pol.run.ids`, `jsonio`, `config` and `ledger` exist and are re-exported from the package root; `pyproject.toml [tool.importlinter]` has five contracts and the gate prints `Contracts: 5 kept, 0 broken.`
- Both schemas of the charter M3 freeze are written before anything can run: `protocol/schemas/problem-spec.json` (closed, `schema_version` const 1, `form` enum `constrained_single` only) and `protocol/schemas/ledger-event.json` (header plus seven event kinds, self-contained, populations confined to `run_opened`, cost closed to `evals` and `cpu_hours`).
- The ledger is an append-only file: `create` opens with `xb`, `append` validates, writes one canonical line in one call and fsyncs, and after every append the previous bytes are a strict prefix (F-40); `read` works on bytes and refuses a torn tail, a repeated key, a non-finite constant, a schema violation and a `seq` that is not its line index.
- A-6 (four `test_a6_*` tests) and the ledger half of A-3 (`test_a3_ledger_schema_keeps_the_two_currencies_apart`) are guards named in `docs/governance/INVARIANTS.md`, each added in the commit that adds the code it guards.

## Task Commits

1. **Task 1 RED** - `660d5d9` (test): run id, strict JSON, problem spec and five-contract import-boundary expectations
2. **Task 1 GREEN** - `b63c4ed` (feat): the run package under its contract, problem-spec schema, A-6 promoted
3. **Task 2 RED** - `864bfb5` (test): failing ledger guards
4. **Task 2 GREEN** - `48910ec` (feat): the ledger, its schema, A-6 extended, A-3 ledger guard promoted

**Plan metadata:** recorded by the closing docs commit.

Gate at both feature commits: `Contracts: 5 kept, 0 broken.` and `SUMMARY: 7/7 steps passed` (196 tests at `b63c4ed`, 206 at `48910ec`).

## Public Names As Built (for plan 04-02)

| Module | Public names |
|---|---|
| `llm4pol.run.ids` | `RUN_ID_PATTERN` (compiled, use `.fullmatch`), `new_run_id(now, token)`, `require_run_id(text)`, `RunIdError` (ValueError), `format_ts(now)`, `utc_now()` (UTC, microseconds dropped), `random_token()`, `Clock` (`Callable[[], datetime]`) |
| `llm4pol.run.jsonio` | `canonical_bytes(record)`, `pretty_bytes(record)`, `loads_strict(text)`, `StrictJsonError` (ValueError) |
| `llm4pol.run.config` | `Objective`, `Constraint`, `Budget`, `ProblemSpec` (`to_json()`, `evals_limit`, `property_keys()`, `schema_version`), `ProblemSpecError` (ValueError), `parse_problem_spec(payload)`, `load_problem_spec(path)`, `RunExists` (FileExistsError, message `run exists; use replay`), `create_run_dir(experiments, run_id)`; also `SCHEMA_DIR`, `PROBLEM_SCHEMA_PATH`, `problem_validator()` |
| `llm4pol.run.ledger` | `LEDGER_NAME` (`ledger.jsonl`), `EVENT_KINDS` (tuple of seven), `Header` (`run_id, problem, seed, snapshot, registry_version, selector, code_git_sha, schema_version`; `to_json`, `from_json`), `Event` (`seq, ts, run_id, iteration, event, payload`; `to_json`, `from_json`), `Ledger` (`header, events`, `problem`, `closed`), `LedgerError`, `TornTail` (`last_lf_offset`, `trailing_bytes`), `LedgerFormatError`, `LedgerIntegrityError`, `header_record(run_id, problem, *, selector, code_git_sha, snapshot, registry_version)`, `event_record(seq, ts, run_id, iteration, kind, payload)`, `create(path, header_record)`, `append(path, event_record)`, `read(path)`, and an addition beyond the plan, `parse_bytes(raw, *, source)`, which is what `read` calls and what a reducer given bytes can call |

`tests/run_support.py`: `FIXED_NOW`, `FIXED_TOKEN`, `FIXED_RUN_ID`, `FIXED_TS`, `FIXED_CODE_SHA`, `SNAPSHOT_ID`, `constant_clock()`, `charter_problem(iterations, candidates_per_beam, beams)`, and the ledger builders `valid_header`, `valid_cost`, `valid_result`, `valid_payload(kind)`, `valid_event(kind, seq, *, iteration, payload)`, `one_event_of_each_kind()`, `EVENT_KINDS`, `CANDIDATE_A/B/C`.

## Files Created/Modified

- `src/llm4pol/run/ids.py` - run id, clock, token, `require_run_id` gate
- `src/llm4pol/run/jsonio.py` - the two byte forms and the strict reader (stdlib only)
- `src/llm4pol/run/config.py` - problem spec dataclasses, validation, `create_run_dir`
- `src/llm4pol/run/ledger.py` - 349 lines: writer, reader, typed records, per-part schema validators
- `src/llm4pol/run/__init__.py` - docstring stating the charter section 6 boundary, re-exports
- `protocol/schemas/problem-spec.json` - closed spec schema, no internal `$ref` so it embeds verbatim
- `protocol/schemas/ledger-event.json` - self-contained header and event schema
- `pyproject.toml` - the fifth contract; `scripts/check.py` - comment only
- `docs/governance/INVARIANTS.md` - A-6 row, A-3 ledger guard, preamble
- `tests/run_support.py`, `tests/test_run_config.py`, `tests/test_run_ledger.py`, `tests/test_import_boundary.py`

## Decisions Made

- `run_closed` is pinned to `iteration` 0 for both reasons, not only `budget_exhausted`. The plan sentence attaches "with `iteration` const 0" to the `budget_exhausted` clause, but RESEARCH A4 (run-scoped events use iteration 0) and the tracer order of plan 04-02 make one rule for the kind the simpler and safer reading. If plan 04-05 needs a `completed` close at another iteration, that is a new schema version.
- `TornTail.last_lf_offset` is the offset of the last LF byte itself (-1 if none), the literal reading of the plan; the length of the valid prefix is `last_lf_offset + 1`.
- Writers take record mappings so the schema, not a dataclass constructor, is the gate.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] Non-finite threshold refused after schema validation**
- **Found during:** Task 1 (`parse_problem_spec`)
- **Issue:** `{"type": "number"}` accepts a Python `nan` (F-54), so a payload dict built in memory with a NaN threshold would validate; `loads_strict` only protects the file path.
- **Fix:** `_refuse_what_a_schema_cannot_say` checks `math.isfinite` on every constraint value, plus the repeated-property and objective-as-constraint refusals the plan names.
- **Files modified:** `src/llm4pol/run/config.py`
- **Verification:** `test_problem_spec_is_validated_before_it_is_typed` (in-memory NaN and file NaN), `test_problem_spec_refuses_a_repeated_or_shared_property`
- **Committed in:** `b63c4ed`

**2. [Rule 2 - Missing critical functionality] `append` refuses a missing ledger and a torn tail**
- **Found during:** Task 2 (`ledger.append`)
- **Issue:** `open("ab")` creates a missing file, and appending after a missing final LF glues two objects on one line (Pitfall 2); the plan lists neither refusal.
- **Fix:** `append` validates first, then checks that the file exists and that its last byte is LF (one byte read); otherwise `LedgerError` or `TornTail`. Nothing is written in either case.
- **Files modified:** `src/llm4pol/run/ledger.py`, `tests/test_run_ledger.py` (`test_append_needs_an_existing_ledger_that_ends_in_a_line_feed`)
- **Committed in:** `48910ec`

**3. [Rule 2 - Missing critical functionality] `ledger` also imports `llm4pol.run.ids`**
- **Found during:** Task 2
- **Issue:** the plan lists the imports of `ledger.py` as the standard library, `jsonschema`, `jsonio`, `config` and `data.snapshot`. The schema pattern `^...$` accepts a trailing newline under Python's `re.search`, so `read` also calls `ids.require_run_id` on the header run id.
- **Fix:** one import of a sibling stdlib-only module; `data.snapshot` arrives through `config.SCHEMA_DIR`, not a direct import. The import contract is unaffected.
- **Committed in:** `48910ec`

**4. Extra tests beyond the plan's six per task**
`test_problem_spec_refuses_a_repeated_or_shared_property`, `test_append_needs_an_existing_ledger_that_ends_in_a_line_feed`, `test_read_refuses_a_missing_header_a_second_header_and_a_foreign_run`, `test_ledger_schema_closes_the_envelope_and_the_payload_rules` and `test_header_and_event_record_builders_match_the_schema` cover behaviour the action text specifies but the behavior list did not name.

---

**Total deviations:** 3 auto-fixed (all Rule 2), 1 note on extra tests.
**Impact on plan:** additive hardening inside the plan's own files; no scope creep and no file outside `files_modified`.

## TDD Gate Compliance

Both tasks have a `test(04-01)` commit before the `feat(04-01)` commit. The RED state of each is a **collection error by the plan's design** (the test module imports `llm4pol.run` or `llm4pol.run.ledger`, which did not exist), not an assertion failure; `check tdd-red-evidence` would classify it INVALID_RED, as recorded for Plan 02-01. The import-boundary expectations of Task 1 did fail on assertions (`4 kept` against the expected 5). The plan sets `type: execute`, so the TDD mode gate was not active. No refactor commit was needed.

## Issues Encountered

- A Python helper script rewrote `tests/test_import_boundary.py` with CRLF on Windows (`Path.write_text` translation); found through git's line-ending warning, normalised to LF (the repository's `.gitattributes` convention) before the GREEN commit. Later scripts wrote bytes.
- Ruff's isort placed `from conftest import` and `from run_support import` inside the first-party block; `ruff check --fix` reordered them.

## Known Stubs

None. The scan of `src/llm4pol/run/`, the three test files and `tests/run_support.py` found no TODO, FIXME, placeholder or skipped test.

## Threat Flags

None. The threats T-04-01..T-04-06 of the plan's register are mitigated as planned; no new network, auth or trust-boundary surface was added.

## Next Phase Readiness

Plan 04-02 (the tracer) can build on the names above. Open notes for it: `ledger.create` and `ledger.append` take records, not typed objects; `ids.utc_now()` drops microseconds so a run id and every `ts` agree to the second; `ids.RUN_ID_PATTERN` is compiled, so use `.fullmatch`. The `problem-spec.json` and `ledger-event.json` schemas are not yet in the `[tool.llm4polcheck]` inventory: their committed examples arrive in plan 04-04.

## Self-Check: PASSED

- All ten created files exist on disk; the four commits `660d5d9`, `b63c4ed`, `864bfb5`, `48910ec` are in `git log`.
- Plan verification re-run: the 4 named Task 1 tests pass, the 3 named Task 2 tests pass, `lint-imports` prints `Contracts: 5 kept, 0 broken.` once, `ls src/llm4pol | grep -cE "^(loop|llm)$"` prints 0, the A-6 and A-3 rows name `tests/test_run_ledger.py` (2 lines), the two schemas pass `check_schema`, `docs/MASTER-PLAN.md` is untouched, `ledger.py` is 349 lines (limit 400).
- Full gate at the final feature commit: `SUMMARY: 7/7 steps passed`.
