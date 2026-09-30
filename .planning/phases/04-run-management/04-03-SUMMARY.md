---
phase: 04-run-management
plan: 03
subsystem: run-record
tags: [adr-0007, gitignore, check-ignore, governance-test, import-linter, run-contract, experiments-readme]

requires:
  - phase: 04-run-management
    provides: "the llm4pol.run package and its fifth import contract (plan 04-01), the run/replay CLI and run-meta.json (plan 04-02)"
provides:
  - "the ADR-0007 pattern block in .gitignore: the run directory re-included, its contents ignored, four names re-included"
  - "test_run_summaries_are_trackable_and_the_ledger_is_ignored and test_tracked_run_summaries_are_polyomics_runs, both asking git"
  - "experiments/README.md describing the five files of a run directory, the tracking policy, the resume and replay rules"
  - "test_run_contract_breaks_when_run_imports_loop_or_llm: the fifth import contract proven live on two scratch copies"
affects: [04-04, 04-07, 04-08, 04-09, phase-07]

plan_head_before: 4665d41e9f5ad6778d80bfab90d09311ac204a29
actuals:
  tokens: 9000
  tasks: 1
  commits: 2

tech-stack:
  added: []
  patterns:
    - "a guard on an ignore pattern asks git (check-ignore --no-index, ls-files) and never reads .gitignore as text"
    - "a negative probe copies src/llm4pol into a temporary directory and adds the violating module there"

key-files:
  created: []
  modified:
    - .gitignore
    - experiments/README.md
    - README.md
    - CLAUDE.md
    - tests/test_governance.py
    - tests/test_import_boundary.py

key-decisions:
  - "Owner note: the pre-registration file of Phase 7 (experiments/PREREG-<date>.md) is ignored by the new block exactly as it was by the old one (F-70); Phase 7 adds its own re-include. experiments/README.md says so."
  - "experiments/README.md states that run-meta.json exists today and that the schemas of usage.json and run_summary.json arrive in later plans of the phase, so the README does not claim a schema that is not yet in protocol/schemas/"

patterns-established:
  - "A tracked meta.json must name a polyomics: snapshot; the test holds with zero tracked runs and fails on a tracked PoLyInfo-derived run"

requirements-completed: [RUN-01, RUN-04]

coverage:
  - id: D1
    description: "Inside experiments/<run-id>/ git tracks meta.json, usage.json, results.csv and run_summary.json and ignores ledger.jsonl, cache.jsonl, a nested file and a stray top-level file; the test asks git check-ignore"
    requirement: RUN-04
    verification:
      - kind: unit
        ref: "tests/test_governance.py#test_run_summaries_are_trackable_and_the_ledger_is_ignored"
        status: pass
      - kind: other
        ref: "git check-ignore -q --no-index on run_summary.json exits 1 (trackable) and on ledger.jsonl exits 0 (ignored)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Every tracked path under experiments/ is the README or one of the four names directly inside a run-id directory, and every tracked meta.json names a polyomics: snapshot; passes with zero tracked runs"
    requirement: RUN-01
    verification:
      - kind: unit
        ref: "tests/test_governance.py#test_tracked_run_summaries_are_polyomics_runs"
        status: pass
    human_judgment: false
  - id: D3
    description: "CLAUDE.md, README.md and experiments/README.md state the ADR-0007 policy; experiments/README.md describes the five files, resume and replay, the ledger check against the repository"
    requirement: RUN-04
    verification:
      - kind: other
        ref: "grep --count ADR-0007 over the four files prints 1, 1, 1, 2; 'ignored except' survives nowhere; run_summary.json appears 7 times in experiments/README.md"
        status: pass
    human_judgment: true
  - id: D4
    description: "The run contract reports BROKEN with the chain named when a run module imports llm4pol.loop, and when it imports llm4pol.llm; the repository holds neither package before and after"
    verification:
      - kind: integration
        ref: "tests/test_import_boundary.py#test_run_contract_breaks_when_run_imports_loop_or_llm"
        status: pass
      - kind: other
        ref: "pixi run --manifest-path env/pixi.toml check -> SUMMARY: 7/7 steps passed (227 tests)"
        status: pass
    human_judgment: false

duration: 15min
completed: 2026-09-30
status: complete
---

# Phase 4 Plan 03: The Tracking Policy of ADR-0007 and the Live Run Contract Summary

**ADR-0007 is a `.gitignore` block that re-includes the run directory and four summary names, guarded by governance tests that ask `git check-ignore` and `git ls-files` instead of reading the file as text, and the fifth import contract is shown to report BROKEN on two violating scratch copies.**

## Performance

- **Duration:** about 15 min
- **Tasks:** 1 (RED commit, then GREEN commit)
- **Files modified:** 6 (none created)
- **Gate:** `SUMMARY: 7/7 steps passed`, 227 tests, at the GREEN commit

## Accomplishments

- The pattern of the plan's objective is in `.gitignore`, in that order, under a comment that gives the ledger, summary and PoLyInfo reasons. Git now treats `meta.json`, `usage.json`, `results.csv` and `run_summary.json` as trackable and everything else in a run directory, and any stray top-level file, as ignored.
- `git check-ignore -q --no-index` exit codes on the plan's probe paths: `experiments/20260101T000000Z-00000000/run_summary.json` exits **1** (trackable) and `.../ledger.jsonl` exits **0** (ignored), as F-66 requires.
- The old governance test, which read `.gitignore` as text and would have stayed green over the inert pattern (F-64, F-67), is replaced by two tests. Test 1 failed on the old pattern at the RED commit (`meta.json must be trackable`); Tests 2 and 3 passed at once and stay as guards.
- `experiments/README.md` is rewritten: the five-row table of a run directory, why four files are tracked, the `polyomics:` requirement, the rules of `resume` and `replay`, the check of a ledger against `run_summary.json`, development runs, and the pre-registration note.
- `README.md` and `CLAUDE.md` each changed in one line only; no other sentence of either file changed.
- The negative probe writes `loop/__init__.py` plus `run/probe_loop.py` (imports `llm4pol.loop`) into one temporary copy and `llm/__init__.py` plus `run/probe_llm.py` into another; the linter, given the run contract read back from `pyproject.toml`, returns 1 with `llm4pol.run.probe_loop -> llm4pol.loop` and `llm4pol.run.probe_llm -> llm4pol.llm`. The test asserts the repository holds neither package.

## Task Commits

1. **Task 1 RED** - `5485a83` (test): `ask git what is tracked under experiments; probe the run contract (ADR-0007, CONTEXT D-06)`
2. **Task 1 GREEN** - `a325306` (feat): `track run summaries, keep the ledger out of version control (ADR-0007, charter section 10)`

**Plan metadata:** recorded by the closing docs commit.

## Owner Note

The pre-registration file of Phase 7 (`experiments/PREREG-<date>.md`) is ignored by the new block exactly as the old block ignored it (F-70). Phase 7 adds its own re-include; `experiments/README.md` records this so nobody is surprised.

## Decisions Made

- `experiments/README.md` names `run-meta.json` as the schema that exists today and says the schemas of `usage.json` and `run_summary.json` arrive later in the phase. The plan asks the README to state that all three validate; stating it without qualification would have claimed two schemas that plans 04-07 and 04-08 have not yet written. When those plans land, the sentence needs no edit beyond removing the qualification.
- `experiments/README.md` describes `resume` as a rule of the format (ADR-0008 item 7) although the verb arrives with plan 04-05; the rule is the ADR's and is stable.

## Deviations from Plan

None - plan executed exactly as written. `docs/MASTER-PLAN.md`, `docs/governance/ADR` and `docs/governance/DECISIONS-LOG.md` are untouched between the revision before the RED commit and the tip (`git diff --stat` is empty).

## TDD Gate Compliance

`test(04-03)` (`5485a83`) precedes `feat(04-03)` (`a325306`). The RED state is an assertion failure on Test 1 (`AssertionError: meta.json must be trackable (ADR-0007)`), a genuine behavioural RED. The plan sets `type: execute`, so the TDD mode gate was not active. No refactor commit was needed.

## Issues Encountered

- My first edit of the new probe test collapsed the `\n` of a scratch module's text into a literal line break (a shell and Python escaping slip), which broke collection until fixed; caught by the first test run, before any commit.
- The working copies of `.gitignore` and `CLAUDE.md` carry CRLF; git warns that they will be normalised to LF. This is the repository's existing `.gitattributes` behaviour and the diff of both files is confined to the intended lines.

## Known Stubs

None. The scan of the six modified files found no TODO, FIXME, placeholder or skipped test.

## Threat Flags

None. The register T-04-14..T-04-17 is mitigated as planned: T-04-14 by `test_tracked_run_summaries_are_polyomics_runs`, T-04-15 and T-04-16 by the test that asks git over the four names, `ledger.jsonl`, `cache.jsonl`, a nested file and a stray top-level file, and T-04-17 by the probe on two scratch copies. No new network, auth or trust-boundary surface was added.

## Next Phase Readiness

The first tracked run directory can now be committed by a later plan without a pattern change. Plans 04-07 and 04-08 write `usage.json` and `run_summary.json`; nothing here blocks them. Plan 04-09 adds the index of `protocol/README.md`.

## Self-Check: PASSED

- Modified files exist on disk (`.gitignore`, `experiments/README.md`, `README.md`, `CLAUDE.md`, `tests/test_governance.py`, `tests/test_import_boundary.py`); commits `5485a83` and `a325306` are in `git log`.
- `git rev-list --count 4665d41..HEAD` was 2 at the GREEN commit (the measured `commits`).
- Plan verification re-run: the two named test files pass, `summary=1` and `ledger=0`, `ADR-0007` count is nonzero in all four files, `ignored except` count is 0, `run_summary.json` appears in `experiments/README.md`, the charter, ADR and decisions-log diff is empty, and the full gate ends `SUMMARY: 7/7 steps passed`.
