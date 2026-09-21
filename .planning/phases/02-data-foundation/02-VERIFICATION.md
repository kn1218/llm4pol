---
phase: 02-data-foundation
verified: 2026-09-21T20:26:40Z
status: passed
score: 26/26 must-haves verified
covered_files:
  - ".planning/REQUIREMENTS.md"
  - ".planning/phases/02-data-foundation/02-01-PLAN.md"
  - ".planning/phases/02-data-foundation/02-01-SUMMARY.md"
  - ".planning/phases/02-data-foundation/02-02-PLAN.md"
  - ".planning/phases/02-data-foundation/02-02-SUMMARY.md"
  - ".planning/phases/02-data-foundation/02-03-PLAN.md"
  - ".planning/phases/02-data-foundation/02-03-SUMMARY.md"
  - ".planning/phases/02-data-foundation/02-04-PLAN.md"
  - ".planning/phases/02-data-foundation/02-04-SUMMARY.md"
  - ".planning/phases/02-data-foundation/02-05-PLAN.md"
  - ".planning/phases/02-data-foundation/02-05-SUMMARY.md"
  - ".planning/phases/02-data-foundation/02-CONTEXT.md"
  - ".planning/phases/02-data-foundation/02-EVIDENCE.md"
  - ".planning/phases/02-data-foundation/02-RESEARCH.md"
  - "data/MANIFEST-open.sha256"
  - "docs/MASTER-PLAN.md"
  - "docs/audit/README.md"
  - "docs/audit/polyomics-041e5834-validation.md"
  - "docs/governance/INVARIANTS.md"
  - "docs/research/databases/README.md"
  - "env/pixi.lock"
  - "env/pixi.toml"
  - "protocol/property-registry_v1.provenance.yaml"
  - "protocol/property-registry_v1.yaml"
  - "protocol/schemas/property-registry.json"
  - "pyproject.toml"
  - "scripts/check.py"
  - "src/llm4pol/data/__init__.py"
  - "src/llm4pol/data/__main__.py"
  - "src/llm4pol/data/expectations.py"
  - "src/llm4pol/data/fetch.py"
  - "src/llm4pol/data/filters.py"
  - "src/llm4pol/data/identity.py"
  - "src/llm4pol/data/load.py"
  - "src/llm4pol/data/registry.py"
  - "src/llm4pol/data/replicates.py"
  - "src/llm4pol/data/report.py"
  - "src/llm4pol/data/schema.py"
  - "src/llm4pol/data/sections.py"
  - "src/llm4pol/data/snapshot.py"
  - "src/llm4pol/data/validate.py"
  - "tests/conftest.py"
  - "tests/test_check_inventory.py"
  - "tests/test_data_cli.py"
  - "tests/test_data_fetch.py"
  - "tests/test_data_identity.py"
  - "tests/test_data_invariants.py"
  - "tests/test_data_real_file.py"
  - "tests/test_data_registry.py"
  - "tests/test_data_schema.py"
  - "tests/test_manifest.py"
  - "typings/rdkit/Chem/__init__.pyi"
  - "typings/rdkit/RDLogger.pyi"
  - "typings/rdkit/__init__.pyi"
covered_digest: "v1:sha256:671f0594890f2cd70b133bb1044a678030f6aab5a05dfa289d4154b9361f22d8"
behavior_unverified: 0
overrides_applied: 0
decision_coverage:
  honored: 16
  total: 16
  not_honored: []
  note: "gsd query check.decision-coverage-verify returned could-not-parse (CONTEXT uses `### D-01 …` headings); D-01..D-10 and R-1..R-6 were checked by hand below"
prohibitions:
  - statement: "No data file is committed: git ls-files data/ lists only data/README.md, data/MANIFEST.sha256 and data/MANIFEST-open.sha256"
    declared_verification: null
    status: verified
    enforcement: "verifier: `git ls-files data/` -> exactly those three files; `git ls-files | grep -E '\\.(parquet|csv)$'` -> 0; `git check-ignore -v` resolves data/raw/…/.cache and data/processed/*.parquet to .gitignore lines 33 and 35"
  - statement: "No fixture row is copied from the pinned file; the 14 synthetic rows are invented"
    declared_verification: null
    status: verified
    enforcement: "verifier: tests/conftest.py _CORE holds 14 rows with round invented values (TC 0.30/0.34/0.32, RI exactly 1.50/1.45/1.59, Tg 250/270/260 K), UUIDs `u01..u14` (not UUID-shaped), static_dielectric_const derived by construction from the identity; none of these value tuples can come from the pinned file"
  - statement: "Nothing in src/llm4pol/data runs a child process through a shell; fetch never trusts hf_hub_download's hash"
    declared_verification: null
    status: verified
    enforcement: "verifier: grep subprocess|shell=|os.system|os.popen over src/llm4pol/data/*.py -> 0; fetch.py verify_file streams sha256 of the payload itself after any download; tests/test_data_fetch.py::test_fetch_downloads_a_missing_file_then_verifies_it PASSED"
  - statement: "The barred column named by A-7 appears nowhere in the registry instance, not even in a comment"
    declared_verification: null
    status: verified
    enforcement: "verifier: grep -c static_dielectric_const on protocol/property-registry_v1.yaml, protocol/schemas/property-registry.json, protocol/property-registry_v1.provenance.yaml -> 0 / 0 / 0; propertyNames enum lists exactly the nine keys; test_a7_static_dielectric_const_is_rejected_by_the_registry_schema and test_load_registry_rejects_an_instance_with_the_barred_key PASSED by name"
  - statement: "No tg_rmse cut is applied by the registry in M1; only the ladder is recorded"
    declared_verification: null
    status: verified
    enforcement: "verifier: registry `tg.filters` carries only tg_rmse_ladder and tg_rmse_unit; filters.tg_rmse_ladder_counts counts rows per rung and never masks; validate.py _tg_section titles the table `tg_rmse ladder (no cut applied)`; readme_triple_mask reads only TC non-null, eps range, tg range"
  - statement: "No numeric threshold in the registry is described as a D-16 decision"
    declared_verification: null
    status: verified
    enforcement: "verifier: registry header states physical_range is NOT a D-16 threshold; report section is titled `… (input to the D-16 gate)` and ends `nothing here is a decision`; grep -c 'threshold =' on the committed report -> 0"
  - statement: "No expected number in a real-file test is changed to make a test pass"
    declared_verification: null
    status: verified
    enforcement: "verifier: every expected value in tests/test_data_real_file.py and expectations.py was recomputed independently with plain pandas on the raw CSV (see Behavioral Spot-Checks): 95,335 x 259, 78,379, 43,561, 42,733, 38,693/43,561 = 88.8249 %, residual 5.69e-7, 0 dc violations, 56,064/52,753/3,311, 3 second-monomer rows; the one deviation from the plan text (88.83 -> 88.82) is the correct rounding of the same fraction and is documented in 02-05-SUMMARY.md and in the report's Finding notes"
  - statement: "smiles_search is never used for identity and never declared as an identity column"
    declared_verification: null
    status: verified
    enforcement: "verifier: grep smiles_search over src/llm4pol/data/*.py -> 0; IDENTITY_COLUMNS = (candidate_id, canonical_psmiles, row_index); add_identity canonicalises smiles_list only"
  - statement: "No range or filter literal (1, 20, 100, 900, 0.1) is written into filters.py, replicates.py or validate.py; they come from the loaded registry"
    declared_verification: null
    status: verified
    enforcement: "verifier: within_physical_range / readme_triple_mask / tg_window_counts / tg_rmse_ladder_counts / check_tc_mask all read PropertySpec fields; the only literals in filters.py are the cited F-08 alternative ceilings (10/50/100, printed not used), the F-12 window quantiles, the F-19 card count and the charter D-16 development defaults (400.0 K, 0.25) which plan 02-05 explicitly requires; test_readme_triple_mask_uses_registry_ranges ran green in the gate"
  - statement: "The noise floor is computed on the candidate table (dedup first, D-7), never on raw rows grouped ad hoc; the mean is never the candidate aggregate"
    declared_verification: null
    status: verified
    enforcement: "verifier: replicates.noise_floor raises ValueError('noise_floor takes the candidate table …') on a frame lacking <col>_median/_n/_std (asserted in test_d7_… against the rows parquet); noise_floor_on_rows filters then calls build_candidates; build_candidates aggregates median/count/min/max/std — no mean"
  - statement: "No task searches for a filter that yields 88.9 % or treats eps_dc >= n^2 as an independent physics check"
    declared_verification: null
    status: verified
    enforcement: "verifier: the share is pinned at its observed 88.82 with tolerance 0.05 and the README's 88.9 % in the finding note; the report's dielectric section states in prose that the zero dc violations are the identity, not an independent check; expectations.py _IDENTITY_NOTE says 'the 0 is algebra'"
  - statement: "The report never writes a threshold as a decision"
    declared_verification: null
    status: verified
    enforcement: "verifier: grep -c 'threshold =' docs/audit/polyomics-041e5834-validation.md -> 0; 'input to the D-16 gate' appears 3 times; test_feasible_set_on_synthetic_is_labelled_as_d16_input ran green in the gate"
  - statement: "The 2026-09-11 text of docs/research/databases/README.md is not rewritten; the correction is an appended dated note"
    declared_verification: null
    status: verified
    enforcement: "verifier: `git diff 0f4a7d6 HEAD -- docs/research/databases/README.md` -> 21 insertions, 0 deletions; the note is headed `#### Correction (2026-09-22, Phase 2 validator)` and says 'The 2026-09-11 text above is kept as written'"
  - statement: "No push happens before the local seven-step gate prints SUMMARY: 7/7 and the history scan reports zero hits"
    declared_verification: null
    status: verified
    enforcement: "verifier: the pushed tip cb22dc9 equals `git ls-remote origin refs/heads/main`; the verifier's own gate at cb22dc9 -> `SUMMARY: 7/7 steps passed`, `scanned 49 commit(s)`, every pattern class 0 hit(s), `dotenv-path-in-history: 0 hit(s)`; CI run 35648565974 at 39c5345 shows the same on both platforms at 46 commits"
human_verification:
  - test: "Dispatch the `check` workflow at the current main tip (`gh workflow run check --ref main`, then `gh run watch <id> --exit-status`) and read `SUMMARY: 7/7 steps passed` in both the windows-latest and ubuntu-latest job logs"
    expected: "Both matrix jobs conclude success with `104 passed, 12 skipped` and `SUMMARY: 7/7 steps passed`"
    why_human: "The only two-platform CI evidence (run 35648565974) is at 39c5345; commit a161ebf (src/llm4pol/data/sections.py split out of validate.py) and the two docs commits after it were pushed without a workflow_dispatch run. The verifier reproduced 7/7 locally on Windows at cb22dc9 and confirmed the report is byte-identical, but cannot run the Linux job from this workstation and did not trigger a remote run (state mutation). Charter M0 / INVARIANTS R-4 require the gate green on both platforms; the owner should either dispatch the run or accept the local evidence for a pure file-move refactor."
---

# Phase 2: Data Foundation Verification Report

**Phase Goal:** PolyOmics `general_polymers` is pinned at one Hugging Face revision, loaded into one parquet snapshot, identified per candidate, and validated by a report that is the authority for every number cited later — charter §13 M1 (`docs/MASTER-PLAN.md`). Freezes: candidate definition, property registry, snapshot identifier (charter §7).
**Verified:** 2026-09-21T20:26:40Z (2026-09-22 05:26 KST) at HEAD `cb22dc9` (= `origin/main`)
**Status:** passed — every must-have verified; the one evidence item (two-platform CI at the current tip) was closed by the orchestrator, see below
**Re-verification:** No — initial verification

Every number and status below was reproduced by the verifier in its own process on this workstation (Windows, `pixi` env, `PYTHONPATH=src`) or by a live `gh` query. Nothing is taken from the SUMMARY or EVIDENCE files on trust; where they are cited it is because the verifier re-ran the command and got the same output. Where the validator's own code could be circular, the headline numbers were recomputed with plain pandas on the raw CSV outside `llm4pol` (Behavioral Spot-Checks, row "independent recomputation").

## Charter §13 M1 exit criteria (ROADMAP Phase 2 success criteria 1–5)

| M1 exit criterion | Reproduced by | Result |
|---|---|---|
| **(1)** pinned-revision files sha256 = manifest | `sha256sum` of the two files under `data/raw/polyomics/041e5834ea1a48682fae12dc39ccd723bcd4f771/` -> `71e955ac…350213` (196,910,783 B) and `c2340252…6cc13` (15,532 B), byte-equal to the two `data/MANIFEST-open.sha256` lines; `# revision: 041e5834ea1a48682fae12dc39ccd723bcd4f771` header equals `snapshot.POLYOMICS_REVISION`; `python -m llm4pol.data fetch` -> `verified …csv size=196910783 sha256=71e955ac1e90…`, `verified README.md size=15532 sha256=c2340252a720…`, `snapshot: polyomics:general_polymers@041e5834`, exit 0, no download (both files present; `fetch` calls the downloader only when `path.is_file()` is false — `test_fetch_verifies_existing_files_and_never_calls_the_downloader` PASSED by name) | REPRODUCED |
| **(2)** row count, unique units, 43,561, Maxwell 88.9 %, dc violation 0 — reproduced or difference documented | `python -m llm4pol.data validate` -> `source_rows 95,335 reproduced`, `source_columns 259 reproduced`, `unique_smiles_list 78,379 reproduced`, `readme_triple_all_rows 43,561 reproduced` (TC non-null ∧ ε_dc ∈ [1, 20] ∧ Tg ∈ [100, 900] K, bounds read from the registry), `readme_triple_in_scope 43,560`, `triple_check_tc_all_rows 42,733 reproduced`, `candidate_triple_filter_then_median 40,212 reproduced`; `static_maxwell_violations_triple 38,693 reproduced`, `static_maxwell_violation_pct_triple 88.82 documented` (README 88.9 %; 38,693/43,561 = 88.8249 % — verifier's independent pandas run gives the same fraction, so RESEARCH F-13's 88.83 was a rounding slip, as 02-05-SUMMARY records); `dc_maxwell_violations 0 reproduced` with `dc_identity_max_residual 5.7e-07 documented` (< 1e-5; independent run: 5.687e-7 on 93,488 rows); Tg window 56,064 / 52,753 / 3,311 and `tg_rmse` ladder 36,592 / 42,232 / 43,316 / 43,521 / 43,545 all `reproduced`, no cut applied; `VALIDATION: 49 reproduced, 38 documented, 0 failed -> exit 0` | REPRODUCED |
| **(3)** 95,335 vs 73,045 resolved | `card_count_73045: documented … not reproducible from any column`; report `## Source shape` prose plus the table `Counts the dataset card's 73,045 could have meant` (78,379 / 78,373 / 95,335 / 95,335 / 78,336); independent check: no column of the CSV has 73,045 unique values | REPRODUCED |
| **(4)** replicate structure and TC·ε·Tg noise floor | report `## Replicate structure and noise floor`: 78,676 candidates, `replicate_multi_row_candidates 12,983 reproduced`, `replicate_max_rows 17 reproduced`, size histogram, same-version 1,887 / cross-version 11,096 (`documented`, tol 10); noise floor on in-scope rows TC 0.0369, ε_dc 0.0084, Tg 0.0577 / 30.21 K, density 0.0034 and on README-triple rows TC 0.0431, ε_dc 0.0112, Tg 0.0540 — all `documented` within tolerance; every table header carries `population`; replicate-vs-tacticity: `multi_tacticity_smiles_with_unknown 303`, `…without_unknown 2`, `…unknown_twins 301` in `## Scope exclusions and identity` | REPRODUCED |
| **(5)** feasible-set size under the development defaults, as D-16 input | `eps_q25_candidates 2.6524 documented`, `feasible_candidates_dev_defaults 6,793 reproduced`, `feasible_pct_dev_defaults 16.89 documented` (of 40,212 candidates), row-level 7,317 under the row Q25; section title `## Feasible set under the development defaults (input to the D-16 gate)`, closing sentence "nothing here is a decision"; `grep -c 'threshold ='` on the report -> 0 | REPRODUCED |
| **(6)** D-7..D-10 and A-7 promoted to tests in the gate | `pytest --collect-only -o addopts=""` -> 116 tests (= the gate's `116 passed`); every test named in an INVARIANTS.md guard cell is in that collection: `test_d7_candidate_table_dedups_replicates_before_any_metric`, `test_d8_no_row_level_split_code_under_llm4pol_data`, `test_d9_report_states_noise_floor_per_property_with_population`, `test_d10_every_count_table_in_report_names_its_population`, `test_a7_validator_and_loader_never_serve_static_dielectric_const`, `test_a7_static_dielectric_const_is_rejected_by_the_registry_schema`, `test_load_registry_rejects_an_instance_with_the_barred_key`; the test bodies assert the invariant (unique ids + `ValueError` on raw rows for D-7; AST scan for sklearn/split identifiers + the import-linter contract for D-8; two noise tables with candidate populations for D-9; every table header has a non-empty `population` cell incl. the committed report for D-10; the barred column absent from `PROPERTY_COLUMNS`, the registry and every property table for A-7); INVARIANTS.md D-7..D-10 cells and the new A-7 row name those tests; commits `10acb31`, `e355015` add loader code and the guard in the same change | REPRODUCED |

## Goal Achievement

### Observable Truths

Truth numbering: R = ROADMAP success criterion, P{plan}.{n} = PLAN frontmatter must-have.

| # | Truth | Status | Evidence |
|---|---|---|---|
| R1 | Every pinned file matches `data/MANIFEST-open.sha256` by sha256 and size | ✓ VERIFIED | M1 (1) above |
| R2 | Report reproduces or documents row count, unique units, 43,561 with the tg_rmse / 100–900 K counts, 88.9 %, dc 0, and resolves 73,045 | ✓ VERIFIED | M1 (2)–(3) above |
| R3 | Report records replicate structure (rows per candidate, replicate vs tacticity) and TC/ε/Tg noise floor | ✓ VERIFIED | M1 (4) above |
| R4 | Report states the feasible-set size under ε ≤ Q25, Tg ≥ 400 K as a D-16 input without fixing D-16 | ✓ VERIFIED | M1 (5) above |
| R5 | D-7..D-10 and A-7 run as tests inside the gate, added with the loader | ✓ VERIFIED | M1 (6) above |
| P1.1 | `fetch` verifies the two files without calling `hf_hub_download`, prints `verified <name>`, exits 0; downloads only absent files | ✓ VERIFIED | CLI run above; `test_fetch_verifies_existing_files_and_never_calls_the_downloader`, `test_fetch_downloads_a_missing_file_then_verifies_it`, `test_fetch_returns_1_on_sha256_mismatch_and_names_the_file` (asserts `calls == []`) PASSED by name |
| P1.2 | `load` writes `polyomics-041e5834.parquet` (95,332 rows, all source columns + 3 identity) and `candidates-041e5834.parquet` (78,676 rows) with metadata `llm4pol.snapshot = polyomics:general_polymers@041e5834` | ✓ VERIFIED | `pq.read_metadata`: rows parquet 95,332 rows × 262 columns (259 + `candidate_id`, `canonical_psmiles`, `row_index`); candidates 78,676 rows; both carry `llm4pol.snapshot=polyomics:general_polymers@041e5834`, `llm4pol.revision`, `llm4pol.source_sha256=71e955ac…`; declared types `string`/`bool`/`int64`/`double` (not `large_string`) |
| P1.3 | `validate` writes the report with `source_rows 95,335`, `source_columns 259`, `unique_smiles_list 78,379` as `reproduce`/`reproduced`, every count naming its population, exit 0 on the pinned file and 1 when numbers differ | ✓ VERIFIED | validate run above; `test_cli_validate_exits_1_on_synthetic_root_because_expected_values_are_polyomics` PASSED by name (exit 1 path); `report.exit_code` returns 1 on any FAILED/MISSING |
| P1.4 | Seven-step gate green under `mypy --strict`; pyyaml + types-pyyaml declared and locked; pandas/pyarrow/jsonschema overrides; `typings/rdkit` on `mypy_path` | ✓ VERIFIED | verifier's gate: `mypy … Success: no issues found in 15 source files`, `SUMMARY: 7/7 steps passed`; `env/pixi.toml` lines 37, 45; `env/pixi.lock` carries `pyyaml-6.0.3` (win-64, linux-64) and `types-pyyaml-6.0.12.20260906` (noarch); `pyproject.toml` `mypy_path = ["src", "typings"]`, override on `pandas.*`, `pyarrow.*`, `jsonschema.*`; `typings/rdkit/Chem/__init__.pyi` declares `MolFromSmiles`/`MolToSmiles` |
| P1.5 | First import-linter contract: `llm4pol.data` forbidden from `evaluate`/`run`/`loop`/`llm`/`sklearn`, reported KEPT | ✓ VERIFIED | gate output `Contracts: 1 kept, 0 broken.`; `pyproject.toml` lines 53–57 |
| P1.6 | Logic tests run on the 14-row synthetic fixture; real-file tests skip with a reason when the pinned dir is absent | ✓ VERIFIED | `tests/conftest.py` `_CORE` has 14 invented rows; `real_csv` fixture `pytest.skip("pinned PolyOmics file absent at … (never committed; run python -m llm4pol.data fetch)")`; CI logs on both platforms: `104 passed, 12 skipped` (9 real-file + 2 invariants + 1 PoLyInfo manifest); local: `116 passed` |
| P1.7 | D-7 and D-10 promoted in the same change; INVARIANTS.md guard cells name the tests | ✓ VERIFIED | M1 (6); INVARIANTS.md D-7 and D-10 rows quote the test node ids; tests collected |
| P2.1 | Registry instance validates against the draft 2020-12 schema and declares exactly the nine keys with column/unit/unit_status/condition/role/physical_range | ✓ VERIFIED | schema `$schema: draft/2020-12`, `propertyNames.enum` of the nine keys, `minProperties`/`maxProperties` 9, root `additionalProperties: false`; instance read above; gate step `llm4polcheck inventory: 1 entries, 1 instances processed` (validates the instance in the gate) |
| P2.2 | Injecting the barred column into a copy of the instance raises `jsonschema.ValidationError` | ✓ VERIFIED | `test_a7_static_dielectric_const_is_rejected_by_the_registry_schema` PASSED by name |
| P2.3 | Units carry `verified` for eight keys and `unverified` for `r2` (`nm^2`) with a `unit_note` naming both candidates | ✓ VERIFIED | instance: TC `W/(m*K)`, ε_dc `"1"`, tg `K`, rg `angstrom`, ffv `"1"`, sp_ced `MPa`, density `g/cm^3`, refractive_index `"1"` all `verified`; `r2: nm^2, unverified`, note cites Table S3 angstrom^2 vs data-consistent nm^2 (F-25) |
| P2.4 | Registry records `tg_rmse_ladder [0.05, 0.1, 0.2, 0.5, 1.0]` with unit `(g/cm^3)^2`, applies no cut, and `check_tc: true` on the objective | ✓ VERIFIED | instance `tg.filters` and `thermal_conductivity.filters`; report prints 42,733 beside 43,561 |
| P2.5 | Provenance file has one entry per instance leaf, leaf sets equal, classes in the enum, `properties.r2.unit` the only `unresolved` | ✓ VERIFIED | `test_provenance_leaf_paths_equal_registry_leaf_paths` PASSED by name; `test_data_registry.py` (19 tests) green in the gate |
| P2.6 | Every number in the instance is a YAML number | ✓ VERIFIED | all floats carry a decimal point (`0.0`, `2.0`, `1.0`, `20.0`, `100.0`, `900.0`, …); `test_registry_numbers_are_numbers_not_strings` green in the gate |
| P3.1 | `fetch` returns 1 with a `MISMATCH …` line per differing file, checks every entry, 1 on a revision-header mismatch, 2 on a missing manifest or a raising downloader, downloader called only for absent files with exact kwargs | ✓ VERIFIED | `tests/test_data_fetch.py` 11 tests PASSED by name (incl. `…returns_1_on_size_mismatch…`, `…returns_1_when_manifest_revision_differs…`, `…returns_2_when_manifest_is_missing`, `…returns_2_when_downloader_raises`, `…checks_every_file_before_returning`); `fetch.py` `_download` passes `repo_id`, `repo_type="dataset"`, `filename`, `revision`, `local_dir` |
| P3.2 | One manifest parser serves both manifests; `tests/test_manifest.py` imports `parse_manifest` / `sha256_of` from `llm4pol.data.fetch` | ✓ VERIFIED | key-link tool: `tests/test_manifest.py -> src/llm4pol/data/fetch.py` verified; `test_manifest.py` 4 tests collected |
| P3.3 | `canonical_psmiles` merges the two PMMA spellings, keeps stereo and both `*`, returns None for `*C(` and comma-joined lists, is idempotent; `candidate_id("*CC*", None) == d220c5c57c4fae2e` | ✓ VERIFIED | `tests/test_data_identity.py` 7 tests PASSED by name |
| P3.4 | Loader declares only registry/identity/flag columns, keeps pass-through columns, writes `string` not `large_string`, counts second-monomer exclusions before parsing and parse failures after, maps missing tacticity to `unknown`, raises `LoaderError` naming missing columns | ✓ VERIFIED | `schema.py` `DTYPES`/`DECLARED_FIELDS` (no `n_atom`/`mol_weight`); `load.add_identity` order matches; parquet types `string`; `test_data_schema.py` 12 tests green in the gate; independent count: 3 `smiles_2` non-null rows excluded -> 95,332 |
| P3.5 | On the pinned file: 95,332 × 262, 78,373 unique canonical, 78,676 unique ids; candidate `n_rows` sums to 95,332, max 17 | ✓ VERIFIED | parquet metadata + validate: `in_scope_rows 95,332`, `unique_canonical 78,373`, `unique_candidate_ids 78,676`, `replicate_max_rows 17`; `test_real_candidates_have_unique_ids_and_sizes_sum_to_in_scope_rows` green in the gate |
| P4.1 | `scripts/check.py` has a seventh `schema-inventory` step after `import-linter` reading `[tool.llm4polcheck]`, failing on a missing table / schema / zero-match required glob; gate prints `SUMMARY: 7/7 steps passed` | ✓ VERIFIED | gate `Steps: ruff check, ruff format --check, mypy, import-linter, schema-inventory, history-secret-scan, pytest`; `validate_inventory` lines 106–140 implement the three failure modes; `test_check_inventory.py` 7 tests green |
| P4.2 | `load_registry()` returns a typed `Registry` with nine `PropertySpec`s, `snapshot == SNAPSHOT_ID`, columns == `PROPERTY_COLUMNS`, barred key refused with `RegistryError` | ✓ VERIFIED | `registry.py` read above; `test_load_registry_rejects_an_instance_with_the_barred_key` PASSED by name; `test_d9_…` asserts registry key order equals the noise-table order |
| P4.3 | Report carries `## Replicate structure and noise floor` with the F-50/F-52/F-55/F-56 numbers on both populations, every table naming its population | ✓ VERIFIED | M1 (4) |
| P4.4 | D-9 is a gate test named in INVARIANTS.md; the D-7 test is extended, not duplicated | ✓ VERIFIED | one `test_d7_…` definition (line 44) carrying the replicate-structure and `ValueError` assertions; D-9 row names `test_d9_…` |
| P5.1 | Committed report is byte-identical to a fresh run and reproduces the README triple ladder and documents 88.8x %, the identity and 73,045 | ✓ VERIFIED | sha256 of `docs/audit/polyomics-041e5834-validation.md` before and after the verifier's `validate` run: `1f30f0aa…5fd64` both times; `git diff --exit-code -- docs/audit/` -> exit 0; M1 (2)–(3). Note: the plan text says 88.83 %; the committed value is 88.82 %, the correct rounding of 38,693/43,561 (independently recomputed) — a deviation recorded in 02-05-SUMMARY "Decisions Made" and in the report's Finding notes, not silently changed |
| P5.2 | Feasible set 6,793 of 40,212 (16.89 %) under Q25 = 2.6524 ∧ Tg ≥ 400 K, labelled `input to the D-16 gate`, never a decision | ✓ VERIFIED | M1 (5) |
| P5.3 | Tg window 56,064 / 52,753 / 3,311 and the ladder 36,592 / 42,232 / 43,316 / 43,521 / 43,545 on the 43,560 in-scope triple rows, no cut | ✓ VERIFIED | validate findings above; ladder table titled `tg_rmse ladder (no cut applied)`, population `in-scope README-triple rows` |
| P5.4 | D-8, A-7 and the Maxwell test run in the gate; D-10 extended to the committed report; INVARIANTS.md D-8 row and new A-7 row | ✓ VERIFIED | M1 (6); `test_maxwell_identity_holds_on_dielectric_rows` collected; `test_d10_…` reads `snapshot.report_path(REPO_ROOT)` when present |
| P5.5 | The report's Tg section and the summary flag the DATA-09 vs R-2 wording discrepancy without resolving it | ✓ VERIFIED | report line 206 `Wording discrepancy raised for the owner: REQUIREMENTS.md DATA-09 reads "filtered by tg_rmse"; … Nothing is resolved here.`; 02-05-SUMMARY "Owner questions (flagged, not resolved)" item 1 |
| P5.6 | `docs/research/databases/README.md` carries a dated correction note pointing at the report without rewriting the 2026-09-11 text | ✓ VERIFIED | `#### Correction (2026-09-22, Phase 2 validator)` at line 106; `git diff 0f4a7d6 HEAD` on that file: +21 / −0 |
| P5.7 | Seven-step gate green locally and in a `workflow_dispatch` CI run on both platforms; `02-EVIDENCE.md` pairs each M1 criterion with command and output | ✓ VERIFIED (at 39c5345) — see Human Verification | local: `SUMMARY: 7/7 steps passed`, `116 passed`, exit 0 at cb22dc9; `gh run view 35648565974` -> `conclusion: success`, `event: workflow_dispatch`, `headSha: 39c5345…`, jobs `check (windows-latest): success`, `check (ubuntu-latest): success`, both logs `SUMMARY: 7/7 steps passed`, `104 passed, 12 skipped`, `llm4polcheck inventory: 1 entries`; 39c5345 is an ancestor of HEAD; `02-EVIDENCE.md` sections (1)–(6) each quote a command and verbatim output that the verifier re-ran with identical results. The three commits after 39c5345 (aaef76a docs, a161ebf src refactor, cb22dc9 docs) have no CI run |

**Score:** 26/26 truths verified (5 roadmap SCs + 21 plan must-haves after deduplication; 0 present-behavior-unverified; 0 overrides)

### Required Artifacts

`gsd query verify.artifacts` on the five plans: 15/15, 4/4, 5/5, 8/9, 8/8. The single tool miss is a pattern check, not a missing artifact:

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `src/llm4pol/data/snapshot.py` | revision constant, `SNAPSHOT_ID`, path helpers | ✓ VERIFIED | 62 lines; imported by every module |
| `src/llm4pol/data/fetch.py` | `parse_manifest`, `sha256_of`, `verify_file`, `fetch` with exit 0/1/2 | ✓ VERIFIED | 193 lines; wired from `__main__`, `load`, `validate`, `tests/test_manifest.py` |
| `src/llm4pol/data/identity.py` | pure `canonical_psmiles`, `candidate_id`, `normalise_tacticity` | ✓ VERIFIED | 52 lines; wired from `load`, `filters` |
| `src/llm4pol/data/schema.py` | `DTYPES`, `PROPERTY_COLUMNS`, `DECLARED_FIELDS`, `cast_declared` | ✓ VERIFIED | 96 lines; wired from `load` |
| `src/llm4pol/data/load.py` | `read_source`, `add_identity`, `build_candidates`, `load` | ✓ VERIFIED | 172 lines; wired from `__main__`, `validate`, `filters`, `replicates` |
| `src/llm4pol/data/report.py` | `Expected`, `Finding`, `CountTable` (refuses no-population header), `render_markdown`, `exit_code` | ✓ VERIFIED | 218 lines; wired from `validate`, `sections`, `replicates` |
| `src/llm4pol/data/validate.py` | `run()`, all sections, `EXPECTED_POLYOMICS` | ✓ VERIFIED | 519 lines; the literal `Replicate structure and noise floor` moved to `replicates.replicate_section`, which `validate._build_report` calls (tool reported "Missing pattern"; the section is rendered — see report line 242) |
| `src/llm4pol/data/registry.py` | `load_registry`, `Registry`, `PropertySpec`, `RegistryError` | ✓ VERIFIED | 121 lines; wired from `filters`, `replicates`, `validate`, tests |
| `src/llm4pol/data/filters.py` | registry-fed masks, ladders, feasible set, `DEV_DEFAULT_*` | ✓ VERIFIED | 400 lines; wired from `validate`, `sections`, `replicates` |
| `src/llm4pol/data/replicates.py` | `replicate_structure`, `noise_floor`, `noise_floor_on_rows`, `same_version_split`, `replicate_section` | ✓ VERIFIED | 236 lines; wired from `validate`, `expectations` |
| `src/llm4pol/data/expectations.py`, `sections.py` | scope additions (file-size ceiling) | ✓ VERIFIED | 251 / 393 lines; wired from `validate` |
| `src/llm4pol/data/__main__.py` | argparse `fetch | load | validate --root`, exit 0/1/2 | ✓ VERIFIED | 61 lines; `python -m llm4pol.data` runs (CLI runs above) |
| `data/MANIFEST-open.sha256` | two entries, `# revision:` header, HF URL | ✓ VERIFIED | content shown above |
| `typings/rdkit/{__init__,RDLogger,Chem/__init__}.pyi` | stub shadowing the broken bundled one | ✓ VERIFIED | mypy strict green |
| `protocol/schemas/property-registry.json`, `protocol/property-registry_v1.yaml`, `protocol/property-registry_v1.provenance.yaml` | the triad | ✓ VERIFIED | schema validated in the gate step; provenance leaf equality test green |
| `scripts/check.py` | `validate_inventory`, `step_schema_inventory` in `STEPS` after `import-linter` | ✓ VERIFIED | gate output |
| `pyproject.toml` | `[tool.llm4polcheck]`, import-linter contract, mypy overrides | ✓ VERIFIED | lines 33–73 |
| `tests/conftest.py`, `tests/test_data_*.py`, `tests/test_check_inventory.py`, `tests/test_manifest.py` | synthetic fixture + 90 new tests | ✓ VERIFIED | 116 collected; no skip/xfail markers on requirement tests (only the two designed `pytest.skip` calls for absent data files) |
| `docs/audit/polyomics-041e5834-validation.md` | the committed number authority | ✓ VERIFIED | 444 lines, 11 `##` sections, byte-identical to a fresh run |
| `docs/governance/INVARIANTS.md` | D-7..D-10 guard cells + A-7 row naming real tests | ✓ VERIFIED | all 8 named tests collected |
| `docs/research/databases/README.md`, `docs/audit/README.md` | correction note; index row | ✓ VERIFIED | shown above |
| `.planning/phases/02-data-foundation/02-EVIDENCE.md` | command + verbatim output per M1 criterion, CI run id and both job conclusions | ✓ VERIFIED | contains `CI run id: 35648565974`, `check (ubuntu-latest): success`; every quoted output re-run by the verifier matched |

### Key Link Verification

`gsd query verify.key-links`: 8/8, 2/2, 3/3, 5/5, 5/5 — all 23 declared links WIRED. Spot-read: `__main__` dispatches to `fetch.fetch` / `load.load` / `validate.run` and maps `LoaderError`/`OSError`/`ValueError` to exit 2; `validate._read_processed` refuses a parquet whose `llm4pol.source_sha256` differs from the manifest (re-load guard); `filters` reads every bound from `PropertySpec`; `registry.load_registry` validates with `jsonschema.validate` before typing; INVARIANTS.md cells name the collected test node ids.

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|---|---|---|---|---|
| `validate.run` findings | `observed[...]` | `read_source(csv)` + `pd.read_parquet(rows/candidates)` -> `filters.*` / `replicates.*` | Yes — 87 findings, values match the verifier's independent pandas recomputation | ✓ FLOWING |
| `load.load` parquets | `rows`, `candidates` | `pd.read_csv(pinned CSV, dtype=DTYPES)` -> RDKit -> `groupby(candidate_id)` | Yes — 95,332 / 78,676 rows on disk with metadata | ✓ FLOWING |
| `fetch.fetch` verdict | `checks` | streamed sha256 of the on-disk bytes vs manifest | Yes — mismatch/size/revision paths tested | ✓ FLOWING |
| Report tables | `CountTable.rows` | the same `observed` dict and registry | Yes — no hardcoded table rows; synthetic root produces different numbers (`test_cli_validate_exits_1_on_synthetic_root…`) | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| Seven-step gate | `pixi run --manifest-path env/pixi.toml check` (once, at cb22dc9) | `Steps: … schema-inventory …`, `Contracts: 1 kept, 0 broken.`, `llm4polcheck inventory: 1 entries, 1 instances processed`, `scanned 49 commit(s)`, all 10 pattern classes `0 hit(s)`, `dotenv-path-in-history: 0 hit(s)`, `116 passed in 42.37s`, `SUMMARY: 7/7 steps passed`, exit 0 | ✓ PASS |
| fetch verify-only | `PYTHONPATH=src pixi run … python -m llm4pol.data fetch` | two `verified` lines + `snapshot: polyomics:general_polymers@041e5834`, exit 0 | ✓ PASS |
| validate | `PYTHONPATH=src pixi run … python -m llm4pol.data validate` | `VALIDATION: 49 reproduced, 38 documented, 0 failed -> exit 0`; 0 lines matching FAILED/MISSING | ✓ PASS |
| committed report byte-identical | `sha256sum` before/after + `git diff --exit-code -- docs/audit/` | `1f30f0aa…` both times; diff exit 0 | ✓ PASS |
| independent recomputation (outside `llm4pol`) | plain pandas on the raw CSV | `(95335, 259)`; unique `smiles_list` 78379; triple 43561; ∧ `check_tc` 42733; static < n² on triple 38693/43561 = 88.8249 %; dc identity max residual 5.687e-7 (93,488 rows); dc violations 0; tg 56064/52753/3311; `smiles_2` non-null 3; no column with 73,045 uniques; (smiles_list, tacticity→unknown) groups 78,682, 12,984 multi, max 17 (CONTEXT table values) | ✓ PASS |
| named tests (fetch paths, CLI exit codes, identity vectors, A-7 schema rejection, provenance leaf equality) | `pytest -o addopts="" -v tests/test_data_fetch.py tests/test_data_cli.py tests/test_data_identity.py tests/test_data_registry.py::test_a7_… ::test_load_registry_rejects_… ::test_provenance_leaf_paths_…` | `25 passed in 0.84s` | ✓ PASS |
| guard tests exist in the gate | `pytest --collect-only -o addopts="" -q tests/` | `116 tests collected`; all 8 INVARIANTS.md node ids present | ✓ PASS |
| CI two-platform evidence | `gh run view 35648565974 --json …`; `--log \| grep SUMMARY` | `success` / `workflow_dispatch` / `39c5345…`; both jobs `SUMMARY: 7/7 steps passed`, `104 passed, 12 skipped` | ✓ PASS (at 39c5345; not at cb22dc9 — see Human Verification) |
| no data file tracked; report aggregates-only | `git ls-files data/`; three greps on the report | only README + two manifests; SMILES-like 0, bare 16-hex 0, UUID 0, `threshold =` 0 | ✓ PASS |
| Phase 1 regression | dotenv name assembled at runtime: `git ls-files \| grep` -> none tracked, `.env.example` tracked; `huggingface_hub = ">=1.32.0,<2"` in `env/pixi.toml`; `test_governance.py` 9 tests collected and green; gate still runs `history-secret-scan` | all hold | ✓ PASS |

Note on invocation: `pixi run --manifest-path env/pixi.toml python -m llm4pol.data …` without `PYTHONPATH=src` fails with `No module named 'llm4pol'` (only the `check` tasks set `PYTHONPATH`); EVIDENCE.md states the convention, and the verifier used it. Recorded as ℹ️ below.

### Probe Execution

No `scripts/*/tests/probe-*.sh` exist and no plan declares a probe. The runnable checks above (gate, CLI, named tests) are the phase's probes. N/A.

### Requirements Coverage

Union of PLAN `requirements:` fields: 02-01 [01,02,04,05,10], 02-02 [03,09], 02-03 [01,02,04], 02-04 [03,05,07,10], 02-05 [06,08,09,10] = DATA-01..DATA-10, no orphan (REQUIREMENTS.md traceability rows 113–122 map exactly these ten to Phase 2, all `Complete`, checkboxes `[x]`).

| Requirement | Source Plan | Description | Status | Evidence |
|---|---|---|---|---|
| DATA-01 | 02-01, 02-03 | fetch at a pinned HF revision; sha256 + size vs `data/MANIFEST-open.sha256` | ✓ SATISFIED | M1 (1); P1.1, P3.1 |
| DATA-02 | 02-01, 02-03 | one parquet `polyomics-<rev>.parquet`, declared pyarrow schema, snapshot id | ✓ SATISFIED | P1.2, P3.4, P3.5 |
| DATA-03 | 02-02, 02-04 | registry declares key/column/unit/condition for the nine keys; barred column absent | ✓ SATISFIED | P2.1–P2.4, P4.2; A-7 greps 0/0/0 |
| DATA-04 | 02-01, 02-03 | `candidate_id = sha256(canonical_psmiles + "\|" + tacticity)[:16]`, stereo-aware | ✓ SATISFIED | `identity.py`; P3.3 (`d220c5c57c4fae2e`) |
| DATA-05 | 02-01, 02-04 | replicates grouped by id; median with count and spread | ✓ SATISFIED | `build_candidates` median/n/min/max/std; P4.3 |
| DATA-06 | 02-05 | report reproduces/documents row count, unique units, 43,561, 88.9 %, dc 0; resolves 73,045 | ✓ SATISFIED | M1 (2)–(3) |
| DATA-07 | 02-04 | replicate structure and TC/ε/Tg noise floor | ✓ SATISFIED | M1 (4) |
| DATA-08 | 02-05 | feasible-set size under ε ≤ Q25, Tg ≥ 400 K | ✓ SATISFIED | M1 (5) |
| DATA-09 | 02-02, 02-05 | Tg rows filtered by `tg_rmse` and to 100–900 K; counts recorded | ✓ SATISFIED (counts) — wording flag open | window and every ladder rung recorded; no `tg_rmse` cut applied per CONTEXT R-2; the discrepancy with the REQUIREMENTS wording is flagged for the owner in the report and the summary, not resolved (P5.5) |
| DATA-10 | 02-01, 02-04, 02-05 | D-7..D-10 and A-7 promoted to tests in the same change as the loader | ✓ SATISFIED | M1 (6) |

### Decision Coverage

`gsd query check.decision-coverage-verify` returned `could-not-parse` (the CONTEXT decisions block uses `### D-01 …` headings). Checked by hand — 16/16 honoured, none abandoned:

| Decision | Honoured by |
|---|---|
| D-01 fetch/pin | `fetch.py` `_download` kwargs; `snapshot.POLYOMICS_REVISION` in one place; manifest header + HF URL; `.cache/` ignored via `data/raw/` |
| D-02 one parquet, declared schema | `schema.DECLARED_FIELDS` + `cast_declared`; 262 columns kept; names unchanged |
| D-03 identity | `identity.canonical_psmiles` (`isomericSmiles=True`, `canonical=True`); parse failures counted (0); second-monomer rows excluded (3); NaN tacticity -> `unknown`; `sha256[:16]` |
| D-04 replicates | candidate table median/n/min/max/std (ddof=1); noise floor = median relative and absolute spread over n ≥ 2 |
| D-05 registry as protocol | triad + keys + unit_status + condition + role + physical_range + filters; barred column asserted absent |
| D-06 schema inventory | `[tool.llm4polcheck]` + `schema-inventory` step |
| D-07 report is the number authority | all listed sections present in the stated order; every count names its population |
| D-08 guards promoted | D-7, D-8, D-9, D-10, A-7, Maxwell tests; INVARIANTS.md updated |
| D-09 tests without data | 14-row fixture; real-file tests skip with reason; CI 12 skipped |
| D-10 CLI | `fetch | load | validate --root`; no shell; exit 0/1/2 |
| R-1 unknown tacticity | separate candidate; both counts printed (303 with unknown / 2 without; 301 unknown twins); raised for the owner in 02-05-SUMMARY |
| R-2 populations | 43,561 and 42,733 side by side; ladder recorded; no cut |
| R-3 narrative correction | dielectric section states the identity; dated note in the research README; A-7 stands |
| R-4 units | registry as decided (sp_ced MPa verified; r2 unverified with note) |
| R-5 exit codes | `reproduce` exact / `documented` with tolerance (88.82 ± 0.05; residual tol 1e-5); any other drift -> FAILED -> exit 1 |
| R-6 environment | pyyaml + types-pyyaml in `env/pixi.toml` and `env/pixi.lock` |

### Owner questions — recorded, not resolved (as required)

These are inputs to Phase 3, carried in `02-05-SUMMARY.md` "Owner questions (flagged, not resolved)" and in the report itself. The verifier confirms none was silently resolved in code or docs:

1. **DATA-09 wording vs CONTEXT R-2** — the report's Tg section carries the verbatim flag; no `tg_rmse` cut is applied; counts satisfy either reading.
2. **303 `unknown`-tacticity twins (R-1)** — kept as separate candidates; the report prints 303 / 2 / 301; nothing folded.
3. **43,561 (README) vs 42,733 (`check_tc == True`)** — both printed; the evaluator's population is left to Phase 3.
4. **88.83 % (RESEARCH F-13) vs 88.82 % (correct rounding)** — the report and correction note use 88.82; the research file is unedited.

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
|---|---|---|---|---|---|---|
| tests/test_data_fetch.py | DATA-01 | 11 | 0 | no | value + behavioural (exit codes, downloader call list) | OK |
| tests/test_data_cli.py | DATA-01/02/06 | 4 | 0 | no | behavioural (round trip, exit codes) | OK |
| tests/test_data_identity.py | DATA-04 | 7 | 0 | no — vectors from RESEARCH/RDKit, hash from hashlib | value | OK |
| tests/test_data_schema.py | DATA-02 | 12 | 0 | no | value (pyarrow types) | OK |
| tests/test_data_registry.py | DATA-03/09 | 19 | 0 | no | value + negative (ValidationError) | OK |
| tests/test_check_inventory.py | DATA-03 (D-06) | 7 | 0 | no | behavioural (step failures) | OK |
| tests/test_data_invariants.py | DATA-05/07/08/10 | 21 | 2 in CI (real file) | no | value + behavioural (ValueError on raw rows, AST scan, table structure) | OK |
| tests/test_data_real_file.py | DATA-01/02/04/06/08/09 | 9 | 9 in CI, 0 locally | expected values come from the README (external) and RESEARCH measurements, independently reconfirmed by the verifier with plain pandas — not from the system under test | value | OK |

**Disabled tests on requirements:** 0. **Circular patterns:** 0. **Insufficient assertions:** 0.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| scripts/check.py | 201 | comment "The [tool.importlinter] section currently declares zero contracts" — stale since 02-01 added the first contract (the gate prints `Contracts: 1 kept`) | ℹ️ Info | misleading comment only; no behaviour |
| src/llm4pol/__init__.py | 3–5 | docstring "Pre-charter scaffold … contains nothing but its version until MASTER-PLAN is approved" — stale now that the charter is Approved and `llm4pol.data` exists (file not modified by this phase) | ℹ️ Info | documentation drift; `tests/test_governance.py` still green |
| env/pixi.toml | tasks | no `python` task carries `PYTHONPATH=src`, so `pixi run … python -m llm4pol.data …` fails without the env var the EVIDENCE convention assumes | ℹ️ Info | reproducibility ergonomics; the documented convention works |
| src/llm4pol/data/identity.py | 41, 44 | `return None` | not a stub | documented parse-failure path, tested |

No `TBD`/`FIXME`/`XXX`/`TODO`/`HACK` markers, no `pytest.mark.skip`/`xfail`, no placeholder text in any file modified by the phase. Files stay under the 800-line ceiling (largest: `validate.py` 519, `test_data_invariants.py` 625).

### Human Verification Required

None remaining. The single item below was procedural and was closed by the orchestrator on 2026-09-22 (no owner judgement involved):

#### 1. Two-platform CI at the current tip — RESOLVED

**Resolution:** `gh workflow run check --ref main` dispatched at `cb22dc9` → run 35651579337 (`workflow_dispatch`): `check (windows-latest): success`, `check (ubuntu-latest): success`; `grep -c "SUMMARY: 7/7 steps passed"` over the run log = 2.

Original item as written by the verifier:

**Test:** `gh workflow run check --ref main`, then `gh run watch <id> --exit-status` and `gh run view <id> --log | grep -E "SUMMARY:|passed"`.
**Expected:** both `check (windows-latest)` and `check (ubuntu-latest)` conclude `success` with `104 passed, 12 skipped` and `SUMMARY: 7/7 steps passed`.
**Why human:** the only two-platform run (35648565974) is at `39c5345`; `a161ebf` (pure move of section builders into `sections.py`) and two docs commits were pushed afterwards with no dispatch (push events create no run in this repository — Phase 1 D-05 convention). The verifier reproduced 7/7 locally on Windows at `cb22dc9` and confirmed the report is byte-identical, but cannot run the Linux job here and deliberately did not trigger a remote run. Charter M0 / INVARIANTS R-4 name both platforms; the owner can dispatch the run (about one minute) or accept the local evidence for a file-move refactor.

### Gaps Summary

No gaps. Every charter §13 M1 exit criterion (1)–(6), every ROADMAP success criterion and every PLAN must-have was reproduced in the verifier's own process; the headline numbers were additionally recomputed outside the package and agree (including 88.8249 %, which settles the 88.82 / 88.83 question in favour of the committed report). The phase freezes hold: candidate definition in `identity.py`, registry triad validated in the gate, snapshot id `polyomics:general_polymers@041e5834` in the parquets and the report. No data file is tracked and the report is aggregates-only. The owner questions are recorded, not resolved. The single open item is procedural evidence (CI at the tip), surfaced above rather than assumed.

---

_Verified: 2026-09-21T20:26:40Z_
_Verifier: Claude (gsd-verifier)_
