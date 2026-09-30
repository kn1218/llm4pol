---
gsd_state_version: "1.0"
milestone: v1.0
current_phase: 04
current_phase_name: Run Management
current_plan: 9
status: executing
stopped_at: Completed 04-08-PLAN.md
last_updated: "2026-09-30T09:00:37.403Z"
last_activity: 2026-09-30
last_activity_desc: Phase 04 execution started
state_head: b117ebccaf4d8b16cc723a7779bcffc3d23c1f15
progress:
  total_phases: 8
  completed_phases: 0
  total_plans: 19
  completed_plans: 18
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-09-21)
Charter: docs/MASTER-PLAN.md v1.0 (approved 2026-09-21, ADR-0005) — highest source of truth (ADR-0002)

**Core value:** The loop attributes a measured gain to a design axis under a matched evaluation budget — if that attribution is not reproducible, nothing else the system produces is a result (charter §1).
**Current focus:** Phase 04 — Run Management

## Current Position

Phase: 04 (Run Management) — EXECUTING
Current Plan: 9
Total Plans in Phase: 9
Status: Ready to execute
Last activity: 2026-09-30 — Phase 04 execution started

Progress: [████░░░░░░] 38%

## Performance Metrics

**Velocity:**

- Total plans completed: 9
- Average duration: — min
- Total execution time: 0.0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1 | 1 | - | - |
| 2 | 5 | - | - |
| 3 | 3 | - | - |

**Recent Trend:**

- Last 5 plans: —
- Trend: —

*Updated after each plan completion*
**Per-Plan Metrics:**

| Plan | Duration | Tasks | Files |
|------|----------|-------|-------|
| Phase 01 P01 | 12 min | 3 tasks | 9 files |
| Phase 02 P01 | 15 min | 2 tasks | 21 files |
| Phase 02 P02 | 7 min | 2 tasks | 4 files |
| Phase 02 P03 | 10min | 2 tasks | 8 files |
| Phase 02 P04 | 11 min | 2 tasks | 10 files |
| Phase 02 P05 | 45min | 4 tasks | 12 files |
| Phase 03 P01 | 16 min | 3 tasks | 19 files |
| Phase 03 P02 | 9min | 2 tasks | 10 files |
| Phase 03 P03 | 13min | 3 tasks | 6 files |
| Phase 02 P06 | 30min | 5 tasks | 21 files |
| Phase 04 P01 | 25 min | 2 tasks | 14 files |
| Phase 04 P02 | 12 min | 1 tasks | 12 files |
| Phase 04 P03 | 15min | 1 tasks | 6 files |
| Phase 04 P04-04 | 12min | 1 tasks | 14 files |
| Phase 04 P05 | 20min | 2 tasks | 11 files |
| Phase 04 P06 | 14 min | 2 tasks | 5 files |
| Phase 04 P07 | 12 min | 1 tasks | 12 files |
| Phase 04 P08 | 11 min | 1 tasks | 15 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table and `docs/governance/DECISIONS-LOG.md`.
Recent decisions affecting current work:

- [Roadmap]: Phases 1–8 are charter milestones M0–M7 one-to-one, in charter §8 order; no merge, split or reorder (charter §14)
- [Roadmap]: Success criteria per phase are the charter §13 exit criteria restated; each phase `VERIFICATION.md` must cite the exit-criterion number (charter §9)
- [Roadmap]: M8 (sim-to-real, D-17) and M9 (live, D-18) are v2 gated follow-ons, entered via `/gsd-new-milestone` when the gate opens
- [ADR-0005]: Gated parameters stay gated — D-14 at Phase 6 entry, D-15 measured in Phase 7, D-16 fixed at Phase 7 pre-registration, D-17 at M8 entry, D-18 at M9 entry. GSD artifacts fixing any of them silently is drift
- [Phase 01]: Ten history-scan pattern classes (D-01 mandatory seven plus AWS, Slack, PEM), generic assignment accepts unquoted dotenv-style values and rejects dotted or digit-free ones — Self-test pins all ten; zero hits on this history; config-key constants in vendored files must not false-positive
- [Phase 01]: scan_history refuses a shallow clone (exit 2) and CI checks out fetch-depth 0 — A depth-1 checkout would scan one commit and pass vacuously
- [Phase 01]: Plan 01-01 commits made on main (sequential executor, branching_strategy none); CI verified by workflow_dispatch run 35627403598 — Orchestrator instruction and D-05; push events create no runs on this repo
- [Phase 02]: fetch resolves its downloader at call time (None -> module hf_hub_download) and catches (OSError, EntryNotFoundError); the on-disk sha256 is the only verification (Q5)
- [Phase 02]: Validator reads second_monomer_rows / parse_failures from the rows parquet metadata with a source_rows - second - parse == in_scope_rows cross-check (exit 2 on inconsistency); unique_candidate_ids from the candidate parquet (D-7)
- [Phase 02]: Plan 02-01 RED evidence is a collection error by the plan's design (type: execute, tdd_mode false); check tdd-red-evidence would say INVALID_RED - recorded in SUMMARY
- [Phase 2]: 02-03: a present-but-mismatched pinned file is reported (MISMATCH, exit 1), never re-downloaded; the downloader is called only for absent files
- [Phase 2]: 02-03: canonical_psmiles('') returns None by guard (RDKit parses the empty string as an empty molecule)
- [Phase 2]: 02-05: static Maxwell share pinned at 88.82 % (38,693 / 43,561 = 88.8249 %); F-13's 88.83 was a rounding slip; the fraction is a reproduce finding
- [Phase 2]: 02-05: feasible set 6,793 of 40,212 (16.89 %) reported as an input to the D-16 gate; row-level 7,317 pinned under the row Q25
- [Phase 2]: 02-05: DATA-09 'filtered by tg_rmse' vs R-2 'no cut' flagged for the owner; ladder recorded at every rung, nothing resolved
- [Phase 03]: 03-01: ValueError kept at the from_json boundary via one _wrong_type helper (ruff 0.16 TRY004 answered structurally, no noqa); ruff isort known-first-party = [llm4pol] so RED-state submodule imports stay stably ordered through GREEN
- [Phase 03]: 03-01: the evaluator applies no population filter (D-03) and charges evals once per distinct candidate per request on its first ok result (R-2); the committed eval-response example is the evaluator's own output on the synthetic table
- [Phase 3]: 03-02: unsupported is decided before a cache key exists (never reaches the cache); a cache hit is dataclasses.replace(hit, cached=True, cost=Cost(0, 0.0)); the CLI meter is per invocation, cross-run spend belongs to the Phase 4 ledger
- [Phase 3]: 03-03: the loop.agents-only llm import contract added per REQUIREMENTS.md EVAL-06 over CONTEXT R-1 (precedence); owner flag, one block and one test to reverse
- [Phase 3]: 03-03: A-2 written as an optional-layers import-linter contract (both layers in parentheses) because a forbidden contract errors on an absent source; Phase 5 may rewrite it once llm4pol.loop exists
- [Phase 2]: 02-06: tacticity_multi_label_canonical counts every in-scope canonical with two or more distinct non-empty labels, not only those carrying an empty row: ADR-0006's Context table states 2 and the plan's extra conjunct publishes 0
- [Phase 2]: 02-06: documented findings that drifted inside their own tolerance were not republished, so the drift budget stays spent-down rather than reset
- [Phase 2]: 02-06: D-11 promoted to a guarded INVARIANTS.md row in the same commit as the call site (ADR-0006, DATA-10)
- [Phase 04]: 04-01: run_closed is pinned to iteration 0 for both reasons (RESEARCH A4); TornTail.last_lf_offset is the offset of the last LF byte (-1 when none); ledger.append refuses a missing ledger and a torn tail — Run-scoped events use iteration 0 and iterations count from 1; a torn tail is refused, never repaired (CONTEXT R-6)
- [Phase 04]: 04-02: the run driver enforces the budget in evals only (limit iterations x candidates_per_beam x beams); dirty is whole-tree until 04-06; the package root does not export the function reduce
- [Phase 04]: 04-03: experiments/README.md says run-meta.json exists today and the usage and run_summary schemas arrive later in Phase 4; PREREG file re-include left to Phase 7 (F-70)
- [Phase 04]: 04-04: meta example made with an empty environment mapping injected by replacing resume.build_meta with a partial; ledger examples are the first event of each kind of the tracer run
- [Phase 04]: 04-05: exit codes fixed within D-07 and R-9 (2 unreadable record, 3 budget refusal recorded by this call, 4 untrusted ledger, header or selector mismatch); resume on an already closed run exits 0 and appends nothing; RunRefused and SequenceMismatch are LedgerIntegrityError subclasses; verify_replay and SequenceMismatch live in selector.py to keep resume.py under 400 lines — The plan left the codes to the executor for review; the ledger is the only state, so a run cut at 18 event boundaries resumes byte-identically
- [Phase 04]: 04-06: members takes the problem table and refuses a rows parquet of another snapshot; redact reads key names only (suffix rule) and write_meta redacts before it validates; dirty is read over six behaviour paths
- [Phase 04]: 04-07: usage cpu_hours compared with event costs to relative 1e-12 (evaluator adds hours as a running sum, usage_of uses fsum); usage verb prints only the integrity line on a differing usage.json; render_csv refuses non-finite floats
- [Phase 04]: 04-08: summary_of lives in the leaf module summary.py because reduce.py is at the 400-line limit; reduce imports it and holds Outputs, render_outputs, result_sha256 and the three-file write_outputs — reduce.py had 19 free lines and the summary code needed about 70; ledger.py stays untouched at 399
- [Phase 04]: 04-08: result_sha256 is the sha256 of results.csv, usage.json and run_summary.json end to end, printed last by replay and never stored; replay compares before writing and refuses a differing file with exit 4 — owner note 1 of the plan objective; ADR-0008 item 7, CONTEXT D-03

### Pending Todos

None yet.

### Blockers/Concerns

- [Phase 6 gate]: D-14 (LLM provider, API key, budget) is undecided and no API key is set on this machine; Phase 6 cannot start until the owner records D-14 and `config/llm.json` passes its schema
- [Phase 7 gate]: D-15 (replicate budget, Holm) is measured in Phase 7; D-16 (objective form/thresholds) is fixed at the Phase 7 pre-registration using Phase 2's feasible-set size and noise floor
- [Phase 8 entry]: no comparison figure may be claimed before the Phase 7 pre-registration sha256 is committed (charter §13 transition M6→M7)
- [Bookkeeping]: REQUIREMENTS.md previously stated 40 v1 requirements; the actual count is 41 (3 FOUND + 10 DATA + 6 EVAL + 6 RUN + 6 LOOP + 5 LLM + 3 VAR + 2 CMP). Coverage counts corrected during roadmap creation

## Deferred Items

Items acknowledged and deferred at milestone close, most recent first:

| Category | Item | Status | Deferred At | Milestone |
|----------|------|--------|-------------|-----------|
| *(none)* | | | | |

## Session Continuity

Last session: 2026-09-30T09:00:37.326Z
Stopped at: Completed 04-08-PLAN.md
Resume file: None
