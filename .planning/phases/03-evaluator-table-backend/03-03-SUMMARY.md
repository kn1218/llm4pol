---
phase: 03-evaluator-table-backend
plan: 03
subsystem: evaluate
tags: [import-linter, layers-contract, forbidden-contract, invariants, real-file, pytest, ci, workflow_dispatch, evidence]

# Dependency graph
requires:
  - phase: 03-evaluator-table-backend
    provides: "03-01: `Evaluator`, `TableBackend`, `PropertyTable`, the CLI, `conftest.real_candidates`; 03-02: `JsonlCache`, `BudgetMeter`, `--cache` / `--evals-limit`, the A-3 row in INVARIANTS.md; Phase 2: the single `llm4pol.data` import-linter contract and `check.lint_imports_argv()`"
provides:
  - "`pyproject.toml [tool.importlinter]`: four contracts -- the Phase 2 `llm4pol.data` contract unchanged; `A-1: llm4pol.evaluate never imports llm4pol.loop, llm4pol.llm or llm4pol.run (charter section 6)` (forbidden); `A-2: llm4pol.loop never imports llm4pol.evaluate.backends.radonpy (ADR-0003, charter section 6)` (layers, both optional: `[\"(llm4pol.evaluate.backends.radonpy)\", \"(llm4pol.loop)\"]`); `A-1: only llm4pol.loop.agents may import llm4pol.llm (charter section 6, EVAL-06)` (forbidden, wildcard source `llm4pol.*`, four `ignore_imports`, `unmatched_ignore_imports_alerting = \"none\"`) -- the gate prints `Contracts: 4 kept, 0 broken.`"
  - "`tests/test_import_boundary.py` (5 tests): exact-module declaration test, the gate-argv KEPT test, two guard-on-the-guard negative probes on a scratch copy (A-2 BROKEN with `llm4pol.loop -> llm4pol.evaluate.backends.radonpy`; the llm rule BROKEN with `llm4pol.loop.problem -> llm4pol.llm` and KEPT when only `loop.agents` imports it), the no-backend-import / no-stub AST test"
  - "`docs/governance/INVARIANTS.md`: A-1 and A-2 rows before A-3 (architecture table now A-1, A-2, A-3, A-7); preamble names the landed guards"
  - "`tests/test_evaluate_real_file.py` (4 tests, skip without the parquet): snapshot metadata == `TableBackend.source`; 100 pinned ids x 3 properties -> 300 results in request order, `ok` / `missing` only, `evaluate` under 1.0 s after the load, `evals` == distinct `ok` candidates <= 100; the same request again fully cached with `evals` 0; the CLI with `--cache` exits 0 twice with a 300-line JSONL"
  - "`.planning/phases/03-evaluator-table-backend/03-EVIDENCE.md`: charter section 13 M2 (1)-(5) each paired with commands and verbatim output, the counts-only real CLI line, the CI run id / head sha / both job conclusions, the owner flags and the data-policy section"
  - "CI run 35661233933 (`workflow_dispatch`, `main`, head `a5e854dc6ede48caebb81fe82da54afb88e65ce3`): `check (windows-latest): success`, `check (ubuntu-latest): success`, both `SUMMARY: 7/7 steps passed`, `Contracts: 4 kept, 0 broken.`, `164 passed, 16 skipped`"
affects: [03-verification (VERIFICATION.md is written from 03-EVIDENCE.md), 05-loop (A-2 may be rewritten as `forbidden` once `llm4pol.loop` exists; the llm rule already covers `loop.problem`), 06-llm (the converse `llm` imports nothing of `llm4pol` contract), owner (EVAL-06 vs R-1 flag)]

# Actuals (#2632) — chars/4 over the realized diff (37,739 bytes of added/removed lines), never a harness token count.
actuals:
  tokens: 9435
  tasks: 3
  commits: 4
plan_head_before: c8e38cc7f92841f61bc804e185b158e6d58332c1

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Guard-on-the-guard (RESEARCH Pattern 7): a contract that is KEPT because its modules are absent is proven live by copying `src/llm4pol` to `tmp_path` (`shutil.copytree(..., ignore=shutil.ignore_patterns(\"__pycache__\"))`), writing the violating module there, writing a probe TOML holding the contract read back from `pyproject.toml`, and running the same `check.lint_imports_argv([\"--config\", probe])` with `PYTHONPATH=<tmp>/src` -- the repository tree is never touched"
    - "Optional-layers form for a contract whose source package does not exist yet (F-19 / F-22): `type = \"layers\"` with both layers in parentheses; `forbidden` with an absent source is a hard error and a wildcard source misses `__init__.py`"
    - "Real-file evidence reduced to counts before quoting: the request is built in a temporary directory from ids read off the parquet at run time, and the response is piped through a one-liner printing `len(results)`, `cost` and the sorted status set"
    - "Evidence `-v` runs use `-v -v` because `addopts = \"-q\"` cancels one `-v` (Phase 2 convention, kept)"

key-files:
  created:
    - tests/test_import_boundary.py
    - tests/test_evaluate_real_file.py
    - .planning/phases/03-evaluator-table-backend/03-EVIDENCE.md
  modified:
    - pyproject.toml
    - scripts/check.py
    - docs/governance/INVARIANTS.md

key-decisions:
  - "The third contract (`only llm4pol.loop.agents may import llm4pol.llm`) was added per REQUIREMENTS.md EVAL-06, which outranks 03-CONTEXT.md R-1's deferral to Phase 6 (CLAUDE.md precedence; ADR-0002); recorded as an owner flag in the plan, this summary and the evidence -- reversal is one TOML block and one test"
  - "Contract names for the three new blocks are ASCII (`charter section 6`) so the gate's console rendering is clean on cp949; the Phase 2 name keeps its `§`, which the console shows as replacement characters (pre-existing, noted in the evidence)"
  - "The probe TOML is generated from the contract read back from `pyproject.toml` (same name, type, modules) rather than a hand-copied literal, so the negative probe cannot drift from the declared contract"
  - "Commits made directly on `main` under the orchestrator's sequential instruction with `branching_strategy: none`, as every prior plan; the protected-branch probe answers true for `main` and no override key exists in config -- recorded, not resolved"

patterns-established:
  - "`tests/test_import_boundary.py` helpers: `_importlinter()`, `_contract(section, prefix)`, `_run_linter(extra, cwd=, pythonpath=)`, `_scratch_copy(tmp_path)`, `_probe_toml(tmp_path, contract)` -- a Phase 5 / 6 plan that adds a contract adds one prefix constant and one probe"
  - "`tests/test_evaluate_real_file.py` helpers: `_first_ids(path)`, `_request_payload(ids)`, `_assert_real_batch_shape(response, request)` -- a later real batch reuses the shape assertion"

requirements-completed: [EVAL-05, EVAL-06]

coverage:
  - id: D1
    description: "Four import-linter contracts declared with the exact modules; the gate's own argv reports `Contracts: 4 kept, 0 broken.` with four KEPT lines and no BROKEN"
    requirement: EVAL-06
    verification:
      - kind: unit
        ref: "tests/test_import_boundary.py#test_a1_a2_contracts_are_declared_with_exact_modules"
        status: pass
      - kind: integration
        ref: "tests/test_import_boundary.py#test_a1_contracts_are_declared_and_kept_by_the_gate_argv"
        status: pass
      - kind: other
        ref: "PYTHONPATH=src pixi run --manifest-path env/pixi.toml lint-imports | grep -c 'Contracts: 4 kept, 0 broken.' -> 1; grep -c '(llm4pol.evaluate.backends.radonpy)' pyproject.toml -> 1"
        status: pass
    human_judgment: false
  - id: D2
    description: "The absent-module contracts are live: A-2 reports BROKEN with `llm4pol.loop -> llm4pol.evaluate.backends.radonpy` on a violating scratch copy; the llm rule reports BROKEN with `llm4pol.loop.problem -> llm4pol.llm` and stays KEPT when only `loop.agents` imports `llm`; no stub or Phase 5/6 package exists in the repository"
    requirement: EVAL-06
    verification:
      - kind: unit
        ref: "tests/test_import_boundary.py#test_a2_layers_guard_breaks_on_a_violating_import"
        status: pass
      - kind: unit
        ref: "tests/test_import_boundary.py#test_llm_rule_breaks_when_a_non_agents_module_imports_llm"
        status: pass
      - kind: unit
        ref: "tests/test_import_boundary.py#test_evaluate_package_init_imports_no_backend_and_no_radonpy_stub_exists"
        status: pass
      - kind: other
        ref: "ls src/llm4pol/evaluate/backends/ src/llm4pol/ | grep -cE '^(radonpy\\.py|loop|llm|run)$' -> 0"
        status: pass
    human_judgment: false
  - id: D3
    description: "A-1 and A-2 promoted: INVARIANTS.md rows before A-3 naming the contracts, the schema `provenance_tier` field and the tests; the charter is untouched"
    requirement: EVAL-06
    verification:
      - kind: other
        ref: "sed -n '/^| A-1 /p;/^| A-2 /p' docs/governance/INVARIANTS.md | grep -c tests/test_import_boundary.py -> 2; git show --stat --format= 2d9444f 9f8a2ab | grep -c MASTER-PLAN -> 0; git status --porcelain -- docs/MASTER-PLAN.md -> empty"
        status: pass
    human_judgment: false
  - id: D4
    description: "On the pinned parquet: 100 entries x 3 properties -> 300 results in request order, statuses `ok` / `missing` (`value_absent`) only, `evaluate` 0.012 s after a 0.03 s load, `evals` 99 == distinct `ok` candidates, schema-valid; the second identical batch fully cached with `evals` 0 and the meter unchanged; the CLI with `--cache` exits 0 twice with a 300-line JSONL unchanged on the second run; the tests skip with the stated reason in CI (16 skipped = 12 + 4)"
    requirement: EVAL-05
    verification:
      - kind: integration
        ref: "tests/test_evaluate_real_file.py#test_real_table_backend_source_matches_the_parquet_snapshot_metadata"
        status: pass
      - kind: integration
        ref: "tests/test_evaluate_real_file.py#test_real_batch_of_100_returns_300_results_in_request_order"
        status: pass
      - kind: integration
        ref: "tests/test_evaluate_real_file.py#test_real_second_identical_batch_is_fully_cached_with_zero_evals"
        status: pass
      - kind: integration
        ref: "tests/test_evaluate_real_file.py#test_real_cli_batch_of_100_exits_0_with_a_schema_valid_response"
        status: pass
      - kind: other
        ref: "pixi run evaluate --request <tmp>/request.json --root . | counts one-liner -> `300 {'cpu_hours': 0.0, 'evals': 99} ['missing', 'ok']`; grep 16-hex on the test file -> 0; git status --porcelain -- data/ -> empty"
        status: pass
    human_judgment: false
  - id: D5
    description: "The seven-step gate is green locally (180 passed) and in the dispatched CI run 35661233933 on windows-latest and ubuntu-latest (164 passed, 16 skipped, `Contracts: 4 kept, 0 broken.`, `llm4polcheck inventory: 3 entries, 3 instances processed` on both); 03-EVIDENCE.md pairs charter section 13 M2 (1)-(5) with commands and outputs, carries the owner flags and contains no real candidate id"
    requirement: EVAL-05
    verification:
      - kind: other
        ref: "gh run view 35661233933 --json event,headBranch,conclusion,jobs -> `workflow_dispatch main success check (ubuntu-latest)=success,check (windows-latest)=success`; --log grep counts: SUMMARY 2, Contracts 2, inventory 2"
        status: pass
      - kind: other
        ref: "grep -c '^## (' 03-EVIDENCE.md -> 5; grep -c 'Owner flags' -> 1; the 16-hex leak check -> 0; git status --porcelain --branch -> `## main...origin/main`"
        status: pass
    human_judgment: false

# Metrics
duration: 13min
completed: 2026-09-22
status: complete
---

# Phase 3 Plan 03: Import boundary frozen, real-file proof and M2 evidence Summary

**The import boundary is frozen by four import-linter contracts inside the gate (`Contracts: 4 kept, 0 broken.`) whose absent-module forms are proven live by negative probes on a scratch copy, A-1 and A-2 are guards named in INVARIANTS.md, a batch of 100 pinned candidates x 3 properties returns 300 ordered results in 0.012 s with a fully cached second batch and a green CLI run, and CI run 35661233933 is green on both platforms with the real-file tests skipping by design -- all recorded in 03-EVIDENCE.md against charter section 13 M2 (1)-(5).**

## Performance

- **Duration:** 13 min
- **Started:** 2026-09-21T22:01:27Z
- **Completed:** 2026-09-21T22:14:30Z (UTC; 2026-09-22 local)
- **Tasks:** 3
- **Files modified:** 6 (3 created, 3 modified)

## Accomplishments

- Charter section 13 M2 (5) complete: `pyproject.toml [tool.importlinter]` holds the Phase 2 contract plus A-1 (forbidden), A-2 (optional layers `["(llm4pol.evaluate.backends.radonpy)", "(llm4pol.loop)"]`) and the `loop.agents`-only llm rule (wildcard source, four `ignore_imports`); the gate's `import-linter` step prints four KEPT lines and `Contracts: 4 kept, 0 broken.` (was `1 kept`).
- The guards are not vacuous: `test_a2_layers_guard_breaks_on_a_violating_import` gets returncode 1, `BROKEN` and the chain `llm4pol.loop -> llm4pol.evaluate.backends.radonpy` from a scratch copy whose `loop/__init__.py` imports the stub; `test_llm_rule_breaks_when_a_non_agents_module_imports_llm` gets `BROKEN` with `llm4pol.loop.problem -> llm4pol.llm` and, on a second copy where only `loop/agents/__init__.py` imports it, returncode 0 with `KEPT`. The repository holds no `radonpy.py`, `loop`, `llm` or `run` before or after (Test 5 and the `ls | grep -c` -> 0).
- A-1 and A-2 promoted in `docs/governance/INVARIANTS.md` (rows before A-3; the architecture table reads A-1, A-2, A-3, A-7); the charter file is untouched in both Task 1 commits.
- Charter section 13 M2 (2) and (3) reproduced on the pinned table: `300 {'cpu_hours': 0.0, 'evals': 99} ['missing', 'ok']` for the first 100 candidate ids x 3 properties (99 distinct candidates with at least one `ok`; one candidate is `missing` on all three); `evaluate` 0.012 s after a 0.03 s full-table load (F-09, F-10); the second identical request every `cached: true`, `Cost(0, 0.0)`, meter unchanged; the CLI run with `--cache` exits 0 twice, 300 JSONL lines both times.
- Gate: local `SUMMARY: 7/7 steps passed` with **180 tests** (171 after 03-02 + 5 + 4; the plan's floor was 161); CI run 35661233933 (`workflow_dispatch`, `main`, head `a5e854d`) `check (windows-latest): success`, `check (ubuntu-latest): success`, both `164 passed, 16 skipped` (12 Phase 2 + 4 Phase 3 real-file tests) with `Contracts: 4 kept, 0 broken.` and `llm4polcheck inventory: 3 entries, 3 instances processed`.

## Task Commits

Each task was committed atomically:

1. **Task 1: four contracts, guard-on-the-guard, A-1 / A-2** -- `2d9444f` (test, RED: `4 failed, 1 passed in 0.46s` -- Tests 1-4 failed on the single Phase 2 contract, Test 5 passed) -> `9f8a2ab` (feat, GREEN; 176 tests)
2. **Task 2: real-file batch of 100, cached second batch, CLI run** -- `a5e854d` (test; 180 tests; the plan specifies one commit -- the tests pin existing 03-01 / 03-02 behaviour on the real table and needed no source change)
3. **Task 3: push, CI on both platforms, evidence** -- pushed tip `a5e854d`; `docs` commit `9977536` (`docs(03-03): record Phase 3 M2 evidence (charter section 13 M2 (1)–(5), CI run 35661233933)`), pushed; no `fix(03-03)` commit was needed (the first dispatched run was green)

**Plan metadata:** see the final `docs(03-03): complete …` commit.

The evidence commit `9977536` post-dates the cited CI run, which ran on `a5e854d` (the evidence file itself is under `.planning/`, excluded from every gate step but the history scan).

## Files Created/Modified

- `pyproject.toml` -- three `[[tool.importlinter.contracts]]` blocks after the Phase 2 contract with the explanatory comments of RESEARCH Code Example 3 (F-18, F-19, F-21, F-22, F-23; Phase 5 may rewrite A-2 as `forbidden`; the converse llm rule lands in Phase 6; the third block's comment states the EVAL-06-over-R-1 precedence and the owner flag); the Phase 2 block's trailing comment is now past tense.
- `scripts/check.py` -- the stale "zero contracts" comment in `step_import_linter` replaced (no code change).
- `docs/governance/INVARIANTS.md` -- A-1 row (schema `provenance_tier`, the two A-1 contracts, `test_a1_contracts_are_declared_and_kept_by_the_gate_argv`, `test_every_result_carries_backend_source_and_provenance_tier`), A-2 row (the layers contract, `test_a1_a2_contracts_are_declared_with_exact_modules`, `test_a2_layers_guard_breaks_on_a_violating_import`); preamble sentence names A-1, A-2 (M2), A-3 (M2 guard; M3 ledger guard pending), A-7 (M1).
- `tests/test_import_boundary.py` (new, 5 tests, 237 lines) -- see Accomplishments.
- `tests/test_evaluate_real_file.py` (new, 4 tests, 186 lines) -- module docstring states the skip contract, the no-edited-number rule and the no-id-leaves-`tmp_path` rule; the measured wall times are in a comment.
- `.planning/phases/03-evaluator-table-backend/03-EVIDENCE.md` (new) -- sections (1)-(5), `## Gate and CI`, `## Owner flags`, `## Data policy`.

## Decisions Made

- **EVAL-06 third clause over CONTEXT R-1** (owner flag (a) below): the plan's objective spells out the precedence; the contract costs one block and is proven live.
- **Probe TOML generated from the declared contract**: `_probe_toml` serialises the contract dict read from `pyproject.toml`, so the negative probe tests the block that ships rather than a copy that could drift.
- **`-v -v` in the evidence commands**: the plan writes `-v`; with `addopts = "-q"` one `-v` prints no PASSED lines (verified), so the Phase 2 convention `-v -v` is used and stated in the evidence header.
- **Task 2 warm-up through `evaluator.backend.lookup(ids[0], "tg")`** as the plan specifies; the timed region is `evaluate` only. The 1.0 s budget is two orders of magnitude above the measured 0.012 s, so the assertion cannot flake on a slow CI machine even if the parquet were present there.

## Deviations from Plan

### Auto-fixed Issues

None.

### Recorded deviation (as the plan instructs)

**[Precedence] The `only llm4pol.loop.agents may import llm4pol.llm` contract was added although 03-CONTEXT.md R-1 defers it to Phase 6.** REQUIREMENTS.md EVAL-06 names the clause; REQUIREMENTS.md outranks a phase CONTEXT file (CLAUDE.md § Source of truth and precedence; ADR-0002). The plan's objective, this summary and `03-EVIDENCE.md` § Owner flags (a) all record it; reversal is one TOML block and one test (`test_llm_rule_breaks_when_a_non_agents_module_imports_llm`, plus the third-contract assertions and the count `4` in `test_a1_a2_contracts_are_declared_with_exact_modules`).

**Total deviations:** 0 auto-fixed; 1 recorded precedence deviation carried as an owner flag. **Impact on plan:** none beyond the flagged contract; no test was weakened, no source behaviour changed to satisfy a check.

## Issues Encountered

- pytest's `-v` produces no per-test lines under this project's `addopts = "-q"`; the RED evidence and the evidence file use `-v -v` (the RED commit message quotes the `4 failed, 1 passed` summary line, which `-v` does print).
- The Phase 2 contract name's `§` renders as replacement characters when the linter's stdout passes through the cp949 console (pre-existing since Phase 2; the three new names are ASCII so their lines are clean). Noted in the evidence; not changed -- the Phase 2 name is cited by `tests/test_data_invariants.py` and the Phase 2 evidence.
- The `--collect-only -q` check prints `tests/test_evaluate_real_file.py: 4` (the `-q -q` collapsed form) rather than four node ids; four tests are collected either way.

## Owner flags (surfaced for the owner; nothing resolved here)

1. **REQUIREMENTS.md EVAL-06 third clause vs CONTEXT R-1** -- the `loop.agents`-only llm contract added by precedence; one block and one test to reverse (see Deviations).
2. **The D-04 charging edge (RESEARCH Open Question 2)** -- a new property of an already-cached candidate in a later request is charged 1 again; pinned by `test_new_property_of_a_cached_candidate_charges_one_eval` (03-02). The loop's 400-eval arithmetic is unaffected while every request asks the same property set.
3. **Phase 2's evaluator-touching open questions are resolved by D-03** for this phase (no population filter; the 303 twins are distinct ids served as such) -- stated, not decided.

## Known Stubs

None. No placeholder, skipped test, xfail or unimplemented branch was introduced. `backends/radonpy.py`, `llm4pol.loop` / `llm` / `run` do not exist in the repository (Test 5; `ls | grep -c` -> 0); the negative probes write them only under `tmp_path`. The four real-file tests skip in CI by the fixture's stated reason (`processed candidate parquet absent … never committed`), which is the designed behaviour, not a stub; locally all four PASS.

## Threat Flags

None beyond the plan's register. T-03-14 (vacuous KEPT) mitigated by the two negative probes; T-03-15 (stub) by Test 5 and the `ls` check; T-03-16 (real ids) by run-time id reads, the test-file grep -> 0 and the evidence leak check -> 0; T-03-17 (secret in pushed history) by the pre-push gate's history scan (`scanned 67 commit(s)`, every class `0 hit(s)`, `dotenv-path-in-history: 0 hit(s)`); T-03-18 (wrong run cited) by the run-id re-query (`workflow_dispatch main success …`); T-03-19 by the 16 skipped in CI. Data policy: `git ls-files data/` lists the three manifest / README files only; no parquet, CSV, JSONL or request file is tracked.

## Next Phase Readiness

- Phase 3 is complete on all three plans; the Phase 3 verifier writes `VERIFICATION.md` from `03-EVIDENCE.md`.
- Phase 4 (ledger): the A-3 ledger-schema guard is the pending half of that row.
- Phase 5 (loop): may rewrite A-2 as `forbidden` with `source_modules = ["llm4pol.loop"]` once the package exists; the llm rule already forbids `loop.problem -> llm` today.
- Phase 6 (llm): the converse contract (`llm4pol.llm` imports nothing of `llm4pol`) needs `source_modules = ["llm4pol.llm"]`.

## Self-Check: PASSED

Files: `tests/test_import_boundary.py`, `tests/test_evaluate_real_file.py`, `03-EVIDENCE.md`, `03-03-SUMMARY.md` found. Commits `2d9444f`, `9f8a2ab`, `a5e854d`, `9977536` found in history. Final gate after the evidence commit: `180 passed in 43.71s`, `SUMMARY: 7/7 steps passed`.
