# Phase 3 — charter section 13 M2 evidence

- **Date (UTC):** 2026-09-21
- **Pushed tip:** `a5e854dc6ede48caebb81fe82da54afb88e65ce3` (`test(03-03): prove the batch of 100 in request order, the cached second batch and the CLI run on the pinned candidate table (D-07, D-08, EVAL-05, charter section 13 M2 (2), (3))`)
- **Snapshot:** `polyomics:general_polymers@041e5834`
- Each section below maps to one ROADMAP Phase 3 success criterion, which is the same-numbered
  charter section 13 M2 exit criterion. Every line is verbatim tool output paired with the
  command that produced it (Phase 1 D-04 convention); nothing here is narrative. All local
  commands run from the repository root on the Windows development machine with
  `PYTHONPATH=src` inside `pixi run --manifest-path env/pixi.toml …`. The `-v` runs are
  `python -m pytest <files> -v -v -k <expr>` (`[tool.pytest.ini_options] addopts = "-q"`
  cancels a single `-v`, as Phase 2 recorded). This evidence commit post-dates the cited CI
  run, which was dispatched on the pushed tip above.

## (1) Each status has a passing test; unsupported and missing consume no evals; error is retried

`python -m pytest tests/test_evaluate_table.py -v -v -k "test_ok_with_spread_when_n_ge_2 or test_ok_with_null_spread_when_n_is_1 or test_missing_value_absent_when_median_is_null or test_missing_candidate_unknown_for_a_well_formed_absent_id or test_unsupported_for_an_unregistered_key_and_the_barred_key_even_on_an_unknown_candidate or test_unsupported_and_missing_consume_no_evals or test_error_when_the_parquet_is_absent_consumes_no_evals_and_is_not_cached or test_error_is_retried_once_the_parquet_appears"`:

```
tests/test_evaluate_table.py::test_ok_with_spread_when_n_ge_2 PASSED
tests/test_evaluate_table.py::test_ok_with_null_spread_when_n_is_1 PASSED
tests/test_evaluate_table.py::test_missing_value_absent_when_median_is_null PASSED
tests/test_evaluate_table.py::test_missing_candidate_unknown_for_a_well_formed_absent_id PASSED
tests/test_evaluate_table.py::test_unsupported_for_an_unregistered_key_and_the_barred_key_even_on_an_unknown_candidate PASSED
tests/test_evaluate_table.py::test_unsupported_and_missing_consume_no_evals PASSED
tests/test_evaluate_table.py::test_error_when_the_parquet_is_absent_consumes_no_evals_and_is_not_cached PASSED
tests/test_evaluate_table.py::test_error_is_retried_once_the_parquet_appears PASSED
8 passed, 6 deselected in 0.71s
```

## (2) A cache hit leaves evals unchanged

`python -m pytest tests/test_evaluate_cache_budget.py tests/test_evaluate_real_file.py -v -v -k "test_cache_hit_leaves_evals_unchanged_in_memory or test_cache_hit_leaves_evals_unchanged_after_jsonl_replay or test_cache_key_includes_backend_and_source or test_real_second_identical_batch_is_fully_cached_with_zero_evals"`:

```
tests/test_evaluate_cache_budget.py::test_cache_hit_leaves_evals_unchanged_in_memory PASSED
tests/test_evaluate_cache_budget.py::test_cache_hit_leaves_evals_unchanged_after_jsonl_replay PASSED
tests/test_evaluate_cache_budget.py::test_cache_key_includes_backend_and_source PASSED
tests/test_evaluate_real_file.py::test_real_second_identical_batch_is_fully_cached_with_zero_evals PASSED
4 passed, 11 deselected in 0.79s
```

The real-file test answers the same 100-entry request twice through one evaluator: the second
response has every result `cached: true`, every result `cost.evals` 0, `response.cost ==
Cost(0, 0.0)` and `evaluator.meter.evals` unchanged from the first response.

## (3) A batch of 100 returns 100·k results in request order

`python -m pytest tests/test_evaluate_table.py tests/test_evaluate_real_file.py -v -v -k "test_batch_of_100_synthetic_entries_returns_300_results_in_request_order or test_real_batch_of_100_returns_300_results_in_request_order"`:

```
tests/test_evaluate_table.py::test_batch_of_100_synthetic_entries_returns_300_results_in_request_order PASSED
tests/test_evaluate_real_file.py::test_real_batch_of_100_returns_300_results_in_request_order PASSED
2 passed, 16 deselected in 0.72s
```

Counts-only run on the pinned table. A short snippet (never committed) read the first 100
`candidate_id` values of `data/processed/candidates-041e5834.parquet` into a request of 100
entries x `["thermal_conductivity", "dielectric_const_dc", "tg"]` in a temporary directory;
`pixi run --manifest-path env/pixi.toml evaluate --request <tmp>/request.json --root .` piped
through `python -c "import json, sys; r = json.load(sys.stdin); print(len(r['results']),
r['cost'], sorted({x['status'] for x in r['results']}))"`:

```
300 {'cpu_hours': 0.0, 'evals': 99} ['missing', 'ok']
```

(300 results for 100 entries x 3 properties; 99 distinct candidates with at least one `ok`
result charged once each — D-04; one candidate of the 100 has no `ok` result across the three
properties and is charged 0; statuses `ok` and `missing` only, no `error`. Measured in the test
file's comment: full-table load 0.03 s, the 300-lookup `evaluate` 0.012 s — RESEARCH F-09, F-10.)

## (4) Every response carries source, backend, provenance_tier, n_replicates, spread, unit and cost

`python -m pytest tests/test_evaluate_table.py tests/test_evaluate_cache_budget.py -v -v -k "test_every_result_carries_backend_source_and_provenance_tier or test_unit_n_replicates_and_spread_come_from_the_registry_and_the_candidate_table or test_a3_budget_meter_keeps_evals_and_cpu_hours_as_separate_currencies"`:

```
tests/test_evaluate_table.py::test_every_result_carries_backend_source_and_provenance_tier PASSED
tests/test_evaluate_table.py::test_unit_n_replicates_and_spread_come_from_the_registry_and_the_candidate_table PASSED
tests/test_evaluate_cache_budget.py::test_a3_budget_meter_keeps_evals_and_cpu_hours_as_separate_currencies PASSED
3 passed, 22 deselected in 0.43s
```

First result object of `protocol/examples/eval-response.example.json` (the evaluator's own
output on the 14-row synthetic fixture; every value invented, the id is the synthetic
`*CC*`/none candidate — `tests/test_evaluate_contract.py::test_committed_response_example_equals_evaluator_output_on_the_synthetic_root`):

```json
{
  "backend": "table",
  "cached": false,
  "candidate_id": "7ec8cb49ff317efc",
  "cost": {
    "cpu_hours": 0.0,
    "evals": 1
  },
  "n_replicates": 3,
  "property": "thermal_conductivity",
  "provenance_tier": "md_simulated",
  "source": "polyomics:general_polymers@041e5834",
  "spread": 0.020000000000000018,
  "status": "ok",
  "unit": "W/(m*K)",
  "value": 0.32
}
```

## (5) Schema validation and the import-linter contracts run inside the gate

`pixi run --manifest-path env/pixi.toml check`, the `schema-inventory` step:

```
llm4polcheck inventory: 3 entries, 3 instances processed
```

`PYTHONPATH=src pixi run --manifest-path env/pixi.toml lint-imports` (the `import-linter` step
runs the same resolved console script through `check.lint_imports_argv()`; the Phase 2
contract name carries `§`, which the cp949 console renders as replacement characters — the
TOML is UTF-8 and the three Phase 3 names are ASCII):

```
Analyzed 41 files, 147 dependencies.
------------------------------------

llm4pol.data is independent of every other llm4pol subpackage (charter §6) and
never imports a splitter (D-8) KEPT
A-1: llm4pol.evaluate never imports llm4pol.loop, llm4pol.llm or llm4pol.run
(charter section 6) KEPT
A-2: llm4pol.loop never imports llm4pol.evaluate.backends.radonpy (ADR-0003,
charter section 6) KEPT
A-1: only llm4pol.loop.agents may import llm4pol.llm (charter section 6,
EVAL-06) KEPT

Contracts: 4 kept, 0 broken.
```

`python -m pytest tests/test_evaluate_contract.py tests/test_import_boundary.py -v -v -k "test_both_schemas_are_valid_draft_2020_12 or test_committed_examples_validate_against_their_schemas or test_committed_response_example_equals_evaluator_output_on_the_synthetic_root or test_a1_contracts_are_declared_and_kept_by_the_gate_argv or test_a2_layers_guard_breaks_on_a_violating_import or test_llm_rule_breaks_when_a_non_agents_module_imports_llm"`:

```
tests/test_evaluate_contract.py::test_both_schemas_are_valid_draft_2020_12 PASSED
tests/test_evaluate_contract.py::test_committed_examples_validate_against_their_schemas PASSED
tests/test_evaluate_contract.py::test_committed_response_example_equals_evaluator_output_on_the_synthetic_root PASSED
tests/test_import_boundary.py::test_a1_contracts_are_declared_and_kept_by_the_gate_argv PASSED
tests/test_import_boundary.py::test_a2_layers_guard_breaks_on_a_violating_import PASSED
tests/test_import_boundary.py::test_llm_rule_breaks_when_a_non_agents_module_imports_llm PASSED
6 passed, 19 deselected in 1.32s
```

The two negative probes run the same tool with `--config` on a scratch copy of `src/llm4pol`
under `tmp_path` (RESEARCH Pattern 7): a copy whose `loop/__init__.py` imports
`llm4pol.evaluate.backends.radonpy` makes the A-2 contract report `BROKEN` with the chain
`llm4pol.loop -> llm4pol.evaluate.backends.radonpy` (F-22); a copy whose `loop/problem.py`
imports `llm4pol.llm` breaks the llm rule with `llm4pol.loop.problem -> llm4pol.llm` while a copy
where only `loop/agents/__init__.py` imports it stays `KEPT` (F-23). The repository holds no
`radonpy.py`, `loop`, `llm` or `run` before or after the tests
(`ls src/llm4pol/evaluate/backends/ src/llm4pol/ | grep -cE "^(radonpy\.py|loop|llm|run)$"` prints `0`).

`sed -n '/^| A-1 /,/^| A-3 /p' docs/governance/INVARIANTS.md`:

```
| A-1 | The evaluator is an interface: `table` and `radonpy` share one contract and no code assumes equal accuracy (`provenance_tier`) | `protocol/schemas/eval-response.json` (`provenance_tier` required on every result; enum `md_simulated` at M2, extended by a new schema version per A-5); the `[tool.importlinter]` contracts `A-1: llm4pol.evaluate never imports llm4pol.loop, llm4pol.llm or llm4pol.run` and `A-1: only llm4pol.loop.agents may import llm4pol.llm` (`import-linter` step of `scripts/check.py`); `tests/test_import_boundary.py::test_a1_contracts_are_declared_and_kept_by_the_gate_argv`; `tests/test_evaluate_table.py::test_every_result_carries_backend_source_and_provenance_tier` |
| A-2 | The loop package never imports the simulation backend (ADR-0003) | the `[tool.importlinter]` layers contract `A-2: llm4pol.loop never imports llm4pol.evaluate.backends.radonpy` (optional layers: KEPT while `llm4pol.loop` is absent, BROKEN on a violating import including from `loop/__init__.py`; `import-linter` step); `tests/test_import_boundary.py::test_a1_a2_contracts_are_declared_with_exact_modules`; `tests/test_import_boundary.py::test_a2_layers_guard_breaks_on_a_violating_import` |
| A-3 | The budget keeps `evals` and `cpu_hours` as two separately counted currencies; no combined score exists | `llm4pol.evaluate.budget.BudgetMeter` (exactly the two fields; `charge` returns a new meter; `remaining` / `exhausted` read `evals` only); `protocol/schemas/eval-response.json` `$defs/cost` (exactly `evals` and `cpu_hours`, `additionalProperties: false`); `tests/test_evaluate_cache_budget.py::test_a3_budget_meter_keeps_evals_and_cpu_hours_as_separate_currencies`. The ledger-schema guard the charter names lands at M3 (Phase 4) |
```

## Gate and CI

Local `pixi run --manifest-path env/pixi.toml check` at the pushed tip (run immediately before
the push; the real-file tests of Phase 2 and Phase 3 run here):

```
Steps: ruff check, ruff format --check, mypy, import-linter, schema-inventory, history-secret-scan, pytest
Contracts: 4 kept, 0 broken.
llm4polcheck inventory: 3 entries, 3 instances processed
dotenv-path-in-history: 0 hit(s)
scanned 67 commit(s) reachable from git rev-list --all
180 passed in 42.27s
SUMMARY: 7/7 steps passed
```

Every pattern class of the history scan printed `0 hit(s)` (ten classes plus the dotenv-path
check) before `git push origin main` (`03190d3..a5e854d  main -> main`).

`gh workflow run check --ref main`, then `gh run view <RUN_ID> --json databaseId,headSha,conclusion,url,event,headBranch,jobs`:

```
CI run id: 35661233933
CI head sha: a5e854dc6ede48caebb81fe82da54afb88e65ce3
CI url: https://github.com/kn1218/llm4pol/actions/runs/35661233933
CI event: workflow_dispatch
CI branch: main
check (windows-latest): success
check (ubuntu-latest): success
```

`gh run view 35661233933 --log | grep -E "SUMMARY:|llm4polcheck inventory|Contracts:|skipped|passed in|scanned [0-9]+ commit"` (job prefix kept, step name and timestamps dropped):

```
check (windows-latest)	Contracts: 4 kept, 0 broken.
check (windows-latest)	llm4polcheck inventory: 3 entries, 3 instances processed
check (windows-latest)	scanned 67 commit(s) reachable from git rev-list --all
check (windows-latest)	164 passed, 16 skipped in 12.01s
check (windows-latest)	SUMMARY: 7/7 steps passed
check (ubuntu-latest)	Contracts: 4 kept, 0 broken.
check (ubuntu-latest)	llm4polcheck inventory: 3 entries, 3 instances processed
check (ubuntu-latest)	scanned 67 commit(s) reachable from git rev-list --all
check (ubuntu-latest)	164 passed, 16 skipped in 6.39s
check (ubuntu-latest)	SUMMARY: 7/7 steps passed
```

The 16 skipped are the 12 of Phase 2 (the pinned PolyOmics CSV and the PoLyInfo manifest tests)
plus the 4 of `tests/test_evaluate_real_file.py` (the candidate parquet is never committed):
180 local = 164 + 16, so every test that skipped in CI passed locally.

## Owner flags

(a) **REQUIREMENTS.md EVAL-06 third clause vs 03-CONTEXT.md R-1.** EVAL-06 names three clauses
including "restrict `llm4pol.llm` to `llm4pol.loop.agents`"; CONTEXT R-1 says that rule enters
with Phase 6. REQUIREMENTS.md outranks a phase CONTEXT file (CLAUDE.md precedence; ADR-0002), so
the contract `A-1: only llm4pol.loop.agents may import llm4pol.llm (charter section 6, EVAL-06)`
was added in the wildcard-source form (RESEARCH F-23) and is proven KEPT today and BROKEN on a
violation. If the owner prefers R-1, the reversal is one `[[tool.importlinter.contracts]]` block
in `pyproject.toml` and one test (`test_llm_rule_breaks_when_a_non_agents_module_imports_llm`,
plus the third-contract assertions of `test_a1_a2_contracts_are_declared_with_exact_modules`
and the count `4`). Nothing is resolved here.

(b) **The D-04 charging edge (RESEARCH Open Question 2).** `evals` is charged once per distinct
candidate per request on its first non-cached `ok` result; a later request asking a *new*
property of an already-cached candidate is a fresh `ok` and is charged 1 again. Pinned by
`tests/test_evaluate_cache_budget.py::test_new_property_of_a_cached_candidate_charges_one_eval`
(plan 03-02). The loop's 400-eval arithmetic is unaffected while every request asks the same
property set; whether the literal reading stays is an owner decision.

(c) **Phase 2 open questions that touch the evaluator** are resolved by CONTEXT D-03 for this
phase: the evaluator applies no population filter (README triple, `check_tc`, `tg` window) and
the 303 twin candidates are distinct ids served as such. Stated for the owner, not decided.

## Data policy

`git ls-files protocol/examples data/`:

```
data/MANIFEST-open.sha256
data/MANIFEST.sha256
data/README.md
protocol/examples/eval-request.example.json
protocol/examples/eval-response.example.json
```

`grep -cE "(^|[^0-9a-f])[0-9a-f]{16}([^0-9a-f]|$)" tests/test_evaluate_real_file.py`:

```
0
```

No parquet, CSV, JSONL cache or request file is tracked; the real-file request of section (3)
was written to a temporary directory and the response reduced to counts before quoting. Every
16-hex token in this evidence file is a synthetic-fixture id from
`protocol/examples/eval-request.example.json` (`tests/conftest.py::SYNTHETIC_ROWS`); no real
candidate id, property value or secret-shaped string appears here.
