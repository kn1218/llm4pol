# Phase 4: Run Management — Context

**Gathered:** 2026-09-22 (draft, orchestrator; owner to review before planning)
**Source:** charter `docs/MASTER-PLAN.md` §4 (A-3, A-6), §7 (run record, problem spec), §10, §12, §13 M3;
Phase 3's evaluator (`llm4pol.evaluate.contract.EvalRequest/EvalResponse/Cost`, `JsonlCache`,
`BudgetMeter`); the CALF20 precedent (ADR-0008 append-only JSONL + rebuildable index, ULID +
`row_version` canonical rows, `calculation_key` vs `run_id`/`attempt_id`, advisory `table_lock`).
**Status:** Draft — needs the owner's answer to the two open items below, then `/gsd-plan-phase 4`.

<domain>
## Phase Boundary

Phase 4 delivers charter M3: a campaign leaves an append-only run record under
`experiments/<run-id>/` that can be resumed without duplicate events and replayed to a byte-
identical `results.csv`; `usage.json` totals equal the ledger sums in two currencies. It freezes
the run record format, the problem spec schema, A-3 and A-6 as ledger tests. It does **not** build
the selector, beams, tags or feedback (Phase 5) — Phase 4's tests drive the ledger with a stub
"selection" that is a plain list of candidate ids, and its `results.csv` reducer is exercised on
recorded events only.
</domain>

<decisions>
## Implementation Decisions (proposed defaults)

### D-01 Run identity
`run_id = <UTC YYYYMMDDTHHMMSSZ>-<8 hex>` (charter §7); the hex is from `secrets.token_hex(4)`.
`experiments/<run_id>/` is created atomically (mkdir fails if it exists — a rerun is a new id, A-6).
`meta.json` written first, once, with: `problem_spec` (validated), `code_git_sha` (`git rev-parse
HEAD`, plus `dirty: bool`), `prompt_versions` (`{}` until Phase 6), `provider`/`model` (null until
Phase 6), `seed`, `snapshot` (`polyomics:general_polymers@041e5834`), `registry_version`
(`property-registry_v1`), `created_at`.

### D-02 Ledger events (`ledger.jsonl`, `protocol/schemas/ledger-event.json`)
One JSON object per line, canonical (`sort_keys`, `separators=(",", ":")`, `allow_nan=False`, LF).
Common envelope: `{seq, ts, run_id, iteration, event, payload, prev_hash, hash}` where `seq` is a
monotonically increasing integer, `prev_hash` is the previous line's `hash` (`"0"*64` for the
first) and `hash = sha256(canonical(line without hash))` — a tamper-evident chain that makes
"append-only" testable (any rewritten line breaks the chain; precedent SC2 byte-prefix test also
applies). Event kinds for M3: `run_opened`, `iteration_opened`, `selection` (beam, candidate ids),
`evaluation` (the full `EvalResponse` or its results subset), `no_match` (beam, query id),
`iteration_closed` (per-beam n and summary values), `run_closed`. Phase 5/6 add `hypothesis`,
`query`, `feedback`, `llm_call` without changing the envelope.

### D-03 Resume
`resume(run_id)` replays the ledger, verifies the hash chain, finds the last `iteration_closed`,
and continues from the next iteration. Idempotency key `(run_id, iteration, beam)` for `selection`
and `evaluation` events: a duplicate is refused before append (R-3 of charter §7). A run whose last
event is not `iteration_closed` is resumed by discarding nothing: the partial iteration's events are
kept and the iteration is re-run under a new `iteration_opened` with `attempt` incremented — the
reducer uses the last completed attempt per iteration (precedent: `run_id`/`attempt_id`).

### D-04 Usage and replay
`usage.json = {evals, cpu_hours, tokens, usd}`; `evals`/`cpu_hours` are sums of `evaluation`
event costs (A-3: two separate numbers, never a combined score); `tokens`/`usd` are 0 until Phase
6. `replay(run_id)` regenerates `results.csv` from `ledger.jsonl` alone; a test writes a run,
copies `results.csv`, deletes it, replays, and asserts byte-identity. `results.csv` columns:
`iteration, beam, n, median_tc, feasible_frac, pct_of_table, hits_top10, hits_top1` — for M3 the
`pct_of_table` / `hits_*` columns are computed against the candidate table's README-triple
population by `llm4pol.data.filters` (percentile of the beam median among candidate medians),
so the format is exercised before Phase 5 fills the beams for real.

### D-05 Problem spec (`protocol/schemas/problem-spec.json`)
Exactly charter §7; `form` enum `["constrained_single"]` now with `"pareto"` reserved (D-16
gated); constraints reference registry keys only (schema `enum` from the registry keys, validated
in the gate inventory with a committed example `protocol/examples/problem-spec.example.json`).

### D-06 Package boundary
`llm4pol.run` may import `llm4pol.evaluate` (contract types) and `llm4pol.data` (filters for the
reducer); forbidden from `llm4pol.loop`, `llm4pol.llm`. Add the contract with the package.

### D-07 CLI
`python -m llm4pol.run open --spec <json> [--seed N]`, `… resume <run_id>`, `… replay <run_id>`,
`… usage <run_id>`; exit 0 / 2 (schema, IO) / 4 (chain broken or duplicate event).

### Claude's Discretion
- Whether to keep an in-memory `seq`/hash cursor object or recompute on every append (the run is
  single-writer; a sidecar advisory lock as in the precedent is optional).
</decisions>

<open_for_owner>
## Two items for the owner before planning
1. **Hash-chained ledger (D-02)** vs the charter's plain "append-only JSONL": the chain is the
   cheapest way to make A-6 a test rather than prose. Accept, or keep plain JSONL with the
   byte-prefix test only?
2. **Experiments directory policy:** `experiments/` is git-ignored except its README (ADR-0001
   wording predates PolyOmics). Keep ignored (recommended; large, append-only), with reduced
   `results.csv` copied into `docs/` only when a figure cites it.
</open_for_owner>

<deferred>
- Selector, beams, tag vocabulary, feedback, memory → Phase 5/6.
- SQLite index over the ledger → only if replay becomes slow (precedent ADR-0008).
</deferred>

---

*Phase: 04-run-management — draft context, not yet planned*
