---
phase: 03-evaluator-table-backend
verified: 2026-09-21T22:24:16Z
status: passed
score: 23/23 must-haves verified
covered_files:
  - ".planning/REQUIREMENTS.md"
  - ".planning/phases/03-evaluator-table-backend/03-01-PLAN.md"
  - ".planning/phases/03-evaluator-table-backend/03-01-SUMMARY.md"
  - ".planning/phases/03-evaluator-table-backend/03-02-PLAN.md"
  - ".planning/phases/03-evaluator-table-backend/03-02-SUMMARY.md"
  - ".planning/phases/03-evaluator-table-backend/03-03-PLAN.md"
  - ".planning/phases/03-evaluator-table-backend/03-03-SUMMARY.md"
  - ".planning/phases/03-evaluator-table-backend/03-CONTEXT.md"
  - ".planning/phases/03-evaluator-table-backend/03-EVIDENCE.md"
  - ".planning/phases/03-evaluator-table-backend/03-RESEARCH.md"
  - "docs/MASTER-PLAN.md"
  - "docs/governance/INVARIANTS.md"
  - "env/pixi.toml"
  - "protocol/README.md"
  - "protocol/examples/eval-request.example.json"
  - "protocol/examples/eval-response.example.json"
  - "protocol/schemas/eval-request.json"
  - "protocol/schemas/eval-response.json"
  - "pyproject.toml"
  - "scripts/check.py"
  - "src/llm4pol/evaluate/__init__.py"
  - "src/llm4pol/evaluate/__main__.py"
  - "src/llm4pol/evaluate/backends/__init__.py"
  - "src/llm4pol/evaluate/backends/table.py"
  - "src/llm4pol/evaluate/budget.py"
  - "src/llm4pol/evaluate/cache.py"
  - "src/llm4pol/evaluate/contract.py"
  - "src/llm4pol/evaluate/evaluator.py"
  - "src/llm4pol/evaluate/registry.py"
  - "tests/conftest.py"
  - "tests/test_check_inventory.py"
  - "tests/test_evaluate_cache_budget.py"
  - "tests/test_evaluate_cli.py"
  - "tests/test_evaluate_contract.py"
  - "tests/test_evaluate_real_file.py"
  - "tests/test_evaluate_table.py"
  - "tests/test_import_boundary.py"
covered_digest: "v1:sha256:96b2e51c4428ebf90ae200f34e2846bd2081636119223ba799937bc35ff34934"
behavior_unverified: 0
overrides_applied: 0
decision_coverage:
  honored: 13
  total: 13
  not_honored: []
  note: "gsd-tools check.decision-coverage-verify returned could-not-parse on this CONTEXT.md heading format; D-01..D-08 and R-1..R-5 were mapped by hand (see Decision Coverage section). R-1's llm-rule deferral is deviated from per REQUIREMENTS.md EVAL-06 and the deviation is recorded in four places, not silent."
owner_flags:
  - "EVAL-06 third clause vs 03-CONTEXT R-1: the `only llm4pol.loop.agents may import llm4pol.llm` contract was added now (REQUIREMENTS.md outranks the phase CONTEXT per CLAUDE.md precedence). Recorded in 03-03-PLAN objective, 03-03-SUMMARY key-decisions, 03-EVIDENCE Owner flags (a) and the pyproject.toml comment. Reversal is one TOML block and one test. Informational; does not affect goal achievement."
  - "D-04 charging edge (RESEARCH Open Question 2): a new property of an already-cached candidate in a later request is charged 1 again; pinned by test_new_property_of_a_cached_candidate_charges_one_eval. Owner decision whether the literal reading stays (03-EVIDENCE Owner flags (b))."
human_verification: []
---

# Phase 3: Evaluator (table backend) Verification Report

**Phase Goal:** Every property lookup goes through one evaluator contract backed by `table`, with a four-value status taxonomy, a cache that never double-charges, and a two-currency budget — charter §13 M2. Freezes: evaluator request/response schemas, import boundary (A-1, A-2).
**Verified:** 2026-09-21T22:24:16Z
**Status:** passed
**Re-verification:** No — initial verification

Every claim below was reproduced by command in this session from the repository at HEAD `0585787` (working tree clean, `main...origin/main` in sync). SUMMARY and EVIDENCE narratives were used only to locate what to check; nothing was accepted on their say-so.

## Goal Achievement

### Observable Truths

Roadmap Success Criteria (charter §13 M2) — the contract:

| #  | Truth | Status | Evidence |
| -- | ----- | ------ | -------- |
| SC1 | Each of `ok`, `unsupported`, `missing`, `error` has a passing test; `unsupported`/`missing` consume no `evals`; `error` is retried | ✓ VERIFIED | Gate `180 passed`; named tests `test_error_is_retried_once_the_parquet_appears`, `test_error_on_snapshot_mismatch_names_the_exception_class` run individually PASSED. CLI drive on synthetic root: statuses `ok,ok,ok,missing,missing,ok,missing,unsupported,ok`, reasons `value_absent,value_absent,candidate_unknown`, per-result evals `[1,0,0,0,0,1,0,0,1]`. CLI on an empty root: 8x `error`/`FileNotFoundError` evals 0, `unsupported` decided before the backend, response cost `{evals 0}`, no cache file written, exit 0 |
| SC2 | A cache hit on `(candidate_id, property, backend, source)` leaves `evals` unchanged | ✓ VERIFIED | CLI `--cache` run 1 → `cost.evals 3`; run 2 → every cacheable result `cached: true`, all evals 0, response `evals 0`, JSONL 8 lines before and after (no growth); stored lines have 4-string keys `[id, prop, "table", "polyomics:general_polymers@041e5834"]`, stored `cached` all `false`, stored statuses `{ok, missing}` only. Real parquet: run 1 `evals 99`, run 2 `evals 0`, all 300 `cached: true`. `test_cache_hit_leaves_evals_unchanged_after_jsonl_replay` PASSED |
| SC3 | A batch of 100 entries returns 100·k results in request order | ✓ VERIFIED | Real parquet, 100 ids x 3 properties (request built in scratchpad from parquet at run time): 300 results, `(candidate_id, property)` sequence equals the flattened request, statuses `{ok, missing/value_absent}`, no `error`, schema-valid, 0.87 s wall for the whole CLI process. Synthetic 100-batch test collected and passing in the gate |
| SC4 | Every response carries `source`, `backend`, `provenance_tier`, `n_replicates`, `spread`, `unit`, `cost {evals, cpu_hours}` | ✓ VERIFIED | Every result of every drive carried `('table', 'polyomics:general_polymers@041e5834', 'md_simulated')` and cost keys exactly `('cpu_hours','evals')`; schema `$defs/result.required` lists all 12 fields, `$defs/cost` `required == [evals, cpu_hours]`, `additionalProperties: false`; `unit`/`n_replicates`/`spread` populated on `ok` (`W/(m*K)`, 3, 0.02; n=1 → spread null) and null otherwise |
| SC5 | Schema validation of `eval-request.json`/`eval-response.json` and the first import-linter contracts run inside the check gate | ✓ VERIFIED | `pixi run check` → `llm4polcheck inventory: 3 entries, 3 instances processed`, `Contracts: 4 kept, 0 broken.`, `SUMMARY: 7/7 steps passed`, exit 0. Both examples registered in `[tool.llm4polcheck].validated` (3 inline entries) |

Plan must_haves (03-01 T1–T6, 03-02 T7–T13, 03-03 T14–T18):

| #  | Truth | Status | Evidence |
| -- | ----- | ------ | -------- |
| T1 | CLI reads a schema-validated request, answers through `Backend`/`TableBackend`, prints a schema-valid response; exit 0 / 2 | ✓ VERIFIED | Synthetic drive: 0 response-schema errors, exit 0. `ZZZZ` id → exit 2 `ERROR: /batch/0/candidate_id: 'ZZZZ' does not match '^[0-9a-f]{16}$'`; dup props → exit 2 `has non-unique elements`; absent request → exit 2; malformed cache → exit 2 `...badcache.jsonl:1: ...`; stdout empty in each |
| T2 | Synthetic example yields the nine statuses in order with reasons and per-candidate charging (`cost.evals` 3, `cpu_hours` 0.0) | ✓ VERIFIED | See SC1; response cost `{'cpu_hours': 0.0, 'evals': 3}` |
| T3 | Every result: `backend` `table`, `source` = registry snapshot, `provenance_tier` `md_simulated`, unit from registry, `n_replicates` = `_n`, `spread` = `_std` iff n ≥ 2, `cached` false, two-field cost | ✓ VERIFIED | See SC4; `table.py` reads `spec.unit`, `_n`, `_std` with `None if n < 2 or isnan`; `source` assigned from `properties.snapshot`, no literal (grep 0) |
| T4 | 100-entry synthetic batch → exactly 300 results in flattened-request order; response cost = sum of result costs | ✓ VERIFIED | `test_batch_of_100_synthetic_entries_returns_300_results_in_request_order` and `test_response_cost_is_the_sum_of_result_costs` collected and passing; real drive `sum evals == 99 == response evals` |
| T5 | Examples committed with invented values only, registered in the inventory; committed response equals the evaluator's own synthetic output | ✓ VERIFIED | Example ids = `{0123456789abcdef, 7ec8cb49ff317efc, 81b997b85ccd2069, b3a635a55e1a6645, d24805b4ce4c381c}` (synthetic + unknown); example request == `conftest.SYNTHETIC_EXAMPLE_REQUEST`; my CLI output on the synthetic root matches the committed response (9 results, same statuses, `evals 3`); `test_committed_response_example_equals_evaluator_output_on_the_synthetic_root` in the gate |
| T6 | No population filter: the absurd synthetic candidate (`check_tc` False) still answers `ok` | ✓ VERIFIED | `table.py` applies no mask; `llm4pol.data.filters` import count 0; `test_no_population_filter_is_applied` collected and passing |
| T7 | Second identical request fully cached, `evals` 0, meter unchanged — in memory and after JSONL replay | ✓ VERIFIED | See SC2; `test_cache_hit_leaves_evals_unchanged_after_jsonl_replay` PASSED individually |
| T8 | Cache key includes backend and source; `error` never stored; `unsupported` never reaches the cache; stored records keep `cached: false`; hit via `dataclasses.replace(..., cached=True, cost=Cost(0, 0.0))` | ✓ VERIFIED | JSONL keys 4 strings with backend/source; stored statuses `{ok, missing}`; `evaluator.py` decides `unsupported` before `key_for`, queues only `_CACHEABLE = {ok, missing}`, returns `dataclasses.replace(hit, cached=True, cost=Cost(0, 0.0))`; `test_cache_key_includes_backend_and_source` in gate |
| T9 | `evals` charged once per distinct candidate per request on its first non-cached `ok`; new property of a cached candidate charges 1 again | ✓ VERIFIED | Per-result evals `[1,0,0,0,0,1,0,0,1]`; `charged: set[str]` in `evaluate`; `test_new_property_of_a_cached_candidate_charges_one_eval` PASSED individually |
| T10 | `BudgetMeter` frozen, `charge` returns a new meter, no combining attribute; `remaining`/`exhausted` read `evals` only; A-3 row names meter, schema cost and test | ✓ VERIFIED | `budget.py` `@dataclass(frozen=True, slots=True)`, grep `__float__|__add__|total` = 0; INVARIANTS A-3 row names `BudgetMeter`, `$defs/cost` and `test_a3_budget_meter_keeps_evals_and_cpu_hours_as_separate_currencies` (collected) |
| T11 | `evals_limit` exceeded → `BudgetExceeded(requested, remaining, limit)`, nothing cached, meter unchanged | ✓ VERIFIED | CLI `--evals-limit 2` on a 3-eval request → exit 3, stderr `BUDGET: requested 3 evals, 2 remaining of limit 2`, stdout empty, cache file not created; `--evals-limit 3` → exit 0, 8 lines. `test_budget_exceeded_leaves_cache_and_meter_untouched` PASSED individually; two-phase commit order read in `evaluate` |
| T12 | Absent parquet → `error`/`FileNotFoundError`, evals 0, nothing cached; retried once the file appears; mismatched snapshot → `error`/`SnapshotMismatch` | ✓ VERIFIED | Empty-root CLI drive (SC1); `_frame()` stores nothing on a failed load; both named retry/mismatch tests PASSED individually |
| T13 | CLI exits 0 / 2 / 3 as documented; JSONL LF-only, one canonical line per record, appended per request with `flush()`, no NaN | ✓ VERIFIED | Exit codes above; cache bytes: no `\r`, ends LF, no `NaN` (synthetic and real 300-line file); `cache.py` `open("a", newline="\n")`, `fh.flush()`, `fsync` count 0, `allow_nan=False` present |
| T14 | `[tool.importlinter]` declares four contracts (data contract unchanged, A-1 forbidden, A-2 optional-layers, llm rule with wildcard source and four `ignore_imports`); gate prints `Contracts: 4 kept, 0 broken.` | ✓ VERIFIED | TOML read: four `[[tool.importlinter.contracts]]` blocks in the stated forms, `layers = ["(llm4pol.evaluate.backends.radonpy)", "(llm4pol.loop)"]`; gate and CI both print `Contracts: 4 kept, 0 broken.` |
| T15 | Guards are live, not vacuous: a scratch copy where `loop/__init__.py` imports the radonpy backend makes A-2 `BROKEN` with chain `llm4pol.loop -> llm4pol.evaluate.backends.radonpy`; a non-agents `llm` import breaks the llm rule, agents-only stays KEPT | ✓ VERIFIED | Named tests `test_a2_layers_guard_breaks_on_a_violating_import`, `test_llm_rule_breaks_when_a_non_agents_module_imports_llm` PASSED individually and assert `code == 1`, `"BROKEN" in output`, exact chains. Independent probe: copied `src/llm4pol` + full `pyproject.toml` to scratchpad, added `loop/__init__.py` importing both, ran `lint-imports --config` → `Contracts: 2 kept, 2 broken.` with `llm4pol.loop -> llm4pol.evaluate.backends.radonpy (l.1)` and `llm4pol.loop -> llm4pol.llm (l.2)`; repository tree untouched (`ls` shows no `loop`, `llm`, `run`, `radonpy.py`) |
| T16 | INVARIANTS.md carries A-1 and A-2 rows before A-3 naming the contracts, the `provenance_tier` field and the tests; charter text not edited | ✓ VERIFIED | Table order A-1, A-2, A-3, A-7; all five test names in the A-1/A-2/A-3 guard cells exist in `pytest --collect-only` (180 items) and the gate runs `python -m pytest` over `tests/`; `docs/MASTER-PLAN.md` §4 unchanged in the phase diff |
| T17 | Real parquet: 100 x 3 → 300 results in order, `ok`/`missing/value_absent` only, under 1 s after load; second identical request fully cached with `evals` 0; CLI run exits 0 schema-valid; tests skip with a stated reason when the parquet is absent | ✓ VERIFIED | See SC2/SC3 (my own CLI drives); `tests/test_evaluate_real_file.py` 4 tests collected, passing locally (parquet present), `real_candidates` fixture `pytest.skip("processed candidate parquet absent at ...")`; CI shows `164 passed, 16 skipped` = 180 local |
| T18 | Seven-step gate green locally and in a `workflow_dispatch` CI run on windows-latest and ubuntu-latest; `03-EVIDENCE.md` pairs each M2 criterion with command and verbatim output and contains no real candidate id or value | ✓ VERIFIED | Local gate 7/7. `gh run view 35661233933`: `conclusion success`, `event workflow_dispatch`, `headBranch main`, `headSha a5e854d…`, jobs `check (windows-latest)=success`, `check (ubuntu-latest)=success`; log shows `SUMMARY: 7/7 steps passed`, `Contracts: 4 kept, 0 broken.`, `inventory: 3 entries` on both. Evidence has 5 `## (n)` sections; 16-hex tokens not in the example request: 0 |

**Score:** 23/23 truths verified (0 present, behavior-unverified)

Behavior-dependent truths (SC1 retry, SC2/T7 cache hit, T11 budget refusal leaves no state, T12 failed load retried, T15 guard breaks on violation) were each upgraded to VERIFIED by a passing named test run individually in this session plus a direct CLI reproduction where one was possible — not on symbol presence.

### CI-verified sha vs HEAD

`git diff --name-only a5e854d HEAD -- . ':(exclude).planning'` is empty. HEAD `0585787` differs from the CI-verified sha only under `.planning/` (REQUIREMENTS, ROADMAP, STATE, state.json, 03-03-SUMMARY, 03-EVIDENCE). **No dispatch needed.**

### Deferred Items

None. No gap was found, so nothing was matched against Phases 4–8.

### Required Artifacts

`gsd_run query verify.artifacts` on the three plans: 10/10, 6/6, 5/5 passed (exists, non-stub, contains pattern). Wiring checked by hand:

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `src/llm4pol/evaluate/contract.py` | Status/Cost/Lookup/Backend Protocol/EvalRequest/EvalResult/EvalResponse/RequestError/parse_request/validators | ✓ VERIFIED | 351 lines; `parse_request` runs `Draft202012Validator` via `best_match` before building tuples; typed `from_json` readers reject bool-for-int; imported by evaluator, cache, budget, CLI |
| `src/llm4pol/evaluate/backends/table.py` | `TableBackend`, `SnapshotMismatch` | ✓ VERIFIED | pyarrow → pandas `set_index("candidate_id")` once per instance; metadata asserted against `properties.snapshot`; NaN → `missing/value_absent`; imported by CLI and tests only (never by `evaluate/__init__`, grep 0) |
| `src/llm4pol/evaluate/evaluator.py` | Two-phase `Evaluator.evaluate` with cache, meter, `evals_limit` | ✓ VERIFIED | Decision order unsupported → cache → backend; `BudgetExceeded` raised before `put_many`/`charge`; called from `__main__.py:104` |
| `src/llm4pol/evaluate/registry.py` | `PropertyTable` adapter, only `load_registry` call site | ✓ VERIFIED | `supported`, `spec`, `snapshot`, `columns`; yaml/registry-path literal count under `evaluate/` = 0 |
| `src/llm4pol/evaluate/cache.py` | `JsonlCache`, `key_for`, `canonical_line`, `CacheError` | ✓ VERIFIED | Replay re-validates through `EvalResult.from_json`; `CacheError(f"{path}:{lineno}: …")` reproduced on a malformed line |
| `src/llm4pol/evaluate/budget.py` | frozen `BudgetMeter`, `BudgetExceeded` | ✓ VERIFIED | 53 lines; no combining names |
| `src/llm4pol/evaluate/__main__.py` | `--request/--root/--cache/--evals-limit`; exit 0/2/3 | ✓ VERIFIED | `--help` lists all four flags; every exit path reproduced |
| `protocol/schemas/eval-request.json`, `eval-response.json` | Draft 2020-12; `^[0-9a-f]{16}$`; batch 1..1000; 5 conditional `allOf` blocks; tier enum `[md_simulated]` | ✓ VERIFIED | Read back programmatically; `test_response_schema_rejects_each_status_shape_violation` (parametrised) in gate |
| `protocol/examples/*.json` | Committed synthetic instances in `[tool.llm4polcheck]` | ✓ VERIFIED | 3 inventory entries; ids all synthetic; `static_` count 0 |
| `tests/test_evaluate_{cli,contract,table,cache_budget,real_file}.py`, `tests/test_import_boundary.py` | 10 + 20 + 14 + 11 + 4 + 5 tests | ✓ VERIFIED | 64 phase tests collected; no `skip`/`xfail`/`.only` markers (only the two by-design fixture skips in `conftest.py` for absent real files) |
| `docs/governance/INVARIANTS.md` | A-1, A-2, A-3 rows | ✓ VERIFIED | Guard cells name existing, collected tests |
| `.planning/phases/03-evaluator-table-backend/03-EVIDENCE.md` | Commands + verbatim outputs for M2 (1)–(5), CI id/sha/conclusions, owner flags | ✓ VERIFIED | Contains `CI run id: 35661233933`, both `check (...): success` lines, `## Owner flags` |
| `src/llm4pol/evaluate/backends/radonpy.py`, `src/llm4pol/{loop,llm,run}` | MUST NOT exist | ✓ ABSENT | `ls … | grep -cE "^(radonpy\.py|loop|llm|run)$"` → 0 |

### Key Link Verification

`gsd_run query verify.key-links`: 03-01 3/4, 03-02 3/4, 03-03 4/4. The two tool-reported misses are RE2 syntax rejections of the plan's patterns `Evaluator(` and `remaining(` (unescaped paren), not missing wiring — both confirmed by fixed-string grep:

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `evaluate/__main__.py` | `evaluate/evaluator.py` | `parse_request` → `Evaluator(TableBackend(...), properties, cache=, evals_limit=).evaluate` → `to_json` → stdout | WIRED | `__main__.py:104`; end-to-end CLI drives above |
| `backends/table.py` | `data/registry.py` (via `PropertyTable`) | unit/snapshot from `load_registry()`; metadata must equal `PropertyTable.snapshot` | WIRED | `SnapshotMismatch` raised on mismatch (named test PASSED) |
| `contract.py` | `protocol/schemas/eval-request.json` | `Draft202012Validator` before any dataclass | WIRED | exit-2 messages carry the JSON pointer |
| `pyproject.toml` | `protocol/examples/*.json` | `[tool.llm4polcheck]` entries → `schema-inventory` step | WIRED | gate prints `3 entries, 3 instances processed` |
| `evaluator.py` | `cache.py` | `cache.get(key)` before lookup; `put_many` only after the budget check | WIRED | `evaluator.py:120` after the raise at `:114` |
| `evaluator.py` | `budget.py` | `meter.remaining(evals_limit)` then `meter.charge(total)` | WIRED | `evaluator.py:112`, `:121` |
| `cache.py` | `contract.py` | `EvalResult.to_json`/`from_json` define and re-validate the JSONL record | WIRED | malformed record → `CacheError` reproduced |
| `INVARIANTS.md` | phase tests | A-1/A-2/A-3 guard cells name tests the gate runs | WIRED | all five names in the 180-item collection |
| `pyproject.toml` | `scripts/check.py` | `step_import_linter` runs `lint_imports_argv()` | WIRED | gate `PASS import-linter` |
| `test_import_boundary.py` | `scripts/check.py` | positive test runs the gate argv; negative probes run `--config` on a scratch copy | WIRED | tests read; independent probe reproduced BROKEN |
| `test_evaluate_real_file.py` | `tests/conftest.py` | `real_candidates` session fixture skips with reason | WIRED | fixture read; CI shows 4 extra skips |
| `03-EVIDENCE.md` | `.github/workflows/ci.yml` | cites the `workflow_dispatch` run and both job conclusions | WIRED | `gh run view` reproduces both `success` |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| `TableBackend.lookup` | `value`, `n_replicates`, `spread` | `frame.at[id, "<col>_median/_n/_std"]` from `pq.read_table(path)` | Yes — real parquet 300 results with 99 `ok` candidates; synthetic values 0.32/3/0.02 trace to hand-authored `SYNTHETIC_ROWS` | ✓ FLOWING |
| `TableBackend.lookup` | `unit` | `PropertyTable.spec(key).unit` ← `load_registry()` | Yes — `W/(m*K)`, `1`, `K` | ✓ FLOWING |
| `EvalResult.from_lookup` | `source` | `backend.source` ← `properties.snapshot` ← registry YAML | Yes — `polyomics:general_polymers@041e5834`; no literal in `evaluate/` | ✓ FLOWING |
| `Evaluator.evaluate` | `cost` | per-request `charged` set, summed | Yes — 3 / 99 / 0 observed | ✓ FLOWING |
| `JsonlCache.get` | `hit` | dict replayed from JSONL through `from_json` | Yes — second runs served entirely from the file | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Full gate | `pixi run --manifest-path env/pixi.toml check` | `Contracts: 4 kept, 0 broken.` / `inventory: 3 entries, 3 instances` / `180 passed in 45.74s` / `SUMMARY: 7/7 steps passed` / exit 0 | ✓ PASS |
| Synthetic example via CLI | `python -m llm4pol.evaluate --request protocol/examples/eval-request.example.json --root <synthetic root>` | exit 0; 9 results; schema errors 0; statuses/reasons/evals/cost as SC1 | ✓ PASS |
| Cache round trip | same + `--cache c1.jsonl` twice | run 2 all cacheable `cached: true`, evals 0, file 8 → 8 lines | ✓ PASS |
| Budget refusal | `--evals-limit 2` / `--evals-limit 3` | exit 3 `BUDGET: requested 3 evals, 2 remaining of limit 2`, no file / exit 0 | ✓ PASS |
| `error` path | `--root <empty dir>` | exit 0; 8x `error`/`FileNotFoundError` evals 0; `unsupported` untouched; no cache file | ✓ PASS |
| Exit 2 inputs | `ZZZZ` id; duplicate property; absent file; malformed cache line | exit 2 with `ERROR:` and pointer/line number each time; stdout empty | ✓ PASS |
| Real batch of 100 | request of first 100 parquet ids x 3 props, `--root .` `--cache creal.jsonl`, twice | 300 results in order, evals 99 then 0, all `cached: true` on run 2, 300 LF-only NaN-free lines, `git status -- data/` clean | ✓ PASS |
| Guard-on-the-guard | named tests + independent scratch-copy probe with the full four-contract config | tests PASSED; probe `Contracts: 2 kept, 2 broken.` with both chains | ✓ PASS |
| Named behavioral tests | 10 tests (import boundary x5, retry, mismatch, replay, Pitfall-5 charging, budget-untouched) run with `-k` | `10 passed, 20 deselected` | ✓ PASS |
| CI | `gh run view 35661233933 --json conclusion,jobs` and `--log` | `success` on both jobs; 7/7, 4 kept, 3 entries on both | ✓ PASS |

### Probe Execution

No `scripts/*/tests/probe-*.sh` exist and none is declared by the plans; the phase's own executable checks are the gate steps and the named pytest probes above. N/A.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| EVAL-01 | 03-01 | Payloads validate against both schemas; the suite loads them | ✓ SATISFIED | `parse_request` validates; response validated in tests and by me (0 errors); inventory step validates both examples |
| EVAL-02 | 03-01, 03-02 | Exactly one status in `{ok, unsupported, missing, error}`; `unsupported`/`missing` free; `error` retryable | ✓ SATISFIED | schema `status` enum of 4; evals 0 observed on all three non-`ok`; retry test PASSED |
| EVAL-03 | 03-01 | `backend`, `source`, `provenance_tier`, `n_replicates`, `spread`, `unit`, `cost {evals, cpu_hours}` on every response | ✓ SATISFIED | SC4 |
| EVAL-04 | 03-02 | Cache keyed by `(candidate_id, property, backend, source)`; hit leaves `evals` unchanged | ✓ SATISFIED | SC2; JSONL key shape |
| EVAL-05 | 03-01, 03-03 | Batch of 100 in request order with matching count | ✓ SATISFIED | SC3 synthetic + real |
| EVAL-06 | 03-03 | import-linter forbids `loop → evaluate.backends.radonpy`, `evaluate → loop/llm`, restricts `llm` to `loop.agents` | ✓ SATISFIED | four contracts KEPT in gate and CI; proven live by negative probes |

REQUIREMENTS.md marks all six `Complete` for Phase 3; no orphaned requirement maps to this phase.

### Decision Coverage

`check.decision-coverage-verify` returned `could-not-parse` (this CONTEXT.md uses `### D-0N` headings). Mapped by hand — 13/13 honored:

| Decision | Honored by | Note |
| -------- | ---------- | ---- |
| D-01 shapes, examples in inventory, order, count | schemas, examples, `evaluate` loops, SC3 | |
| D-02 taxonomy, `reason` enum, `error` retryable | SC1; `reason` `value_absent`/`candidate_unknown`/exception class | |
| D-03 value semantics, no population filter, `md_simulated` | `table.py`; filters import 0; T6 | |
| D-04 cache key, JSONL, per-candidate charging, `BudgetMeter`, `BudgetExceeded` | SC2, T9–T11 | charging edge flagged for owner (Open Question 2) |
| D-05 contract dataclasses, `Backend` Protocol, `TableBackend`, no radonpy | `contract.py`, `table.py`; stub count 0 | |
| D-06 import boundary clauses; `evaluate` may import `data` | T14; data contract unchanged | |
| D-07 CLI flags and exit codes; batch of 100 | T1, T13, SC3 | |
| D-08 synthetic fixture ≤ 20 (9 candidates), real-file skip, contract tests, INVARIANTS rows | fixtures, 64 tests, A-1/A-2/A-3 rows | |
| R-1 A-2 in layers form | T14 | **Deviation**: the "llm rule enters with Phase 6" clause was overridden by REQUIREMENTS.md EVAL-06 (higher precedence). Recorded in 03-03-PLAN objective, 03-03-SUMMARY key-decisions, 03-EVIDENCE Owner flags (a) and the `pyproject.toml` comment — not silent |
| R-2 charge once per distinct candidate per request | T9 | |
| R-3 tier enum; malformed id is exit 2 | schema enum `[md_simulated]`; `ZZZZ` → exit 2 | |
| R-4 flush per request, no fsync, never cache `error`, stored `cached: false`, NaN → None | T8, T13 | |
| R-5 pyarrow → pandas indexed by `candidate_id`, loaded once | `table.py::_frame` | |

### Prohibitions

All twelve plan prohibitions carry `verification: null`; each was checked with a deterministic command rather than judgment:

| Prohibition | Check | Result |
| ----------- | ----- | ------ |
| No `loop`/`run`/`llm` package or `backends/radonpy.py` (03-01, 03-03) | `ls` grep | 0 — absent, and the negative tests re-assert absence after running |
| `evaluate` never re-reads the registry YAML; no unit/snapshot literal (03-01) | greps | 0 / 0 |
| No README-triple / `check_tc` filter; `filters` not imported (03-01) | grep | 0 |
| Example ids are synthetic or the unknown id (03-01) | id set | exactly the five synthetic/unknown ids |
| No `error` cached; `unsupported` never reaches the cache (03-02) | stored statuses in my JSONL; `evaluator.py` order | `{ok, missing}`; `unsupported` handled before `key_for` |
| `budget.py` defines no combining attribute; `Cost`/`BudgetMeter` have exactly two fields (03-02) | grep; dataclass fields | 0; `evals`, `cpu_hours` |
| No per-line fsync (03-02) | grep | 0 |
| No `cached: true` stored (03-02) | stored flags | `{False}` |
| A-2 not in `forbidden`-with-absent-source or wildcard-source form (03-03) | TOML | `type = "layers"`, both optional |
| No real candidate id/value in evidence, tests or committed requests (03-03) | regex | 0 in test file; 0 non-synthetic 16-hex tokens in evidence; `git ls-files data/` = 2 manifests + README |
| No push before the gate passed (03-03) | CI at the pushed sha | `success` on both platforms at `a5e854d`; local gate output quoted in evidence pre-push (process claim; its observable consequence holds) |

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
| --------- | ---------- | ------ | ------- | -------- | --------------- | ------- |
| `test_evaluate_cli.py` | EVAL-01/02/05, D-07 | 10 | 0 | no | value + behavioral (exit codes, stdout/stderr, file growth) | OK |
| `test_evaluate_contract.py` | EVAL-01, R-3 | 20 | 0 | one by design (see below) | value (validator message fragments) | OK |
| `test_evaluate_table.py` | EVAL-02/03/05, D-03 | 14 | 0 | no | value (literal 0.32 / 3 / 0.02 from hand-authored `SYNTHETIC_ROWS`; cross-checked against the fixture parquet columns) | OK |
| `test_evaluate_cache_budget.py` | EVAL-04, A-3, R-2, R-4 | 11 | 0 | no | behavioral (multi-request state, bytes on disk, `FrozenInstanceError`) | OK |
| `test_import_boundary.py` | EVAL-06, A-1, A-2 | 5 | 0 | no | behavioral (exit code + BROKEN chain on a scratch copy) | OK |
| `test_evaluate_real_file.py` | EVAL-05, M2 (2)(3) | 4 | 0 locally (4 in CI by design, reason stated) | no | value + behavioral | OK |

**Disabled tests on requirements:** 0. **Circular patterns:** `test_committed_response_example_equals_evaluator_output_on_the_synthetic_root` compares the committed example to the evaluator's own output — circular by design as a freshness guard, and paired with independent literal pins in `test_evaluate_table.py` whose expected values come from the invented fixture rows, so correctness is not proven by the circular test alone. Not a blocker. **Insufficient assertions:** 0.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| — | — | No `TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/placeholder markers in any phase-modified file | — | none |
| `src/llm4pol/evaluate/contract.py` | 272, 281, 290 | `return None` | ℹ️ Info | typed optional-field readers returning `None` for a null optional field; not a stub |
| `pyproject.toml` (Phase 2 contract name) | — | `§` renders as replacement characters on the cp949 console | ℹ️ Info | pre-existing, cosmetic; the three new contract names are ASCII |

### Regression (Phase 1 and Phase 2 truths)

| Check | Result |
| ----- | ------ |
| No dotenv file tracked (only the `.example` template) | tracked dotfiles starting `.e`: `.env.example` only |
| `git ls-files data/` | `MANIFEST-open.sha256`, `MANIFEST.sha256`, `README.md` |
| Validator report byte-identical | `python -m llm4pol.data validate` exit 0; `git diff --exit-code -- docs/audit/` exit 0 |
| History secret scan | 10 pattern classes + dotenv-path check all `0 hit(s)` over 69 commits |
| Phase 2 import-linter contract unchanged | first contract block text unchanged; KEPT |
| Working tree | clean; `main...origin/main` |

### Human Verification Required

N/A — infrastructure/foundation phase (core library, CLI for developers, contracts, gate). Every success criterion was verifiable programmatically and no truth is left behavior-unverified. The two owner flags in the frontmatter are decisions for the owner to confirm at leisure, not blockers to goal achievement.

### Gaps Summary

None. The phase goal is achieved in the codebase: one `Backend` contract served by `TableBackend`, the four-status taxonomy with both `missing` reasons, a cache keyed by `(candidate_id, property, backend, source)` that never double-charges (in memory, on disk, and on the real 78,676-candidate table), a two-currency `BudgetMeter` with a structured refusal that commits nothing, provenance on every result, both schemas frozen with committed synthetic examples validated in the gate, and four import-linter contracts that are proven to break on a violation. CI is green on both platforms at a sha whose non-`.planning` tree equals HEAD.

---

_Verified: 2026-09-21T22:24:16Z_
_Verifier: Claude (gsd-verifier)_
