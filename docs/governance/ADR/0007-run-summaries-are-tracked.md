# ADR-0007: Run summaries are tracked; the ledger stays out of version control

- **Status:** Accepted
- **Date:** 2026-09-29
- **Deciders:** owner (D-27, 2026-09-24); the form of the change decided by the agent under the
  delegation the owner gave on 2026-09-29
- **Relates to:** ADR-0001 (narrowed by this ADR for the PolyOmics layer), ADR-0004, charter §7 and
  §10, DECISIONS-LOG D-27

## Context

ADR-0001 ignores everything under `experiments/` except its README and gives two reasons: run
directories hold content derived from PoLyInfo, whose terms forbid redistribution, and they are
large and rewritten constantly.

ADR-0004 made PolyOmics (CC BY 4.0) the hidden table. Until the sim-to-real milestone M8 no run
touches PoLyInfo data, so the first reason does not apply to any run the first seven milestones can
produce. The second reason applies to `ledger.jsonl` and not to the small files beside it.

Leaving every run output untracked has a cost the charter names: a number in a figure should be
traceable to the record that produced it, and a record that is never shared cannot be cited.

## Decision

Inside each `experiments/<run-id>/` directory, `meta.json`, `usage.json`, `results.csv` and
`run_summary.json` are tracked. `ledger.jsonl` is not. `run_summary.json` carries the sha256 of the
ledger and of `results.csv`, so that a person holding the ledger can check it against the
repository.

A run that reads PoLyInfo-derived data (M8 onward) is not covered by this ADR: its directory stays
untracked in full under ADR-0001 until a later ADR says otherwise.

## Alternatives considered

| Option | Why not |
|---|---|
| Keep everything ignored (ADR-0001 unchanged) | The stated licence reason is false for PolyOmics runs, and no published number could be cited from the repository |
| Track the ledger as well | A replicate battery is tens of megabytes of append-only text; version control is the wrong store for it |
| Track only `results.csv` | Without `meta.json` the numbers lose the problem, seed, snapshot and code version that produced them |

## Consequences

- `.gitignore` tracks the four summary files by name and ignores the rest of `experiments/`.
- `tests/test_governance.py` replaces the "ignored except the README" assertion with one that checks
  the four names are trackable and `ledger.jsonl` is ignored, using `git check-ignore`.
- Development runs accumulate. A run whose summary is committed is a record; throwaway runs are
  deleted before committing, not committed and reverted.
- Charter §10 "Run 출력" row, the directory table in `CLAUDE.md`, `README.md` and
  `experiments/README.md` are updated in the change that implements this ADR.
- **Guard:** the governance test above; the history secret scan already covers the tracked files.
