---
phase: 04-run-management
verified: 2026-09-30T11:24:00Z
status: passed
score: 9/9 must-haves verified
covered_files:
  - .planning/REQUIREMENTS.md
  - .planning/phases/04-run-management/04-01-PLAN.md
  - .planning/phases/04-run-management/04-01-SUMMARY.md
  - .planning/phases/04-run-management/04-02-PLAN.md
  - .planning/phases/04-run-management/04-02-SUMMARY.md
  - .planning/phases/04-run-management/04-03-PLAN.md
  - .planning/phases/04-run-management/04-03-SUMMARY.md
  - .planning/phases/04-run-management/04-04-PLAN.md
  - .planning/phases/04-run-management/04-04-SUMMARY.md
  - .planning/phases/04-run-management/04-05-PLAN.md
  - .planning/phases/04-run-management/04-05-SUMMARY.md
  - .planning/phases/04-run-management/04-06-PLAN.md
  - .planning/phases/04-run-management/04-06-SUMMARY.md
  - .planning/phases/04-run-management/04-07-PLAN.md
  - .planning/phases/04-run-management/04-07-SUMMARY.md
  - .planning/phases/04-run-management/04-08-PLAN.md
  - .planning/phases/04-run-management/04-08-SUMMARY.md
  - .planning/phases/04-run-management/04-09-PLAN.md
  - .planning/phases/04-run-management/04-09-SUMMARY.md
  - docs/governance/ADR/0007-run-summaries-are-tracked.md
  - docs/governance/ADR/0008-run-record-format.md
  - docs/governance/DECISIONS-LOG.md
  - protocol/schemas/ledger-event.json
  - protocol/schemas/problem-spec.json
  - protocol/schemas/run-meta.json
  - protocol/schemas/run-summary.json
  - protocol/schemas/run-usage.json
  - protocol/schemas/selection-plan.json
  - src/llm4pol/run/__init__.py
  - src/llm4pol/run/__main__.py
  - src/llm4pol/run/atomic.py
  - src/llm4pol/run/config.py
  - src/llm4pol/run/ids.py
  - src/llm4pol/run/jsonio.py
  - src/llm4pol/run/ledger.py
  - src/llm4pol/run/lock.py
  - src/llm4pol/run/population.py
  - src/llm4pol/run/records.py
  - src/llm4pol/run/redaction.py
  - src/llm4pol/run/reduce.py
  - src/llm4pol/run/resume.py
  - src/llm4pol/run/selector.py
  - src/llm4pol/run/strictschema.py
  - src/llm4pol/run/summary.py
  - tests/fixtures/run/reference-ledger.jsonl
  - tests/run_support.py
  - tests/test_check_inventory.py
  - tests/test_run_atomic.py
  - tests/test_run_canonical.py
  - tests/test_run_cli.py
  - tests/test_run_config.py
  - tests/test_run_crosscheck.py
  - tests/test_run_examples.py
  - tests/test_run_git.py
  - tests/test_run_iofailure.py
  - tests/test_run_jsonio.py
  - tests/test_run_ledger.py
  - tests/test_run_lock.py
  - tests/test_run_patterns.py
  - tests/test_run_population.py
  - tests/test_run_real_file.py
  - tests/test_run_redaction.py
  - tests/test_run_reduce.py
  - tests/test_run_replay.py
  - tests/test_run_replay_out.py
  - tests/test_run_resume.py
  - tests/test_run_stray_temp.py
covered_digest: "v1:sha256:5dace701a53b261feb5f576e03f43feba00b72e50ba1724af8477556e360d88f"
behavior_unverified: 0
overrides_applied: 0
coincidental_reliance_items:
  - truth: "ADR-0008 guard: a resumed ledger equals the uninterrupted run byte for byte at every event boundary"
    reason: fixture-only
    harden: "The equality holds because the test injects a constant clock and a fixed run id; the production path stamps ids.utc_now, so a resumed ledger differs in the ts of appended events (and run_summary.json, which embeds ledger_sha256, differs with it). Still not stated in ADR-0008 or experiments/README.md at this HEAD (grep for wall-clock / injected clock finds nothing in either). State it in one sentence so the guard is not read as a wall-clock property."
gaps: []
deferred:
  - truth: "WR-04: the selector protocol hands run_opened (both full population arrays) to a selector in `history`; blindness then depends on each selector author skipping one event kind"
    addressed_in: "Phase 6"
    evidence: "Phase 6 success criterion 5: 'The A-4 payload test - nothing sent to the provider carries row ids, table size, percentiles, thresholds or global statistics - runs inside the check gate (charter section 13 M5, A-4, D-19)'. Nothing leaks in Phase 4: PlanSelector ignores history. Phase 5's deterministic selector also receives the arrays, so filter run_opened out of history there (see advisory)."
advisory:
  - finding: "WR-04 (deferred by the orchestrator): `_history_before` and `verify_replay` still pass the `run_opened` event, whose payload holds both population arrays, to every selector. Confirmed still true in resume.py `_history_before` (returns events[:position])."
    category: security
    reason: "Latent, not exploitable in Phase 4 (PlanSelector never reads history). Resolves when Phase 5 either filters run_opened out of `history` or defines a SelectorView without populations, and Phase 6's A-4 payload test covers the provider boundary."
    evidence_status: "none provided (review states nothing leaks today; I found no test that fails)"
  - finding: "IN-01 (deferred): `resume` compares only code_git_sha; `dirty` and meta.json `snapshot_sha256` are not re-checked, so a resume under an edited working tree at the same HEAD, or over a rebuilt parquet of the same snapshot id, passes."
    category: architectural
    reason: "Follows ADR-0008 item 7 as written; changing it is an owner decision that amends the ADR."
    evidence_status: "none provided"
  - finding: "IN-05 (deferred): the pinned-table tests in tests/test_run_real_file.py skip whenever data/processed/ lacks the parquets, which is always in CI. The real-table M3 evidence is reproduced on the owner's machine only; 'two-platform CI' does not cover it."
    category: other
    reason: "Accepted by the data policy (no data file is committed). On this machine all 5 real-file tests ran and passed (0 skipped in the gate)."
    evidence_status: "none provided"
  - finding: "IN-07 (deferred): three separate cost aggregations (rebuild_state, _cost, usage_of) and a mutable payload dict inside frozen Event objects."
    category: architectural
    reason: "They agree on every ledger the gate builds; `_finish` runs usage_of (which cross-checks event costs against result costs) before Outcome is built. Freeze the payload or deep-copy at the selector boundary when Phase 5 lands."
    evidence_status: "none provided"
  - finding: "Carried from the earlier verification, still true: exit code for resume on an already closed run is 0 with nothing appended; exit 3 is returned only by the call that appends the budget run_closed (Outcome.appended). Consistent with R-9 and D-40."
    category: other
    reason: "Recorded so the exit-code table (0, 2, 3, 4, 5, 6) is read with this idempotence rule."
    evidence_status: "none provided"
human_verification:
  - test: "Push local main (23 commits ahead of origin/main, the 18 Phase 4 fix commits among them) and run the check workflow on ubuntu-latest and windows-latest (`gh workflow run ci.yml`, or the push trigger), then `gh run view <id>`."
    expected: "Both matrix legs report success at the pushed tip: SUMMARY 7/7 steps passed, `Contracts: 5 kept, 0 broken.`, `llm4polcheck inventory: 9 entries, 16 instances processed`, and the pinned fixture reduces to results_sha256 0e31cfc3... on both legs."
    why_human: "The only CI run on record (36695769247) was at f52ff67, before the code review fixes. The fixes added POSIX-only branches (fcntl.flock in lock.py, os.link publish and directory fsync in atomic.py) that this Windows machine cannot execute for real, and no WSL or Docker is available here. Pushing to the remote is an owner action the verifier does not take."
---

# Phase 4: Run Management Verification Report

**Phase Goal:** A campaign leaves an append-only run record under `experiments/<run-id>/` that can be resumed without duplicate events and replayed to a byte-identical `results.csv` (charter section 13 M3).
**Verified:** 2026-09-30T11:24:00Z, at HEAD `dc3de4a`
**Status:** human_needed
**Re-verification:** Yes, at the current HEAD. The previous report (status passed, 8/8, at `f52ff67`) predates 18 review-fix commits (24 commits in all, `fc994e3` to `dc3de4a`); it carried no `gaps:`, so every truth was re-derived, not spot-checked.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | SC1: an interrupted run, resumed, records zero duplicate `(run_id, iteration, beam)` events and continues where the ledger stops, also when a second process tries to resume the same run | VERIFIED | Code: `drive` takes `lock.held(ledger)` before it reads anything; `_drive_locked` rebuilds cache, meter and recorded keys from the ledger (`rebuild_state`) and skips each recorded key; `ledger.append` calls `_require_next` (tail `seq` + 1, not after `run_closed`, same run id); `ledger.read` refuses a repeated event key. Tests: `test_resume_at_every_event_boundary_is_byte_identical` (18 boundaries, run by name: passed), `test_real_run_resumes_to_the_same_bytes` on the pinned table (passed, not skipped), `test_drive_refuses_a_locked_run_and_appends_nothing` and `test_the_cli_refuses_a_locked_run_with_its_own_exit_code` (a real second process holds the lock: exit 6, ledger bytes unchanged). My own race: on the synthetic table, 4 real `resume` processes started at once over a run cut after 0, 3, 5 and 9 events. In every case exactly one exited 0 and three exited 6 (`ERROR: run is in use by another process`); the final ledger reads cleanly, 17 events (the reference count), 17 distinct event keys, closed, five files present. |
| 2 | SC2: `replay` regenerates `results.csv` from `ledger.jsonl` alone, byte-identical | VERIFIED | I copied only `tests/fixtures/run/reference-ledger.jsonl` (sha256 `bc2370c0...`, unchanged since `f52ff67`) into a scratch run directory and ran `replay --out`. In the same process `numpy`, `pandas` and `pyarrow` were not in `sys.modules`. Output: `results_sha256 0e31cfc380aaaf9f86a68b5e83986ad34ce57cd3c4704634ea2de840f0512fc6` (pinned), `usage.json` `bb11fcba...` (pinned), `run_summary.json` `8190025e...`; the last two are `cmp`-identical to `protocol/examples/run-usage.example.json` and `run-summary.example.json`. The canonical-form check added by WR-02 accepts the committed fixture byte for byte. |
| 3 | SC3: `usage.json` `evals` and `cpu_hours` equal the ledger sums, kept as two currencies (A-3) | VERIFIED | A plain-`json` sum over the fixture (no llm4pol import): evals 5, cpu_hours 0.0. `python -m llm4pol.run usage` prints `{"cpu_hours": 0.0, "evals": 5, "schema_version": 1, "tokens": 0, "usd": 0.0}`. `usage_of` sums `evals` as an integer and `cpu_hours` with `math.fsum`, refuses an event whose cost is not its results' sum, and never combines the currencies. `test_usage_equals_the_ledger_sums_in_two_currencies` passed by name. |
| 4 | The run record is five files with schemas and committed examples; the ledger carries the populations `replay` needs (RUN-01, RUN-02, RUN-04, ADR-0008) | VERIFIED | Six closed schemas in `protocol/schemas/`; 15 files in `protocol/examples/`, unchanged since `f52ff67` (`git diff` empty) and validated and reproduced by `test_run_examples.py` in the 589-test run. The only schema edits since then are `\d` to `[0-9]` in run-id and timestamp patterns (WR-07), semantically identical on ASCII. `run_opened` still carries per-population objective and constraint arrays; the replay above needed no parquet. |
| 5 | A-6: the run directory is append-only, a rerun gets a new id | VERIFIED | `create_run_dir` uses `mkdir(exist_ok=False)`, `ledger.create` opens with `xb`, `append` writes one fsynced LF-terminated line after a tail check, `atomic.write_new` publishes without overwrite (`os.link` on POSIX, `os.rename` on Windows, both refuse an existing target). Independent negative checks on copies of the fixture (`usage` verb): torn tail (20 bytes cut) exit 2, not repaired; CRLF-converted ledger exit 2; a line with a space after a colon exit 2; one evaluation event duplicated with `seq` renumbered exit 4; untouched fixture exit 0. |
| 6 | ADR-0007: four summaries trackable, ledger ignored | VERIFIED | `tests/test_governance.py` asks `git check-ignore` (in the passing run); `git ls-files experiments data` lists `experiments/README.md` and the data manifests and READMEs only. |
| 7 | Problem specs validate against `protocol/schemas/problem-spec.json` (RUN-06) | VERIFIED | `load_problem_spec` validates before any object or directory exists; `test_problem_spec_refusals` and the new `test_run_crosscheck.py` (population constraint keys against the header problem) pass. `strictschema.validator_class` makes every `pattern` a `re.fullmatch` with `re.ASCII`, and `test_check_inventory.py` asserts every schema pattern is anchored `^...$`. |
| 8 | Import boundary and the local gate hold at HEAD | VERIFIED | `Contracts: 5 kept, 0 broken.`, including `llm4pol.run never imports llm4pol.loop or llm4pol.llm`. No module of `llm4pol.run` imports `loop` or `llm`; the new modules `lock`, `atomic`, `records`, `redaction`, `strictschema` import the standard library, `jsonschema` and sibling `run` modules only. `replay` loads no dataframe library (checked above; `test_replay_and_usage_need_no_table_and_no_dataframe_library` passed). Gate below. |
| 9 | The seven-step gate is green in one `workflow_dispatch` run on windows-latest and ubuntu-latest at the tip that holds the phase's code (04-09 must-have 7) | VERIFIED | Pushed `fa467da..dc3de4a`; run 36708444014 (`workflow_dispatch`, head `dc3de4a`, which holds every review fix and D-40): `check (ubuntu-latest)` success - `Contracts: 5 kept, 0 broken.`, `563 passed, 26 skipped`, `SUMMARY: 7/7 steps passed`; `check (windows-latest)` success - `567 passed, 22 skipped`, `SUMMARY: 7/7 steps passed`. The four extra skips on ubuntu are exactly the `rename` variants of the `publish_mode` fixture in `tests/test_run_atomic.py` (skipif `os.name != "nt"`; used by 4 test instances), so the POSIX `os.link` publish, `fsync_dir` and `fcntl.flock` lock paths ran on Linux. Closed by the orchestrator 2026-09-30 after the human item below. |

**Score:** 8/9 truths verified (0 present, behavior-unverified; 1 uncertain, routed to human verification)

The charter section 13 M3 exit row has three checks: zero duplicate events after resume, byte-identical replay, and `usage.json` equal to the ledger sums in two currencies. Truths 1 to 3 cover them one to one, and all three still hold after the fixes, including under a concurrent second process.

### Preservation Check on the Fixes

| Concern | Result |
|---------|--------|
| Resume, zero duplicates, 18 boundaries | Preserved. Byte identity of ledger, `results.csv`, `usage.json`, `run_summary.json` at every boundary passed in the gate. |
| Concurrent second process | New guarantee, verified (truth 1). Lock is released by the OS on process death; `test_a_lock_held_by_another_process_refuses_and_dying_releases_it` passed in the gate. |
| Byte-identical replay of the pinned fixture | Preserved; fixture and the three hashes unchanged, reproduced independently (truth 2). |
| Usage = ledger sums, two currencies | Preserved (truth 3). |
| Committed `protocol/examples` | Byte-unchanged since `f52ff67`; reproduced by code under the fixed identity. |
| Import-boundary contracts | Preserved, 5 kept, 0 broken. |
| Package size rule | `reduce.py` 399 lines, `resume.py` 399, `ledger.py` 328; new helpers live in small modules. |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/llm4pol/run/{ids,ledger,config,resume,reduce}.py` | the five modules of the charter row | VERIFIED | Present, wired through `__main__.py`. Also `jsonio`, `population`, `selector`, `summary`, and since the fixes `lock`, `atomic`, `records`, `redaction`, `strictschema`. |
| `protocol/schemas/{ledger-event,problem-spec,run-meta,run-usage,run-summary,selection-plan}.json` | frozen run record | VERIFIED | Closed schemas; 9 inventory entries, 16 instances. |
| `experiments/README.md` | updated layout | VERIFIED | Five-file layout and tracking policy; the only tracked file under `experiments/`. |
| `tests/test_run_*.py`, `tests/fixtures/run/reference-ledger.jsonl`, `tests/test_check_inventory.py` | guards | VERIFIED | 589 tests in the gate. New guard files: atomic, canonical, crosscheck, git, iofailure, jsonio, lock, patterns, redaction, replay_out, stray_temp. |
| `docs/governance/DECISIONS-LOG.md` D-40 | exit codes 5 and 6 recorded | VERIFIED | D-40 present; `__main__` docstring and `EXIT_IO = 5`, `EXIT_LOCKED = 6` agree with it. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `__main__._run` | `resume.open_run` then `resume.drive` | call | WIRED | `drive` locks the ledger; `RunLocked` maps to exit 6, `RecordWriteError` to exit 5 (caught before the `OSError` in `_INPUT_ERRORS`) |
| `__main__._resume` | `resume.resume` then `drive` | call | WIRED | problem from the ledger header; no option relaxes a check |
| `resume.drive` | `lock.held`, `atomic.remove_stray_temporaries`, `ledger.read`, `rebuild_state`, `Evaluator` | call under the lock | WIRED | order: lock, clear strays, read, verify replay prefix, rebuild, drive |
| `resume._Recorder.emit` | `ledger.append` | call | WIRED | `append` re-checks the tail on disk |
| `reduce.write_outputs` | `atomic.write_new_or_keep` | call | WIRED | equal bytes are kept, different bytes raise `LedgerIntegrityError` (exit 4) |
| `__main__._replay`, `_usage` | `reduce.render_outputs`, `render_usage` | call, no lock | WIRED | independent run above |
| `ledger` / `reduce` / `config` | `strictschema.validator_class` | call | WIRED | fullmatch and ASCII patterns for every run schema |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `results.csv` | `Row` cells | ledger events plus `run_opened` population arrays | yes (fixture replay; pinned-table run, 5 real-file tests passed locally) | FLOWING |
| `usage.json` | `evals`, `cpu_hours` | `evaluation` event result costs | yes (5 and 0.0, equals plain-json sum) | FLOWING |
| `run_opened` population | objective and constraint arrays | `population.capture` over the candidate parquet | yes (real-file tests on the pinned table passed) | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| replay from the ledger alone, no dataframe library | `python -m llm4pol.run replay --run 20260101T000000Z-00000000 --experiments <scratch> --out <scratch>` | exit 0, `results_sha256 0e31cfc3...`, outputs equal the committed examples | PASS |
| usage sums | `python -m llm4pol.run usage ...` and a plain-json sum | evals 5, cpu_hours 0.0 on both | PASS |
| four concurrent `resume` processes | scratch script over cuts 0, 3, 5, 9 | one exit 0, three exit 6, ledger valid, 17 events, no duplicate key | PASS |
| torn tail, CRLF, spaced line, duplicated event | `usage` on edited copies | exits 2, 2, 2, 4 | PASS |
| named guards | pytest by node id: boundary sweep (18), lock refusals (2), pinned fixture, two-currency usage, no-dataframe replay, `test_run_real_file.py` | 28 passed | PASS |
| full gate | `pixi run --manifest-path env/pixi.toml check` (run once) | `SUMMARY: 7/7 steps passed`; `589 passed in 141.31s`; `Contracts: 5 kept, 0 broken.`; `llm4polcheck inventory: 9 entries, 16 instances processed`; history scan 0 hits | PASS |

### Probe Execution

No `probe-*.sh` is declared or present. SKIPPED (not applicable).

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| RUN-01 | 04-01, 04-02, 04-03, 04-04, 04-06, 04-09 | run id and `meta.json` | SATISFIED | `new_run_id`, `build_meta`, `validate_meta`; redaction widened (WR-05, RR-6) and the committed run-meta example redacts to itself |
| RUN-02 | 04-01, 04-02, 04-04, 04-05, 04-09 | append-only ledger inside `run_opened` and `run_closed`; rerun gets a new id | SATISFIED | truths 4 and 5; `append` tail check and the run lock strengthen it |
| RUN-03 | 04-05, 04-09 | `resume` never records the same key twice | SATISFIED | truth 1, now also against a concurrent second process |
| RUN-04 | 04-02, 04-03, 04-06, 04-07, 04-08, 04-09 | `replay` byte-identical; populations in the ledger | SATISFIED | truths 2 and 4 |
| RUN-05 | 04-07, 04-09 | `usage.json` equals ledger sums; tokens and USD apart | SATISFIED | truth 3 |
| RUN-06 | 04-01, 04-06 | problem specs validate against the schema | SATISFIED | truth 7 |

All six IDs appear in plan frontmatter; none is orphaned.

**Traceability correction still needed in `.planning/REQUIREMENTS.md`** (I did not edit it, as instructed). RUN-01 and RUN-04 are ticked; RUN-02, RUN-03, RUN-05 and RUN-06 are still unchecked (lines 42, 43, 45, 46) and `Pending` (lines 130, 131, 133, 134), and each is satisfied. Editing the file changes `covered_digest`, since it is in `covered_files`; regenerate the fingerprint afterwards. `.planning/ROADMAP.md` also still shows Phase 4 as open.

### Judgment of the Recorded Deviations

1. **Resumed CLI ledger differs from the uninterrupted one in `ts`. Accepted, still.** The exit criterion attaches byte identity to `replay`, and the ADR-0008 guard is met under the injected clock. Under the wall clock `run_summary.json` differs too, through its embedded `ledger_sha256`. The one sentence recommended last time is still absent from ADR-0008 and `experiments/README.md`; it stays as the `coincidental_reliance_items` entry.
2. **Exit codes.** D-07 and R-9 give 0, 2, 3, 4; D-40 (`dc3de4a`) adds 5 (write failure) and 6 (run locked). Code, `__main__` docstring and DECISIONS-LOG agree. Reading a torn line stays 2; writing that fails is 5.
3. **Ubuntu pinned-fixture PASS inferred from CI at `f52ff67`.** Superseded: CI must be re-run at the new tip (truth 9, human item).
4. **Review findings.** CR-01, WR-01, WR-02, WR-03, WR-05, WR-06, WR-07, IN-02, IN-03, IN-04, IN-06 (partly) and RR-2 to RR-6, RR-8 are fixed and each has a guard file; I confirmed the CR-01 fix by racing real processes. WR-04, IN-01, IN-05, IN-07 remain deferred by the orchestrator (see `deferred:` and `advisory:`). IN-06 remains partial by the fixer's own account: `run_closed(completed)` after every budget iteration and result coverage of the property keys are not checked by the reader. That is a hardening gap, not a must-have.

### Anti-Patterns Found

None. A scan of `src/llm4pol/run`, `tests/test_run_*.py`, `tests/run_support.py`, `tests/test_check_inventory.py`, the schemas and `experiments/README.md` for TBD, FIXME, XXX, TODO, HACK, placeholder, NotImplemented and xfail found nothing. The `except OSError: pass` in `atomic.write_new`'s `finally` is deliberate and documented (a stray temporary is cleared by the next resume, RR-4). Skips are limited to the real-file fixture (with a stated reason) and one platform `skipif` in `test_run_atomic.py`.

### Human Verification Required

### 1. CI on both platforms at the current tip - RESOLVED 2026-09-30 (run 36708444014, both legs success at `dc3de4a`; see truth 9)

**Test:** Push `main` and run the `check` workflow (push trigger or `workflow_dispatch`), then `gh run view <id>`.
**Expected:** `check (ubuntu-latest)` and `check (windows-latest)` both `success`, each with `SUMMARY: 7/7 steps passed`, `Contracts: 5 kept, 0 broken.` and `9 entries, 16 instances processed`.
**Why human:** the recorded CI run predates the review fixes, and the POSIX code paths they added cannot run on this machine. Pushing is an owner action.

### Gaps Summary

No code gaps. All three charter M3 exit checks hold at HEAD and survived the review fixes, including a new guarantee that a second process cannot write the same run. One item is open and is not a defect: the fix commits have never been through the two-platform CI, so the Linux leg is unproven. Housekeeping remains as before: the REQUIREMENTS.md and ROADMAP.md ticks and one sentence on wall-clock resume.

---

_Verified: 2026-09-30T11:24:00Z_
_Verifier: Claude (gsd-verifier)_
