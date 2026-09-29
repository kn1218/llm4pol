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

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_run_config.py`, `tests/test_run_ledger.py`, `tests/test_run_resume.py`,
      `tests/test_run_reduce.py`, `tests/test_run_cli.py`, `tests/test_run_real_file.py` — none exists
- [ ] A committed fixture ledger and the pinned sha256 of its `results.csv`
- [ ] A Phase 4 fixture that extends a copy of `SYNTHETIC_ROWS` with a row inside the triple and
      `check_tc == False`, so the two populations differ on the synthetic root; the shared constant
      is not edited
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
