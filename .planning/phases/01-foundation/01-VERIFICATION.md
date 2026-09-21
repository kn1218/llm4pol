---
phase: 01-foundation
verified: 2026-09-21T16:53:32Z
status: passed
score: 13/13 must-haves verified
covered_files:
  - ".github/workflows/ci.yml"
  - ".planning/REQUIREMENTS.md"
  - ".planning/phases/01-foundation/01-01-PLAN.md"
  - ".planning/phases/01-foundation/01-01-SUMMARY.md"
  - ".planning/phases/01-foundation/01-CONTEXT.md"
  - ".planning/phases/01-foundation/01-EVIDENCE.md"
  - ".planning/phases/01-foundation/deferred-items.md"
  - "docs/governance/INVARIANTS.md"
  - "experiments/README.md"
  - "scripts/check.py"
  - "scripts/history_secret_scan.py"
  - "tests/conftest.py"
  - "tests/test_environment.py"
  - "tests/test_history_secret_scan.py"
covered_digest: "v1:sha256:358cc8a8192372ad0f1337ce7f5ef785ef4932bbcb227a95f449ab0886248e0b"
behavior_unverified: 0
overrides_applied: 0
prohibitions:
  - statement: "No secret value, real or synthetic, is ever printed, logged, committed or written into a plan artifact"
    declared_verification: null
    status: verified
    enforcement: "tests/test_history_secret_scan.py::test_seeded_secrets_in_temp_repo_are_detected_without_printing_them (ran inside the gate, 26 passed); verifier's own seeded-repo run: 10/10 HIT lines, value leaked: []; full-history scan at HEAD: 16 commits, 0 hits in every class"
  - statement: "The RED test commit is never pushed alone; the only push happens after the local gate prints SUMMARY: 6/6"
    declared_verification: null
    status: verified
    enforcement: "git reflog show origin/main: one push moved 8cf794e -> 007cda5 (RED d6db064 and GREEN f0c8b8b arrived together); the workflow_dispatch run at 007cda5 is 6/6 on both platforms"
  - statement: "Nothing listed as already done in 01-CONTEXT.md is re-implemented (env/pixi.toml, env/pixi.lock, .gitattributes, .gitignore, .env.example untouched)"
    declared_verification: null
    status: verified
    enforcement: "git diff --stat 4ec32b6 HEAD -- env/pixi.toml env/pixi.lock .gitignore .gitattributes pyproject.toml and the example file: empty"
---

# Phase 1: Foundation Verification Report

**Phase Goal:** The repository is a reproducible development base whose single check gate is green on both CI platforms with the snapshot-fetch dependency locked in — charter §13 M0 (`docs/MASTER-PLAN.md`).
**Verified:** 2026-09-21T16:53:32Z
**Status:** passed
**Re-verification:** No — initial verification

Every claim below was reproduced by the verifier in its own process on this workstation (Windows, `pixi` env) or by a live `gh` query; nothing is taken from `01-01-SUMMARY.md` or `01-EVIDENCE.md` on trust. Where the evidence file is cited it is because the verifier re-ran the same command and got the same output.

## Charter §13 M0 exit criteria (ROADMAP Phase 1 success criteria 1-3)

Charter §14 requires the phase `VERIFICATION.md` to cite the exit-criterion numbers with the evidence that reproduces them.

| M0 exit criterion | Reproduced by | Result |
|---|---|---|
| **(1)** `pixi run check` green on both platforms; `huggingface_hub` resolves in the lock on both | `gh run view 35627403598 --json conclusion,event,headBranch,headSha,jobs` -> `{"conclusion":"success","event":"workflow_dispatch","headBranch":"main","headSha":"007cda58…","jobs":[{"conclusion":"success","name":"check (ubuntu-latest)"},{"conclusion":"success","name":"check (windows-latest)"}]}`; `gh run view 35627403598 --log \| grep -c "SUMMARY: 6/6 steps passed"` -> `2`; both job logs carry `Steps: ruff check, ruff format --check, mypy, import-linter, history-secret-scan, pytest`, `scanned 14 commit(s)`, `SELF-TEST OK`, `dotenv-path-in-history: 0 hit(s)`, `25 passed, 1 skipped`. `tests/test_environment.py::test_huggingface_hub_importable` is collected inside that gate (verified by `pytest --collect-only`) and imports the package, so a green gate on both jobs is the import proof. Local re-run at HEAD `46a8e14`: `SUMMARY: 6/6 steps passed`, `26 passed`, exit 0. `env/pixi.toml` line 34: `huggingface_hub = ">=1.32.0,<2"`; `env/pixi.lock` carries the package. | REPRODUCED |
| **(2)** First commit of the approved-charter era exists on `main` | `git log --reverse --format="%h %ad %s" --date=short --max-parents=0` -> `567ce1d 2026-09-21 chore: bootstrap repository with governance, research inputs and charter v1.0`; `git ls-remote origin refs/heads/main` -> `46a8e14…` (remote `kn1218/llm4pol`, `git status --porcelain --branch` -> `## main...origin/main`, not ahead/behind) | REPRODUCED |
| **(3)** `.env` untracked, `.env.example` committed, no secret value in output, logs or history | `git ls-files -- <dotenv> <dotenv>.example` (name assembled at runtime) -> `'.env.example\n'`; scan of every path in `git ls-files` for the dotenv basename or any non-`.example` suffix -> `[]`; `python scripts/history_secret_scan.py --self-test` -> exit 0, ten `1 match(es)` lines, `SELF-TEST OK: 10 pattern classes…`; full-history scan inside the gate at HEAD -> `scanned 16 commit(s)`, `0 hit(s)` for all ten classes, `dotenv-path-in-history: 0 hit(s)`; CI logs on both platforms show the same `dotenv-path-in-history: 0 hit(s)` at 14 commits; verifier's own seeded temp repo -> 10/10 HIT lines, no positive-control string in captured output | REPRODUCED |

## Goal Achievement

### Observable Truths

Truths 1-3 are the ROADMAP success criteria (roadmap contract); 4-13 are the PLAN `must_haves.truths`, deduplicated against them.

| # | Truth | Status | Evidence |
|---|---|---|---|
| 1 | Gate green on windows-latest and ubuntu-latest from the committed lock; `huggingface_hub` resolves on both (SC 1 / M0-1) | ✓ VERIFIED | Live `gh run view 35627403598`: both jobs `success`; `SUMMARY: 6/6 steps passed` counted twice in the log; import test collected in the gate |
| 2 | First commit of the approved-charter era on `main` (SC 2 / M0-2) | ✓ VERIFIED | Root commit `567ce1d` printed by `git log --max-parents=0`; remote tip matches local |
| 3 | `.env` untracked, `.env.example` committed, no secret in output/logs/history (SC 3 / M0-3, R-3) | ✓ VERIFIED | `tracked-dotenv-paths: '.env.example\n'`; index scan `[]`; history scan 16 commits 0 hits; CI logs 0 hits |
| 4 | Gate prints the six-step `Steps:` line and ends `SUMMARY: 6/6 steps passed` locally and in CI (FOUND-01, D-01, D-05) | ✓ VERIFIED | Local run at HEAD: exact `Steps:` line, `PASS` on all six, `SUMMARY: 6/6 steps passed`, exit 0; both CI job logs print the identical `Steps:` line and `SUMMARY: 6/6` |
| 5 | A secret-shaped token anywhere in history turns the gate red: `scan_history` returns 1, prints `HIT pattern=<name> commit=<sha> path=<path>`, never the value (FOUND-03, R-3) | ✓ VERIFIED (behavioral) | Verifier seeded a temp repo with all ten positive controls and drove `main(["--root", …])`: rc 1, 10/10 `HIT pattern=` lines, `value leaked: []`. Same invariant pinned by `test_seeded_secrets_in_temp_repo_are_detected_without_printing_them`, which ran inside the gate |
| 6 | Every pattern class fires on its positive control; `--self-test` exits 0 with `SELF-TEST OK: 10 …`; a zero-match regex fails the self-test and the gate (D-01) | ✓ VERIFIED (behavioral) | `--self-test` exit 0, ten `1 match(es)` lines, `SELF-TEST OK` line; `self_test()` appends zero-match names and returns 1; `step_history_secret_scan` runs `scan_main(["--self-test"])` first and ANDs the result |
| 7 | Dotenv basename (or dotenv + any non-`.example` suffix) anywhere in `git log --all --name-only` turns the gate red; `.env.example` never flagged (FOUND-03, M0-3) | ✓ VERIFIED (behavioral) | Verifier's seeded repo committed the dotenv file and the `.example` file: `dotenv-path-in-history: 1 hit(s)`, `.example` not flagged, rc 1. `is_dotenv_path` returns False only for the `.example` basename, True for name or `name.` prefix |
| 8 | Scan cannot pass vacuously on a shallow clone: returns 2 with a refusal; CI checks out `fetch-depth: 0` (D-01, R-4) | ✓ VERIFIED (behavioral) | Verifier's `git clone --depth 1 file://…` then `main(["--root", dst])` -> rc 2, `refusing to scan a shallow repository`; `.github/workflows/ci.yml` checkout step carries `fetch-depth: 0`; CI logs show `scanned 14 commit(s)` = full history at that sha |
| 9 | `huggingface_hub` imports with `__version__` in `>=1.32,<2`, proven by `test_huggingface_hub_importable` inside the gate on both platforms (FOUND-02, D-02) | ✓ VERIFIED | Test read: module-level `import huggingface_hub`, regex `^(\d+)\.(\d+)`, asserts `>= (1, 32)` and major `< 2`; collected in the gate; `grep -c pixi tests/test_environment.py` -> 0 (no lock grep); passes in both CI jobs (gate green) |
| 10 | `INVARIANTS.md` R-3 names `scripts/history_secret_scan.py`, the `history-secret-scan` step and `tests/test_history_secret_scan.py`; no longer says postponed (D-01) | ✓ VERIFIED | R-3 row read: names all three; `grep -c -i "until there is history"` on that row -> 0; GREEN commit diff to the file is exactly one removed and one added line, both the R-3 row |
| 11 | `experiments/README.md` § Why it is ignored states charter §10's reasons in order: policy (size, churn); PolyOmics CC BY 4.0 carries no licence problem; PoLyInfo-derived case (ADR-0001) arrives with M8 (D-06) | ✓ VERIFIED | Section read: items 1-3 in exactly that order, cites `docs/MASTER-PLAN.md §10`, `CC BY 4.0`, `charter §13 M8`, `ADR-0001`, the word `policy`; `grep -c "Two reasons, and both are binding"` -> 0; commit `007cda5` hunk is confined to that section |
| 12 | `01-EVIDENCE.md` cites per M0 exit criterion the command run and its captured output (D-04, D-05) | ✓ VERIFIED | Sections (1), (2), (3) and `## D-05 observation` present; every line the verifier re-ran (`gh run view`, root commit, tracked-dotenv-paths, self-test, history scan) reproduced the recorded output; the only drift is the scan count (14 at the evidence tip vs 16 at HEAD) which is the two later `.planning/`-only commits |
| 13 | No tooling beyond D-01/D-02/D-06 was added; `env/pixi.toml`, `env/pixi.lock`, `.gitignore` unchanged (D-03, D-06) | ✓ VERIFIED | `git diff --stat 4ec32b6 HEAD -- env/pixi.toml env/pixi.lock .gitignore .gitattributes pyproject.toml` and the example file: empty. Phase diff (`4ec32b6..HEAD`) touches only the nine planned files plus `.planning/` docs; no version report, hook installer, SQLite or schema-inventory step exists |

**Score:** 13/13 truths verified (0 present, behavior-unverified)

Behavior-dependent truths 5-8 (exit-code transitions, HIT emission, refusal) were exercised by the verifier's own seeded/shallow/clean repositories via `history_secret_scan.main(["--root", …])`, not inferred from symbol presence.

### Advisory (New Scope, Unevidenced)

Not applicable — initial verification, not a re-verification.

### Required Artifacts

`gsd_run query verify.artifacts` -> `all_passed: true, 9/9`. Level 2 (substantive) and 3 (wired) were then checked by reading.

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `scripts/history_secret_scan.py` | 10 runtime-assembled pattern classes, `--self-test`, dotenv-path check, shallow refusal, `--root`, never prints a value | ✓ VERIFIED | 353 lines; defines `_join`, `_KEY_PREFIX_BOUNDARY`, `PatternClass`, `_generic_value_is_secret_shaped`, `_matches`, `_build_patterns`, `PATTERNS`, `is_dotenv_path`, `_run_git`, `_is_shallow`, `_iter_commit_hits`, `_check_dotenv_history`, `self_test`, `scan_history`, `main`; `shell=True` count 0; HIT lines print name/sha/path only |
| `scripts/check.py` | `history-secret-scan` step before `pytest`, in-process | ✓ VERIFIED | `step_history_secret_scan` inserts `scripts/` on `sys.path`, `from history_secret_scan import main as scan_main`, returns `scan_main(["--self-test"]) == 0 and scan_main([]) == 0`; `STEPS` order: ruff check, ruff format --check, mypy, import-linter, history-secret-scan, pytest; `shell=True` count 0 |
| `tests/conftest.py` | `scripts/` on `sys.path`, `repo_root` fixture | ✓ VERIFIED | `REPO_ROOT`, `SCRIPTS_DIR`, `sys.path.insert(0, …)`, `repo_root` fixture |
| `tests/test_history_secret_scan.py` | 12 tests incl. seeded-secret, dotenv, clean, shallow | ✓ VERIFIED | `pytest --collect-only` lists all 12 named tests; `_git` helper strips `GIT_*` env vars and passes `cwd=root` on every call; `git add --force`; no bare dotenv literal in source; every sample built from fragments / `positive_control` (full-history scan 0 hits confirms) |
| `tests/test_environment.py` | `test_huggingface_hub_importable` | ✓ VERIFIED | One test, module-level import, `>=(1,32)` and `<2` bounds, no lock read |
| `.github/workflows/ci.yml` | `fetch-depth: 0` | ✓ VERIFIED | Checkout `actions/checkout@v7.0.1` with `fetch-depth: 0` and the two-line comment; one job `check`, two-OS matrix, unchanged `pixi run … check` step |
| `docs/governance/INVARIANTS.md` | R-3 promoted | ✓ VERIFIED | R-3 guard cell names the script, the step of `scripts/check.py`, CI on both platforms, and the test; rows R-1, R-2, R-4, R-5 untouched (1 line removed / 1 added in GREEN) |
| `experiments/README.md` | Charter §10 wording | ✓ VERIFIED | Three ordered reasons with `CC BY 4.0` and `ADR-0001`; other sections untouched |
| `.planning/phases/01-foundation/01-EVIDENCE.md` | Command-and-output evidence for M0-1..3 | ✓ VERIFIED | Contains `CI run id: 35627403598`, both `check (…): success` lines, two job-prefixed `SUMMARY: 6/6`, `scanned 14 commit(s)`, `tracked-dotenv-paths: '.env.example\n'`, self-test block, scan block, `test_huggingface_hub_importable PASSED`, `567ce1d` line, `## D-05 observation` |

### Key Link Verification

`gsd_run query verify.key-links` -> `all_verified: true, 5/5`; each then confirmed by reading.

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `scripts/check.py` | `scripts/history_secret_scan.py` | in-process `from history_secret_scan import main` | ✓ WIRED | Step registered in `STEPS`; gate output shows `SELF-TEST OK` then scan report then `PASS history-secret-scan` |
| `tests/test_history_secret_scan.py` | `scripts/history_secret_scan.py` | `conftest.py` `sys.path` insert; imports `PATTERNS, _matches, is_dotenv_path, scan_history, self_test` | ✓ WIRED | 12 tests collected and passing inside the gate |
| `.github/workflows/ci.yml` | `scripts/history_secret_scan.py` | `fetch-depth: 0` -> non-shallow clone | ✓ WIRED | CI logs: `scanned 14 commit(s)` (would be exit 2 on a depth-1 clone) |
| `docs/governance/INVARIANTS.md` | `scripts/check.py` | R-3 cell names the `history-secret-scan` step | ✓ WIRED | Row text read |
| `01-EVIDENCE.md` | `.github/workflows/ci.yml` | cites run id and both job conclusions | ✓ WIRED | Run id re-queried live; conclusions match |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|---|---|---|---|---|
| `scan_history` | `commits` | `git rev-list --all` via `_run_git` | Yes (16 at HEAD, 14 in CI) | ✓ FLOWING |
| `scan_history` | `hits` | `git show --no-color --format= <sha>` per commit, regex over each patch line | Yes (10 hits on the seeded repo, 0 on this history) | ✓ FLOWING |
| `scan_history` | `dotenv_hits` | `git log --all --name-only --pretty=format:` filtered by `is_dotenv_path` | Yes (1 on seeded repo, 0 here) | ✓ FLOWING |
| `self_test` | `count` per class | `_matches(pattern, pattern.positive_control)` | Yes (1 per class) | ✓ FLOWING |
| `test_huggingface_hub_importable` | `version` | `huggingface_hub.__version__` from the locked env | Yes | ✓ FLOWING |

### Behavioral Spot-Checks

All run by the verifier; none taken from the SUMMARY.

| Behavior | Command | Result | Status |
|---|---|---|---|
| Single gate is green at HEAD | `pixi run --manifest-path env/pixi.toml check` | exit 0; `Steps:` six names; `PASS` ×6; `26 passed`; `scanned 16 commit(s)`; all `0 hit(s)`; `SUMMARY: 6/6 steps passed` | ✓ PASS |
| Self-test fires every class | `pixi run … python scripts/history_secret_scan.py --self-test` | exit 0; ten `1 match(es)` lines; `SELF-TEST OK: 10 pattern classes each matched their positive control` | ✓ PASS |
| CI run green on both platforms | `gh run view 35627403598 --json conclusion,event,headBranch,headSha,jobs` | `success` / `workflow_dispatch` / `main` / `007cda5…` / both jobs `success` | ✓ PASS |
| Both CI jobs printed the six-step summary | `gh run view 35627403598 --log \| grep -c "SUMMARY: 6/6 steps passed"` | `2` | ✓ PASS |
| Only the example dotenv file is tracked | `git ls-files -- <n> <n>.example` (runtime-assembled) + full index scan | `'.env.example\n'`; `[]` | ✓ PASS |
| Seeded secrets detected, value never printed | temp repo with all 10 positive controls + dotenv file, `main(["--root", …])` | rc 1; 10/10 HIT classes; `dotenv-path-in-history: 1 hit(s)`; `.example` not flagged; leaked `[]` | ✓ PASS |
| Shallow clone refused | `git clone --depth 1 file://…` then `main(["--root", dst])` | rc 2; `refusing to scan a shallow repository` | ✓ PASS |
| Clean repo green | one-commit prose repo, `main(["--root", …])` | rc 0; `no secrets found in any reachable commit` | ✓ PASS |
| Phase tests exist | `pytest --collect-only tests/test_history_secret_scan.py tests/test_environment.py` | `13 tests collected` (12 + 1), all names match the plan | ✓ PASS |
| Root commit present | `git log --reverse --format="%h %ad %s" --date=short --max-parents=0` | `567ce1d 2026-09-21 chore: bootstrap repository …` | ✓ PASS |
| Repository not shallow locally | `git rev-parse --is-shallow-repository` | `false` | ✓ PASS |
| Commits cited in SUMMARY exist | `gsd_run query verify.commits d6db064 f0c8b8b 83a8100 007cda5 33fc516 46a8e14` | `all_valid: true` | ✓ PASS |
| RED/GREEN commit shapes | `git show --stat --format= d6db064` / `f0c8b8b` | RED = `tests/conftest.py`, `tests/test_history_secret_scan.py`; GREEN = `scripts/history_secret_scan.py`, `scripts/check.py`, `.github/workflows/ci.yml`, `docs/governance/INVARIANTS.md` | ✓ PASS |

### Probe Execution

No `scripts/*/tests/probe-*.sh` exists and the plan declares none. The gate itself (`scripts/check.py`) is the phase's runnable check and was executed above. N/A.

### Requirements Coverage

PLAN frontmatter `requirements: [FOUND-01, FOUND-02, FOUND-03]`. REQUIREMENTS.md traceability maps exactly FOUND-01..03 to Phase 1; no orphaned requirement.

| Requirement | Source Plan | Description | Status | Evidence |
|---|---|---|---|---|
| FOUND-01 | 01-01 | Check gate passes on windows-latest and ubuntu-latest from a committed lock file | ✓ SATISFIED | Run 35627403598: both jobs `success`, both logs `SUMMARY: 6/6 steps passed`; lock untouched (`git diff` empty for `env/`) |
| FOUND-02 | 01-01 | `huggingface_hub` available in the locked environment on both platforms | ✓ SATISFIED | `env/pixi.toml` `huggingface_hub = ">=1.32.0,<2"`; `test_huggingface_hub_importable` collected in the gate and green on both CI jobs; local pass |
| FOUND-03 | 01-01 | Secrets read only from `.env`; no secret value printed, logged or committed (R-3); `.env` never tracked | ✓ SATISFIED | Index: only `.env.example` tracked; history: 16 commits, 0 hits, `dotenv-path-in-history: 0`; scanner prints names/shas/paths only (verified on seeded repo); R-3 guard promoted to script + step + test. The "read only from `.env`" clause has no consumer yet (`src/llm4pol/` is the charter-mandated scaffold); `scripts/check.py` keeps its documented promise not to read the dotenv file. That clause becomes testable at LLM-01 (Phase 6) |

### Context decisions D-01..D-06

| Decision | Honoured | Evidence |
|---|---|---|
| D-01 history scan + step + test + R-3 promotion | Yes | Artifacts and links above; mandatory classes OpenAI, Anthropic, Google AI, Hugging Face, GitHub (two classes), generic all present (`test_pattern_names_are_exactly_the_declared_set`) |
| D-02 import proof, not lock grep | Yes | `tests/test_environment.py` imports; `grep -c pixi` -> 0 |
| D-03 no extra tooling | Yes | Phase diff limited to the nine planned files + `.planning/`; `env/`, `.gitignore`, `.gitattributes`, `pyproject.toml`, example file byte-identical |
| D-04 evidence not narrative | Yes | `01-EVIDENCE.md` is command -> fenced output throughout; every re-run reproduced |
| D-05 verify by `workflow_dispatch`, record push observation | Yes | Run event is `workflow_dispatch`; `gh run list --event push` -> `[]` (verifier re-queried) |
| D-06 README wording, no `.gitignore` change | Yes | Section rewritten as specified; `.gitignore` diff empty |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| `tests/test_history_secret_scan.py` | 228 | `PLACEHOLDER=1` | ℹ️ Info | Fixture file content for the seeded-dotenv test, not a stub; the value is a deliberately non-secret-shaped string |
| (working tree) | — | untracked `.gsd/`, `.planning/state.json` | ℹ️ Info | GSD runtime artifacts that predate the plan; D-03 forbade a `.gitignore` change this phase; logged in `deferred-items.md` for the owner to decide (ignore vs commit). Not a Phase 1 gap |
| (CI coverage) | — | HEAD `46a8e14` post-dates the CI-verified sha `007cda5` | ℹ️ Info | `git diff --name-only 007cda5 HEAD` outside `.planning/` is empty, so the CI evidence covers every source file at HEAD; the local gate at HEAD is 6/6 |

No `TBD`/`FIXME`/`XXX`/`TODO`/`HACK` markers, no `shell=True`, no empty returns, no skipped or `.only` tests in any phase file.

### Human Verification Required

None. Every truth resolved programmatically: the CI result was queried live from GitHub, the gate and self-test were re-run in this process, and the scanner's red/refusal/green paths were exercised on throwaway repositories.

### Gaps Summary

No gaps. Charter §13 M0 exit criteria (1), (2) and (3) are each reproduced by a command run by the verifier, not by reading the SUMMARY. The single gate is six steps and green on `windows-latest` and `ubuntu-latest` from the committed lock (run 35627403598, `workflow_dispatch`, head `007cda5`); `huggingface_hub` is locked and proven by import inside that gate; the first commit `567ce1d` is on `main`; only `.env.example` is tracked; the R-3 history guard is a real scanner that walks every reachable commit, refuses a shallow clone, self-tests all ten classes, fails the gate on a seeded secret and never prints the value. Decisions D-01..D-06 were honoured, including D-03's "no extra tooling".

---

_Verified: 2026-09-21T16:53:32Z_
_Verifier: Claude (gsd-verifier)_
