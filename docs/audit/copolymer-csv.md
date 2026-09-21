# Data-quality audit: `polymer_final_0824.csv` (copolymer table)

File: `C:/Users/molsim/Dropbox/Work to do/LLM4POL/polymer_final_0824.csv` (10,015,654 bytes, CRLF, no BOM).
42,557 rows x 29 columns, 7,385 `polymer_id`, `sample_id` unique.
All numbers below were computed in this session (Python 3.13 / pandas / RDKit 2025.09.6).
Helper artefacts in the same folder as this report:
`parse_comp.py` (composition grammar), `df_str.pkl`, `df_parsed.pkl`, `props_num.pkl`,
`rdkit_invalid_smiles.csv`, `cid_to_smiles_resolved.csv`, `tg_vs_comp_monotonicity.csv`.

## 0. Headline findings (read this first)

| # | Finding | Number |
|---|---------|--------|
| A | The file is **UTF-8, not cp949**. cp949 decodes without error but silently corrupts 16 cells in 15 rows (`ｐoly` -> `節릓ly`, eating the letter "o"). Use `encoding='utf-8', encoding_errors='replace'`. | 51 non-ASCII bytes in 18 runs, all valid/truncated UTF-8 |
| B | One record (P908185, physical line 38646) has an **unclosed quote**; it swallows the next two physical lines. P908186 never appears; two rows carry garbage in `smiles1/2`, `copolymer_type` (`'4'`, `'7'`). | 42,561 physical lines vs 42,558 CSV records |
| C | **42.6 % of rows have no composition at all** (18,116 rows; 18,090 of them still carry 2 SMILES). | 18,116 / 42,557 |
| D | One grammar parses 99.92 % / 99.95 % of `composition1` / `composition2`; a numeric value is recovered for 96.7 % / 95.9 %. | see section 1 |
| E | Only 79.6 % of numeric same-basis pairs sum to exactly 100; 2.8 % sum to 1 (fractions), 15.5 % are in (1.02, 99) (ratios / partial compositions), 1.4 % exceed 101 (unit counts such as `m992`/`m8`). | 18,320 / 23,025 exact |
| F | `smiles1/smiles2` order is a **polymer-level constant**, but `component1/component2` (and therefore `composition1/composition2`) is **sample-level and swapped relative to the SMILES in ~30 % of rows**. Composition follows the component id, not the SMILES slot. | 5,224 of 17,697 resolved rows swapped; 16 of 19 slope-sign tests flip |
| G | `polymer_id` -> unordered SMILES pair is a pure function (1 violation = the broken record), but 683 SMILES pairs are shared by >1 `polymer_id` (26,126 rows), dominated by `smiles1 == smiles2` rows (3,952 rows, 713 ids: e.g. PEO-b-PPO-b-PEO stored as `*CCO*`,`*CCO*`). | 683 / 5,322 pairs |
| H | `volume_resistivity` and `electric_conductivity` are **strings with unit suffixes** (`'800000000ohm*cm'`, `'2e-161/(ohm*cm)'` = 2e-16 + "1/(ohm*cm)") and are mutual reciprocals on all 4,015 rows that have both. | 0 numeric before parsing |
| I | Tg has replicate measurements: 2,243 (polymer, composition) groups hold 10,222 of the 18,142 Tg rows; within-group SD median 7.0 C, p90 33 C. **Sample-level replicate modelling is required.** | 56.3 % of Tg rows |
| J | `sample_id` = `source(7)-polymer_in_source(3)-sample(3)-measurement(3)`. | (seg0,seg1) -> exactly 1 polymer_id in 22,440/22,440 groups |

## 1. Composition grammar

### 1.1 Inventory
`composition1`: 24,441 non-null (18,116 null), 85 distinct shapes after replacing numbers by N/F.
`composition2`: 24,251 non-null (18,306 null), 89 distinct shapes. 190 rows have composition1 only; 0 rows have composition2 only.

Top shapes (composition1 / composition2 counts):

| shape | c1 | c2 | example | meaning |
|---|---|---|---|---|
| `mN`, `mF` | 9,643 + 5,836 | 9,497 + 5,856 | `m97`, `m2.5` | mol % |
| `wN`, `wF` | 3,335 + 1,675 | 3,050 + 1,858 | `w80` | wt % |
| `N%`, `F%` | 1,073 + 308 | 878 + 292 | `70%`, `23.50%` | % with unspecified basis |
| `uN`, `uF` | 414 + 82 | 400 + 74 | `u72.4` | % with unspecified basis (see 1.3) |
| `m(N)`, `w(N)`, `m(F)`, `w(F)` | 320 + 221 + 102 + 194 | 267 + 240 + 212 + 149 | `m(80)` | parenthesised value (meaning unresolved, see 1.3) |
| `vN`, `vF` | 90 + 85 | 81 + 74 | `v50` | vol % |
| `%x`, `%N-x`, `wx`, `wN-x`, `mN-x` | 126 + 0 + 102 + 0 + 14 | 1 + 123 + 6 + 63 + 19 | `%x` / `%68-x` | algebraic unknown; `N-x` = remainder after a dropped third component |
| `m-`, `w-`, `%-`, `v-`, `w(-)` | 76 + 73 + 24 + 8 + 15 | 75 + 117 + 95 + 22 + 7 | `w-` | basis known, value missing |
| bare prefix `m`, `w`, `u`, `v` | 14 + 95 + 21 + 18 | 19 + 81 + 21 + 18 | `w` | basis known, value missing |
| `-N%` | 33 | 51 | `39%` / `-61%` | stray separator dash: 39 + 61 = 100 |
| `mN-N`, `%N-N` | 26 + 14 | 26 + 8 | `m16-20` | range |
| `m(N/N)`, `m(F/F)`, `v(F/F/F)` | 26 + 29 + 12 | 8 + 17 + ... | `m(60/40)` | multipart block/sub-component list (paired with composite ids `(CU../CU..)`) |
| `rN` | 24 | 21 | `r10` / `r1` | ratio (feed ratio), not percent |
| `mN-Fx`, `rN-Fx` | 21 | 10 + 7 | `m45-0.45x` | expression |
| blank `' '` | 45 | 0 | | blank |
| `wca.N`, `%>N`, `%<N` | 1 + 2 | 1 + 2 | `wca.75`, `%>99` | approx / bound |
| `IN`, `aN`, `CN`, `NF`, `mm1`, `m94,0`, `m(a)` | 4+1+1+3+1+1 | 4+1+1+3+1+1 | `I25`, `N99.5` | typos / unknown prefixes |
| mojibake | 4 | 0 | `w\ufffdi8\ufffdj` | Shift-JIS full-width parentheses `（）` (0x8169/0x816A) lost upstream = `w(8)` |

### 1.2 Proposed grammar (implemented in `parse_comp.py`)
```
comp   := ws* [prefix] body ws*
prefix := 'm' | 'w' | 'v' | 'u' | 'r' | '%' | ''       -> basis mol | wt | vol | unknown(u) | unknown(r) | unknown | unknown
body   := NUM ['%']                      -> value                     (flag pct_suffix if '%')
        | '-' NUM '%'                    -> value                     (flag stray_dash)
        | '(' inner ')'                  -> inner                     (flag paren)
        | 'ca.' NUM                      -> value                     (flag approx)
        | ('<'|'>') NUM                  -> value                     (flag bound)
        | NUM '-' NUM                    -> midpoint                  (flag range)
        | (NUM|x)('-' [NUM] x)+ | NUM x  -> null                      (flag expression)
        | inner ('/' inner)+             -> sum if all numeric else null (flag multipart)
        | 'x'|'y'|'z'                    -> null                      (flag variable)
        | '' | '-'                       -> null                      (flag missing)
blank  -> basis unknown, value null, flag blank
```
Output: `(basis in {mol, wt, vol, unknown}, value: float|null, flags[])`.

Parse results:

| column | non-null | grammar ok | ok rate | numeric value | numeric rate | basis mol / wt / vol / unknown |
|---|---|---|---|---|---|---|
| composition1 | 24,441 | 24,421 | 99.92 % | 23,629 | 96.68 % | 16,207 / 5,738 / 228 / 2,268 |
| composition2 | 24,251 | 24,240 | 99.95 % | 23,267 | 95.94 % | 16,180 / 5,679 / 228 / 2,164 |

Residual unparseable strings (all of them; counts):
composition1 (20): `%(x/68-x)` 5, `m(0.765x/0.235x)` 2, `I25` 2, `I30` 2, `w\ufffdi6.91` 2 (unbalanced mojibake paren), `%\ufffdi8\ufffdj` 1, `w\ufffdi8\ufffdj` 1 (these two now parse after the mojibake fix), `a70`, `C32`, `N99.5`, `N99.0`, `N98.4`, `m94,0`, `mm1` (1 each).
composition2 (10): `I75` 2, `I70` 2, `a30`, `C68-x`, `N0.5`, `N1.0`, `N1.6`, `m(a)`, `mm2` (1 each).

### 1.3 Prefix semantics and evidence (pairs = both compositions numeric, same prefix)

| prefix | n pairs | sum exactly 100 | interpretation | evidence |
|---|---|---|---|---|
| `m` | 15,857 | 12,373 (78.0 %) | mol % | dominant PoLyInfo notation; 650 pairs sum to 1.0 (mole fraction, e.g. `m0.942`/`m0.058`); 314 pairs sum >101 (`m992`/`m8`, `m420`/`m20`: repeat-unit counts / DP) |
| `w` | 5,255 | 4,346 (82.7 %) | wt % | e.g. P900005 `w20/w80` ... `w80/w20` with Tg 91 -> 23 C |
| `v` | 181 | 150 (82.9 %) | vol % | block copolymers (polystyrene-b-polyisoprene `v50/v50`) |
| `u` | 507 | 454 (89.6 %) | percent with **unspecified/unknown basis** (highest sum-to-100 rate of all prefixes; values 0..100, median 65) | 540 rows, 137 ids, mostly `['unspecified']` type; `u1/u1` also used as 1:1 ratio |
| `r` | 23 | 5 (21.7 %) | **ratio** (feed / molar ratio), not percent | values `r10/r1`, `r2/r1`, `r1/r0.2`, `r100/r100` |
| `%` (prefix) | 10 | 10 (100 %) | percent, unspecified basis, used when the value is algebraic | `%x`, `%68-x`, `%-`, `%>99` |
| `N%` (suffix, no prefix) | 1,085 | 892 (82.2 %) | percent, unspecified basis | same polymers (P900074, P900414) as the `%`-prefix family |
| `x`, `y`, `z` | - | - | unknown variable; `N-x` = "N minus x" i.e. remainder after a **third component that was dropped when the table was truncated to 2 components** | P900074 poly(acrylonitrile-co-butadiene): `32%` / `%68-x`; P905576 triblock: `wx` / `w92.50-x` |
| `-N%` | 116 rows | 39%+61% = 100 | leading dash is a stray separator | 41 (`N%`,`-N%`) pairs, 116 rows total |
| `( )` | 1,751 values | paren-only-one-side pairs: 84.0 % / 82.0 % exact-100 vs 79.0 % for no-paren | **unresolved**; weak evidence for "nominal/feed value" (multiple-of-5 fraction 0.429 vs 0.302 for composition1) | only 61 of 4,062 ids mix paren and non-paren rows |

Different bases inside one polymer_id: 278 of 4,062 ids with compositions use more than one basis across their rows (e.g. P900016 EVA has wt, mol and unknown rows).

## 2. Composition sums

Rows with both compositions non-null: 24,251.
Same basis: 24,245; **different basis: 6 rows (0.02 %)** and all 6 are parser residuals (`m(0.765x/0.235x)`, `w\ufffdi6.91`, `m(a)`, `m94,0`), i.e. there is no real mixed-basis row.

Same basis and both numeric: 23,025 rows.

| sum class | rows | share |
|---|---|---|
| exactly 100 | 18,320 | 79.6 % |
| 99 <= sum <= 101 | 18,436 | 80.1 % |
| 95 <= sum <= 105 | 18,887 | 82.0 % |
| 0.98 <= sum <= 1.02 (fractions) | 650 | 2.8 % |
| 1.02 < sum < 99 (ratios, partial compositions, third component missing) | 3,562 | 15.5 % |
| sum > 101 (unit counts, DP) | 314 | 1.4 % |
| sum < 0.98 | 63 | 0.3 % |

By basis: mol 78.6 % within 99-101 (n 15,857), wt 83.2 % (5,255), vol 83.4 % (181), unknown 84.0 % (1,732).
Sum quantiles (all): p1 = 1.0, p5 = 2.4, median 100, p99 = 110.8, max 34,593 (`w` values that are clearly not percents).

## 3. Component id vs SMILES alignment

Component ids: 3,079 unique (prefix classes: `CU` 47,910 slot-occurrences, `L` 394, `JU` 210, `B` 46; composite `(CU.../CU...)` ids in 2,065 rows, of which 189 have multipart compositions like `m(60/40)`).

* 693 of 3,079 ids map to >1 SMILES (max 104 SMILES for `CU020001`; distribution 1: 2,386, 2: 408, 3: 115, 4: 58, >=5: 112).
* 635 of 2,719 SMILES map to >1 id (max 149).

Stability inside a polymer_id (rows with both ids and both SMILES, 24,163 rows, 4,008 ids):

| test | ids violating |
|---|---|
| unordered SMILES pair varies | 1 (P908185, broken record) |
| **ordered** SMILES pair varies | 1 |
| unordered component-id pair varies | 139 |
| **ordered** component-id pair varies | 277 |
| ordered id pair varies while ordered SMILES pair is constant | 276 |
| (c1,c2,s1,s2) tuples that have an id-swapped twin with identical SMILES order | 504 tuples in 301 ids |
| tuples with SMILES-swapped twin and identical id order | 231 tuples in 215 ids |

Root cause: `smiles1/smiles2` were attached **per polymer** (constant), while `component1/component2/composition1/composition2` come from the **per-sample** record whose component order varies. Consequently the same id lands in slot 1 next to a "foreign" SMILES.

Which column does the composition follow? Two independent tests:
1. Concrete example P900005 poly[acrylonitrile-co-(ethyl acrylate)]: rows have `component1 = CU040003` (ethyl acrylate, by global resolution) next to `smiles1 = *C(C#N)C*` (acrylonitrile). `composition1` = w20, w40, w60, w80 gives Tg = 91, 74, 48, 23 C. Tg falls as composition1 rises, so composition1 is the ethyl-acrylate fraction = **component1, not smiles1**.
2. For the 19 polymer_ids that contain both id orders with >=3 compositions each, the Spearman sign of Tg vs composition1 flips between the two orders in **16 of 19** ids (same sign in 3). If composition followed the SMILES slot the sign would never flip.

Quantification with a majority-vote constraint propagation (`cid_to_smiles_resolved.csv`; rows with 2 distinct plain ids and 2 distinct SMILES = 20,929): 1,964 of 2,635 ids resolved; rows aligned 12,473, **swapped 5,224 (29.5 % of resolved-consistent rows)**, unresolved 2,200, inconsistent 1,032. Naive "mode SMILES per id" gives: same slot 18,754, other slot only 3,697, in neither slot 1,902 (7.8 %; these are SMILES representation variants, e.g. butadiene as `*CCC=C*`, `*CC/C=C/*`, `*C(C=C)C*`, plus >=3-component polymers truncated to 2 SMILES: 31.7 % of these rows have >=3 components in the name vs 21.7 % for aligned rows).

Decision: **SMILES pair = reliable polymer identity; component id = reliable composition slot owner; the SMILES slot order must not be trusted for composition.** Reconstruct `(smiles_for_composition1, smiles_for_composition2)` via id -> SMILES mapping (16,760 of 24,163 rows are directly realignable because both ids' resolved SMILES appear in the row; 2,221 need a swap).

## 4. polymer_id vs unordered SMILES pair

* polymer_id -> >1 unordered SMILES pair: **1 of 7,385** (P908185, CSV artefact). polymer_id -> polymer_name is also 1:1 except the same id.
* unordered SMILES pair -> >1 polymer_id: **683 of 5,322 pairs**, affecting **26,126 rows (61.4 %)**; multiplicity 2: 402, 3: 122, 4: 58, 5: 25, 6-8: 34, max 79 ids for (`*CCCCCC(=O)O*`,`*CCCCCC(=O)O*`).
* Driver: `smiles1 == smiles2` in 3,952 rows / 713 ids (PEO-b-PPO-b-PEO -> `*CCO*`,`*CCO*`; PS-b-PI-b-PS -> styrene twice; D/L-lactide). Of the 683 shared pairs, 661 have >1 polymer_name and 527 >1 copolymer_type.
* RDKit canonicalisation does not change this: 4,782 valid SMILES -> 4,782 canonical (0 duplicate representations), so 683 shared canonical pairs, same 26,126 rows.
* 83 polymer_names map to 2 ids and 7 to 3 ids (synonym ids).

## 5. copolymer_type

`ast.literal_eval` succeeds on all 42,557 values: 42,555 lists + 2 ints (`4`, `7`, from the broken P908185 rows).
List length: 1: 30,778; 2: 10,979; 3: 794; 4: 6. **Rows with >=2 tags: 11,779 (27.7 %)**. 29 distinct tag sets; no duplicated tag inside a list.

Exploded tag frequency: unspecified 28,938; alternating copolymer 9,346; random copolymer 6,821; block copolymer 6,814; graft copolymer 2,740; statistical copolymer 471; periodic copolymer 10.
Top sets: {unspecified} 20,843; {random} 5,262; {alternating, unspecified} 5,160; {block} 2,822; {alternating, block} 1,910; {graft} 1,305; {alternating, random} 1,258; {graft, unspecified} 1,129; {block, unspecified} 1,089; {alternating, block, unspecified} 585.

Tag set varies within a polymer_id in **1 of 7,385** ids (P908185) -> it is a polymer-level attribute, not a per-source annotation.
Interpretation: the list is the union of architecture labels of every level of the name hierarchy, plus `unspecified` as filler. 4,892 of the 11,779 multi-tag rows carry `-alt-` in the name; {alternating, block} rows are segmented polyurethanes/polyesters written `poly{[diol]-alt-[diisocyanate]}-block-...`; {alternating, unspecified} is the typical condensation copolymer (`-alt-` inside, no architecture stated). 8,095 rows combine `unspecified` with another tag. For modelling, `unspecified` should be dropped from multi-tag lists and the remaining tag(s) treated as multi-label.

## 6. Properties

Units: Tg/Tm in C (homopolymer xlsx Tg_K median 410 K vs 52.6 here); density g/cm3; tensile modulus and stress in GPa (xlsx medians 2.1 / 0.081 GPa vs 0.255 / 0.0185 here, this table has many elastomers); elongation in %; resistivity ohm*cm; conductivity S/cm. Resistivity/conductivity must be log10-transformed (span 30 decades).

| property | n | min | p1 | median | p99 | max | zero | neg | impossible / suspicious |
|---|---|---|---|---|---|---|---|---|---|
| density | 3,104 | 0.024 | 0.581 | 1.096 | 2.20 | 6.194 | 0 | 0 | >5: 9 (P900027 PTFE-co-VDF 5.24); <0.5: 29 (P900016 EVA 0.024-0.127, foam or mis-entry) |
| glass_transition_temperature | 18,142 | -151.3 | -110 | 52.55 | 338 | 455 | 55 | 5,687 | none outside (-200, 500); Tg > Tm on 78 of 3,728 rows with both |
| melting_temperature | 8,713 | -68 | -7.88 | 128 | 375 | 533 | 2 | 120 | none outside (-100, 600) |
| tensile_modulus (GPa) | 3,709 | 8e-8 | 7e-5 | 0.255 | 62.8 | 916 | 0 | 0 | >100 GPa: 25 (e.g. 606, 767 for poly[ethylene-co-hexene]: MPa entered as GPa); <0.01: 929 (gels/elastomers) |
| tensile_stress_strength_at_break (GPa) | 5,046 | 0 | 1.7e-4 | 0.0185 | 11.06 | 580 | 8 | 0 | >500: 2 (PDMS-b-PC 570, 580: MPa) |
| elongation_at_break (%) | 5,072 | 0 | 1.1 | 250 | 1,800 | 6,190 | 15 | 0 | >2000 %: 32 |
| volume_resistivity (ohm*cm, parsed) | 4,015 (+11 `ohm*m`, +4 `[NR]` unparsed) | 9.6e-12 | 0.029 | 1.2e4 | 2.0e16 | 1e19 | 0 | 0 | log10 range -11 .. 19; log10 median 4.08 |
| electric_conductivity (S/cm, parsed) | 4,045 (+10 `mS/cm`, +2 `ohm/m`, +1 unit-only unparsed) | 0 | 2.7e-17 | 8e-5 | 32.6 | 1.0e11 | 6 | 0 | log10 median -4.09; >1e6 physically impossible for polymers |
| refractive_index | 684 | 1.295 | 1.344 | 1.53 | 2.266 | 2.467 | 0 | 0 | none |

Resistivity and conductivity are present together on 4,015 rows and log10(res*cond) has median 0.00 (IQR 0.00) -> one is derived from the other; **keep only one**. Raw strings: `'5000000000000000.0ohm*cm'`, `'2e-161/(ohm*cm)'` (= 2e-16 followed by the unit `1/(ohm*cm)`).

Properties per row (9 properties, after parsing the two string columns): 0: 11,151 (26.2 %); 1: 17,839; 2: 8,782; 3: 2,829; 4: 1,293; 5: 529; 6: 115; 7: 19. **Rows with >=2 properties: 13,567 (31.9 %)**.

Joint coverage (row counts with both non-null):

| | dens | Tg | Tm | E | sigma_b | eps_b | rho_v | sigma_e | n_D |
|---|---|---|---|---|---|---|---|---|---|
| density | 3,104 | 1,119 | 792 | 238 | 373 | 376 | 102 | 104 | 55 |
| Tg | 1,119 | 18,142 | 3,728 | 1,273 | 1,609 | 1,569 | 812 | 816 | 184 |
| Tm | 792 | 3,728 | 8,713 | 739 | 836 | 839 | 198 | 199 | 37 |
| tensile_modulus | 238 | 1,273 | 739 | 3,709 | 2,823 | 2,891 | 251 | 252 | 7 |
| tensile_stress | 373 | 1,609 | 836 | 2,823 | 5,046 | 4,446 | 439 | 442 | 15 |
| elongation | 376 | 1,569 | 839 | 2,891 | 4,446 | 5,072 | 414 | 417 | 9 |
| vol_resistivity | 102 | 812 | 198 | 251 | 439 | 414 | 4,015 | 4,015 | 11 |
| conductivity | 104 | 816 | 199 | 252 | 442 | 417 | 4,015 | 4,045 | 11 |
| refractive_index | 55 | 184 | 37 | 7 | 15 | 9 | 11 | 11 | 684 |

## 7. Measurement multiplicity (Tg)

Grouping the 18,142 Tg rows by (polymer_id, basis, parsed composition1, parsed composition2) gives 10,163 groups.
* Groups with >1 Tg row: **2,243**, holding **10,222 rows (56.3 % of all Tg rows)**; 2,018 of them have >1 distinct value.
* Within-group SD: p25 2.1, **median 7.0**, p75 15.7, p90 33.1, p95 52.4, p99 120 C; mean 13.8. Range >20 C in 872 groups, >50 C in 355.
* Groups with a known composition (1,053): median SD 4.75, p90 29.8. Groups with no composition (1,190): median SD 8.6, p90 34.6.
* Even within one physical sample (sample_id segments 1-3 equal): 650 samples have >1 Tg row, 606 with distinct values, median SD 4.95 C.
* Total Tg variance 9,197 vs mean within-group variance 682 (7.4 %).
Worst groups are no-composition ids with Tg values like -132 and 298 C in the same group (P903245): two different block Tgs stored as separate rows.
Conclusion: the table is sample/measurement-level, replicates are the norm; models must either aggregate (median per group) or use replicate-aware losses, and block copolymers can legitimately have two Tg rows.

## 8. sample_id structure `SSSSSSS-PPP-CCC-MMM`

| segment | width | unique | evidence |
|---|---|---|---|
| seg0 | 7 | 6,909 | maps to 1..162 polymer_ids (1: 4,534, 2: 1,285, 3: 525 ...); corr(seg0, polymer number) = 0.066 -> **source / document id** (e.g. 0020270 covers P900005, P900463, P900464, P900468, P900469 = one paper series) |
| seg1 | 3 | 88 (001-101) | (seg0, seg1) -> exactly 1 polymer_id in all 22,440 groups -> **polymer index within the source** |
| seg2 | 3 | 59 | (seg0,seg1,seg2) -> 34,960 groups; composition never differs inside a group (0 of 5,452 multi-row groups) while Tg differs in 3,221 -> **sample / specimen index** |
| seg3 | 3 | 17 | 001: 34,943, 002: 5,458, 003: 1,143 ... 017 -> **measurement / record index** within the sample |

## 9. Rows with 1 or 0 SMILES; SMILES with `*` count != 2

* 115 one-SMILES rows (37 ids): smiles2 missing in 96, smiles1 in 19. Almost all are monomers with unspecified substitution position written `x-` in the name (e.g. P904828 `poly{1-[(x-chloromethyl)phenyl]ethylene/...}`, P906362 `x-(dioxaborolanyl)phenyl`), plus a few ferrocenyl phosphazenes; component ids are present so the monomer is known, only its SMILES is absent.
* 4 zero-SMILES rows: P904415 (1 row, poly[(N,N-diphenylamine)-co-(N-methylaniline)]) and P908136 (3 rows, fluorinated bis-benzoxazole); no ids, no composition.
* `*` count over 4,792 unique SMILES: 2 -> 4,646; 3 -> 80 (459 rows); 4 -> 53 (203 rows); 6 -> 6; 8 -> 2 (3 rows); 16 -> 1; 0 -> 4.
  * 0 stars: the 4 strings are **text fragments from the broken P908185 record** (`"['unspecified']"`, `"7-trimethylbicyclo[2.2.1]heptan-2-yl)...]"`), not SMILES.
  * 3 / 4 stars: branching / cross-linking units: trifunctional acids (`*Oc1cc(cc(c1)C(=O)*)C(=O)*`), dendritic bis-MPA units (`*OCC(NC(=O)CCCC(=O)*)(CO*)CO*`), dimethacrylate cross-linkers (`*CC(C(=O)OCCOC(=O)C(C*)(C)*)*`), tetrafunctional thiophenes.
  * 6 / 8 stars: multi-arm / network cores (triazine-tris(thiophene/pyrrole), benzoxazine, carbazole-tetrathiophene).
  * 16 stars: a POSS cage with 8 methacrylate arms (`*CC(C(=O)OCCCC[Si]12O[Si]3...`).
  Recommended tags: 2 = linear; 3-4 = branched/crosslinker (133 SMILES); >4 = multi-arm/network (9); 0 = malformed (4).

## 10. RDKit validity

`Chem.MolFromSmiles` fails on **10 of 4,792** unique SMILES (46 rows); replacing `*` with `[*]` does not help. Six are carborane clusters written with many `[B]` ring closures (P904273 15 rows, P904274 9, P901377 8, P904536 2, P907666 4, P907667 4) - they parse with `sanitize=False`; four are the P908185 text fragments. 257 SMILES carry formal charges, 74 have `/` or `\` double-bond stereo, 0 have `@`, 1 contains `.`. Canonicalisation collapses nothing (4,782 -> 4,782).

## 11. Tg vs composition trend (basis validation)

Global: among the 379 polymer_ids with >=5 distinct compositions (same basis, sum in 99-101, distinct SMILES) the median |Spearman rho(Tg, composition1)| is **0.868**; 234 (61.7 %) have |rho| > 0.7 and 67 have |rho| < 0.3. The three ids with the most Tg rows spanning composition are physically "flat" or non-monotonic systems, which is itself informative:

P900016 poly[ethene-co-(vinyl acetate)], wt basis, n = 74, rho = 0.20 (p 0.08). composition1 = ethylene wt% per the component id (`CU010001`). EVA Tg is known to be non-monotonic because crystallinity changes with VA content; the wide scatter at w72 (23 rows, -25 .. 46 C) also shows multiple Tg definitions.

| ethylene wt% | n | median Tg | min | max |
|---|---|---|---|---|
| 10 | 1 | 19 | 19 | 19 |
| 20 | 3 | -13 | -13 | 3 |
| 30 | 5 | -15 | -22 | -14.5 |
| 50 | 3 | -27.5 | -31 | -26 |
| 60 | 4 | -17.5 | -38 | -14 |
| 72 | 23 | -14.8 | -25 | 46 |
| 80 | 5 | -17.5 | -28 | -16 |
| 88 | 2 | 8.5 | 7 | 10 |
| 91 | 1 | 25 | 25 | 25 |

P900007 poly(acrylonitrile-co-styrene), wt basis, n = 57, rho = -0.06: Tg 100-116 C across 5.5-98 wt% - correct, because PS (100 C) and PAN (105 C) have almost equal Tg; SAN is a null test for basis.

P900492 poly[styrene-co-(4-sulfostyrene)], mol basis, n = 55, rho = 0.12; the id order changes inside this polymer (`CU020001/CU320022` vs `CU070064/CU110087`), so the composition slot is mixed - an instance of finding F.

Clean monotonic example (P900005 poly[acrylonitrile-co-(ethyl acrylate)], source 0020270): composition1 = w20, w40, w60, w80 -> Tg 91, 74, 48, 23 C, consistent with composition1 being the ethyl-acrylate (component1) wt%. The sign-flip test (16/19) in section 3 is the strongest basis/slot validation.

## 12. Encoding and text hygiene

* Bytes: 10,015,654; no BOM; CRLF line ends; 42,561 physical lines but 42,558 CSV records (header + 42,557) because record P908185 (line 38646, 1 quote character, 20 commas) has an unclosed `"` and absorbs lines 38647-38648 (`0052076-001-002-001` and `0052078-005-001-001`/P908186). P908186 is entirely absent from the parsed table; two P908185 rows carry an embedded CRLF in `polymer_name` and garbage in `smiles1`, `smiles2`, `copolymer_type`.
* Non-ASCII bytes: 51, in 18 runs, all UTF-8: 9x `EF BD 90` (`ｐ` U+FF50, the 9 rows of P900100 `ｐoly[(vinylidene fluoride)-co-(1,1,1,3,3,3-hexafluoroacetone)]`), 6x `EF BF BD` (U+FFFD already embedded, in composition1 of P900212 and P904134: `w\ufffdi8\ufffdj` = Shift-JIS `w（8）`), 3x truncated `EF BD` + `?` (P908185).
* `pd.read_csv(..., encoding='utf-8')` fails (invalid continuation byte); `encoding='cp949'` succeeds but produces 16 differing cells in 15 rows compared with `encoding='utf-8', encoding_errors='replace'` (which yields 9 U+FFFD). **The file is UTF-8 with 3 damaged bytes, not cp949**; the cp949 reading mangles `ｐoly` into `節릓ly` and swallows the "o".
* Non-ASCII per column (utf-8 reading): polymer_name 11 rows (3 unique values), composition1 4 rows, smiles1 1 row (P908185), all other columns 0. No full-width characters remain after the P900100 `ｐ`.
* Whitespace: polymer_name 17 rows with leading/trailing whitespace, 2 with control characters (CRLF); composition1 47 rows (45 are the bare `' '` blank); composition2 2; smiles2 1 with a space; component1 3 with spaces. 18,762 polymer_names contain commas (properly quoted except P908185). `Unnamed: 4` is empty in all rows.

## 13. Recommendations for the data-loading layer

1. Read with `encoding='utf-8', encoding_errors='replace'`; drop or hand-repair the two P908185 rows; note P908186 is lost.
2. Parse compositions with `parse_comp.py`; keep `basis`, `value`, `flags`; treat `sum` classes: ~100 (percent), ~1 (fraction x100), else ratio/unit-count (normalise to 100 only when both values are present and `flags` are empty).
3. Re-derive the SMILES for each composition slot through the component id (`cid_to_smiles_resolved.csv` or the resolved map recomputed with all rows); never pair `composition1` with `smiles1` directly.
4. Strip units from resistivity/conductivity, log10-transform, keep one of the two.
5. Aggregate replicates by (polymer_id, basis, comp1, comp2) or use replicate-aware training; keep `sample_id` segments as source/sample/measurement keys for grouped CV (group by seg0 = source to avoid paper leakage).
6. Drop `unspecified` from multi-tag `copolymer_type` lists; treat the remainder as multi-label.
7. Flag rows with `smiles1 == smiles2` (3,952) and `*`-count != 2 SMILES (676 SMILES-slot occurrences) for architecture-aware handling.
