---
phase: 02-data-foundation
plan: 01
subsystem: data
tags: [huggingface-hub, pandas, pyarrow, parquet, rdkit, mypy, import-linter, pytest]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: six-step gate (scripts/check.py), tests/conftest.py path setup, data/MANIFEST.sha256 line format, env/pixi.toml locked environment with huggingface_hub
provides:
  - "`python -m llm4pol.data fetch | load | validate` with exit codes 0 / 1 / 2 (D-10)"
  - "`data/MANIFEST-open.sha256` pinning the two PolyOmics files at revision 041e5834 by sha256 and byte size (D-01)"
  - "`llm4pol.data.snapshot` (POLYOMICS_REVISION, SNAPSHOT_ID `polyomics:general_polymers@041e5834`, path helpers)"
  - "`llm4pol.data.identity` (canonical_psmiles, candidate_id = sha256(canonical|tacticity)[:16]) — the frozen candidate definition (charter §6)"
  - "`llm4pol.data.schema` (DTYPES, PROPERTY_COLUMNS, DECLARED_FIELDS, cast_declared) and `llm4pol.data.load` (row-level + candidate parquets with llm4pol.* metadata)"
  - "`llm4pol.data.report` (Expected, Finding, CountTable refusing a header without `population`, render_markdown, exit_code) and `llm4pol.data.validate` (EXPECTED_POLYOMICS, sections Fetch identity / Source shape / Scope exclusions and identity / Findings)"
  - "14-row synthetic fixture `SYNTHETIC_ROWS` + `synthetic_root`, and the `real_csv` / `real_load` session fixtures that skip without the pinned file (D-09)"
  - "First import-linter contract (llm4pol.data may not import evaluate/run/loop/llm/sklearn), mypy strict on the data stack (typings/rdkit, overrides), pyyaml + types-pyyaml locked"
  - "D-7 and D-10 promoted from prose to named tests in INVARIANTS.md"
affects: [02-02, 02-03, 02-04, 02-05, evaluate, loop]

# Actuals (#2632) — chars/4 over the realized diff (env/pixi.lock excluded), never a harness token count.
actuals:
  tokens: 15400
  tasks: 2
  commits: 4
plan_head_before: 0f4a7d6f8d6c33da2030daf062472fecce27302d

# Tech tracking
tech-stack:
  added: [pyyaml (explicit, was transitive), types-pyyaml 6.0.12.20260906 (conda-forge), typings/rdkit hand-written stub]
  patterns:
    - "Verify-first fetch: the hash on disk is the only verification; hf_hub_download is called only for an absent or mismatched file, never trusted (Q5)"
    - "Declared-subset schema: pd.read_csv dtype map mirrors DECLARED_FIELDS; cast_declared sets each field by index then table.cast (pandas 3 large_string -> string, boolean -> bool)"
    - "Identity via a dict cache over unique smiles_list; missing tacticity -> the literal `unknown` before hashing so candidate_id is total"
    - "Report model: CountTable.__post_init__ refuses a header without `population` (D-10 by construction); findings carry a class (`reproduce` | `documented`) and status; no timestamp, byte-reproducible"
    - "Tests run on a synthetic root (tmp_path) built by the fixture; real-file tests use session fixtures that write only to tmp_path_factory dirs"
    - "Test-module imports of llm4pol.data go through `from llm4pol.data import <module>` so ruff's isort classification is stable before and after a module exists"

key-files:
  created:
    - data/MANIFEST-open.sha256
    - src/llm4pol/data/__init__.py
    - src/llm4pol/data/__main__.py
    - src/llm4pol/data/snapshot.py
    - src/llm4pol/data/fetch.py
    - src/llm4pol/data/identity.py
    - src/llm4pol/data/schema.py
    - src/llm4pol/data/load.py
    - src/llm4pol/data/report.py
    - src/llm4pol/data/validate.py
    - typings/rdkit/__init__.pyi
    - typings/rdkit/RDLogger.pyi
    - typings/rdkit/Chem/__init__.pyi
    - tests/test_data_cli.py
    - tests/test_data_invariants.py
    - tests/test_data_real_file.py
  modified:
    - env/pixi.toml
    - env/pixi.lock
    - pyproject.toml
    - tests/conftest.py
    - docs/governance/INVARIANTS.md

key-decisions:
  - "`fetch(root, *, downloader=None)`: None resolves to the module-level `hf_hub_download` at call time (not a bound default) so `monkeypatch.setattr(fetch, 'hf_hub_download', ...)` in the mismatch test takes effect; behaviour is otherwise the plan's"
  - "Download failures are caught as `(OSError, EntryNotFoundError)`: every huggingface_hub 1.32 error class derives from one of the two (HfHubHTTPError -> OSError; LocalEntryNotFoundError -> FileNotFoundError); AssertionError from a refusing test downloader propagates"
  - "The RED commit's evidence is a collection error (`ImportError: cannot import name 'load' from 'llm4pol.data'`) as the plan specifies; `gsd_run check tdd-red-evidence` would classify that INVALID_RED under #3770 — recorded, not hidden (plan is `type: execute`, `tdd_mode: false`)"
  - "Validator takes `second_monomer_rows` and `parse_failures` from the rows parquet's llm4pol.* metadata (re-canonicalising 78,379 SMILES would cost 15 s per run) and cross-checks `source_rows - second - parse == in_scope_rows`, raising -> exit 2 on inconsistency"
  - "`unique_candidate_ids` is `pc.unique` over the candidate parquet's candidate_id column (D-7: read from the candidate table, never recounted from rows)"
  - "Commits made directly on `main`: the orchestrator ran this executor in sequential mode on the main working tree with `branching_strategy: none` (same as plan 01-01); the executor's protected-branch assertion was consciously overridden by that instruction"

patterns-established:
  - "Manifest-open format: `<sha256>  <size_bytes>  <filename>` with `# revision:` and `# source:` headers; `fetch.parse_manifest` fails fast on any malformed line"
  - "CLI errors: LoaderError / OSError / ValueError -> `ERROR: <msg>` on stderr, exit 2; findings -> stdout `finding <id>: <class> expected=<fmt> observed=<fmt> <status>` then `VALIDATION: n reproduced, m documented, k failed -> exit c`"
  - "Guard promotion: the D-7 / D-10 rows of INVARIANTS.md name the function, the artifact and the test; D-8 and D-9 still read `prose` for plans 02-05 and 02-04"

requirements-completed: [DATA-01, DATA-02, DATA-04, DATA-05, DATA-10]

coverage:
  - id: D1
    description: "`python -m llm4pol.data fetch` verifies the two pinned files by sha256 and size without downloading (exit 0), exits 1 on a mismatch, downloads only when absent"
    requirement: DATA-01
    verification:
      - kind: integration
        ref: "tests/test_data_real_file.py#test_real_fetch_verifies_pinned_files_without_downloading"
        status: pass
      - kind: unit
        ref: "tests/test_data_cli.py#test_cli_fetch_exits_1_on_a_sha256_mismatch"
        status: pass
      - kind: other
        ref: "pixi run --manifest-path env/pixi.toml python -m llm4pol.data fetch (exit 0; .cache mtime unchanged 1790007241 before and after)"
        status: pass
    human_judgment: false
  - id: D2
    description: "`load` writes polyomics-041e5834.parquet (95,332 rows, every source column + candidate_id / canonical_psmiles / row_index, declared types) and candidates-041e5834.parquet (78,676 rows) with metadata llm4pol.snapshot = polyomics:general_polymers@041e5834"
    requirement: DATA-02
    verification:
      - kind: integration
        ref: "tests/test_data_real_file.py#test_real_load_writes_95332_rows_and_78676_candidates"
        status: pass
      - kind: unit
        ref: "tests/test_data_cli.py#test_tracer_fetch_load_validate_round_trip_on_synthetic_root"
        status: pass
    human_judgment: false
  - id: D3
    description: "candidate_id = sha256(canonical_psmiles|tacticity)[:16] with RDKit canonical isomeric SMILES, `*` kept, NaN tacticity -> `unknown`; 78,373 unique canonical, 78,676 candidates on the pinned file"
    requirement: DATA-04
    verification:
      - kind: integration
        ref: "tests/test_data_real_file.py#test_real_validate_reproduces_source_shape"
        status: pass
      - kind: unit
        ref: "tests/test_data_cli.py#test_tracer_fetch_load_validate_round_trip_on_synthetic_root"
        status: pass
    human_judgment: false
  - id: D4
    description: "Candidate table groups replicates by candidate_id before any metric: median / n / min / max / std per registry property, n_rows, one row per id"
    requirement: DATA-05
    verification:
      - kind: unit
        ref: "tests/test_data_invariants.py#test_d7_candidate_table_dedups_replicates_before_any_metric"
        status: pass
    human_judgment: false
  - id: D5
    description: "D-7 and D-10 promoted from prose to named tests in INVARIANTS.md in the same change as the code they guard; every report table names its population"
    requirement: DATA-10
    verification:
      - kind: unit
        ref: "tests/test_data_invariants.py#test_d10_every_count_table_in_report_names_its_population"
        status: pass
      - kind: other
        ref: "sed -n '/^| D-7 /p;/^| D-10 /p' docs/governance/INVARIANTS.md | grep -c test_d (2); D-8 / D-9 rows still `| prose |` (2)"
        status: pass
    human_judgment: false
  - id: D6
    description: "Gate green under mypy strict with pyyaml + types-pyyaml locked from conda-forge, stub gaps covered by overrides + typings/rdkit, first import-linter contract KEPT"
    verification:
      - kind: other
        ref: "pixi run --manifest-path env/pixi.toml check -> SUMMARY: 6/6 steps passed; mypy Success: no issues found in 10 source files; Contracts: 1 kept, 0 broken"
        status: pass
    human_judgment: false

# Metrics
duration: 15min
completed: 2026-09-22
status: complete
---

# Phase 2 Plan 01: Tracer — pinned CSV to validator exit code Summary

**One end-to-end path through `python -m llm4pol.data fetch | load | validate`: the two pinned PolyOmics files verify against `data/MANIFEST-open.sha256` without a network call, the loader writes a typed row-level parquet (95,332 rows) and a candidate parquet (78,676 candidates) carrying `polyomics:general_polymers@041e5834`, and the validator reproduces 95,335 x 259 / 78,379 / 78,373 / 78,676 with every count labelled by population, exiting 0 on the pinned file and 1 on the synthetic root.**

## Performance

- **Duration:** 15 min
- **Started:** 2026-09-21T18:26:51Z
- **Completed:** 2026-09-21T18:42:17Z
- **Tasks:** 2
- **Files modified:** 21 (16 created, 5 modified)

## Accomplishments

- `data/MANIFEST-open.sha256` pins `general_polymers_with_sp_abbe_dynamic-dielectric.csv` (196,910,783 bytes, `71e955ac…`) and `README.md` (15,532 bytes, `c2340252…`) at revision `041e5834ea1a48682fae12dc39ccd723bcd4f771`; `fetch` verifies both by streamed sha256 and byte size, downloads only when absent, and never trusts `hf_hub_download`'s fast path (Q5).
- The candidate definition and snapshot identifier are frozen in code (`identity.candidate_id`, `snapshot.SNAPSHOT_ID`) and written into both parquets' metadata (charter §7 M1 freeze).
- The validator is the number authority for 95,335 x 259, 78,379, 3, 0, 95,332, 78,373 and 78,676, with populations named on every row (D-10) and finding classes per R-5; it exits 1 on drift and 2 on a missing or mismatched input.
- The environment work needed for the whole phase is done inside the tracer: `pyyaml` + `types-pyyaml` declared and locked (conda-forge only), `typings/rdkit` shadows rdkit's broken bundled stub, `[[tool.mypy.overrides]]` for pandas / pyarrow / jsonschema, and the first `[[tool.importlinter.contracts]]` (KEPT).
- D-7 and D-10 promoted from prose to `tests/test_data_invariants.py` in the same change as the code they guard (promotion policy, DATA-10).

## Task Commits

Each task was committed atomically (TDD task: chore → test → feat; Task 2: docs):

1. **Task 1 STEP 1 (environment, typing, import boundary)** — `c83b7c9` (chore) — `chore(02-01): declare pyyaml and types-pyyaml, type the data stack under mypy strict, add the llm4pol.data import contract (R-6, D-8)`
2. **Task 1 STEP 2 (RED)** — `9595349` (test) — `test(02-01): add failing tracer tests for fetch → load → validate on a synthetic root, with D-7 and D-10 promoted (D-09, D-10, DATA-10)`; `git show --stat --format= 9595349` lists exactly `tests/conftest.py`, `tests/test_data_cli.py`, `tests/test_data_invariants.py`, `tests/test_data_real_file.py`
3. **Task 1 STEPS 3–4 (GREEN + promotion)** — `d374870` (feat) — `feat(02-01): tracer — fetch, load, identity, parquet and the first validator section through python -m llm4pol.data; promote D-7 and D-10 (D-01, D-02, D-03, D-04, D-07, D-10, DATA-10)`; `git show --format= d374870 -- docs/governance/INVARIANTS.md` shows exactly two removed and two added lines (D-7, D-10)
4. **Task 2 (real-file proof, timing comment)** — `5c04f3d` (docs) — `docs(02-01): record real-file timing in the real-file test module`

Full shas: `c83b7c986d9a613123e89c0b8a4f2bc49d0558e5`, `9595349a55a41d5894c395514d1404c2ef2339fd`, `d3748709b2ce5b4d2337e51730b20d499ef4b466`, `5c04f3d`.

**Plan metadata:** see the `docs(02-01): complete …` commit that follows this file.

## Recorded lines (per the plan's output spec)

- RED collection error: `E   ImportError: cannot import name 'load' from 'llm4pol.data' (C:\Users\molsim\Desktop\LLM4POL\src\llm4pol\data\__init__.py)` (test_data_invariants; test_data_cli reported `ImportError: cannot import name '__main__' from 'llm4pol.data'`). The tests were re-sorted once by `ruff check --fix` before the RED commit; ruff classified the not-yet-existing submodules as third-party, so the imports were rewritten as `from llm4pol.data import <module>` to keep the order stable after GREEN.
- Resolved `Steps:` line: `Steps: ruff check, ruff format --check, mypy, import-linter, history-secret-scan, pytest`
- Final gate: `SUMMARY: 6/6 steps passed` — mypy `Success: no issues found in 10 source files`; import-linter `never imports a splitter (D-8) KEPT` / `Contracts: 1 kept, 0 broken.`; pytest `35 passed in 21.03s` (26 pre-existing + 6 new + 3 real-file)
- `fetch` on this repository (exit 0, `.cache` mtime `1790007241` before and after — no network call):
  - `verified general_polymers_with_sp_abbe_dynamic-dielectric.csv size=196910783 sha256=71e955ac1e90… (existing)`
  - `verified README.md size=15532 sha256=c2340252a720… (existing)`
  - `snapshot: polyomics:general_polymers@041e5834`
- `load:` line (18.5 s wall): `load: read 95,335 rows x 259 columns; excluded 3 second-monomer rows, 0 parse failures; wrote 95,332 rows -> data/processed/polyomics-041e5834.parquet; 78,676 candidates -> data/processed/candidates-041e5834.parquet`
- Rows parquet schema: `candidate_id string`, `canonical_psmiles string`, `row_index int64`, `smiles_list string`, `thermal_conductivity double`, `check_tc bool`; 262 columns; metadata `llm4pol.snapshot = polyomics:general_polymers@041e5834`. Candidate parquet: 49 columns (`candidate_id`, 9 x `_median/_n/_min/_max/_std`, `n_rows`, `canonical_psmiles`, `tacticity`), same snapshot metadata.
- `validate` on this repository (exit 0):
  - `finding source_rows: reproduce expected=95,335 observed=95,335 reproduced`
  - `finding source_columns: reproduce expected=259 observed=259 reproduced`
  - `finding unique_smiles_list: reproduce expected=78,379 observed=78,379 reproduced`
  - `finding second_monomer_rows: reproduce expected=3 observed=3 reproduced`
  - `finding parse_failures: reproduce expected=0 observed=0 reproduced`
  - `finding in_scope_rows: reproduce expected=95,332 observed=95,332 reproduced`
  - `finding unique_canonical: reproduce expected=78,373 observed=78,373 reproduced`
  - `finding unique_candidate_ids: reproduce expected=78,676 observed=78,676 reproduced`
  - `VALIDATION: 8 reproduced, 0 documented, 0 failed -> exit 0`
  - writes `docs/audit/polyomics-041e5834-validation.md` (left untracked here; plan 02-05 commits the complete report); every table header contains `population`
- Real-file suite (`-vv --durations=5`, exit 0):
  - `tests/test_data_real_file.py::test_real_fetch_verifies_pinned_files_without_downloading PASSED`
  - `tests/test_data_real_file.py::test_real_load_writes_95332_rows_and_78676_candidates PASSED`
  - `tests/test_data_real_file.py::test_real_validate_reproduces_source_shape PASSED`
  - durations: `16.22s setup tests/test_data_real_file.py::test_real_load_writes_95332_rows_and_78676_candidates` / `2.30s call tests/test_data_real_file.py::test_real_validate_reproduces_source_shape` / `0.14s call tests/test_data_real_file.py::test_real_fetch_verifies_pinned_files_without_downloading` / `(2 durations < 0.005s hidden.)` / `3 passed in 18.87s`
- D-09 skip path: proven by inspection (the `real_csv` fixture body calls `pytest.skip(f"pinned PolyOmics file absent at {path} (never committed; run python -m llm4pol.data fetch)")` on `not path.is_file()`; every real-file test reaches the pinned path only through `real_csv` / `real_load`). Not simulated with a flag or a renamed directory; the CI run that plan 02-05 dispatches exercises it.
- `git ls-files data/`: `data/MANIFEST-open.sha256`, `data/MANIFEST.sha256`, `data/README.md` only; `git status --porcelain data/` prints nothing (both parquets untracked, ignored).
- Environment: `env/pixi.lock` gained only `types-pyyaml-6.0.12.20260906-pyh5ded981_0.conda` from `conda.anaconda.org/conda-forge/noarch` (3 lock lines); `pyyaml-6.0.3` unchanged. `grep -c pyyaml env/pixi.toml` = 4.
- mypy overrides / stubs widened beyond the plan: none. The plan's three overrides (`pandas.*`, `pyarrow.*`, `jsonschema.*`) and the three-function `typings/rdkit` stub were sufficient; `pyarrow.compute` and `pyarrow.parquet` fall under `pyarrow.*`.

## Files Created/Modified

- `data/MANIFEST-open.sha256` — six lines: header, `# revision:`, `# source:`, format line, the two entries
- `src/llm4pol/data/__init__.py` — package docstring; re-exports `SNAPSHOT_ID`, `POLYOMICS_REVISION`
- `src/llm4pol/data/snapshot.py` — constants and path helpers (`raw_dir`, `csv_path`, `readme_path`, `manifest_path`, `processed_dir`, `rows_parquet`, `candidates_parquet`, `report_path`), `DEFAULT_ROOT`
- `src/llm4pol/data/fetch.py` — `Manifest`, `FileCheck`, `parse_manifest`, `sha256_of`, `verify_file`, `fetch`
- `src/llm4pol/data/identity.py` — `UNKNOWN_TACTICITY`, `normalise_tacticity`, `canonical_psmiles`, `candidate_id`
- `src/llm4pol/data/schema.py` — `PROPERTY_COLUMNS`, `IDENTITY_COLUMNS`, `DTYPES`, `REQUIRED_SOURCE_COLUMNS`, `DECLARED_FIELDS`, `cast_declared`
- `src/llm4pol/data/load.py` — `LoaderError`, `LoadResult`, `read_source`, `add_identity`, `build_candidates`, `load`
- `src/llm4pol/data/report.py` — `Expected`, `Finding`, `CountTable`, `Section`, `Report`, `evaluate_finding`, `format_int/float/pct/value`, `render_markdown`, `exit_code`
- `src/llm4pol/data/validate.py` — `EXPECTED_POLYOMICS`, `POPULATIONS`, `run`
- `src/llm4pol/data/__main__.py` — `main(argv)` with `fetch | load | validate --root`
- `typings/rdkit/{__init__,RDLogger}.pyi`, `typings/rdkit/Chem/__init__.pyi` — minimal stubs (`Mol`, `MolFromSmiles`, `MolToSmiles`, `DisableLog`)
- `tests/conftest.py` — `SYNTHETIC_ROWS` (14), `SYNTHETIC_README`, `MANIFEST_HEADER`, `sha256_of_file`, `write_manifest`, fixtures `synthetic_root`, `real_csv`, `real_load`
- `tests/test_data_cli.py` — `SYNTHETIC_EXPECTED` and the four behaviours 1–4
- `tests/test_data_invariants.py` — D-7 and D-10 tests, `_markdown_tables` helper
- `tests/test_data_real_file.py` — behaviours 5–7 plus the timing comment
- `env/pixi.toml`, `env/pixi.lock` — `pyyaml`, `types-pyyaml`
- `pyproject.toml` — `mypy_path`, `[[tool.mypy.overrides]]`, `[[tool.importlinter.contracts]]`
- `docs/governance/INVARIANTS.md` — D-7 and D-10 guard cells only

## Decisions Made

See `key-decisions` in the frontmatter. In brief: `fetch`'s downloader default is resolved at call time (monkeypatch-able), download errors are caught as `(OSError, EntryNotFoundError)`, the validator reads exclusion counts from parquet metadata with a consistency cross-check, `unique_candidate_ids` comes from the candidate parquet, commits went to `main` under the orchestrator's sequential instruction.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `fetch` signature `downloader: Downloader | None = None` instead of `= hf_hub_download`**
- **Found during:** Task 1 (writing behaviour 4)
- **Issue:** A default bound to `hf_hub_download` at definition time cannot be replaced by `monkeypatch.setattr(llm4pol.data.fetch, "hf_hub_download", …)`, which is exactly how the plan's mismatch test injects the fake download.
- **Fix:** `None` resolves to the module attribute at call time; every other behaviour unchanged.
- **Files modified:** `src/llm4pol/data/fetch.py`
- **Verification:** `test_cli_fetch_exits_1_on_a_sha256_mismatch` PASSED; real-file fetch still verifies without downloading.
- **Committed in:** `d374870`

**2. [Rule 3 - Blocking] Test imports rewritten as `from llm4pol.data import <module>`**
- **Found during:** Task 1 STEP 2 (RED)
- **Issue:** ruff's isort rule (enabled in this machine's effective ruff config) classifies a not-yet-existing submodule (`llm4pol.data.report`) as third-party, so the import order it demanded before GREEN would be wrong after GREEN — the GREEN commit would then have to touch the test files.
- **Fix:** Import only the existing package (`from llm4pol.data import load, report, …`) and use `report.Expected`, `load.LoadResult`.
- **Files modified:** `tests/test_data_cli.py`, `tests/test_data_real_file.py`
- **Verification:** `ruff check tests` clean in both the RED and GREEN states; GREEN commit touched no test file.
- **Committed in:** `9595349`

---

**Total deviations:** 2 auto-fixed (2 blocking). **Impact on plan:** Both are mechanics of making the plan's own tests runnable; no scope change, no numbers touched.

## Issues Encountered

- The GSD `check tdd-red-evidence` verdict for the RED record was `INVALID_RED` (the record schema also differs from what I supplied). The plan explicitly specifies a collection-error RED ("`ModuleNotFoundError … or equivalent at collection`") because the package modules do not exist before GREEN, and this plan is `type: execute` with `tdd_mode: false`, so the plan-level gate does not apply. Recorded here for the verifier; no test was skipped or weakened.
- import-linter prints the contract name's `§` as replacement characters on this cp949-locale Windows console (`charter ��6`); the verdict `KEPT` and `Contracts: 1 kept, 0 broken.` are unaffected. Cosmetic; CI on Linux prints it correctly.

## TDD Gate Compliance

RED `test(02-01)` `9595349` precedes GREEN `feat(02-01)` `d374870`; no REFACTOR commit was needed (GREEN passed on the first run and the gate was already clean). The RED evidence is a collection error by the plan's design (see Issues).

## Known Stubs

None. Every function in `src/llm4pol/data` is wired to real data; the only placeholder in the tree is the plan-sanctioned untracked report `docs/audit/polyomics-041e5834-validation.md`, which plan 02-05 completes and commits.

## Threat Flags

None beyond the plan's register. New surface introduced: none outside `--root` (T-02-05, accepted) and the two pinned downloads (T-02-01, mitigated by the on-disk hash).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plans 02-03 (error paths, identity vectors, schema assertions), 02-04 (registry loader, replicates, noise floor) and 02-05 (ladders, Maxwell, the committed report, CI evidence) expand from this proven slice; `validate.EXPECTED_POLYOMICS` / `POPULATIONS` and `report.Section` are the extension points.
- Plan 02-02 (registry triad) shares no file with this plan.
- The synthetic fixture satisfies the F-14 identity by construction, so plan 02-05's Maxwell tests hold on it.

---
*Phase: 02-data-foundation*
*Completed: 2026-09-22*

## Self-Check: PASSED

All 13 checked files exist on disk; commits c83b7c9, 9595349, d374870, 5c04f3d are in `git log`; the final gate printed `SUMMARY: 6/6 steps passed`.
