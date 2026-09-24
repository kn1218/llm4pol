# Phase 4: Run Management — Context

**Gathered:** 2026-09-22, **rewritten 2026-09-23**
**Status:** Draft — four divergences answered by the owner (D-21..D-24); item E is the last one
before planning.

**Why it was rewritten.** The first draft derived this phase from `CALF20_DiscoveryLoop`'s ledger
spine (ULID, `row_version`, fourteen tables, transitive invalidation, a hash chain). That was the
wrong precedent: CALF20 is a physisorption instrument with a much larger record, and the owner's
instruction was to look at how **LLM4MOF** built its project. This draft is derived from the two
references that actually apply, plus the charter, which outranks both.

**Sources, in precedence order**

1. `docs/MASTER-PLAN.md` §4 (A-3, A-6), §7 (run record, problem spec), §10, §13 M3 — the authority.
2. **LLM4MOF** (`LLM2POR_Core_20260319`), read directly at
   `C:/Users/molsim/Dropbox/Antigravity/LLM2POR_Core_20260319/experiments/` — the scientific parent's
   actual run artifacts.
3. **LLM4MO** (`C:/Users/molsim/Desktop/LLM4MO`) — the owner's **sibling port** of the same parent to
   oxide semiconductors, started the same week. `src/llm4mo/{contracts,database_run,database_evaluator,
   database_metrics}.py` are the twin of LLM4POL's Phases 3–4 and are already Phase-1-verified there.
4. `llm4pol.evaluate` as built in Phase 3 (`EvalRequest/EvalResult/EvalResponse/Cost`, `JsonlCache`,
   `BudgetMeter`).

`CALF20_DiscoveryLoop` is **not** a source for this phase. Its contribution to LLM4POL is confined to
three build-plane items already landed in Phases 1–2 (`history_secret_scan.py`, the
`schema-inventory` check step, the protocol triad).

<domain>
## Phase Boundary

Charter M3: a campaign leaves a run record under `experiments/<run-id>/` that can be **resumed**
without duplicate events and **replayed** to a byte-identical `results.csv`; `usage.json` totals equal
the ledger sums in two currencies. Freezes the run record format, the problem spec schema, A-3 and A-6.

Not in scope: selector, beams, tags, feedback text, agents (Phases 5–6). Phase 4's tests drive the
ledger with a stub selection (a plain list of candidate ids) and exercise the reducer on recorded
events only.
</domain>

<reference_facts>
## What the two references actually do (read, not recalled)

### LLM4MOF — `experiments/<run_id>/` (verified 2026-09-23)

```
run_config.json      {run_id, start_time, config{mode, target_metric, num_iterations,
                      openai_model, openai_api_key: "***REDACTED***", temperature, seed,
                      agent1_prompt, agent2_prompt, experiment_name, experiment_group,
                      sample_n, pattern_top_n, max_retries, request_timeout}}
iteration_00N.json   {iteration, timestamp, data{hypothesis_raw, constraints, n_candidates,
                      feedback{iteration, beams[4], diagnosis, constraints_used},
                      metrics{n_candidates, n_total, reduction_ratio,
                              percentile_of_candidate_median,
                              candidate_stats{...}, full_db_stats{...},
                              agent1_tokens, agent2_tokens, agent2_corrections[]}}}
run_summary.json     {run_id, start_time, end_time, summary{n_iterations,
                      percentile_trend[], candidate_count_trend[], improving,
                      best/worst_iteration, best/worst_percentile, query, mode,
                      target_metric, completed_iterations}}
```

Five facts worth carrying:

- **One immutable file per iteration**, not one rewritten file. Append-only is a filesystem property.
- **The API key is `***REDACTED***` in the committed record.** Matches R-3 here.
- **`candidate_stats` and `full_db_stats` are both recorded per iteration**, and the headline metric
  is `percentile_of_candidate_median` — the population denominator travels with the number.
- **Token counts live in the per-iteration metrics**, not in a separate usage file.
- **No hash chain, no ULID, no `row_version`, no SQLite.** All of that was CALF20.

### LLM4MO — the sibling port (verified 2026-09-23, `contracts.py` read in full)

- `run | resume | replay` as three CLI commands over one ledger — the same three verbs charter §13 M3
  names.
- The ledger carries a **header** (`problem` + `provenance{partition, seed, engineering_smoke,
  policy}`); `resume`/`replay` read the header rather than re-taking CLI arguments, so a resumed run
  cannot silently change its own problem.
- **`run` refuses to touch an existing ledger** (`"Run ledger already exists; use replay"`) — A-6 as a
  precondition, not a test.
- **Replay is the source of truth**: `evaluator.replay()` returns the event pairs, and the run asserts
  the policy's expected sequence matches the replayed prefix (`"Random policy sequence mismatch"`)
  before continuing. Determinism is checked, not assumed.
- `Observation` carries `status ∈ {ok, missing, invalid, budget_exhausted}`, `cached`, `charged`,
  `spent`, `artifact_sha256`, `evidence_class`, `reference`, and a validator enforcing
  **`cached ⊕ charged`** ("Cache cannot consume a new query") and status ⟺ evidence agreement.
- The run result ends with `result_sha256 = sha256(canonical(result))`.
- Errors print one generic message and return 1 — no internal detail leaks.
</reference_facts>

<decisions>
## Implementation Decisions (proposed; each cites its source)

### D-01 Run identity and meta (charter §7)
`run_id = <UTC YYYYMMDDTHHMMSSZ>-<8 hex>`. `experiments/<run_id>/` is created with `mkdir(exist_ok=
False)`; an existing directory is refused with the twin's message shape ("run exists; use replay").
`meta.json` is written once and holds the charter's fields — problem spec, `code_git_sha` (+`dirty`),
`prompt_versions` ({} until Phase 6), `provider`/`model` (null until Phase 6), `seed`, `snapshot`
(`polyomics:general_polymers@041e5834`), `registry_version`, `created_at` — and, from LLM4MOF, any
secret-shaped config value is written as `***REDACTED***`, asserted by a test.

### D-02 Ledger events (`ledger.jsonl`, `protocol/schemas/ledger-event.json`)
One canonical JSON object per line (`sort_keys`, `separators=(",",":")`, `allow_nan=False`, LF).
**The first line is a header** (`{schema_version, run_id, problem, provenance{seed, snapshot,
registry_version, selector, code_git_sha}}`); `resume` and `replay` read the problem from it rather
than from CLI arguments, so a resumed run cannot silently change its own problem (D-21, taken from
LLM4MO; the text format is kept so the record stays readable and diffable).
Every later line is an event with the envelope
`{seq, ts, run_id, iteration, event, payload}`. Event kinds for M3: `run_opened`,
`iteration_opened`, `selection`, `evaluation`, `no_match`, `iteration_closed`, `run_closed`.
Phases 5–6 add `hypothesis`, `query`, `feedback`, `llm_call` without changing the envelope.
**No hash chain** — neither reference uses one (see D-03 for what replaces it).

### D-03 Integrity by replay, not by chaining (from LLM4MO)
Append-only is enforced three ways, all proven in the sibling project:
1. `run` refuses an existing run directory; a rerun gets a new id (A-6 as a precondition).
2. A byte-prefix test: after every append, the previous file content is a prefix of the new content.
3. **Replay-sequence match**: `resume` replays the ledger and asserts the deterministic selector's
   expected prefix equals what was recorded, refusing to continue on mismatch. This catches a doctored
   or truncated ledger at the only moment it matters — when the run is continued or a result is
   re-derived — without making a repaired ledger unusable.
`replay` ends by printing `result_sha256` over the canonical reduced result, so a published number
has a hash anyone can recompute from the committed record.

### D-04 Usage, metrics and replay output
`usage.json = {evals, cpu_hours, tokens, usd}` — `evals`/`cpu_hours` summed from `evaluation` event
costs, never combined (A-3); `tokens`/`usd` 0 until Phase 6. From LLM4MOF, **every per-iteration
metric row carries its population**: `results.csv` columns `iteration, beam, n, n_population,
median_tc, feasible_frac, pct_of_population, hits_top10, hits_top1`, and `run_summary.json` carries
`percentile_trend[]` and `candidate_count_trend[]`. `replay` regenerates `results.csv` from
`ledger.jsonl` alone, byte-identical.

### D-05 Problem spec (`protocol/schemas/problem-spec.json`)
Charter §7 exactly, with the twin's strictness: `extra` forbidden, `schema_version` pinned,
`budget > 0`, constraints referencing registry keys only, `form` enum `["constrained_single"]` with
`"pareto"` reserved (D-16 gated). A committed example goes in the `schema-inventory` gate step.

### D-06 Package boundary
`llm4pol.run` may import `llm4pol.evaluate` and `llm4pol.data`; forbidden from `llm4pol.loop` and
`llm4pol.llm`. Contract added with the package.

### D-07 CLI
`python -m llm4pol.run {run|resume|replay|usage} …` — the twin's verb set. Exit 0 / 2 (schema, IO) /
4 (sequence mismatch or duplicate event). Errors print one generic message (twin's convention) with
detail on stderr only.
</decisions>

<open_for_owner>
## Decisions for the owner

The rewrite surfaced that **LLM4POL and its sibling LLM4MO diverge on four choices** that were made
here without knowing the twin had already gone the other way. All four were put to the owner on
2026-09-23 and answered; they are recorded as D-21..D-24 in `docs/governance/DECISIONS-LOG.md`.

| # | Question | LLM4MO (twin) | **Decision for LLM4POL** |
|---|---|---|---|
| A | Ledger storage | SQLite, header row + events | **JSONL with a header line** — the twin's resume-safety property, text format kept (D-21) |
| B | Data partitions | `development / validation / test` | **None**; charter §8 stands — DB mode trains nothing, so there is no model to overfit. A scaffold-grouped split enters by ADR when a surrogate first joins the loop (D-22) |
| C | Contract types | pydantic `BaseModel` (frozen, extra=forbid, strict) | **Keep frozen dataclasses + JSON Schema** — built and green in Phase 3; the schemas check the contract from outside the language and ride the `schema-inventory` gate step (D-23) |
| D | Public/private data split | `public/` and `priv*/` jsonl directories | **No physical split** — blindness is guaranteed by testing the payload that leaves for the provider (A-4), not by storage layout; revisit if the Phase 6 payload test proves insufficient (D-24) |

Plus the Phase 4 item still open:

| # | Question |
|---|---|
| E | `experiments/` git policy — ADR-0001's stated licence reason no longer applies to the PolyOmics layer |
</open_for_owner>

<deferred>
- Selector, beams, tag vocabulary, feedback, memory → Phases 5–6.
- `evidence_class` / `reference` provenance fields (twin) → revisit at M8 when a second source exists.
</deferred>

---

*Phase: 04-run-management — draft, rewritten from LLM4MOF + LLM4MO + the charter*
