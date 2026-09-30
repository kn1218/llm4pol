---
phase: 04-run-management
verified: 2026-09-30T12:00:00Z
status: passed
score: 8/8 must-haves verified
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
  - protocol/schemas/ledger-event.json
  - protocol/schemas/problem-spec.json
  - protocol/schemas/run-meta.json
  - protocol/schemas/run-summary.json
  - protocol/schemas/run-usage.json
  - protocol/schemas/selection-plan.json
  - src/llm4pol/run/__init__.py
  - src/llm4pol/run/__main__.py
  - src/llm4pol/run/config.py
  - src/llm4pol/run/ids.py
  - src/llm4pol/run/jsonio.py
  - src/llm4pol/run/ledger.py
  - src/llm4pol/run/population.py
  - src/llm4pol/run/reduce.py
  - src/llm4pol/run/resume.py
  - src/llm4pol/run/selector.py
  - src/llm4pol/run/summary.py
  - tests/fixtures/run/reference-ledger.jsonl
  - tests/run_support.py
  - tests/test_run_cli.py
  - tests/test_run_config.py
  - tests/test_run_examples.py
  - tests/test_run_ledger.py
  - tests/test_run_population.py
  - tests/test_run_real_file.py
  - tests/test_run_reduce.py
  - tests/test_run_replay.py
  - tests/test_run_resume.py
covered_digest: "v1:sha256:699f4f64cbc2b29dc3cd0c54ade2d98f7524bc619741da0801ca5df0dc5a79ba"
behavior_unverified: 0
overrides_applied: 0
coincidental_reliance_items:
  - truth: "ADR-0008 guard: a resumed ledger equals the uninterrupted run byte for byte at every event boundary"
    reason: fixture-only
    harden: "The equality holds because the test injects a constant clock and a fixed run id; the production path stamps ids.utc_now, so a resumed ledger differs in the ts of appended events (and run_summary.json, which embeds ledger_sha256, differs with it). State this in ADR-0008 / experiments/README.md so the guard is not read as a wall-clock property."
gaps: []
---

# Phase 4: Run Management Verification Report

**Phase Goal:** A campaign leaves an append-only run record under `experiments/<run-id>/` that can be resumed without duplicate events and replayed to a byte-identical `results.csv` (charter section 13 M3).
**Verified:** 2026-09-30
**Status:** passed
**Re-verification:** No, initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | SC1: an interrupted run, resumed, records zero duplicate `(run_id, iteration, beam)` events and continues where the ledger stops | VERIFIED | `resume.py` derives cache, meter and recorded keys from the ledger only (`rebuild_state`) and skips every recorded key in `_drive_iteration`. `ledger.read` refuses a repeated event key. `test_resume_at_every_event_boundary_is_byte_identical` (18 boundaries) and `test_real_run_resumes_to_the_same_bytes` (pinned table) are in the 392 passing tests of my own gate run. Independent check: a ledger with one evaluation event duplicated (seq renumbered) gives `duplicate event ('evaluation', 1, 'full', ...)`, exit 4. A torn final line gives exit 2 and is not repaired. |
| 2 | SC2: `replay` regenerates `results.csv` from `ledger.jsonl` alone, byte-identical | VERIFIED | I copied only `tests/fixtures/run/reference-ledger.jsonl` into a scratch run directory and ran `python -m llm4pol.run replay --out`. It printed `results_sha256 0e31cfc3...`, the pinned hash, and wrote `usage.json` `bb11fcba...` and `run_summary.json` `8190025e...`, equal to the committed values. `reduce.py` imports no dataframe library. |
| 3 | SC3: `usage.json` `evals` and `cpu_hours` equal the ledger sums, kept as two currencies (A-3) | VERIFIED | Independent sum over the fixture ledger (plain json, no llm4pol): evals 5, cpu_hours 0.0. `replay` gives `usage.json` `{"cpu_hours": 0.0, "evals": 5, "tokens": 0, "usd": 0.0, "schema_version": 1}`. `usage_of` uses an integer sum and `math.fsum` and never combines them. `run-usage.json` and the ledger `$defs/cost` are closed with exactly the two fields. `test_a3_ledger_schema_keeps_the_two_currencies_apart` passes. |
| 4 | The run record is frozen as five files with schemas and committed examples; the ledger carries the populations `replay` needs (RUN-01, RUN-02, RUN-04, ADR-0008) | VERIFIED | `protocol/schemas/` holds ledger-event, problem-spec, run-meta, run-usage, run-summary and selection-plan. `protocol/examples/` holds 15 files. `test_run_examples.py` checks that the code reproduces them. `run_opened` carries objective and constraint arrays per population, and `replay` never opens a parquet. `meta.json` example carries code git sha, seed, snapshot and its sha256, prompt_versions, provider/model. |
| 5 | A-6 (append-only run directory, rerun gets a new id) is a test | VERIFIED | `create_run_dir` uses `mkdir(exist_ok=False)`. `ledger.create` opens the file exclusively. `ledger.append` writes one LF-terminated line and fsyncs. The four `test_a6_*` tests and the truncation-at-every-byte test are in the passing run. INVARIANTS.md A-6 row lists them. |
| 6 | ADR-0007 tracking policy holds: four summaries trackable, ledger ignored | VERIFIED | `git check-ignore -v` on a probe path: `.gitignore:46` ignores `experiments/*/ledger.jsonl`, and the four summary names are re-included at lines 47 to 50. `git ls-files experiments data` prints the README and manifests only. |
| 7 | Problem specs validate against `protocol/schemas/problem-spec.json` (RUN-06) | VERIFIED | `test_problem_spec_refusals` has 25 refusal cases (extra keys, pareto form, weighted-sum form, barred keys, direction, seeds, wrong table and others). `load_problem_spec` runs before any directory is created. The same block sits inside the ledger header schema. |
| 8 | Package boundary holds and the gate is green on both platforms | VERIFIED | The `llm4pol.run` forbidden contract for `llm4pol.loop` and `llm4pol.llm` is in `pyproject.toml`; `Contracts: 5 kept, 0 broken.` My gate run: `SUMMARY: 7/7 steps passed`, 392 passed. CI run 36695769247 (`workflow_dispatch`, main, head `f52ff67`): `gh` reports both jobs success. |

**Score:** 8/8 truths verified (0 present, behavior-unverified)

The charter section 13 M3 exit row has three checks: zero duplicates after resume, byte-identical replay, and `usage.json` equal to the ledger sums in two currencies. Truths 1 to 3 cover them one to one.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/llm4pol/run/{ids,ledger,config,resume,reduce}.py` | the five modules of the charter row | VERIFIED | All exist (64, 399, 365, 376, 397 lines) and are wired through `__main__.py`. Also present: `jsonio`, `population`, `selector`, `summary`. |
| `protocol/schemas/ledger-event.json`, `problem-spec.json` | frozen run record and problem spec | VERIFIED | Closed schemas; in the `schema-inventory` step (9 entries, 16 instances). |
| `experiments/README.md` | updated layout | VERIFIED | Five-file layout and the tracking policy are present; the README is the only tracked file in `experiments/`. |
| `tests/test_run_*.py`, `tests/fixtures/run/reference-ledger.jsonl` | guards | VERIFIED | `sha256sum` of the fixture equals `bc2370c0...`, the constant the test pins. No TODO, FIXME, xfail or skip in these files, apart from the one stated skip of the real-file fixture. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `__main__._run` | `resume.open_run` and `resume.drive` | call | WIRED | `run` prints `run_id`, `evals`, `cpu_hours`, `results_sha256` |
| `__main__._resume` | `resume.resume` | call, problem taken from the ledger header | WIRED | no option relaxes a check |
| `resume.drive` | `reduce.write_outputs` | `_finish` | WIRED | outputs come from the recorded ledger |
| `__main__._replay` and `_usage` | `reduce.render_outputs` and `render_usage` | call | WIRED | independent run above |
| `resume.rebuild_state` | `Evaluator(cache, meter)` | rebuilt from `evaluation` events | WIRED | this is what makes a resumed run identical |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `results.csv` | `Row` cells | ledger events plus `run_opened` population arrays | yes (fixture replay above; pinned-table run in `04-EVIDENCE.md`) | FLOWING |
| `usage.json` | `evals`, `cpu_hours` | `evaluation` event costs | yes | FLOWING |
| `run_opened` population | objective and constraint arrays | `population.capture` reading the candidate parquet | yes (39,454 and 40,212 members, tests pass on the pinned table on this machine) | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| replay from ledger alone | `python -m llm4pol.run replay --run 20260101T000000Z-00000000 --experiments <scratch> --out <scratch>` | exit 0, results hash `0e31cfc3...` | PASS |
| duplicate event refused | `usage` on a ledger with one evaluation duplicated | exit 4, `duplicate event` | PASS |
| torn tail refused | `usage` on a ledger cut 20 bytes short | exit 2, offset and byte count on stderr | PASS |
| two-currency sum | plain-json sum over the fixture | evals 5, cpu 0.0, no duplicate keys | PASS |
| full gate | `pixi run --manifest-path env/pixi.toml check` | `SUMMARY: 7/7 steps passed` | PASS |

### Probe Execution

No `probe-*.sh` is declared or present under `scripts/`. SKIPPED (not applicable).

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| RUN-01 | 04-01, 04-02, 04-03, 04-04, 04-06, 04-09 | run id and `meta.json` | SATISFIED | `new_run_id`, `build_meta`, `validate_meta`; run-meta schema and example carry all listed fields |
| RUN-02 | 04-01, 04-02, 04-04, 04-05, 04-09 | append-only ledger, one event per selection, candidate and iteration close, inside `run_opened` and `run_closed`; rerun gets a new id | SATISFIED | schema event enum, `ledger.py`, A-6 tests, `seq` and lifecycle checks in `ledger.read` |
| RUN-03 | 04-05, 04-09 | `resume` never records the same key twice | SATISFIED | truth 1 |
| RUN-04 | 04-02, 04-03, 04-06, 04-07, 04-08, 04-09 | `replay` regenerates `results.csv` and `run_summary.json`, byte-identical; the ledger carries the populations | SATISFIED | truth 2, truth 4 |
| RUN-05 | 04-07, 04-09 | `usage.json` equals the ledger sums; tokens and USD apart | SATISFIED | truth 3 |
| RUN-06 | 04-01, 04-06 | problem specs validate against the schema | SATISFIED | truth 7 |

All six IDs appear in the plan frontmatter (04-09 declares all six). No requirement mapped to Phase 4 is orphaned.

**Traceability correction needed in `.planning/REQUIREMENTS.md`.** RUN-01 and RUN-04 are marked Complete and both are confirmed by the evidence above, so the early ticks were correct in outcome. RUN-02, RUN-03, RUN-05 and RUN-06 are still unchecked and shown Pending, and each is also satisfied. Fix: tick lines 42, 43, 45 and 46 and set lines 130, 131, 133 and 134 to `Complete`. I did not edit the file; the orchestrator should do so with the phase completion. `.planning/ROADMAP.md` line 44 (`- [ ] **Phase 4: Run Management**`) is also still open although the phase detail says 9/9 executed. Editing REQUIREMENTS.md changes `covered_digest`, since that file is in `covered_files`, so regenerate the fingerprint after the edit.

### Judgment of the Recorded Deviations

1. **Resumed CLI ledger differs from the uninterrupted one in `ts` (04-09). Accepted; the exit criterion does not require it.** The M3 exit criterion reads "중단→resume 후 중복 이벤트 0; replay byte-identical". Zero duplicates is a property of event keys, which is proven at 18 boundaries and on the pinned table. Byte identity in the charter is attached to `replay`, that is, to the reduced files derived from a ledger, not to a ledger that carries a wall-clock `ts` by design; a ledger resumed later cannot carry the same wall-clock times. Charter L2 (line 32) says "resume/replay byte-identical" loosely, and the ADR-0008 guard says "resumed ledger and `results.csv` equal the bytes of the uninterrupted run"; that guard is met under the injected clock, and the evidence says so openly. The CLI evidence shows `results.csv` and `usage.json` identical under the real clock, and the `ts`-blanked ledger hashes equal (`0aa773a2...`). One correction to the framing in the request: `run_summary.json` is byte-identical only under the injected clock. It embeds `ledger_sha256`, and the two CLI ledger hashes differ (`20036c7f...` and `c252cbb8...`), so under the wall clock the resumed run's `run_summary.json` differs from the uninterrupted one in that field. The CLI evidence does not compare it and does not claim to. This does not affect any exit-criterion check, but it should be stated in one sentence in ADR-0008 or `experiments/README.md`. Advisory, not a gap.
2. **Exit codes 2, 3, 4 and resume on a closed run returning 0 (04-05). Consistent.** D-07 gives 0, 2 (schema, IO) and 4 (sequence mismatch or duplicate event). R-9, later and at ADR level, adds 3 for a budget refusal that records `run_closed`. The code follows this: a torn final line or unreadable record is 2, which fits D-07's IO class; a duplicate, `seq` gap, lifecycle break or header naming other code, snapshot or selector is 4, which extends D-07's 4 to the refusals ADR-0008 item 7 introduces without naming a code. Exit 3 is returned only by the call that appends the budget `run_closed` (`Outcome.appended`), so `resume` on an already closed run returns 0 and appends nothing; that is idempotent and does not contradict R-9, which speaks of the refusal, not of later reads. I ran the 2 and 4 paths myself. The choice is recorded as an owner note in `04-EVIDENCE.md`. Info.
3. **Ubuntu pinned-fixture test PASS inferred (04-09 D8). Acceptable.** I read `gh run view 36695769247 --log`. It contains only `370 passed, 22 skipped` per leg and `SUMMARY: 7/7 steps passed`, because `addopts = "-q"`, so the per-test line is absent. The inference is sound rather than statistical: `test_committed_fixture_ledger_reduces_to_the_pinned_bytes` has no skip path (no skip, xfail or skipif in `test_run_replay.py`, and its fixtures do not use `real_*`), it is collected on both legs, and a failure would have failed the pytest step and the job, which both report success. `.gitattributes` forces `eol=lf`, so the raw fixture bytes match on Windows. The 22 skips fit the real-file tests (5 + 10 + 4 in the three `*_real_file.py` files, 3 more in `test_data_invariants.py`). Optional hardening: add `-rA` or a `-v -v` step to the workflow so the line is readable; not needed for M3.
4. **Local `main` is one commit ahead of `origin/main` (`15ddb63`). Fine.** `git diff --stat f52ff67 HEAD` touches only `.planning/ROADMAP.md`, `.planning/STATE.md`, `04-09-SUMMARY.md` and `04-EVIDENCE.md`. No source, test, schema or example changed after the CI-tested tip, so the CI reading of the exit criterion applies to the current code. Push before the phase is closed so that `origin/main` matches.

### Anti-Patterns Found

None. The scan of `src/llm4pol/run`, `tests/test_run_*.py`, `tests/run_support.py`, the run schemas and `experiments/README.md` for TBD, FIXME, XXX, TODO, HACK, placeholder, NotImplemented and xfail found nothing. The single `pytest.skip` (`tests/test_run_real_file.py:66`) is the real-file fixture's skip with a stated reason, the pattern of Phases 2 and 3.

### Notes

- **SC1 wording.** "continues from the last closed iteration" is met in a stronger form: the run continues at the first unrecorded event key inside an open iteration, so no completed candidate is re-evaluated or re-recorded.
- **Real interruption.** A process killed between appends leaves a whole-line prefix (one fsynced LF-terminated line per append), which resumes cleanly. A torn last line, possible only on a mid-write power loss, is refused with exit 2 and not repaired, as ADR-0008 item 7 decides. Tests simulate interruption by cutting at event boundaries, not by killing a process; the equivalence follows from one line per append.
- **ADR-0008 freeze.** ADR-0008 says each item is open to owner revision before the format freezes at M3 exit. The agent decided these items under the owner's delegation of 2026-09-29. The owner may want to read ADR-0008 before Phase 5 builds on it, but no gap exists in the codebase.
- **New event kinds.** The ledger schema states that event kinds added in Phases 5 and 6 arrive as a new schema version in a new file. RUN-02 says the kinds join "without changing the envelope"; the envelope is unchanged, so the two agree.

### Human Verification Required

None.

### Gaps Summary

No gaps. All three charter M3 exit checks are reproduced by tests that pass in my own gate run, and the replay, duplicate and torn-tail behaviours were re-checked independently of the phase's own tests. The remaining items are documentation housekeeping: the REQUIREMENTS.md and ROADMAP.md ticks, one sentence on wall-clock resume and `run_summary.json`, and pushing the last docs commit.

---

_Verified: 2026-09-30_
_Verifier: Claude (gsd-verifier)_
