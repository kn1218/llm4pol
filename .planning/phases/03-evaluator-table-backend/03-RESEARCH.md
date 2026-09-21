# Phase 3: Evaluator (table backend) — Research

**Researched:** 2026-09-22
**Domain:** Python evaluator contract over a parquet lookup table — JSON Schema 2020-12 payloads, frozen-dataclass contract with a `Protocol` backend, append-only JSONL cache, two-currency budget, import-linter boundary (charter §4 A-1..A-3, §7, §13 M2)
**Confidence:** HIGH — every load-bearing claim below was probed in the locked pixi environment this session (outputs pasted); library semantics were cross-checked against Context7 docs. Nothing in this phase installs a new package.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

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

### Deferred Ideas (OUT OF SCOPE)
- `backends/radonpy.py`, `config/hpc.json` → M9.
- Second-table backends (OpenPoly/PoLyInfo) → M8; they differ only in `source`.
- Population selection and percentile metrics → Phase 5 (loop).
</user_constraints>

> **One correction to a locked decision's parenthetical (D-06 clause 2).** "research confirmed
> import-linter accepts that" is true only for an absent **forbidden** module. A `forbidden`
> contract whose **source** module (`llm4pol.loop`) does not exist is a hard error in
> import-linter 2.15 (`Module 'llm4pol.loop' does not exist.`, exit 1 — F-20). The A-2 rule is
> still expressible today in the optional-layers form (F-22), which is KEPT while both modules are
> absent and BROKEN the moment `llm4pol.loop` imports the backend. The decision's *intent* (the
> contract names `radonpy` now) is honoured; only its contract *type* changes. Flagged for the
> owner in Open Questions Q1; not silently resolved.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| EVAL-01 | Request/response validate against `protocol/schemas/eval-request.json` / `eval-response.json`; the test suite loads those schemas | F-24..F-31 (schema patterns probed with jsonschema 4.26.0 Draft 2020-12), Pattern 2, Code Example 1, `[tool.llm4polcheck]` entry shape (F-32) |
| EVAL-02 | Exactly one status in `{ok, unsupported, missing, error}`; `unsupported`/`missing` consume no budget; `error` retryable | F-05..F-08 (null-median population per property), Pattern 3 (status decision order), Pattern 5 (never cache `error`), schema `const 0` on non-ok cost (F-28) |
| EVAL-03 | Every response carries `backend`, `source`, `provenance_tier`, `n_replicates`, `spread`, `unit`, `cost` | F-02..F-04 (columns `_median/_n/_std`, snapshot metadata), F-11 (registry units), schema `required` list (F-26) |
| EVAL-04 | Cache keyed by `(candidate_id, property, backend, source)`; a hit leaves `evals` unchanged | F-33..F-38 (JSONL append/replay probe on Windows, canonical key, NaN guard), Pattern 5, Pitfalls 2–4 |
| EVAL-05 | Batch of 100 returns responses in request order with matching count | F-09, F-10 (O(1) lookup: 0.5–11 µs; 100·9 lookups ≪ 10 ms), Pattern 4 (nested-loop ordering, two-phase commit) |
| EVAL-06 | import-linter contracts: `loop` ↛ `evaluate.backends.radonpy`; `evaluate` ↛ `loop`/`llm`; `llm` reachable only from `loop.agents` | F-18..F-23 (probed contract forms), Code Example 3 (exact TOML), Pattern 7 (guard-on-the-guard test) |
</phase_requirements>

## Summary

Phase 3 is a pure-Python, no-new-dependency phase. Everything it needs is already in the locked
environment (Python 3.13.15, pandas 3.0.5, pyarrow 25.0.0, jsonschema 4.26.0, import-linter
2.15, mypy 2.3.1, pytest 9.1.1 — F-01) and in Phase 2's `llm4pol.data` package: the candidate
parquet (78,676 rows, 49 columns, `candidate_id` unique 16-hex, `<column>_median/_n/_min/_max/_std`
per registry column, snapshot id in the parquet metadata — F-02..F-04), the typed registry
(`load_registry()` → `Registry.properties[key].column/unit`, 9 keys — F-11) and the synthetic
14-row fixture from which `load.add_identity` + `load.build_candidates` produce a 9-candidate table
in 0.05 s with every status case present (F-39..F-41).

Three findings change how the plan should be written. (1) **import-linter**: an absent
*forbidden* target is silently skipped (KEPT) but an absent *source* module is a hard error, so
the A-2 contract must use the optional-layers form `layers = ["(llm4pol.evaluate.backends.radonpy)", "(llm4pol.loop)"]`
today, and the "only `loop.agents` may import `llm`" rule uses a wildcard source
`llm4pol.*` with `ignore_imports`; both forms were falsified (BROKEN on a violating import) in
the scratchpad (F-18..F-23). (2) **JSON Schema**: the conditional null-ness, the `reason` enum
per status and the "non-ok and cached results carry `evals: 0`" rule are all expressible in
Draft 2020-12 with `allOf` of `if/then/else` blocks and were validated positively and negatively
with jsonschema 4.26 (F-24..F-31). (3) **JSONL cache on Windows**: `open(path, "a",
encoding="utf-8", newline="\n")` writes LF-only lines, `json.dumps(sort_keys=True,
separators=(",", ":"), allow_nan=False)` gives a canonical line and refuses NaN — which matters
because `<column>_std` is NaN for every n = 1 candidate (59,602 of 78,676 for TC) and null
medians arrive as NaN; per-append `fsync` costs ~2 ms on this disk, so persist per request, not
per result (F-33..F-38).

**Primary recommendation:** Build `llm4pol.evaluate` as seven small modules (`contract`,
`registry`, `cache`, `budget`, `evaluator`, `backends/table`, `__main__`), decide status in the
order *unsupported → candidate_unknown → error → value_absent → ok*, compute every result
first and commit cache + meter only after the `BudgetExceeded` check passes (two-phase), never
cache `error`, and land the four import-linter contracts with a negative test that proves the
optional-layers guard breaks on a violating import.

## Facts the plan may cite

Every fact is tagged `verified` (probed in this session in the locked environment, output pasted
in the probe log below or quoted from a file read this session) or `unverified` (reasoned or
recalled, not probed). The plan cites `F-nn`; it never re-derives a number.

| ID | Fact | Status | Source |
|----|------|--------|--------|
| F-01 | Locked environment: Python 3.13.15, pandas 3.0.5, pyarrow 25.0.0, jsonschema 4.26.0, import-linter 2.15, mypy 2.3.1, pytest 9.1.1, pixi 0.80.0. No package is added by this phase | verified | `pixi run … python -c "import …"` this session |
| F-02 | `data/processed/candidates-041e5834.parquet`: 78,676 rows, 49 columns, 1 row group, 23,880,837 bytes. Columns: `candidate_id` (large_string), then for each of the nine registry columns in `schema.PROPERTY_COLUMNS` order `<col>_median` (double), `<col>_n` (int64), `<col>_min` (double), `<col>_max` (double), `<col>_std` (double), then `n_rows` (int64), `canonical_psmiles` (large_string), `tacticity` (large_string) | verified | pyarrow schema dump this session |
| F-03 | Parquet schema metadata keys: `llm4pol.snapshot` = `polyomics:general_polymers@041e5834`, `llm4pol.revision`, `llm4pol.source_rows`, `llm4pol.source_columns`, `llm4pol.excluded_second_monomer`, `llm4pol.excluded_parse_failure`, `llm4pol.source_sha256`, `pandas` | verified | `pq.ParquetFile(...).schema_arrow.metadata`; written by `load.py` `metadata = {b"llm4pol.snapshot": snapshot.SNAPSHOT_ID.encode("utf-8"), …}` |
| F-04 | `candidate_id` is unique (78,676 distinct) and every value is exactly 16 characters; `identity.candidate_id` returns `hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]` (`src/llm4pol/data/identity.py:52`) so the pattern `^[0-9a-f]{16}$` is exact | verified | probe (`is_unique True`, `len set [16]`); file read |
| F-05 | Null-median ("missing / value_absent") population per property on the real table: `thermal_conductivity` 9,635; `dielectric_const_dc` 1,571; `tg` 27,138; `Rg` 0; `r2` 306; `fractional_free_volume` 3,633; `sp_ced` 15,796; `density` 0; `refractive_index` 1,571. In every case `null_median == (n == 0)` | verified | pandas probe this session |
| F-06 | n = 1 candidates (`_std` is NaN, `spread` must be null): TC 59,602; eps_dc 64,263; tg 49,161; Rg 65,693; r2 65,464; ffv 65,590; sp_ced 54,274; density 65,693; RI 64,263. n ≥ 2 (spread is a number): TC 9,439; eps_dc 12,842; tg 2,377; Rg 12,983; r2 12,906; ffv 9,453; sp_ced 8,606; density 12,983; RI 12,842 | verified | pandas probe |
| F-07 | `_std` NaN count = n0 + n1 exactly (e.g. TC 69,237 = 9,635 + 59,602): `build_candidates` uses pandas `std` with ddof=1, NaN when n ≤ 1 (`load.py` docstring: "``std`` is pandas' default ddof=1 (NaN when ``n`` is 1)") | verified | probe + file read |
| F-08 | Dtypes after `to_pandas()`: `_median` float64 (null → NaN), `_n` int64 (never null; 0 when absent), `candidate_id` pandas `str` dtype (pandas 3), `n_rows` int64 | verified | probe |
| F-09 | Load time: `pq.read_table` 0.049 s + `to_pandas` 0.003 s for the full table; `dict[candidate_id, row_index]` build 0.010 s; `set_index("candidate_id")` 0.001 s | verified | probe |
| F-10 | Lookup cost per (candidate, property): `df.at[row, col]` via dict index 11.1 µs; `DataFrame.set_index(...).at[id, col]` 14.4 µs; `dict[candidate_id, dict[column, value]]` built by `to_dict("records")` 0.46 µs but costs 0.63 s to build. A 100-candidate × 9-property batch is ≤ 10 ms on any of them; the dict-of-rows form is the fastest per call and still loads the table in < 1 s total | verified | probe |
| F-11 | Registry (`load_registry()` this session): `thermal_conductivity` col `thermal_conductivity` unit `W/(m*K)` role objective check_tc True; `dielectric_const_dc` unit `1` constraint; `tg` unit `K` constraint; `rg` col `Rg` unit `angstrom` intermediate; `r2` unit `nm^2` validator (unit_status unverified); `ffv` col `fractional_free_volume` unit `1`; `sp_ced` unit `MPa`; `density` unit `g/cm^3`; `refractive_index` unit `1` validator. `Registry.snapshot` = `polyomics:general_polymers@041e5834`, `registry_version` `v1` | verified | probe |
| F-12 | Registry API: `load_registry(path=REGISTRY_PATH, *, schema_path=SCHEMA_PATH) -> Registry`; `Registry.properties: dict[str, PropertySpec]` (registry order), `.columns()`, `.spec_for_column(column)`, `.by_role(role)`; `PropertySpec(key, column, unit, unit_status, role, physical_range, check_tc, tg_rmse_ladder, tg_rmse_unit, unit_note)` frozen dataclass; `RegistryError(ValueError)` | verified | `src/llm4pol/data/registry.py` read this session |
| F-13 | Snapshot API: `snapshot.SNAPSHOT_ID`, `snapshot.DEFAULT_ROOT` (repo root, `Path(__file__).resolve().parents[3]`), `snapshot.processed_dir(root)`, `snapshot.candidates_parquet(directory) -> directory / f"candidates-{POLYOMICS_REVISION_SHORT}.parquet"` | verified | `src/llm4pol/data/snapshot.py` read |
| F-14 | Loader API: `load.add_identity(frame) -> (rows, excluded_second_monomer, excluded_parse_failure)`; `load.build_candidates(rows) -> DataFrame` (one row per `candidate_id`, `groupby(..., sort=True)`); `schema.PROPERTY_COLUMNS` (9 names, charter order); `schema.DTYPES` (read_csv dtype map) | verified | `load.py`, `schema.py` read |
| F-15 | Filters API the loop will use later (not the evaluator, D-03): `filters.readme_triple_mask(df, registry, *, suffix="")` (`suffix="_median"` on the candidate table) and `filters.check_tc_mask(df, registry)` (row-level; `check_tc` is not a candidate-table column) | verified | `filters.py` read |
| F-16 | `pyproject.toml`: `[tool.mypy] strict = true`, `packages = ["llm4pol"]`, `mypy_path = ["src", "typings"]`, overrides `ignore_missing_imports = true` for `pandas.*`, `pyarrow.*`, `jsonschema.*` — their values are `Any`; typed functions convert to builtins before returning | verified | file read |
| F-17 | `[tool.importlinter]`: `root_package = "llm4pol"`, `include_external_packages = true`, one contract (`forbidden`, source `llm4pol.data`, forbidden `llm4pol.evaluate, llm4pol.run, llm4pol.loop, llm4pol.llm, sklearn`). `scripts/check.py` runs it through `lint_imports_argv()` (console script, never `python -m importlinter`) | verified | file read |
| F-18 | import-linter 2.15: a `forbidden` contract whose **forbidden** modules are absent from the graph is KEPT (source `forbidden.py`: "forbidden_modules_in_graph = [m for m in forbidden_modules if m.name in graph.modules]"); probe E: `evaluate ↛ loop/llm/run` with all three absent → `KEPT`, exit 0 | verified | Context7 `/seddonym/import-linter` + probe |
| F-19 | import-linter 2.15: a `forbidden` contract whose **source** module is absent is a hard error: `Module 'llm4pol.loop' does not exist.`, exit 1 (probe B with `evaluate` present and `loop` absent) | verified | probe |
| F-20 | Consequence: CONTEXT D-06 clause (2) cannot be written as `type = "forbidden", source_modules = ["llm4pol.loop"]` until Phase 5 creates `llm4pol.loop` | verified | derived from F-19 |
| F-21 | A wildcard source `source_modules = ["llm4pol.loop.*"]` (or `.**`) that matches nothing is KEPT (exit 0), **but** it does not cover an import placed in `llm4pol/loop/__init__.py` itself: probe X put `from llm4pol.evaluate.backends import radonpy` in `loop/__init__.py` and both `X1 loop.*` and `X2 loop.**` stayed KEPT. Wildcards replace whole segments only (`llm4pol.loo*` → "A wildcard can only replace a whole module") | verified | probe |
| F-22 | The optional-layers form `type = "layers", layers = ["(llm4pol.evaluate.backends.radonpy)", "(llm4pol.loop)"]` is KEPT while both modules are absent (probe G) and BROKEN with `llm4pol.loop is not allowed to import llm4pol.evaluate.backends.radonpy: llm4pol.loop -> llm4pol.evaluate.backends.radonpy (l.2)` when `loop/__init__.py` imports it (probe H/Y). Without parentheses a missing layer errors: `Missing layer 'llm4pol.loop': module llm4pol.loop does not exist.` (also with `exhaustive = false`). Docs: "You can make a layer optional by wrapping it in parentheses" | verified | Context7 + probe |
| F-23 | "Only `loop.agents` may import `llm`": `type = "forbidden", source_modules = ["llm4pol.*"], forbidden_modules = ["llm4pol.llm"], ignore_imports = ["llm4pol.loop.agents -> llm4pol.llm", "llm4pol.loop.agents -> llm4pol.llm.*", "llm4pol.loop.agents.* -> llm4pol.llm", "llm4pol.loop.agents.* -> llm4pol.llm.*"], unmatched_ignore_imports_alerting = "none"` is KEPT today (probe W), BROKEN on `llm4pol.loop.problem -> llm4pol.llm` while `loop.agents -> llm` is reported as "1 ignored import" (probe X3), and does not flag `llm`'s own intra-package imports (probe Z). A `\|` inside a layer means *independent siblings*, not "or" (probe G second contract broke on `evaluate -> data`) | verified | probe + Context7 |
| F-24 | jsonschema 4.26.0 `Draft202012Validator.check_schema` accepts the request and response schemas drafted in Code Example 1; `allOf: [ {if/then/else}, … ]` on `status` enforces `value`/`unit`/`n_replicates` `type: number/string/integer` when `status == "ok"` and `type: null` otherwise (probe: "ok but value null" INVALID `None is not of type 'number'`; "missing with value" INVALID `0.3 is not of type 'null'`) | verified | probe |
| F-25 | `then: {"not": {"required": ["reason"]}}` forbids `reason` on `ok` (probe: "ok with reason" INVALID) | verified | probe |
| F-26 | `if status == "missing" then required: ["reason"], reason enum ["value_absent", "candidate_unknown"]` works (probe: "missing without reason" INVALID `'reason' is a required property`; "bad reason" INVALID `'nope' is not one of […]`); `if status == "error" then required: ["reason"]` works | verified | probe |
| F-27 | `spread: {"type": ["number", "null"], "minimum": 0}` accepts `null` (`minimum` applies only to numbers) — "ok n=1 spread null" VALID | verified | probe |
| F-28 | `if status in [unsupported, missing, error] then cost.evals const 0` and `if cached == true then cost.evals const 0` both work (probe: "missing charged evals" INVALID `0 was expected`; "cached ok evals 1" INVALID) | verified | probe |
| F-29 | Request: `batch minItems 1 maxItems 1000`, `properties minItems 1 uniqueItems true` — "dup props" INVALID `has non-unique elements`; "empty batch" INVALID; "1001 batch" INVALID | verified | probe |
| F-30 | Python `True` is rejected by `{"type": "integer"}` in jsonschema 4.26 ("req bool iteration" INVALID) — no extra bool guard needed | verified | probe |
| F-31 | A request naming `static_dielectric_const` is schema-valid (the request schema does not enumerate keys); the evaluator answers `unsupported`. This is by design: the registry enum lives in `property-registry.json`, the request schema stays key-agnostic so M8 backends can add keys without a schema bump | verified (behaviour) / design choice | probe |
| F-32 | `[tool.llm4polcheck].validated` entry shape (`scripts/check.py::validate_inventory`): `{ name, instances = "<glob relative to root>", schema = "<path>", required = bool }`; `.json` instances are `json.load`ed and validated with `jsonschema.validate`; a `required = true` glob with zero matches fails; the step prints `llm4polcheck inventory: N entries, M instances processed` (currently `1 entries, 1 instances`) | verified | file read |
| F-33 | Windows JSONL: `path.open("a", encoding="utf-8", newline="\n")` + `json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False) + "\n"` produced bytes with no `\r`, LF-terminated, 2 lines for 2 puts; replay with `open("r", encoding="utf-8", newline="\n")` restored 2 entries equal to the originals | verified | probe |
| F-34 | `allow_nan=False` raises `ValueError: Out of range float values are not JSON compliant: nan` — a NaN `spread`/`value` can never reach the cache file; the backend must map NaN → `None` first | verified | probe |
| F-35 | `sort_keys=True` gives key-order-independent bytes (`{"b":1,"a":2}` and `{"a":2,"b":1}` → identical `{"a":2,"b":1}`) | verified | probe |
| F-36 | Per-append `flush()+os.fsync()` costs 2.1 ms on this machine (2,000 appends 4.24 s); replaying 2,002 lines takes 0.020 s | verified | probe |
| F-37 | `isinstance(obj, Backend)` works with `@runtime_checkable` `Protocol` using `@property` members; frozen dataclass mutation raises `FrozenInstanceError`; the skeleton in Code Example 2 passes `mypy --strict --python-version 3.13` with zero errors | verified | probe |
| F-38 | mypy strict does **not** narrow `str` to `Literal[...]` through an `==` chain (`Incompatible return value type (got "str", expected "Literal['ok', …]")`); narrow with `if s in STATUSES: return cast(Status, s)` where `STATUSES = frozenset(get_args(Status))` | verified | probe |
| F-39 | Synthetic fixture path (no real file): `pd.DataFrame(conftest.SYNTHETIC_ROWS).astype(DTYPES-subset)` → `load.add_identity` → `load.build_candidates` yields **9 candidates** in 0.05 s (incl. RDKit); `pq.write_table(pa.Table.from_pandas(cands, preserve_index=False).replace_schema_metadata({b"llm4pol.snapshot": …}), snapshot.candidates_parquet(tmp))` writes a 49-column parquet whose `candidate_id` is `large_string` like the real one | verified | probe |
| F-40 | Synthetic status cases: `7ec8cb49ff317efc` (`*CC*`/none) TC median 0.32, n 3, std 0.02 → `ok` with spread; `b3a635a55e1a6645` (`*CC(*)c1ccccc1`/atactic) n 2 → `ok` with spread 0.007071; `81b997b85ccd2069` (`*CO*`/none) TC NaN, n 0 → `missing/value_absent`; `d24805b4ce4c381c` (`*CC(*)F`/none) tg NaN, n 0 → `missing/value_absent` for `tg`, `ok` for TC (n 1, spread null); `182075ab56be81bf` TC 15.0 / tg 1.0e6 (physically absurd, `check_tc False`) → still `ok` (D-03: no population filter); any 16-hex id not in the table → `missing/candidate_unknown`; `static_dielectric_const` or `foo` → `unsupported` | verified | probe (values are invented fixture values, not data) |
| F-41 | Real-file tests skip pattern: session fixture `real_csv` in `tests/conftest.py` calls `pytest.skip(f"pinned PolyOmics file absent at {path} (never committed; run python -m llm4pol.data fetch)")`; `real_load` runs `load.load(REPO_ROOT, processed_dir=tmp_path_factory.mktemp("processed"))` once per session (16–19 s). For Phase 3 the cheaper analogue is a `real_candidates` fixture that skips when `snapshot.candidates_parquet(snapshot.processed_dir(REPO_ROOT))` is absent (read-only, 0.05 s) | verified | conftest read + F-09 |
| F-42 | Test baseline: 116 tests collected; full `python -m pytest -q` 40 s locally (real-file tests included), a single test file 1.5 s; CI reports `104 passed, 12 skipped` | verified | run this session; 02-05-SUMMARY |
| F-43 | Precedent (`calfloop.ledger.writer`): appends in binary mode with a canonical `\n`-terminated line, `flush()` + `os.fsync()`, under an OS advisory sidecar lock (`msvcrt.locking` / `fcntl.flock`); ADR-0012 separates a content-hash `calculation_key` (dedup/reuse) from `run_id`/`attempt_id` (one per attempt). No two-currency budget accounting exists in the precedent (`grep -rIn cpu_hours\|evals src/calfloop` → 0 hits) | verified | files read + grep |
| F-44 | `tests/test_governance.py` sibling-schema rule applies to `config/*.json` only; `protocol/` instances are covered by `[tool.llm4polcheck]`. `protocol/README.md` "Current contents" still says "Empty" (it predates Phase 2) | verified | file read |
| F-45 | CLI pattern in `llm4pol.data.__main__`: argparse, `stream.reconfigure(encoding="utf-8", errors="replace")`, exceptions → `print(f"ERROR: {exc}", file=sys.stderr); return 2`; `tests/test_data_cli.py` calls `cli.main([...])` in-process and asserts exit codes | verified | file read |
| F-46 | INVARIANTS.md today carries no A-1/A-2/A-3 rows — the "Architecture (charter §4) — guards landed" table has only A-7; rows are *added* when a guard lands ("the charter text is not edited") | verified | file read |
| F-47 | `gh` 2.96.0 is available; origin is `https://github.com/kn1218/llm4pol.git`; CI (`.github/workflows/ci.yml`) has `workflow_dispatch` and runs `pixi run --manifest-path env/pixi.toml check` on a two-OS matrix | verified | probe + file read |
| F-48 | Worst-case in-memory cache size: 78,676 × 9 = 708,084 entries; at ≈ 200 B per `EvalResult` ≈ 140 MB — never reached in practice (a 400-eval campaign × 3 properties = 1,200 entries). No size bound is needed for M2 | unverified (arithmetic on F-02; byte estimate not measured) | — |
| F-49 | A `layers` contract also flags *indirect* chains (loop → evaluate.__init__ → backends.radonpy) — so `llm4pol/evaluate/__init__.py` must not import `backends` eagerly in a way that would later drag `radonpy` in. Today harmless (no radonpy); design `evaluate/__init__.py` to export the contract only | unverified (documented behaviour of layers contracts; not probed with a chain) | Context7 docs |

## Project Constraints (from CLAUDE.md)

- Precedence: charter > REQUIREMENTS.md > CLAUDE.md > generated blocks; conflicts are **flagged**, never silently resolved (ADR-0002). The D-06 clause-2 correction above is such a flag.
- Gate `pixi run --manifest-path env/pixi.toml check` (ruff, format, mypy strict, import-linter, schema-inventory, history-secret-scan, pytest) passes before any commit; CI on Windows and Linux.
- Every cross-component payload has a JSON Schema in `protocol/schemas/`; "a payload with no schema has no guard".
- No data file is ever committed; `data/processed/` is git-ignored. Example instances under `protocol/examples/` must carry **invented** values (synthetic ids and numbers), never rows of the pinned file.
- Budget: `evals` and `cpu_hours` are separate currencies (A-3) — no combined score anywhere.
- Blindness (A-4) is a Phase 6 payload test; the evaluator response is *not* an LLM payload. Nothing here goes to a hosted model.
- Authoring and review are separate passes (`docs/governance/REVIEW-CHECKLIST.md`).
- "A rule that matters becomes a test, a schema or a CI check as soon as it is stable"; A-1, A-2, A-3 promotion lands in the same change as the code (D-08).
- "A number is published in one place; elsewhere it is cited" — units and the snapshot id come from `load_registry()` / `snapshot.SNAPSHOT_ID`, never from a literal in `evaluate`.
- Placeholder notes, skipped tests, stubs and unimplemented branches are blockers — `backends/radonpy.py` must **not** be created as a stub (D-05).
- Commit messages: conventional commits scoped by GSD plan id (`feat(03-01): …`). `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>` trailer per the session reminder.
- Never print or log `.env` contents; the evaluator reads no secrets.
- File-size discipline: < 800 lines per module (Phase 2 split `validate.py` into `sections.py`).

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Request parsing + schema validation | `llm4pol.evaluate.contract` (library) | `__main__` (CLI boundary) | Validate at the system boundary once; typed dataclasses inside |
| Status decision (`unsupported`/`missing`/`error`/`ok`) | `evaluate.evaluator` (orchestrator) using `evaluate.registry` (adapter) | `backends/table` reports `Lookup` facts | The backend only knows the table; the registry decides supportedness; the orchestrator composes |
| Value lookup | `evaluate.backends.table` | — | The only module that touches pyarrow/pandas |
| Units, key → column | `evaluate.registry` → `llm4pol.data.registry.load_registry()` | — | One place for the number (CLAUDE.md); D-06 allows `evaluate → data` |
| Cache (dict + JSONL) | `evaluate.cache` | — | Pure state container; no charging logic |
| Budget meter + refusal | `evaluate.budget` (+ orchestrator pre-commit check) | — | A-3: two fields, no combined score |
| Import boundary | `pyproject.toml [tool.importlinter]` + `tests/test_import_boundary.py` | `scripts/check.py` (already wired) | A-1/A-2 guard is static, not runtime |
| Population masks | **not this phase** — `llm4pol.data.filters` consumed by Phase 5 | — | D-03 |

## Standard Stack

### Core (all already locked in `env/pixi.lock`; nothing to install)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `jsonschema` | 4.26.0 | Draft 2020-12 validation of request/response (`Draft202012Validator`) | Already used by `data.registry` and `scripts/check.py`; same validator class the gate runs |
| `pyarrow` | 25.0.0 | Read the candidate parquet, read its schema metadata (`llm4pol.snapshot`) | Phase 2 writer; `Any`-typed under the mypy override |
| `pandas` | 3.0.5 | Row access / NaN handling on the loaded table | Phase 2 convention; `to_pandas()` costs 3 ms |
| `import-linter` | 2.15 | Contracts (F-18..F-23) | Already the gate's `import-linter` step |
| stdlib `dataclasses`, `typing.Protocol`, `json`, `argparse` | 3.13 | Contract types, cache lines, CLI | D-05 says pydantic-free |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pytest` | 9.1.1 | Tests (`tmp_path`, `tmp_path_factory`, `capsys`) | All tests |
| `mypy` | 2.3.1 | `--strict` on `llm4pol` | Gate |
| `ruff` | (locked) | lint/format, line-length 100 | Gate |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| dict-of-rows (`to_dict("records")`, 0.46 µs/lookup, 0.63 s build) | `dict[candidate_id, row_index]` + `df.at` (11 µs/lookup, 0.01 s build) | Both are O(1) and both are ≪ 10 ms for a 100×9 batch (F-10). Prefer `dict[candidate_id, int]` + column arrays (`tbl.column(c).to_pylist()` or numpy) — cheapest build, no pandas object on the hot path |
| `layers` optional form for A-2 (F-22) | `forbidden` with source `llm4pol.loop` | The latter errors until Phase 5 (F-19). Phase 5 may convert to `forbidden` when `loop` exists; both express the same rule |
| pydantic models | frozen dataclasses + jsonschema | Locked by D-05 (pydantic-free) |

**Installation:** none. **Version verification:** done in-session (F-01).

## Package Legitimacy Audit

No external package is installed by this phase; every import is already in `env/pixi.lock`
(F-01). `gsd-tools query package-legitimacy` was therefore not run. **Packages removed:** none.
**Packages flagged:** none.

## Architecture Patterns

### System Architecture Diagram

```
 caller (Phase 5 loop / CLI --request file)
        │  JSON request {run_id, iteration, batch[]}
        ▼
 ┌────────────────────────────┐   schema fail → exit 2 (CLI) / RequestError (lib)
 │ contract.parse_request     │◄── protocol/schemas/eval-request.json
 └────────────┬───────────────┘
              │ EvalRequest (frozen)
              ▼
 ┌──────────────────────────────────────────────────────────────┐
 │ evaluator.Evaluator.evaluate(request)                        │
 │  for entry in batch, for key in entry.properties (in order): │
 │   1. registry.is_supported(key)? no → unsupported (evals 0)  │
 │   2. cache.get((cid,key,backend.name,backend.source))         │
 │        hit → copy(cached=True, cost.evals=0)                 │
 │   3. backend.lookup(cid, key) → Lookup                       │
 │        error → status error, reason=ExcClass (never cached)  │
 │        missing → reason value_absent|candidate_unknown       │
 │        ok → value/unit/n/spread                              │
 │   4. charge: first non-cached ok per cid in this request     │
 │        → cost.evals 1, later ones 0; cpu_hours 0.0           │
 │  PHASE 1 done (pure, no state touched)                       │
 │   5. if evals_limit set and Σevals > meter.remaining(limit)  │
 │        → raise BudgetExceeded (nothing committed)            │
 │  PHASE 2 commit: cache.put(new ok/missing), meter.charge     │
 └────────────┬─────────────────────────────────────────────────┘
              │ EvalResponse (results in request order, cost = Σ)
              ▼
 contract.to_json → validated against eval-response.json in tests → stdout (CLI, exit 0)

 backends/table.TableBackend(path)          llm4pol.data
   lazy load on first lookup ──────────────► snapshot.candidates_parquet(processed_dir)
   asserts parquet meta llm4pol.snapshot == registry.snapshot
   index: dict[candidate_id → row]; columns <col>_median/_n/_std
   key → column via evaluate.registry ─────► data.registry.load_registry()
```

### Recommended Project Structure (Claude's discretion, D-05 names honoured)

```
src/llm4pol/evaluate/
├── __init__.py          # docstring + re-export of the contract types and Evaluator; imports NO backend (F-49)
├── __main__.py          # D-07 CLI: --request, --cache, --evals-limit; exit 0/2/3 (pattern F-45)
├── contract.py          # Status/MissingReason Literals, Cost, Lookup, EvalRequest, EvalResult, EvalResponse,
│                        #   Backend Protocol, parse_request(json)->EvalRequest (schema-validated), to_json()
├── registry.py          # adapter: PropertyTable = load_registry() once; supported(key), column(key), unit(key)
├── cache.py             # ResultCache: dict + optional JSONL (append per request, replay on open), CacheError
├── budget.py            # BudgetMeter (frozen; evals:int, cpu_hours:float), BudgetExceeded
├── evaluator.py         # Evaluator(backend, registry, cache, meter, evals_limit) — the two-phase algorithm
└── backends/
    ├── __init__.py      # docstring only
    └── table.py         # TableBackend(path, *, registry) implementing Backend over the candidate parquet
protocol/schemas/eval-request.json, eval-response.json
protocol/examples/eval-request.example.json, eval-response.example.json   (synthetic values)
tests/test_evaluate_contract.py     # schemas load, examples validate, dataclass<->json round trip, each status
tests/test_evaluate_table.py        # synthetic parquet fixture: statuses, order/count, error path
tests/test_evaluate_cache_budget.py # hit leaves evals unchanged, per-candidate charge, two currencies, JSONL replay
tests/test_evaluate_cli.py          # exit codes 0/2/3 in-process
tests/test_evaluate_real_file.py    # skips when candidates parquet absent; 100-entry batch on real ids
tests/test_import_boundary.py       # contracts present + negative probe (Pattern 7)
```

Charter §13 M2 names `evaluate/{contract,registry,cache,budget,backends/table}.py`; the extra
`evaluator.py` and `__main__.py` keep each file well under 800 lines and keep the orchestration out
of the type module.

### Pattern 1: Status decision order (D-02) — decided in the orchestrator, facts from the backend
**What:** `unsupported` is decided by the registry adapter *before* any backend call (so it never
touches the table and is never cached); `candidate_unknown` vs `value_absent` are both `missing`
but the backend distinguishes them in `Lookup.reason`; `error` is any exception raised inside
`backend.lookup`, converted to `Lookup(status="error", reason=type(exc).__name__)`.
**When to use:** always; the order guarantees that an unsupported key on an unknown candidate is
`unsupported`, not `missing` (tests should pin this).
```python
# evaluator.py (sketch; verified pieces: F-11, F-12, F-40)
def _lookup(self, cid: str, key: str) -> Lookup:
    if not self.registry.supported(key):          # A-7 holds: static_dielectric_const is not a key
        return Lookup(status="unsupported")
    try:
        return self.backend.lookup(cid, key)
    except Exception as exc:                      # snapshot unreadable, schema mismatch, KeyError…
        return Lookup(status="error", reason=type(exc).__name__)
```

### Pattern 2: Draft 2020-12 conditional null-ness (F-24..F-30)
See Code Example 1 for the full schema. The shape: top-level `properties` declare the *union*
types (`["number", "null"]`); an `allOf` of `if/then/else` blocks tightens per `status`. The
`reason` field is optional at the top level, forbidden on `ok`, required with an enum on
`missing`, required (free string = exception class name) on `error`. `cost.evals` is pinned to
`const 0` when status ≠ ok or `cached == true`.

### Pattern 3: Table backend — lazy load, snapshot assertion, NaN → None
```python
# backends/table.py (sketch)
class TableBackend:
    name = "table"; provenance_tier = "md_simulated"
    def __init__(self, path: Path, *, registry: Registry) -> None:
        self._path, self._registry = path, registry
        self.source = registry.snapshot                      # "polyomics:general_polymers@041e5834" (F-11)
        self._rows: dict[str, int] | None = None             # built on first lookup (D-08 error path)
        self._cols: dict[str, list[float | None]] = {}       # "<col>_median", "<col>_n", "<col>_std"
    def _load(self) -> None:
        table = pq.read_table(self._path)                    # FileNotFoundError → error status (F-19-style)
        meta = (table.schema.metadata or {}).get(b"llm4pol.snapshot", b"").decode()
        if meta != self.source:
            raise SnapshotMismatch(f"parquet snapshot {meta!r} != registry {self.source!r}")
        ids = table.column("candidate_id").to_pylist()
        self._rows = {cid: i for i, cid in enumerate(ids)}   # 0.01 s (F-09)
        for col in self._registry.columns():
            for suffix in ("_median", "_n", "_std"):
                self._cols[col + suffix] = table.column(col + suffix).to_pylist()  # None for nulls
    def lookup(self, candidate_id: str, property_key: str) -> Lookup:
        if self._rows is None: self._load()
        row = self._rows.get(candidate_id)
        if row is None: return Lookup(status="missing", reason="candidate_unknown")
        spec = self._registry.properties[property_key]
        median = self._cols[spec.column + "_median"][row]
        if median is None or median != median: return Lookup(status="missing", reason="value_absent")
        n = int(self._cols[spec.column + "_n"][row]); std = self._cols[spec.column + "_std"][row]
        spread = None if n < 2 or std is None or std != std else float(std)
        return Lookup(status="ok", value=float(median), unit=spec.unit, n_replicates=n, spread=spread)
```
`to_pylist()` on a double column yields `None` for nulls (not NaN) — but keep the `!= x` NaN guard,
because a pandas path would yield NaN (F-08, F-34). 28 columns `to_pylist` cost 0.53 s (F-10);
acceptable once per process. `int(...)` / `float(...)` conversions keep mypy strict happy under
the `pyarrow.*` `Any` override (F-16).

### Pattern 4: Two-phase evaluate (compute, then commit) with request-order results
**What:** Phase 1 builds the full `results` list by nested loops (`for entry in batch: for key in
entry.properties`) — this *is* the required ordering and count (D-01, EVAL-05). Charging is a
`set[str]` of candidate ids charged in this request. Phase 2 runs only after the budget check.
**Why:** `BudgetExceeded` must leave the cache and meter untouched (a refused request is not an
evaluation), and lookups are side-effect-free so computing first is free. It also makes the
"distinct uncached candidates" count in D-04 *exact* (based on real `ok` outcomes) instead of an
upper bound.
```python
charged: set[str] = set(); results: list[EvalResult] = []; new: list[tuple[CacheKey, EvalResult]] = []
for entry in request.batch:
    for key in entry.properties:
        ck = (entry.candidate_id, key, self.backend.name, self.backend.source)
        hit = self.cache.get(ck)
        if hit is not None:
            results.append(replace(hit, cached=True, cost=Cost(0, 0.0))); continue
        lk = self._lookup(entry.candidate_id, key)
        evals = 1 if (lk.status == "ok" and entry.candidate_id not in charged) else 0
        if evals: charged.add(entry.candidate_id)
        res = EvalResult.from_lookup(entry.candidate_id, key, lk, self.backend, cost=Cost(evals, 0.0))
        results.append(res)
        if lk.status in ("ok", "missing"): new.append((ck, res))       # never cache error (Pattern 5)
total = Cost(sum(r.cost.evals for r in results), 0.0)
if self.evals_limit is not None and total.evals > self.meter.remaining(self.evals_limit):
    raise BudgetExceeded(requested=total.evals, remaining=..., limit=self.evals_limit)
self.cache.put_many(new); self.meter = self.meter.charge(total)      # commit
```
Note `replace(hit, cached=True, cost=Cost(0, 0.0))`: the stored record keeps `cached: false` and
its original cost; the *returned* copy is what carries `cached: true` (F-33 shows the stored flag
stays `False` after replay).

### Pattern 5: Cache policy
- Key = `(candidate_id, property, backend.name, backend.source)` (EVAL-04). Serialise the key as a
  4-element list inside the line so replay is unambiguous (F-33).
- Cache `ok` and `missing` (deterministic facts of an immutable snapshot); **never** cache
  `error` (retryable, D-02) and never `unsupported` (never reaches the backend).
- Persistence off unless `cache_path` is given (Claude's discretion, CONTEXT recommends off).
- Append **per request** in one `open("a", encoding="utf-8", newline="\n")` block, `flush()`;
  `fsync` is optional (2 ms each, F-36) — the cache is a derived artifact; the Phase 4 ledger is
  the record. Replay on open; a malformed line raises `CacheError(f"{path}:{lineno}: …")`
  (no silent skipping; CLAUDE.md "never silently swallow errors").
- No size bound for M2 (F-48); `len(cache)` exposed for tests.

### Pattern 6: Budget meter — two currencies that cannot be merged (A-3)
```python
@dataclass(frozen=True, slots=True)
class BudgetMeter:
    evals: int = 0
    cpu_hours: float = 0.0
    def charge(self, cost: Cost) -> BudgetMeter: return BudgetMeter(self.evals + cost.evals, self.cpu_hours + cost.cpu_hours)
    def remaining(self, evals_limit: int) -> int: return max(evals_limit - self.evals, 0)
    def exhausted(self, evals_limit: int) -> bool: return self.evals >= evals_limit
```
Immutable (`charge` returns a new meter, per the coding-style rule); no `__float__`, no `total`,
no `__add__` between an `int` and a `float` field. **Test that pins A-3:** `charge(Cost(3, 0.0))`
then `charge(Cost(0, 2.5))` → `evals == 3` and `cpu_hours == 2.5` (probe output: `BudgetMeter(evals=3,
cpu_hours=2.5)`), plus an AST/`inspect` assertion that no attribute or method of `BudgetMeter`,
`Cost` or the response combines the two (e.g. grep the module source for `evals +` / `+ cpu_hours`
across fields — or simpler: `assert not hasattr(BudgetMeter, "total")` and a schema test that
`cost` has exactly the two keys `additionalProperties: false`, F-26). No two-currency prior art
exists in `calfloop` (F-43); this is new ground and the test is the guard.

### Pattern 7: Import-boundary guard-on-the-guard test
A contract that is KEPT because its modules are absent is indistinguishable from a vacuous one.
`tests/test_import_boundary.py` should (a) parse `pyproject.toml` and assert the four contract
names exist with the exact types/modules; (b) run `check.lint_imports_argv()` via `subprocess`
(same argv the gate uses, `cwd=REPO_ROOT`) and assert `0 broken`; (c) **negative probe**: copy
`src/llm4pol` into `tmp_path`, write `loop/__init__.py` containing `from llm4pol.evaluate.backends
import radonpy` and an empty `evaluate/backends/radonpy.py`, write a temp TOML with the A-2
contract, run `lint-imports --config <tmp.toml>` with `PYTHONPATH=<tmp>/src`, and assert the
output contains `BROKEN` and `llm4pol.loop -> llm4pol.evaluate.backends.radonpy`. This is exactly
what probe H/Y did (F-22) and proves the guard is live. (The temp copy must exclude
`__pycache__`; `shutil.copytree(..., ignore=shutil.ignore_patterns("__pycache__"))`.)

### Anti-Patterns to Avoid
- **Stub `backends/radonpy.py` "so the contract has a target"** — forbidden by D-05 and CLAUDE.md; unnecessary (F-18).
- **`source_modules = ["llm4pol.loop.*"]` as the A-2 guard** — silently misses `loop/__init__.py` (F-21).
- **Filtering candidates by the README triple or `check_tc` in the backend** — D-03 forbids; population is the loop's concern.
- **Re-reading `protocol/property-registry_v1.yaml` in `evaluate`** — use `load_registry()` (CONTEXT specifics; F-12).
- **Charging `evals` per property** — D-04 charges per distinct candidate per request.
- **Caching `error` results** — makes `error` non-retryable (D-02).
- **Writing `cached: true` into the JSONL** — the stored record is the fact; `cached` is a property of the *response*, set on return (Pattern 4).
- **A single `EvalResponse.cost` computed as anything but Σ of result costs** — the schema cannot check the sum; a test must.
- **`json.dumps` without `allow_nan=False`** — NaN would be written as `NaN` (invalid JSON) and break replay (F-34).
- **`open(..., "a")` without `newline="\n"` on Windows** — writes CRLF; the LF-only line discipline is what F-33 verified.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Payload validation | ad-hoc `if "run_id" not in …` checks | `jsonschema.Draft202012Validator(schema).iter_errors` with the committed schema | The gate validates the same schema; one definition (F-32) |
| Registry facts (units, columns, snapshot) | literals in `evaluate` | `llm4pol.data.registry.load_registry()` (F-11, F-12) | "A number is published in one place" |
| Parquet paths | string concatenation | `snapshot.candidates_parquet(snapshot.processed_dir(root))` (F-13) | Single source of the revision |
| Synthetic candidate table in tests | hand-written parquet columns | `load.add_identity` + `load.build_candidates` on `conftest.SYNTHETIC_ROWS` (F-39) | Guarantees the fixture has the writer's exact 49-column shape |
| Canonical JSON line | custom serialiser | `json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)` (F-33..F-35) | Deterministic bytes, NaN refused |
| Status narrowing for mypy | `==` chains | `frozenset(get_args(Status))` + `cast` (F-38) | mypy strict does not narrow `str` → `Literal` |
| Import boundary | runtime `sys.modules` walks | import-linter contracts (F-18..F-23) | Static, sees unreferenced modules and transitive chains (precedent Contract C rationale) |

**Key insight:** the evaluator is a thin, deterministic adapter between two frozen artifacts (a
schema and a parquet); every place it could improvise (units, paths, population, status) already
has an owner in `llm4pol.data` or in `protocol/`.

## Common Pitfalls

### Pitfall 1: Declaring the A-2 contract as `forbidden` with source `llm4pol.loop`
**What goes wrong:** the `import-linter` gate step fails on every run with `Module 'llm4pol.loop' does not exist.` (F-19).
**Why it happens:** import-linter validates *source* modules against the graph; only *forbidden* modules are filtered (F-18).
**How to avoid:** optional-layers form (F-22, Code Example 3) plus the negative test (Pattern 7).
**Warning signs:** the step's output has no `Contracts:` summary line at all.

### Pitfall 2: NaN leaking into results or the JSONL
**What goes wrong:** `json.dumps(..., allow_nan=False)` raises, or (without it) writes `NaN` which `json.loads` accepts but the schema rejects (`NaN is not of type 'number'` is *not* raised — Python's json parses `NaN` as float nan, and jsonschema treats it as a number, so the corruption is silent).
**Why it happens:** 69,237 of 78,676 TC rows have NaN `_std`; 9,635 have NaN `_median` (F-05..F-07).
**How to avoid:** map to `None` in the backend (Pattern 3) and keep `allow_nan=False` as the tripwire (F-34).
**Warning signs:** a `spread` of `nan` in any printed response.

### Pitfall 3: Replayed cache entries returned with `cached: false` / `evals: 1`
**What goes wrong:** a hit re-charges the budget or the schema's `cached == true ⇒ evals 0` rule fails (F-28).
**How to avoid:** `dataclasses.replace(hit, cached=True, cost=Cost(0, 0.0))` on every hit (Pattern 4); test "cache hit leaves `evals` unchanged" with a *fresh* `ResultCache(path)` instance (replay path), not only the in-memory one.

### Pitfall 4: CRLF cache files on Windows
**What goes wrong:** lines end in `\r\n`; `json.loads` tolerates it, but byte-identity tests and the Linux CI diverge.
**How to avoid:** `newline="\n"` on both open calls (F-33).

### Pitfall 5: Charging per (candidate, request) vs per candidate ever
**What goes wrong:** D-04's literal rule charges again when a *later* request asks a **new** property of an already-evaluated candidate (its other properties are cached, the new one is not). The loop's "400 evals" arithmetic assumes the same property set per candidate, so the readings coincide in practice — but a test must pin one reading.
**How to avoid:** implement the literal D-04 (per request), document the edge in `evaluator.py`'s docstring, add the test `test_new_property_of_a_cached_candidate_charges_one_eval`. Raised as Open Question Q2.

### Pitfall 6: `unsupported` vs `missing` precedence and the A-7 key
**What goes wrong:** an unknown candidate asked for `static_dielectric_const` returns `missing/candidate_unknown` if the backend is called first.
**How to avoid:** Pattern 1 order; pin with a test using an unknown id and the barred key (the registry enum already makes the key unregisterable — `test_a7_…` in Phase 2).

### Pitfall 7: pixi cwd for ad-hoc commands
**What goes wrong:** Phase 2 recorded that `pixi run … ruff check --fix <path>` picked up a different config. This session's ad-hoc `pixi run --manifest-path env/pixi.toml python …` from the repo root ran with the repo root as cwd (relative `data/processed/…` paths worked), but **`PYTHONPATH=src` must be set explicitly** for anything outside the `check`/`check-fast` tasks.
**How to avoid:** quick-run commands in the Validation Architecture below carry `PYTHONPATH=src`; the gate itself is unchanged.

### Pitfall 8: mypy strict and the `Any` boundary
**What goes wrong:** returning a pyarrow scalar or numpy float from a typed function fails strict (`Returning Any from function declared to return "float"`).
**How to avoid:** `float(...)`/`int(...)` at the boundary (Pattern 3); `Status` narrowing via `cast` (F-38).

### Pitfall 9: `protocol/README.md` still says "Current contents: Empty"
Update it with the schema/example rows in the docs task (F-44) so the protocol index is not stale after this phase.

## Code Examples

### 1. `eval-response.json` core (verified shape, F-24..F-28) and `eval-request.json` (F-29)
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/kn1218/llm4pol/protocol/schemas/eval-response.json",
  "title": "LLM4POL evaluator response — charter §7 (M2 freeze), A-1, A-3",
  "type": "object", "additionalProperties": false,
  "required": ["run_id", "iteration", "results", "cost"],
  "properties": {
    "run_id": {"type": "string", "minLength": 1},
    "iteration": {"type": "integer", "minimum": 0},
    "results": {"type": "array", "items": {"$ref": "#/$defs/result"}},
    "cost": {"$ref": "#/$defs/cost"}
  },
  "$defs": {
    "cost": {"type": "object", "additionalProperties": false, "required": ["evals", "cpu_hours"],
             "properties": {"evals": {"type": "integer", "minimum": 0}, "cpu_hours": {"type": "number", "minimum": 0}}},
    "result": {
      "type": "object", "additionalProperties": false,
      "required": ["candidate_id", "property", "status", "value", "unit", "n_replicates", "spread",
                   "backend", "source", "provenance_tier", "cached", "cost"],
      "properties": {
        "candidate_id": {"type": "string", "pattern": "^[0-9a-f]{16}$"},
        "property": {"type": "string", "minLength": 1},
        "status": {"enum": ["ok", "unsupported", "missing", "error"]},
        "value": {"type": ["number", "null"]},
        "unit": {"type": ["string", "null"]},
        "n_replicates": {"type": ["integer", "null"], "minimum": 1},
        "spread": {"type": ["number", "null"], "minimum": 0},
        "backend": {"type": "string", "minLength": 1},
        "source": {"type": "string", "minLength": 1},
        "provenance_tier": {"enum": ["md_simulated"]},
        "cached": {"type": "boolean"},
        "cost": {"$ref": "#/$defs/cost"},
        "reason": {"type": "string", "minLength": 1}
      },
      "allOf": [
        {"if": {"properties": {"status": {"const": "ok"}}},
         "then": {"properties": {"value": {"type": "number"}, "unit": {"type": "string"}, "n_replicates": {"type": "integer"}},
                  "not": {"required": ["reason"]}},
         "else": {"properties": {"value": {"type": "null"}, "unit": {"type": "null"}, "n_replicates": {"type": "null"}, "spread": {"type": "null"}}}},
        {"if": {"properties": {"status": {"const": "missing"}}},
         "then": {"required": ["reason"], "properties": {"reason": {"enum": ["value_absent", "candidate_unknown"]}}}},
        {"if": {"properties": {"status": {"const": "error"}}}, "then": {"required": ["reason"]}},
        {"if": {"properties": {"status": {"enum": ["unsupported", "missing", "error"]}}},
         "then": {"properties": {"cost": {"properties": {"evals": {"const": 0}}}}}},
        {"if": {"properties": {"cached": {"const": true}}},
         "then": {"properties": {"cost": {"properties": {"evals": {"const": 0}}}}}}
      ]
    }
  }
}
```
Notes: (a) `provenance_tier` enum has one value at M2; M9 extends it (A-5: a new schema version,
not an in-place edit once results cite v1 — or keep it a `string minLength 1` now; Q3). (b) The
`candidate_id` pattern is exact for this snapshot (F-04); a malformed id is a schema failure
(exit 2), an unknown well-formed id is `missing/candidate_unknown` (Q4). (c) Optional tightening:
`spread` must be a number when `n_replicates ≥ 2` — expressible as a fourth `if` (`"n_replicates":
{"minimum": 2}` in the `if`), untested this session; a Python test pins it anyway.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/kn1218/llm4pol/protocol/schemas/eval-request.json",
  "type": "object", "additionalProperties": false,
  "required": ["run_id", "iteration", "batch"],
  "properties": {
    "run_id": {"type": "string", "minLength": 1},
    "iteration": {"type": "integer", "minimum": 0},
    "batch": {"type": "array", "minItems": 1, "maxItems": 1000,
      "items": {"type": "object", "additionalProperties": false, "required": ["candidate_id", "properties"],
        "properties": {"candidate_id": {"type": "string", "pattern": "^[0-9a-f]{16}$"},
                       "properties": {"type": "array", "minItems": 1, "uniqueItems": true, "items": {"type": "string", "minLength": 1}}}}}
  }
}
```
Inventory registration (F-32):
```toml
[tool.llm4polcheck]
validated = [
    { name = "property registry v1 (DATA-03, A-7)", instances = "protocol/property-registry_v1.yaml", schema = "protocol/schemas/property-registry.json", required = true },
    { name = "evaluator request example (EVAL-01)", instances = "protocol/examples/eval-request.example.json", schema = "protocol/schemas/eval-request.json", required = true },
    { name = "evaluator response example (EVAL-01)", instances = "protocol/examples/eval-response.example.json", schema = "protocol/schemas/eval-response.json", required = true },
]
```
The example response should be the evaluator's *actual* output on the synthetic fixture for the
example request (a test can assert byte-equality after `json.dumps(indent=2, sort_keys=True)`),
so the committed example is never stale — and every value in it is invented (F-40), never a
PolyOmics row.

### 2. Contract skeleton that passes `mypy --strict` (F-37, F-38)
```python
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal, Protocol, cast, get_args, runtime_checkable

Status = Literal["ok", "unsupported", "missing", "error"]
STATUSES: frozenset[str] = frozenset(get_args(Status))

def parse_status(s: str) -> Status:
    if s in STATUSES:
        return cast(Status, s)
    raise ValueError(f"unknown status {s!r}")

@dataclass(frozen=True, slots=True)
class Cost:
    evals: int
    cpu_hours: float

@dataclass(frozen=True, slots=True)
class Lookup:
    status: Status
    value: float | None = None
    unit: str | None = None
    n_replicates: int | None = None
    spread: float | None = None
    reason: str | None = None

@runtime_checkable
class Backend(Protocol):
    @property
    def name(self) -> str: ...
    @property
    def source(self) -> str: ...
    @property
    def provenance_tier(self) -> str: ...
    def lookup(self, candidate_id: str, property_key: str) -> Lookup: ...
```
A class with plain class attributes `name = "table"` satisfies the `@property` protocol members
(`isinstance(T(), Backend)` → True, F-37).

### 3. `[tool.importlinter]` contracts — exact TOML, every line probed (F-17..F-23)
```toml
[tool.importlinter]
root_package = "llm4pol"
include_external_packages = true

# Phase 2 contract, unchanged (D-06 clause 3).
[[tool.importlinter.contracts]]
name = "llm4pol.data is independent of every other llm4pol subpackage (charter §6) and never imports a splitter (D-8)"
type = "forbidden"
source_modules = ["llm4pol.data"]
forbidden_modules = ["llm4pol.evaluate", "llm4pol.run", "llm4pol.loop", "llm4pol.llm", "sklearn"]

# A-1 (charter §6 row `evaluate`): the evaluator never reaches the loop, the LLM adapter or run
# management. The forbidden modules do not exist yet; import-linter skips absent forbidden
# modules and reports KEPT (F-18).
[[tool.importlinter.contracts]]
name = "A-1: llm4pol.evaluate never imports llm4pol.loop, llm4pol.llm or llm4pol.run (charter §6)"
type = "forbidden"
source_modules = ["llm4pol.evaluate"]
forbidden_modules = ["llm4pol.loop", "llm4pol.llm", "llm4pol.run"]

# A-2 (ADR-0003): the loop never imports the simulation backend. Written as a layers contract
# with BOTH layers optional because a `forbidden` contract errors when its source module does
# not exist (F-19) and `llm4pol.loop` is created in Phase 5. KEPT while absent, BROKEN the
# moment llm4pol.loop (or any module under it) imports the backend, including from
# loop/__init__.py (F-22). Phase 5 may rewrite it as `forbidden` once the package exists.
[[tool.importlinter.contracts]]
name = "A-2: llm4pol.loop never imports llm4pol.evaluate.backends.radonpy (ADR-0003, charter §6)"
type = "layers"
layers = ["(llm4pol.evaluate.backends.radonpy)", "(llm4pol.loop)"]

# EVAL-06 third clause (charter §6 row `llm`): only llm4pol.loop.agents may import llm4pol.llm.
# Wildcard source covers every present and future subpackage; the agents package is exempted
# through ignore_imports (F-23). The converse rule -- llm imports nothing of llm4pol -- needs
# `source_modules = ["llm4pol.llm"]` and lands in Phase 6 when the package exists.
[[tool.importlinter.contracts]]
name = "A-1: only llm4pol.loop.agents may import llm4pol.llm (charter §6)"
type = "forbidden"
source_modules = ["llm4pol.*"]
forbidden_modules = ["llm4pol.llm"]
ignore_imports = [
    "llm4pol.loop.agents -> llm4pol.llm",
    "llm4pol.loop.agents -> llm4pol.llm.*",
    "llm4pol.loop.agents.* -> llm4pol.llm",
    "llm4pol.loop.agents.* -> llm4pol.llm.*",
]
unmatched_ignore_imports_alerting = "none"
```
Expected gate output after this lands (from probe E/G/W): `Contracts: 4 kept, 0 broken.`

### 4. JSONL cache line and replay (F-33..F-35)
```python
def _line(key: CacheKey, result: EvalResult) -> str:
    record = {"key": list(key), "result": result.to_json()}          # to_json drops reason when None
    return json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False) + "\n"

def put_many(self, items: Iterable[tuple[CacheKey, EvalResult]]) -> None:
    items = list(items)
    for key, result in items: self._store[key] = result
    if self._path is not None and items:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8", newline="\n") as fh:
            fh.writelines(_line(k, r) for k, r in items)
            fh.flush()

def _replay(self, path: Path) -> None:
    with path.open("r", encoding="utf-8", newline="\n") as fh:
        for lineno, raw in enumerate(fh, start=1):
            if not raw.strip(): continue
            try: record = json.loads(raw)
            except json.JSONDecodeError as exc: raise CacheError(f"{path}:{lineno}: {exc.msg}") from exc
            k = record["key"]; self._store[(k[0], k[1], k[2], k[3])] = EvalResult.from_json(record["result"])
```

### 5. CLI exit-code contract (D-07; pattern F-45)
```python
def main(argv: Sequence[str] | None = None) -> int:
    ...
    try:
        request = contract.parse_request(json.loads(Path(args.request).read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError, contract.RequestError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr); return 2
    try:
        response = evaluator.evaluate(request)
    except BudgetExceeded as exc:
        print(f"BUDGET: {exc}", file=sys.stderr); return 3
    except OSError as exc:                       # cache path unwritable etc.
        print(f"ERROR: {exc}", file=sys.stderr); return 2
    print(json.dumps(response.to_json(), indent=2, sort_keys=True, allow_nan=False)); return 0
```
Backend read failures are **not** exit 2: they surface as per-result `error` (D-02) and exit 0.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `forbidden` contract naming a not-yet-existing importer | optional-layers `(module)` form (F-22) | import-linter has supported optional layers for years; the *need* appeared when Phase 3 pre-dates Phase 5 | Contract is live today and needs no stub |
| Draft-07 `dependencies` for conditional fields | Draft 2020-12 `if/then/else` in `allOf` (F-24) | 2020-12 is the project standard (`property-registry.json` already uses `if/then`, `prefixItems`) | Same validator class as the gate |
| pydantic models for payloads (calfloop precedent) | frozen dataclasses + jsonschema | D-05 | No pydantic in `evaluate`; JSON boundary explicit |

**Deprecated/outdated:** `jsonschema.__version__` attribute (DeprecationWarning; use `importlib.metadata`) — do not read it in tests.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | F-48: ~200 B per cached `EvalResult`; no size bound needed | Pattern 5 | Memory growth only in an unrealistic full-table sweep; add `max_entries` later |
| A2 | F-49: a `layers` contract flags indirect chains, so an eager `evaluate/__init__ → backends` import could one day chain to `radonpy` | Structure | Only bites in M9; keeping `__init__` free of backend imports costs nothing |
| A3 | The optional `spread`-when-`n ≥ 2` schema tightening works as written (not probed) | Code Example 1 note (c) | Test in Python regardless; schema tightening is optional |
| A4 | Phase 4's `run_id` format is compatible with `minLength: 1` (D-01 says any non-empty string) | Schema | None — Phase 4 may tighten the pattern in a new schema version |

## Open Questions (RESOLVED where CONTEXT decides)

1. **Contract type for A-2 (D-06 clause 2).** *Resolved by research, flagged for the owner:* the
   `forbidden` form errors while `llm4pol.loop` is absent (F-19); use the optional-layers form
   (F-22, Code Example 3). Same rule, same module names, live today. Phase 5 may convert it.
2. **`evals` per (candidate, request) or per candidate ever?** *Resolved by D-04 wording* ("once per
   distinct candidate per request"): implement literally; pin with the Pitfall 5 test; note that the
   loop's 400-eval arithmetic is unaffected because every request asks the same property set.
3. **`provenance_tier` as a one-value enum or a free string?** *Recommendation:* enum
   `["md_simulated"]` now — A-1 is about not conflating tiers, and an enum makes a typo a schema
   failure; M9 adds its value in `eval-response` v2 per A-5. Planner's call; either validates today.
4. **Malformed `candidate_id` (not 16 hex): schema failure or `missing`?** *Recommendation:* schema
   pattern `^[0-9a-f]{16}$` (F-04) → exit 2; `candidate_unknown` is reserved for well-formed ids
   absent from the snapshot. A malformed id is a caller bug, not a data fact.
5. **Which population the hidden table serves (Phase 2 owner question 3).** *Resolved by D-03:* the
   evaluator serves every candidate; populations are Phase 5's concern via `filters` (F-15).
6. **The 303 `unknown`-tacticity twins (Phase 2 owner question 2).** *Out of scope here:* they are
   distinct `candidate_id`s in the table and the evaluator answers per id; the decision affects
   Phase 5 sampling, not the contract.
7. **`fsync` on cache appends.** *Claude's discretion:* flush only (Pattern 5, F-36); the ledger
   (Phase 4) is the durable record.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| pixi | gate | ✓ | 0.80.0 | — |
| Python | everything | ✓ | 3.13.15 (pixi env) | — |
| pandas / pyarrow | table backend, fixture | ✓ | 3.0.5 / 25.0.0 | — |
| jsonschema | schemas | ✓ | 4.26.0 | — |
| import-linter | EVAL-06 | ✓ | 2.15 (`lint-imports` console script resolved by `check.lint_imports_argv`) | — |
| mypy / pytest / ruff | gate | ✓ | 2.3.1 / 9.1.1 / locked | — |
| `data/processed/candidates-041e5834.parquet` | real-file tests, evidence | ✓ locally (23.9 MB); ✗ in CI | — | tests skip with the F-41 reason; synthetic fixture covers logic |
| `gh` | CI evidence (`workflow_dispatch`) | ✓ | 2.96.0 | — |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** the processed parquet in CI (skip pattern, F-41).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.1.1 (`[tool.pytest.ini_options] testpaths = ["tests"], addopts = "-q"`) |
| Config file | `pyproject.toml` |
| Quick run command | `PYTHONPATH=src pixi run --manifest-path env/pixi.toml python -m pytest tests/test_evaluate_contract.py -x -q` (≈ 1.5 s per file, F-42) |
| Full suite command | `pixi run --manifest-path env/pixi.toml check` (7 steps; pytest alone 40 s locally incl. real-file tests, F-42) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| EVAL-01 | both schemas are valid 2020-12; examples validate; evaluator output on the synthetic fixture validates; dataclass ↔ JSON round trip | unit | `… pytest tests/test_evaluate_contract.py -x` | ❌ Wave 0 |
| EVAL-01 | examples registered in `[tool.llm4polcheck]` and processed by the gate step (`3 entries, 3 instances processed`) | unit | `… pytest tests/test_check_inventory.py -x` (+ new assertion on the live inventory) | ✅ (extend) |
| EVAL-02 | each status on the synthetic parquet (F-40): `ok` n=1/n≥2, `missing/value_absent`, `missing/candidate_unknown`, `unsupported` (barred key + `foo`), `error` (missing parquet path; reason `FileNotFoundError`); `unsupported`/`missing`/`error` carry `evals 0`; `error` re-attempted on the next call after the file appears (retryable, never cached) | unit | `… pytest tests/test_evaluate_table.py -x` | ❌ Wave 0 |
| EVAL-03 | every result has `backend == "table"`, `source == registry.snapshot`, `provenance_tier == "md_simulated"`, `unit` from `load_registry()` (F-11), `n_replicates == <col>_n`, `spread == <col>_std` or null | unit | same file | ❌ Wave 0 |
| EVAL-04 | second identical request: all `cached: true`, response `evals 0`, meter unchanged; same after `ResultCache(path)` re-open (replay); key includes backend and source (a different `source` string misses) | unit | `… pytest tests/test_evaluate_cache_budget.py -x` | ❌ Wave 0 |
| EVAL-04 / A-3 | `BudgetMeter` two currencies never merged (Pattern 6); `BudgetExceeded` leaves cache and meter untouched; per-candidate charging (3 properties → 1 eval; all-missing candidate → 0) | unit | same file | ❌ Wave 0 |
| EVAL-05 | 100-entry synthetic batch (ids cycled from the 9 + unknown ids) × k properties → `100·k` results, `[(r.candidate_id, r.property)] == flattened request` | unit | `… pytest tests/test_evaluate_table.py -x` | ❌ Wave 0 |
| EVAL-05 | 100 real candidate ids × 3 properties on the real parquet, order + count + all `ok`/`missing` (no `error`), < 1 s | integration (skips in CI) | `… pytest tests/test_evaluate_real_file.py -x` | ❌ Wave 0 |
| EVAL-06 | four contracts present; gate's `lint-imports` argv reports `0 broken`; negative probe BROKEN (Pattern 7) | unit + subprocess | `… pytest tests/test_import_boundary.py -x` | ❌ Wave 0 |
| D-07 | CLI exit 0 / 2 (bad JSON, schema failure, unreadable file) / 3 (`--evals-limit` exceeded); stdout is schema-valid JSON | unit (in-process `main([...])`) | `… pytest tests/test_evaluate_cli.py -x` | ❌ Wave 0 |
| D-08 | INVARIANTS.md gains A-1, A-2, A-3 rows naming the contracts and tests | doc + grep test (extend `test_governance`-style check that each named test is collected) | `… pytest tests/test_governance.py -x` | ✅ (extend) |

### Sampling Rate
- **Per task commit:** the one new test file for the task, `-x -q` (≤ 2 s).
- **Per wave merge:** `pixi run --manifest-path env/pixi.toml check-fast` (all steps except mypy), then `check`.
- **Phase gate:** `check` green locally on Windows and, by `workflow_dispatch`, on both CI runners (F-47); `03-EVIDENCE.md` cites the run id, head sha and the `Contracts: 4 kept, 0 broken` / `llm4polcheck inventory: 3 entries, 3 instances processed` lines.

### Wave 0 Gaps
- [ ] `tests/conftest.py` — add `synthetic_candidates(tmp_path) -> Path` (F-39: rows → `add_identity` → `build_candidates` → parquet with `llm4pol.snapshot` metadata) and `real_candidates()` session fixture (skip reason F-41, read-only, never writes `data/processed/`).
- [ ] `tests/test_evaluate_contract.py`, `tests/test_evaluate_table.py`, `tests/test_evaluate_cache_budget.py`, `tests/test_evaluate_cli.py`, `tests/test_evaluate_real_file.py`, `tests/test_import_boundary.py` — RED first per task.
- [ ] `protocol/examples/` directory (new) and the two `[tool.llm4polcheck]` entries.
- Framework install: none.

## Security Domain

`security_enforcement` is enabled (config). The evaluator is a local library + CLI with file I/O
only; no network, no auth, no secrets.

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — |
| V3 Session Management | no | — |
| V4 Access Control | no | — |
| V5 Input Validation | yes | `jsonschema` Draft 2020-12 at the boundary (`parse_request`); `maxItems 1000` bounds batch size; `candidate_id` pattern; unknown keys rejected by `additionalProperties: false` |
| V6 Cryptography | no | — (candidate ids are Phase 2's sha256 prefixes, not computed here) |
| V12 Files & Resources | yes | cache path is caller-supplied: open with explicit `encoding`, never `shell`, never follow a path outside the caller's intent (no globbing); a malformed line is a loud `CacheError`; the CLI never prints file contents on error, only the exception message |
| V14 Configuration | yes | no `.env` read; no secret can appear in a response (values are floats and registry strings) |

### Known Threat Patterns for this stack
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Oversized request (DoS) | Denial of service | schema `maxItems: 1000` on batch (F-29); properties bounded by `uniqueItems` and registry size in practice |
| Cache poisoning via a hand-edited JSONL | Tampering | replayed entries are re-validated (`EvalResult.from_json` type-checks; optional: validate each replayed result against `#/$defs/result`); a mismatch in the stored `source` vs the live registry snapshot is a miss, not a hit (key includes `source`) |
| Snapshot substitution (wrong parquet at the expected path) | Tampering | backend asserts parquet metadata `llm4pol.snapshot == registry.snapshot` at load (Pattern 3; F-03) |
| NaN/Infinity in JSON output | Information integrity | `allow_nan=False` everywhere (F-34) |
| Path traversal in `--cache`/`--request` | Elevation | paths are opened as given for the local user; no privilege boundary exists; document that the CLI is a developer tool |
| Data leakage into committed files | Information disclosure | `protocol/examples/*` carry invented values only (F-40); `data/processed/` stays git-ignored; the real-file test writes nothing under `data/` |

## Sources

### Primary (HIGH confidence — probed this session in the locked environment)
- pixi env probes: parquet schema/nulls/timings (F-02..F-10), registry dump (F-11), import-linter probes A–Z (F-18..F-23), jsonschema probes (F-24..F-31), JSONL/mypy/Protocol probes (F-33..F-38), synthetic fixture probe (F-39, F-40), pytest timing (F-42).
- Files read: `src/llm4pol/data/{registry,snapshot,load,schema,replicates,filters,__main__,identity}.py`, `pyproject.toml`, `scripts/check.py`, `tests/{conftest,test_data_real_file,test_check_inventory,test_data_registry,test_data_cli}.py`, `protocol/schemas/property-registry.json`, `protocol/property-registry_v1.yaml`, `docs/governance/INVARIANTS.md`, `docs/MASTER-PLAN.md` §4/§6/§7/§8/§9/§13, `.planning/phases/02-data-foundation/02-05-SUMMARY.md`, `02-VERIFICATION.md`, `.planning/ROADMAP.md` Phase 3, `env/pixi.toml`, `.github/workflows/ci.yml`.
- Precedent: `CALF20_DiscoveryLoop/docs/governance/ADR/0012-calculation-key-vs-run-id.md`, `src/calfloop/ledger/{writer,canonical_row,lock}.py`, `pyproject.toml [tool.importlinter]` (F-43).

### Secondary (MEDIUM confidence — official docs via Context7)
- `/seddonym/import-linter` — `docs/contract_types/layers.md` (optional layers in parentheses, `|` independent siblings), `docs/contract_types/forbidden.md` (options, wildcards), `src/importlinter/contracts/forbidden.py` (absent forbidden modules filtered). Confidence seam: `classify-confidence --provider context7 --verified` → MEDIUM; every cited behaviour was additionally reproduced locally.

### Tertiary (LOW confidence)
- none.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new packages; versions printed from the locked env.
- Architecture: HIGH for the contract/backend/cache/budget patterns (all probed); MEDIUM for the exact module split (Claude's discretion).
- Pitfalls: HIGH — each was observed (F-19, F-21, F-34, F-38) or derived from an observed number (F-05..F-07).

**Research date:** 2026-09-22
**Valid until:** 2026-10-22 (stable stack; re-probe only if `env/pixi.lock` changes)

---

### Probe log (abridged; commands run from the repository root with `PYTHONPATH=src pixi run --manifest-path env/pixi.toml python …`, scratch files under the session scratchpad)

```
# parquet
num_rows 78676 num_row_groups 1
snapshot meta: b'polyomics:general_polymers@041e5834'
read_table 0.049s; to_pandas 0.003s; shape (78676, 49)
candidate_id unique: True dtype str ; len set: [16]
thermal_conductivity     null_median=  9635 n0=  9635 n1= 59602 n>=2=  9439 std_nan= 69237
tg                       null_median= 27138 n0= 27138 n1= 49161 n>=2=  2377 std_nan= 76299
dict build 0.010s ; set_index 0.001s
1000 lookups: dict+df.at 11.1us each; set_index .at 14.4us each; records-dict build 0.630s, lookup 0.46us each

# import-linter 2.15 (lint-imports --config <tmp.toml>, PYTHONPATH=<tmp>/src)
B  forbidden, source llm4pol.loop absent            -> rc 1  "Module 'llm4pol.loop' does not exist."
E  forbidden, forbidden targets absent              -> rc 0  KEPT / KEPT
C  layers with plain missing layer                  -> rc 1  "Missing layer 'llm4pol.loop': module llm4pol.loop does not exist."
G  layers ["(…radonpy)", "(llm4pol.loop)"] absent   -> KEPT
H  same, loop/__init__.py imports radonpy           -> BROKEN  llm4pol.loop -> llm4pol.evaluate.backends.radonpy (l.2)
X  forbidden source "llm4pol.loop.*"/".**", same    -> KEPT (leaky)
Y  source "llm4pol.loo*"                            -> "A wildcard can only replace a whole module."
W/X3 source "llm4pol.*" forbidden llm + ignore      -> KEPT (absent); BROKEN on loop.problem -> llm; agents "1 ignored import"
Z  same, llm.provider -> llm.config                 -> KEPT

# jsonschema 4.26 Draft 2020-12 (see F-24..F-30): 11 negative cases INVALID with the expected message, 8 positive cases VALID

# JSONL / mypy
bytes has CR? False | ends with LF? True | lines: 2 ; replayed 2 equal? True | cached flag stored: False
NaN refused by allow_nan=False ; isinstance(T(), Backend): True ; frozen: FrozenInstanceError
2000 appends with fsync: 4.24s ; replay 2002 lines: 0.020s
mypy --strict: "Success: no issues found in 1 source file" (after the Literal-narrowing fix)

# synthetic fixture
candidates: 9 excluded: 1 1 (0.05s incl. RDKit) ; fixture parquet: candidates-041e5834.parquet cols 49 rows 9
```
