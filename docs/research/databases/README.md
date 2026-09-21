# Polymer database survey — 2026-09-11

Three independent surveys asking one question: what plays the role that hMOF, QMOF and
CoRE-MOF play in LLM4MOF. Every claim in these reports is tagged `fetched` or
`search-result-only`; treat an untagged number as unverified.

| File | Scope |
|---|---|
| `DB-computed.md` | Large computed, generated and enumerated databases — the hMOF role |
| `DB-firstprinciples.md` | DFT and physics-simulation databases on known structures — the QMOF role |
| `DB-experimental.md` | Measured-property databases and their licensing — the CoRE-MOF role |
| `openpoly_readme.md`, `pm_datasets.md` | Raw metadata captured during the experimental survey |

## The result in one table

| Layer | LLM4MOF | Polymer equivalent | Licence | Verdict |
|---|---|---|---|---|
| Hypothetical structures, simulated labels | hMOF, 51,163 | **PolyOmics**, 95,335 general polymers | CC BY 4.0, ungated | Strong match |
| Real structures, first-principles labels | QMOF, 20,373 | **none public** | — | Empty |
| Real structures, measured labels | CoRE-MOF | PoLyInfo (closed) or ~39k points scattered across open sets | Contract-gated or mixed | Open but thin |

## PolyOmics — verified directly, not taken from the report

`huggingface.co/datasets/yhayashi1986/PolyOmics`, DOI 10.57967/hf/7475, arXiv:2511.11626,
RadonPy Consortium. CC BY 4.0, `gated: false`. `general_polymers` config downloaded and
counted on 2026-09-11: **95,335 rows, 259 columns, 78,379 unique repeat units**, all at 300 K,
force field `GAFF2_mod`, monomer QM at wb97m-d3bj. Structures are largely **virtual**, from
chemical language models and SMiPoly, which is exactly hMOF's position.

| Property | Rows | Share |
|---|---|---|
| density | 95,335 | 100% |
| Rg, self-diffusion, Cp, bulk modulus, static dielectric, expansion coefficients | ~95,300 | 100% |
| refractive index | 93,488 | 98.1% |
| free volume, fractional free volume | 87,849 | 92.1% |
| thermal conductivity | 81,405 | 85.4% |
| cohesive energy density (`sp_ced`) | 71,848 | 75.4% |
| glass transition (`tg`) | 56,064 | 58.8% |
| Abbe number | 18,943 | 19.9% |

Tg together with `sp_ced` and fractional free volume: 41,026 rows. `tg` contains failed fits
(maximum 1.08e6 K); filter on `tg_rmse`. Median 488.5 K. Tacticity is a column: atactic
45,032, none 48,790, isotactic 951, syndiotactic 8. Other configs: cellulose 50,661, small
molecules 28,159, PFAS 5,810, non-ladder 1,050, ladder 519, biodegradable polyesters 372,
plus per-solvent Flory-Huggins chi tables and per-class MD snapshots.

## Two findings that change what may be used

**A relabelling trap.** The PolyMetriX curated Tg set (Zenodo, CC BY 4.0, 7,367 experimental
Tg) looks like a clean CoRE-MOF analogue and was independently recommended by two of the three
survey lanes. It is **97.3% PoLyInfo data**: PolyMetriX names GREA as its source for
7,170 of 7,367 rows, and the GREA paper states that its glass-transition, melting and density
sets are collected from PoLyInfo. The same relabelling pattern recurs at least three more
times in this space. A permissive licence on a derived file does not launder the original
terms. Check provenance to the primary source before adopting any "open experimental" polymer
set.

**The PoLyInfo carve-out is narrower than assumed.** The research-deliverable carve-out
attaches to Article 10(2) and 10(3) only, not to 10(1) or 10(5). Publishing values in a paper
is permitted; bulk acquisition never is. A machine-readable route exists (PoLyInfoRDF) but is
contract-gated. NIMS has open-sourced the schema, ontology under CC BY 4.0 plus ShEx, while
keeping the values closed, so the **data model** may be adopted freely. The PolyOmics
consortium states in print that PoLyInfo experimental data could not be redistributed.

## The open experimental floor

Redistributable measured data, roughly 39,000 points across about 38 properties: polyVERSE
14,511 points including 5,212 gas-transport values over 851 polymers and 1,586 chi values with
per-row DOIs (GTRC licence, redistribution permitted but copyleft, and two files must be
dropped because they cite PoLyInfo); rhnet 16,004 rows over 107 polymers and 81 gases (MIT);
OpenPoly 3,985 points over 741 polymers (MIT); PolymerSolarCellsML 3,910 rows (MIT); Bhati
2026 copolymer Tg 666 rows (CC BY 4.0); Brierley-Croft PAEK 146 points (CC BY 4.0).

Disqualified: the Kaggle NeurIPS 2025 set, whose labels are MD-simulated, not measured. Free
to view but never redistributable: CAMPUS, ATHAS, CROW, MatWeb, the Polymer Handbook, Van
Krevelen.

A larger route exists and is unclaimed: literature mining. One group has deposited 720,308
property records under CC BY 4.0 with a data-descriptor paper using MIT-licensed tooling, an
unchallenged five-year precedent, and **no polymer-specific database of that kind has ever
been published**. Constraints: publisher text-and-data-mining agreements, two major publishers
restricting output to non-commercial use, and extraction quality near F1 0.67 for glass
transition, so manual verification would be required for benchmark-grade data.

---

## Direct analysis of PolyOmics `general_polymers` — 2026-09-11

Computed locally on the downloaded table, not taken from any survey report.

### A broken column, and the right one

`static_dielectric_const` is **not usable as a dielectric constant**. Median 1.392, with 76.3%
of rows below 1.8, which is below any real polymer. It fails the Maxwell relation that
requires the static permittivity to be at least the square of the refractive index: **88.9% of
rows violate it**, and its rank correlation with the square of the refractive index is -0.05.

`dielectric_const_dc` is the correct column. Median 2.868, 88% of rows between 2 and 5,
**zero Maxwell violations**, rank correlation 0.520 with the square of the refractive index,
93,488 rows. A dynamic measurement, `efdp_permittivity_real`, exists for 1,084 rows and agrees
(median 2.90).

This is the same class of defect as the mislabelled elongation column in the PoLyInfo export.
Any work using PolyOmics must pick `dielectric_const_dc` and say so.

### The chain-length layer is a simulation parameter, not an industrial variable

| Column | Median | Range | Unique values |
|---|---|---|---|
| DP | 23 | 6 to 496, concentrated 12 to 32 | 58 |
| Mn | 7,491 | 4,519 to 37,710 | 30,657 |
| Mw/Mn | **1.0** | 1.0 for every row | **1** |
| chains per cell | 10 | 5 to 10 | 2 |

Every cell is perfectly monodisperse and roughly an order of magnitude lighter than an
engineering grade. These are MD cell-construction settings. PolyOmics cannot support design
over molecular weight or dispersity; that would need new simulations at higher degree of
polymerisation, or experimental data.

### The industrial property triple is large and the trade-off is weak

Rows carrying thermal conductivity, a physical `dielectric_const_dc`, and a Tg whose fit
survives a 100 to 900 K filter: **43,561**. The same 43,561 also carry refractive index.

Rank correlations on that set:

| | thermal cond. | dielectric | Tg |
|---|---|---|---|
| thermal conductivity | 1.000 | 0.170 | 0.010 |
| dielectric | 0.170 | 1.000 | 0.199 |
| Tg | 0.010 | 0.199 | 1.000 |
| cohesive energy density | 0.355 | 0.631 | 0.223 |
| fractional free volume | -0.069 | -0.436 | 0.291 |
| radius of gyration | 0.304 | 0.328 | 0.394 |
| density | -0.270 | 0.486 | 0.293 |

Thermal conductivity and Tg are effectively independent. Cohesive energy density is the shared
driver of both thermal conductivity and permittivity, which is where a trade-off would come
from, yet at the tails the two barely conflict: polymers in the top decile of thermal
conductivity **and** the bottom quartile of permittivity number **1,140, or 2.62% of the set**,
against 2.5% under exact independence.

That window has a clear and physically sensible signature relative to the whole set:

| | window | all |
|---|---|---|
| radius of gyration | 30.54 | 20.19 |
| density | 0.967 | 1.130 |
| fractional free volume | 0.221 | 0.187 |
| cohesive energy density | 251 | 295 |
| thermal conductivity | 0.349 | 0.239 |
| dielectric constant | 2.462 | 2.894 |

Extended, low-density, high-free-volume, weakly cohesive chains carry heat well without paying
in permittivity: transport along the backbone rather than through dense packing. Chain
dimension, not density, is the controlling variable — and it is measured in the same table as
the targets, which is what an attribution gate needs.
