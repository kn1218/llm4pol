# LLM4POL audit: cross-file linkage and unified schema PROPOSAL

Auditor: cross-linkage lane. Date: 2026-09-11.
Inputs (read-only): `polymer_final_0824.csv` (42,557 x 29, cp949) and `230227_Homopolymer_CanonicalSMILES.xlsx` (13,725 x 12). `copolymer.zip` is corrupt and was not touched.
Scripts and intermediate tables live next to this file (`s1_canon.py` ... `s11_binding2.py`, `pcanon.py`, `monomer_link_table.csv`, `row_component_alignment.csv`). Every number below was printed by one of those scripts.

---

## 0. Headline findings

| # | Finding | Number |
|---|---------|--------|
| 1 | The two files share **no identifier namespace**. Linkage is only possible through structure. | 0 of 42,557 CSV `polymer_id` and 0 of 45,636 component ids occur in XLSX `pid` |
| 2 | Naive string join of monomer SMILES against the XLSX is nearly useless. | 118 / 4,792 unique CSV SMILES (2.5%) |
| 3 | RDKit linear canonicalization (same procedure on both files) lifts it to | 1,725 / 4,792 (36.0%) |
| 4 | A cut-point-invariant "periodic" key (delete both `*`, bond their neighbours, canonicalize) lifts it further to | 2,060 / 4,792 (43.0%) |
| 5 | Copolymer ROWS where both components match a homopolymer: naive / linear / periodic | 5.5% / 67.1% / 77.8% of 42,438 two-SMILES rows |
| 6 | CSV Tg is in degC, XLSX Tg in K: for 254 near-homopolymer rows, median abs diff with the 273.15 offset is 15.4 degC; without it 264.0 | N=254 |
| 7 | **composition_i is bound to component_i, not to smiles_i.** In 2,221 rows the component/composition columns are swapped relative to smiles1/smiles2 (plus 881 half-swapped). Tg linear-mixing confirms: in swapped rows the component binding has median error 13.7 degC vs 56.8 degC for the smiles binding. | 45 vs 4 rows |
| 8 | `electric_conductivity` strings have the unit glued to the number (`'2e-161/(ohm*cm)'` = 2e-16 in 1/(ohm*cm)); a naive float parse gives 1e-161-scale garbage. | 4,060 strings, 0 parse as float |

---

## 1. Canonicalization procedure and failures

Procedure (identical for both files): `Chem.MolToSmiles(Chem.MolFromSmiles(s.strip()))`, RDKit 2025.09.6, `*` atoms kept.

| Set | unique inputs | canon failures | notes |
|-----|---------------|----------------|-------|
| CSV `smiles1` U `smiles2` | 4,792 | 10 | at least 5 are carborane `[B]...` cluster SMILES RDKit cannot sanitize; 4 are non-SMILES strings (`"['block copolymer']"`, `"['unspecified']"`, truncated IUPAC text) coming from **column-shifted rows** of polymer P908185 whose `polymer_name` contains an embedded CRLF. The 10 failing strings touch 30 rows / 9 polymer_ids. |
| XLSX `polymer_smiles` | 13,661 | 0 | |
| XLSX `CanonSMILES` | 13,624 | 0 | |

XLSX internal consistency: `canon(polymer_smiles) == canon(CanonSMILES)` for **13,725 / 13,725** rows, but the raw strings are equal for only **7,023** rows. So the XLSX `CanonSMILES` column was produced by a different canonicalizer/version and must **not** be used for string joins; recanonicalize it.

XLSX duplication: 13,725 `pid` -> 13,624 unique linear-canonical SMILES (101 pids are structural duplicates) -> 13,602 unique periodic keys (123 pids collapse). 108 periodic keys are shared by >1 pid; 22 of those unify genuine cut-point variants of the same repeat unit, e.g. `*CCCCCC=CCCC*` (P050029) vs `*CCCCCCCCC=C*` (P010077, P360004).

`*` counts in XLSX `CanonSMILES`: 2 -> 13,637; 3 -> 63; 4 -> 21; 8 -> 1; 0 -> 3.

### 1.1 Periodic key definition (`pcanon.py`)
1. parse; if #`*` != 2 or a `*` has degree != 1 -> use linear canon, tag status.
2. n1, n2 = neighbours of the two `*`; if n1 == n2 (e.g. `*C*`) or already bonded (vinyl-type `*CC(*)R`) -> use linear canon (these have a unique cut anyway).
3. else add bond n1-n2 with the star bond type, delete both `*`, sanitize, canonical SMILES.

Status counts: CSV {ok 3,336, neighbors_already_bonded 1,259, nstar!=2 142, same_neighbor 45, parse_fail 10}; XLSX {ok 11,395, neighbors_already_bonded 2,114, same_neighbor 67, nstar!=2 85}.

**Known loss:** the ring closure discards E/Z on the closed ring. In the CSV, 13 periodic keys merge >1 linear canon; 11 of those are stereo-only merges (cis-/trans-polybutadiene `*CC/C=C\*` vs `*CC/C=C/*` both -> `C1=CCC1`), 2 are true cut-point variants. Only 74 / 4,792 CSV and 35 / 13,725 XLSX SMILES carry stereo marks. Recommendation: primary key = periodic key, secondary field = stereo-aware linear canon; match on periodic key, then prefer same-stereo candidates.

---

## 2. Match statistics (task items 1 and 2)

Unique CSV monomer SMILES (4,792) matching an XLSX homopolymer repeat unit:

| method | matched | fraction |
|--------|---------|----------|
| naive string (vs `polymer_smiles` or `CanonSMILES`) | 118 | 0.0246 |
| RDKit linear canonical | 1,725 | 0.3600 |
| periodic key | 2,060 | 0.4299 |

Copolymer rows (42,438 rows with two SMILES):

| method | both match | exactly one | none |
|--------|-----------|-------------|------|
| naive | 2,331 (5.49%) | 12,968 (30.56%) | 27,139 (63.95%) |
| linear canon | 28,480 (67.11%) | 8,598 (20.26%) | 5,360 (12.63%) |
| periodic | 32,994 (77.75%) | 7,717 (18.18%) | 1,727 (4.07%) |

Per unique polymer_id (7,346 with two SMILES), periodic: both 4,481; one 2,163; none 702.

Most frequent monomers still unmatched after periodic key (rows, polymer_ids, SMILES):
```
 140 rows,  7 pids : *CCC1OC1(*)C                                (2-methyl-THF-type ring; cut variant *C1CCC(*)(C)O1 exists in CSV too)
 138 rows,  1 pid  : FC(C(OC(C(F)(F)*)(F)*)(F)F)(C(F)(F)F)OC(C(S(=O)(=O)O)(F)F)(F)F   (Nafion-type)
  89 rows, 12 pids : *OC(F)(F)*
  84 rows, 16 pids : *CCCCOC(=O)NC1CCC(CC1)CC1CCC(CC1)NC(=O)O*    (H12MDI polyurethane)
  67 rows,  5 pids : *Oc1cccc(c1C#N)Oc1ccc(cc1)*
  64 rows, 10 pids : *C(C(=O)O[Na])(C*)C                          (sodium methacrylate)
  57 rows,  4 pids : *Oc1ccc(cc1)c1ccc(cc1)OC(=O)c1ccc(cc1)OCCOCCOCCOc1ccc(cc1)C(=O)*
  57 rows,  5 pids : *Oc1ccc(cc1S(=O)(=O)O)S(=O)(=O)c1ccc(c(c1)S(=O)(=O)O)Oc1ccc(cc1)c1ccc(cc1)*
  56 rows,  1 pid  : *Sc1cccc(c1)*
  54 rows,  5 pids : CCCC(CC(=O)*)O*                              (PHB-type polyester)
```
Before the periodic key the top unmatched were PET (`*CCOC(=O)c1ccc(cc1)C(=O)O*`, 1,070 rows) and polybutadiene (`*CC/C=C\*`, 773 rows) -- both pure cut-point artefacts, which is why the periodic key matters.

Remaining 2,732 unmatched unique SMILES are genuinely absent from the homopolymer sheet (salts, ionomers, PU hard segments, macromonomers) or fail RDKit.

---

## 3. Unit reconciliation (task item 3)

Selection: CSV rows where one component has a parseable composition >= 95 (any basis) and that component's periodic key exists in the XLSX; XLSX value = median over pids sharing the key. 3,117 such rows (653 polymer_ids); of these the ones with both values present:

| property | N rows (pids) | median abs diff **with** offset | median abs diff **without** offset | within 5 / within 20 |
|----------|---------------|----------------------------------|-------------------------------------|----------------------|
| Tg: CSV degC vs `Tg_K` - 273.15 | 254 (104) | **15.35 degC** | 264.0 | 10.2% / 56.7% |
| Tm: CSV degC vs `melting_temp_K` - 273.15 | 78 (33) | **42.0 degC** | 283.0 | 9.0% / 25.6% |
| density: CSV vs `density_g_per_cm3` (no offset) | 24 (12) | **0.087 g/cm3** (m-basis rows: 0.01) | same | - |

Conclusion: CSV Tg/Tm are degC, XLSX are K (offset test is unambiguous: 15 vs 264). CSV `density` and XLSX density share g/cm3. The residual 15 degC for Tg is the expected spread of a 5% comonomer plus literature scatter, not a unit problem. Tm's 42 degC residual is larger because Tm of copolymers with 5% comonomer drops sharply and because w-basis rows dominate (N=39, median 47.4).

Examples (sample_id, polymer_id, dominant fraction, CSV, XLSX pid/value, diff):
- Tg `0022284-002-001-001` P903463 m95 : CSV 56.0 vs P372652 329.0 K -> diff +0.15
- Tg `0030056-002-002-001` P900449 m95.3 poly[styrene-co-(4-vinylpyridine)]: CSV 109.4 vs P020001 367 K -> +15.55
- Tg `0040912-001-011-001` P906076 m97.17: CSV 206.2 vs P020045 300 K -> +179 (outlier; likely mis-assigned dominant component or bad match)
- Tm `0029758-006-001-001` P904483 m98.3: 33.0 vs P373107 307 K -> -0.85
- Tm `0050453-001-006-001` P901078 m100 poly[(4-aminobutanoic acid)-co-(6-aminohexanoic acid)]: 216 vs P100187 532 K -> -42.85
- Tm `0044639-002-001-001` P906563 w100: 253.7 vs P040006 318 K -> +208.9 (graft copolymer; "w100" is meaningless there)
- density `0001308-005-001-001` P900007 w98 poly(acrylonitrile-co-styrene): 1.0487 vs P020001 1.045 -> +0.004
- density `0013498-002-001-001` P900007 w95: 1.151 vs 1.045 -> +0.106
- density `0014954-013-001-001` P905139 m99 polybutadiene: 0.889 vs P010070 1.455 -> -0.566 (XLSX median across cut-variant pids is suspect here)

Other unit hints (small N, not conclusive): `tensile_modulus` CSV vs `Tensile_modulus_GPa`, N=12, median ratio CSV/XLSX = 0.87 -> CSV tensile modulus is plausibly GPa as well. CSV Tg range -151.3..455 (p50 52.6); XLSX Tg_K 138..768 (p50 410).

---

## 4. The 115 single-SMILES CSV rows (task item 4)

- 115 rows, 37 polymer_ids; the single SMILES sits in `smiles1` for 96 rows and in `smiles2` for 19.
- **They are not homopolymers.** 90 of 115 carry two component ids, and `copolymer_type` is `['unspecified']` (55) / `['random copolymer']` (44) / ...; names are two-component (e.g. `poly{1-[(x-chloromethyl)phenyl]ethylene/1-(isopropylcarbamoyl)ethylene}` with only the isopropylacrylamide SMILES present). The missing SMILES is a missing-value problem (typically an `x-` positional-isomer monomer PoLyInfo cannot encode), not a homopolymer signal.
- Match of the surviving SMILES to XLSX: naive 18, linear canon 100, periodic **106 / 115** (15 of 19 unique SMILES).
- Property agreement with the matched homopolymer (only meaningful where the present monomer dominates): Tg N=28, median abs diff 7.05 degC (9 within 5, max 92); density N=13, median 0.018 g/cm3; Tm N=1 (diff 120, ferrocene copolymer - not comparable).
- Unmatched examples: `*P(=N*)(CCCC)C` (polyphosphazene), imide-type `CCN1C(=O)C(C(C1=O)*)*`.
- The 4 zero-SMILES rows are P904415 (1 row) and P908136 (3 rows); both have no component ids either.

---

## 5. Column semantics discovered en route (needed for the schema)

1. **`polymer_id` is a sound Polymer key.** `smiles1`, `smiles2`, `polymer_name`, `copolymer_type` are constant within `polymer_id` for 7,384 / 7,385 ids; the single exception is P908185 (embedded CRLF corruption).
2. **`component1/2` and `composition1/2` are per-row and can be in the opposite order from `smiles1/2`.** Row classes (majority component-id -> SMILES map): aligned 15,409; swapped 2,221; half_aligned 5,309; half_swapped 881; neither 433; one_component_id 190; no_component_ids 18,114. 136 polymer_ids contain both aligned and swapped rows. Composition is present only when component ids are present (0 of 18,114 no-id rows have a composition).
   Tg linear-mixing test (rows with Tg, both homopolymer Tgs known, |dTg| >= 30 degC): aligned rows N=343: comp<->smiles_i median err 14.1 vs reversed 27.5 (201 vs 97 rows better); swapped rows N=50: comp<->smiles_i 56.8 vs reversed **13.7** (4 vs 45). => **composition_i belongs to component_i**; the monomer for a composition must be resolved through the component id (or through swap detection), never by column position alone.
3. `component` ids map to >1 SMILES in 693 / 3,079 cases; 3,697 of 5,600 disagreements are explained by the swap above; the remainder (433 'neither' rows, e.g. P900350 `poly[ethylene-co-(but-1-ene)]` with ids CU010002/CU010004) are ids whose majority mapping is dominated by another polymer -- i.e. component ids are **not globally unique monomer ids** and cannot be trusted as a Monomer key.
4. Composition basis: both parsed values always share a basis (pairs m/m 14,998; w/w 4,530; none/none 1,188; u/u 460; v/v 155; r/r 23; no mixed pair). Of 21,354 same-basis pairs, 17,063 (79.9%) sum to 100 +/- 1; 4,023 sum < 99 (1,408 of them have >= 3 components in the name, i.e. a third component with no columns); 268 sum > 101. With a relaxed regex `^[mwvur]?x?\s*-?\s*\d+(\.\d+)?\s*%?$`, 1,823 of 24,441 `composition1` values remain unparseable (`%x` 126, `wx` 102, `w` 95, `m-` 76, `w-` 73, `m(80)` 59, `mx` 50, ...). 2,080 rows have exactly one parseable composition.
5. `volume_resistivity` (4,031 non-null) and `electric_conductivity` (4,060) are strings with the unit appended with no separator: `'5000000000000000.0ohm*cm'`, `'2e-161/(ohm*cm)'`. Unit classes: resistivity `ohm*cm` (>= 4,013), `ohm*m` (9); conductivity `1/(ohm*cm)` (>= 4,048), `mS/cm` (10), `ohm/m` (1). Parse with `^([0-9.eE+-]+?)(ohm\*cm|ohm\*m|1/\(ohm\*cm\)|mS/cm|ohm/m)$` -- the `1` of `1/(ohm*cm)` must be stripped before float().
6. `sample_id` always matches `^\d{7}-\d{3}-\d{3}-\d{3}$` (42,557 / 42,557) and is unique. The first 7-digit block (6,909 unique) is not 1:1 with `polymer_id` (872 polymer_ids span >1 block; 2,375 blocks span >1 polymer_id) -> it is a source/literature-entry id, not a polymer id. Suggested reading: `<source>-<sample>-<condition>-<replicate>`, unverified.
7. `copolymer_type` is a Python-list literal string; 59 distinct tag-lists; 11,779 rows / 2,723 polymer_ids carry >1 tag (e.g. `['unspecified', 'alternating copolymer']` 4,097 rows; `['block copolymer', 'alternating copolymer']` 1,588).
8. Non-ASCII in `polymer_name`: 11 rows / 2 polymer_ids, code points U+7BC0 and U+B993 (cp949 mis-decoding of what should be `p` and a stray byte), not U+FF50. Treat as an encoding defect, not full-width text.
9. XLSX `iupac`: 13 null, 247 duplicated strings; XLSX property columns: Tg_K 7,733; melting 3,696; density 1,651 (0.23..2.9); `Elongation_at_break_GPa` 0.45..3000 (column name says GPa but values are clearly %); `Tensile_modulus_GPa` 8.6e-6..180.8.
10. CSV rows with zero numeric properties: 13,892 (but most of these carry the string-typed resistivity/conductivity).

---

## 6. PROPOSAL: unified domain model (NOT fact - a design proposal)

### 6.1 Entities

#### Monomer  (one row per distinct repeat unit)
| field | type | null | CSV source | XLSX source | transform | lossless |
|-------|------|------|-----------|-------------|-----------|----------|
| monomer_key | str, PK | no | smiles1 / smiles2 | polymer_smiles | periodic key (`pcanon.periodic_canon`); linear canon when the periodic form is undefined | **no** (E/Z on the closed ring lost; 11 known merges) |
| psmiles_canonical | str | no | same | same | RDKit linear canonical, `*` kept | yes (up to RDKit version) |
| psmiles_raw_variants | list[str] | no | same | polymer_smiles, CanonSMILES | collect distinct raw strings | yes |
| stereo_flag | bool | no | same | same | `/`, `\`, `@` present in raw | yes |
| n_star | int | no | same | same | count `*` after parse | yes |
| topology_tag | enum {linear2, multiarm, terminal_only, unparsed} | no | same | same | n_star==2 -> linear2; 3,4,6,8,16 -> multiarm; 0 -> terminal_only; RDKit fail -> unparsed | yes |
| periodic_status | enum | no | - | - | status string from pcanon | yes |
| xlsx_pids | list[str] | yes | - | pid | all pids sharing monomer_key | yes |
| csv_component_ids | list[str] | yes | component1/2 | - | ids whose majority SMILES maps here (advisory only) | n/a |
| homopolymer_props | list[Measurement] | yes | - | Tg_K.. | see Measurement | yes |

#### Polymer  (one row per CSV polymer_id and one per XLSX pid)
| field | type | null | CSV | XLSX | transform | lossless |
|-------|------|------|-----|------|-----------|----------|
| polymer_uid | str, PK | no | polymer_id | pid | prefix `csv:`/`xlsx:` + id (namespaces are disjoint anyway) | yes |
| source_file | enum | no | const | const | | yes |
| name | str | yes | polymer_name | iupac | strip; repair CRLF-shifted rows (P908185); flag non-ASCII (2 ids) | yes |
| architecture_tags | list[enum] | no | copolymer_type | const `homopolymer` | `ast.literal_eval`; vocabulary {unspecified, random, statistical, alternating, block, graft, ...}; keep order | yes |
| monomers | list[MonomerRef] ordered | no | smiles1, smiles2 (name order) | polymer_smiles | list of monomer_key; length 1 for XLSX; 0/1/2 for CSV (4 rows 0, 115 rows 1) | yes |
| n_components_declared | int | yes | polymer_name | - | count separators (`/`, `-co-`, `-alt-`, `-block-`, `-graft-`) + 1 | heuristic |

#### Sample  (one row per CSV sample_id; XLSX has none - its rows are Polymer-level aggregates)
| field | type | null | CSV | transform | lossless |
|-------|------|------|-----|-----------|----------|
| sample_id | str, PK | no | sample_id | as is; validate `^\d{7}-\d{3}-\d{3}-\d{3}$` | yes |
| source_block | str | no | sample_id[:7] | slice | yes |
| polymer_uid | FK | no | polymer_id | | yes |
| composition | list[CompositionEntry] | yes | component_i, composition_i, smiles_i | see 6.2 | **no** (1,823 unparseable strings kept only as raw) |
| composition_basis | enum {mol, wt, vol, u, r, none} | yes | prefix | m->mol, w->wt, v->vol, u/r/none kept verbatim | yes |
| composition_sum | float | yes | | sum of parsed values | derived |
| row_alignment_class | enum | no | derived | aligned / swapped / half_* / neither / no_ids | derived |
| measurements | list[Measurement] | no | property columns | see 6.3 | yes |

CompositionEntry: `{monomer_key, position_in_smiles (1|2|null), component_id_raw, value_raw, value, basis, exact_flag (x suffix absent), resolution ('by_component_majority'|'by_position'|'unresolved')}`. Resolution rule: if component_id's majority SMILES equals smiles1 or smiles2 use that; else use position and mark `by_position` (only safe for aligned rows).

#### Measurement
| field | type | null | CSV | XLSX | transform | lossless |
|-------|------|------|-----|------|-----------|----------|
| property | enum | no | column | column | map: glass_transition_temperature->Tg; melting_temperature->Tm; density->density; tensile_modulus->E; tensile_stress_strength_at_break->sigma_b; elongation_at_break->eps_b; volume_resistivity->rho_v; electric_conductivity->sigma_e; refractive_index->n_D | yes |
| value | float | no | | | Tg,Tm: CSV `+273.15`, XLSX as is; density as is; rho_v: parse number, `ohm*m` * 100; sigma_e: parse number, `mS/cm` * 1e-3; E, sigma_b: CSV assumed GPa (unverified, ratio 0.87 on N=12) | Tg/Tm/density yes; resistivity/conductivity yes after parse; E units **unverified** |
| unit | str | no | | | K, g/cm3, GPa, %, ohm*cm, S/cm, 1 | |
| value_raw | str | no | | | original cell | yes |
| provenance | struct {file, row_index, column, sample_id or pid} | no | | | | yes |
| aggregation | enum {single_sample, polymer_median} | no | const single_sample | const polymer_median (XLSX appears aggregated) | | |

### 6.2 Draft JSON Schema (abridged, pydantic-style)
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$defs": {
    "Monomer": {"type":"object","required":["monomer_key","psmiles_canonical","n_star","topology_tag","periodic_status"],
      "properties":{
        "monomer_key":{"type":"string"},
        "psmiles_canonical":{"type":"string","pattern":"\\*"},
        "psmiles_raw_variants":{"type":"array","items":{"type":"string"},"minItems":1},
        "stereo_flag":{"type":"boolean"},
        "n_star":{"type":"integer","minimum":0},
        "topology_tag":{"enum":["linear2","multiarm","terminal_only","unparsed"]},
        "periodic_status":{"enum":["ok","neighbors_already_bonded","same_neighbor","nstar!=2","star_degree!=1","bondtype_mismatch","sanitize_fail","parse_fail"]},
        "xlsx_pids":{"type":"array","items":{"type":"string","pattern":"^P\\d{6}$"}},
        "csv_component_ids":{"type":"array","items":{"type":"string"}}}},
    "Polymer": {"type":"object","required":["polymer_uid","source_file","architecture_tags","monomers"],
      "properties":{
        "polymer_uid":{"type":"string","pattern":"^(csv|xlsx):P\\d{6}$"},
        "source_file":{"enum":["polymer_final_0824.csv","230227_Homopolymer_CanonicalSMILES.xlsx"]},
        "name":{"type":["string","null"]},
        "architecture_tags":{"type":"array","items":{"enum":["homopolymer","unspecified","random copolymer","statistical copolymer","alternating copolymer","block copolymer","graft copolymer","periodic copolymer","gradient copolymer"]},"minItems":1},
        "monomers":{"type":"array","items":{"type":"string"},"minItems":0,"maxItems":5},
        "n_components_declared":{"type":["integer","null"]}}},
    "CompositionEntry":{"type":"object","required":["value_raw","resolution"],
      "properties":{
        "monomer_key":{"type":["string","null"]},
        "position_in_smiles":{"type":["integer","null"],"enum":[1,2,null]},
        "component_id_raw":{"type":["string","null"]},
        "value_raw":{"type":"string"},
        "value":{"type":["number","null"],"minimum":0,"maximum":100},
        "basis":{"enum":["mol","wt","vol","u","r","none",null]},
        "exact_flag":{"type":"boolean"},
        "resolution":{"enum":["by_component_majority","by_position","unresolved"]}}},
    "Measurement":{"type":"object","required":["property","value","unit","value_raw","provenance","aggregation"],
      "properties":{
        "property":{"enum":["Tg","Tm","density","E","sigma_b","eps_b","rho_v","sigma_e","n_D"]},
        "value":{"type":"number"},
        "unit":{"enum":["K","g/cm3","GPa","%","ohm*cm","S/cm","1"]},
        "value_raw":{"type":"string"},
        "provenance":{"type":"object","required":["file","row_index","column"],
          "properties":{"file":{"type":"string"},"row_index":{"type":"integer"},"column":{"type":"string"},"sample_id":{"type":["string","null"]},"pid":{"type":["string","null"]}}},
        "aggregation":{"enum":["single_sample","polymer_median"]}}},
    "Sample":{"type":"object","required":["sample_id","polymer_uid","measurements","row_alignment_class"],
      "properties":{
        "sample_id":{"type":"string","pattern":"^\\d{7}-\\d{3}-\\d{3}-\\d{3}$"},
        "source_block":{"type":"string","pattern":"^\\d{7}$"},
        "polymer_uid":{"type":"string"},
        "composition":{"type":"array","items":{"$ref":"#/$defs/CompositionEntry"}},
        "composition_basis":{"enum":["mol","wt","vol","u","r","none",null]},
        "composition_sum":{"type":["number","null"]},
        "row_alignment_class":{"enum":["aligned","swapped","half_aligned","half_swapped","neither","one_component_id","no_component_ids"]},
        "measurements":{"type":"array","items":{"$ref":"#/$defs/Measurement"}}}}
  }
}
```

### 6.3 Candidate INVARIANTS for a validator (with the current pass/fail count where computed)
| id | invariant | current status |
|----|-----------|----------------|
| I1 | `sample_id` unique and matches `^\d{7}-\d{3}-\d{3}-\d{3}$` | passes (42,557 / 42,557) |
| I2 | Within a `polymer_id`, smiles1/smiles2/name/copolymer_type are constant | 7,384 / 7,385 pass; P908185 fails (CRLF) |
| I3 | Every Monomer with `topology_tag == linear2` has exactly two `*`; multiarm must be explicitly tagged | CSV: 84,315 two-star cells; 672 multi-star; 4 zero-star |
| I4 | `periodic_canon(psmiles)` of every Monomer is stable under re-run (idempotence) | by construction |
| I5 | Two Monomers with equal `monomer_key` but different stereo-aware canon must be linked as stereo variants, never silently merged | 11 CSV cases to link |
| I6 | Tg and Tm stored in K everywhere; validator: 100 <= Tg_K <= 800 (CSV after +273.15: 121.8..728.2; XLSX 138..768) | passes after transform |
| I7 | For a Sample with all compositions parsed and the same basis, `abs(sum - 100) <= 1` unless `n_components_declared > len(composition)` | 17,063 pass; 4,023 low (1,408 explainable by a 3rd component); 268 high |
| I8 | All composition entries of one Sample share one basis | passes (0 mixed-basis pairs) |
| I9 | composition entry resolved to a monomer of the parent Polymer (`resolution != unresolved`) | 433 'neither' rows + 190 one-id rows at risk |
| I10 | Resistivity/conductivity: the numeric part is parsed with the unit token removed; sigma_e in S/cm must satisfy 1e-20 <= v <= 1e8 | 0 of 4,060 parse without stripping |
| I11 | density in 0.2..3.5 g/cm3 | CSV min 0.024 / max 6.194 -> outliers exist |
| I12 | XLSX `polymer_smiles` and recanonicalized `CanonSMILES` agree | 13,725 / 13,725 |
| I13 | No CSV id appears in XLSX id namespace (guards against accidental id joins) | 0 overlaps |
| I14 | `architecture_tags` parses as a Python list of known vocabulary | 59 tag-lists, all list literals |
| I15 | Every Sample has >= 1 Measurement (after parsing string columns) | to be recomputed post-parse (13,892 rows have no numeric property) |
| I16 | Near-homopolymer consistency: Sample with one component >= 95 mol% and matched homopolymer must have abs(Tg - Tg_hom) <= 40 K (soft warning) | 56.7% within 20, use as warning not error |

---

## 7. Open questions (cannot be decided from the data alone)
1. Meaning/unit of composition prefixes `u` (496 rows), `r` (24), `x` suffix (`wx`, `mx`, `%x`, 126+102+50 rows) and the bare-number / `%` forms (`23.50%`, `70%`); `u` may be "unspecified basis".
2. Meaning of multi-tag `copolymer_type` lists (11,779 rows): is `['unspecified','alternating copolymer']` an ordered hierarchy (block of alternating?), a disjunction, or per-segment tags for graft/block architectures?
3. Whether smiles1/smiles2 order always follows the name order (assumed; cannot be verified without an independent structure parser for the IUPAC names).
4. Whether a composition value when only one is parseable (2,080 rows) refers to the listed component or the remainder; and what `m100`/`w100` mean in block/graft rows (e.g. P903202 `m100` + `m49`).
5. Units of CSV `tensile_modulus` and `tensile_stress_strength_at_break` (GPa vs MPa): N=12 overlap gives ratio 0.87, too few to be sure; `elongation_at_break` in XLSX is labelled GPa but is evidently %.
6. Whether XLSX property values are medians, means, or single picks over PoLyInfo samples (the CSV has many samples per polymer; XLSX one row per pid).
7. Semantics of the 4 `sample_id` blocks (source / sample / condition / replicate is a guess).
8. The composition for 3+-component polymers (1,408 rows with sum < 99 and >= 3 names) - the third component columns are empty in this export; is a fuller export available?
9. Whether component ids (`CUxxxxxx`, `JUxxxxxx`, `L1...`, and composite strings like `(CU010001/CU010040)`) are PoLyInfo monomer ids that should be globally unique -- in this file 693 of 3,079 map to >1 SMILES even after accounting for swaps.
10. Whether cis/trans polydienes should be distinct Monomers (periodic key merges them) - a modelling decision.
11. Correct text for the 2 polymer_ids with cp949-mangled names (U+7BC0/U+B993).
12. Whether the XLSX pids sharing one periodic key (108 keys) are true duplicates in PoLyInfo or distinct entries (e.g. different tacticity encoded only in the name).
