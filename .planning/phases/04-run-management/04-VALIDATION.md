---
phase: "4"
slug: "run-management"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-09-29"
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution. Seeded from
> `04-RESEARCH.md` § Validation Architecture; the per-task map is filled from the plans.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.1 |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` (`testpaths = ["tests"]`, `addopts = "-q"`) |
| **Quick run command** | `PYTHONPATH=src pixi run --manifest-path env/pixi.toml python -m pytest tests/<file touched by the task> -q` |
| **Full suite command** | `pixi run --manifest-path env/pixi.toml check` |
| **Estimated runtime** | quick run 1–2 s per file; full gate about 72 s |

---

## Sampling Rate

- **After every task commit:** the quick run of the test file the task touches
- **After every plan wave:** the full gate, `SUMMARY: 7/7 steps passed`
- **Before `/gsd-verify-work`:** full gate green locally and on both CI platforms, run id recorded
- **Max feedback latency:** 90 seconds

---

## What runs where

| Layer | Runs in CI (both platforms) | Needs the real parquet (skips in CI) |
|-------|-----------------------------|--------------------------------------|
| Schemas and examples | `schema-inventory` step, schema tests | — |
| Ledger write, read, truncation, byte prefix | yes, on `tmp_path` | — |
| Campaign with a plan-file selector, crash and resume | yes, on the synthetic candidate table | — |
| Reducer and byte identity | yes; pinned sha256 of a committed fixture ledger's `results.csv` | — |
| Usage equals ledger sums | yes | — |
| Population sizes 39,454 and 40,212 | — | real-file fixture, skips with a stated reason |
| Ignore policy (ADR-0007) | yes, `git check-ignore` | — |
| Import contract and its negative probe | yes | — |

---

## Per-Task Verification Map

Filled from the plans by the planner; one row per task, quoting the task's own `<automated>` command.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 04-01-T1 | 04-01 | 1 | RUN-01, RUN-06 | T-04-01, T-04-02, T-04-03 | A problem spec is validated before it is typed; a path-like run id is refused before a path is built; a run directory cannot be created twice | unit | `PYTHONPATH=src pixi run --manifest-path env/pixi.toml python -m pytest tests/test_run_config.py tests/test_import_boundary.py` | W0: `tests/test_run_config.py`, `tests/run_support.py`; `tests/test_import_boundary.py` exists | ⬜ pending |
| 04-01-T2 | 04-01 | 1 | RUN-02 | T-04-03, T-04-04, T-04-05, T-04-06 | Every ledger line is validated on write and on read; an append only extends the file; a third cost field is refused; population arrays are admitted in `run_opened` only | unit | `PYTHONPATH=src pixi run --manifest-path env/pixi.toml python -m pytest tests/test_run_ledger.py tests/test_run_config.py` | W0: `tests/test_run_ledger.py` | ⬜ pending |
| 04-02-T1 | 04-02 | 2 | RUN-01, RUN-02, RUN-04 | T-04-07 .. T-04-13 | Invalid input creates no run directory; `meta.json` is validated before writing and holds no key value; `replay` needs the ledger only | integration (end to end, module entry point) | `PYTHONPATH=src pixi run --manifest-path env/pixi.toml python -m pytest tests/test_run_cli.py tests/test_run_config.py tests/test_run_ledger.py tests/test_import_boundary.py` | W0: `tests/test_run_cli.py` | ⬜ pending |
| 04-03-T1 | 04-03 | 2 | RUN-01, RUN-04 | T-04-14 .. T-04-17 | The four summaries are trackable and the ledger is ignored, asked of git; a summary of a PoLyInfo-derived run cannot be tracked; the run contract breaks on a violating import | unit (governance) and integration (linter probe) | `PYTHONPATH=src pixi run --manifest-path env/pixi.toml python -m pytest tests/test_governance.py tests/test_import_boundary.py` | exists: `tests/test_governance.py`, `tests/test_import_boundary.py` | ⬜ pending |
| 04-04-T1 | 04-04 | 3 | RUN-01, RUN-02, RUN-06 | T-04-18 .. T-04-21 | Committed examples equal what the code writes; no schema is edited to fit an example; examples hold fixture ids and invented values | unit and gate step `schema-inventory` | `PYTHONPATH=src pixi run --manifest-path env/pixi.toml python -m pytest tests/test_run_examples.py tests/test_check_inventory.py` | W0: `tests/test_run_examples.py`; `tests/test_check_inventory.py` exists | ⬜ pending |
| 04-05-T1 | 04-05 | 3 | RUN-02 | T-04-22, T-04-25 | A torn, duplicated or out-of-order ledger is refused and left as found | unit | `PYTHONPATH=src pixi run --manifest-path env/pixi.toml python -m pytest tests/test_run_ledger.py` | exists after 04-01: `tests/test_run_ledger.py` | ⬜ pending |
| 04-05-T2 | 04-05 | 3 | RUN-03 | T-04-22 .. T-04-27 | Cache and meter are rebuilt from the ledger; a run under other code, snapshot, registry or plan is refused; a budget refusal is recorded | integration | `PYTHONPATH=src pixi run --manifest-path env/pixi.toml python -m pytest tests/test_run_resume.py` | W0: `tests/test_run_resume.py` | ⬜ pending |
| 04-06-T1 | 04-06 | 3 | RUN-01, RUN-06 | T-04-28 .. T-04-31, T-04-33 | No key value reaches `meta.json`; its schema pins names and types; every problem spec that must be refused is refused | unit | `PYTHONPATH=src pixi run --manifest-path env/pixi.toml python -m pytest tests/test_run_config.py` | exists after 04-01: `tests/test_run_config.py` | ⬜ pending |
| 04-06-T2 | 04-06 | 3 | RUN-04 | T-04-32 | Membership follows the filter, values are the served medians | integration | `PYTHONPATH=src pixi run --manifest-path env/pixi.toml python -m pytest tests/test_run_population.py` | W0: `tests/test_run_population.py` | ⬜ pending |
| 04-07-T1 | 04-07 | 4 | RUN-04, RUN-05 | T-04-34 .. T-04-37 | Metrics follow the recorded problem, not a literal; the two currencies are never merged; `usage.json` is validated before writing | unit | `PYTHONPATH=src pixi run --manifest-path env/pixi.toml python -m pytest tests/test_run_reduce.py tests/test_check_inventory.py` | W0: `tests/test_run_reduce.py` | ⬜ pending |
| 04-08-T1 | 04-08 | 5 | RUN-04 | T-04-38 .. T-04-44 | `replay` refuses an edited file and overwrites nothing; no written file matches a scanner class; the fixture holds fixture ids and invented values only | integration and pinned-byte | `PYTHONPATH=src pixi run --manifest-path env/pixi.toml python -m pytest tests/test_run_replay.py tests/test_run_resume.py tests/test_run_cli.py tests/test_check_inventory.py` | W0: `tests/test_run_replay.py`, `tests/fixtures/run/reference-ledger.jsonl` | ⬜ pending |
| 04-09-T1 | 04-09 | 6 | RUN-03, RUN-04, RUN-05 | T-04-45, T-04-49, T-04-50 | No id literal is written into the test file; an expected count is never edited to pass | real-file (skips in CI) | `PYTHONPATH=src pixi run --manifest-path env/pixi.toml python -m pytest tests/test_run_real_file.py -v -v` | W0: `tests/test_run_real_file.py` | ⬜ pending |
| 04-09-T2 | 04-09 | 6 | RUN-01 .. RUN-06 | T-04-45 | The evidence quotes counts only from the pinned table | document check | `grep -c "^## (" .planning/phases/04-run-management/04-EVIDENCE.md` | W0: `04-EVIDENCE.md` is written by the task | ⬜ pending |
| 04-09-T3 | 04-09 | 6 | RUN-01 .. RUN-06 | T-04-46, T-04-47, T-04-48 | History is scanned before the push; the cited run is the dispatched run on the pushed tip | CI on two platforms | `gh run view $(grep -m1 -oE "CI run id: [0-9]+" .planning/phases/04-run-management/04-EVIDENCE.md \| grep -oE "[0-9]+") --json event,headBranch,conclusion,jobs --jq '[.event, .headBranch, .conclusion, ([.jobs[] \| .name + "=" + .conclusion] \| sort \| join(","))] \| join(" ")'` | n/a: reads the CI run | ⬜ pending |

`File Exists`: `W0` names a file the task itself creates in its RED step, before the code it tests; `exists` names a file an earlier plan or phase created. Every command is the first `<automated>` command of its task, quoted verbatim, except that a pipe inside a command is preceded by a backslash, as a table cell requires; each task also runs the full gate, `pixi run --manifest-path env/pixi.toml check`.

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_run_config.py`, `tests/test_run_ledger.py`, `tests/test_run_resume.py`,
      `tests/test_run_reduce.py`, `tests/test_run_cli.py`, `tests/test_run_real_file.py` — none exists
- [ ] A committed fixture ledger and the pinned sha256 of its `results.csv`
- [ ] A Phase 4 fixture that extends a copy of `SYNTHETIC_ROWS` with a row inside the triple and
      `check_tc == False`, so the two populations differ on the synthetic root; the shared constant
      is not edited
- [ ] Also created by the plans, beyond the six test files above: `tests/run_support.py` (04-01),
      `tests/test_run_examples.py` (04-04), `tests/test_run_population.py` (04-06),
      `tests/test_run_replay.py` (04-08)
- [ ] `protocol/examples/` instances for every new schema and their `[tool.llm4polcheck]` entries
- [ ] Edits to `tests/test_import_boundary.py`, `tests/test_governance.py` and
      `tests/test_check_inventory.py`

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 90s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
