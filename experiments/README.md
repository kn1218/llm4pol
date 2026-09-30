# experiments/

Run outputs. Inside a run directory git tracks four small summaries and ignores the ledger and
everything else (ADR-0007; charter `docs/MASTER-PLAN.md` §10). Nothing in here is a result until it
has been reduced into `docs/` or a figure script; a tracked summary is the record a published number
is cited from.

## Layout of a run directory

`experiments/<run-id>/`, where the run id is `<UTC timestamp>-<8 hex>` (for example
`20260930T071500Z-3f9a1c2e`). Five files:

| File | What it holds | Tracked |
|---|---|---|
| `meta.json` | what was run: the problem, the code version, the seed, the snapshot, the selector; written once when the run opens | yes |
| `ledger.jsonl` | a header line, then append-only events, one canonical JSON object per line; the populations travel in the `run_opened` event | no |
| `usage.json` | the two budget currencies and the token count: `evals`, `cpu_hours`, `tokens`, `usd` | yes |
| `results.csv` | one row per iteration, beam and population; the column definitions are in ADR-0008 | yes |
| `run_summary.json` | completed iterations, per-beam trends, the sha256 of `ledger.jsonl` and of `results.csv` | yes |

`meta.json`, `usage.json` and `run_summary.json` each validate against a schema under
`protocol/schemas/` and carry `schema_version` (D-39). `run-meta.json` and `run-usage.json` exist
today (`usage.json` holds `evals` and `cpu_hours` as two separate sums of the ledger, and `tokens`
and `usd`, which stay 0 until Phase 6); the schema of `run_summary.json` is added by a later plan of
the same phase, before the run record freezes at the exit of M3.

## Why four files are tracked and the ledger is not

A number in a figure should be traceable to the record that produced it, and a record that is never
shared cannot be cited. `meta.json`, `usage.json`, `results.csv` and `run_summary.json` are small.
`ledger.jsonl` is large and append-only, and a replicate battery of them runs to tens of megabytes,
which version control is the wrong store for. `run_summary.json` carries the sha256 of the ledger and
of `results.csv`, so a person holding a ledger can check it against the repository: compute its
sha256 and compare it with the value in the tracked `run_summary.json`.

A tracked `meta.json` must name a `polyomics:` snapshot. A run that reads PoLyInfo-derived data (M8
onward) is not covered by ADR-0007: its directory stays untracked in full under ADR-0001, because the
NIMS MatNavi terms forbid redistribution of that data and of anything derived from it.
`tests/test_governance.py` enforces both rules by asking git (`git check-ignore`, `git ls-files`)
and not by reading `.gitignore` as text.

## Rules

- A run directory is append-only. A rerun gets a new identifier; it never overwrites.
- `resume` continues a run from its ledger, rebuilding the evaluation cache and the budget meter from
  the recorded events. It refuses a ledger whose header names another snapshot, registry version or
  code version than the running code, and a ledger with a torn final line; it reports the offset and
  repairs nothing (ADR-0008 item 7).
- `replay` regenerates `results.csv` and `run_summary.json` from the ledger alone, byte-identical to
  the originals. It does not compare the code version and loads no data table.
- `meta.json` records the exact prompt versions from `protocol/prompts/` and the exact configuration
  used, so a result can be traced to what produced it.
- Development runs accumulate. A run whose summary is committed is a record; throwaway runs are
  deleted before committing, not committed and reverted.
- Anything else a figure or a claim depends on is reduced into a small committed file and cited from
  the document that uses it.
- The pre-registration file of Phase 7 (`experiments/PREREG-<date>.md`) is ignored by the pattern
  block in `.gitignore`, as every top-level file here is except this README; Phase 7 adds its own
  re-include.
