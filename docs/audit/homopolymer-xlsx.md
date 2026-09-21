# Data-quality audit: 230227_Homopolymer_CanonicalSMILES.xlsx

Audited file: `C:/Users/molsim/Dropbox/Work to do/LLM4POL/230227_Homopolymer_CanonicalSMILES.xlsx`
Sheet: `Homopolymer_IBMSMILES_wPD_ver2` (the only sheet). 13,725 rows x 12 columns.
Cross-referenced against `polymer_final_0824.csv` (cp949) for id-namespace and unit checks.
Tools: python 3.13 (anaconda base), pandas, openpyxl, rdkit 2025.09.6, scipy. All numbers below were computed in this session; scripts were run as python heredocs from the Bash tool. Cached intermediates: `homo.pkl` (the sheet), `rdkit.pkl` (RDKit-canonical SMILES + validity), `coverage_matrix.csv`, all in this audit directory.

Legend: **[FACT]** computed number. **[INFERENCE]** my interpretation. **[CONTEXT]** literature-free background, not verified.

---

## 0. Executive summary (the things that matter for modelling)

1. **Column `Elongation_at_break_GPa` is NOT in GPa; it is percent (%).** Median 11, 95th pct 292.8, max 3000 (poly(butyl acrylate)); cis-polybutadiene = 1960.5. Only 3 of 1,059 values are < 1. The CSV's `elongation_at_break` (median 250, max 6190) is on the same scale. Rename to `elongation_at_break_pct` before use.
2. **`Tg_K` and `melting_temp_K` are genuinely Kelvin.** Tg_K min 138 K (poly(methyl ethyl siloxane)), median 410 K, no value < 100 K; Tg_K-273.15 lands on a distribution comparable to the CSV's degrees-C column (KS statistic 0.331 after subtracting 273.15 vs 0.906 raw). Values are all integer or half-integer (6,932 integers, 801 x.5, 0 others) - no `.15` fractions, so they were rounded/averaged at source, not converted by adding 273.15.
3. **Tensile modulus / stress at break are plausibly GPa** (medians 2.1 GPa and 0.081 GPa = 81 MPa), but the tails contain almost-certain MPa-for-GPa errors: stress at break 64.02 GPa (P100143), 35.08 (P100126), 34.11 (P070232); modulus 180.75 GPa (P190001 polyketone), 180 (P100247), 150 (P160103). 14 rows have stress > modulus.
4. **Conductivity is only partially the reciprocal of resistivity.** On the 1,268-row overlap, Pearson r(log10 rho, log10 sigma) = -0.858; only 842/1,268 (66.4%) satisfy |log10(rho*sigma)| < 0.5; 371 rows (29%) are off by >= 1 decade, always with sigma > 1/rho. Conductivity has physically impossible values: 7 rows > 1000 S/cm, max 1.9e7 S/cm for poly(glycine) (P100169). Do not treat the two columns as redundant, and clip/inspect before log-transforming.
5. **2,338 rows (17.0%) carry no property at all**, and they include the most famous polymers: polyethene P010001, polystyrene P020001, PMMA P040048, PVC P050002, PET P090027, PDMS P170031, PTFE P050006, PVA P030001, PAN P030010, PEO P070013, PCL P090089, PLA P090176 (14 of 21 well-known names checked have zero properties). Property coverage therefore does **not** track how well studied a polymer is; the property join looks incomplete.
6. **pid is unique (13,725/13,725) and is a different namespace from the CSV**: xlsx pids are `P` + 2-digit class code (01..52) + 4-digit serial; CSV `polymer_id` is exclusively `P90xxxx` (P900001..P908686); CSV component ids are `CU` + 6 digits. Overlap of xlsx pid with CSV polymer_id = 0, with component ids = 0, with sample_id = 0. The digit part of 1,353 CU ids coincides with an xlsx pid digit part, but only 293/852 testable pairs are the same structure, so the coincidence is not a usable join key.
7. **SMILES are clean**: 0 RDKit-invalid strings in either column; CanonSMILES is exactly RDKit's canonical form for 13,579/13,725 rows (the other 146 differ only in atom ordering: 102 contain bracketed metals/metalloids, 3 have `*=`/`=*`, 43 fused-imide aromatics); 91 CanonSMILES strings are shared by 2-4 different pids (192 rows, 101 excess). 41 of these 91 groups are cis/trans/cyclo isomers collapsed by loss of stereo marks (only 30 CanonSMILES carry `@`, `/` or `\`); at least some are name/SMILES mismatches (P373700 vs P373706).

---

## 1. pid namespace

**[FACT]**
- 13,725 pids, 13,725 unique, 0 duplicates. All match `^P[0-9]{6}$` (13,725/13,725); no other id shape.
- Structure: `P` + `CC` (2-digit class, 43 distinct values: 01-21, 31-52 with no 22-30) + `SSSS` (4-digit serial).
- Class sizes (top): P37 2,320; P43 2,224; P39 889; P46 805; P40 740; P07 693; P38 662; P34 633; P09 585; P10 577. Smallest: P19 4; P48 8; P35 17.
- The 3rd digit carries sub-series information: serial ranges cluster at `0001-0999` (third digit 0), `2001-2999` (third digit 2, only in classes 31-52), `4xxx` (third digit 4) and `9xxx` (third digit 9). Suffix buckets: 1-10: 363 rows, 11-100: 2,088, 101-1000: 4,046, 1001-2000: **0**, 2001-4000: 6,612, 4001-5000: 587, 5001+: 29.
- Class-code exemplars (first two iupac names of each class): P01 polyethene / poly(prop-1-ene) (polyolefins); P02 polystyrene / poly(2-methylstyrene); P03 poly(vinyl alcohol) / poly(acrylaldehyde); P04 poly(acrylic acid) / poly(methyl acrylate); P05 poly(vinyl fluoride) / poly(vinyl chloride); P06 trans-polyisoprene / cis-1,4-polyisoprene (dienes); P07 polyformaldehyde (polyoxides); P08 poly(methylene sulfide); P09 poly(ethylene oxalate) (polyesters); P10 poly(3-aminopropionic acid) (polyamides); P12 ureas; P13 polyimides; P14 anhydrides; P15 carbonates; P16 imines; P17 siloxanes; P18 phosphazenes; P19 ketones; P20 sulfones/sulfonates; P21 poly(1,4-phenylene) (aromatics); P31-P52 mirror P01-P22 with a second series of the same chemical classes (P31 cycloaliphatics, P32 styrenes, P33 vinyls, P34 (meth)acrylates, P35 halo-olefins, P36 dienes, P37 ethers, P38 sulfides/thiophenes, P39 esters, P40 amides, P41 urethanes, P42 ureas, P43 imides, P44 anhydrides, P45 carbonates, P46 imines/pyrroles, P47 silanes/siloxanes, P48 phosphazenes, P49 selenium, P50 sulfones, P51 arylenes, P52 misc). **[INFERENCE]** This matches PoLyInfo's public "P + class + serial" homopolymer id scheme; the class codes are PoLyInfo polymer-class codes.
- Rows are sorted by pid ascending except 6 decreases (file is nearly but not perfectly pid-sorted).

**Comparison with the CSV (polymer_final_0824.csv)**
- CSV `polymer_id`: 42,557 rows, all `P90xxxx` (prefix `P90` count 42,557), 7,385 unique, range P900001..P908686. Zero overlap with xlsx pid.
- CSV `sample_id`: 19-char strings like `0014863-001-002-001`; zero overlap with pid.
- CSV component ids (`component1`/`component2`, 48,299 non-null): 45,636 are `CU` + 6 digits (2,671 unique CU ids), the rest are literal SMILES/fragments (`(C...`, `L1...`, `JU...`, `B(...`, etc.). Zero exact overlap with pid.
- Digit-part coincidence test: 1,353 of 2,671 CU ids share their 6 digits with an xlsx pid; of 852 such pairs where the CSV supplies a SMILES for the CU, only 293 (34%) are the same RDKit-canonical structure (e.g. P010001 polyethene `*CC*` vs CU010001 `*C*`; P040055 poly(tert-butyl methacrylate) vs CU040055 `*CC(c1ccccc1)*`). **Conclusion: CU ids are a separate (monomer/constitutional-unit) namespace, not the homopolymer pid namespace, and must not be joined on digits.**
- Name join: 17 of 7,268 CSV polymer_names match an xlsx iupac exactly (case-insensitive). Structure join: the 96 CSV rows with exactly one SMILES map to 139 xlsx rows, 28 of which have Tg on both sides, but those CSV rows are labelled as copolymers, so the join is not meaningful.

Repro:
```python
import pandas as pd
df=pd.read_excel("C:/Users/molsim/Dropbox/Work to do/LLM4POL/230227_Homopolymer_CanonicalSMILES.xlsx")
p=df.pid.astype(str); print(p.nunique(), p.str.fullmatch(r"P\d{6}").all(), p.str[:3].value_counts().sort_index().to_dict())
cs=pd.read_csv("C:/Users/molsim/Dropbox/Work to do/LLM4POL/polymer_final_0824.csv",encoding="cp949",low_memory=False)
print(cs.polymer_id.str[:3].value_counts().to_dict(), len(set(p)&set(cs.polymer_id)), len(set(p)&set(pd.concat([cs.component1,cs.component2]).dropna())))
```

## 2. polymer_smiles vs CanonSMILES

**[FACT]**
- `polymer_smiles != CanonSMILES` in 6,702 rows; identical in 7,023.
- Unique strings: polymer_smiles 13,661; CanonSMILES 13,624; RDKit-canonical structures 13,624 (CanonSMILES already collapses everything RDKit would collapse).
- After RDKit re-canonicalisation both columns give the same structure in 13,725/13,725 rows (0 mismatches) - the two columns are alternative spellings of the same molecule in every row.
- `CanonSMILES == Chem.MolToSmiles(Chem.MolFromSmiles(CanonSMILES))` for 13,579 rows; 146 differ (102 contain bracketed metals/metalloids such as `[Sn]`, `[Ge]`, `[Na]`, `[Li]`, `[Si]`; 3 contain `*=`/`=*`; 43 are large fused-imide aromatics such as P130181). **[INFERENCE]** CanonSMILES was produced by an RDKit canonicaliser (an older RDKit version explains the 146 ordering differences).
- Duplicated CanonSMILES: 91 strings occur in 2-4 pids, covering 192 rows (101 excess rows). Top: `*C=CCC*` x4 (P010070 trans-polybutadiene, P010071 cis-polybutadiene, P010072 1,4-poly(buta-1,3-diene), P054499); `*C=C*` x3 (trans-/cis-/polyacetylene); `*CC(*)OCC(=O)OC` x3 (P330073-75, identical name 3 times); `*CCC(C)=C(*)C` x3 (2,3-dimethylbutadiene cis/trans); `*C=CCCC*` x3 (polycyclopentene); `*CCC=C(*)C` x3 (polyisoprene cis/trans); `*NC(CCC(=O)OC)C(*)=O` x3 (gamma-methyl glutamate, D/L); `*CCC=C(*)Cl` x3 (polychloroprene cis/trans); `*CC(*)c1ccccn1` x2 (poly(2-vinylpyridine) vs cyclo-); `*CCCCCCOC(=O)C=CC(=O)O*` x2 (hexamethylene fumarate vs maleate).
  - 27 groups have identical iupac (true duplicate entries), 64 have different names; 41 groups differ only by a cis/trans/cyclo/1,4- prefix (stereo/topology lost in SMILES).
  - Two groups look like SMILES assignment errors rather than isomers: P373700 (name: fluorinated ether) and P373706 (name: ureylene polymer) share one urea-containing SMILES; P370074 (biphenyl-4,4-diol / difluorobenzophenone) and P372152 (3,3',5,5'-tetramethyl variant) share the un-methylated SMILES.
  - Property conflicts inside duplicate-structure groups: Tg present in >= 2 members for 33 groups, 30 of them conflicting, max spread 169 K (P373700 383 K vs P373706 552 K); Tm 15 groups, 14 conflicting, max spread 165 K; density 11 groups, 11 conflicting, max spread 0.38. For an ML model these are identical inputs with different targets.
- `polymer_smiles` duplicates: 56 strings shared, 64 excess rows.
- `*` count distribution (identical in both columns): 2 stars 13,637; 3 stars 63; 4 stars 21; 0 stars 3; 8 stars 1 (P382512). Zero-star rows: P370214, P522049, P522050 (no attachment points at all - unusable as repeat units). 3- and 4-star rows are branched/cross-linkable units (e.g. P373835 `*OCCCCOc1nc(*)nc(*)n1`, P322201 `**Cc1ccc(...)`). 133 CanonSMILES have a double-bonded star (`*=`/`=*`, e.g. phosphazenes `*=NP(=*)(Cl)Cl`).
- RDKit validity: 0 invalid in polymer_smiles, 0 invalid in CanonSMILES (13,725/13,725 parse).
- Style: polymer_smiles uses `[*]` in 192 rows and `%nn` ring closures in 114; CanonSMILES has 0 `[*]`, 245 `%nn`; 13,722 CanonSMILES start with `*` (the 3 zero-star rows do not). 4 rows contain a `.` (counter-ions `[I-]`, `[Na+]`: P342374-76, P044508). Stereo marks present in 35 polymer_smiles / 30 CanonSMILES rows only.
- Elements present (rows): C 13,716, O 11,903, N 8,532, S 2,348, F 1,345, Si 714, P 438, Cl 398, Br 183, Na 43, Se 29, I 26, explicit H 24, Ge 14, B 13, Sn 13, Li 9, Fe 9, K 6, Co 4, As 4, Te 3, Ni 2, Ca 2, Cd 2, Pb 2, Zn 2. CanonSMILES string length: mean 57.8, median 52, min 3, max 306 characters.

Repro:
```python
from rdkit import Chem
ps,cs=df.polymer_smiles.astype(str),df.CanonSMILES.astype(str)
print((ps!=cs).sum(), cs.value_counts().gt(1).sum(), cs.str.count(r'\*').value_counts().to_dict())
print(sum(Chem.MolFromSmiles(s) is None for s in ps), sum(Chem.MolFromSmiles(s) is None for s in cs))
```

## 3. Property coverage

**[FACT]** non-null per column: Tg_K 7,733; melting_temp_K 3,696; density 1,651; volume resistivity 1,268; conductivity 1,296; elongation 1,059; tensile modulus 1,003; tensile stress 1,064.

Rows by number of non-null properties: 0 -> 2,338; 1 -> 6,881; 2 -> 2,861; 3 -> 707; 4 -> 731; 5 -> 136; 6 -> 57; 7 -> 12; 8 -> 2. So 0: 2,338 (17.0%), 1: 6,881 (50.1%), 2: 2,861 (20.8%), >=3: 1,645 (12.0%). 4,663 rows have Tg and nothing else.

Joint coverage matrix (rows with both non-null; diagonal = column count):

| | Tg | Tm | dens | rho | sigma | elong | E | sigma_b |
|---|---|---|---|---|---|---|---|---|
| Tg | 7733 | 1474 | 946 | 276 | 283 | 875 | 836 | 884 |
| Tm | 1474 | 3696 | 593 | 119 | 120 | 158 | 121 | 126 |
| dens | 946 | 593 | 1651 | 83 | 83 | 182 | 156 | 171 |
| rho | 276 | 119 | 83 | 1268 | 1268 | 69 | 62 | 62 |
| sigma | 283 | 120 | 83 | 1268 | 1296 | 69 | 62 | 62 |
| elong | 875 | 158 | 182 | 69 | 69 | 1059 | 896 | 959 |
| E | 836 | 121 | 156 | 62 | 62 | 896 | 1003 | 896 |
| sigma_b | 884 | 126 | 171 | 62 | 62 | 959 | 896 | 1064 |

Notes: every row with resistivity also has conductivity (1,268 = 1,268); 28 rows have conductivity only. All three mechanical properties together: 854 rows; any mechanical: 1,229. Tg and Tm together: 1,474.

Zero-property rows by class (fraction): P49 61%, P51 38%, P42 37%, P50 34%, P31 33%, P40 32%, P33 31%; by count: P37 387, P43 384, P40 234, P39 172, P38 167, P46 174, P34 164. 9 of the 40 `xx0001` "first entry of class" rows have zero properties. Well-known homopolymers with zero properties (14 of 21 checked): polyethene P010001, poly(prop-1-ene) P010002, polystyrene P020001, PVA P030001, PAN P030010, PMMA P040048, PVC P050002, PTFE P050006, PVDF P050003, PEO P070013, PET P090027, PCL P090089, PLA P090176, PDMS P170031. **[INFERENCE]** The property merge that produced this sheet did not cover the whole PoLyInfo property tables; coverage is not a proxy for data abundance, and any "polymers with data" filter will silently drop the canonical benchmark polymers.

Repro:
```python
props=['Tg_K','melting_temp_K','density_g_per_cm3','Volume_resistivity__ohmXcm','Electric_conduct_1_per_ohmXcm','Elongation_at_break_GPa','Tensile_modulus_GPa','Tensile_stressAt_break_GPa']
nn=df[props].notna(); print(nn.sum().to_dict(), nn.sum(axis=1).value_counts().sort_index().to_dict()); print(nn.astype(int).T @ nn.astype(int))
print(df[df.iupac.isin(['polystyrene','polyethene','poly(methyl methacrylate)'])][props].notna().sum(axis=1).tolist())
```

## 4. Units sanity per column

Quantiles (min / 1% / median / 99% / max), n:

| column | n | min | 1% | median | 99% | max | verdict |
|---|---|---|---|---|---|---|---|
| Tg_K | 7733 | 138 | 195 | 410 | 657 | 768 | Kelvin (see below) |
| melting_temp_K | 3696 | 211 | 248 | 461.75 | 768 | 853 | Kelvin |
| density_g_per_cm3 | 1651 | 0.23 | 0.86 | 1.23 | 1.87 | 2.9 | g/cm3, plausible |
| Volume_resistivity__ohmXcm | 1268 | 6.7e-8 | 0.035 | 1.05e7 | 7.8e17 | 2.5e18 | ohm cm; log10 range -7.17..18.40 |
| Electric_conduct_1_per_ohmXcm | 1296 | 1e-18 | 9.8e-18 | 1.1e-5 | 151 | 1.9e7 | S/cm with impossible upper tail |
| Elongation_at_break_GPa | 1059 | 0.45 | 1.5 | 11.0 | 712 | 3000 | **percent, not GPa** |
| Tensile_modulus_GPa | 1003 | 1e-5 | 0.0024 | 2.1 | 34.9 | 180.75 | GPa, tail suspicious |
| Tensile_stressAt_break_GPa | 1064 | 9e-5 | 0.00126 | 0.081 | 0.845 | 64.02 | GPa, tail suspicious |

No column contains negative, zero, or infinite values (n<=0 = 0 for all eight).

**Tg_K is Kelvin [FACT]**
- 0 values < 100 K, 0 values in (0,120) (the range where Celsius Tg values would sit), 4 values < 150 K (all siloxanes: P170074 138, P470046 141.5, P472310 143.5, P472023 148 - consistent with PDMS-type Tg ~150 K), 336 > 600 K, 10 > 700 K (all aromatic polyimides/polybenzoxazoles, max 768 K P080136).
- CSV `glass_transition_temperature` (n = 18,142, copolymers): min -151.35, median 52.55, max 455 - unambiguously Celsius. Two-sample KS statistic CSV vs Tg_K = 0.906 (raw) vs 0.331 (Tg_K - 273.15). Medians: CSV 52.55 C; Tg_K - 273.15 = 136.85 C. The residual difference is a population effect (homopolymer set is dominated by aromatic polyimides/polyethers P37/P43, ~4,500 rows), not a unit effect.
- Sanity anchors: cyclo-polystyrene P322231 Tg 367 K (94 C); poly(2-methylstyrene) 386 K; poly(diethylsiloxane) 165.5 K; poly(ethylene carbonate) 278 K.
- Decimal structure: 6,932 integers + 801 half-integers, 0 others, 0 values ending in .15 -> not produced by adding 273.15 to Celsius values; **[INFERENCE]** values are (averaged) integer-Kelvin entries from the source.
- Tm_K: 78 values < 273 K (e.g. poly(oct-1-ene) 264, polycyclopentene 232 - plausible low-melting polyolefins), 0 < 150 K. 25 of 1,474 rows with both Tg and Tm have Tm < Tg (e.g. P322188 Tg 382 / Tm 248 K), which is physically inconsistent; median Tg/Tm = 0.751 (plausible).
- 2,222 rows have Tm but no Tg. Among them, amorphous polymers carry Tm values that look like Tg values: poly(vinyl acetate) P030024 Tm 314 K (Tg literature ~305 K), poly(butyl acrylate) P040006 Tm 318 K, poly(acrylic acid) P040001 Tm 373 K. **[INFERENCE]** some PoLyInfo "melting" entries for amorphous polymers are transition temperatures misfiled; treat Tm for acrylics (P04: 24 Tm-without-Tg rows of 33 Tm rows) with caution.

**Elongation_at_break is percent [FACT]**: 1,055/1,059 values > 1; 125 > 100; 5 > 1000 (cis-polybutadiene 1960.5, poly(ethyl acrylate) 1514, poly(butyl acrylate) 3000, poly(2-methoxyethyl acrylate) 1975, poly(pentadecanolactone) 1200); glassy polymers sit at 3-6 (poly(2-methylstyrene) 3.0). GPa is dimensionally wrong for a strain anyway. The CSV column `elongation_at_break` (median 250, max 6190) is the same scale.

**Tensile modulus [FACT]**: median 2.1 GPa, 25-75% 1.585-2.7 GPa (typical glassy polymers), 5% 0.184 GPa - consistent with GPa. Suspicious tail: 6 values > 50 GPa (P190001 polyketone 180.75, P100247 180, P160103 150, P430191 69.25, P372600 chitin 59, P070064 poly(tetramethylene glycol) 55 - the last is a soft polyether and cannot be 55 GPa); 4 values < 0.001 GPa (P040217 poly(N,N-dimethylacrylamide) 9e-6, P040001 2e-5).

**Tensile stress at break [FACT]**: median 0.081 GPa (81 MPa), 25-75% 0.058-0.098 GPa - consistent with GPa. 9 values > 1 GPa, 3 > 10 GPa: P100143 64.02, P100126 35.08, P070232 34.11 (aramids; Kevlar fibre is ~3 GPa, so these are almost certainly MPa mislabelled as GPa or a x1000 error). 14 rows have stress > modulus (impossible for a linear-elastic solid), e.g. P100143 modulus 7.2 vs stress 64.02.

**Density [FACT]**: 1 value < 0.5 (P382422 0.23, a terthiophene polymer - implausible for a solid), 2 > 2.5 (poly(vinylidene bromide) 2.865, poly(1,3,5-triselenane) 2.9 - plausible for Br/Se). 1% = 0.86, 99% = 1.87: g/cm3 confirmed.

**Resistivity / conductivity [FACT]**
- Resistivity log10 quantiles: 1% -1.45, 5% 0.0, 50% 7.02, 95% 15.95, 99% 17.89; 63 rows <= 1 ohm cm (conductive polymers or errors); 0 rows > 1e20.
- Conductivity log10 quantiles: 1% -17.01, 50% -4.96, 95% 0.83, 99% 2.18, max 7.28; 110 rows > 1 S/cm, 7 > 1000 S/cm: P100169 poly(glycine) 2e6, P070557 23,500, P382524 30,000, P044508 poly(sodium acrylate) 1600, P380049 poly(3-methylthiophene) 1000. Copper is ~6e5 S/cm, so 2e6 S/cm for polyglycine is impossible.
- Overlap 1,268 rows: Pearson r(log10 rho, log10 sigma) = -0.858, Spearman -0.850. Exact reciprocal (rel 1e-6): 549 rows; within 1%: 641; |log10(rho*sigma)| < 0.5: 842 (66.4%). Histogram of round(log10(rho*sigma)): 0 -> 842, 1 -> 110, 2 -> 69, 3 -> 53, 4 -> 54, 5 -> 45, 6 -> 26, 7 -> 17, 8 -> 12, 9 -> 13, >=10 -> 27 (max 18 for P130124). All 371 rows off by >= 1 decade have sigma > 1/rho. **[INFERENCE]** ~1/3 of the conductivity/resistivity pairs come from different samples/measurements (PoLyInfo aggregates many samples per polymer; the sheet appears to hold one number per property, chosen independently), so the two columns are not interchangeable.

Repro:
```python
import numpy as np
e=df.Elongation_at_break_GPa.dropna(); print(e.median(), (e>1).sum(), (e>100).sum(), e.max())
x=df.Tg_K.dropna(); print(x.min(), (x<100).sum(), ((x%1==0).sum(), (x%1==0.5).sum()))
from scipy import stats; c=pd.to_numeric(cs.glass_transition_temperature,errors='coerce').dropna(); print(stats.ks_2samp(c,x).statistic, stats.ks_2samp(c,x-273.15).statistic)
b=df.dropna(subset=['Volume_resistivity__ohmXcm','Electric_conduct_1_per_ohmXcm']); lr,lc=np.log10(b.iloc[:,7]),np.log10(b.iloc[:,8]); print(len(b), np.corrcoef(lr,lc)[0,1], ((lr+lc).abs()<0.5).sum())
```

## 5. Outliers / impossible values (pid, name, value)

- Conductivity > 1000 S/cm (7): P100169 poly(glycine) 2.0e6; P382524 3.0e4; P070557 poly[(4,6-diaminoresorcinol)-alt-(terephthalic acid)] 2.35e4; P044508 poly(sodium acrylate) 1600; P380049 poly(3-methylthiophene) 1000; (2 more between 1000 and 1e4).
- Resistivity < 1 ohm cm paired with huge conductivity: P100169 rho 5e-7 / sigma 2e6; P070557 2.45e-5 / 23,500.
- Resistivity-conductivity pairs off by > 10 decades (27 rows), e.g. P130124 rho 1e16 / sigma 45; P380161 rho 1e17 / sigma 1.25e-5; P380048 poly(3-hexylthiophene) rho 9e7 / sigma 175.
- Tensile stress at break > 10 GPa (3): P100143 64.02; P100126 35.08; P070232 34.11. Stress > modulus (14 rows), also P370404 modulus 0.0024 vs stress 0.05.
- Tensile modulus > 50 GPa (6): P190001 180.75; P100247 180; P160103 150; P430191 69.25; P372600 chitin 59; P070064 poly(tetramethylene glycol) 55.
- Tensile modulus < 1 MPa (4): P040217 9e-6 GPa; P040001 2e-5; P374034 6e-4; P374035 8e-4.
- Elongation > 1000 % (5): P040006 3000; P040034 1975; P010071 1960.5; P040003 1514; P090092 1200 (plausible for elastomers/acrylates, flag only).
- Density: P382422 0.23 g/cm3 (implausible); P512008 0.66.
- Tm < Tg (25 rows): P169043 Tg 538 / Tm 516.5; P210027 poly(p-phenylenevinylene) 513 / 487.5; P322188 382 / 248; P322189 381 / 267; P322190 377 / 287.
- Tg > 700 K (10): P080136 768; P130369 763; P430285 739; P432410 733; P433495 729; P070638 710; P134302 709; P370256 703; P432456 703; P370204 701 - all aromatic polyimide/benzazole; high but not impossible.
- Zero-star SMILES (3): P370214, P522049, P522050 - no polymerisation points, cannot be used as repeat units.
- Name/SMILES mismatch pairs: P373700 vs P373706; P370074 vs P372152 (see section 2).
- iupac encoding damage: 1 name contains a non-ASCII replacement character (`poly(2,5-didodecy\ufffd?1,4-phenylene)`); 0 full-width characters; 0 leading/trailing whitespace; 212 names do not start with "poly" (cis-/trans-/1,4- prefixes, "chitin", "polyacenaphthylene", etc.); 1 typo `pol(1,3,5-triselenane)` P520001. iupac duplicates: 13,477 unique names among 13,712 non-null; 206 names appear more than once (235 excess rows; top: `poly{[2,2-dimethyl-4,5-bis(hydoxymethyl)-1,3-dioxolane]-alt-(diethyl carbonate)}` x9, `polyaniline` x4, `poly(gamma-methyl L-glutamate)` x4); 178 names map to more than one CanonSMILES (same name, different structure).

## 6. The 13 rows with missing iupac

All 13 are in class P39 (polyesters, second series) with consecutive-ish pids: P390234, P390236, P390238, P390239, P390240, P390244, P390245, P390248, P390249, P390250, P390251, P390252, P390253. All have a valid 2-star CanonSMILES and all have Tg_K (316, 413, 406, 421, 419, 293, 428, 333, 367, 369, 369, 380, 390 K); P390248 also has density 1.19. Chemistry: P390234-P390253 are aromatic (phenyl-substituted biphenyl/naphthalene) polyesters and carbazole-containing cyano-acrylate polyesters; P390245 is `*CC(C)(CC)COC(=O)c1ccc(C(=O)O*)cc1` (a 2-ethyl-2-methylpropylene terephthalate). **[INFERENCE]** a single contiguous block whose names failed to export; harmless for SMILES-based modelling, but name-based lookups will miss them.

Repro: `df[df.iupac.isna()][['pid','CanonSMILES','Tg_K']]`

## 7. Sheet-name tokens 'IBMSMILES' and 'wPD' (all INFERENCE)

- `IBMSMILES`: The CanonSMILES column is byte-identical to RDKit's `Chem.MolToSmiles(Chem.MolFromSmiles(s))` for 13,579/13,725 rows and structurally identical for all rows, with `[*]` rewritten as `*` and ring-closure digits renumbered. **[INFERENCE]** "IBM" most likely refers to the canonicalisation/curation pipeline used to generate the column (IBM Research has published polymer-SMILES canonicalisation tooling and datasets derived from PoLyInfo); the evidence here only proves that the column is an RDKit-style canonical polymer SMILES with `*` attachment points, not who produced it. Alternative reading ("in-house / internal build of monomer SMILES") cannot be excluded from the file alone.
- `wPD`: **[INFERENCE]** "with Property Data" (the sheet appends 8 property columns to an id/name/SMILES table). Note that 2,338 rows (17%) have no property, so "wPD" describes the schema, not a row filter. An alternative reading, "with PoLyInfo Data", is equally consistent.
- `ver2`: a second revision; no changelog is present in the file (single sheet, no metadata rows).
- `230227` in the file name: **[INFERENCE]** 2023-02-27 export date (YYMMDD), i.e. this predates the CSV (`0824` = 2024-08? or 2023-08-24; unknown).

## 8. Context: is 7,733 Tg values consistent with published PoLyInfo homopolymer counts?

**[CONTEXT, not verified here]** Papers that train on PoLyInfo homopolymer Tg typically report roughly 5,000-8,000 unique homopolymers with Tg (values in the literature vary with the snapshot date and with whether multiple measurements per polymer are averaged). The 7,733 non-null Tg_K values here (914 distinct values, integer/half-integer) sit at the upper end of that band and are consistent with a 2023 PoLyInfo snapshot with one averaged Tg per homopolymer. The 13,725 total homopolymers with SMILES is also in line with the commonly cited ~13-15k homopolymer SMILES in PoLyInfo-derived sets. This is context only; it does not confirm provenance.

## 9. Recommendations for the LLM4POL pipeline

1. Rename `Elongation_at_break_GPa` -> `elongation_at_break_pct`; keep Tg/Tm in K (or subtract 273.15 consistently, and never both).
2. Keep conductivity and resistivity as separate targets; drop or cap conductivity > ~1e4 S/cm and inspect the 371 non-reciprocal pairs; model in log10.
3. Flag tensile stress > 5 GPa, modulus > 50 GPa or < 1e-3 GPa, density < 0.7, Tm < Tg, stress > modulus as suspect (about 60 rows total).
4. Deduplicate on RDKit-canonical SMILES **after** deciding how to handle stereo (41 cis/trans/cyclo groups) - either keep the stereo-bearing `polymer_smiles` (35 rows have marks) or aggregate targets.
5. Do not join to the CSV on ids; the CSV is an entirely separate P90xxxx copolymer namespace. Structure-level join is possible only for CSV rows that are effectively homopolymers.
6. Remove the 3 zero-star SMILES (P370214, P522049, P522050).
7. Be aware that the benchmark homopolymers (PE, PS, PMMA, PVC, PET, PDMS, PTFE, PEO, PLA, PCL) have no property values in this sheet.
