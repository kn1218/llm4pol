---
phase: 01-foundation
plan: 01
subsystem: infra
tags: [check-gate, secret-scan, git-history, ci, github-actions, pixi, huggingface_hub, pytest]

# Dependency graph
requires: []
provides:
  - "scripts/history_secret_scan.py: ten runtime-assembled pattern classes, --self-test, dotenv-path check, shallow-clone refusal, --root override; never prints a value"
  - "history-secret-scan step in scripts/check.py (in-process self-test then scan), gate is six steps"
  - "tests/conftest.py puts scripts/ on sys.path for tests"
  - "tests/test_history_secret_scan.py (12 tests) and tests/test_environment.py (FOUND-02 import proof)"
  - "CI checks out full history (fetch-depth: 0) so the scan is non-vacuous on both platforms"
  - "INVARIANTS.md R-3 guard is the scanner, the check step and its test"
  - "01-EVIDENCE.md: command-and-output evidence for charter §13 M0 exit criteria 1-3"
affects: [02-data-foundation, verification, ci, secrets]

# Actuals (#2632) — same estimateTokens scale as the plan's estimate (chars/4 over the realized diff)
actuals:
  tokens: 9515
  tasks: 3
  commits: 5
plan_head_before: 4ec32b6d454c50b33a4364a333ef1f1a483c46fe

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Secret-shaped literals and the withheld dotenv name are assembled from fragments at runtime in every committed source file (scanner, tests, evidence)"
    - "Check-gate steps that are Python modules are called in-process from scripts/check.py, never via subprocess or a shell"
    - "tests/conftest.py inserts scripts/ on sys.path so tests import the exact module the gate runs"
    - "CI verification by workflow_dispatch + gh run watch, cited by run id and per-job conclusion (D-05)"

key-files:
  created:
    - scripts/history_secret_scan.py
    - tests/conftest.py
    - tests/test_history_secret_scan.py
    - tests/test_environment.py
    - .planning/phases/01-foundation/01-EVIDENCE.md
  modified:
    - scripts/check.py
    - .github/workflows/ci.yml
    - docs/governance/INVARIANTS.md
    - experiments/README.md

key-decisions:
  - "Ten pattern classes: D-01's mandatory seven (OpenAI, Anthropic, Google AI, Hugging Face, GitHub classic, GitHub fine-grained, generic KEY=value) plus AWS, Slack and PEM carried over from the precedent (zero hits on this history)"
  - "generic_credential_assignment accepts an unquoted dotenv-style value (quote optional) and rejects dotted or digit-free values, so config-key constants in vendored .claude/ files do not false-positive"
  - "scan_history returns 2 and refuses a shallow clone; CI sets fetch-depth: 0 rather than letting a depth-1 checkout pass vacuously"
  - "Commits were made on main per the orchestrator's sequential-mode instruction (branching_strategy none, use_worktrees false); the executor's protected-branch assertion was overridden by that explicit direction and recorded here"

patterns-established:
  - "RED/GREEN commit pair per plan id: test(01-01) then feat(01-01), with the RED commit's gate failure named in its message"
  - "Evidence files pair each command with its verbatim output and cite the charter exit-criterion number"

requirements-completed: [FOUND-01, FOUND-02, FOUND-03]

# Coverage metadata (#1602)
coverage:
  - id: D1
    description: "Six-step check gate (ruff check, ruff format --check, mypy, import-linter, history-secret-scan, pytest) is green locally and in a workflow_dispatch run on windows-latest and ubuntu-latest"
    requirement: FOUND-01
    verification:
      - kind: integration
        ref: "pixi run --manifest-path env/pixi.toml check -> SUMMARY: 6/6 steps passed"
        status: pass
      - kind: e2e
        ref: "gh run view 35627403598 -> check (ubuntu-latest): success, check (windows-latest): success, both logs SUMMARY: 6/6 steps passed"
        status: pass
    human_judgment: false
  - id: D2
    description: "huggingface_hub imports from the locked environment with __version__ in >=1.32,<2 on both CI platforms"
    requirement: FOUND-02
    verification:
      - kind: unit
        ref: "tests/test_environment.py#test_huggingface_hub_importable"
        status: pass
    human_judgment: false
  - id: D3
    description: "A secret-shaped token or a withheld dotenv path anywhere in reachable history turns the gate red; the scanner never prints a value; every pattern class fires on its positive control; a shallow clone is refused"
    requirement: FOUND-03
    verification:
      - kind: unit
        ref: "tests/test_history_secret_scan.py#test_seeded_secrets_in_temp_repo_are_detected_without_printing_them"
        status: pass
      - kind: unit
        ref: "tests/test_history_secret_scan.py#test_seeded_dotenv_file_in_temp_repo_is_detected"
        status: pass
      - kind: unit
        ref: "tests/test_history_secret_scan.py#test_self_test_exits_zero_and_reports_every_class"
        status: pass
      - kind: unit
        ref: "tests/test_history_secret_scan.py#test_shallow_repository_is_refused"
        status: pass
      - kind: integration
        ref: "python scripts/history_secret_scan.py -> scanned 15 commit(s), 0 hit(s) per class, dotenv-path-in-history: 0 hit(s)"
        status: pass
    human_judgment: false
  - id: D4
    description: "INVARIANTS.md R-3 guard cell names the scanner, the check step and the test; experiments/README.md states charter §10's reasons; 01-EVIDENCE.md cites command-and-output for M0 exit criteria 1-3"
    requirement: FOUND-03
    verification:
      - kind: other
        ref: "sed -n '/^| R-3 /p' docs/governance/INVARIANTS.md | grep -c history_secret_scan.py -> 1; grep -c 'CC BY 4.0' experiments/README.md -> 1; grep -c 'CI run id:' 01-EVIDENCE.md -> 1"
        status: pass
    human_judgment: true
    rationale: "Whether the reworded prose says what the charter §10 and the promotion policy mean is a reading judgment; the greps only prove the required tokens are present"

# Metrics
duration: 12min
completed: 2026-09-21
status: complete
---

# Phase 1 Plan 01: Foundation Summary

**History secret scan (10 self-tested pattern classes plus dotenv-path check, shallow-clone refusal) wired as the sixth check-gate step and proven green on both CI platforms by a workflow_dispatch run, with huggingface_hub proven by import and M0 evidence recorded**

## Performance

- **Duration:** 12 min
- **Started:** 2026-09-21T16:34:12Z
- **Completed:** 2026-09-21T16:46:40Z
- **Tasks:** 3
- **Files modified:** 9

## Accomplishments

- `scripts/history_secret_scan.py` walks every commit from `git rev-list --all`, checks `git log --all --name-only` for the withheld dotenv name, refuses a shallow clone (exit 2), and proves each of its ten pattern classes fires via `--self-test`; it prints pattern names, shas and paths only.
- `scripts/check.py` runs the scanner in-process as `history-secret-scan` before `pytest`; the `Steps:` line is now `ruff check, ruff format --check, mypy, import-linter, history-secret-scan, pytest` and the gate prints `SUMMARY: 6/6 steps passed`.
- CI checks out full history (`fetch-depth: 0`); run 35627403598 (`workflow_dispatch`, `main`, head `007cda58…`) is `success` on `check (windows-latest)` and `check (ubuntu-latest)`, both logs show `SUMMARY: 6/6 steps passed` and `scanned 14 commit(s)`.
- `tests/test_environment.py::test_huggingface_hub_importable` proves FOUND-02 by import (version `>=1.32,<2`), inside the gate on both platforms.
- `INVARIANTS.md` R-3 guard is promoted from prose to the scanner, the check step and its test; `experiments/README.md` states charter §10's reasons; `01-EVIDENCE.md` pairs each M0 exit criterion with commands and verbatim output.

## Task Commits

Each task was committed atomically:

1. **Task 1 (tracer, TDD): history secret scan end to end**
   - RED `d6db064cca1e31112f369c1c5b1f8f635d09da97` — `test(01-01): add failing history-secret-scan tests (D-01, R-3)` (`tests/conftest.py`, `tests/test_history_secret_scan.py`)
   - GREEN `f0c8b8b83ebe110e1415ecb3f1bdf2a38c239ca7` — `feat(01-01): add the history secret scan as a check step and promote R-3 to a guard (D-01, FOUND-03)` (`scripts/history_secret_scan.py`, `scripts/check.py`, `.github/workflows/ci.yml`, `docs/governance/INVARIANTS.md`)
2. **Task 2: import proof and experiments policy**
   - `83a8100be0ee65a022f2698be9f2bde1663da502` — `test(01-01): prove huggingface_hub imports from the locked environment (D-02, FOUND-02)`
   - `007cda58cb9fcc3ef761bc71776ad66aa3649daf` — `docs(01-01): restate why experiments/ is untracked per charter §10 (D-06)` (the pushed tip the CI run cites)
3. **Task 3: push, dispatch, evidence**
   - `33fc516` — `docs(01-01): record Phase 1 M0 evidence (D-04, D-05)` (a `.planning/` doc that post-dates the cited CI run; pushed separately)

**Plan metadata:** see the final `docs(01-01): complete …` commit.

## Recorded lines (per the plan's output spec)

- RED collection error: `E   ModuleNotFoundError: No module named 'history_secret_scan'`
- Resolved `Steps:` line: `Steps: ruff check, ruff format --check, mypy, import-linter, history-secret-scan, pytest`
- Local `scanned N commit(s)` lines: `scanned 11 commit(s)` after RED, `scanned 12 commit(s)` after GREEN, `scanned 14 commit(s)` at the pushed tip, `scanned 15 commit(s)` after the evidence commit (the plan's grounding assumed 8 pre-existing commits; there were 10)
- CI `scanned N commit(s)`: `scanned 14 commit(s) reachable from git rev-list --all` on both jobs
- CI run: `35627403598`, `check (windows-latest): success`, `check (ubuntu-latest): success`
- D-05 observation: `gh run list --workflow=ci.yml --event push --branch main --limit 3` printed `[]` — no push-triggered run appeared for the pushed tip; the verification run was a `workflow_dispatch`
- Pytest counts: 25 passed after Task 1, 26 passed after Task 2 locally; CI reports `25 passed, 1 skipped` because `test_raw_files_match_manifest` skips without local PoLyInfo raw files (by design, ADR-0001)

## Files Created/Modified

- `scripts/history_secret_scan.py` — the R-3 guard: `PatternClass`, `PATTERNS` (10), `_join`, `_matches`, `is_dotenv_path`, `_run_git`, `_is_shallow`, `_iter_commit_hits`, `_check_dotenv_history`, `self_test`, `scan_history`, `main`; CLI `--self-test`, `--root`
- `scripts/check.py` — `step_history_secret_scan` (in-process, self-test then scan) inserted before `pytest`; docstring lists the new step
- `tests/conftest.py` — `REPO_ROOT`, `SCRIPTS_DIR` on `sys.path`, `repo_root` fixture
- `tests/test_history_secret_scan.py` — 12 tests, helper `_seed_repo`, every sample fragment-assembled
- `tests/test_environment.py` — `test_huggingface_hub_importable`
- `.github/workflows/ci.yml` — `fetch-depth: 0` with a two-line comment
- `docs/governance/INVARIANTS.md` — R-3 guard cell only (one line removed, one added)
- `experiments/README.md` — `## Why it is ignored` body only
- `.planning/phases/01-foundation/01-EVIDENCE.md` — M0 evidence

## Decisions Made

- Kept the three precedent-only classes (AWS, Slack, PEM) alongside D-01's mandatory set; zero hits on this history, and the self-test pins all ten.
- The generic assignment regex takes an optional quote (D-01's `KEY=<long token>` dotenv form) with `_generic_value_is_secret_shaped` rejecting dotted or digit-free values; six known-benign lines are regression fixtures.
- Test git calls strip `GIT_DIR`/`GIT_WORK_TREE`/`GIT_INDEX_FILE`/`GIT_OBJECT_DIRECTORY` from the environment and pass `cwd=<tmp repo>` (T-01-06); `git add --force` so a global excludes file cannot hide the seeded dotenv file.
- Commits made directly on `main`: the orchestrator ran this executor in sequential mode on the main working tree with `branching_strategy: none`, and Task 3 by design pushes `origin main`; the executor's protected-branch assertion was consciously overridden by that instruction.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Acceptance-criterion greps for `shell=True` and `subprocess` matched prose comments**
- **Found during:** Task 1 (acceptance criteria gate)
- **Issue:** `grep -c "shell=True" scripts/check.py` must print 0, but the pre-existing docstring said "never ``shell=True``" and my new step comment repeated it and mentioned "subprocess"; both were prose, not calls.
- **Fix:** Reworded the docstring phrase to "never through a shell" and the step comment to "no child process, no shell"; amended the unpushed GREEN commit so it still lists exactly the four planned files.
- **Files modified:** scripts/check.py
- **Verification:** both greps print 0; gate 6/6
- **Committed in:** f0c8b8b (GREEN, amended before any push)

**2. [Rule 3 - Blocking] Workstation hook rejected commit commands containing `-n`**
- **Found during:** Task 1 GREEN commit
- **Issue:** The `block-no-verify` hook refuses any Bash command text containing git's `-n` short flag; my commit command chained `git log … -n 2`.
- **Fix:** Commit messages written to scratchpad files and committed with `-F`; log inspection moved to separate commands with `--max-count`. No hook bypassed.
- **Files modified:** none
- **Verification:** all five commits ran through the normal hooks
- **Committed in:** n/a

### Noted, not fixed

- RED commit also fails `ruff check` (I001) because isort classifies the not-yet-existing `history_secret_scan` module as third-party until GREEN adds it; named in the RED commit message, green in GREEN. The plan sanctioned the RED gate failure.
- `git status --porcelain --branch` prints `?? .gsd/` and `?? .planning/state.json` in addition to `## main...origin/main`; both are GSD runtime artifacts untracked before this plan started and D-03 forbids a `.gitignore` change. Logged in `deferred-items.md`.

---

**Total deviations:** 2 auto-fixed (1 bug, 1 blocking)
**Impact on plan:** Wording-only and tooling-only; no scope change, no extra tooling (D-03 honoured: `env/`, `.gitignore`, `.gitattributes`, `.env.example` untouched).

## Issues Encountered

None beyond the deviations above. All `<verify>` blocks passed on the first run after each task.

## Authentication Gates

None. `gh` was already logged in as `kn1218`; only `workflow run`, `run list`, `run watch`, `run view` were used.

## Known Stubs

None.

## Threat Flags

None. The only new surface is the scanner's `--root` CLI argument, which reads a local repository path and prints names/shas/paths only (covered by T-01-02).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Charter M0 exit criteria 1-3 are evidenced in `01-EVIDENCE.md`; the Phase 1 verifier can derive `01-VERIFICATION.md` from it without re-running CI.
- Phase 2 (data foundation) can add its schema-inventory step to `STEPS` in `scripts/check.py` the same way (D-03 deferred it to the first schema).
- Open: whether to ignore or commit the GSD runtime artifacts noted in `deferred-items.md`.

---
*Phase: 01-foundation*
*Completed: 2026-09-21*

## Self-Check: PASSED

- Created files present on disk: scripts/history_secret_scan.py, tests/conftest.py, tests/test_history_secret_scan.py, tests/test_environment.py, 01-EVIDENCE.md
- Commits present: d6db064, f0c8b8b, 83a8100, 007cda5, 33fc516
- Gate after the evidence commit: SUMMARY: 6/6 steps passed; history scan 15 commit(s), 0 hits
