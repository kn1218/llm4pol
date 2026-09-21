# Adversarial refutation of `copolymer-csv.md` (polymer_final_0824.csv audit)

Independent recomputation of all 18 claims. Scripts and outputs live in this folder
(`r_*.py`, `out_*.txt`, `my_parsed.pkl`, `my_props.pkl`, `my_cid_to_smiles.csv`).
Every number below was computed by me in this session (Python 3.13, pandas, RDKit 2025.09.6, scipy).
Where I used the audit's `parse_comp.py` it is only because the claim is *about* that parser.

Verdict summary: 12 confirmed, 6 refuted in part (C6, C7, C10, C15, C17, and C3 off by 3 rows -- C3 kept as confirmed).
No claim is wrong in its main conclusion; the refutations are specific sub-numbers that do not reproduce or are
double counts / degenerate cases.

## C1 -- encoding: CONFIRMED
* 10,015,654 bytes, no BOM; 51 non-ASCII bytes in 18 runs: `EF BD 90` x9, `EF BF BD` x6, `EF BD` x3 (truncated).
* strict utf-8 decode fails at byte 8,775,994; cp949 decodes.
* cp949 vs utf-8/replace: 16 differing cells in 15 rows (polymer_name 11, composition1 4, smiles1 1);
  by id P900100 x9, P900212 x2, P904134 x2, P908185 x2.
* Code points: cp949 turns `EF BD 90 6F` into U+7BC0 U+B993 (`節릓`), eating the `o`; utf-8 gives U+FF50 `ｐ` + `o`.
  utf-8/replace frame contains 9 U+FFFD (6 embedded + 3 from truncated bytes).

## C2 -- broken record: CONFIRMED (mechanism slightly imprecise)
* `b.split(b'\r\n')` gives 42,561 elements, but the last is the empty trailer: 42,560 physical lines; 42,558 records
  (header + 42,557) -> **2 lines lost**, not 3.
* Four physical lines carry an odd (1) quote count, not one: idx 38646, 38647, 38648 (all P908185) and 38649 (P908186,
  whose name ends in `"""`). Line 38646 has 20 commas / 1 quote as claimed.
* Parsing merges 38646+38647 into row `0052076-001-001-001` and 38648+38649 into row `0052076-001-003-001`.
  Net effect exactly as claimed: sample `0052076-001-002-001` absent (0), P908186 absent (0), 2 polymer_name values
  contain CRLF, `copolymer_type` literal_eval gives ints 4 and 7.

## C3 -- null compositions: CONFIRMED (one number off by 3)
* both null 18,116 (42.6 %); composition1-only 190; composition2-only 0.
* "still carry two SMILES": `smiles2.notna()` gives 18,090 (the repro); rows with **both** SMILES present = 18,087.

## C4 -- parser coverage: CONFIRMED
* composition1: 24,441 non-null, ok 24,421 (99.92 %), numeric 23,629 (96.68 %).
* composition2: 24,251, ok 24,240 (99.95 %), numeric 23,267 (95.94 %).
* basis over all non-null composition1: mol 16,207 / wt 5,738 / vol 228 / unknown 2,268 (2,248 parsed + 20 unparsed).
* unparsed list identical (20 / 10); identical on cp949 and utf-8 frames (the parser's FIX table handles both mojibake forms).

## C5 -- composition sums: CONFIRMED
* both non-null 24,251; different basis 6 (the same six residual strings); same-basis numeric 23,025.
* ==100: 18,320 (79.6 %); 99-101: 18,436 (80.1 %); 95-105: 18,887; 0.98-1.02: 650 (2.8 %); (1.02,99): 3,562 (15.5 %);
  >101: 314 (1.4 %); <0.98: 63. Sum quantiles p1 1.0, p5 2.4, p50 100, p99 110.8, max 34,593.
* Note: `np.isclose(s,100)` gives 18,323 (3 float-rounding cases excluded by exact equality).

## C6 -- prefix evidence: REFUTED IN PART
* Confirmed: m 12,373/15,857 (78.0 %), w 4,346/5,255 (82.7 %), v 150/181 (82.9 %), u 454/507 (89.5 %),
  r 5/23 (21.7 %; values r10/r1 x6, r2/r1 x6, r75/r25, r50/r50, ...), `%`-prefix 10/10.
* No-prefix `N%`: 892/1,085 reproduces only with the definition "first character is a digit" (excludes `-N%`);
  with all `%`-suffixed pairs it is 968/1,176 (82.3 %). Rate is the same, count is definition dependent.
* **Refuted**: "116 rows of the form `39%`/`-61%` sum to 100". 41 composition1 + 75 composition2 values start with
  `-` = 116 *values*, but only **105 distinct rows** (11 rows have the dash in both columns), 104 are numeric pairs and
  only **87 sum to exactly 100** (shapes: (`N%`,`-N%`) 64, (`-N%`,`N%`) 28, (`-N%`,`-N%`) 11, 2 others).

## C7 -- component/SMILES alignment: REFUTED IN PART (core finding stands)
* Confirmed: ordered SMILES pair varies in 1/7,385 ids (1/4,008 on rows with both ids+SMILES); ordered id pair varies
  in 277/4,008; unordered id pair in 139; ordered id varies while ordered SMILES constant 276.
* **Refuted**: "504 (c1,c2,s1,s2) tuples in 301 ids have an id-swapped twin" reproduces only when tuples with
  component1 == component2 (their own twin) are included: 122 self-twins; **genuine swapped twins = 382 tuples in 182 ids**.
  The report's companion figure "231 tuples with SMILES-swapped twin" is 100 % smiles1 == smiles2 self-twins
  (231/231); genuine SMILES-swapped twins within an id = 0 (necessarily, since the ordered SMILES pair is constant).
* Independent id->SMILES resolution (seed = ids whose row-wise SMILES sets intersect to one SMILES, then majority-vote
  propagation), on 20,889 simple rows / 2,612 ids: seeds 568, resolved 1,963, aligned 12,509, **swapped 5,333
  (29.9 % of resolved-consistent rows)**, unresolved 1,087, inconsistent 1,960. Swap share matches (29.5 % claimed);
  the unresolved/inconsistent split is method dependent (claimed 2,200 / 1,032).
* Naive mode-SMILES per id: same slot 16,337 / other slot 3,184 / neither 1,368 (claimed 18,754 / 3,697 / 1,902; same
  qualitative picture, different denominator).

## C8 -- composition follows the component id: CONFIRMED (count of the sign test not reproducible)
* P900005 rows exactly as claimed: component1 CU040003 next to smiles1 `*C(C#N)C*`; composition1 w20/40/60/80 ->
  Tg 91/74/48/23. My resolution maps CU040003 -> `CCOC(=O)C(C*)*` (ethyl acrylate) and CU030010 -> `*C(C#N)C*`.
* Sign-flip test: "19 ids, 16 flip / 3 agree" not reproducible under any definition I tried, but the majority-flip
  result is robust: swapped id orders with >=3 distinct compositions each -> 36 tested, 28 flip; restricted to sums
  99-101 -> 32 tested, 27 flip; exactly two swapped orders -> 30 tested, 24-27 flip; any two orders -> 51 tested,
  30 flip. Null expectation is 50 %.

## C9 -- polymer_id vs SMILES pair: CONFIRMED
* id -> >1 unordered pair: 1 (P908185); pairs 5,322, shared by >1 id: 683, rows 26,126 (61.4 %); multiplicity 2: 402,
  3: 122, 4: 58, 5: 25; max 79 ids for (`*CCCCCC(=O)O*`,`*CCCCCC(=O)O*`).
* smiles1 == smiles2: 3,952 rows / 713 ids. RDKit: 4,782 valid -> 4,782 canonical; canonical pairs 5,322, shared 683,
  rows 26,126. names -> 2 ids: 83, -> 3 ids: 7 (and 6 names map to >3 ids, not mentioned).
* Caveat on the report's wording "dominated by smiles1 == smiles2": only 46 of the 683 shared pairs and 3,454 of the
  26,126 rows are smiles1 == smiles2 pairs.

## C10 -- copolymer_type: REFUTED IN PART
* Confirmed: 42,555 lists + 2 ints; lengths 1: 30,778 / 2: 10,979 / 3: 794 / 4: 6; >=2 tags 11,779 (27.7 %);
  tag frequencies identical; 29 distinct sets; varies within id in 1/7,385; 8,095 multi-tag rows contain `unspecified`.
* **Refuted**: "4,892 of the multi-tag rows carry `-alt-`": I count **5,255** (`str.contains('-alt-')`, 1,198 ids,
  1,174 unique names); no variant (single occurrence 3,871; excluding `unspecified` 2,167) gives 4,892.
* Extra: name/tag consistency is one-directional: name has `-alt-` but no alternating tag in only 5 rows, whereas
  4,033 rows carry the alternating tag without `-alt-` in the name; block tag without `-block-`/`-b-` 4,766; graft tag
  without `-graft-`/`-g-` 1,498.

## C11 -- resistivity / conductivity strings: CONFIRMED
* 0 numeric before parsing. Suffixes: `ohm*cm` 4,016 (one is unit-only), `ohm*m` 11, `[NR]` 4;
  `1/(ohm*cm)` 4,048 (3 unit-only), `mS/cm` 10, `ohm/m` 2. Parsed: 4,015 and 4,045.
* log10 medians 4.08 / -4.09; both present 4,015 rows; log10(res*cond) median 0.0000, IQR 0.004.
* Caution confirmed: a greedy number regex reads `2e-161/(ohm*cm)` as 2e-161 (2,061 of 4,048 strings would drop
  below 1e-40); the `1/(ohm*cm)` suffix must be stripped first.
* Extra: not perfect reciprocals -- 351 rows deviate by |log10| > 0.05 and 33 by > 0.5; 30 rows have conductivity
  only; 6 conductivity zeros; 4 values > 1e6 S/cm.

## C12 -- property ranges: CONFIRMED
All n/min/p1/median/p99/max reproduce (Tg 18,142, -151.35, -110.0, 52.55, 338, 455; Tm 8,713, -68, -7.88, 128, 375,
533; density 3,104, 0.024, 0.581, 1.096, 2.20, 6.194; modulus 3,709, 8e-8, 1e-4, 0.255, 62.84, 916; stress 5,046, 0,
2e-4, 0.0185, 11.06, 580; elongation 5,072, 0, 1.1, 250, 1,800, 6,190; RI 684, 1.295, 1.344, 1.53, 2.266, 2.467).
Tg zeros 55, negatives 5,687; density >5: 9, <0.5: 29; modulus >100: 25, <0.01: 929; stress >500: 2; elongation
>2000: 32; Tg>Tm 78 of 3,728 (Tg==Tm 2). Extra: Tg/Tm in K median 0.708, 41 rows < 0.4, 186 rows > 0.9.

## C13 -- property coverage: CONFIRMED
0: 11,151 (26.2 %), 1: 17,839, 2: 8,782, 3: 2,829, 4: 1,293, 5: 529, 6: 115, 7: 19; >=2: 13,567 (31.9 %).
Joint matrix identical to the audit's (Tg&Tm 3,728, stress&elong 4,446, modulus&elong 2,891, res&cond 4,015,
Tg&modulus 1,273, density&Tg 1,119).

## C14 -- Tg replicates: CONFIRMED
10,163 groups; 2,243 multi-row groups holding 10,222 rows (56.3 %); 2,018 with >1 distinct Tg; SD quantiles
p25/p50/p75/p90/p95/p99 = 2.12/7.00/15.69/33.13/52.39/120.03, mean 13.82; range >20: 872, >50: 355; known-composition
groups 1,053 (median SD 4.75, p90 29.8) vs none 1,190 (8.59, 34.6); sample-level: 650 samples, 606 distinct, median SD
4.95. Grouping by raw composition strings instead of parsed values gives 2,239 groups / 10,132 rows / median SD 6.85.

## C15 -- sample_id structure: REFUTED IN PART
* Confirmed: 7-3-3-3 digit widths; seg0 6,909 unique; corr(seg0, polymer number) 0.066; (seg0,seg1) -> exactly 1
  polymer_id in all 22,440 groups; composition never differs within (seg0,seg1,seg2) (0 of 5,452 multi-row groups);
  seg3 001: 34,943, 002: 5,458, max 017.
* **Refuted**: "seg0 spans 1..162 polymer_ids": a seg0 maps to **1..85** polymer_ids (max 85 for source 0020270,
  340 rows). 162 is the reverse direction (max number of distinct seg0 per polymer_id).
* **Refuted**: "Tg differs in 3,221" of the (seg0,seg1,seg2) groups: 3,221 is `nunique(dropna=False) > 1`, i.e. it
  counts a Tg row next to a non-Tg row. Groups with two *different* Tg values = **606**. What actually differs across
  seg3 is the property pattern: 4,268 of 5,452 multi-row samples have >1 property-presence pattern, so seg3 is mostly
  a "which property record" index, not a replicate index.
* Caveat: seg1 does not start at 001 in 2,936 of 6,909 sources, so it indexes all polymers of the source (probably
  including homopolymers not in this table), not just the copolymers present.

## C16 -- SMILES counts and `*` counts: CONFIRMED (qualifier overstated)
* 2 SMILES 42,438, 1: 115 (37 ids; smiles2 missing 96, smiles1 missing 19), 0: 4 (P904415 x1, P908136 x3).
* `*` count over 4,792 unique: 0: 4, 2: 4,646, 3: 80, 4: 53, 6: 6, 8: 2, 16: 1; slot occurrences 2: 84,315, 3: 459,
  4: 203, 6: 6, 8: 3, 16: 1; the 16-star SMILES contains `[Si]`.
* Overstated: "nearly all are monomers with unspecified substitution position written `x-`": only 32 of the 115
  one-SMILES rows (13 of 37 ids) contain `x-` in the name; 90 of 115 have both component ids.

## C17 -- RDKit validity: REFUTED IN PART
* Confirmed: 10 of 4,792 fail; 6 contain `[B]` and parse with sanitize=False; 4 are text fragments (fail even
  unsanitised); `[*]` substitution fixes none; charged 257 (RDKit formal charge) / 258 (regex); `/`or`\` 74; `@` 0;
  `.` 1; 4,782 -> 4,782 canonical.
* **Refuted**: "46 rows" -- 46 is the number of SMILES *slot occurrences*; distinct rows = **30**, in **9** ids:
  P901377 8, P901378 4, P907666 4, P907667 4, P904273 3, P904274 3, P908185 2, P904536 1, P904537 1.
  The claim's per-id counts (P904273 15, P904274 9, P904536 2) do not match row counts (3, 3, 1 -- these ids have only
  3, 3 and 1 rows in the whole table) and it omits P901378 and P904537.

## C18 -- Tg vs composition monotonicity: CONFIRMED
* Cohort = group by polymer_id only, both compositions numeric, same basis, sum 99-101, >=5 distinct composition1
  (the "distinct SMILES" filter is not actually applied in the audit's CSV): 378 ids (audit 379), median |rho| 0.868,
  234 > 0.7, 67 < 0.3 -- exact match. Adding the smiles1 != smiles2 filter gives 368 ids / 0.873 / 226 / 66.
* Named examples reproduce under per-basis grouping: P900016 wt n=74 rho 0.204 (p 0.08); P900007 wt n=57 rho -0.056;
  P900492 mol n=55 rho 0.121. Note the audit's own CSV (id-level) lists P900016 n=89 rho 0.37, P901010 n=88,
  P902489 n=85 as the largest ids, so the text mixes two groupings.
* Extra: re-aligning composition to smiles1 through my id->SMILES map raises median |rho| from 0.878 to 0.900 and
  the >0.7 count from 200 to 214 on the same 323 ids -- weak but consistent support for the swap finding.

## What the audit missed (extra findings)
1. **Exact duplicate records**: 6,548 rows are identical to another row on every column except sample_id (9,047 rows
   in 2,499 groups, 1,285 ids); 1,355 of the duplicates carry a property value (462 ids; e.g. P900007 samples
   0013258-008-001-001/-002 both Tg 102.5); 1,979 groups span >1 sample and 548 span >1 source. Dedup before modelling.
2. **Terpolymers truncated to two components**: 7,389 rows (17.4 %, 1,320 ids) name >=3 repeat units (counting
   `-co-/-alt-/-block-/-graft-` links and `/` inside braces); conservative link-word-only count 4,243 rows / 548 ids.
   3,709 of the 7,389 rows carry a 2-component composition and 1,440 of those sum to exactly 100.
3. **No composition anywhere for 45 % of ids**: 3,323 ids (11,071 rows) have composition null in every row; 1,878 of
   the 4,578 Tg-bearing ids never have a composition. Component ids are missing in exactly the same rows
   (18,107 rows with SMILES but no component id; 18,114 rows with both component ids null).
4. **Source leakage is nearly total**: 6,513 of 7,385 ids (88.2 %, 21,200 rows) come from a single source (seg0), and
   4,534 sources hold a single polymer -> grouping CV by source is almost the same as grouping by polymer.
5. **Tm replicates**: 1,133 (polymer, composition) groups hold 5,057 of 8,713 Tm rows (58 %), median SD 5.2 C, p90 32.6.
6. **Degenerate slot pairs**: component1 == component2 in 779 rows / 121 ids (499 of them also smiles1 == smiles2);
   smiles1 == smiles2 with two *different* component ids in 792 rows (stereo/tacticity or D/L variants lost in SMILES).
7. **Composition extremes**: values >100 in 109 (c1) / 94 (c2) rows; ==0 in 57 / 129; ==100 in 204 / 49; 98 rows are
   0/100 pairs (effectively homopolymer samples inside a copolymer id).
8. **Property-free ids**: 1,301 polymer_ids (17.6 %) have no property in any row.
9. **Attachment-point variants**: removing `*` atoms and re-canonicalising collapses 4,782 SMILES to 4,666 backbones,
   i.e. 116 SMILES are the same monomer drawn with different attachment points (RDKit canonicalisation with `*` kept
   does not merge them).
10. Physical sanity: 89 tensile-stress values > 1 GPa (likely MPa), 94 moduli > 10 GPa, 25 densities > 3 g/cm3,
    3 rows with modulus > 1 GPa and stress > modulus; conductivity > 1e6 S/cm in 4 rows.
11. `[2H]` deuterium in 26 SMILES; Si in 317; 5 with transition metals.
