# Phase 3: Evaluator (table backend) — Context

**Gathered:** 2026-09-22
**Source:** charter `docs/MASTER-PLAN.md` §4 (A-1, A-2, A-3), §6 (package boundaries), §7 (evaluator
contract), §13 M2; what Phase 2 built (`llm4pol.data.registry.Registry`/`PropertySpec`,
`load.build_candidates` → `data/processed/candidates-041e5834.parquet` with `<column>_median`,
`<column>_n`, `<column>_min/max/std`, `filters.readme_triple_mask`, `filters.check_tc_mask`,
`snapshot.candidates_parquet`); the CALF20 precedent's `calculation_key` vs `run_id` split (ADR-0012
there) and its append-only cache convention. No discuss-phase interview (owner unavailable).
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 3 delivers charter M2: every property lookup goes through one evaluator contract backed by
`table`, with a four-value status taxonomy, a cache that never double-charges, a two-currency
budget, and provenance on every response. It freezes the evaluator request/response schemas and
the import boundary (A-1, A-2). It does **not** build the loop, beams, problem spec or run ledger
(Phases 4–5) and does not decide which population the hidden table serves (see D-03 below — the
evaluator answers per candidate; populations are a caller concern).

Inputs that already exist: the candidate parquet (78,676 candidates, replicate medians), the
registry (9 keys, `role`, `physical_range`, `check_tc`), the snapshot identifier
`polyomics:general_polymers@041e5834`.
</domain>

<decisions>
## Implementation Decisions

### D-01 Contract as protocol
`protocol/schemas/eval-request.json` and `protocol/schemas/eval-response.json` (Draft 2020-12),
plus committed example instances `protocol/examples/eval-request.example.json` and
`eval-response.example.json` registered in `[tool.llm4polcheck]` so the `schema-inventory` gate
step validates them. Shapes exactly as charter §7:

- request: `{run_id, iteration, batch: [{candidate_id, properties: [...]}]}`; `run_id` any
  non-empty string (Phase 4 defines its format); `iteration` integer ≥ 0; batch 1..1000 entries;
  properties non-empty, unique.
- response: `{run_id, iteration, results: [...], cost: {evals, cpu_hours}}` where each result is
  `{candidate_id, property, status, value, unit, n_replicates, spread, backend, source,
  provenance_tier, cached, cost: {evals, cpu_hours}}`. `value`/`unit`/`n_replicates`/`spread`
  are `null` unless `status == "ok"`. Results are in request order (candidate order, then property
  order) and the count equals Σ|properties| over the batch.

### D-02 Status taxonomy (charter §7)
- `ok` — candidate known, property in registry, median non-null.
- `unsupported` — property key not in the registry (or `static_dielectric_const`, which is not a
  key — A-7 holds by construction). Consumes no budget.
- `missing` — candidate known but the property median is null, **or** the candidate_id is not in
  the snapshot (the contract has no separate "unknown candidate" status; the result note field is
  not part of the schema, so `missing` covers both and a per-result `reason` enum
  `{"value_absent", "candidate_unknown"}` is added to the schema as an optional field). Consumes no
  budget.
- `error` — the backend raised (snapshot unreadable, schema mismatch). Retryable; the response
  carries the exception class name in `reason`; consumes no budget.

### D-03 Value semantics and populations
`value` = replicate median from the candidate table; `n_replicates` = `<column>_n`; `spread` =
`<column>_std` (null when n < 2); `unit` from the registry. The evaluator applies **no**
population filter (README triple, `check_tc`) — a candidate outside the triple still gets its
values. Population masks are exported by `llm4pol.data.filters` and are consumed by the loop
(Phase 5) for sampling and percentile metrics. `provenance_tier = "md_simulated"` for `table`.

### D-04 Cost and cache
- Cache key `(candidate_id, property, backend, source)`; in-memory dict with optional JSONL
  persistence (`cache_path`, append-only, one JSON object per line, replayed on open). A hit
  returns the stored result with `cached: true` and `cost.evals = 0`.
- `evals` is charged **once per distinct candidate per request** on the first non-cached `ok`
  result of that candidate (the loop budget "400 evals = 10 iterations × 4 beams × 10 candidates"
  counts candidates, not properties). Later properties of the same candidate in the same request
  carry `cost.evals = 0`. `cpu_hours = 0.0` for `table` always. Response-level `cost` is the sum.
- `BudgetMeter` holds `evals` and `cpu_hours` as separate integers/floats with no combined score
  (A-3); `remaining(limit)` and `exhausted(limit)` helpers; the evaluator refuses a request whose
  distinct uncached candidates would exceed the remaining `evals` limit when a limit is set, with a
  structured `BudgetExceeded` error (not a per-result status).

### D-05 Backend interface
`llm4pol.evaluate.contract` defines `EvalRequest`, `EvalResult`, `EvalResponse`, `Cost` (frozen
dataclasses, pydantic-free, validated against the JSON Schemas in tests) and a `Backend` Protocol:
`name`, `source`, `provenance_tier`, `lookup(candidate_id, property_key) -> Lookup` where `Lookup`
is `{status, value, unit, n_replicates, spread, reason}`. `backends/table.py` implements it over the
candidate parquet (loaded once, indexed by `candidate_id`). `backends/radonpy.py` is **not**
created (M9); the import-linter contract names it anyway.

### D-06 Import boundary (A-1, A-2) — first real contracts
Add to `[tool.importlinter]`: (1) `llm4pol.evaluate` must not import `llm4pol.loop`, `llm4pol.llm`,
`llm4pol.run`; (2) `llm4pol.loop` must not import `llm4pol.evaluate.backends.radonpy` (forbidden
contract; module may not exist yet — research confirmed import-linter accepts that); (3) keep
Phase 2's `llm4pol.data` independence contract. `llm4pol.evaluate` may import `llm4pol.data`
(registry, snapshot paths, filters).

### D-07 CLI and batch
`python -m llm4pol.evaluate --request <json> [--cache <jsonl>] [--evals-limit N]` prints the
response JSON; exit 0 on success, 2 on request-schema failure or IO error, 3 on `BudgetExceeded`.
Batch of 100 entries returns 100·|properties| results in order (charter §13 M2 exit criterion).

### D-08 Tests
Synthetic candidate parquet fixture (≤ 20 candidates) written by the test via
`load.build_candidates` on a synthetic row frame; real-file tests skip with the Phase 2 reason
when the processed parquet is absent. Contract tests: each status; order and count; cache hit
leaves `evals` unchanged; per-candidate charging; two currencies never merged; every result
carries `backend/source/provenance_tier`; schema validation of request and response in the
suite; `error` path by pointing the backend at a missing parquet. INVARIANTS.md A-1, A-2, A-3
guard cells flip from "prose"/"(M2)" to the contract and test names in the same change.

### Claude's Discretion
- Whether the cache persists by default (recommend: off unless `cache_path` given).
- Module split inside `llm4pol.evaluate` (contract, registry adapter, cache, budget, backends).
</decisions>

<specifics>
## Specific Ideas
- Reuse `llm4pol.data.registry.load_registry()` for keys/units; never re-read the YAML in
  `evaluate`.
- Candidate lookup must be O(1): build a `dict[candidate_id, row-index]` or set the parquet index.
- Keep `validate.py`-style module size discipline (< 800 lines; Phase 2 split into `sections.py`).
- Evidence file `03-EVIDENCE.md` + CI `workflow_dispatch` on both platforms as in Phases 1–2.
</specifics>

<deferred>
## Deferred Ideas
- `backends/radonpy.py`, `config/hpc.json` → M9.
- Second-table backends (OpenPoly/PoLyInfo) → M8; they differ only in `source`.
- Population selection and percentile metrics → Phase 5 (loop).
</deferred>

---

*Phase: 03-evaluator-table-backend*
*Context gathered: 2026-09-22 from the charter and the Phase 2 code (owner asleep; no interview)*

<post_research_decisions>
## Decisions after 03-RESEARCH.md (2026-09-22, orchestrator; owner unavailable — development defaults)

- **R-1 A-2 contract form.** import-linter errors on a `forbidden` contract whose *source* package is absent, so D-06 clause 2 uses the `layers` form now — `layers = ["(llm4pol.evaluate.backends.radonpy)", "(llm4pol.loop)"]` (KEPT while `loop` is absent, BROKEN on a violating import once it exists); it is rewritten as `forbidden` when Phase 5 creates `llm4pol.loop`. The "only `loop.agents` may import `llm`" rule enters with Phase 6, not now.
- **R-2 Charging.** `evals` is charged once per distinct candidate per request on its first non-cached `ok` result (D-04 literal reading), pinned by a test; the loop's 400-eval arithmetic counts candidates.
- **R-3 Schema strictness.** `provenance_tier` is a one-value enum `["md_simulated"]` for `table` (extended by M8/M9 ADRs); a malformed `candidate_id` (not 16 lowercase hex) is a request-schema failure (exit 2), not `missing`.
- **R-4 Cache.** Persist per request with `flush()` (no per-line fsync); never cache `error`; stored records keep `cached: false` and a hit is returned via `dataclasses.replace(hit, cached=True, cost=Cost(0, 0.0))`; NaN medians/std become `None` before serialisation (`allow_nan=False`).
- **R-5 Backend load.** `pyarrow.read_table` → pandas, `candidate_id` as index (11 µs lookups); the table is loaded once per `TableBackend` instance.
</post_research_decisions>
