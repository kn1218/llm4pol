---
phase: 04-run-management
plan: 09
subsystem: run-record
tags: [pinned-table, populations, real-file-tests, m3-evidence, protocol-index, ci, two-platform, adr-0008, d-30, m3-exit-1-2-3]

requires:
  - phase: 04-run-management
    provides: "populations, driver, resume, reducer, the campaign verbs, the committed fixture ledger with pinned hashes, run-summary.json (04-01 to 04-08); the seven-step gate with the schema inventory at 9 entries and 16 instances"
  - phase: 03-evaluator
    provides: "the candidate parquet the evaluator serves medians from; the real-file test pattern (a session fixture that skips with a stated reason)"
provides:
  - "tests/test_run_real_file.py: five tests on polyomics:general_polymers@041e5834 that reproduce both populations (39,454 and 40,212), the reference counts on served medians (F-25 as corrected), the two members above the filtered maximum (F-23), a real run with both populations side by side, replay and usage, and a resume from the eighth event; all skip without the parquets"
  - "protocol/README.md lists the six schemas of the run record and their committed examples"
  - ".planning/phases/04-run-management/04-EVIDENCE.md: charter section 13 M3 exit criteria (1), (2), (3) each paired with its command and verbatim output, the freezes, the deliverables, the pinned-table section, the nine owner notes, the data policy, and the CI section"
  - "one workflow_dispatch run (36695769247) at the pushed tip f52ff67, green on windows-latest and ubuntu-latest, with Contracts 5 kept and inventory 9 entries, 16 instances on both; the four pinned fixture hashes hold on ubuntu-latest"
affects: [phase-04-verification, phase-05, phase-06]

plan_head_before: 97020798e1a62c79aebdf78b6ddb3f96165317fb
actuals:
  tokens: 11800
  tasks: 3
  commits: 4

tech-stack:
  added: []
  patterns:
    - "real-file tests read ids from the parquet at run time and write only under tmp_path; the file holds no id, repeat unit or per-candidate value, only the aggregate counts the research measured"
    - "evidence assembled from captured command output by a scratch script (not committed), so every block is verbatim; the only edits are progress percentages of pytest and the scratch directory path written $SCRATCH"

key-files:
  created:
    - tests/test_run_real_file.py
    - .planning/phases/04-run-management/04-EVIDENCE.md
  modified:
    - protocol/README.md

key-decisions:
  - "The byte-for-byte comparison of a resumed ledger is made under the injected clock; the command-line verbs stamp the wall clock, so a ledger resumed through them differs from the uninterrupted one in the ts field of the appended events (owner-visible note in the evidence)"
  - "The 16-hex check on the run_opened line looks for quoted 16-hex strings, as plan 04-08 did: the 16-digit fractional part of a float is also a 16-hex token"
  - "The summary and state commits stay on local main and are not pushed; origin/main equals local main at the last commit of Task 3 (fa467da)"

patterns-established:
  - "A population block is 2.9 MB in a ledger: the run_opened line of a run on the pinned table with two populations is 2,904,340 bytes"

requirements-completed: [RUN-01, RUN-02, RUN-03, RUN-04, RUN-05, RUN-06]

coverage:
  - id: D1
    description: "the code reproduces the population sizes ADR-0008 names on the pinned snapshot: 39,454 check_tc and 40,212 readme_triple candidates, each id unique, the first set a subset of the second"
    requirement: RUN-03
    verification:
      - kind: integration
        ref: "tests/test_run_real_file.py#test_real_population_sizes"
        status: pass
    human_judgment: false
  - id: D2
    description: "on served medians 24,497 and 24,589 members lie below 0.25; 39,449 distinct served values against 39,446 distinct medians over check_tc-passing rows only; 5,533 and 5,620 members feasible under dielectric_const_dc <= 2.6 and tg >= 400.0; no null objective in either array"
    requirement: RUN-04
    verification:
      - kind: integration
        ref: "tests/test_run_real_file.py#test_real_reference_counts_on_served_values"
        status: pass
    human_judgment: false
  - id: D3
    description: "the largest served check_tc objective is 1.284, the largest median over check_tc-passing rows only 0.910 to three decimals, and exactly two members are served a value above it"
    requirement: RUN-04
    verification:
      - kind: integration
        ref: "tests/test_run_real_file.py#test_real_served_values_above_the_filtered_maximum"
        status: pass
    human_judgment: false
  - id: D4
    description: "a run on the pinned table leaves five files, prints n_population 39454 on the check_tc rows and 40212 on the readme_triple rows with n_selected 10, has usage evals equal to the ledger sum and at most 20, holds no quoted 16-hex token in the run_opened line, replays the three reduced files byte for byte with --out, and the usage verb returns 0"
    requirement: RUN-05
    verification:
      - kind: integration
        ref: "tests/test_run_real_file.py#test_real_run_prints_both_populations_side_by_side"
        status: pass
    human_judgment: false
  - id: D5
    description: "a copy of a run on the pinned table cut after its eighth event resumes under the fixed identity to the ledger and the three reduced files of the uninterrupted run byte for byte, with no repeated event key"
    requirement: RUN-03
    verification:
      - kind: integration
        ref: "tests/test_run_real_file.py#test_real_run_resumes_to_the_same_bytes"
        status: pass
    human_judgment: false
  - id: D6
    description: "04-EVIDENCE.md has three numbered criterion sections and the five named sections plus the CI section; the replay section shows the pinned results.csv hash 0e31cfc3... and the usage section the pinned usage.json hash bb11fcba...; 20 lines name the boundary test; the 16-hex check prints 0"
    requirement: RUN-04
    verification:
      - kind: other
        ref: "grep -c '^## (' 04-EVIDENCE.md -> 3; named sections -> 5; both hashes present; 16-hex check -> 0"
        status: pass
    human_judgment: false
  - id: D7
    description: "one workflow_dispatch run on the pushed tip is green on windows-latest and ubuntu-latest; both legs print SUMMARY: 7/7 steps passed, Contracts: 5 kept, 0 broken., llm4polcheck inventory: 9 entries, 16 instances processed, and 370 passed, 22 skipped"
    requirement: RUN-04
    verification:
      - kind: other
        ref: "gh run view 36695769247 -> workflow_dispatch main success check (ubuntu-latest)=success,check (windows-latest)=success; headSha f52ff6732eb130aca5e553509d1a3f3ed05ae491"
        status: pass
    human_judgment: false
  - id: D8
    description: "the reading of the pinned fixture ledger on ubuntu-latest: test_committed_fixture_ledger_reduces_to_the_pinned_bytes cannot skip and both legs report 370 passed, so the reducer gives the same bytes on both platforms"
    requirement: RUN-04
    human_judgment: true
    rationale: "The CI log prints only pytest's summary line (addopts -q), so the per-test PASSED line of that test on the Linux leg is inferred from the equal passed and skipped counts and the test's lack of a skip path, not read from the log; the owner may want one -v -v run added to the workflow later, which this plan forbids editing"

duration: 27min
completed: 2026-09-30
status: complete
---

# Phase 4 Plan 09: The Pinned Table, The M3 Evidence And The Two-Platform CI Run Summary

**Both populations ADR-0008 names are reproduced by the code on `polyomics:general_polymers@041e5834` (39,454 and 40,212, every research count equal), a real run resumes from its eighth event and replays to the same bytes, `04-EVIDENCE.md` pairs charter section 13 M3 (1) to (3) with commands and verbatim output, and one `workflow_dispatch` run on the pushed tip is green on windows-latest and ubuntu-latest.**

## Performance

- **Duration:** 27 min (09:01Z to 09:28Z)
- **Tasks:** 3 (Task 1 as a test-only task on an unchanged code path; Task 3 split at the push boundary)
- **Files:** 2 created, 1 modified
- **Gate:** `SUMMARY: 7/7 steps passed`, 392 tests locally, `Contracts: 5 kept, 0 broken.`, `llm4polcheck inventory: 9 entries, 16 instances processed`, zero history hits, `dotenv-path-in-history: 0 hit(s)`, run before every commit that touched a file the gate reads and immediately before the push

## Accomplishments

- **The observed numbers equal the expected ones; nothing was edited to make a test pass.** All five tests passed on the first run of the code as it stood after plan 04-08. Table below.
- **Charter section 13 M3 (1), (2), (3) on the real table.** A run of two beams of ten candidates on the pinned table leaves five files, prints `n_population` 39454 beside 40212 on adjacent rows, has `usage.json` `evals` 20 equal to the ledger sum, replays byte for byte, and its copy cut after event 8 resumes to the same ledger and the same three reduced files.
- **The evidence is a set of commands, not narrative.** `04-EVIDENCE.md` has the three criterion sections (18 boundary lines PASSED; 20 lines name the test), the freezes, the deliverables, the pinned-table section, the nine owner notes, the data policy and the CI section.
- **Byte identity across platforms was settled by CI.** The four pinned hashes of plan 04-08 hold on ubuntu-latest: both legs pass the same 370 tests (392 locally = 370 + 22 skipped without the pinned files).

## Observed numbers of the pinned table beside the expected ones

| Fact | Expected | Observed |
|---|---|---|
| `check_tc` candidates | 39,454 | 39,454 |
| `readme_triple` candidates | 40,212 | 40,212 |
| `check_tc` below 0.25 (served medians) | 24,497 | 24,497 |
| `readme_triple` below 0.25 | 24,589 | 24,589 |
| distinct TC values, served medians (`check_tc`) | 39,449 | 39,449 |
| distinct TC values, medians over `check_tc`-passing rows only | 39,446 | 39,446 |
| feasible members, `check_tc` and `readme_triple` | 5,533 and 5,620 | 5,533 and 5,620 |
| largest served value / largest filtered median | 1.284 / 0.910 | 1.284 / 0.910 |
| members above the filtered maximum | 2 | 2 |

Observed and not asserted (recorded in the evidence as ADR-0008 item 2 asks): in a real run of two beams of ten candidates, the `run_opened` line is **2,904,340 bytes**, the header line 659, the whole ledger 27 lines and **2,927,882 bytes**; `evals` 20, `cpu_hours` 0.0.

## Record for the owner

| Item | Value |
|---|---|
| Commit, Task 1 | `5369f4c` test(04-09): reproduce both populations and a resumable, replayable run on the pinned table |
| Commit, Task 2 step 1 | `0205a7f` docs(04-09): list the run-record schemas and examples in the protocol index |
| Commit, Task 2 step 4 | `f52ff67` docs(04-09): record Phase 4 M3 evidence (charter section 13 M3 (1)-(3)) |
| Commit, Task 3 step 4 | `fa467da` docs(04-09): record the two-platform CI run of Phase 4 |
| Pushed tip that CI ran on | `f52ff6732eb130aca5e553509d1a3f3ed05ae491` (`f850b2d..f52ff67`); a second push moved `origin/main` to `fa467da` |
| CI run | `36695769247`, event `workflow_dispatch`, branch `main`, `headSha` equal to the pushed tip, `check (ubuntu-latest)`: success, `check (windows-latest)`: success |
| CI counts | ubuntu-latest `370 passed, 22 skipped in 9.26s`; windows-latest `370 passed, 22 skipped in 26.76s` |
| CI gate lines (both legs) | `Contracts: 5 kept, 0 broken.`, `llm4polcheck inventory: 9 entries, 16 instances processed`, `SUMMARY: 7/7 steps passed` |
| `git ls-files experiments data/` | `data/MANIFEST-open.sha256`, `data/MANIFEST.sha256`, `data/README.md`, `experiments/README.md`, before and after the push |
| Not pushed | this summary and the state and roadmap commit that follows it: local `main` is ahead of `origin/main` by those docs commits only |

**Owner notes of the objective (the nine, as recorded in the evidence).**
1. Exit codes: 2 for a record that cannot be read as a ledger, 3 for a budget refusal, 4 for a readable ledger that cannot be trusted or continued (plan 04-05; CONTEXT D-07, R-9).
2. The budget is enforced in `evals` only, limit `iterations * candidates_per_beam * beams`; the driver does not police `candidates_per_beam` or `beams` (plan 04-02).
3. `result_sha256` is the sha256 of the bytes of `results.csv`, `usage.json` and `run_summary.json` in that order; `replay` prints it and nothing stores it (plan 04-08).
4. `status` in `run_summary.json` takes `open`, `completed`, `budget_exhausted` (plan 04-08).
5. `usage.json` has five keys: the four of CONTEXT D-04 and `schema_version` (D-39; plan 04-07).
6. The fixture ids are hashes of public repeat units and tacticities, so some are also ids of the pinned table; the guards read "fixture ids and invented values" (plan 04-08).
7. Research F-25 is corrected: 39,449 distinct served values, 39,446 distinct filtered medians; each is asserted on its own basis.
8. The research cross-reference tables cite some facts under shifted numbers (the spike as F-57..F-59, the baseline as F-60); the plans cite the facts table, where the spike is F-59..F-62 and the baseline F-77.
9. The pre-registration file of Phase 7 needs its own re-include in `.gitignore` (plan 04-03, F-70).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] The "no 16-hex token in the `run_opened` line" check read fractions as ids**
- **Found during:** Task 1, while writing Test 4
- **Issue:** the plan says the `run_opened` line holds no 16-hex token; the line holds tens of thousands of floats, and the 16-digit fractional part of one (for example `0.5355339059327378`) is also a 16-hex token under a bare pattern, so the literal check would fail on a correct ledger. Plan 04-08 met the same fact (its deviation 3).
- **Fix:** the test searches for a quoted 16-hex string, which is how an id appears in a ledger; a run of the check on the real ledger finds none.
- **Files modified:** `tests/test_run_real_file.py`
- **Commit:** `5369f4c`

**2. [Rule 1 - Bug] The expected outcome "two equal ledger hashes" cannot come from the command-line verbs**
- **Found during:** Task 2 step 2, when the synthetic run was made through `campaign run`, a cut copy and `campaign resume`
- **Issue:** the plan asks the resume section to show `campaign run`, a copy cut after event 9, `campaign resume` and `sha256sum` of both ledgers, and its acceptance line says "two equal ledger hashes". The verbs stamp the wall clock (`ids.utc_now`), so the eight events a resume appends carry new `ts` values and the two ledgers hash differently (`20036c7f...` against `c252cbb8...`). Nothing is wrong with resume: with every `ts` blanked the two ledgers hash equal (`0aa773a2...`), and `results.csv` and `usage.json` are equal to the byte.
- **Fix:** the evidence shows both readings. First a fixed-identity run (fixed run id, constant clock) with a copy cut after event 9 and resumed under the same clock, where the two ledgers hash equal (`bc2370c0...`, the hash of the committed fixture ledger) and so do `results.csv`, `usage.json`, `run_summary.json` and `meta.json`; then the command-line run with its `ts`-blanked comparison, labelled as such. The byte-for-byte comparison at every one of 18 boundaries stays in the test of the first block. No source line was changed.
- **Files modified:** `.planning/phases/04-run-management/04-EVIDENCE.md`
- **Commit:** `f52ff67`

**3. [Rule 2 - Missing critical functionality] Local paths and a typing fix**
- **Issue:** the captured command output holds the absolute path of the scratch directory under a Windows user profile; the evidence is published by the push. A type error (`bisect_left` over `float | None`) also surfaced in my own test file under mypy, and the first gate run failed `ruff format --check` on it.
- **Fix:** the evidence writes the path as `$SCRATCH` (stated in its header as the only edit to any output besides pytest's progress percentages); the test filters `None` before bisecting (the length and null assertions come first) and was formatted; the gate was re-run to 7/7 before the commit.
- **Files modified:** `tests/test_run_real_file.py`, `.planning/phases/04-run-management/04-EVIDENCE.md`
- **Commit:** `5369f4c`, `f52ff67`

**Total deviations:** 2 auto-fixed bugs or plan conflicts (Rule 1), 1 set of additive items (Rule 2). **Impact on plan:** none on a source file, a schema or a pinned value; two statements of the plan's expected output are met by a different but stronger comparison (item 2) or a stricter pattern (item 1).

### Notes, no change

- **Task 1 has no separate RED commit.** The plan gives one commit for Task 1 and the code under test already existed (plans 04-02 to 04-08); the tests passed on their first run, so there was no failing state to commit. No expected value was edited at any point.
- **Reading of the pinned fixture on ubuntu-latest is inferred, not read.** The CI log prints pytest's summary line only, so the per-test line of `test_committed_fixture_ledger_reduces_to_the_pinned_bytes` on the Linux leg is not in it; that test has no skip path, both legs report `370 passed`, and it passes locally. Recorded as coverage item D8 for the owner.
- **The 22 skipped tests are not itemised by the CI log.** The evidence states the arithmetic (392 local = 370 + 22) and that the five tests of this plan skip by construction of the `real_processed` fixture.
- **No red CI run.** The first dispatched run on the pushed tip was green, so no `fix(04-09)` commit was made.
- **The dispatch matched the pushed tip on the first list**; no run of another event was cited.

## Authentication Gates

None. `gh auth status` reported a logged-in account for github.com before the push.

## TDD Gate Compliance

The plan sets `type: execute`; Task 1 is marked `tdd="true"` but tests a code path that existed, so it has one `test(04-09)` commit and no `feat`. The TDD mode gate was not active.

## Known Stubs

None. The scan of `tests/test_run_real_file.py`, `protocol/README.md` and `04-EVIDENCE.md` found no TODO, FIXME, placeholder or xfail; the one `pytest.skip` is the fixture's stated skip when the pinned parquets are absent, the established pattern of Phases 2 and 3.

## Threat Flags

None new. Register mitigations in place: T-04-45 (no id, SMILES or per-candidate value in the test file or the evidence; the 16-hex checks print 0 in both), T-04-46 (history scan immediately before the push: 130 commits, zero hits in each of ten classes, `dotenv-path-in-history: 0 hit(s)`), T-04-47 (`git ls-files experiments data/` printed four tracked files before and after the push), T-04-48 (the verify re-queried run `36695769247` by id: `workflow_dispatch main success`, both job conclusions), T-04-49 (no expected count was edited; all nine matched), T-04-50 (both legs skip the same 22 tests and pass the same 370). T-04-SC: nothing installed.

## Next Phase Readiness

The Phase 4 verifier can cite `04-EVIDENCE.md` sections (1) to (3) as ROADMAP Phase 4 success criteria 1 to 3 and the `## CI` section for the two-platform reading. Two facts for Phase 5 and 6: a population block costs about 2.9 MB in the ledger (untracked by ADR-0007), and the command-line verbs stamp the wall clock, so a byte-equal ledger comparison across a resume needs the injected clock.

## Self-Check: PASSED

- Created and modified files exist: `tests/test_run_real_file.py`, `.planning/phases/04-run-management/04-EVIDENCE.md`, `protocol/README.md`.
- Commits `5369f4c`, `0205a7f`, `f52ff67`, `fa467da` are in `git log`; `git rev-list --count 97020798e1a62c79aebdf78b6ddb3f96165317fb..HEAD` gave 4 (the measured `commits`, taken before this summary).
- Plan verification re-run: `tests/test_run_real_file.py` lists five PASSED tests; the 16-hex grep of the test file prints 0; the evidence has 3 criterion sections, 5 named sections, both pinned hashes, 20 lines naming the boundary test and a 16-hex check that prints 0; the run `36695769247` re-queried by id gives `workflow_dispatch main success check (ubuntu-latest)=success,check (windows-latest)=success` and 2 matches for each of `SUMMARY: 7/7 steps passed`, `Contracts: 5 kept, 0 broken.` and `llm4polcheck inventory: 9 entries, 16 instances processed`; `git rev-parse HEAD origin/main | sort -u` printed one revision after the final push of Task 3.
- Full gate at the last code-bearing commit: `SUMMARY: 7/7 steps passed`, 392 tests.
