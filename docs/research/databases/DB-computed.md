# DB-computed.md — Large computed / generated / enumerated polymer databases (the hMOF analogue)

**Scope:** large *hypothetical / enumerated / generated* polymer sets, and large *computed-label* polymer property sets. This is the polymer counterpart of **hMOF** (51,163 enumerated MOFs + GCMC-computed uptakes) used in LLM4MOF as the "hidden table" for cheap closed-loop benchmarking.
**Survey date:** 2026-09-11. Every claim is tagged `verified_by: fetched` (I retrieved the page/file myself) or `verified_by: search-result-only`.

---

## 0. The one thing to decide first: ML-predicted labels are NOT an oracle

The hMOF role requires that the hidden table's labels be **independent of the search model**. hMOF works because its labels come from GCMC *simulation*, not from an ML surrogate.

For polymers the landscape splits cleanly:

| Label provenance | Databases | Valid as hidden-table oracle? |
|---|---|---|
| **MD simulation** (all-atom classical) | **PolyOmics** (~10^5 polymers, 62 props), Open Polymer Challenge / Kaggle 2025 (~11.5k), RadonPy 2022 (~1k), HTPMD (6,286 electrolyte trajectories) | **YES** — direct hMOF analogue |
| **DFT** (quantum, but *fragment/cluster-level*, not bulk property) | OPoly26 (6.57M single-point DFT), OMG_PhysicalProperties (QM on ~48k monomers) | Partly — labels are energies/forces/frontier orbitals, not design-relevant bulk properties |
| **ML-predicted** | **polyOne** (100M × 29), **PolyUniverse** (8M × 15), polyVERSE/BRICS-bio (1.4M × 14), POINT2 | **NO** — benchmarking an ML search loop against an ML surrogate's own predictions is circular. Useful only as a *generation* corpus or a *plausibility* filter. |
| **Unlabeled (structures only)** | **PI1M** (~1M pSMILES), **SMiPoly** (169,347), **OMG CRUs** (~12M), PolyUniverse monomer files | **NO** — no labels at all |

**This is the single most important finding of this survey.** The polymer database that *looks* most like hMOF (polyOne: 100 million enumerated hypothetical polymers, 29 properties, one big table) is **entirely ML-predicted** by polyBERT. The database that *functions* like hMOF (real simulated labels on a large enumerated set) is **PolyOmics** (Nov 2025, RadonPy consortium, CC BY 4.0).

---

## 1. Master table

| # | Name | Year | Entries | Representation | Labels (n props) | Label provenance | Licence | Access | Hidden-table verdict |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **PolyOmics** | 2025 | >100,000 polymers; >7.3M property data points | SMILES + MD snapshots (JSON) | 62 | **all-atom MD (RadonPy/LAMMPS) + DFT ωB97M-D3BJ monomer QM** | CC BY 4.0 | HF `yhayashi1986/PolyOmics`, direct download | **BEST hMOF analogue.** Real simulated labels, 10^5 scale, one CSV table, permissive licence |
| 2 | **polyOne** | 2022 | 100,000,000 (206 parquet shards × 500k rows) | pSMILES | 29 (37 columns) | **ML-predicted (polyBERT multitask NN)** | GTRC "General Public Use License Agreement" — **non-commercial**, academic use only | Zenodo 10.5281/zenodo.7766806, 32.7 GB, direct | **Structurally perfect, scientifically invalid as oracle** — labels are ML |
| 3 | **PolyUniverse** | 2024 | 8 × ~1M labelled + ~10k PBI; monomer sets total "hundreds of quadrillions" combinatorially | SMILES (+ the two precursor SMILES) | 15 (Tg, Tm, Td, DC, PL, Eg, YS, YM, BS, He/H2/O2/N2/CO2/CH4 perm.) | **ML-predicted (feed-forward NN)** | **CC BY 4.0** | Zenodo 10.5281/zenodo.12585902, direct | Best-licensed large *labelled* hypothetical set, but ML labels |
| 4 | **Open Polymer Challenge / Kaggle NeurIPS 2025** | 2025 | 11,475 unique polymers; 9,625 labelled (7,973 train SMILES) | SMILES | 5 (Tg, FFV, Tc, Density, Rg) | **MD simulation** (LAMMPS; GAFF2 for Tc/ρ/Rg, PCFF+Materials Studio for Tg/FFV) | CC BY 4.0 | Kaggle competition + `alexliu99/neurips-open-polymer-prediction-2025-test-data`; pipeline on GitHub `sobinalosious/ADEPT` | Good small/clean MD oracle; too small & sparse per property for rich constraint queries |
| 5 | **OPoly26** | 2026 | 6,573,734 single-point DFT calcs; 2,444 unique repeat units; 94k MD cells | 3D atomic clusters (≤360 atoms) | DFT energy, forces, HOMO/LUMO, gaps, Mulliken/Löwdin/NBO charges, dipoles | **DFT ωB97M-V/def2-TZVPD (ORCA 6.0.0)** | CC-BY-4.0 (paper); HF mirror under "FAIR Chemistry License" | HF `facebook/OMol25` (gated), ColabFit mirror `colabfit/OPoly26-train` | **No.** It is an MLIP training set (energies/forces), not a design-property table; only 2,444 distinct chemistries |
| 6 | **OMG (Open Macromolecular Genome)** | 2023 | ~12,000,000 CRUs from 77,281 reactants, 17 polymerization templates | SMILES (CRU) | **none in the base set** | — (structures only) | GPL-3.0 (code); Zenodo record 7556992 GPL-3.0 | GitHub `TheJacksonLab/OpenMacromolecularGenome`; Zenodo 10.5281/zenodo.7556992 (`OMG_monomers_CRU.zip`, 162.5 MB) | **Unlabeled.** Excellent *candidate-space* generator, not an oracle |
| 6b | **OMG_PhysicalProperties** | 2024 | monomer-level props for the 12M OMG polymers | SMILES + conformers | monomer-level electronic/optical props + Flory-Huggins χ | **QM (DFT/TD-DFT + xTB2) on ~32,529 + ~15,147 monomers; the 12M are ML-extrapolated (D-MPNN active learning, with uncertainties)** | MIT | Zenodo 10.5281/zenodo.13863778 (~52 GB across 7 files) | Hybrid — the QM subset (~48k) is a real oracle; the 12M layer is ML |
| 7 | **PI1M** | 2020 | 995,799 pSMILES (995,800 lines incl. header — I counted the file) | pSMILES | **none** (v2 adds an SA score only) | RNN generative model trained on ~12k PolyInfo polymers | **MIT** (repo LICENSE); README adds "Data for academic purpose only." | GitHub `RUIMINMA1996/PI1M` — `PI1M.csv`, `PI1M_v2.csv`, direct raw download | **Unlabeled.** The standard polymer *chemical-space* corpus; needs an external oracle |
| 8 | **SMiPoly** | 2023 | 169,347 unique polymers from 1,083 monomers, 22 rules, 7 classes | SMILES (repeat unit) | **none** | rule-based enumeration | BSD-3-Clause (code); paper CC BY 4.0 | GitHub `PEJpOhno/SMiPoly` — generator + `202207_smip_monset.csv` (1,083 monomers). Prebuilt 169k file **not** shipped; you regenerate it | **Unlabeled.** Clean, cheap, synthesizability-aware candidate generator |
| 9 | **RadonPy published dataset** | 2022 | >1,000 amorphous polymers | SMILES + MD cells | 15 (incl. thermal conductivity, density, Cp, thermal expansion, refractive index) | **all-atom classical MD (Fugaku)** | RadonPy code BSD-3 (repo); dataset superseded by PolyOmics | GitHub `RadonPy/RadonPy`; npj Comput Mater 2022 | Superseded by PolyOmics (same group, 100× larger) |
| 10 | **HTPMD** | 2022–23 | 6,286 MD trajectories, 6,057 unique polymers, 5.7 TB | SMILES + raw MD trajectories | ion-transport properties (conductivity, diffusivity, transference no.) | **MD simulation** | not verified | `htpmd.matr.io` web app (DNS failed at survey time); code `TRI-AMDD/htp_md` | Narrow domain (polymer electrolytes) but genuinely simulated; a valid *niche* oracle |
| 11 | **POINT²** | 2025 | reuses PI1M (~1M) + assorted labelled sets; 6 properties | SMILES | Tg, Tm, density, gas permeability (experimental); FFV, thermal conductivity (MD) | mixed exp + MD for the labelled core; **ML-predicted** for the 1M PI1M layer | MIT (repo) | GitHub `Jiaxin-Xu/POINT2` — README says "more info regarding data & model availability will be available upon formal publication" | **Not yet a usable table.** Data not fully released as of survey |
| 12 | **polyVERSE** | 2024– | umbrella repo, many CSVs (largest single item: 1.4M bioplastic candidates with 14 predicted props) | SMILES | per-folder | mixed: experiment, MD/DFT, and ML predictions — *stated explicitly in the README* | **Georgia Tech / GTRC proprietary licence** (no commercial sale without separate GTRC agreement) | GitHub `Ramprasad-Group/polyVERSE`; Zenodo 10.5281/zenodo.13352644 (v1.0.0 zip, 2.7 MB) | **Not a single large table.** It is a *directory* of ~25 modest property CSVs; polyOne is referenced from it, not contained in it |
| 13 | **polyGNN / Polymer Genome training set** | 2023 | 13,388 polymers, 36 properties, >21,000 data points | SMILES | 36 | mixed experimental + DFT (literature/handbook curation) | code "for academic use" | **Not publicly downloadable.** Paper: "The sources of data used in this work and the availability of each source is reported in the paper." Code only: `Ramprasad-Group/polygnn` | **No.** Underlying corpus is not released as a table |
| 14 | **OpenPoly** | 2025 | 3,985 polymer–property data points, 26 properties | SMILES | 26 | **experimental** (literature-mined, manually validated) | not verified | GitHub `WangGroupFDU/Openpoly_benchmark` | Experimental, small — belongs to the CoRE-MOF/QMOF lane, not this one |

---

## 2. Detailed entries

### 2.1 polyOne — the "looks like hMOF but isn't" case
- **Reference:** Kuenneth & Ramprasad, *polyOne Data Set — 100 million hypothetical polymers including 29 properties*, Zenodo, v1 published 2022-09-29. https://zenodo.org/records/7766806 — `verified_by: fetched`
- **Paper:** Kuenneth & Ramprasad, "polyBERT: a chemical language model to enable fully machine-driven ultrafast polymer informatics", *Nat Commun* **14**, 4099 (2023). https://pmc.ncbi.nlm.nih.gov/articles/PMC10336012/ — `verified_by: fetched`
- **Exact file inventory** (Zenodo REST API, `https://zenodo.org/api/records/7766806`) — `verified_by: fetched`:
  - 209 files, **32,705,092,046 bytes (32.7 GB)**
  - **206 `.parquet` shards** named `polyOne_aa.parquet` … `polyOne_hx.parquet`, ~115.1 MB each
  - `generated_polymer_smiles_train.txt` (8.1 GB, 80M pSMILES), `generated_polymer_smiles_dev.txt` (904.6 MB, 20M pSMILES)
  - `LICENSE` (6,523 bytes)
  - Zenodo licence id: **`other-nc`** ("Other (Non-Commercial)")
- **Parquet schema — I read the footer of `polyOne_aa.parquet` via an HTTP range request and decoded the embedded pandas metadata** — `verified_by: fetched`. 38 columns, 500,000 rows per shard (`"start": 0, "stop": 500000`):
  ```
  smiles, Egc, Egb, Eib, CED, Ei, Eea, nc, ne,
  epse_1.78, epse_2.0, epse_3.0, epse_4.0, epse_5.0, epse_6.0, epse_7.0, epse_9.0, epse_15.0,
  epsc, TSb, TSy, epsb, YM,
  permCH4, permCO2, permH2, permO2, permN2, permHe,
  Eat, rho, LOI, Xc, Xe, Cp, Td, Tg, Tm
  ```
  37 property columns = **29 properties** once the 9 `epse_*` frequency-resolved dielectric constants are counted as one property. This reconciles the "29 properties" claim exactly.
  206 shards × 500,000 = 103,000,000 nominal rows (advertised as "100 million").
- **Label provenance — decisive:** the Zenodo description states the dataset contains "100 million hypothetical polymers each with **29 predicted properties using machine learning models**". The polyBERT paper's own training corpus was only **35,517 data points** (28,061 homopolymers + 7,456 copolymers) across 11,145 monomers. Per-property training counts from the paper (`verified_by: fetched`): Tg 8,495 · Td 4,648 · Egc 4,224 · Tm 3,655 · Eib 2,610 · kf 1,187 · εb 1,128 · E 914 · ρ 910 · σb 981 · μO2 600 · Egb 597 · ne 516 · Xc 432 · μCO2 405 · Eat 390 · nc 382 · kc 382 · μN2 483 · μCH4 378 · Ei 370 · Eea 368 · μHe 297 · δ 294 · σy 294 · μH2 286 · Xe 111 · Oi 101 · cp 79.
  → **Several properties are extrapolated to 100 million polymers from fewer than 500 measurements.** Using this as a benchmark oracle would measure how well an agent reproduces polyBERT, not chemistry.
- **How generated:** BRICS decomposition of 13,766 synthesized polymers → 4,424 unique fragments → random + enumerative recombination → 100M chemically valid pSMILES, "mostly, have never been synthesized before."
- **Licence — exact text I downloaded** (`https://zenodo.org/records/7766806/files/LICENSE?download=1`, 6,523 bytes) — `verified_by: fetched`:
  > "GENERAL PUBLIC USE LICENSE AGREEMENT … This Program is licensed, not sold to you by GEORGIA TECH RESEARCH CORPORATION ("GTRC"), owner of all code, data and accompanying documentation … At no time shall the program be sold for commercial gain either alone or incorporated with other program(s) without entering into a separate agreement with GTRC."
  The paper's data-availability statement reads: "The data set of 100 million hypothetical polymers with 29 predicted properties is available for **academic use** at 10.5281/zenodo.7766806."
- **Verdict:** the correct *structural* analogue of hMOF (one giant enumerated table, pSMILES + many property columns, trivially queryable with `pandas`/`dask`). But because labels are ML predictions it **cannot honestly be used to benchmark an ML-driven closed-loop search**. Use it as (a) the candidate pool the agent proposes into, and (b) a cheap *pretext* benchmark clearly labelled as "surrogate-vs-surrogate", never as ground truth.

### 2.2 PolyOmics — the real hMOF analogue
- **Reference:** Yoshida, Hayashi, Furuya *et al.*, "Omics-scale polymer computational database transferable to real-world artificial intelligence applications", arXiv:2511.11626 (submitted 2025-11-07). https://arxiv.org/abs/2511.11626 — `verified_by: fetched`
- **Data:** Hugging Face `yhayashi1986/PolyOmics`, DOI **10.57967/hf/7475** — `verified_by: fetched` (dataset card + HF API `https://huggingface.co/api/datasets/yhayashi1986/PolyOmics?full=true`)
- **Scale:** >100,000 polymeric materials; **>7.3 million property data points**; **62 automated properties**; ~100 million node-hours on **Fugaku** over ~4 years; ~260 researchers / 48 institutions. (`verified_by: fetched` — alphaXiv overview of 2511.11626; HF card.)
- **Files (HF API, 51 files)** — `verified_by: fetched`:
  - `all_data.csv` (combined, ~128k+ rows)
  - `general_polymers_with_sp_abbe_dynamic-dielectric.csv` — **73,045** isotropic amorphous polymers
  - `cellulose.csv` — **50,661** cellulose derivatives
  - `PFAS.csv` — **3,821**
  - `small_molecules.csv` — 23,361 · `ladder_polymers.csv` — 519 · `biodegradable_candidate_polyester.csv` — 383 · `corresponding_non_ladder_polymers.csv`
  - `chi_parameter/Summary_<solvent>.csv` — χ parameters for 93,331 polymers against many solvents/plasticizers (Acetone, DMSO, Benzene, Chloroform, DEHP, …)
  - `MD_snapshot_JSON/*.tar.gz` — 22 archives of raw MD snapshots by polymer class (PI, PEST, PAMD, PURT, PSTR, …)
- **Property columns — I pulled the real CSV header via HTTP range request** (`verified_by: fetched`). Confirmed MD-computed columns include:
  `density, Rg, Scaled Rg, self-diffusion, Cp, Cv, compressibility, isentropic_compressibility, bulk_modulus, isentropic_bulk_modulus, volume_expansion, linear_expansion, static_dielectric_const, dielectric_const_dc, nematic_order_parameter, refractive_index, thermal_conductivity, thermal_diffusivity, TC_ke/TC_pe/TC_pair/TC_bond/TC_angle/TC_dihed/TC_improper/TC_kspace/TC_fix` (thermal-conductivity decomposition), `Tg` (+ `preset_tg_ver`, `tg_*` fields), plus monomer-level QM columns `qm_homo_monomerN, qm_lumo_monomerN, qm_dipole_{x,y,z}_monomerN, qm_polarizability*_monomerN, mol_weight_monomerN, vdw_volume_monomerN`, and full simulation provenance (`RadonPy_ver, LAMMPS_ver, Psi4_ver, RDKit_ver, temp, press, DP, n_mol, n_atom, tacticity, copoly_ratio_list, copoly_type`).
- **Label provenance:** all-atom classical MD via **RadonPy** (GAFF2) for bulk properties; **DFT ωB97M-D3BJ** (Psi4) for monomer electronic properties. **Genuinely simulated — not ML.**
- **Licence:** `cc-by-4.0` (HF `cardData.license`, verified via the HF API) — `verified_by: fetched`. No gating observed.
- **Verdict:** **This is the hMOF analogue.** It has all four hMOF properties: (i) large (10^5, same order as hMOF's 51,163), (ii) enumerated/virtual chemistries, (iii) *simulated* labels from a documented physics pipeline, (iv) a flat table you can look up for free. Bonus over hMOF: 62 properties instead of a handful of gas uptakes, plus copolymer composition and tacticity as extra design variables, plus χ parameters against ~dozens of solvents which is a natural multi-constraint query surface ("find a polymer with Tg > 450 K, thermal conductivity > 0.3 W/m·K, and χ < 0.5 in acetone").

### 2.3 PolyUniverse
- **Reference:** Yue, He & Li, "Polyuniverse: generation of a large-scale polymer library using rule-based polymerization reactions for polymer informatics", *Digital Discovery* **3**, 2465–2478 (2024). RSC page 403-blocked; ChemRxiv preprint 10.26434/chemrxiv-2024-7069c (2024-07-12) — `verified_by: search-result-only` for the paper text.
- **Data:** Zenodo **10.5281/zenodo.12585902**, "PolyUniverse: Generation Results", creator Tianle Yue, published 2024-06-28, licence **`cc-by-4.0`** — `verified_by: fetched` (Zenodo REST API).
- **66 files.** Two kinds:
  - **Labelled polymer sets (8 × ~1M + 1 × 10k):** `Polyimide_1M_p.csv` (370.8 MB), `Polyolefin_1M_p.csv` (279.7 MB), `Polyester_1M_p.csv` (291.4 MB), `Polyamide_1M_p.csv` (273.6 MB), `Polyurethane_1M_p.csv` (310.5 MB), `Epoxy_1M_p.csv` (265.4 MB), `Vitrimers_1M_p.csv` (271.5 MB), `PIPIM_1M_p.csv` (334.3 MB), `PBI_10k_p.csv` (2.5 MB), plus `PolyInfo_p.csv` (2.7 MB, the real-polymer reference set). → **~8 million labelled hypothetical polymers.**
  - **Unlabeled monomer pools** from GDB-13 / GDB-17 / PubChem by functional class (`GDB-13_cOle.csv` 4.6 GB, `GDB-13_diamin.csv` 4.2 GB, `GDB-13_vinyl.csv` 4.6 GB, `PubChem_diamin.csv` 834 MB, etc.) — these are the combinatorial precursors.
- **Columns — I read the real header of `Polyimide_1M_p.csv` via range request** (`verified_by: fetched`):
  `Smiles, Smiles_Compound_1, Smiles_Compound_2, Tg, DC, PL, Eg, YS, YM, BS, He, H2, O2, N2, CO2, CH4, Tm, Td`
  → 15 properties **plus the two precursor monomer SMILES**, which is unusual and valuable: every row carries its own retrosynthetic recipe.
- **Label provenance:** "Customized feedforward neural network models predicted thermal, mechanical, and gas permeation properties" — **ML-predicted** (`verified_by: search-result-only`, RSC/ChemRxiv abstract text via search).
- **Verdict:** the best-*licensed* large labelled hypothetical set (CC BY 4.0, no academic-only restriction, unlike polyOne). Still ML labels → same circularity objection. Its real strength for LLM4POL is the **precursor pair on every row**, which makes "propose a synthesizable polymer meeting constraints X" checkable.

### 2.4 Open Polymer Challenge / Kaggle NeurIPS 2025 — small but honest MD oracle
- **Reference:** Liu, Alosious *et al.*, "Open Polymer Challenge: Post-Competition Report", arXiv:2512.08896 (2025-12-09). https://arxiv.org/html/2512.08896v1 — `verified_by: fetched`
- **Size:** 11,475 unique polymers; **9,625 have ≥1 label**; train set 7,973 unique SMILES.
- **Per-property counts** (`verified_by: fetched`):
  | Property | Train | Test (public+private) |
  |---|---|---|
  | Tg | 511 | 261 |
  | FFV | 7,030 | 223 |
  | Tc (thermal conductivity) | 737 | 1,404 |
  | Rg | 614 | 1,110 |
  | Density | 613 | 1,526 |
- **Label provenance:** **MD simulation**, two parallel pipelines — GAFF2 + LAMMPS for Tc/Density/Rg; PCFF + Materials Studio + LAMMPS for Tg/FFV.
- **Licence:** CC BY 4.0 (paper metadata). Test labels were released openly after data-leakage was detected during the competition. Data generation pipeline (simulates >25 properties): GitHub `sobinalosious/ADEPT`. Test data: Kaggle `alexliu99/neurips-open-polymer-prediction-2025-test-data`.
- **Verdict:** clean, small, honest. Too sparse per property (511 Tg values) to support the kind of multi-constraint lookup hMOF supports, but ideal as a **held-out validation set** for anything trained/benchmarked on PolyOmics. The ADEPT pipeline also means you can *generate new ground truth on demand* if you have compute.

### 2.5 OPoly26 — big, new, and the wrong shape for this job
- **Reference:** Levine, Liesen, …, Blau, Antoniuk, "The Open Polymers 2026 (OPoly26) Dataset and Evaluations", arXiv:2512.23117v2 (2026-03-05). LLNL + Meta FAIR. — `verified_by: fetched` (PDF metadata + abstract)
- **Size:** **6,573,734 single-point DFT calculations** on clusters ≤360 atoms, >1.2 billion atoms total; derived from MD of **94k unique amorphous polymer simulation cells** (>239,000 ns cumulative); **2,444 unique repeat units** across 6 classes (synthetic homopolymers, fluoropolymers, conjugated polymers, polymer electrolytes, peptoids, lipid-like amphiphiles). Splits: 6,099,878 train / 210,924 val / 259,740 test. 1.2 billion core-hours on LLNL Tuolumne. — `verified_by: fetched` (emergentmind topic page; ColabFit card gives 6,104,876 configurations in the train split)
- **Level of theory:** ωB97M-V/def2-TZVPD (ORCA 6.0.0), with COSX/RI-J.
- **Labels:** DFT total energy, atomic forces, HOMO/LUMO, gaps, Mulliken/Löwdin/NBO charges & spins, dipole moments. **Not** Tg, density, permeability, etc.
- **Licence/access:** paper CC-BY-4.0; primary host `https://huggingface.co/facebook/OMol25` returned **HTTP 401** for me (gated — requires HF login/terms acceptance). Ungated mirror: `https://huggingface.co/datasets/colabfit/OPoly26-train`, listed licence "FAIR Chemistry License". — `verified_by: fetched`
- **Verdict:** **not a hidden table.** It is a machine-learning-interatomic-potential training corpus. Only 2,444 distinct chemistries, and the labels are per-configuration quantum quantities, not per-material design properties. Relevant to LLM4POL only if you want an MLIP to *generate* new labels cheaply.

### 2.6 OMG — the best unlabeled candidate space
- **Reference:** Kim, Schroeder & Jackson, "Open Macromolecular Genome: Generative Design of Synthetically Accessible Polymers", *ACS Polymers Au* **3**(4), 318–330 (2023). doi:10.1021/acspolymersau.3c00003 (ACS 403-blocked; ChemRxiv 10.26434/chemrxiv-2023-3hn5r) — `verified_by: search-result-only` for the paper; the size figure ("from 77,281 selected reactants, nearly 12 million chemically distinct CRUs generated by 17 template-based polymerization algorithms implemented with RDKit") comes from a search result whose title matches the paper.
- **Code:** GitHub `TheJacksonLab/OpenMacromolecularGenome`, **GPL-3.0**. README: repo provides "python scripts to construct the OMG database"; users must obtain `version.smi` from **eMolecules** themselves. — `verified_by: fetched`
- **Data:** Zenodo **10.5281/zenodo.7556992** ("v1.0b — First release of OMG with data", 2023-01-21, GPL-3.0): `OMG_monomers_CRU.zip` 162.5 MB + repo zip 206.9 MB. — `verified_by: fetched`
- **Property layer:** Zenodo **10.5281/zenodo.13863778**, "TheJacksonLab/OMG_PhysicalProperties: OMG-Property-Database", 2024-12-01, **MIT**, 7 files totalling ~52 GB. Description (quoted from the Zenodo record): *"Monomer-level properties for 12M synthetically accessible polymers in the Open Macromolecular Genome derived via quantum chemistry."* The record's own notes reveal the QM coverage: **32,529 QM-calculated OMG methyl-terminated geometries (pareto-greedy) + 15,147 (test)**. — `verified_by: fetched`
  The GitHub README confirms the 12M layer is **ML-extrapolated**: "trained ML models, conformer geometry, and **ML-based monomer-level properties for 12M OMG polymers with prediction uncertainties** are available at Zenodo." QM stack: RDKit/UFF conformers → xTB2 optimization → DFT/TD-DFT; plus COSMO-SAC Flory–Huggins χ; ML = D-MPNN evidential active learning. — `verified_by: fetched`
- **Verdict:** the ~12M CRUs are an outstanding **synthesizability-constrained candidate space** (every CRU traces to purchasable reactants + a named polymerization). Base set is unlabeled; the property layer is a ~48k QM core with an ML shell. Pair OMG (candidates) + PolyOmics (oracle) and you have a very defensible closed loop.

### 2.7 PI1M — the standard unlabeled corpus
- **Reference:** Ma & Luo, "PI1M: A Benchmark Database for Polymer Informatics", *J. Chem. Inf. Model.* **60**(10), 4684–4690 (2020). doi:10.1021/acs.jcim.0c00726 — `verified_by: search-result-only` for the article; README `verified_by: fetched`
- **I downloaded and counted the file:** `PI1M_v2.csv` = **995,800 lines including header → 995,799 polymers**. Columns: `SMILES, SA Score`. `PI1M.csv` = same count, single column `SMILES`. — `verified_by: fetched`
- **No property labels.** The README is explicit: "~1 million polymer structures", "Data format: p-SMILES". The four properties named in the abstract (density, Tg, Tm, dielectric constant) refer to *downstream regression tasks the authors ran on PolyInfo data*, not columns in PI1M.
- **Licence:** repo `LICENSE` is **MIT License, Copyright (c) 2020 RUIMINMA1996** (`verified_by: fetched`), but the README adds "Note: Data for academic purpose only." — conflicting; treat as academic-use in practice.
- **Generation:** RNN generative model trained on ~12,000 PolyInfo polymers.
- **Verdict:** unlabeled. Useful as the "chemically plausible polymer space" prior and as a negative control, not as an oracle.

### 2.8 SMiPoly
- **Reference:** Ohno, Hayashi, Zhang, Kaneko & Yoshida, "SMiPoly: Generation of a Synthesizable Polymer Virtual Library Using Rule-Based Polymerization Reactions", *J. Chem. Inf. Model.* **63**(17), 5539–5548 (2023). doi:10.1021/acs.jcim.3c00329. Open-access via https://pmc.ncbi.nlm.nih.gov/articles/PMC10498440/ — `verified_by: fetched`
- **Size:** **169,347 unique polymers** from **1,083** readily-available monomers, **22 rules** (6 chain-growth + 16 step-growth), 7 classes (polyolefin, polyester, polyether, polyamide, polyimide, polyurethane, polyoxazolidone). Coverage 48% / novelty 53% vs ~16,000 real polymers.
- **Labels:** **none — structures only** (explicitly confirmed in the PMC article).
- **Licence/access:** GitHub `PEJpOhno/SMiPoly`, **BSD-3-Clause**; paper CC BY 4.0. Ships `202207_smip_monset.csv` (1,083 monomers) + `monc.py`/`polg.py` + demo notebook. The 169,347-polymer file is **not** shipped — you run the generator. — `verified_by: fetched`
- **Verdict:** unlabeled, but the cleanest *synthesizability-aware* enumerator and the natural candidate space to pair with PolyOmics (same lab lineage — Yoshida group — so chemistry conventions match).

### 2.9 polyVERSE — an umbrella, not a database
- **Reference:** Ramprasad *et al.* (2024), *polyVERSE: Informatics-Ready Polymer Datasets (Version 1.0)*, Zenodo DOI **10.5281/zenodo.13352644**, published 2024-08-21, creators Harikrishna Sahu *et al.* Zip is **2.7 MB**. — `verified_by: fetched`
- **README (quoted, fetched from raw GitHub):** *"polyVERSE (Polymer Universe, also 'polymers generated by Virtually-Executed Rule-based Synthesis Experiments') is a comprehensive repository for informatics-ready datasets curated by the Ramprasad Group … It includes datasets generated through physical experiments, physics-based simulations, and machine learning model predictions."* — `verified_by: fetched`
- **Full file tree via GitHub API** — `verified_by: fetched`. Two top folders plus extras:
  - `Virtual-Polymer/` — **only four items**: `BRICS/polyBERT/README.md` (a *pointer* to the polyOne Zenodo record — polyOne itself is NOT in this repo); `BRICS-bio/` (`predictions_01_11_2022.csv` = ~1.4 million bioplastic candidates with **14 ML property predictions**, + `candidates.csv` = 70 screened candidates; paper arXiv:2203.12033); `GA/HighTemperaturePolymerDielectrics/` (GA-predicted hypothetical polymers, xlsx); `VFS/ROP/packaging_replacements/`.
  - `Other/` — ~25 small-to-medium property CSVs: `bandgap_chain`, `bandgap_crystal`, `charge_injection_barrier`, `chi_parameter`, `Atomization_enthalpy`, `Cohesive_energy_density`, `Electron_Affinity`, `Ionization_energy`, `Melt_Viscosity`, `Gas_permeability_solubility_diffusivity` (with the actual LAMMPS input decks: `amorphous_polymer_diffusivity.lmps`, `widom_insertions.in`, `CH4_TraPPE_FF.txt` — i.e. **real MD/GCMC-style labels**), `Solvent_Diffusivity_Sorption_*`, `Organic_solar_cell`, `ROP_enthalpy`, `AM_hardness` (`combined_dft_exp.csv`), `Conductivity_*`, `Thermoset_DMREF_Project`.
  - `ROP/` — 3 parquet splits; `ROMP-Recipes/`; `Structure-database/`.
- **Licence:** repo has a `LICENSE` file; Zenodo record is under the **Georgia Tech / GTRC proprietary licence** (same family as polyOne: no commercial sale without a separate GTRC agreement). — `verified_by: fetched`
- **Verdict:** **not** the hMOF analogue. It is a well-curated *collection of small tables* (2.7 MB zip!). Its `Other/Gas_permeability_solubility_diffusivity` folder is however the closest thing in the polymer world to hMOF's *methodology* (Widom insertions + TraPPE force field, i.e. literal GCMC-style gas sorption), and it ships the input decks — worth a close look if you want to run your own hMOF-style GCMC on polymers.

### 2.10 Other entries verified
- **RadonPy 2022:** Hayashi *et al.*, *npj Comput Mater* **8**, 222 (2022), https://www.nature.com/articles/s41524-022-00906-4 (paywall redirect; abstract via search). >1,000 amorphous polymers, 15 MD properties, computed on Fugaku in ~2 months. Code: `github.com/RadonPy/RadonPy`. The ISM press release (https://www.ism.ac.jp/ura/press/ISM2022-08_e.html) announces the intent to build a >100,000-polymer database — which became PolyOmics. The latest RadonPy implements **62 automated properties**. — `verified_by: search-result-only`
- **HTPMD:** TRI + MIT. **6,286 MD trajectories, 6,057 unique polymers, 5.7 TB**, polymer electrolytes, ion-transport properties. Web app `https://www.htpmd.matr.io/` (DNS resolution failed for me at survey time — `getaddrinfo ENOTFOUND`); code `github.com/TRI-AMDD/htp_md`; paper arXiv:2208.01692. — `verified_by: search-result-only`
- **POINT²:** Xu, Liu, Guo, Jiang & Luo, arXiv:2503.23491 (2025-03-30), CC-BY-4.0 paper. 6 properties (gas permeability, thermal conductivity, Tg, Tm, FFV, density); labelled core is mixed experimental + MD; the ~1M PI1M layer is ML-populated. GitHub `Jiaxin-Xu/POINT2` (MIT) currently says *"more info regarding data & model availability will be available upon formal publication"* and provides **no direct download**. — `verified_by: fetched` (arXiv abs + GitHub README)
- **polyGNN:** Gurnani, Kuenneth, Toland & Ramprasad, *Chem. Mater.* **35**(4), 1560–1567 (2023), https://pmc.ncbi.nlm.nih.gov/articles/PMC9979603/. 13,388 polymers, 36 properties, >21,000 data points. **Data availability:** "The sources of data used in this work and the availability of each source is reported in the paper"; only the code (`Ramprasad-Group/polygnn`) is released, "for academic use". **The curated corpus is not downloadable as a table.** — `verified_by: fetched`
- **OpenPoly:** Wang, Sun *et al.*, *Chinese J. Polym. Sci.* (2025), doi:10.1007/s10118-025-3402-y. **3,985 polymer–property data points, 26 experimentally measured properties**; benchmark code `github.com/WangGroupFDU/Openpoly_benchmark`. Experimental → belongs in the CoRE-MOF/QMOF lane, listed here only for completeness. — `verified_by: search-result-only`
- **Useful index:** the Notre Dame "International Workshop on Polymer Data" resource page, https://polymerdataworkshop.nd.edu/info/ — `verified_by: fetched`. It is the single best curated index of polymer data resources I found and is how I discovered PolyUniverse and HTPMD. Note it lists PolyOmics as "130,000 polymers; 5M data points, 81 properties", which conflicts slightly with the paper's own "10^5 polymers / 7.3M data points / 62 properties" — flagging the discrepancy rather than picking one.

---

## 3. Recommendation for LLM4POL

**Use PolyOmics as the hidden table.** Then:

| LLM4MOF role | LLM4POL substitute | Why |
|---|---|---|
| **hMOF** (enumerated + simulated labels, hidden-table oracle) | **PolyOmics** (10^5 polymers, 62 MD/DFT properties, CC BY 4.0, HF direct download) | Only large polymer set whose labels are real simulations. Same order of magnitude as hMOF (51k vs 100k+). Flat CSV → free lookup. |
| **hMOF** at 100× scale, *if* you accept surrogate labels | **polyOne** (100M × 29, Zenodo, non-commercial academic) — clearly labelled as a surrogate benchmark, never as ground truth | Structurally identical to hMOF, 2000× bigger, but ML labels |
| *candidate-generation space* (hMOF's building-block enumeration) | **OMG** (~12M synthesizable CRUs, GPL-3.0) or **SMiPoly** (169k, BSD-3) or **PI1M** (~1M, MIT) | All unlabeled; all give the agent a legal move set |
| *held-out validation* | **Open Polymer Challenge** (9,625 labelled, 5 MD properties, CC BY 4.0, labels now public) | Independent MD pipeline, so it tests transfer rather than memorization |

**Why PolyOmics and not polyOne, in one paragraph.** polyOne is superficially the obvious answer — 100 million enumerated hypothetical polymers, 29 property columns, one Zenodo DOI, exactly the shape of hMOF. But its every label is a polyBERT prediction extrapolated from a training corpus of only 35,517 data points, several properties of which rest on fewer than 500 measurements (heat capacity: 79; limiting oxygen index: 101; experimental crystallization tendency: 111). A closed-loop benchmark in which an LLM agent proposes constraints and gets back polyBERT's opinion is measuring agreement between two machine-learning models, not discovery; the loop can be "solved" by reproducing polyBERT's biases, and any apparent hit rate is uninterpretable as chemistry. It is also under a Georgia Tech non-commercial, academic-use-only licence. PolyOmics, released November 2025 by the RadonPy consortium, inverts every one of those weaknesses: its >7.3 million property values come from fully automated all-atom MD (RadonPy/LAMMPS/GAFF2) plus ωB97M-D3BJ DFT for monomer electronic structure, burning ~100 million node-hours on Fugaku — physics, not regression, exactly as GCMC is physics in hMOF. It covers >100,000 polymers across 62 properties (Tg, density, thermal conductivity and its full decomposition, refractive index, dielectric constants, Cp/Cv, bulk modulus, thermal expansion, self-diffusion, Rg, plus Flory–Huggins χ against dozens of solvents for 93,331 polymers), carries copolymer composition and tacticity as extra design axes, ships the raw MD snapshots, is released **CC BY 4.0** with no gating, and is one `huggingface-cli download` away. The only cost relative to polyOne is three orders of magnitude in row count — which is irrelevant for a hidden-table benchmark, since hMOF itself has only 51,163 rows. If more candidate breadth is needed, pair PolyOmics-as-oracle with OMG or SMiPoly as the proposal space, and reserve polyOne/PolyUniverse for what they are genuinely good at: enormous, cheap, chemically-valid candidate pools with soft ML priors attached.
