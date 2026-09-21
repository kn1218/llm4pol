# Phase 2: Data Foundation - Research

**Researched:** 2026-09-22
**Domain:** PolyOmics `general_polymers` snapshot (Hugging Face pin, pandas 3 / pyarrow parquet, RDKit identity, jsonschema-validated property registry, validator report)
**Confidence:** HIGH for every number measured on the pinned file this session; MEDIUM for RadonPy unit derivations (fetched source, cross-checked against the data); LOW only where marked `[ASSUMED]`

Every fact below is tagged. `[VERIFIED: …]` = confirmed by a tool this session from an authoritative source (the pinned file itself, the live HF API, the locked pixi environment, RadonPy source, the PolyOmics paper). `[CITED: …]` = quoted from official documentation or source without an independent cross-check. `[ASSUMED]` = training knowledge or a judgement call; listed in the Assumptions Log. "verified" / "unverified" in the facts table follow the same rule.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

### D-01 Fetch and pin
`llm4pol.data.fetch` uses `huggingface_hub.hf_hub_download(repo_id="yhayashi1986/PolyOmics",
repo_type="dataset", revision=<sha>, filename=…, local_dir=data/raw/polyomics/<sha>/)` for the
config file and `README.md`, then verifies size and sha256 against `data/MANIFEST-open.sha256`
(same line format as `data/MANIFEST.sha256`, with a `# revision:` header and the HF URL). The
revision is a constant in one place (`llm4pol.data.snapshot.POLYOMICS_REVISION`) and appears in
the snapshot identifier `polyomics:general_polymers@041e5834`. Files stay untracked (size).
The `.cache/` directory that `hf_hub_download` creates under `local_dir` is ignored.

### D-02 One parquet, declared schema
`llm4pol.data.load` reads the CSV with an explicit dtype map for the registry columns and the
identity columns, keeps every original column (the loop may later need `TC_*` decompositions and
`qm_*` monomer descriptors), adds `candidate_id`, `canonical_psmiles`, `row_index`, and writes
`data/processed/polyomics-041e5834.parquet` with a pyarrow schema asserted by a test. Column
names are kept as in the source; the registry maps keys to columns.

### D-03 Identity (charter §6)
`canonical_psmiles` = RDKit canonical SMILES of `smiles_list` with `*` polymerisation points
kept (`Chem.MolToSmiles(mol, canonical=True, isomericSmiles=True)`), stereo retained (D-6).
Rows whose SMILES fails RDKit parsing are excluded with a count in the report. Rows with a second
monomer (`smiles_2` non-null, 3 rows) are excluded as out of the homopolymer scope (ADR-0004
§4) and counted. `tacticity` NaN is mapped to the literal `"unknown"` before hashing so the id is
total. `candidate_id = sha256(canonical_psmiles + "|" + tacticity)[:16]`.

### D-04 Replicates and candidate values
Rows sharing `candidate_id` are replicates. The candidate table (`data/processed/candidates-
041e5834.parquet`) holds, per candidate and registry property: median, n, min, max, and the
population spread (`std` with ddof=1 where n ≥ 2). The row-level parquet keeps every row. The
noise floor reported in the validator is the median of the within-candidate relative spread
(and absolute spread) over candidates with n ≥ 2, per property (D-9, D-10).

### D-05 Property registry as protocol
`protocol/schemas/property-registry.json` is the JSON Schema; the registry instance is
`protocol/property-registry_v1.yaml` (precedent triad: instance + schema + provenance). Keys:
`thermal_conductivity`, `dielectric_const_dc`, `tg`, `rg`, `r2`, `ffv` (column
`fractional_free_volume`), `sp_ced`, `density`, `refractive_index`. Each entry: `column`, `unit`,
`unit_status` (`verified` | `unverified`), `condition` (300 K, 1 atm, GAFF2_mod), `role`
(`objective` | `constraint` | `intermediate` | `validator`), `physical_range` [min, max] used by
the validator, and `filters` (for `tg`: `tg_rmse` ≤ threshold and 100–900 K). `static_dielectric_const`
must not appear (A-7; a test asserts it). Units: the README states none; the plan's research task
reads arXiv:2511.11626 / RadonPy documentation and records each unit's status. Until verified,
`unit_status: unverified` with the assumed unit (TC W/(m·K), Tg K, density g/cm³, Rg Å, sp_ced
J/cm³ — assumed).

### D-06 Check-step schema inventory (precedent `[tool.calfcheck]`)
Add `[tool.llm4polcheck] validated = [...]` to `pyproject.toml` and a `schema-inventory` step in
`scripts/check.py` that validates every listed instance against its schema (jsonschema, YAML
instances allowed) and fails on a missing table or a zero-match required glob. First entry: the
property registry. `config/*.json` pairing test stays.

### D-07 Validator report is the authority for numbers
`llm4pol.data.validate` computes the report and writes
`docs/audit/polyomics-041e5834-validation.md` (committed; aggregates only). Sections: fetch
identity (revision, hashes), row/column counts, structure and scope exclusions, identity
(unique candidates, parse failures, multi-tacticity SMILES), coverage per registry property,
physical-range filter counts per property, Maxwell check (`static_dielectric_const` vs
`refractive_index**2` violation share — expected 88.9 %; `dielectric_const_dc` — expected 0),
the triple count under each filter step until 43,561 is reproduced or the difference is
documented, replicate structure and noise floor, feasible-set size under the development
default thresholds (ε_dc ≤ table Q25 computed on candidates, Tg ≥ 400 K) stated as an input
to the D-16 gate, and the `tg_rmse` / 100–900 K filter counts (DATA-09). Every number carries
the population it is drawn from (D-10).

### D-08 Guards promoted in the same change (DATA-10)
Tests for: D-7 (dedup before any metric — candidate table has unique ids), D-8 (no row-level
random split — no split code exists; the test asserts `train_test_split` is not imported under
`llm4pol.data`), D-9 (report contains the noise floor), D-10 (every count in the report names its
population), A-7 (registry has no `static_dielectric_const`; loader never selects it as a
property), plus a Maxwell-consistency test on the physical `dielectric_const_dc` rows.
`INVARIANTS.md` guard column updated from "prose" to the test names.

### D-09 Tests without the data file
The raw CSV and parquet are untracked, so tests that need data use a tiny synthetic fixture
(≤ 20 rows written by the test, CSV with the registry columns) and skip the real-file tests with
a stated reason when `data/raw/polyomics/<sha>/` is absent — the same pattern as
`tests/test_manifest.py`. CI therefore exercises the loader logic, not the 197 MB file.

### D-10 CLI
`python -m llm4pol.data fetch | load | validate` with `--root` defaulting to the repository; no
`shell=True`; exit 1 on any validator finding that contradicts an expected value, 2 on IO error.

### Claude's Discretion
- pandas vs pyarrow for the CSV read (pandas with explicit dtypes is fine at 197 MB).
- How the "physical" filter search is expressed, as long as each candidate filter and its count
  is printed in the report.

### Deferred Ideas (OUT OF SCOPE)
- OpenPoly / PoLyInfo loaders → M8 (D-17).
- `chi_parameter/` solvent tables and `MD_snapshot_JSON/` → not needed for M1–M7.
- Tag vocabulary (RDKit SMARTS) → Phase 5 (M4).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DATA-01 | `llm4pol.data.fetch` acquires PolyOmics `general_polymers` at a pinned HF revision and verifies each file's sha256 and size against `data/MANIFEST-open.sha256` | Q5: `hf_hub_download` local_dir fast path never re-hashes; `.metadata` etag = LFS sha256 for the CSV but git blob sha1 for README.md; live API facts (F-01..F-05) |
| DATA-02 | `llm4pol.data.load` produces one parquet with a declared pyarrow schema and identifier `polyomics:general_polymers@<rev>` | Q6: pandas 3 `str` → Arrow `large_string`; declare-subset-and-cast pattern; Snappy default, 64 MB, 0.6 s (F-40..F-45) |
| DATA-03 | Property registry declares key/column/unit/condition for nine keys; `static_dielectric_const` absent | Q1: units resolved per column with status (F-20..F-31); registry skeleton with `propertyNames` enum enforcing A-7 |
| DATA-04 | `candidate_id = sha256(canonical_psmiles + "\|" + tacticity)[:16]` with stereo-aware canonical SMILES | Q4: RDKit 2026.03.6 parses all 78,378 single SMILES, stereo preserved, 5 raw-string merges, 78,676 candidates, no collisions (F-32..F-39) |
| DATA-05 | Replicates grouped by `candidate_id`; candidate value = median with count and spread | Q3: 12,984 multi-row groups, replicate vs re-run split, noise floor per property (F-50..F-58) |
| DATA-06 | Validator reproduces or documents: row count, unique units, 43,561, 88.9 %, 0, 95,335 vs 73,045 | Q2: exact filter for 43,561 found; 88.9 % is 88.83 % on the triple set; the "0" is an algebraic identity; 73,045 not reproducible from the file (F-06..F-19) |
| DATA-07 | Report records replicate structure and noise floor of TC, ε_dc, Tg | Q3 tables (F-50..F-58) |
| DATA-08 | Report states feasible-set size under ε ≤ Q25, Tg ≥ 400 K | F-60..F-63: Q25 = 2.65 on candidates; 6,793 candidates (16.9 %) / 7,317 rows (16.8 %) |
| DATA-09 | Tg rows filtered by `tg_rmse` and 100–900 K; counts recorded | `tg_rmse` is a sum of squared density residuals, not K; threshold ladder F-64..F-66 |
| DATA-10 | D-7..D-10 and A-7 promoted to tests in the same change | Validation Architecture section: test names, synthetic fixture, skip pattern |
</phase_requirements>

## Summary

The pinned file is well understood now. Every number the charter asks Phase 2 to reproduce was re-derived this session directly on `data/raw/polyomics/041e5834ea1a48682fae12dc39ccd723bcd4f771/general_polymers_with_sp_abbe_dynamic-dielectric.csv` (sha256 `71e955ac…`, 95,335 × 259). The single most valuable result: **the README's 43,561 is exactly `thermal_conductivity` non-null ∧ `dielectric_const_dc` ∈ [1, 20] ∧ `tg` ∈ [100, 900] K** — no `tg_rmse`, `check_tc` or Maxwell term is involved. The rank-correlation table and the 1,140 / 2.62 % window reproduce to three decimals on that population, so the population is certain. Two of the README's other numbers do **not** reproduce as stated and the validator must document the differences rather than chase them: the `static_dielectric_const` Maxwell violation is 88.83 % (38,693 / 43,561) on the triple set and 84.3 % on all rows, not 88.9 %; and the `dielectric_const_dc` "zero violations" is an identity, because **`dielectric_const_dc = static_dielectric_const − 1 + refractive_index²` on every one of the 93,488 rows** (max residual 6e-7) — the paper's Table S3 calls it the "corrected static dielectric constant". `static_dielectric_const` is therefore the uncorrected orientational permittivity of non-polarizable MD, not a "broken column"; A-7 stands (use the corrected column) but the report's explanation must change. 73,045 cannot be reproduced from any column of the file; it is the dataset card's description and probably a per-class unique-structure sum from the paper's Table S2.

Units are resolved for every registry column from RadonPy source, the paper's Supplementary Table S3 and internal physical identities in the data: TC W/(m·K), Tg K, density g/cm³, Rg Å, `fractional_free_volume` dimensionless, `refractive_index` dimensionless, `sp_ced` MPa (numerically J/cm³, since `sp_total² = sp_ced`), ε_dc dimensionless. One conflict: `r2` is Å² per the paper but the data only make sense in nm² (`r2/Rg²` = 5.58 with r2 nm², Rg Å — the ideal-chain value is 6). `tg_rmse` is a **sum of squared density residuals**, not an RMSE in kelvin, so its threshold is a protocol decision, not a physics bound.

Replicates: 12,984 of 78,682 (`smiles_list`, tacticity-with-unknown) groups have more than one row; only 1,888 are same-version replicates, 11,096 are re-runs across RadonPy/preset versions, yet the TC spread is the same in both (3.8 % vs 3.7 % median relative std), so one noise floor per property is defensible. Noise floor (median relative std, n ≥ 2): TC 3.7 %, ε_dc 0.8 %, Tg 5.8 % (30 K), density 0.3 %. Identity works out of the box: RDKit 2026.03.6 parses all 78,378 single SMILES with stereo preserved; the only "failure" is the comma-joined cellulose `smiles_list` on the 3 out-of-scope rows. Two pitfalls dominate the implementation: pandas 3 makes strings `large_string` in Arrow (declare and cast), and pandas `groupby` drops the 554 NaN-tacticity rows silently unless `dropna=False` — that is why CONTEXT.md counted 2 multi-tacticity SMILES where the D-03 rule (NaN → `"unknown"`) yields 303.

**Primary recommendation:** Implement the validator as a printed ladder of named filter steps over named populations (row-level, then candidate-level), with the four expected values as `expected`/`observed`/`status` rows; reproduce 43,561 with the `[1, 20]` ε_dc filter, report 88.83 % and the ε_dc identity as documented differences, and pin the `tg_rmse` and `check_tc` filters in the registry as protocol decisions whose counts are printed alongside the unfiltered numbers.

## Facts the plan may cite

All "measured" facts were computed this session on the pinned file with pandas 3.0.5 / RDKit 2026.03.6 in the locked pixi environment (`pixi run --manifest-path env/pixi.toml python`), scripts kept in the session scratchpad. Populations are stated explicitly (D-10).

### Fetch identity (DATA-01)

| # | Fact | Value | Status |
|---|---|---|---|
| F-01 | HF dataset `yhayashi1986/PolyOmics`, revision | `041e5834ea1a48682fae12dc39ccd723bcd4f771`; `main` still resolves to it on 2026-09-22; last_modified 2026-09-03 20:17:45 UTC; `gated: False`; card licence `cc-by-4.0` | verified `[VERIFIED: HfApi.dataset_info live, 2026-09-22]` |
| F-02 | Config file `general_polymers_with_sp_abbe_dynamic-dielectric.csv` | 196,910,783 bytes; LFS sha256 `71e955ac1e90574ad009ccbf1238e595cf42905f3e600523ba2a6ea65c350213`; blob_id `7c7e8a77aadf770e6442bffa3df073b7fc83d186`; local `sha256sum` identical | verified `[VERIFIED: HfApi.get_paths_info + sha256sum]` |
| F-03 | `README.md` | 15,532 bytes; **not LFS** (`lfs: None`, no sha256 from the API); blob_id `18c8ef89fe96fd30004c3a915921184172a57543`; local sha256 `c2340252a720f7b9f56fcc368105d9e1e351c2bd75f31a364f7c2afcb5a6cc13` | verified `[VERIFIED: HfApi + sha256sum]` |
| F-04 | `git hash-object --no-filters README.md` reproduces the blob_id; plain `git hash-object` does **not** on this machine (`core.autocrlf=true`) | `18c8ef89…` vs `6dde8205…` | verified `[VERIFIED: git]` |
| F-05 | `.cache/huggingface/download/<file>.metadata` layout | three lines: commit hash, etag, timestamp; etag = LFS sha256 for the CSV, = git blob sha1 for README.md; `.cache/huggingface/.gitignore` contains `*` | verified `[VERIFIED: files on disk + huggingface_hub source via Context7]` |

### Shape and the README numbers (DATA-06)

| # | Fact | Value | Status |
|---|---|---|---|
| F-06 | Rows × columns (`pd.read_csv(low_memory=False)`) | 95,335 × 259 | verified |
| F-07 | Unique `smiles_list` | 78,379; unique canonical (RDKit, in scope) 78,373; unique `candidate_id` 78,676; unique `UUID` 95,335; unique `monomer_ID` 78,336 (76 null) | verified |
| F-08 | **43,561 filter** | `thermal_conductivity.notna() & dielectric_const_dc.between(1, 20) & tg.between(100, 900)` = **43,561** on all rows. Since min ε_dc = 1.028, `ε_dc ≤ 20` alone is equivalent. Steps: TC 81,405 → ∧ ε_dc∈[1,20] … → ∧ Tg window = 43,561. Naive `ε_dc.notna()` gives 45,821; `≤ 10` gives 42,186; `≤ 50` gives 45,134; `≤ 100` gives 45,704 | verified |
| F-09 | 43,561 needs no `tg_rmse` filter | with `tg_rmse ≤ 5` the count is unchanged; `≤ 0.5` → 43,522; `≤ 1` → 43,546; `≤ 2` → 43,557 | verified |
| F-10 | The same 43,561 rows all carry `refractive_index` | 43,561 (the README's "also carry refractive index") | verified |
| F-11 | Rank correlations (Spearman) on the 43,561 rows | TC–ε_dc 0.170, TC–Tg 0.010, ε_dc–Tg 0.199, `sp_ced`–TC 0.355, `ffv`–TC −0.069, `Rg`–TC 0.304, `density`–TC −0.270 — README table reproduced to three decimals | verified |
| F-12 | Window (top-decile TC ∧ bottom-quartile ε_dc on the 43,561) | 1,140 rows = 2.62 %; medians window/all: Rg 30.54/20.19, density 0.967/1.130, ffv 0.221/0.187, sp_ced 251/295, TC 0.349/0.239, ε_dc 2.462/2.894 — README reproduced | verified |
| F-13 | `static_dielectric_const` "Maxwell violation" (`sd < refractive_index²`) | **88.83 %** (38,693 / 43,561) on the triple set; 84.30 % (78,807 / 93,488) on all rows with both columns; 89.18 % on ε_dc ≤ 20 rows; `<` and `≤` give the same count. README's 88.9 % is **not reproduced exactly**; 88.83 → rounds to 88.8 | verified (difference documented) |
| F-14 | `dielectric_const_dc ≡ static_dielectric_const − 1 + refractive_index²` | holds on all 93,488 rows with ε_dc; max abs residual 5.7e-7, median 8e-10 | verified `[VERIFIED: data; definition CITED: arXiv 2511.11626 Table S3 "Corrected dielectric constant (static) … Defined as (static dielectric constant) − 1 + (refractive index)²"]` |
| F-15 | Consequence: ε_dc ≥ n² ⇔ `static_dielectric_const` ≥ 1, and min `static_dielectric_const` = 1.00016 | so "0 Maxwell violations" for ε_dc is an identity, not an independent check; the Maxwell-consistency test (D-08) should assert the identity residual and `static ≥ 1`, not merely `ε_dc ≥ n²` | verified |
| F-16 | ε_dc coverage = refractive-index coverage | 93,488 rows each; ε_dc is NaN exactly where `refractive_index` is NaN (0 mismatches) | verified |
| F-17 | `static_dielectric_const` descriptives | median 1.392; 76.3 % below 1.8; Spearman vs n²: 0.003 (all rows), −0.144 (triple set) — README's −0.05 not reproduced on either population | verified (difference documented) |
| F-18 | ε_dc descriptives | median 2.897; 88.4 % of rows in [2, 5]; Spearman vs n² 0.515 (all), 0.476 (triple); `efdp_permittivity_real` 1,084 rows, median 2.900 | verified |
| F-19 | 73,045 | is the dataset card's description text ("73,045 general polymers in the isotropic amorphous state"); **no column of the file reproduces it** (unique smiles 78,379; monomer_ID 78,336; UUID 95,335; class flags are multi-label, 220,137 flags). The paper's Table S2 "# of unique chemical structures" per class sums to ≈ 73,046 in a pdftotext extraction | verified as "not reproducible from the file"; the Table S2 origin is `[ASSUMED]` (imperfect PDF text) |

### Units and conditions (DATA-03) — answer to Q1

| # | Column | Unit in the file | Evidence | Status |
|---|---|---|---|---|
| F-20 | `thermal_conductivity` | W/(m·K) | RadonPy `sim/preset/tc.py`: LAMMPS input converts heat flux to SI (`heatflux = (f_mp*kcal2j/NA)/(2*Jarea*ang2m*ang2m)`, time `*1e-15` s) and `get_Tgrad_twoway` divides the K/Å slope by `grad_conv = length*1e-10` → K/m; `TC = Qgrad/Tgrad`. Paper Table S3 lists `TC_*` decomposition columns as W·m⁻¹·K⁻¹. Data identity: `thermal_diffusivity = TC / (1000·density·Cp)` holds to 1e-7 with Cp in J/(kg·K) | **verified** `[VERIFIED: RadonPy source + paper Table S3 + data identity]` |
| F-21 | `dielectric_const_dc` | dimensionless; = ε_static − 1 + n² (F-14) | paper Table S3; data | **verified** |
| F-22 | `tg` | K | `sim/preset/tg.py`: `tg = (b2−b1)/(a1−a2)` intersection of two density-vs-T fits; paper Table S3 "tg K"; data median 488.5 K | **verified** `[VERIFIED: RadonPy source + Table S3]` |
| F-23 | `tg_rmse` | (g/cm³)² — a **sum of squared density residuals**, not an RMSE and not kelvin | `tg.py`: `rmse.append(np.sum(np.square(diff)))`, `data['tg_rmse'] = rmse[rmse_arg]`; data median 0.029, p95 0.099, p99 0.236, max 36.3 | **verified** `[VERIFIED: RadonPy source via WebFetch]` — treat the exact expression as `[CITED]`; the "not kelvin" conclusion is safe either way |
| F-24 | `Rg` | Å | paper Table S3 "Radius of gyration Rg — Å"; data: `Rg/√Mn` = 0.228 raw units (Å-scale for a Mn ≈ 7,500 chain; nm would be 10× any real polymer), cubic cell edge 47.7 Å vs median Rg 19.9; `Scaled Rg = Rg / Mw^0.6` exactly (Table S3 definition) | **verified** `[VERIFIED: Table S3 + data]`. Note: RadonPy's `Analyze` computes Rg with `mdtraj.compute_rg` after `mdtraj.load_lammpstrj` (which converts to nm) with no `×10` visible in the fetched branch — the pipeline that produced the file evidently rescaled; the file value is Å |
| F-25 | `r2` | **nm²** in the file | paper Table S3 says "Mean square end-to-end distance — Å²", but `r2/Rg²` = 0.0558 raw; = 5.58 if r2 is nm² and Rg Å (ideal chain: 6). In Å² the end-to-end distance would be 4.6 Å for a chain with Rg 20 Å, which is impossible. RadonPy computes it as `mean(compute_contacts(TU0,TU1,'closest')**2)` on an mdtraj (nm) trajectory | **unverified** — paper and data conflict; registry entry `unit: nm^2`, `unit_status: unverified`, note the conflict. `r2` is only an intermediate/validator variable |
| F-26 | `fractional_free_volume` | dimensionless | `= (cell_volume − 1.3·vdw_volume_bulk)/cell_volume` exactly on all 87,849 rows (RadonPy `core/calc.py fractional_free_volume` formula); paper Table S3 "dimensionless"; `cell_volume`, `free_volume`, `vdw_volume_bulk` in Å³ (`density·cell_volume·1e-24·N_A/(n_mol·Mn)` = 0.9998) | **verified** |
| F-27 | `sp_ced` | MPa ≡ J/cm³ (numerically identical; 1 J/cm³ = 1 MPa) | RadonPy `sim/preset/sp.py`: `CED = (etotal_intra − etotal_inter)/Vm` with energies in J/mol and Vm in cm³/mol, plot label "Cohesive Energy Density [J cm^-3]"; paper Table S3 lists `sp_total`… as MPa^0.5; data identity `sp_total² = sp_ced` to 2e-5. Not cal/cm³ (ratio would be 0.239) | **verified** `[VERIFIED: RadonPy source + Table S3 + data identity]` |
| F-28 | `density` | g/cm³ | LAMMPS `units real` thermo density; paper Table S3 "g·cm⁻³"; data identity F-26 | **verified** |
| F-29 | `refractive_index` | dimensionless, Lorentz–Lorenz from DFT polarizability (`core/calc.py refractive_index`: `ri = sqrt((1+2φ)/(1−φ))`); `refractive_index_sos_*` are the TD-DFT wavelength-dependent variants (18,943 rows) | paper Table S3; RadonPy source | **verified** |
| F-30 | Conditions | `temp` 300 on every row, `press` 1 (atm), `forcefield` `GAFF2_mod` on every row, `charge` `RESP`, `qm_method` `wb97m-d3bj` (94,726 rows, 609 NaN), `input_natom` 1000 (**per chain**: `n_atom` is a `/`-joined per-chain string, median 998), `input_nchain` 10 (`n_mol` 10; 5 on 1 row), `Mw/Mn` 1.0, DP median 23 | verified (paper Methods: GAFF2, 300 K, 1 atm, ~1,000 atoms per chain, 10 chains) |
| F-31 | Versions | `RadonPy_ver` 0.2.10 (63,119) / 0.2.9 (21,512) / 0.2.1 / 0.2.0b3 / 0.2.0b2 / 0.2.8 / 11 more (17 values); `preset_tg_ver` 0.1.1 / 0.1.3 / 0.1.0 (NaN 39,271); `preset_tc_ver` 0.2.1 (57,657) / NaN 13,807 / 0.2.8 / …; `preset_sp_ver` 0.1.1 (71,854) / NaN | verified |

### Identity (DATA-04) — answer to Q4

| # | Fact | Value | Status |
|---|---|---|---|
| F-32 | RDKit 2026.03.6 `Chem.MolFromSmiles` on all 78,379 unique `smiles_list` | 1 failure, and it is the comma-joined cellulose list `[6*]OC[C@@H](O1)…,…,*[H]` that is the `smiles_list` of the 3 `smiles_2`-non-null rows (not a SMILES). All 78,378 single SMILES parse; 15.6 s total | verified |
| F-33 | `*` handling | every single SMILES has exactly two `*`; canonical output keeps `*`; labelled dummies `[2*]`,`[3*]`,`[6*]` occur only in the cellulose rows (their `smiles_1..4` parse individually, with 5/4/4/1 dummies) | verified |
| F-34 | Stereo | 8,467 inputs carry `@`, `/` or `\`; all 8,467 canonical outputs still do; 0 lost, 0 gained; canonicalisation is idempotent (5,000 sampled) | verified |
| F-35 | Merges | 78,379 raw → 78,373 canonical: 5 pairs of raw strings are the same molecule (e.g. `*C(C*)(C)C(=O)OC` and `*C(C*)(C(=O)OC)C` → `*CC(*)(C)C(=O)OC`; `*/C(=C/CC*)C` and `*CC/C=C(/*)C`); 3 of the 5 pairs join rows of tacticity `atactic`/`none` with rows of `unknown` | verified |
| F-36 | `smiles_search` is **not** a canonical monomer | it is a ring-closed ~10-mer with stereo stripped (e.g. `*Cc1cccc(*)c1` → `c1cc2cc(c1)Cc1cccc(c1)C…C2`); 4,149 lose stereo; 0 of 78,378 equal our canonical. This is exactly the D-6 "naive ring-closing key". Never use it for identity | verified |
| F-37 | Candidate ids | in-scope rows 95,332 (3 cellulose rows excluded); unique `(canonical, tacticity∪unknown)` keys 78,676 = unique `sha256[:16]` ids 78,676 (no truncation collisions) | verified |
| F-38 | Tacticity | `none` 48,790 / `atactic` 45,032 / `isotactic` 951 / `syndiotactic` 8 / NaN 554. `tacticity` NaN ⇔ `input_tacticity` NaN (554 rows); `none` ⇔ `input_tacticity` `atactic` (48,784) or NaN (6): `none` means "atactic requested, no stereocentre" | verified |
| F-39 | Multi-tacticity SMILES | **2** when NaN is dropped (pandas default) — the CONTEXT.md number; **303** when NaN → `"unknown"` (D-03): the 554 unknown rows are old-workflow runs of repeat units that also exist with a known tacticity. D-03 therefore creates 303 `unknown` twins | verified |

### Loader mechanics (DATA-02) — answer to Q6

| # | Fact | Value | Status |
|---|---|---|---|
| F-40 | `pd.read_csv(path, low_memory=False, dtype=<map>)` | 2.1–2.3 s; dtypes without a map: 177 float64, 50 `str`, 22 bool, 7 int64, 3 object | verified |
| F-41 | Columns that are strings but look numeric | `n_atom`, `mol_weight` are `/`-joined per-chain lists (`'996/996/…'`); `tg_init_density_check` is bool + NaN (object); `check_tc` / `do_TC` have None → declare `boolean` | verified |
| F-42 | pandas 3 `str` → Arrow `large_string`, `boolean` → `bool` with nulls; a declared `pa.string()` field does **not** match `from_pandas` output | fix: `full = tbl.schema; full = full.set(full.get_field_index(name), field)` for each declared field, then `tbl = tbl.cast(full)` (0.0 s); a wrong type raises `ArrowInvalid` | verified |
| F-43 | `pq.write_table` default compression | SNAPPY; 64.0 MB, 0.6 s; zstd 55.0 MB, 0.6 s; `pq.read_schema(path).remove_metadata().equals(schema.remove_metadata())` round-trips | verified `[VERIFIED: pixi env + Arrow docs]` |
| F-44 | `pd.read_parquet` of the result | 0.1 s; dtypes: 179 float64, 50 `str`, 22 bool, 5 int64, 2 `BooleanDtype`, 1 object | verified |
| F-45 | jsonschema 4.26.0 + PyYAML 6.0.3 | `jsonschema.validate(yaml.safe_load(...), schema)` selects `Draft202012Validator` from `$schema`; `prefixItems`, `items: false`, `propertyNames` work; `Draft202012Validator.check_schema` validates the schema | verified |
| F-46 | `pyyaml` is **not declared** in `env/pixi.toml`; present only as a transitive dependency of `huggingface_hub` (`pixi.lock` line 3566: `pyyaml >=5.1`) | must be declared explicitly; `types-pyyaml` (conda-forge `6.0.12.20260906`) is required for `mypy --strict` — `import yaml` without stubs fails ("Library stubs not installed") | verified |
| F-47 | PyYAML 1.1 float quirk | `yaml.safe_load("x: 1e-3")` → the **string** `'1e-3'`; write `1.0e-3` | verified |
| F-48 | pandas `groupby` drops NaN keys by default | `(smiles_list, tacticity)` groups: 78,324 with NaN dropped vs 78,682 with `dropna=False`/`fillna` | verified |

### Replicates and noise floor (DATA-05, DATA-07) — answer to Q3

| # | Fact | Value | Status |
|---|---|---|---|
| F-50 | Group structure by (`smiles_list`, tacticity∪unknown) | 78,682 groups; sizes 1: 65,698 / 2: 11,368 / 3: 578 / 4: 55 / 5: 964 / 6: 16 / 7: 2 / 17: 1; 12,984 multi-row groups holding 29,637 rows. By `candidate_id` (canonical): 78,676 candidates, 12,983 multi-row, max 17 | verified |
| F-51 | Are they independent runs? | `UUID` unique per row (95,335); `monomer_ID` identical within 12,952 / 12,984 groups; `input_natom`, `input_nchain`, `ini_density`, `LAMMPS_ver` identical within every group; `DP`, `n_atom`, `Mn` identical in all but 1 group | verified |
| F-52 | Replicate vs re-run | all eight version columns (`RadonPy_ver`, `preset_eq/tc/tg/sp_ver`, `RDKit_ver`, `Psi4_ver`, `Python_ver`) identical within the group: **1,888** groups (same-version replicates); differ in ≥ 1: **11,096** (re-runs across workflow versions; `preset_tg_ver` differs in 8,188, `preset_tc_ver` in 5,342, `RadonPy_ver` in 3,896) | verified |
| F-53 | Spread does not depend on that split | TC median relative std: 0.0376 (same-version, n = 1,860) vs 0.0368 (mixed-version) → one noise floor per property is defensible | verified |
| F-54 | Exact duplicates | 6 rows in multi-row groups are identical on identity + all 9 registry columns | verified |
| F-55 | **Noise floor, all candidates with n ≥ 2** (median over groups; abs = std ddof=1; rel = std/\|median\|) | TC: 9,439 groups, abs 0.0082 W/(m·K), rel **0.0369**, rel range (max−min)/median 0.0552, p90 rel 0.090 · ε_dc: 12,842, abs 0.0227, rel **0.0084**, range 0.0130 · Tg: 2,377, abs **30.2 K**, rel **0.0577**, range 0.105, p90 rel 0.46 · density: 12,984, abs 0.0036, rel 0.0034 · Rg: 12,984, abs 0.61 Å, rel 0.035 · r2: 12,906, rel 0.163 · ffv: 9,453, rel 0.024 · sp_ced: 8,606, abs 4.8, rel 0.022 · refractive_index: 12,842, rel 0.0014 | verified |
| F-56 | Noise floor on the triple population (filter rows to the 43,560 in-scope triple rows, then group by `candidate_id`, n ≥ 2 = 1,725 groups) | TC rel 0.0431 (abs 0.0098); ε_dc rel 0.0112 (abs 0.031); Tg rel 0.0540 (abs 27.5 K) | verified |
| F-57 | Outliers inside replicate groups | e.g. PMMA `*CC(*)(C)C(=O)OC` 11 rows with TC 0.19…19.1 W/(m·K); a `check_tc == False` run is what produces such values (F-59) → the candidate median, not the mean, is the right aggregate (D-04 already says median) | verified |
| F-58 | CONTEXT.md example "TC 0.187 vs 0.130" | is `*/C(=C(/*)C(F)(F)F)c1ccccc1` (tacticity `none`, 2 rows: 0.1305 / 0.1867) | verified |
| F-59 | `check_tc` | True 79,927 / False 15,376 / None 32; TC non-null ∧ `check_tc == False`: **1,511** rows; of the 109 rows with TC > 1 W/(m·K), 108 are `check_tc == False`; triple ∧ `check_tc == True` = **42,733** (42,732 in scope); TC max 43.4 W/(m·K) overall; `remarks` carries `[ERROR: Low linearity of temperature gradient.]` on 1,688 rows. RadonPy AutoMD README: `check_tc` = "thermal conductivity checks passed", `do_TC` = whether TC was computed; the check is R² ≥ 0.98 on both temperature-profile halves | verified `[VERIFIED: data; semantics CITED: RadonPy AutoMD_scripts/README.md + tc.py]` |

### Feasible set and filter ladders (DATA-08, DATA-09)

| # | Fact | Value | Status |
|---|---|---|---|
| F-60 | ε_dc Q25 | rows of the triple: 2.6427; candidates (triple rows → median per `candidate_id`): **2.6524**; all rows 2.6071 | verified |
| F-61 | Candidate-level triple size depends on order | filter rows then median per candidate: **40,212** candidates; median per candidate then filter: 40,426. The plan must fix one order (recommend filter-then-median: a candidate is "in the table" if it has at least one physical row per property) | verified |
| F-62 | Feasible set (ε_dc ≤ Q25 ∧ Tg ≥ 400 K), development defaults, **not a D-16 decision** | rows: 7,317 of 43,560 in-scope triple rows (16.80 %); candidates: **6,793 of 40,212 (16.89 %)** with Q25 computed on candidates | verified |
| F-63 | Tg medians | all rows 488.5 K; triple rows 472.2 K | verified |
| F-64 | `tg` window | 56,064 non-null; 52,753 inside [100, 900]; 3,311 outside (fit failures up to 1.08e6 K); `tg_max_temp` 800–5,100 K, `tg_min_temp` 50 K, `tg_interval_temp` 10 K, `tg_cooling_rate` 8,000 on every row | verified |
| F-65 | `tg_rmse` ladder on in-scope triple rows (43,560) | `≤ 0.05` → 36,592 · `≤ 0.1` → **42,232** · `≤ 0.2` → 43,316 · `≤ 0.5` → 43,521 · `≤ 1.0` → 43,545; window rows removed by the same thresholds: 8,170 / 1,471 / 259 / 39 / 15 | verified |
| F-66 | Recommended default threshold `tg_rmse ≤ 0.1` (≈ 0.027 g/cm³ RMS over ~135 cooling points) | protocol decision, must be pinned in the registry with provenance `protocol_decision` and printed with the ladder | `[ASSUMED]` (A3) |
| F-67 | Physical ranges observed | TC min 0.038, p99 0.50, p99.9 1.23, max 43.4; ε_dc 1.03…3,678 (5,123 rows > 20, 7,742 > 10); density 0.388…2.84; ffv min −0.046, max 0.71; refractive_index 0.81…3.07 (1 row < 1, 34 > 2); Rg 9.5…124 Å; sp_ced 36.6…1,741 | verified |

## Answers to the planner's questions

**Q1 — Units.** Resolved above (F-20..F-31). Registry `unit_status`: `verified` for `thermal_conductivity`, `dielectric_const_dc`, `tg`, `rg`, `ffv`, `sp_ced`, `density`, `refractive_index`; `unverified` for `r2` (paper says Å², data says nm²). `condition` for every key: 300 K, 1 atm, `GAFF2_mod`, RESP charges, ~1,000 atoms/chain × 10 chains, isotropic amorphous cell. Source locations: RadonPy `radonpy/sim/preset/tc.py` (`NEMD_MP.make_lammps_input`, `NEMD_MP_Analyze.get_Tgrad_twoway`, `calc_tc`), `radonpy/sim/preset/sp.py` (`data['sp_ced'] = CED`), `radonpy/sim/preset/tg.py` (`TGMD_analyze.step_wise`), `radonpy/sim/lammps.py` (`Analyze`, `elif prop == 'rg'`, `elif prop == 'r2'`, `elif prop == 'dielectric'`), `radonpy/core/calc.py` (`refractive_index`, `mol_density`, `fractional_free_volume`); arXiv:2511.11626 Supplementary Table S3 "62 properties … Unit in the database". `[CITED: github.com/RadonPy/RadonPy develop branch, fetched 2026-09-22; arXiv:2511.11626 PDF via pdftotext]`.

**Q2 — The 43,561 filter.** `TC notna ∧ ε_dc ∈ [1, 20] ∧ Tg ∈ [100, 900]` reproduces it exactly (F-08). The validator should print the ladder: all rows 95,335 → TC 81,405 → ∧ ε_dc non-null 79,929 → ∧ ε_dc ≤ 20 → ∧ Tg ∈ [100, 900] = 43,561 (and the in-scope 43,560 after excluding the cellulose row). Then the *additional* protocol filters with their counts: `check_tc == True` → 42,733; `tg_rmse ≤ 0.1` → 42,232; both → to be printed. The 88.9 % becomes 88.83 % (F-13) and the "0" is the F-14 identity — both documented as differences, not chased.

**Q3 — Replicates.** Rows in a group are separate MD runs of the same monomer record (unique `UUID`, shared `monomer_ID`, identical cell settings); 15 % are same-version replicates and 85 % are re-runs across RadonPy/preset versions, with indistinguishable spread (F-52, F-53). Noise floor (median relative std, n ≥ 2): **TC 3.7 %, ε_dc 0.8 %, Tg 5.8 % (30 K), density 0.3 %** (F-55); on the triple population TC 4.3 %, ε_dc 1.1 %, Tg 5.4 % (F-56). Report both the absolute and relative spread, both populations, and the p90 (TC 9 %, Tg 46 %) because the Tg tail is heavy.

**Q4 — RDKit.** Works as locked in D-03 with zero parse failures on single SMILES; stereo fully preserved; `*` kept; 5 raw-string merges are correct chemistry (same molecule written differently); the only pitfalls are the comma-joined cellulose list (already excluded by the `smiles_2` rule — exclude by `smiles_2.notna()` *before* parsing so it is counted as scope, not as a parse failure), `smiles_search` (never use), and the 303 `unknown` twins created by the NaN rule (F-39; report it, see Open Question 1). `[CITED: rdkit.org docs — MolToSmiles isomeric by default since 2018.03; parameters `isomericSmiles`, `canonical`]`.

**Q5 — huggingface_hub.** `hf_hub_download(..., revision=<40-hex sha>, local_dir=…)`: if the file exists and `.cache/huggingface/download/<file>.metadata` records the same commit hash, it returns immediately with **no network call and no re-hash**; otherwise it HEADs `/resolve`, compares etags, and downloads only on mismatch (`[CITED: huggingface_hub file_download._hf_hub_download_to_local_dir via Context7]`). The library never verifies content against the LFS sha256 — `fetch` must hash the file itself and compare to `MANIFEST-open.sha256`. The remote sha256 is available for the CSV via `HfApi.dataset_info(repo_id, revision=sha, files_metadata=True).siblings[i].lfs.sha256` or `get_paths_info(...)[i].lfs.sha256`; **README.md has no LFS sha256** (only `blob_id`, a git sha1 = `sha1(b"blob %d\0" + bytes)`), so its manifest sha256 is a locally computed, committed value (F-03..F-05). Behaviour when the file exists: skip (fast path) — so `fetch` is idempotent and works offline once the files are in place; `force_download=True` re-downloads.

**Q6 — pyarrow schema.** Declare only the registry + identity + added columns as `pa.field`s; take `pa.Table.from_pandas(df, preserve_index=False).schema`, override those fields by index, `cast` (F-42), write with `pq.write_table` (Snappy default, F-43). The test asserts `pq.read_schema(path)` contains the declared fields with the declared types and that `schema.remove_metadata()` equals the loader's declared full schema. Use `pa.string()` (after cast) or accept `large_string` — pick one and assert it; the cast to `string` costs nothing.

**Q7 — jsonschema / YAML.** jsonschema 4.26.0 supports Draft 2020-12 and picks it from `$schema` (F-45). PyYAML 6.0.3 is importable but undeclared (F-46): add `pyyaml = "*"` to `[feature.base.dependencies]` and `types-pyyaml = "*"` to `[feature.dev.dependencies]` in `env/pixi.toml` and re-lock (conda packages lock for linux-64 from the Windows host; only the pypi-editable case was the FOUND-01 problem). Alternative that avoids the re-lock: keep the registry instance as `protocol/property-registry_v1.json` — but D-05 locks YAML, so re-lock.

**Q8 — Validation architecture.** See the section below: CI runs everything on a ≤ 20-row synthetic CSV written by the test; the real-file tests are the same functions parametrised over the real path and `pytest.skip` when `data/raw/polyomics/<sha>/<csv>` is absent, exactly as `tests/test_manifest.py::test_raw_files_match_manifest` does.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Pin + download + hash verification | `llm4pol.data.fetch` (library) | CLI `python -m llm4pol.data fetch` | Only place that touches the network; identity constant lives in `llm4pol.data.snapshot` |
| CSV → typed parquet, added columns | `llm4pol.data.load` + `llm4pol.data.schema` | — | Schema is a declared pyarrow object asserted by tests |
| Canonical SMILES + `candidate_id` | `llm4pol.data.identity` (pure functions) | `load` calls it per row | Pure, testable on strings; no I/O |
| Replicate aggregation (candidate table) | `llm4pol.data.load` (writes `candidates-<rev>.parquet`) | `validate` reads it | Dedup happens once, before any metric (D-7) |
| Registry (keys, units, ranges, filters) | `protocol/property-registry_v1.yaml` + `.schema.json` + `.provenance.yaml` | `llm4pol.data.registry` loads it; `scripts/check.py schema-inventory` validates it | Protocol, not code; A-7 enforced by `propertyNames` enum in the schema |
| Validator report | `llm4pol.data.validate` → `docs/audit/polyomics-<rev>-validation.md` | tests assert sections/populations | The authority for numbers (charter §10) |
| Guards D-7..D-10, A-7 | `tests/test_data_*.py` inside the check gate | `INVARIANTS.md` guard column | Promotion policy: same change as the loader |

## Project Constraints (from CLAUDE.md)

- Precedence: charter > REQUIREMENTS.md > CLAUDE.md > generated blocks; conflicts are flagged, never silently resolved (ADR-0002). Gate parameters (D-16 thresholds) stay gated — the report *states* the feasible-set size and must not fix D-16.
- No data file is ever committed (`data/raw/`, `data/interim/`, `data/processed/` git-ignored); aggregates only in `docs/audit/`. Row-level exports, per-record SMILES tables and fixtures embedding real rows are forbidden by `data/README.md` — the synthetic fixture must be invented rows, not copied ones.
- `pixi run --manifest-path env/pixi.toml check` (ruff, ruff format, mypy strict on `src/llm4pol`, import-linter, history secret scan, pytest) passes before any commit; CI runs it on windows-latest and ubuntu-latest with `fetch-depth: 0`.
- Every cross-component payload has a JSON Schema in `protocol/schemas/`; `config/*.json` needs a sibling `*.schema.json` (existing test).
- No `shell=True`; subprocesses via `sys.executable -m …` (check.py convention). Never print `.env` or secret values.
- Conventional commits scoped by GSD plan id (`feat(02-01): …`).
- A rule that matters becomes a test/schema/CI check as soon as it is stable; placeholders, skipped tests and stubs are blockers.
- `src/llm4pol/` may now hold production code (charter `Status: Approved`; `tests/test_governance.py::test_charter_status_gates_production_code`).
- Import boundary for this phase: `llm4pol.data` imports nothing from `llm4pol.loop`, `llm4pol.evaluate`, `llm4pol.llm` (they do not exist yet; `[tool.importlinter]` has zero contracts until Phase 3).
- mypy is `strict` with `packages = ["llm4pol"]`: every new module needs full annotations; third-party imports need stubs (`types-pyyaml`) or `py.typed` (pandas-stubs is not in the env — pandas ships no `py.typed`; expect `ignore_missing_imports`-free code to fail on `import pandas` unless mypy already tolerates it — **verify in the first plan task by running the gate on a skeleton module**; `[ASSUMED]` A5).

## Standard Stack

### Core

| Library | Version (locked) | Purpose | Why Standard |
|---------|------------------|---------|--------------|
| `huggingface_hub` | 1.32.0 `[VERIFIED: pixi env]` | `hf_hub_download` with `revision` + `local_dir`; `HfApi.dataset_info` / `get_paths_info` for remote sha256 | Already locked by FOUND-02; the dataset card itself documents this route |
| `pandas` | 3.0.5 | CSV read with dtype map, groupby aggregation | Claude's discretion: pandas is fine at 197 MB (2.2 s) |
| `pyarrow` | 25.0.0 | Declared schema, `write_table`, `read_schema` | The parquet engine pandas uses; schema assertion needs the Arrow object |
| `rdkit` | 2026.03.6 | `MolFromSmiles` / `MolToSmiles(canonical=True, isomericSmiles=True)` | Locked in D-03; verified on the whole file |
| `jsonschema` | 4.26.0 | Draft 2020-12 validation of the registry instance and of `MANIFEST-open` parsing tests | Already in the env; the precedent check step uses it |
| `pyyaml` | 6.0.3 (transitive today) | `yaml.safe_load` of the registry instance | Precedent (`calfcheck`); must be declared (F-46) |
| `hashlib`, `tomllib`, `argparse`, `pathlib` | stdlib | sha256, `[tool.llm4polcheck]` parsing, CLI | No dependency needed |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `types-pyyaml` | 6.0.12.20260906 (conda-forge) | mypy stubs for `yaml` | Required the moment `llm4pol.data.registry` imports `yaml` under `mypy --strict` (F-46) |
| `scipy` | 1.18.0 | `spearmanr` for the optional rank-correlation confirmation | Only if the report reproduces F-11 |
| `numpy` | 2.5.3 | quantiles, std | via pandas |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| pandas `read_csv` | `pyarrow.csv.read_csv` | faster, but the per-column dtype map and NaN-string handling are easier in pandas; 2 s is already fine |
| YAML registry instance | JSON instance | avoids `pyyaml`/`types-pyyaml`; **rejected** — D-05 locks YAML and the precedent triad |
| `groupby(...).agg` | polars | not in the env |

**Installation** (edit `env/pixi.toml`, then `pixi install --manifest-path env/pixi.toml` re-locks; commit `pixi.lock`):
```toml
[feature.base.dependencies]
pyyaml = "*"          # explicit; today only transitive via huggingface_hub
[feature.dev.dependencies]
types-pyyaml = "*"    # mypy --strict stubs for `import yaml`
```

**Version verification:** all versions above were read from the locked environment this session (`importlib.metadata`), not from training data. `pixi search` confirmed `types-pyyaml 6.0.12.20260906` and `pyyaml 6.0.3` on conda-forge `[VERIFIED: pixi search]`.

## Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| `pyyaml` | PyPI / conda-forge | 2006-era project; 6.0.3 published 2025-09-25 | unknown to the seam | pyyaml.org (github.com/yaml/pyyaml) | seam: `SUS` (reason: `unknown-downloads` only) | **Approved** — canonical package, already in `pixi.lock` as a `huggingface_hub` dependency; no postinstall concept on conda |
| `types-pyyaml` | PyPI / conda-forge | typeshed stubs, re-published on a dated cadence (latest 2026-09-06) | unknown to the seam | github.com/python/typeshed | seam: `SUS` (`too-new`, `unknown-downloads`) | **Approved with note** — "too new" is the typeshed release cadence, not a squat; conda-forge build exists. Planner may add a `checkpoint:human-verify` before the lock edit if it wants to be strict |

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** `pyyaml`, `types-pyyaml` — both flagged only because the seam could not read PyPI download counts; both confirmed on conda-forge via `pixi search` and (pyyaml) already present in the committed lock file.

## Architecture Patterns

### System Architecture Diagram

```
                      Hugging Face Hub (dataset yhayashi1986/PolyOmics @ 041e5834)
                                   │  hf_hub_download(revision=sha, local_dir=…)
                                   │  HfApi.get_paths_info → lfs.sha256 (CSV only)
                                   ▼
   data/MANIFEST-open.sha256 ──►  fetch  ──► data/raw/polyomics/<sha>/{csv, README.md, .cache/}
   (sha256, size, revision)        │  local sha256 + size == manifest ? else exit 1
                                   ▼
                      load ── read_csv(dtype map) ─► exclude smiles_2 rows (count) ─► identity (canonical_psmiles,
                       │                                                             candidate_id, parse failures count)
                       │        ┌──── declared pyarrow schema (registry + identity + added columns; rest pass-through)
                       ▼        ▼
          data/processed/polyomics-<sha>.parquet   (row level, every row, every column, + row_index)
                       │
                       ▼   groupby(candidate_id) → median / n / min / max / std(ddof=1) per registry property
          data/processed/candidates-<sha>.parquet (one row per candidate_id)
                       │
                       ▼
   protocol/property-registry_v1.yaml ──► validate ──► docs/audit/polyomics-<sha>-validation.md
   (columns, units, ranges, filters)        │  ladders: population → filter step → count
                                            │  expected vs observed (95,335 / 78,379 / 43,561 / 88.9 % / 0)
                                            │  noise floor, feasible set, tg_rmse ladder
                                            ▼
                                   exit 0 | 1 (finding contradicts expected) | 2 (IO)
```

### Recommended Project Structure

```
src/llm4pol/data/
├── __init__.py        # public surface only
├── __main__.py        # argparse: fetch | load | validate, --root; exit codes 0/1/2
├── snapshot.py        # POLYOMICS_REPO, POLYOMICS_REVISION, FILES, snapshot_id(), paths(root)
├── fetch.py           # hf_hub_download per file; manifest parse (same format as MANIFEST.sha256); sha256+size check
├── schema.py          # DECLARED_FIELDS (pa.field list), full_schema(inferred), cast_declared(table)
├── identity.py        # canonical_psmiles(smiles) -> str | None; candidate_id(canonical, tacticity) -> str; UNKNOWN_TACTICITY
├── registry.py        # load_registry(path) -> Registry (yaml.safe_load + jsonschema.validate); typed accessors
├── load.py            # read_csv(dtype map) → scope exclusion → identity → parquet; candidates parquet
└── validate.py        # populations, filter ladders, expected/observed table, markdown writer
protocol/
├── property-registry_v1.yaml
├── property-registry_v1.provenance.yaml
└── schemas/property-registry.json          # D-05 name; JSON Schema draft 2020-12
data/MANIFEST-open.sha256
docs/audit/polyomics-041e5834-validation.md
tests/
├── conftest.py                 # + synthetic_csv fixture (tmp_path), real_csv fixture (skip if absent)
├── test_data_fetch.py          # manifest parsing, sha256 mismatch → exit 1, no network (monkeypatch hf_hub_download)
├── test_data_schema.py         # declared fields present with declared types after load; parquet schema equals
├── test_data_identity.py       # canonical/stereo/`*`/unknown-tacticity/id length; known vectors
├── test_data_registry.py       # A-7 absent; schema validates instance; units status enum; every key has column in CSV header
├── test_data_invariants.py     # D-7 unique candidate ids; D-8 no train_test_split import; D-9/D-10 report content; Maxwell identity
└── test_data_real_file.py      # skips without the file: 95,335 / 78,379 / 43,561 / 88.83 % / identity residual / noise floor
```

### Pattern 1: Manifest line format reused from `data/MANIFEST.sha256`

**What:** `<sha256>  <size_bytes>  <filename>` per line, `#` comments; add a `# revision: 041e5834…` header and `# source: https://huggingface.co/datasets/yhayashi1986/PolyOmics/tree/041e5834…` comment. Parse with the same 3-field split `tests/test_manifest.py::_parse_manifest` uses so one parser can serve both manifests (move it into `llm4pol.data.fetch` and let the test import it).
**When to use:** DATA-01. Verified content (F-02, F-03):
```
# data/MANIFEST-open.sha256 -- PolyOmics general_polymers at one pinned Hugging Face revision (CC BY 4.0, never committed for size)
# revision: 041e5834ea1a48682fae12dc39ccd723bcd4f771
# source: https://huggingface.co/datasets/yhayashi1986/PolyOmics  (repo_type=dataset)
# Format: <sha256>  <size_bytes>  <filename>   (files live under data/raw/polyomics/<revision>/)
71e955ac1e90574ad009ccbf1238e595cf42905f3e600523ba2a6ea65c350213  196910783  general_polymers_with_sp_abbe_dynamic-dielectric.csv
c2340252a720f7b9f56fcc368105d9e1e351c2bd75f31a364f7c2afcb5a6cc13  15532  README.md
```

### Pattern 2: Fetch with a pinned full commit hash and local verification

```python
# Source: huggingface_hub docs (guides/download.md, quick-start.md) via Context7; behaviour verified in file_download.py
from huggingface_hub import hf_hub_download

path = hf_hub_download(
    repo_id="yhayashi1986/PolyOmics",
    repo_type="dataset",
    filename="general_polymers_with_sp_abbe_dynamic-dielectric.csv",
    revision=POLYOMICS_REVISION,          # full 40-hex sha: enables the offline fast path
    local_dir=root / "data" / "raw" / "polyomics" / POLYOMICS_REVISION,
)
# hf_hub_download never hashes the payload -> do it here, streaming 1 MiB chunks, compare to MANIFEST-open
```
Optional pre-flight (network): `HfApi().get_paths_info(repo_id, [csv], repo_type="dataset", revision=sha)[0].lfs.sha256` must equal the manifest — useful as a `--check-remote` flag, not required for the gate.

### Pattern 3: Declared-subset pyarrow schema with cast

```python
# Source: verified in the pixi env (F-42, F-43)
import pyarrow as pa, pyarrow.parquet as pq

DECLARED = [
    pa.field("UUID", pa.string()), pa.field("smiles_list", pa.string()), pa.field("smiles_2", pa.string()),
    pa.field("tacticity", pa.string()),
    pa.field("thermal_conductivity", pa.float64()), pa.field("dielectric_const_dc", pa.float64()),
    pa.field("tg", pa.float64()), pa.field("tg_rmse", pa.float64()), pa.field("Rg", pa.float64()),
    pa.field("r2", pa.float64()), pa.field("fractional_free_volume", pa.float64()),
    pa.field("sp_ced", pa.float64()), pa.field("density", pa.float64()), pa.field("refractive_index", pa.float64()),
    pa.field("static_dielectric_const", pa.float64()),          # kept as a column, never a registry property (A-7)
    pa.field("check_tc", pa.bool_()), pa.field("temp", pa.float64()), pa.field("forcefield", pa.string()),
    pa.field("candidate_id", pa.string()), pa.field("canonical_psmiles", pa.string()), pa.field("row_index", pa.int64()),
]

def cast_declared(table: pa.Table) -> pa.Table:
    schema = table.schema
    for field in DECLARED:
        schema = schema.set(schema.get_field_index(field.name), field)   # pandas 3 'str' arrives as large_string
    return table.cast(schema)                                             # wrong type -> ArrowInvalid

table = cast_declared(pa.Table.from_pandas(df, preserve_index=False))
table = table.replace_schema_metadata({**(table.schema.metadata or {}), b"llm4pol.snapshot": SNAPSHOT_ID.encode()})
pq.write_table(table, out_path)   # Snappy by default; 64 MB
```
The dtype map for `read_csv` mirrors DECLARED (`"float64"`, `"str"`, `"boolean"` for `check_tc`/`do_TC`). Do **not** declare `n_atom`, `mol_weight` numeric (F-41).

### Pattern 4: Identity, total and pure

```python
# Source: RDKit docs (MolToSmiles isomeric by default since 2018.03); verified on all 78,378 SMILES (F-32..F-37)
import hashlib
from rdkit import Chem, RDLogger
RDLogger.DisableLog("rdApp.*")            # 0 failures on the file, but keep the log quiet for synthetic bad inputs
UNKNOWN_TACTICITY = "unknown"

def canonical_psmiles(smiles: str) -> str | None:
    mol = Chem.MolFromSmiles(smiles)
    return None if mol is None else Chem.MolToSmiles(mol, canonical=True, isomericSmiles=True)

def candidate_id(canonical: str, tacticity: str | None) -> str:
    tac = UNKNOWN_TACTICITY if tacticity is None or tacticity != tacticity else tacticity   # NaN-safe
    return hashlib.sha256(f"{canonical}|{tac}".encode("utf-8")).hexdigest()[:16]
```
Known vectors for the test (computed this session): `*C(C*)(C)C(=O)OC` and `*C(C*)(C(=O)OC)C` → `*CC(*)(C)C(=O)OC`; `*/C(=C/CC*)C` → `*CC/C=C(/*)C`; the comma-joined cellulose `smiles_list` → `None`.

### Pattern 5: Validator as a ladder of named populations

```python
# Own design; the numbers are F-08, F-13, F-14
Step = tuple[str, "pd.Series[bool]"]   # (label, mask)
ladder: list[Step] = [
    ("all rows", all_rows),
    ("thermal_conductivity non-null", tc),
    ("∧ dielectric_const_dc non-null", tc & eps.notna()),
    ("∧ dielectric_const_dc ≤ 20 (physical)", tc & eps.between(1, 20)),
    ("∧ tg ∈ [100, 900] K", tc & eps.between(1, 20) & tg.between(100, 900)),   # == 43,561 expected
    ("∧ check_tc == True (protocol)", ...),                                      # 42,733
    ("∧ tg_rmse ≤ 0.1 (protocol)", ...),
]
# each row of the report: label | population it filters | count | expected (if any) | status ok/differs
```
Every count line carries its population name (D-10); expected values live in one table in `validate.py` (`EXPECTED = {"rows": 95335, "unique_smiles": 78379, "triple": 43561, "static_maxwell_pct": 88.9, "dc_maxwell_violations": 0}`) and each becomes `reproduced` / `differs (observed X, documented)`; exit 1 only when a `reproduced`-class expectation fails (rows, unique smiles, triple), exit 0 with `differs` for the two documented ones — or, cleaner, mark the two as `expected_documented_difference` with the observed value from this research so any *further* drift fails.

### Pattern 6: `[tool.llm4polcheck]` + `schema-inventory` step (port of `validate_inventory`)

Port `C:/Users/molsim/Desktop/CALF20_DiscoveryLoop/scripts/check.py::validate_inventory` verbatim with `calfcheck` → `llm4polcheck`: `tomllib.load(pyproject)`; missing table → failure; per entry `name`, `instances` (glob), `schema`, `required`; `.yaml`/`.yml` → `yaml.safe_load`, else `json.load`; `jsonschema.validate`; print `"llm4polcheck inventory: N entries, M instances processed"`. Append `("schema-inventory", step_schema_inventory)` to `STEPS` after `import-linter`. Note `scripts/` is not under mypy (`packages = ["llm4pol"]`), so the step can import `yaml` without stubs; `ruff` does check `scripts/`.

```toml
[tool.llm4polcheck]
validated = [
    { name = "property registry v1 (DATA-03, A-7)", instances = "protocol/property-registry_v1.yaml", schema = "protocol/schemas/property-registry.json", required = true },
]
```

### Pattern 7: Registry triad skeleton

`protocol/property-registry_v1.yaml` (values from F-20..F-31, F-67; thresholds in `filters` are protocol decisions):
```yaml
schema_version: 1
registry_version: v1
snapshot: polyomics:general_polymers@041e5834ea1a48682fae12dc39ccd723bcd4f771
condition: {temperature_K: 300, pressure_atm: 1, forcefield: GAFF2_mod, charges: RESP, state: isotropic_amorphous}
properties:
  thermal_conductivity: {column: thermal_conductivity, unit: "W/(m*K)", unit_status: verified, role: objective,
                         physical_range: [0.0, 2.0], filters: {check_tc: true}}
  dielectric_const_dc:  {column: dielectric_const_dc, unit: "1", unit_status: verified, role: constraint,
                         physical_range: [1.0, 20.0]}
  tg:                   {column: tg, unit: K, unit_status: verified, role: constraint,
                         physical_range: [100.0, 900.0], filters: {tg_rmse_max: 0.1}}
  rg:                   {column: Rg, unit: angstrom, unit_status: verified, role: intermediate, physical_range: [0.0, 200.0]}
  r2:                   {column: r2, unit: "nm^2", unit_status: unverified, role: validator, physical_range: [0.0, 2000.0]}
  ffv:                  {column: fractional_free_volume, unit: "1", unit_status: verified, role: intermediate, physical_range: [0.0, 1.0]}
  sp_ced:               {column: sp_ced, unit: "MPa", unit_status: verified, role: intermediate, physical_range: [0.0, 2000.0]}
  density:              {column: density, unit: "g/cm^3", unit_status: verified, role: intermediate, physical_range: [0.5, 2.5]}
  refractive_index:     {column: refractive_index, unit: "1", unit_status: verified, role: validator, physical_range: [1.0, 3.0]}
```
`protocol/schemas/property-registry.json`: `$schema` 2020-12, `additionalProperties: false` at root, `properties.properties.propertyNames.enum` = exactly the nine keys (A-7 by construction — `static_dielectric_const` fails `propertyNames`, verified F-45), each entry `required: [column, unit, unit_status, role, physical_range]`, `unit_status: {enum: [verified, unverified]}`, `role: {enum: [objective, constraint, intermediate, validator]}`, `physical_range: {prefixItems: [number, number], items: false, minItems: 2, maxItems: 2}`, `filters` an object with `additionalProperties: false` listing only `check_tc` (boolean) and `tg_rmse_max` (number). `protocol/property-registry_v1.provenance.yaml`: one entry per leaf with `provenance_class` ∈ {`paper_or_source` (F-20..F-29 evidence), `protocol_decision` (ranges, thresholds), `unresolved` (`r2` unit)} — mirror the CALF20 `partition_v1.provenance.yaml` shape and add a test that the leaf-path sets of instance and provenance are equal (precedent's second verify command). Write floats with a decimal point (`1.0e-3` never `1e-3`, F-47).

### Anti-Patterns to Avoid
- **`groupby(["smiles_list", "tacticity"])` with the default `dropna=True`:** silently discards the 554 NaN-tacticity rows (F-48). Map to `"unknown"` first (D-03) or pass `dropna=False`.
- **Using `smiles_search` as identity:** it is a cyclised oligomer with stereo stripped (F-36) — the D-6 false-merge key.
- **Treating "0 Maxwell violations" as a physics check:** it is the F-14 identity. Test the identity residual instead.
- **Mean instead of median for candidate values:** replicate groups contain `check_tc == False` outliers 100× the median (F-57).
- **Declaring `pa.string()` and asserting equality on a `from_pandas` table without casting:** it is `large_string` (F-42).
- **Declaring `n_atom`, `mol_weight` as numeric:** they are `/`-joined per-chain strings (F-41).
- **Relying on `hf_hub_download` to detect corruption:** the fast path returns an existing file on a commit-hash match without hashing (Q5).
- **`git hash-object` without `--no-filters` to compare with HF `blob_id`:** `core.autocrlf=true` changes the hash (F-04).
- **Fixing D-16 in the report:** state the feasible-set size under the development defaults and label it "input to the D-16 gate"; never write "threshold = 2.65" as a decision (charter §13, ADR-0005).
- **Copying real rows into a test fixture:** forbidden by `data/README.md`; invent ≤ 20 rows.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Pinned download with resume/offline fast path | urllib + retry loop | `hf_hub_download(revision=sha, local_dir=…)` | handles etag, xet, locks, offline fast path; already locked (FOUND-02) |
| Remote LFS sha256 lookup | scraping the web page | `HfApi.get_paths_info` / `dataset_info(files_metadata=True)` | typed `BlobLfsInfo.sha256` |
| SMILES canonicalisation / stereo | regex normalisation | RDKit `MolToSmiles(canonical=True, isomericSmiles=True)` | verified on 78,378 strings, stereo preserved |
| Schema validation of YAML/JSON protocol files | ad-hoc key checks | `jsonschema` Draft 2020-12 + `propertyNames`/`prefixItems` | A-7 becomes a schema rule, not code |
| Parquet typing | pickles / CSV copies | pyarrow declared fields + `cast` | `ArrowInvalid` on drift; schema readable without loading data |
| Manifest parsing | new format | reuse `_parse_manifest` from `tests/test_manifest.py` (moved into `llm4pol.data.fetch`) | one parser for both manifests |
| Check-step inventory | custom validator runner | port `validate_inventory` from CALF20 `scripts/check.py` | proven; identical failure semantics (missing table = failure) |

**Key insight:** every hard part of this phase is a *counting* problem on a fixed file; the value is in naming populations and printing ladders, not in clever code.

## Runtime State Inventory

Not a rename/refactor phase — omitted. (The only runtime state this phase creates is `data/raw/polyomics/<sha>/`, `data/processed/*.parquet` — all git-ignored — and the committed report.)

## Common Pitfalls

### Pitfall 1: Reproducing 88.9 % and 0 literally
**What goes wrong:** the validator loops over filters trying to hit 88.9 % and treats `ε_dc ≥ n²` as a real check.
**Why it happens:** the README rounded 88.83 % up (or used a slightly different population), and `ε_dc` is *defined* as `ε_s − 1 + n²` (F-13, F-14).
**How to avoid:** expected table carries `88.9 (documented: 88.83 % on the 43,561 triple rows; 84.30 % on all 93,488 rows)` and `0 (identity: max |ε_dc − (ε_s − 1 + n²)| = 5.7e-7)`; exit 0 with the difference printed. Correct the narrative: `static_dielectric_const` is the orientational (non-polarizable MD) permittivity, `dielectric_const_dc` adds the electronic part `n² − 1` — A-7 still picks the corrected column.
**Warning signs:** a plan task saying "find the filter that gives 88.9 %".

### Pitfall 2: 43,561 vs 43,560 vs 40,212
**What goes wrong:** three "triple counts" appear and get mixed.
**Why:** 43,561 is on all rows; 43,560 after excluding the 3 cellulose rows (one is in the triple); 40,212 is candidates after dedup (F-08, F-61).
**How to avoid:** each has a population label; the report prints all three; the Phase 3 hidden-table size is the candidate-level number.

### Pitfall 3: NaN tacticity and the 303 twins
**What goes wrong:** the identity test expects 2 multi-tacticity SMILES (CONTEXT.md) and gets 303.
**Why:** CONTEXT's 2 came from pandas dropping NaN group keys; D-03's `"unknown"` makes the 554 rows visible (F-39, F-48).
**How to avoid:** report both counts with their definitions; keep D-03 as locked (total, deterministic id); raise Open Question 1 for the owner.

### Pitfall 4: `tg_rmse` is not kelvin
**What goes wrong:** a threshold like "rmse ≤ 5 K" is written into the registry.
**Why:** the name suggests RMSE; it is `sum(square(density residuals))` (F-23).
**How to avoid:** registry unit `"(g/cm^3)^2"`, description "sum of squared density residuals of the two-line fit", threshold pinned as a protocol decision with the ladder (F-65) printed.

### Pitfall 5: `check_tc` and the TC outliers
**What goes wrong:** candidate medians or the top-decile window include 19 W/(m·K) runs.
**Why:** 108 of the 109 TC > 1 rows are `check_tc == False` (F-59); the README's 43,561 does not filter them.
**How to avoid:** registry `filters: {check_tc: true}` for TC as a protocol filter; report both the 43,561 reproduction (without) and 42,733 (with). Whether the Phase 3 hidden table applies it is an owner decision (Open Question 2).

### Pitfall 6: mypy strict on new third-party imports
**What goes wrong:** the gate fails on `import yaml` (no stubs) or on pandas/pyarrow typing.
**Why:** `[tool.mypy] strict = true`, `packages = ["llm4pol"]`; `types-pyyaml` absent (F-46); pandas has no bundled stubs `[ASSUMED]`.
**How to avoid:** first plan task adds `pyyaml` + `types-pyyaml` to `env/pixi.toml`, re-locks, and runs the gate on a skeleton `llm4pol/data/__init__.py` that imports pandas/pyarrow/rdkit/yaml — surfacing any `ignore_missing_imports` need before real code exists.

### Pitfall 7: Windows path length and `.cache`
**What goes wrong:** `hf_hub_download` creates `data/raw/polyomics/<40-hex>/.cache/huggingface/download/<long name>.csv.metadata` (already there); `.gitignore` covers `data/raw/` so nothing leaks, but `ruff`/`pytest` collection must not descend into `data/` (ruff already excludes `data`; pytest `testpaths = ["tests"]`).
**How to avoid:** nothing to do beyond not adding `data/` to any glob.

## Code Examples

### Reading the CSV with the declared dtype map (verified 2.1 s)
```python
# Source: verified in the pixi env (F-40, F-41)
DTYPES: dict[str, str] = {
    "UUID": "str", "smiles_list": "str", "smiles_1": "str", "smiles_2": "str", "tacticity": "str",
    "RadonPy_ver": "str", "forcefield": "str",
    "thermal_conductivity": "float64", "dielectric_const_dc": "float64", "tg": "float64", "tg_rmse": "float64",
    "Rg": "float64", "r2": "float64", "fractional_free_volume": "float64", "sp_ced": "float64",
    "density": "float64", "refractive_index": "float64", "static_dielectric_const": "float64",
    "temp": "float64", "press": "float64", "check_tc": "boolean", "do_TC": "boolean",
}
df = pd.read_csv(csv_path, low_memory=False, dtype=DTYPES)
df["row_index"] = range(len(df))
scope = df["smiles_2"].isna()                      # 95,332 True / 3 False
```

### Candidate table (D-04)
```python
# Source: own design; numbers F-50, F-55
g = rows.groupby("candidate_id", sort=True)
agg = {p: ["median", "count", "min", "max", "std"] for p in REGISTRY_COLUMNS}   # std is ddof=1 in pandas
cand = g.agg(agg)
cand.columns = [f"{p}_{stat}" for p, stat in cand.columns]
cand["n_rows"] = g.size()
noise = {p: (cand.loc[cand[f"{p}_count"] >= 2, f"{p}_std"] / cand.loc[cand[f"{p}_count"] >= 2, f"{p}_median"].abs()).median()
         for p in REGISTRY_COLUMNS}               # → TC 0.0369, ε_dc 0.0084, tg 0.0577 on all candidates
```

### Real-file skip pattern (mirrors `tests/test_manifest.py`)
```python
# Source: tests/test_manifest.py::test_raw_files_match_manifest (this repo)
import pytest
from llm4pol.data.snapshot import POLYOMICS_REVISION, CSV_NAME
RAW = ROOT / "data" / "raw" / "polyomics" / POLYOMICS_REVISION / CSV_NAME

@pytest.fixture(scope="session")
def real_csv() -> Path:
    if not RAW.is_file():
        pytest.skip(f"pinned PolyOmics file absent at {RAW} (never committed; run `python -m llm4pol.data fetch`)")
    return RAW
```

### Maxwell identity test (replaces a naive ε ≥ n² check)
```python
# Source: F-14, F-15
resid = (df.dielectric_const_dc - (df.static_dielectric_const - 1 + df.refractive_index**2)).abs()
assert resid.max() < 1e-5                       # identity holds on all 93,488 rows (observed 5.7e-7)
assert (df.static_dielectric_const >= 1).all()  # hence ε_dc ≥ n² everywhere
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| pandas `object` strings | pandas 3.0 `str` dtype (pyarrow-backed, NaN missing) | pandas 3.0 (2026) | Arrow `large_string`; `groupby`/`str` accessors use RE2 regex (a `\` inside a character class raised `ArrowInvalid` this session) |
| `MolToSmiles(isomericSmiles=True)` explicit | isomeric by default | RDKit 2018.03 | explicit kwargs still fine (D-03) |
| HF cache symlinks | `local_dir` with `.cache/huggingface` metadata sidecar | huggingface_hub ≥ 0.23 | the fast path and `.metadata` layout in F-05 |

**Deprecated/outdated:** `jsonschema.__version__` (DeprecationWarning — use `importlib.metadata.version("jsonschema")`); `hf_hub_download(local_dir_use_symlinks=…)` (removed; not needed).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | 73,045 in the dataset card equals the paper's Table S2 per-class "unique chemical structures" sum (≈ 73,046 in a pdftotext extraction) | F-19 | none for the gate — the report only needs "not reproducible from the file" plus the card provenance; wording of one sentence |
| A2 | `r2` is stored in nm² (data-consistency argument) while the paper's Table S3 says Å² | F-25 | `r2` is a validator/intermediate only; registry marks it `unverified`; no plan numbers depend on it |
| A3 | `tg_rmse ≤ 0.1` as the development default threshold | F-66, registry skeleton | changes the Tg-filtered count (42,232 vs 43,316 at 0.2); owner may pick another rung of the printed ladder |
| A4 | Physical ranges in the registry skeleton (TC [0, 2], density [0.5, 2.5], RI [1, 3], Rg [0, 200], sp_ced/r2 upper bounds) | Pattern 7 | only affect the "physical-range filter counts" section; not the 43,561 reproduction |
| A5 | mypy strict will need `ignore_missing_imports`/stubs for pandas or pyarrow | Project Constraints, Pitfall 6 | one extra pyproject line; verified by the first plan task's gate run |
| A6 | The Phase 3 hidden table should apply `check_tc == True` (42,733 rows) rather than the README's 43,561 | F-59, Open Q2 | owner decision; the report prints both so nothing is lost either way |
| A7 | RadonPy's produced-file pipeline rescaled Rg to Å (the fetched `Analyze` branch shows no `×10`) | F-24 | none — the unit in the *file* is settled by Table S3 and the data; this only concerns why |

## Open Questions (RESOLVED)

Resolved on 2026-09-22 as development defaults in `02-CONTEXT.md` § Decisions after 02-RESEARCH.md
(owner unavailable; each stays raised for the owner as the plans state):

- Q1 (303 `unknown`-tacticity twins) → **R-1**: NaN tacticity maps to `"unknown"` and stays a separate candidate in M1; the report prints both the with-twins and folded counts; raised before Phase 3.
- Q2 (`check_tc == True` in the hidden table) → **R-2**: the report prints the README triple (43,561) and the quality-filtered triple (`check_tc`, 42,733) side by side; the choice is a Phase 3 decision; the `tg_rmse` ladder is recorded with no cut applied in M1.
- Q3 (`r2` unit conflict) → **R-4**: registry `unit_status: unverified` for `r2` with both candidate units stated; every other unit `verified`.
- Q4 (exit-code policy for documented differences) → **R-5**: two finding classes, `reproduce` (exact) and `documented` (stated difference with tolerance: Maxwell share 88.83 % ± 0.05, identity residual < 1e-5); any other drift exits 1.

The original questions are kept below for the record.

1. **The 303 `unknown`-tacticity twins (F-39).** D-03 maps NaN → `"unknown"`, so 303 repeat units get a second `candidate_id` whose rows are older-workflow runs of a polymer that also exists with `none`/`atactic`. Options: keep as locked (two candidates; report the count) or, in a later ADR, fold `unknown` into the unique known tacticity of the same canonical when exactly one exists. Recommendation: keep D-03 for M1 (total, deterministic); print the 303 and the 2; raise for the owner before Phase 3 freezes the hidden table.
2. **Does the hidden table apply `check_tc == True`?** (F-59, A6). Recommendation: yes for Phase 3 (physical TC), documented as a registry `filters` entry with the count; the 43,561 reproduction stays as the README check.
3. **`r2` unit conflict** (F-25). Recommendation: registry `unverified`; ask the PolyOmics community tab or check RadonPy's AutoMD data-export script if `r2` ever becomes a design variable (it is not in the A1 window list).
4. **Documented-difference policy for exit codes.** Should `validate` exit 1 when 88.83 % ≠ 88.9 %? Recommendation: the expected table distinguishes `reproduce` (rows, unique smiles, 43,561 → exit 1 on mismatch) from `documented` (88.9 %, 0, 73,045 → exit 0, print observed and the reason); a *further* drift from the observed values recorded here (88.83 %, residual < 1e-5) exits 1.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python (pixi default env) | everything | ✓ | 3.13.15 | — |
| huggingface_hub | fetch | ✓ | 1.32.0 | — |
| pandas / numpy / pyarrow | load, validate | ✓ | 3.0.5 / 2.5.3 / 25.0.0 | — |
| rdkit | identity | ✓ | 2026.03.6 | — |
| jsonschema | registry, check step | ✓ | 4.26.0 | — |
| pyyaml | registry | ✓ (transitive only) | 6.0.3 | declare explicitly (F-46) |
| types-pyyaml | mypy strict | ✗ | conda-forge 6.0.12.20260906 | add to dev feature; or `[[tool.mypy.overrides]] ignore_missing_imports` for `yaml` (weaker) |
| pytest / ruff / mypy / import-linter | gate | ✓ | 9.1.1 / – / – / 2.15 | — |
| Network to huggingface.co | fetch (first run only) | ✓ this session | — | files already present → offline fast path |
| Pinned files on disk | real-file tests | ✓ | 196,910,783 B + 15,532 B, hashes match | tests skip when absent (CI) |
| Git with `fetch-depth: 0` in CI | history scan (unchanged) | ✓ | — | — |
| pdftotext (mingw64) | research only | ✓ | — | not needed by the plan |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** `types-pyyaml` (add to lock).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.1.1 (`[tool.pytest.ini_options] testpaths = ["tests"], addopts = "-q"`) |
| Config file | `pyproject.toml` |
| Quick run command | `pixi run --manifest-path env/pixi.toml python -m pytest tests/test_data_identity.py -x` (any single file; `PYTHONPATH=src` is set by the pixi task — when calling pytest directly set `PYTHONPATH=src`, otherwise `llm4pol` fails to import at collection, as observed this session) |
| Full suite command | `pixi run --manifest-path env/pixi.toml check` (baseline today: 6/6 steps — ruff check, ruff format --check, mypy, import-linter, history-secret-scan, pytest — 26 tests; Phase 2 adds `schema-inventory` as the seventh) |

### What runs where

| Layer | Runs in CI (no file) | Runs locally with the pinned file | Mechanism |
|---|---|---|---|
| Manifest parse, sha256/size mismatch → exit 1, `hf_hub_download` not called when files verify | ✓ | ✓ | `tmp_path` files with known bytes; `monkeypatch` `llm4pol.data.fetch.hf_hub_download` to a fake that writes bytes |
| Loader dtype map, scope exclusion, `row_index`, declared schema types, parquet round-trip | ✓ | ✓ | synthetic ≤ 20-row CSV written by the fixture carrying only the declared columns (registry + identity + `smiles_2`, `check_tc`, `tg_rmse`, `static_dielectric_const`), not all 259 — so the loader must treat undeclared columns as optional pass-through and declare only what it needs |
| Identity vectors (merges, stereo kept, `*` kept, `unknown`, 16-hex id, cellulose list → None) | ✓ | ✓ | pure functions, known vectors from F-35 |
| Registry: instance validates; A-7 absent; nine keys; every `column` exists in the loader's declared columns; `unit_status` enum; provenance leaf sets equal | ✓ | ✓ | jsonschema + yaml on the committed files |
| `schema-inventory` check step: missing table → failure; zero-match required glob → failure | ✓ | ✓ | run `validate_inventory(tmp_root)` on temp pyproject copies (precedent tests) |
| D-7 unique `candidate_id` in candidate table; D-8 no `train_test_split`/`sklearn.model_selection` import under `llm4pol.data` (AST or `importlinter`-free grep of source); D-9 report contains "noise floor" table; D-10 every count line names a population | ✓ (synthetic) | ✓ | validator run on the synthetic parquet; markdown parsed for the required sections |
| Maxwell identity (F-14) | ✓ (synthetic rows constructed to satisfy it) | ✓ (max residual < 1e-5 on 93,488 rows) | same test, parametrised over both fixtures |
| Expected numbers: 95,335 × 259; 78,379 unique `smiles_list`; 78,373 canonical; 78,676 candidates; 43,561 / 43,560 / 40,212; 88.83 %; noise floor TC 0.0369 ± tolerance; feasible 6,793 | ✗ skipped | ✓ | `real_csv` fixture skips with reason when absent (Pattern above) — identical to `tests/test_manifest.py` |
| Sha256 of the committed report? | ✗ | — | not a test: the report is an artifact; a test asserts it exists, names the revision and has the required section headings |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DATA-01 | fetch verifies sha256+size against `MANIFEST-open`; mismatch exits 1; no network when present | unit (monkeypatched) + real-file | `pytest tests/test_data_fetch.py -x` | ❌ Wave 0 |
| DATA-02 | parquet written with declared schema; identifier string | unit + real-file | `pytest tests/test_data_schema.py -x` | ❌ Wave 0 |
| DATA-03 | registry validates; nine keys; A-7 absent; units/status | unit | `pytest tests/test_data_registry.py -x` | ❌ Wave 0 |
| DATA-04 | canonical + id vectors | unit | `pytest tests/test_data_identity.py -x` | ❌ Wave 0 |
| DATA-05 | candidate table median/n/min/max/std; unique ids | unit + real-file | `pytest tests/test_data_invariants.py -x -k candidates` | ❌ Wave 0 |
| DATA-06 | report reproduces/documents the five numbers | real-file (skip in CI) + unit on section presence | `pytest tests/test_data_real_file.py -x` | ❌ Wave 0 |
| DATA-07 | noise-floor table present with TC/ε_dc/Tg | unit (synthetic) + real-file values | `pytest tests/test_data_invariants.py -x -k noise` | ❌ Wave 0 |
| DATA-08 | feasible-set line present, labelled "input to D-16", not a decision | unit (text) + real-file value | `pytest tests/test_data_invariants.py -x -k feasible` | ❌ Wave 0 |
| DATA-09 | tg window + rmse ladder counts in report | unit + real-file | `pytest tests/test_data_real_file.py -x -k tg` | ❌ Wave 0 |
| DATA-10 | D-7..D-10, A-7 tests exist and pass; INVARIANTS.md guard column updated | unit + doc grep | `pytest tests/test_data_invariants.py tests/test_governance.py -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pixi run --manifest-path env/pixi.toml check-fast` (skips mypy; ~10 s)
- **Per wave merge:** `pixi run --manifest-path env/pixi.toml check` (full, incl. mypy strict and the new `schema-inventory` step)
- **Phase gate:** full gate green on both CI platforms **and** the real-file tests green locally (they skip in CI) — the VERIFICATION.md must paste the local real-file run since CI cannot exercise charter M1 (2)–(5).

### Wave 0 Gaps
- [ ] `tests/conftest.py` — add `synthetic_csv` (tmp_path, ≤ 20 invented rows, deterministic) and `real_csv` (skip) fixtures
- [ ] `tests/test_data_fetch.py`, `test_data_schema.py`, `test_data_identity.py`, `test_data_registry.py`, `test_data_invariants.py`, `test_data_real_file.py`
- [ ] `env/pixi.toml`: `pyyaml`, `types-pyyaml`; re-lock; gate run on a skeleton module (Pitfall 6)
- [ ] `pyproject.toml`: `[tool.llm4polcheck]` table; `scripts/check.py`: `schema-inventory` step + its self-tests (port of the precedent's tests if any exist there)
- Framework install: none (pytest present)

## Security Domain

`security_enforcement` is enabled (ASVS level 1). This phase has no auth, session, or web surface; the relevant controls are input validation and supply-chain integrity.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | HF dataset is ungated; no token needed (`gated: False`); never read `.env` for this phase |
| V3 Session Management | no | — |
| V4 Access Control | no | — |
| V5 Input Validation | yes | jsonschema (registry, `additionalProperties: false`), manifest 3-field parse with `int()` and 64-hex check (existing test pattern), RDKit parse failure counted not raised, `argparse` with a fixed choice set for the CLI |
| V6 Cryptography | yes (integrity) | `hashlib.sha256` streaming; compare to committed manifest and to HF `lfs.sha256`; no hand-rolled hashing |
| V10 Malicious Code / supply chain | yes | packages only from the committed `pixi.lock`; the two new packages are audited above; no `postinstall` concept on conda |
| V14 Configuration | yes | no `shell=True`; paths built with `pathlib` under `--root`; `.cache/` and data dirs git-ignored |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Tampered or partially downloaded dataset file accepted | Tampering | sha256 + size vs manifest after every fetch; `hf_hub_download` fast path does not hash (Q5) |
| Silent revision drift (`main` moves) | Repudiation | full commit hash constant in one place; snapshot id embeds it; report prints it |
| YAML deserialisation of arbitrary objects | Elevation | `yaml.safe_load` only (never `yaml.load`) |
| Path traversal via `--root` / filenames | Tampering | filenames are constants; `local_dir` derived from `root / "data" / "raw" / …`; no user-supplied filenames |
| Secret leakage in logs | Information disclosure | phase reads no secrets; keep R-3 (never print env) |
| Committing data by accident | Information disclosure / licence | `.gitignore` already covers `data/raw/`, `data/processed/`; `tests/test_governance.py::test_data_directories_are_ignored` |

## Sources

### Primary (HIGH confidence)
- The pinned file `data/raw/polyomics/041e5834…/general_polymers_with_sp_abbe_dynamic-dielectric.csv` (sha256 `71e955ac…`) — all F-06..F-19, F-32..F-67 measured with pandas 3.0.5 / RDKit 2026.03.6 in the locked env, 2026-09-22
- Hugging Face API live (`HfApi.dataset_info`, `get_paths_info`) — F-01..F-03
- Locked pixi environment (`importlib.metadata`, `pixi search`, `mypy --strict` probe, parquet/jsonschema/yaml probes) — F-40..F-48, stack versions
- `C:/Users/molsim/Desktop/CALF20_DiscoveryLoop/scripts/check.py::validate_inventory`, `protocol/partition_v1.{yaml,schema.json,provenance.yaml}`, `pyproject.toml [tool.calfcheck]` — Patterns 6, 7
- This repo: `scripts/check.py`, `tests/test_manifest.py`, `tests/conftest.py`, `pyproject.toml`, `env/pixi.toml`, `env/pixi.lock` (line 3566), `.github/workflows/ci.yml`, `docs/MASTER-PLAN.md` §4/§6/§7/§9/§10/§13, `docs/governance/INVARIANTS.md`, ADR-0004, `docs/research/databases/README.md`

### Secondary (MEDIUM confidence)
- RadonPy source, `develop` branch, fetched 2026-09-22 via WebFetch (summarised, not read line-by-line): `radonpy/sim/preset/tc.py`, `sp.py`, `tg.py`, `radonpy/sim/lammps.py`, `radonpy/core/calc.py`; Context7 `/radonpy/radonpy` (AutoMD_scripts/README.md for `check_tc`/`do_TC`) — F-20..F-29
- arXiv:2511.11626 PDF (Yoshida, Hayashi, Furuya et al., submitted 2025-11-07), Supplementary Table S3 "Unit in the database" and Methods, extracted with `pdftotext` — F-20..F-29, F-14 definition, F-30
- Context7 `/huggingface/huggingface_hub` (`file_download._hf_hub_download_to_local_dir`, `_local_folder.write_download_metadata`, `HfApi.dataset_info`, `RepoFile/BlobLfsInfo`) — Q5
- Context7 `/websites/pandas_pydata` (3.0 whatsnew, migration-3-strings), `/apache/arrow` (parquet compression, `write_table`), `/python-jsonschema/jsonschema` (Draft202012Validator, validate), `/websites/rdkit` (MolToSmiles defaults) — Q6, Q7, Q4
- mdtraj `load_lammpstrj` docs (unit_set 'real', nm internal) — F-24 note

### Tertiary (LOW confidence)
- Table S2 per-class sums from the PDF text (A1); mdtraj/RadonPy rescaling story for Rg (A7)

## Metadata

**Confidence breakdown:**
- Facts about the file: HIGH — every number recomputed this session on the exact pinned bytes; scripts reproducible
- Units: HIGH for TC, Tg, density, sp_ced, ffv, RI, ε_dc (source + paper + data identity agree); MEDIUM for Rg (paper + data agree, RadonPy path unclear); LOW/unverified for `r2`
- Standard stack: HIGH — versions read from the lock; behaviours probed
- Architecture / patterns: HIGH — precedent files read; decisions locked in CONTEXT.md
- Pitfalls: HIGH — each one was hit or measured this session

**Research date:** 2026-09-22
**Valid until:** the pinned revision never changes, so the file facts are permanent; library behaviours (pandas 3 strings, hf fast path) 90 days; re-check `main` of the HF dataset only if a re-pin is ever proposed
