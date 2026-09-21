# Invariants

Rules that must hold. Each one names its **guard**: the test, schema or CI check that enforces
it. An invariant with guard "prose" is not yet enforced and is a candidate for promotion.

The data invariants below are derived from `docs/audit/DATA-FOUNDATION-REPORT.md` section 4.
They are architecture-neutral: they constrain the data, not the design. Architecture
invariants A-1..A-7 are declared in `docs/MASTER-PLAN.md` §4 with the milestone that adds
each guard; they are prose until that milestone. D-1..D-6 apply to the PoLyInfo loader
(first written at M8); D-7..D-10 apply to every table, PolyOmics included (guard at M1).

## Repository and process

| ID | Invariant | Guard |
|---|---|---|
| R-1 | No PoLyInfo-derived data file is ever committed | `.gitignore` plus `tests/test_manifest.py` |
| R-2 | Any file present in `data/raw/` matches `data/MANIFEST.sha256` in sha256 and byte size | `tests/test_manifest.py` |
| R-3 | No secret value is printed, logged or committed | `.gitignore` dotenv rules; `scripts/history_secret_scan.py` (pattern classes over `git rev-list --all` plus the dotenv-path check over `git log --all --name-only`), run as the `history-secret-scan` step of `scripts/check.py` (self-test, then scan) and in CI on both platforms; `tests/test_history_secret_scan.py` |
| R-4 | The check gate passes before any commit | `scripts/check.py`, CI on two platforms |
| R-5 | `src/llm4pol/` contains production code only while `docs/MASTER-PLAN.md` declares `Status: Approved` (ADR-0005) | `tests/test_governance.py::test_charter_status_gates_production_code` |

## Data — enforced by the loader and validator once they exist

| ID | Invariant | Guard |
|---|---|---|
| D-1 | The copolymer CSV is read as UTF-8 with replacement, never as cp949. A cp949 read silently alters 16 cells in 15 rows | prose |
| D-2 | `composition_i` is bound to `component_i`, never to `smiles_i`. Position-based pairing is wrong for about 30 percent of resolvable rows and inverts the sign of the composition effect | prose |
| D-3 | Rows whose component-to-SMILES binding is undetermined are excluded, not guessed | prose |
| D-4 | Temperatures are stored in one unit throughout. The XLSX is Kelvin, the CSV is degrees Celsius | prose |
| D-5 | Electrical values are parsed by stripping the glued unit with an anchored expression, never by a greedy number match | prose |
| D-6 | Structural identity uses a stereo-aware key that does not merge topologically different polymers. The naive ring-closing key produces false merges | prose |
| D-7 | Rows that differ only in `sample_id` are deduplicated before any split or metric | `llm4pol.data.load.build_candidates` groups by `candidate_id` before any metric (candidate table `data/processed/candidates-<rev>.parquet`, read by the validator); `tests/test_data_invariants.py::test_d7_candidate_table_dedups_replicates_before_any_metric` |
| D-8 | Splits are grouped by polymer identity, never random at row level. Replicates would otherwise leak | no split code exists in `llm4pol.data`; `[tool.importlinter]` contract forbidding `sklearn` from `llm4pol.data` (`import-linter` step); `tests/test_data_invariants.py::test_d8_no_row_level_split_code_under_llm4pol_data`; sampling in later phases is at candidate level after `build_candidates` (charter §9) |
| D-9 | A reported effect smaller than the measured replicate noise floor is not reported as an effect | the `Replicate structure and noise floor` section of `docs/audit/polyomics-041e5834-validation.md` (per-property median relative and absolute spread over candidates with n ≥ 2, on the in-scope rows and on the README-triple rows); `tests/test_data_invariants.py::test_d9_report_states_noise_floor_per_property_with_population` |
| D-10 | Every reported count states the population it is drawn from. Matched-set sizes are recorded alongside every aggregate | `llm4pol.data.report.CountTable` refuses a table without a `population` column; every finding line of `python -m llm4pol.data validate` names its population; `tests/test_data_invariants.py::test_d10_every_count_table_in_report_names_its_population` |

## Architecture (charter §4) — guards landed

Rows are added here when a charter §4 guard lands; the charter text is not edited. Test names in
this table carry the barred column's name by design (so the row, the evidence file and `-v` output
can cite them) while every grep gate on test bodies excludes `def test_` lines.

| ID | Invariant | Guard |
|---|---|---|
| A-7 | The uncorrected static permittivity column is not a registry property; `dielectric_const_dc` only (ADR-0004) | `protocol/schemas/property-registry.json` propertyNames enum; `scripts/check.py` schema-inventory step; `tests/test_data_registry.py::test_a7_static_dielectric_const_is_rejected_by_the_registry_schema`; `tests/test_data_registry.py::test_load_registry_rejects_an_instance_with_the_barred_key`; `tests/test_data_invariants.py::test_a7_validator_and_loader_never_serve_static_dielectric_const` |

## Promotion policy

An invariant is promoted from prose to a guard as soon as the code it constrains exists. A
change that adds code touching an unguarded invariant adds the guard in the same change.
