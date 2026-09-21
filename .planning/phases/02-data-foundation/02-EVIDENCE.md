# Phase 2 — charter §13 M1 evidence

- **Date (UTC):** 2026-09-22
- **Pushed tip:** `39c534517dbd4585fc3777ef48e16c3697b61b27` (`docs(02-05): add the dated correction note to the database survey, pointing at the validator report (R-3)`)
- **Snapshot:** `polyomics:general_polymers@041e5834`, revision `041e5834ea1a48682fae12dc39ccd723bcd4f771`
- Each section below maps to one ROADMAP Phase 2 success criterion, which is the same-numbered
  charter §13 M1 exit criterion. Every line is verbatim tool output paired with the command
  that produced it (Phase 1 D-04 convention); nothing here is narrative. All local commands
  run from the repository root on the Windows development machine with `PYTHONPATH=src`
  inside `pixi run --manifest-path env/pixi.toml …`.

## (1) Pinned files match data/MANIFEST-open.sha256

`python -m llm4pol.data fetch` (no download: both files present and matching):

```
verified general_polymers_with_sp_abbe_dynamic-dielectric.csv size=196910783 sha256=71e955ac1e90…
verified README.md size=15532 sha256=c2340252a720…
snapshot: polyomics:general_polymers@041e5834
```

`python -m pytest tests/test_data_real_file.py tests/test_data_fetch.py -v -v`:

```
tests/test_data_real_file.py::test_real_fetch_verifies_pinned_files_without_downloading PASSED
tests/test_data_fetch.py::test_committed_manifest_open_lists_the_two_pinned_files_with_research_hashes PASSED
```

## (2) Row count, unique units, 43,561, 88.9 %, 0 — reproduced or documented

`python -m llm4pol.data validate` (finding lines; `reproduce` is exact, `documented` pins the
observed research value within a tolerance, R-5):

```
finding source_rows: reproduce expected=95,335 observed=95,335 reproduced
finding source_columns: reproduce expected=259 observed=259 reproduced
finding unique_smiles_list: reproduce expected=78,379 observed=78,379 reproduced
finding dc_identity_max_residual: documented expected=5.7e-07 observed=5.7e-07 documented
finding static_maxwell_violations_triple: reproduce expected=38,693 observed=38,693 reproduced
finding static_maxwell_violation_pct_triple: documented expected=88.82 observed=88.82 documented
finding dc_maxwell_violations: reproduce expected=0 observed=0 reproduced
finding readme_triple_all_rows: reproduce expected=43,561 observed=43,561 reproduced
finding readme_triple_in_scope: reproduce expected=43,560 observed=43,560 reproduced
finding triple_check_tc_all_rows: reproduce expected=42,733 observed=42,733 reproduced
finding candidate_triple_filter_then_median: reproduce expected=40,212 observed=40,212 reproduced
finding tg_non_null: reproduce expected=56,064 observed=56,064 reproduced
finding tg_inside_window: reproduce expected=52,753 observed=52,753 reproduced
finding tg_outside_window: reproduce expected=3,311 observed=3,311 reproduced
finding tg_rmse_le_0.05: reproduce expected=36,592 observed=36,592 reproduced
finding tg_rmse_le_0.1: reproduce expected=42,232 observed=42,232 reproduced
finding tg_rmse_le_0.2: reproduce expected=43,316 observed=43,316 reproduced
finding tg_rmse_le_0.5: reproduce expected=43,521 observed=43,521 reproduced
finding tg_rmse_le_1.0: reproduce expected=43,545 observed=43,545 reproduced
```

The README's 88.9 % is documented as 88.82 %: the violation count 38,693 of 43,561 is a
`reproduce` finding (F-13's own fraction) and 38,693 / 43,561 = 88.8249 %, which rounds to 88.82
(RESEARCH F-13 printed 88.83 for the same fraction; the README's rounding is the documented
difference). The `dielectric_const_dc` violation count 0 is the identity
`dielectric_const_dc = static_dielectric_const − 1 + refractive_index²` (max residual 5.7e-7, F-14)
combined with `static_dielectric_const ≥ 1` (F-15), stated as such in the report's
`## Dielectric columns: identity and Maxwell check` section.

ROADMAP criterion 2 names the `tg_rmse` / 100–900 K counts: the window and every ladder rung are
above (`tg_*` and `tg_rmse_le_*`); no `tg_rmse` cut is applied. The report's Tg section carries
the wording flag for the owner (W-3), verbatim:

```
Wording discrepancy raised for the owner: REQUIREMENTS.md DATA-09 reads "filtered by tg_rmse"; CONTEXT R-2 (a development default recorded with the owner unavailable) applies no tg_rmse cut in M1 and records the ladder instead. This report records the count at every rung so the numbers satisfy either reading; which reading holds is an owner decision (precedence: charter > REQUIREMENTS.md > phase context, ADR-0002). Nothing is resolved here.
```

## (3) 95,335 vs 73,045 resolved

```
finding card_count_73045: documented expected=not reproducible from any column observed=not reproducible from any column documented
```

Report paragraph (`## Source shape`), verbatim:

```
The dataset card's 73,045 ("73,045 general polymers in the isotropic amorphous state") is reproduced by no column of the file: the table below lists the unique count of every identifier the card could have meant, and none equals 73,045. It is the card's description text, not a row count. The closest explanation, the paper's Table S2 per-class sum of unique structures, is an assumption (A1; RESEARCH F-19; charter section 13 M1 exit criterion (3)).
```

`## Counts the dataset card's 73,045 could have meant` table of the report:

```
| unique smiles_list | all source rows | 78,379 |
| unique canonical_psmiles (in scope) | all source rows | 78,373 |
| unique UUID | all source rows | 95,335 |
| source rows | all source rows | 95,335 |
| unique monomer_ID | all source rows | 78,336 |
```

## (4) Replicate structure and noise floor

```
finding replicate_multi_row_candidates: reproduce expected=12,983 observed=12,983 reproduced
finding replicate_max_rows: reproduce expected=17 observed=17 reproduced
finding same_version_replicate_candidates: documented expected=1,888 observed=1,887 documented
finding cross_version_rerun_candidates: documented expected=11,096 observed=11,096 documented
finding noise_floor_rel_thermal_conductivity: documented expected=0.0369 observed=0.0369 documented
finding noise_floor_rel_dielectric_const_dc: documented expected=0.0084 observed=0.0084 documented
finding noise_floor_rel_tg: documented expected=0.0577 observed=0.0577 documented
finding noise_floor_rel_density: documented expected=0.0034 observed=0.0034 documented
finding noise_floor_abs_tg: documented expected=30.2000 observed=30.2107 documented
finding noise_floor_triple_rel_thermal_conductivity: documented expected=0.0431 observed=0.0431 documented
finding noise_floor_triple_rel_dielectric_const_dc: documented expected=0.0112 observed=0.0112 documented
finding noise_floor_triple_rel_tg: documented expected=0.0540 observed=0.0540 documented
```

## (5) Feasible set under the development defaults

```
finding eps_q25_candidates: documented expected=2.6524 observed=2.6524 documented
finding eps_q25_triple_rows: documented expected=2.6427 observed=2.6427 documented
finding feasible_candidates_dev_defaults: reproduce expected=6,793 observed=6,793 reproduced
finding feasible_pct_dev_defaults: documented expected=16.89 observed=16.89 documented
finding feasible_rows_dev_defaults: documented expected=7,317 observed=7,317 documented
```

Report sentence (`## Feasible set under the development defaults (input to the D-16 gate)`),
verbatim:

```
The feasible set is the candidates of the README triple (filter then median) whose `dielectric_const_dc` median is at or below the Q25 of those medians and whose `tg` median is at or above the Tg minimum, both inclusive (F-60, F-62). The row-level count on the in-scope README-triple rows is printed under the row-level Q25 and under the candidate Q25 so nothing is lost either way. These thresholds are the charter's development defaults (section 13, D-16 row). This section is an input to the D-16 gate, which is fixed at the Phase 7 pre-registration (ADR-0005); nothing here is a decision.
```

## (6) D-7..D-10 and A-7 promoted

`python -m pytest tests/test_data_invariants.py tests/test_data_registry.py -v -v` (the `-v -v`
lines; test names carry the barred column's name by design — the grep gates on test bodies
exclude `def test_` lines):

```
tests/test_data_invariants.py::test_d7_candidate_table_dedups_replicates_before_any_metric PASSED
tests/test_data_invariants.py::test_d8_no_row_level_split_code_under_llm4pol_data PASSED
tests/test_data_invariants.py::test_d9_report_states_noise_floor_per_property_with_population PASSED
tests/test_data_invariants.py::test_d10_every_count_table_in_report_names_its_population PASSED
tests/test_data_invariants.py::test_a7_validator_and_loader_never_serve_static_dielectric_const PASSED
tests/test_data_registry.py::test_a7_static_dielectric_const_is_rejected_by_the_registry_schema PASSED
tests/test_data_registry.py::test_load_registry_rejects_an_instance_with_the_barred_key PASSED
```

`sed -n '/^| D-7 /,/^| D-10 /p' docs/governance/INVARIANTS.md`:

```
| D-7 | Rows that differ only in `sample_id` are deduplicated before any split or metric | `llm4pol.data.load.build_candidates` groups by `candidate_id` before any metric (candidate table `data/processed/candidates-<rev>.parquet`, read by the validator); `tests/test_data_invariants.py::test_d7_candidate_table_dedups_replicates_before_any_metric` |
| D-8 | Splits are grouped by polymer identity, never random at row level. Replicates would otherwise leak | no split code exists in `llm4pol.data`; `[tool.importlinter]` contract forbidding `sklearn` from `llm4pol.data` (`import-linter` step); `tests/test_data_invariants.py::test_d8_no_row_level_split_code_under_llm4pol_data`; sampling in later phases is at candidate level after `build_candidates` (charter §9) |
| D-9 | A reported effect smaller than the measured replicate noise floor is not reported as an effect | the `Replicate structure and noise floor` section of `docs/audit/polyomics-041e5834-validation.md` (per-property median relative and absolute spread over candidates with n ≥ 2, on the in-scope rows and on the README-triple rows); `tests/test_data_invariants.py::test_d9_report_states_noise_floor_per_property_with_population` |
| D-10 | Every reported count states the population it is drawn from. Matched-set sizes are recorded alongside every aggregate | `llm4pol.data.report.CountTable` refuses a table without a `population` column; every finding line of `python -m llm4pol.data validate` names its population; `tests/test_data_invariants.py::test_d10_every_count_table_in_report_names_its_population` |
```

`sed -n '/^| A-7 /p' docs/governance/INVARIANTS.md`:

```
| A-7 | The uncorrected static permittivity column is not a registry property; `dielectric_const_dc` only (ADR-0004) | `protocol/schemas/property-registry.json` propertyNames enum; `scripts/check.py` schema-inventory step; `tests/test_data_registry.py::test_a7_static_dielectric_const_is_rejected_by_the_registry_schema`; `tests/test_data_registry.py::test_load_registry_rejects_an_instance_with_the_barred_key`; `tests/test_data_invariants.py::test_a7_validator_and_loader_never_serve_static_dielectric_const` |
```

## Gate and CI

`pixi run --manifest-path env/pixi.toml check` (local, immediately before the push; grepped lines):

```
Steps: ruff check, ruff format --check, mypy, import-linter, schema-inventory, history-secret-scan, pytest
SELF-TEST OK: 10 pattern classes each matched their positive control
scanned 46 commit(s) reachable from git rev-list --all
pattern openai_secret_key: 0 hit(s)
pattern anthropic_secret_key: 0 hit(s)
pattern google_ai_api_key: 0 hit(s)
pattern huggingface_token: 0 hit(s)
pattern github_token: 0 hit(s)
pattern github_fine_grained_token: 0 hit(s)
pattern aws_access_key_id: 0 hit(s)
pattern slack_token: 0 hit(s)
pattern private_key_header: 0 hit(s)
pattern generic_credential_assignment: 0 hit(s)
dotenv-path-in-history: 0 hit(s)
116 passed in 39.52s
SUMMARY: 7/7 steps passed
```

`git push origin main` → tip `39c534517dbd4585fc3777ef48e16c3697b61b27`; `gh workflow run check --ref main` (Phase 1 D-05
convention: push events create no run here); `gh run list --workflow=check --event
workflow_dispatch --limit 1 --json databaseId,headSha,status --jq '.[0]'` returned the run below
with `headSha` equal to the pushed tip; `gh run watch 35648565974 --exit-status` exited 0.

```
CI run id: 35648565974
CI head sha: 39c534517dbd4585fc3777ef48e16c3697b61b27
CI url: https://github.com/kn1218/llm4pol/actions/runs/35648565974
CI event: workflow_dispatch
CI branch: main
CI conclusion: success
check (windows-latest): success
check (ubuntu-latest): success
```

`gh run view 35648565974 --json databaseId,headSha,conclusion,url,jobs --jq '{databaseId,headSha,conclusion,url,jobs:[.jobs[]|{name,conclusion}]}'`:

```
{"conclusion":"success","databaseId":35648565974,"headSha":"39c534517dbd4585fc3777ef48e16c3697b61b27","jobs":[{"conclusion":"success","name":"check (windows-latest)"},{"conclusion":"success","name":"check (ubuntu-latest)"}],"url":"https://github.com/kn1218/llm4pol/actions/runs/35648565974"}
```

`gh run view 35648565974 --log | grep -E "SUMMARY:|llm4polcheck inventory|skipped|passed in|scanned [0-9]+ commit"`
(log timestamps stripped; each line is prefixed by its job name):

```
check (windows-latest)	Run pixi run --manifest-path env/pixi.toml check llm4polcheck inventory: 1 entries, 1 instances processed
check (windows-latest)	Run pixi run --manifest-path env/pixi.toml check scanned 46 commit(s) reachable from git rev-list --all
check (windows-latest)	Run pixi run --manifest-path env/pixi.toml check 104 passed, 12 skipped in 7.11s
check (windows-latest)	Run pixi run --manifest-path env/pixi.toml check SUMMARY: 7/7 steps passed
check (ubuntu-latest)	Run pixi run --manifest-path env/pixi.toml check llm4polcheck inventory: 1 entries, 1 instances processed
check (ubuntu-latest)	Run pixi run --manifest-path env/pixi.toml check scanned 46 commit(s) reachable from git rev-list --all
check (ubuntu-latest)	Run pixi run --manifest-path env/pixi.toml check 104 passed, 12 skipped in 3.41s
check (ubuntu-latest)	Run pixi run --manifest-path env/pixi.toml check SUMMARY: 7/7 steps passed
```

The 12 skipped tests in CI are the eleven real-file tests (nine in
`tests/test_data_real_file.py`, two in `tests/test_data_invariants.py`) plus
`tests/test_manifest.py::test_raw_files_match_manifest`; all skip by design because the pinned
PolyOmics CSV and the PoLyInfo-derived raw files are never committed (D-09, ADR-0001). Locally,
where the pinned file exists, the same gate reports `116 passed`.

`python -m llm4pol.data validate` (last line):

```
VALIDATION: 49 reproduced, 38 documented, 0 failed -> exit 0
```

## Data policy

`git ls-files data/ docs/audit/polyomics-041e5834-validation.md`:

```
data/MANIFEST-open.sha256
data/MANIFEST.sha256
data/README.md
docs/audit/polyomics-041e5834-validation.md
```

Aggregates-only greps on the committed report (charter §10; each must print 0):

```
grep -c -E '\*[A-Za-z]' docs/audit/polyomics-041e5834-validation.md -> 0
grep -c -E '(^|[^0-9a-f])[0-9a-f]{16}([^0-9a-f]|$)' docs/audit/polyomics-041e5834-validation.md -> 0
grep -c -E '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}' docs/audit/polyomics-041e5834-validation.md -> 0
```

