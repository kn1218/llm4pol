# Phase 2: Data Foundation — Context

**Gathered:** 2026-09-22
**Source:** charter `docs/MASTER-PLAN.md` §6, §7, §10, §13 M1; `docs/research/databases/README.md`
(the 2026-09-11 direct analysis); direct inspection of the pinned file on 2026-09-22 (facts below,
measured, not quoted); the CALF20 precedent's protocol triad convention
(`<name>_v1.yaml` + `.schema.json` + `.provenance.yaml`, validated by a check-step inventory in
`pyproject.toml`). No discuss-phase interview (owner unavailable); the charter is the input.
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 2 delivers charter M1: PolyOmics `general_polymers` pinned at one Hugging Face revision,
loaded into one parquet snapshot, identified per candidate, and validated by a report that is the
authority for every number cited later. It freezes the candidate definition, the property registry
and the snapshot identifier (charter §7).

**Measured on 2026-09-22 against the pinned revision (the plan's facts, to be reproduced by code):**

| Fact | Value |
|---|---|
| Dataset commit (HF `sha`) | `041e5834ea1a48682fae12dc39ccd723bcd4f771`, last modified 2026-09-03, licence `cc-by-4.0`, ungated |
| Config `general_polymers` → file | `general_polymers_with_sp_abbe_dynamic-dielectric.csv`, 196,910,783 bytes, sha256 `71e955ac1e90574ad009ccbf1238e595cf42905f3e600523ba2a6ea65c350213` |
| `README.md` | 15,532 bytes, sha256 `c2340252a720f7b9f56fcc368105d9e1e351c2bd75f31a364f7c2afcb5a6cc13`; states no units |
| Rows × columns | 95,335 × 259 (pandas `read_csv`, `low_memory=False`) |
| The "73,045" in `DB-computed.md` | is the README's own description line ("73,045 general polymers in the isotropic amorphous state"), not the file's row count. Resolved: the file has 95,335 rows; record both and their provenance |
| Structure columns | `smiles_list` (95,335 non-null, 78,379 unique) equals `smiles_1` on every row; `smiles_2..4` non-null on 3 rows only; `smiles_search` 78,364 unique (a normalised form); `copoly_ratio_list`, `copoly_type` exist |
| Tacticity | `none` 48,790 / `atactic` 45,032 / `isotactic` 951 / `syndiotactic` 8 / NaN 554 |
| Replicates | grouping by (`smiles_list`, `tacticity`) gives 78,682 groups; 12,984 groups have >1 row, max 17 rows. Example: the same repeat unit with TC 0.187 vs 0.130 W/(m·K) — replicate spread is large and must be reported (D-9). 2 SMILES appear with more than one tacticity |
| Conditions | `temp` 300 on every row, `press` 1, `forcefield` `GAFF2_mod`, `input_natom` 1000 (3 rows 2000), `input_nchain` 10 (1 row 5); `RadonPy_ver` 0.2.10/0.2.9/0.2.1/0.2.0b3; `preset_tg_ver` 0.1.3/0.1.1/0.1.0; `preset_tc_ver` present on 81,528 rows |
| Coverage | `thermal_conductivity` 81,405; `dielectric_const_dc` 93,488; `tg` 56,064 (with `tg_rmse`); `fractional_free_volume` 87,849; `sp_ced` 71,848; `Rg`, `density` 95,335; `refractive_index` 93,488 |
| Outliers | TC max 43.4 W/(m·K); `dielectric_const_dc` max 3,678; `fractional_free_volume` min −0.046; `tg` max 1.08e6 K; `tg_rmse` max 36.3 |
| Naive triple | TC ∧ ε_dc ∧ Tg∈[100, 900] K = **45,821**, not the README's 43,561 — the README's "physical `dielectric_const_dc`" filter is not stated; the validator must find the filter that reproduces 43,561 or document that it cannot |
</domain>

<decisions>
## Implementation Decisions

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
</decisions>

<specifics>
## Specific Ideas

- Precedent files to read for conventions: `C:/Users/molsim/Desktop/CALF20_DiscoveryLoop/scripts/check.py`
  (`step_schema_inventory`, `[tool.calfcheck]` parsing), `.../protocol/partition_v1.{yaml,schema.json,provenance.yaml}`
  (triad shape), `.../src/calfloop/ledger/identity.py` (hash conventions).
- The `docs/research/databases/README.md` numbers to reproduce: 95,335 / 78,379 / 43,561 /
  88.9 % / 0 / rank correlations table / window 1,140 (2.62 %). Reproduce the first five;
  the correlations are optional confirmation.
- Import boundary for this phase: `llm4pol.data` imports nothing from `llm4pol.loop`,
  `llm4pol.evaluate`, `llm4pol.llm` (they do not exist yet; add the contract when they do — Phase 3).
</specifics>

<deferred>
## Deferred Ideas

- OpenPoly / PoLyInfo loaders → M8 (D-17).
- `chi_parameter/` solvent tables and `MD_snapshot_JSON/` → not needed for M1–M7.
- Tag vocabulary (RDKit SMARTS) → Phase 5 (M4).
</deferred>

---

*Phase: 02-data-foundation*
*Context gathered: 2026-09-22 from the charter, the 2026-09-11 analysis and direct inspection of the pinned file*

<post_research_decisions>
## Decisions after 02-RESEARCH.md (2026-09-22, orchestrator; owner unavailable — recorded as development defaults)

- **R-1 Unknown tacticity.** NaN `tacticity` maps to `"unknown"` and stays a separate candidate for M1 (303 twins arise); the report prints both the with-twins and folded counts. Raised for the owner before Phase 3.
- **R-2 Populations.** The report prints the README triple (`TC` non-null ∧ `dielectric_const_dc` ∈ [1, 20] ∧ `tg` ∈ [100, 900] K = 43,561) and the quality-filtered triple (`check_tc == True`, 42,733) side by side; which one the evaluator serves is a Phase 3 decision. `tg_rmse` is a sum of squared density residuals, not kelvin: the registry records the ladder (≤ 0.1 → 42,232; ≤ 0.2 → 43,316) and applies no `tg_rmse` cut in M1.
- **R-3 Narrative correction.** `static_dielectric_const` is the uncorrected orientational permittivity of non-polarisable MD, and `dielectric_const_dc = static_dielectric_const − 1 + refractive_index²` holds on all 93,488 rows (residual < 1e-5). A-7 stands as a rule (the registry serves `dielectric_const_dc` only); the validator report states the identity and the 88.83 % figure, and `docs/research/databases/README.md` gets a dated correction note pointing at the report. ADR-0004's consequence sentence stays; its "broken column" wording is superseded by the report.
- **R-4 Units.** Registry `unit_status: verified` for TC (W/(m·K)), Tg (K), density (g/cm³), Rg (Å), ffv (–), sp_ced (MPa = J/cm³), refractive_index (–), dielectric_const_dc (–); `r2` `unverified` with both candidate units stated.
- **R-5 Exit codes.** Validator findings have two classes: `reproduce` (must equal the expected value) and `documented` (a stated difference with tolerance: Maxwell share 88.83 % ± 0.05, identity residual < 1e-5). Any other drift exits 1.
- **R-6 Environment.** `pyyaml` and `types-pyyaml` are added to `env/pixi.toml` (research F-facts: pyyaml only transitive today; mypy strict needs the stubs).
</post_research_decisions>
