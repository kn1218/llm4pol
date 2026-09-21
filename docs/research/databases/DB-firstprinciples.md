# DFT / Quantum-Chemistry / Physics-Simulation Polymer Property Databases
### Survey for LLM4POL — searching for a polymer analogue of QMOF (20,373 DFT band gaps on *synthesized* MOFs)

Survey date: 2026-09-11. Every row tagged `verified_by: fetched` was opened (HTTP/curl/WebFetch) in this session;
rows tagged `search-result-only` rest on a search-engine snippet whose title matched, and are flagged as such.
Where a paper reports simulations but does **not** release data, that is stated plainly.

---

## 0. Executive framing — the structural problem

QMOF = (a) **real, experimentally-synthesized** structures, (b) **first-principles** labels, (c) **~20k** entries,
(d) one clean scalar property (band gap), (e) openly downloadable.

**No polymer dataset satisfies all five.** The field splits into three families, each missing something:

| Family | Has | Missing |
|---|---|---|
| Khazana / Polymer Genome DFT sets | DFT band gap, dielectric, refractive index; SMILES+CIF; open | only ~1k–4k entries; structures **mostly hypothetical/enumerated** |
| OPoly26, PolyOmics (2025–26, huge) | 10^5–10^6 scale, open, CC-BY | labels are **energies/forces** (OPoly26) or **classical-MD** (PolyOmics); polymers largely **virtual** |
| RadonPy 2022 benchmark, Afzal 2021 | **real polymers from PoLyInfo / commercial grades** | raw data **not openly released** (on-request / SI-only) |

The closest practical QMOF analogues are therefore **Khazana's `Polymer Properties` (Kuenneth 2021) table**
(3,655 polymers x 8 DFT properties, 3,380 DFT band gaps) for the *DFT-label* axis,
and **PolyOmics** (73k–130k polymers, 62 MD properties, CC BY 4.0) for the *scale + thermophysical-label* axis.

---

## 1. Khazana — Ramprasad group computational knowledgebase

**verified_by: fetched** — `https://khazana.gatech.edu/` and `https://khazana.gatech.edu/dataset/`
(NOTE: the site presents an **incomplete TLS chain**; `WebFetch` fails with "unable to verify the first certificate".
Retrieved with `curl -k`. Downloads return HTTP 200/206 with **no login**.)

### 1.0 What Khazana actually is
Khazana is **not** a single polymer table. It is a landing page + a **`/dataset/` page listing exactly 33
paper-attached downloadable archives** (verified: `grep -c 'href="/download/'` -> 33), spanning 2014–2025,
covering polymers *and* hafnia, perovskites, Al/Cu/Pt force fields, graphene allotropes, etc.
Roughly 12 of the 33 are polymer-related. There is **no browsable polymer property table, no API, no bulk dump,
no site-wide licence statement**. Each archive carries its own README with a "please cite" line.
`https://khazana.gatech.edu/polymer/` and `/materials/` -> **404** (verified).

### 1.1 Khazana — `Polymer Properties` (Kuenneth et al., *Patterns* 2021, multi-task learning) — BEST DFT ANALOGUE
| Field | Value |
|---|---|
| Name | Khazana "Polymer Properties" / MTL_Khazana |
| Year | 2021 |
| Reference | Kuenneth, Chitteth Rajan, Tran, Chen, Kim, Ramprasad, *Polymer Informatics with Multi-Task Learning*, Patterns 2, 100238 (2021) — article link `https://www.cell.com/patterns/fulltext/S2666-3899(21)00058-1`; data `https://khazana.gatech.edu/download/2021_Patterns_Chris/MTL_Khazana.zip` (72,726 bytes, **downloaded and unzipped**) |
| Entries | **6,265 property values over 3,655 unique polymer SMILES** (counted directly from `export.csv`) |
| Structure representation | **SMILES with `[*]` end-points** (long format: `smiles, property, value`) |
| Properties + how computed | All 8 are **DFT** (README verbatim: "This folder contains the dataset (export.csv) for DFT properties"): `Egc` band gap of the isolated **chain** (eV), `Egb` band gap of the **bulk/crystal** (eV), `Eat` atomization energy (eV/atom), `Xc` crystallization tendency (%), `Eea` electron affinity (eV), `Ei` ionization energy (eV), `nc` refractive index (DFT), `eps` dielectric constant (DFT). Underlying engine = VASP, PBE/GGA geometry + **HSE06** gaps, **DFPT** dielectric (per the 2016 Sci Data protocol, section 1.2) |
| Entries per property | **Egc 3,380 · Egb 561 · Xc 432 · Eat 390 · nc 382 · eps 382 · Ei 370 · Eea 368** (counted first-hand) |
| Real vs hypothetical | **MIXED, majority hypothetical.** Real ones are present and recognisable (row 0 `[*]CC([*])C` = polypropylene, row 1 `[*]CC([*])F` = poly(vinyl fluoride)); the bulk is combinatorially enumerated repeat units from the Ramprasad block library |
| Licence | **None stated.** README gives only a citation request. No CC/CC0 text anywhere in the archive or on the page |
| Access method | Direct anonymous HTTPS download, 71 kB zip -> single `export.csv` |
| **Verdict** | **The single best QMOF-shaped polymer table that exists today: SMILES -> DFT band gap, ~3.4k labels, one file, no login. Weak on (i) licence provenance and (ii) "real polymer" purity. ~6x smaller than QMOF.** |
| verified_by | fetched (downloaded, unzipped, parsed) |

### 1.2 Khazana / Dryad — `A polymer dataset for accelerated property prediction and design` (Huan/Tran 2016)
| Field | Value |
|---|---|
| Name | Khazana polymer dataset "PLMDB" / Dryad `doi:10.5061/dryad.5ht3n` |
| Year | 2016 (Sci Data); Dryad publication date **2017-02-11**, last modified 2020-06-24 |
| Reference | Huan, Mannodi-Kanakkithodi, Kim, Sharma, Pilania, Ramprasad, *A polymer dataset for accelerated property prediction and design*, Sci. Data 3, 160012 (2016), doi 10.1038/sdata.2016.12. Paper read at `https://pmc.ncbi.nlm.nih.gov/articles/PMC4772654/` (**fetched**); data at `https://datadryad.org/dataset/doi:10.5061/dryad.5ht3n` (**fetched**) and `https://khazana.gatech.edu/download/2016_SD_Huan/PLMDB_03102016.zip` (**downloaded, 2,091,709 bytes**) |
| Entries | **1,073** — verified by unzipping: files `0001.cif` … `1073.cif` (2,142 files incl. macOS junk). Dryad `storageSize` 714,927 B for `Polymer-CIF.tgz` |
| Structure representation | **CIF (pymatgen-written), periodic crystal**, with a commented property block appended to each file |
| Properties + how computed | Verified verbatim from `0001.cif` (cellulose): `Dielectric_constant_electronic 2.84888E+00`, `Dielectric_constant_ionic 9.33221E-01`, `Dielectric_constant_total 3.78210E+00`, `Band_gap_at_the_GGA_level_(eV) 5.61940E+00`, `Band_gap_at_the_HSE06_level_(eV) 7.47570E+00`, `Atomization_energy_(eV/atom) -5.47556E+00`, `Volume_of_the_unit_cell_(A^3)`, plus `Simulation_tool: VASP-5.X`, `Pseudopotential: PAW`, `Simulation_conditions: ENCUT=400eV, k-spacing_relax=0.25/Angstrom, k-spacing_bandgap=0.20/Angstrom`. Paper: rPW86-GGA + vdW-DF2 relaxation, **HSE06** gaps, **DFPT** dielectric. **4,292 DFT runs total** (4 per structure: relax, dielectric, GGA gap, HSE06 gap) |
| Entries per property | Nominally 1,073 each for the 5 properties in the CIF header |
| Real vs hypothetical | **Mostly hypothetical.** Composition per the paper: **34 common (known) polymers**, **314 new organic + 472 organometallic** computationally generated (USPEX / minima-hopping from CH2, NH, CO, O, CS, C6H4, C4H2S blocks and Sn/Zn/Cd/Pb/Mg/Ca/Al/Ti/Hf/Zr moieties), **253 molecular crystals from the Crystallography Open Database** |
| Licence | **Dryad API `license` field = `https://spdx.org/licenses/CC0-1.0.html` (CC0 1.0)** — verified via `datadryad.org/api/v2/datasets/...`. Paper itself CC BY 4.0 with CC0 waiver on metadata |
| Access method | Dryad download, or direct Khazana zip. Also mirrored as **4,292 raw DFT runs on NoMaD, doi 10.17172/NOMAD/2016.01.27-1** (paper text + search snippet; NoMaD landing page not opened) |
| **Verdict** | **Cleanest licence (CC0) and the only one carrying DFT provenance inside each file, but only 1,073 entries and <=34 are actually known polymers. Good small hidden table; too small and too hypothetical to be "the" QMOF analogue.** |
| verified_by | fetched |

### 1.3 Khazana — `Polymer Insulators` / high-voltage set (Kamal 2021, JCP)
| Field | Value |
|---|---|
| Year / ref | 2021 — Kamal, Tran, Kim, Wang, Chen, Cao, Joseph, Ramprasad, *Novel high voltage polymer insulators using computational and data-driven techniques*, J. Chem. Phys. 154, 174906 (2021); data `https://khazana.gatech.edu/download/2021_JCP_Deepak/high_voltage_polymers.zip` (**downloaded, 88,345 bytes**) |
| Entries | **4,209 unique polymer SMILES** (counted from `data.csv`) |
| Representation | SMILES with `[*]` |
| Properties (DFT) | `bandgap_chain` **4,209 values**, `eib` electron-injection barrier **1,826 values**, `bandgap_crystal` **236 values** (counted) |
| Real vs hypothetical | **Hypothetical** — a computationally screened design library |
| Licence | **None stated**; README is a citation request only |
| Access | Anonymous HTTPS zip |
| **Verdict** | **4,209 DFT chain band gaps — larger than the MTL table on that one property — but hypothetical design candidates.** |
| verified_by | fetched (downloaded + parsed) |

### 1.4 Other polymer-relevant Khazana archives (link list extracted from `/dataset/`, **fetched**)
| Archive | Paper | What I verified |
|---|---|---|
| `Poly24.tar.gz` (PolyGET) | *PolyGET: Learning Generalizable Force Fields…* (page says "Submitted (2025)"; arXiv:2309.00585) | **25,492,955 bytes** downloaded OK. Per search results: **24 polymer types ("Poly24")**, DFT-level MD trajectories for force-field training — energies/forces, *not* property labels. The page's article link is literally `href="None"` |
| `esw_07242019.tar` — Polymeric Electrolytes | Chen et al., *Electrochemical Stability Window of Polymeric Electrolytes*, Chem. Mater. 31, 4598 (2019) | Downloaded + untarred: **98 CIF files (`3995.cif`–`4092.cif`)**. Property block verified: `Tool: VASP`, `Pseudopotential: PBE-HSE06`, `Bandgap_(eV): 7.09` |
| `polymer_morphology_07122018.zip` — Polymer Dielectrics | Chen et al., *Electronic Structure of Polymer Dielectrics: The Role of Chemical and Morphological Complexity*, Chem. Mater. 30, 7699 (2018) | Downloaded: **20 CIF files** (up to 1,608 atoms). Header verified: `Tool: VASP`, `PBE-HSE06`, `Bandgap_(eV): 6.34`, plus note "**HSE06 Band gap is derived from PBE band gap, based on Eg(HSE06)=1.140*Eg(PBE)+0.799, R2=0.97**" — i.e. *extrapolated*, not directly computed HSE06 |
| `ROP_2022.zip` — Recyclable polymers (ring-opening polymerisation enthalpy from first principles, JPCL 13, 4778, 2022) | Huan et al. | **Downloads only 956 bytes — effectively an empty/placeholder archive. Broken.** |
| `pe_str_08072017.zip`, `peoli_08012018.zip`, `data_pdms_2023.zip`, `ML-DFT_database.zip`, `Sublimaion_enthalpy_Yifan.tar.gz`, `AM-Active-Learning-Khazana.zip` | Various | Listed and linked; not individually opened |

### 1.5 Khazana summary verdict
> Khazana is a **collection of ~12 small paper-attached polymer DFT archives (1k–4k entries each), not a
> 20k-row queryable database**. It is fully open (no login) but **carries no licence** except the Dryad
> CC0 on the 2016 set. It is the right *place* to look for a polymer QMOF; it does not yet contain one.

---

## 2. Polymer Genome (polymergenome.org)

| Field | Value |
|---|---|
| Name | Polymer Genome |
| Year | 2018 -> present (JPC C 2018; J. Appl. Phys. 128, 171104 (2020)) |
| Reference | `https://www.polymergenome.org` (**fetched** — returns a login/landing page) |
| Is it a dataset? | **NO — it is a prediction web service.** Verbatim from the site: *"It is an informatics platform for **PREDICTING** the properties of polymers using pre-built machine learning models."* Query by drawing tool or SMILES; separate homopolymer and copolymer interfaces |
| Download / bulk access | **None offered.** No API, no dump, no export. Requires an account. The site links out to Khazana for data |
| Underlying data composition | Per search snippets of the JAP 2020 / JPC C 2018 papers: **854 organic polymers**, where **band gap, dielectric constant, refractive index and atomization energy are DFT-computed (VASP)** and **glass transition temperature, Hildebrand solubility parameter and density are experimental**. Consistent with the 3,655-SMILES DFT table of section 1.1 being the computed backbone |
| Licence | **None visible.** Only legal text on the landing page is a cookie notice |
| **Verdict** | **Unusable as a hidden table. Its outputs are ML PREDICTIONS — exactly what LLM4POL must avoid. Its training data is what you want, and that lives in Khazana (1.1 / 1.2).** |
| verified_by | fetched (site); search-result-only (854-polymer composition) |

---

## 3. OPoly26 — Open Polymers 2026 (LLNL + Meta FAIR Chemistry)

| Field | Value |
|---|---|
| Name | **OPoly26** (Open Polymers 2026) |
| Year | 2025/2026 (arXiv 2512.23117) |
| Reference | *The Open Polymers 2026 (OPoly26) Dataset and Evaluations* — `https://arxiv.org/abs/2512.23117` (**fetched**), full text `https://arxiv.org/html/2512.23117v1` (**fetched**) |
| Entries | **> 6.57 million single-point DFT calculations**, clusters of **up to 360 atoms**, **> 1.2 billion atoms total**. ColabFit mirror card: **6.1 M unique configurations / ~1.1 B atoms** |
| Structure representation | **Hydrogen-capped molecular CLUSTERS / oligomer fragments excised from polymer chains — NOT periodic repeat units, NOT whole polymers.** Fragments span DP ~20–500 repeat-unit atoms per cluster. Sampled from ~94,000 unique classical-MD polymer cells, plus MLIP-MD, DFTB and AFIR reactivity searches |
| Properties + how computed | **Energies and atomic forces** (MLIP training targets), plus further per-calculation properties in the paper's Appendix A.2. Level of theory per the paper: **wB97M-V / def2-TZVPD**, code **ORCA** (matching OMol25). WARNING — **discrepancy:** the ColabFit HF card states **B97M-V / def2-SVP, ORCA**. Treat the paper as authoritative and re-check before quoting |
| Entries per property | Energy + forces on essentially all 6.57 M. **No polymer-level scalar property table** (no Tg, no bulk band gap, no dielectric constant) |
| Real vs hypothetical | **MIXED, unusually well-provenanced.** Sources named in the paper: traditional polymers from the **RadonPy benchmark and textbooks (REAL)**, fluoropolymers from the **Open Macromolecular Genome (ML-generated but reaction-compatible)**, optical polymers from **Polymer Chemprop**, polymer electrolytes from **PolyGen**, peptoids from the **Peptoid Data Bank**, lipids from the **NMRlipid** database |
| Licence | **CC-BY-4.0** per the paper. WARNING — the ColabFit HF mirror is tagged `license: other` and its card reads **"FAIR Chemistry License"** (verified via HF API: `license: other`, `gated: False`) |
| Access method | Primary: `https://huggingface.co/facebook/OMol25` — **verified via HF API: `gated: "manual"`, `license: "other"` -> requires manual approval to download.** Open mirror: `https://huggingface.co/datasets/colabfit/OPoly26-train` — **verified `gated: False`**, parquet, `size_categories: 1M<n<10M`, dirs `ds.parquet`, `co/`, `cs/`, `cs_co_map/`. Code: `github.com/facebookresearch/fairchem` |
| **Verdict** | **The largest first-principles polymer resource by far, but it is MLIP training data (energies/forces on oligomer fragments), not a property table. It cannot answer "what is the band gap of PMMA?". Poor hidden table for LLM4POL, and the primary host is access-gated.** |
| verified_by | fetched (arXiv abs + html; HF API for both repos) |

---

## 4. polyChainStructures (polyGen)

| Field | Value |
|---|---|
| Name | **polyChainStructures** |
| Year | 2025 |
| Reference | Jain, Srivastava, Ramprasad et al., *polyGen: A Learning Framework for Atomic-Level Polymer Structure Generation*, arXiv:2504.17656; published Chem. Mater. (2025). Read at `https://pmc.ncbi.nlm.nih.gov/articles/PMC12461786/` (**fetched**) |
| Entries | **3,855 DFT-optimized infinite polymer-chain structures**, max **208 atoms** incl. H. Split 3,084 / 386 / 385 |
| Structure representation | **1D-periodic infinite chain**, atomic coordinates (the generative target) |
| Properties + how computed | Set was built to compute the **electronic band gap Eg**. DFT validation runs reported with **VASP, GGA, DFT-D3, 520 eV cutoff**; full protocol deferred to SI |
| Entries per property | Not stated; band gap presumably on all 3,855 |
| Real vs hypothetical | **Not stated in the paper.** It stresses diversity of repeat-unit chemistry and linear/branched conformations. Given the Ramprasad-group lineage (section 1), assume **substantially enumerated/hypothetical** — do not claim "real" |
| Licence | **Not specified anywhere visible** |
| Access method | WARNING — **the paper's data-availability statement says the dataset "is available on … Khazana (https://khazana.gatech.edu/dataset)". I enumerated all 33 download links on that page and NONE corresponds to polyGen / polyChainStructures.** The newest polymer item listed is `Poly24` (PolyGET). **As of 2026-09-11 the dataset does not appear downloadable at the cited location**; it would have to be requested from the authors |
| **Verdict** | **Structures only, no released property table, and the advertised download is missing. Unusable as a hidden table today.** |
| verified_by | fetched (paper + exhaustive enumeration of the Khazana download list) |

---

## 5. PolyOmics — RadonPy Consortium (2025/2026) — BEST MD ANALOGUE

| Field | Value |
|---|---|
| Name | **PolyOmics** |
| Year | 2025 (arXiv Nov 2025); README (C) 2026 |
| Reference | Yoshida, Hayashi, Furuya *et al.* (~105 co-authors), *Omics-scale polymer computational database transferable to real-world artificial intelligence applications*, **arXiv:2511.11626** (`https://arxiv.org/abs/2511.11626` **fetched**; overview `https://www.alphaxiv.org/overview/2511.11626` **fetched**). Data: **`https://huggingface.co/datasets/yhayashi1986/PolyOmics`**, dataset DOI **10.57967/hf/7475** (README + files **downloaded and parsed**) |
| Entries | README (verbatim, **fetched**): `general_polymers_with_sp_abbe_dynamic-dielectric.csv` **73,045 general polymers**; `cellulose.csv` **50,661**; `PFAS.csv` **3,821**; `biodegradable_candidate_polyester.csv` **357 polyesters + 26 polycarbonates**; `ladder_polymers.csv` **519**; `small_molecules.csv` **23,361**; `chi_parameter/` **93,331 polymers** x 19 solvents. Paper/overview: **>10^5 polymeric materials, 62 distinct properties, >7.3 M property entries**, ~100 M node-hours on **Fugaku** over 4 years, 260 researchers / 48 institutions. (A third source — the Notre Dame polymer-data workshop page, `https://polymerdataworkshop.nd.edu/info/`, **fetched** — quotes "**81 properties for 130,000 polymers … 5 million data points**". The three counts disagree; prefer the README per-file counts, which I verified directly) |
| Structure representation | **SMILES** (`smiles_list`, `smiles_1..4`, terminator SMILES), plus copolymer ratios, tacticity, DP, chain counts. Raw **MD snapshots as JSON** in 21 per-class `.tar.gz` archives (PAMD, PEST, PI, PSTR, …) |
| Properties + how computed | I downloaded `general_polymers_with_sp_abbe_dynamic-dielectric.csv` (**196,910,783 bytes; 95,335 data rows x 259 columns**) and counted non-nulls directly. **Force field: `GAFF2_mod` on 100% of rows.** **Monomer-level QM: `wb97m-d3bj` on 94,726 rows** (Psi4 DFT — used for charges *and* as HOMO/LUMO/dipole/polarizability labels). MD engine LAMMPS; RadonPy/RDKit/Psi4/LAMMPS versions stored per row |
| Entries per property (**counted first-hand**) | `density` **95,335** · `static_dielectric_const` **95,335** · `Rg` **95,335** · `Cp` **95,312** · `bulk_modulus` **95,312** · `self-diffusion` **95,311** · `qm_homo_monomer1` / `qm_lumo_monomer1` **94,740** each · `refractive_index` **93,488** · `fractional_free_volume` **87,849** · `thermal_conductivity` **81,405** · `sp_total` (solubility parameter) **71,848** · **`tg` (glass transition) 56,064** · `abbe_number_sos` **18,942**. Plus Cv, compressibility, thermal expansion (linear + volumetric), thermal diffusivity with full decomposition (`TC_bond`, `TC_angle`, `TC_pair`, …), `dielectric_const_dc`, `efdp_permittivity_real/imaginary`, `dielectric_loss_tan`, nematic order parameter, free volume, cell volume |
| Real vs hypothetical | **Predominantly VIRTUAL.** Per the alphaXiv overview of the paper: ~73,000 general polymers generated by **chemical language models and rule-based algorithms (SMiPoly)**; ~50,000 cellulose derivatives; **PoLyInfo is used as the experimental validation / transfer target, not as the structure source**. README is explicit that entries are **"isotropic amorphous systems"** lacking crystallinity, orientation and processing history |
| Licence | **CC BY 4.0.** README verbatim: *"(C) 2026 The RadonPy Consortium. This dataset is released under the **Creative Commons Attribution 4.0 International (CC BY 4.0)** license. Redistribution and reuse are permitted under the terms of CC BY 4.0. Please provide appropriate attribution when using or redistributing the dataset."* HF API confirms `license: cc-by-4.0`, **`gated: False`** |
| Access method | Anonymous HF download; plain CSV; `curl` works with no token (I pulled the 197 MB file). Also loadable via `datasets` with named configs (`general_polymers`, `cellulose`, `pfas`, …) |
| CAVEAT | The `chi_parameter/` files are **ML-ESTIMATED, not simulated** — the README says so explicitly. Exclude them from any "physics-computed" claim |
| **Verdict** | **By far the best physics-simulated polymer property table in existence: 56k MD Tg, 95k density and dielectric constant, 81k thermal conductivity, all SMILES-keyed, CC BY 4.0, one-command download. Its only defect as a QMOF analogue is that the polymers are mostly virtual rather than synthesized.** |
| verified_by | fetched (arXiv, alphaXiv, HF API, README, and the 197 MB CSV parsed locally) |

---

## 6. RadonPy original benchmark (Hayashi et al. 2022) — REAL polymers, but data NOT released

| Field | Value |
|---|---|
| Name | RadonPy 1,070-polymer benchmark |
| Year | 2022 |
| Reference | Hayashi, Shiomi, Morikawa, Yoshida, *RadonPy: automated physical property calculation using all-atom classical molecular dynamics simulations for polymer informatics*, npj Comput. Mater. 8, 222 (2022). arXiv:2203.14090 **PDF downloaded and text-extracted locally**; npj page `https://www.nature.com/articles/s41524-022-00906-4` **fetched (HTTP 200)** |
| Entries | **1,138 homopolymers attempted; 1,070 succeeded at least once; 1,001 succeeded >=3x; 759 succeeded all 5x** (verbatim from the extracted paper text) |
| Structure representation | SMILES repeat unit -> built amorphous simulation cell |
| Properties + how computed | **15 MD properties** (thermal conductivity, density, Cp, linear & volumetric expansion coefficients, refractive index, …). Force field **GAFF2**; charges/conformers via **Psi4 DFT**; MD in **LAMMPS**; NEMD for thermal conductivity with per-term decomposition. Run mainly on **Fugaku** |
| Real vs hypothetical | **REAL — this is the key point.** Verbatim: *"The PoLyInfo database contains 15,335 homopolymers … Among these, we selected 1,138 unique homopolymers as the calculation target"*, filtered to neat resin, no additives/fillers/dopants, 273–323 K, amorphous, linear topology. **These are synthesized, experimentally-characterised polymers** |
| Entries per property (experimental validation N) | density **N=382**, thermal conductivity **N=34**, refractive index **N=107**, Cp **N=66**, linear expansion **N=165**, volume expansion **N=144** |
| Licence / access | **NOT RELEASED.** npj Data-availability statement, verbatim: *"The data that support the findings of this study are available from the corresponding authors upon reasonable request."* Code-availability points only to `github.com/RadonPy/RadonPy` (README verified: software library only, **no bundled property dataset**). The arXiv preprint says "The calculated dataset is provided in the Supporting Information", but the SI table of contents I extracted lists **only Figures S1–S4**, no data table |
| **Verdict** | **Conceptually the *perfect* QMOF analogue — 1,070 REAL PoLyInfo polymers with simulated thermophysical properties, and the paper's own closing line invokes exactly that framing ("just like the first-principles computational database for inorganic crystals"). But the table is on-request-only, so it cannot serve as a blind hidden table. PolyOmics is its public successor, at the cost of switching to virtual polymers.** |
| verified_by | fetched (arXiv PDF parsed locally; npj Data-availability string extracted from live HTML) |

---

## 7. HTP-MD — polymer electrolyte MD database (MIT + Toyota Research Institute)

| Field | Value |
|---|---|
| Name | **HTP-MD** (htpmd.matr.io) |
| Year | 2022–2023 |
| Reference | *A cloud platform for sharing and automated analysis of raw data from high-throughput polymer MD simulations*, APL Machine Learning 1, 046108 (2023) — **publisher page returned HTTP 403, not read**; preprint arXiv:2208.01692. Underlying simulations: Nat. Commun. 13, 3415 (2022), doi 10.1038/s41467-022-30994-1 |
| Entries | **6,024 unique amorphous polymer electrolytes / 6,286 MD trajectories, ~5.7 TB raw** (search-result-only; consistent across multiple snippets). Distilled table: **`PolyGen-train-set-from-HTP-MD.csv`** in `github.com/TRI-AMDD/PolyGen`, Zenodo DOI `10.5281/zenodo.14261933` (search-result-only) |
| Structure representation | SMILES + CIF structures + LAMMPS trajectories |
| Properties + how computed | **Ionic conductivity, Li+/TFSI- and polymer-chain diffusion coefficients, transference number, molality, MSD time series, CIF structure.** **LAMMPS** with **PCFF+** force field (TFSI- charges adjusted), LiTFSI salt at **353 K** — verified from the `TRI-AMDD/htp_md` README I fetched |
| Real vs hypothetical | **HYPOTHETICAL** — polymers filtered from **53,362 ZINC-derived structures** (H, C, F, S, P, O, N only) for synthesizability + electrolyte plausibility |
| Licence | **Not stated in the README.** The repo embeds GPL-licensed pizza.py code (governs the *code*, not the data). `https://www.htpmd.matr.io/` **fetched but renders as an empty JS shell — no terms of use retrievable** |
| Access method | Web UI (JS app), analysis library from `github.com/TRI-AMDD/htp_md`, plus the PolyGen CSV extract |
| **Verdict** | **Large, single-domain (Li-battery electrolytes), one headline property (ionic conductivity) — structurally the most QMOF-like MD set after PolyOmics, but hypothetical ZINC-derived chemistries and an unstated data licence.** |
| verified_by | fetched (GitHub README; htpmd.matr.io shell); search-result-only (6,024/6,286 counts, Zenodo DOI) |

---

## 8. Smaller / single-paper MD releases requested in scope

| # | Dataset | Year | Entries & properties | Method | Real? | Data public? | Licence | Verdict |
|---|---|---|---|---|---|---|---|---|
| 8.1 | **Marti et al., biopolymer Tg** (Nextmol + L'Oreal). ACS Appl. Polym. Mater. (2024), doi 10.1021/acsapm.3c03040. Page read: `https://www.nextmol.com/resources/paper-predicting-glass-transition-temperature-of-biopolymers/` (**fetched**) | 2024 | **58 homopolymers + 488 copolymers = 546 polymers**; MD Tg. ML surrogate MAE 19.34 K, R2 0.83. (**The "2,184 simulations" figure was NOT confirmed by any page I opened**) | All-atom MD; **force field and engine not stated on any page I could reach** (ACS and ChemRxiv both returned 403) | Biopolymers, largely real cosmetics-relevant chemistries, but copolymer compositions enumerated | **Only the trained ML MODEL is public** (`https://biopolymer-ml-pub.nextmol.com/`). **Raw Tg table not located** | n/a | NOT usable — model, not data |
| 8.2 | **Afzal et al., thermophysical MD** (Schrodinger). *High-Throughput Molecular Dynamics Simulations and Validation of Thermophysical Properties of Polymers for Various Applications*, ACS Appl. Polym. Mater. 3, 620 (2021), doi 10.1021/acsapm.0c00524 | 2021 | **315 polymers**, glass transition temperature + thermophysical properties; >10 GPU-years | **Desmond** GPU MD, **OPLS3e** force field | **REAL** — "the accuracy of MD simulations for Tg prediction was validated across an extensive range of polymers" | **Not confirmed.** ACS page 302 -> paywall; ChemRxiv full text 403. Assume SI-only | Unknown | Real polymers, but release unverified. **search-result-only** |
| 8.3 | **Zheng et al., vitrimers**, Digital Discovery 4, 2559 (2025) | 2024/25 | **1,000,000 hypothetical vitrimers sampled from 2.5e9 combinations of 50k carboxylic acids x 50k epoxides (ZINC15); of these 8,424 have MD Tg**; 90/10 train/test | MD Tg, then Gaussian-process calibration against literature experimental Tg | **HYPOTHETICAL** | Not verified in this session | Unknown | 8,424 MD labels is a usable size; hypothetical; licence unchecked. **search-result-only** |
| 8.4 | **Bhati et al., binary copolymer Tg** (Schrodinger). Zenodo **10.5281/zenodo.19242815**, v1 2026-03-27 (**record fetched; files downloaded**) | 2026 | **I downloaded the files: `md_tg_data.csv` has only 49 data rows** (each = 3 MD replicas + weighted average + calibrated value); `md_elastic_constant_data.xlsx` covers **30 copolymers**; `experimental_dataset.csv` = **665 rows**. The large files (`enumerated_copolymer_tg_prediction.csv`, 25.9 MB; `enumerated_elastomer_copolymer_tg_prediction.csv`, 5.3 MB) are **ML PREDICTIONS, not simulations** | MD (Schrodinger stack) + ML | Copolymers of real monomers, enumerated compositions | **Yes, fully open** | **Creative Commons Attribution 4.0 International (CC-BY-4.0)** | **Only ~49 genuine MD Tg values — do NOT cite the 25.9 MB file as simulated data** |
| 8.5 | **Phan et al., gas permeability**, npj Comput. Mater. 10, 186 (2024), arXiv:2406.14809 (**HTML fetched**) | 2024 | **584 simulated polymer-gas systems** (342 with experimental counterparts) across **CO2, CH4, O2, N2, H2, He**; experimental side = **5,007 points (3,748 permeability / 709 diffusivity / 550 solubility) over 820 unique polymers from 84 publications + Polymer Handbook** | **GAFF2** polymer + **TraPPE** gases; MD diffusivity (100–200 ns production, 27 chains x ~150 atoms per box); **Widom-insertion Monte Carlo** solubility; permeability P = D x S | Simulation targets drawn from the experimental membrane literature -> **largely REAL membrane polymers** | **Yes** — paper states *"All data, experimental and simulation, are available free of charge at [GitHub repository]"* (PSP package + MD/MC code + polyGNN training code). The literal GitHub URL was not resolvable from the HTML I read | Paper CC-BY (npj); repo terms say "available for academic use" | **Best small real-polymer + simulated-property set found.** 584 MD/MC permeability systems on real membrane polymers |
| 8.6 | **Huang & Ju, thermal conductivity**, Mater. Today Phys. 44, 101438 (2024); tutorial J. Appl. Phys. 135, 171101 (2024) | 2024 | **1,144 polymers with MD thermal conductivity** used to train a DNN; a sibling Wu et al. study reports 501 backbone polymers and a 1,243-polymer Rg correlation | Classical MD (NEMD/EMD) | Mixed; design space largely enumerated | **Not verified as publicly released** | Unknown | Treat as unreleased until checked. **search-result-only** |

---

## 9. Out of scope but worth recording (not first-principles / not simulated)

| Resource | What it is | Why it is NOT a DFT/MD hidden table |
|---|---|---|
| **PoLyInfo** (`polymer.nims.go.jp`) | ~32k homopolymers/copolymers/blends, ~500k **experimental** data points (per Notre Dame workshop page, **fetched**) | Experimental; registration-gated. It is the *ground truth* against which the simulation sets are validated |
| **OpenPoly** (Chin. J. Polym. Sci. 43, 1749 (2025), doi 10.1007/s10118-025-3402-y) | **3,985 unique polymer-property data points over 26 properties**, literature-mined + manually validated; benchmark code `github.com/WangGroupFDU/Openpoly_benchmark` | **Experimental**, not computed. Its own paper criticises Khazana for being CIF-only and ML-pipeline-unfriendly |
| **NIST PPPDB** (`pppdb.uchicago.edu`, NIST + CHiMaD) | Flory-Huggins chi parameters + glass transition temperatures | Experimental, literature-extracted. NIST's computational side is **WebFF** (force-field repository) and **COMSOFT** — tooling, not property tables |
| **Conducting-polymer DFT set** (J. Chem. Inf. Model. 2025, `https://pmc.ncbi.nlm.nih.gov/articles/PMC12152970/`, **fetched**) | **3,120 donor-acceptor conjugated polymers** with **DFT band gap + hole reorganization energy**; **B3LYP / 6-311+G(d)**, code **Jaguar**; built from **60 donor + 52 acceptor units that are "successfully synthesized and characterized"**, combinatorially recombined via R-groups; released in the **Supporting Information**; article **CC-BY 4.0** | **Actually in scope and a strong find** — 3,120 DFT band gaps on real-building-block conjugated polymers. Downsides: SI-only distribution (no DOI'd archive), and the D-A pairs are enumerated rather than individually synthesized |
| **ToPoRg-1342** (`https://zenodo.org/records/10672434`) | 1,342 topologically diverse **coarse-grained** polymers, single-chain radii of gyration | Coarse-grained toy models, not chemistry-resolved |
| **PI1M / OMG / SMiPoly / POINT2 / PolyUniverse** | 1e6–1.2e7 computationally generated polymer structures | Structures only, **no property labels** |
| **Dielectric DFPT dump** `doi 10.5281/zenodo.10456384` | DFPT dielectric dataset | Inorganic dielectrics, not polymers. **search-result-only** |

---

## 10. Ranked recommendation for LLM4POL

1. **Khazana `Polymer Properties` (Kuenneth 2021)** — 3,655 SMILES x 8 DFT properties, **3,380 DFT band gaps**. Structurally identical to QMOF (identifier -> DFT band gap), 71 kB, no login. Weaknesses: no licence text; mixed real/hypothetical.
2. **PolyOmics** — 73,045 polymers x up to 55 properties, CC BY 4.0, **56,064 MD Tg / 95,335 density and static dielectric constant / 81,405 thermal conductivity**. The only polymer resource at true QMOF scale with usable scalar labels. Weakness: polymers mostly virtual; labels are GAFF2 MD, not DFT.
3. **Khazana high-voltage insulators (Kamal 2021)** — 4,209 DFT chain band gaps. Hypothetical, no licence.
4. **Phan 2024 gas permeability** — 584 MD/MC polymer-gas systems on **real** membrane polymers + 5,007 experimental points. Best real-polymer/simulated-property pairing; small.
5. **HTP-MD** — 6,024 polymer electrolytes with MD ionic conductivity. Hypothetical; licence unstated.

Honourable mention: the **JCIM 2025 conjugated-polymer set** (3,120 B3LYP band gaps, CC-BY, SI-only) is a genuine
fourth option if SI-only distribution is acceptable.

### Which is the best QMOF analogue, and why

**If "QMOF analogue" means *same shape* — a mid-size table mapping a structure identifier to a first-principles
electronic-structure label — the answer is the Khazana `Polymer Properties` table from Kuenneth et al. 2021.**
It holds 3,655 polymer SMILES carrying 6,265 DFT-computed values, of which 3,380 are HSE06-grade chain band gaps
and the rest are DFT dielectric constants, refractive indices, electron affinities, ionization energies,
crystallization tendencies and atomization energies — produced with the same VASP / HSE06 / DFPT protocol
documented inside the 2016 Sci Data CIFs. It downloads in one anonymous HTTP request as a single 71 kB CSV, needs
no parsing beyond `pandas.read_csv`, and an agent that has never seen it can be asked "what is the DFT chain band
gap of this SMILES?" exactly as QMOF is queried. Its two defects: it is ~6x smaller than QMOF's 20,373 rows, and
unlike QMOF's exclusively synthesized MOFs only a minority of its repeat units correspond to polymers anyone has
actually made — and it ships with **no licence statement at all**, only a citation request.
**If instead "QMOF analogue" means *same role* — the big open computational database that unlocks informatics for a
material class — the answer is PolyOmics**, the only polymer resource at genuine QMOF scale: 73,045 general
polymers with 56k MD glass-transition temperatures, 95k densities and static dielectric constants and 81k thermal
conductivities, explicitly CC BY 4.0, one `curl` away, generated for precisely this purpose on ~100 M Fugaku
node-hours by a 260-person consortium. The honest caveat LLM4POL must state rather than paper over is that
**neither is QMOF: the one dataset that truly matches QMOF's "real, synthesized structures + simulated labels"
criterion is the RadonPy 2022 benchmark of 1,070 PoLyInfo homopolymers — and its authors released only the
software, keeping the property table "available from the corresponding authors upon reasonable request."**
For a polymer QMOF built on *real* structures, the field currently has no public option at scale.
