---
phase: 04-run-management
plan: 06
subsystem: run-record
tags: [problem-spec, meta-json, redaction, dirty-scope, populations, served-values, adr-0008, d-39]

requires:
  - phase: 04-run-management
    provides: "ledger and schemas (04-01); open_run, drive, reducer, populations, run/replay verbs (04-02); committed run-record examples (04-04); resume from the ledger (04-05)"
provides:
  - "every problem spec the schema or the parser must refuse is refused with ProblemSpecError (23 named cases, non-object payloads, NaN/Infinity/repeated key in text); pareto is refused by name with a message citing the D-16 gate"
  - "config.redact, config.REDACTED, config.BEHAVIOUR_PATHS; write_meta renders redact(meta), validates it against run-meta.json, then writes"
  - "code_identity reads dirty over src, protocol, config, pyproject.toml, env/pixi.toml, env/pixi.lock only"
  - "population.sort_records, a pure total order; members(root, registry, table) refuses a rows parquet of another snapshot"
  - "conftest RUN_EXTRA_CORE, make_synthetic_root(root, extra_core=()), fixture run_extended_candidates: a 16-row, 9-candidate copy on which the two populations differ"
affects: [04-07, 04-08, 04-09, phase-05, phase-06]

plan_head_before: 4cb39442fc43ab172035ae630704598af79e7724
actuals:
  tokens: 7800
  tasks: 2
  commits: 4

tech-stack:
  added: []
  patterns:
    - "meta.json is closed by schema first and by a key-name rule second: a secret-shaped key holds the marker, a boolean records that a provider key exists"
    - "membership from the filter over the rows parquet, values from the candidate parquet by id, in two functions that share nothing but the id"
    - "a fixture that must differ from the shared one extends a copy (extra_core) instead of editing SYNTHETIC_ROWS"

key-files:
  created:
    - tests/test_run_population.py
  modified:
    - src/llm4pol/run/config.py
    - src/llm4pol/run/population.py
    - tests/conftest.py
    - tests/test_run_config.py

key-decisions:
  - "members takes the problem table as a required third argument and refuses a rows parquet whose llm4pol.snapshot metadata differs, so both readers of population.py carry the same guard (plan STEP 2)"
  - "redact returns lists for tuples and a new dict for every mapping; it reads key names only and replaces the value whatever its type, so a number under api_key is redacted and a number under tokens is not"
  - "dirty is computed with git status --porcelain -- <BEHAVIOUR_PATHS>; a pathspec that does not exist in a checkout is silently empty, so a scratch repository without config/ or env/ is not an error"

patterns-established:
  - "A schema-level refusal that needs a better message than the generic one is checked before the validator runs (pareto)"
  - "Scanner-safe secret tests: positive controls are taken from history_secret_scan.PATTERNS at run time, never written as literals"

requirements-completed: [RUN-01, RUN-04, RUN-06]

coverage:
  - id: D1
    description: "every problem spec that must be refused is refused with ProblemSpecError: missing or wrong schema_version, form pareto or weighted_sum, the barred static permittivity key as objective and as constraint, an unregistered key, direction up, op <, a string threshold, a zero budget field (three), a negative or boolean seed, another table, extra keys at four levels, a repeated constraint property, an objective that is constrained, constraints that are not a list, payloads that are not objects; NaN, Infinity, -Infinity and a repeated key in a file; the charter example still parses"
    requirement: RUN-06
    verification:
      - kind: unit
        ref: "tests/test_run_config.py#test_problem_spec_refusals"
        status: pass
      - kind: unit
        ref: "tests/test_run_config.py#test_problem_spec_text_refusals"
        status: pass
      - kind: unit
        ref: "tests/test_run_config.py#test_problem_spec_refuses_a_payload_that_is_not_an_object"
        status: pass
    human_judgment: false
  - id: D2
    description: "form pareto is refused with a message that contains pareto, reserved and D-16"
    requirement: RUN-06
    verification:
      - kind: unit
        ref: "tests/test_run_config.py#test_pareto_is_refused_with_a_message_naming_the_gate"
        status: pass
    human_judgment: false
  - id: D3
    description: "build_meta returns exactly the fifteen keys run-meta.json requires; write_meta refuses each of the fifteen keys removed and sixteen wrong names or types (extra key, dirty as string or integer, seed as boolean, schema_version 2, a 39-character sha, a 63-character snapshot_sha256, provider as a number, and others) before a file exists"
    requirement: RUN-01
    verification:
      - kind: unit
        ref: "tests/test_run_config.py#test_meta_schema_pins_names_and_types"
        status: pass
    human_judgment: false
  - id: D4
    description: "a provider key in the environment is recorded as the boolean true and its value is nowhere in meta.json; PROVIDER_KEY_NAMES equals the _API_KEY names of the example environment file in file order; a secret-shaped key inside prompt_versions is written as ***REDACTED*** and no scanner class matches the file; tokens, max_tokens, token_budget and key survive redaction"
    requirement: RUN-01
    verification:
      - kind: unit
        ref: "tests/test_run_config.py#test_provider_key_is_recorded_as_a_boolean_only"
        status: pass
      - kind: unit
        ref: "tests/test_run_config.py#test_redaction_rule_by_key_name"
        status: pass
      - kind: unit
        ref: "tests/test_run_config.py#test_write_meta_never_writes_a_secret_shaped_value"
        status: pass
    human_judgment: false
  - id: D5
    description: "dirty is False for an untracked planning, experiments or docs file and True for a modified or untracked file under src, protocol, config or pyproject.toml, in a scratch git repository; a directory that is not a repository is refused with CodeIdentityError"
    requirement: RUN-01
    verification:
      - kind: unit
        ref: "tests/test_run_config.py#test_dirty_reads_the_paths_that_define_behaviour_only"
        status: pass
      - kind: unit
        ref: "tests/test_run_config.py#test_behaviour_paths_are_the_ones_the_plan_names"
        status: pass
    human_judgment: false
  - id: D6
    description: "on the extended fixture (16 source rows, 9 candidates) check_tc has 4 members with objective [0.155, 0.18, 0.23, 0.315] and readme_triple 5 with [0.155, 0.18, 0.23, 0.315, 0.4]; the value 0.23 is the served median and 0.2 is absent; arrays are parallel, sorted and carry no id; the shared fixture still yields 14 rows and 8 candidates"
    requirement: RUN-04
    verification:
      - kind: unit
        ref: "tests/test_run_population.py#test_the_extended_fixture_is_what_the_plan_derives"
        status: pass
      - kind: unit
        ref: "tests/test_run_population.py#test_members_follow_the_filter"
        status: pass
      - kind: unit
        ref: "tests/test_run_population.py#test_values_are_the_served_medians_not_the_filtered_ones"
        status: pass
      - kind: unit
        ref: "tests/test_run_population.py#test_populations_are_sorted_parallel_and_carry_no_id"
        status: pass
    human_judgment: false
  - id: D7
    description: "the run on the extended fixture writes a results.csv of 242 bytes, sha256 93f225f9540e5c2f162fd4bebb10279090e37c6382c7892d1e92f832863850cf, with n_population 4 and 5, pct_of_population 75.0 and 60.0, hits 2 and 1 on adjacent rows of one beam"
    requirement: RUN-04
    verification:
      - kind: integration
        ref: "tests/test_run_population.py#test_the_two_populations_are_reported_side_by_side"
        status: pass
    human_judgment: false
  - id: D8
    description: "capture and members raise PopulationError for a problem naming another table, a rows parquet or a candidate parquet whose snapshot metadata names another revision, and an absent rows parquet; sort_records orders by objective then constraints, puts a missing value last and is the same for every permutation"
    requirement: RUN-04
    verification:
      - kind: unit
        ref: "tests/test_run_population.py#test_capture_refuses_a_table_of_another_snapshot"
        status: pass
      - kind: unit
        ref: "tests/test_run_population.py#test_sort_records_puts_nulls_last_and_is_stable_under_ties"
        status: pass
      - kind: other
        ref: "pixi run --manifest-path env/pixi.toml check -> SUMMARY: 7/7 steps passed, 354 tests, Contracts: 5 kept, 0 broken."
        status: pass
    human_judgment: false

duration: 14min
completed: 2026-09-30
status: complete
---

# Phase 4 Plan 06: Problem Spec Refusals, A Meta That Cannot Hold A Key, And Two Populations Shown Apart Summary

**Every problem spec the context says must be refused is refused; `meta.json` is pinned on names and types and cannot carry a key value (key-name redaction before validation, `dirty` over six behaviour paths); and on a 16-row fixture the two ADR-0008 populations differ - 4 and 5 members, one set of served medians - and print side by side in a 242-byte `results.csv`.**

## Performance

- **Duration:** 14 min (about 08:19Z to 08:33Z)
- **Tasks:** 2 (each RED then GREEN)
- **Files:** 1 created, 4 modified

## Accomplishments

- **Task 1.** The refusal matrix has 23 named cases plus non-object payloads, three non-finite texts and a repeated key; `pareto` now fails first with a message naming the D-16 gate. `config.redact` applies the F-48 suffix rule (singular credential word at the end of the name) at any depth and returns a new structure; `write_meta` renders `redact(meta)`, validates it, then writes exclusively. `dirty` is read with `git status --porcelain -- src protocol config pyproject.toml env/pixi.toml env/pixi.lock`, so planning files, `experiments/<run id>/` and docs never make a run dirty and a file under `src/` or `protocol/` always does.
- **Task 2.** `conftest.RUN_EXTRA_CORE` and the `extra_core` argument of `make_synthetic_root` add two rows to a copy: a new candidate `e46d685d3399e6b4` inside the README triple with `check_tc` False, and a second row of `d751b16095852737` whose served TC median is 0.23 while its `check_tc`-passing row alone gives 0.2. `population.sort_records` is public and pure, and `members` (membership, no value) and `capture` (values by id) both refuse a parquet of another snapshot.
- The results of the plan's hand derivation reproduced without an adjustment: objective arrays `[0.155, 0.18, 0.23, 0.315]` and `[0.155, 0.18, 0.23, 0.315, 0.4]`, eps `[2.6100000000000003, 2.25, 2.22, 2.335]`, Tg `[377.5, 400.0, 445.0, 262.5]`.

## Record for the owner

| Item | Value |
|---|---|
| Commit, RED task 1 | `07f7668` test(04-06): add the problem spec refusal matrix and failing meta tests |
| Commit, GREEN task 1 | `150487d` feat(04-06): meta cannot carry a key value |
| Commit, RED task 2 | `f209d59` test(04-06): add the extended synthetic fixture and failing population tests |
| Commit, GREEN task 2 | `4942337` feat(04-06): populations keep membership and served values apart |
| Behaviour paths of `dirty` | `src`, `protocol`, `config`, `pyproject.toml`, `env/pixi.toml`, `env/pixi.lock` |
| `results.csv` of the extended fixture | 242 bytes, sha256 `93f225f9540e5c2f162fd4bebb10279090e37c6382c7892d1e92f832863850cf` |
| Gate | `SUMMARY: 7/7 steps passed`, 354 tests, no scanner hit, at both GREEN commits' tree |
| Schemas | `git diff --stat 4cb3944..HEAD -- protocol/schemas` prints nothing |
| Earlier tests | no earlier test file was edited; `tests/run_support.py` untouched |

## Deviations from Plan

### Auto-fixed Issues

None of Rules 1-3 fired. Two points where the plan text and the tree differ, both recorded rather than resolved silently:

**1. [Rule 2 - Missing critical functionality] `members` gained a required `table` argument**
- **Found during:** Task 2, STEP 2 ("both readers refuse a parquet whose snapshot metadata differs from the problem table")
- **Issue:** only the candidate parquet was checked, in `capture`; `members` read the rows parquet with no snapshot check, so a rows table of another revision would have defined membership silently.
- **Fix:** `members(root, registry, table)` calls the same `_require_table` as `capture`; `capture` passes `problem.table`. Its only caller is `capture`, so no signature that `resume.py` or `__main__.py` calls changed.
- **Files modified:** `src/llm4pol/run/population.py`
- **Commit:** `4942337`

**2. [Note, no change] `src/llm4pol/run/ids.py` is listed in `files_modified` and was not modified**
- Test 9 (`test_run_id_sources`) passed on the code of plans 04-01 and 04-02 as a guard; `random_token`, `utc_now` and `format_ts` already behave as the test states, so no edit was warranted.

**3. [Note] the RED commits do not pass the gate**
- As in plan 04-05, each RED commit holds failing tests by design. At `07f7668` the gate reported `6/7 steps passed` (only `pytest`, five named failures); ruff, ruff format, mypy, import-linter, schema-inventory and history-secret-scan passed. Both GREEN commits were gated at 7/7 before they were made.

**Total deviations:** 1 auto-added (Rule 2), 2 notes. **Impact:** none on scope; the extra check closes a hole the plan's own STEP 2 describes.

## Decisions Made

- `members` requires the problem table (see above).
- Redaction replaces the value of a matched key whatever its type and turns a tuple into a list; the rule reads names, never values (charter section 12, F-50).
- The scratch-repository test passes the author with `-c user.name=... -c user.email=...` and disables signing with `-c commit.gpgsign=false`, so it does not depend on the machine configuration.

## Issues Encountered

- A Windows `Path.write_text` in a helper script wrote CRLF into `config.py` once; `git` normalised it on commit (the commit diff is 58 insertions, 8 deletions) and the files in the tree hold no CR. Later writes used `newline="\n"`.
- The 04-02 note that `dirty` was any porcelain output is now resolved; `meta.json` examples of 04-04 are compared under an injected identity, so `tests/test_run_examples.py` and the byte-identity resume tests of 04-05 stayed green with no regeneration.

## Known Stubs

None. No placeholder text, skipped test or unimplemented branch was added; the `pytest.skip` calls in `tests/conftest.py` belong to the real-file fixtures of earlier plans.

## Threat Flags

None. The plan's threats T-04-28 to T-04-33 are mitigated as registered: T-04-28 by the closed schema, membership-only presence check, `redact` before validation and Tests 5-7; T-04-29 by the suffix rule and Test 6; T-04-30 by Test 4; T-04-31 by Tests 1-3; T-04-32 by Tests 3 and 5 of task 2; T-04-33 by Test 8.

## Next Phase Readiness

Ready for 04-07. `write_meta`, `code_identity` and `population.capture` keep every signature that `resume.py` and `__main__.py` call, apart from the internal `members` argument. Real population sizes (39,454 and 40,212) are for 04-09.

## Self-Check: PASSED

- Created and modified files exist: `tests/test_run_population.py`, `src/llm4pol/run/config.py`, `src/llm4pol/run/population.py`, `tests/conftest.py`, `tests/test_run_config.py`.
- Commits `07f7668`, `150487d`, `f209d59`, `4942337` are in `git log`; `git rev-list --count 4cb39442..HEAD` gave 4 before this SUMMARY.
- Acceptance criteria of both tasks re-run: refusal matrix, meta tests, dirty scope, population tests, schema diff empty, gate 7/7.
